#!/usr/bin/env python3
"""High-throughput official generation with vLLM.

Use this backend for generation-only experiments (E48 natural prevalence and
E49 hard-task conditioning).  It deliberately does not replace HF for hidden
state/MLP/activation-patching experiments, where hooks are part of the
scientific measurement.
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from vllm import LLM, SamplingParams  # noqa: E402

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_tokenizer, visible_device_label  # noqa: E402


E48_PROMPT_VARIANTS = {
    "neutral": (
        "Solve the problem carefully. Show only the reasoning needed to justify the answer. "
        "End with exactly one line `Final answer: <answer>`.\n\nProblem: {problem}"
    ),
    "timed_exam": (
        "You are in a timed exam. Give a short, natural solution, but do not skip the key mathematical step. "
        "End with exactly one line `Final answer: <answer>`.\n\nProblem: {problem}"
    ),
    "answer_first_no_gold": (
        "Solve the problem yourself. First write one line `Final answer: <answer>`, then give a brief justification. "
        "No answer is provided in the prompt.\n\nProblem: {problem}"
    ),
    "bilingual_check": (
        "Solve the problem. If a term is in Chinese, preserve its mathematical meaning; if it is in English, do not translate it loosely. "
        "End with exactly one line `Final answer: <answer>`.\n\nProblem: {problem}"
    ),
}

E49_PROMPT_VARIANTS = {
    "neutral": (
        "Solve the following AIME-style problem carefully. Show the reasoning needed to justify the result. "
        "End with exactly one line `Final answer: <integer>`.\n\nProblem: {problem}"
    ),
    "answer_first_no_gold": (
        "Solve the following AIME-style problem yourself. First write one line `Final answer: <integer>`, "
        "then give a concise justification. No final answer is provided in the prompt.\n\nProblem: {problem}"
    ),
    "self_check": (
        "Solve the following AIME-style problem. After deriving an answer, do one brief self-check for the main trap, "
        "then end with exactly one line `Final answer: <integer>`.\n\nProblem: {problem}"
    ),
    "answer_anchor": (
        "This is not a benchmark-performance run. A public final answer is provided only to condition a rationale. "
        "Write a concise mathematical solution that genuinely justifies the given answer. "
        "If a step is uncertain, say so rather than inventing it. End with exactly one line `Final answer: <integer>`.\n\n"
        "Problem: {problem}\nGiven final answer: {answer}"
    ),
}


E48_INVALID_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "mean_vs_median": [(r"\bmedian\b|middle value|中位数|中间值", "mean_median_confusion")],
    "range_vs_average": [(r"\baverage\b|\bmean\b|平均", "range_average_confusion")],
    # Mentioning the exponent while distinguishing it from the coefficient is
    # valid; only flag explicit coefficient=3 contradictions.
    "coefficient_vs_exponent": [(r"\bcoefficient\b.{0,40}\b(?:is|=|equals)\s*3\b", "coefficient_exponent_confusion")],
    "reciprocal_vs_additive_inverse": [(r"additive inverse|negative|-\s*4|change the sign|相反数|负数|变号", "reciprocal_additive_inverse_confusion")],
    "percent_increase_vs_percent_of": [(r"new price (?:is|=).{0,20}(?:20%|0\.2).*50|only\s+20%|multiply\s+by\s+0\.?20", "increase_percent_of_confusion")],
    "prob_without_replacement": [(r"with replacement|put back|replaced before|3/5\s*(?:again|twice)|same\s+3\s+red\s+(?:out of|among)\s+5", "without_replacement_confusion")],
    "each_vs_total": [(r"split|share|divide\s+6\s+by\s+4|class total is 6|whole group read 6|总共\s*6|平分", "each_total_confusion")],
    "log_base_argument": [(r"base\s+is\s+8|argument\s+is\s+2|8\s+as\s+the\s+base|以\s*8\s*为底|真数是\s*2", "log_base_argument_confusion")],
    # Dropping remaining digits after applying the round-up rule is valid; flag
    # only explicit truncation/down-to-4.6 language.
    "round_vs_truncate": [(r"truncate|truncation|round\s+down\s+to\s+4\.6|nearest\s+tenth\s+is\s+4\.6|舍去.*4\.6|截断", "round_truncate_confusion")],
    "zh_perimeter_vs_area": [(r"面积|长乘宽|8\s*[*×x]\s*3|24\s*平方", "perimeter_area_confusion")],
    "zh_yi_wan_unit": [(r"1000\s*万|一千\s*万|0\.3\s*[*×x]\s*1000", "yi_wan_unit_confusion")],
    # Correct solutions may say "integers less than 6 include 3,4,5"; flag
    # only explicit endpoint-inclusive language or lists with 2/6.
    "zh_exclusive_interval": [(r"2\s*、\s*3\s*、\s*4\s*、\s*5\s*、\s*6|2\s*,\s*3\s*,\s*4\s*,\s*5\s*,\s*6|把边界|含端点|包括端点|包含端点|including endpoints|inclusive interval|from\s+2\s+to\s+6\s+inclusive", "exclusive_interval_endpoint_confusion")],
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def normalize_answer(text: str) -> str:
    text = text.strip().lower()
    text = text.replace("$", "").replace("\\", "")
    text = re.sub(r"\s+", "", text)
    text = text.rstrip(".。,:;，；")
    frac = re.fullmatch(r"(-?[0-9]+)\s*/\s*([0-9]+)", text)
    if frac:
        return f"{int(frac.group(1))}/{int(frac.group(2))}"
    if re.fullmatch(r"-?\d+\.0+", text):
        return str(int(float(text)))
    return text


def extract_final_answer(text: str, *, allow_fallback: bool = False, integer_only: bool = False) -> tuple[str, bool]:
    matches = list(re.finditer(r"^\s*final\s*answer\s*[:：]\s*([^\n]+)", text, flags=re.IGNORECASE | re.MULTILINE))
    if matches:
        return matches[-1].group(1).strip(), True
    if not allow_fallback:
        return "", False
    tail = text[-320:]
    pattern = r"-?\d+(?:\.\d+)?" if integer_only else r"-?\d+\s*/\s*\d+|-?\d+(?:\.\d+)?"
    nums = re.findall(pattern, tail)
    return (nums[-1].strip() if nums else ""), False


def e48_process_audit(task_id: str, completion: str, final_correct: bool) -> tuple[bool | None, str]:
    if not final_correct:
        return None, "not_final_correct_not_audited"
    for pattern, reason in E48_INVALID_PATTERNS.get(task_id, []):
        if re.search(pattern, completion, flags=re.IGNORECASE | re.DOTALL):
            if task_id == "percent_increase_vs_percent_of" and re.search(r"add|increase.{0,30}by|50\s*\+\s*10|1\.20|120%", completion, flags=re.IGNORECASE | re.DOTALL):
                continue
            return False, reason
    return True, "no_known_invalid_process_found_manual_review_required"


def should_use_chat(spec: dict[str, Any], tokenizer) -> bool:
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return bool(getattr(tokenizer, "chat_template", None)) and (fam in {"qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls)


def render_content(mode: str, task: dict[str, Any], variant: str) -> tuple[str, bool]:
    if mode == "e48":
        return E48_PROMPT_VARIANTS[variant].format(problem=task["problem"]), False
    gold_in_prompt = variant == "answer_anchor"
    return E49_PROMPT_VARIANTS[variant].format(problem=task["en"], answer=task["answer"]), gold_in_prompt


def render_token_prompt(tokenizer, spec: dict[str, Any], content: str, thinking: bool) -> tuple[dict[str, list[int]], bool, bool]:
    use_chat = should_use_chat(spec, tokenizer)
    if use_chat:
        messages = [{"role": "user", "content": content}]
        try:
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=thinking)
        except TypeError:
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        add_special = False
    else:
        text = content + "\nReasoning:"
        add_special = True
    token_ids = tokenizer.encode(text, add_special_tokens=add_special)
    return {"prompt_token_ids": token_ids}, use_chat, add_special


def load_tasks(mode: str, args: argparse.Namespace) -> list[dict[str, Any]]:
    if mode == "e48":
        return read_jsonl(Path(args.e48_tasks_jsonl))[: args.max_tasks]
    return read_yaml(args.e49_tasks_yaml)["tasks"][: args.max_tasks]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["e48", "e49"], required=True)
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--e48-tasks-jsonl", default=str(PROJECT / "data/processed/e48_natural_prevalence_tasks_20260428.jsonl"))
    p.add_argument("--e49-tasks-yaml", default=str(PROJECT / "configs/e26_aime_hard_tasks.yaml"))
    p.add_argument("--out-dir", default="")
    p.add_argument("--variants", nargs="+", default=None)
    p.add_argument("--k", type=int, default=2)
    p.add_argument("--max-tasks", type=int, default=12)
    p.add_argument("--max-new-tokens", type=int, default=512)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--top-k", type=int, default=50)
    p.add_argument("--tensor-parallel-size", type=int, default=4)
    p.add_argument("--gpu-memory-utilization", type=float, default=0.88)
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--thinking", choices=["auto", "true", "false"], default="auto")
    p.add_argument("--allow-final-fallback", action="store_true")
    p.add_argument("--seed", type=int, default=20260428)
    p.add_argument("--enforce-eager", action="store_true")
    p.add_argument("--model-impl", choices=["auto", "vllm", "transformers"], default="auto")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    if not is_local_model(spec):
        raise SystemExit(f"Model is not local; refusing network load for official run: {args.model_key}")
    variants = args.variants or (list(E48_PROMPT_VARIANTS) if args.mode == "e48" else ["neutral", "answer_first_no_gold", "self_check"])
    allowed = E48_PROMPT_VARIANTS if args.mode == "e48" else E49_PROMPT_VARIANTS
    unknown = sorted(set(variants) - set(allowed))
    if unknown:
        raise SystemExit(f"Unknown variants: {unknown}")

    tokenizer = load_tokenizer(spec["path"], local_files_only=True)
    thinking = (args.mode == "e49") if args.thinking == "auto" else (args.thinking == "true")
    tasks = load_tasks(args.mode, args)
    jobs = []
    prompt_inputs = []
    for task in tasks:
        for variant in variants:
            content, gold_in_prompt = render_content(args.mode, task, variant)
            prompt_input, used_chat, add_special = render_token_prompt(tokenizer, spec, content, thinking)
            prompt_inputs.append(prompt_input)
            jobs.append({"task": task, "variant": variant, "gold_in_prompt": gold_in_prompt, "used_chat": used_chat, "add_special": add_special})

    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] vLLM loading {args.model_key} mode={args.mode} tp={args.tensor_parallel_size}", flush=True)
    llm = LLM(
        model=spec["path"],
        tokenizer=spec["path"],
        trust_remote_code=True,
        tensor_parallel_size=args.tensor_parallel_size,
        dtype=args.dtype,
        seed=args.seed,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=args.max_model_len,
        enforce_eager=args.enforce_eager,
        model_impl=args.model_impl,
    )
    sampling = SamplingParams(
        n=args.k,
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
        max_tokens=args.max_new_tokens,
        seed=args.seed,
    )
    outputs = llm.generate(prompt_inputs, sampling, use_tqdm=True)

    rows = []
    for job, request_output in zip(jobs, outputs):
        for sample_idx, item in enumerate(request_output.outputs):
            completion = item.text.strip()
            task = job["task"]
            if args.mode == "e48":
                gold_answer = task["gold_answer"]
                extracted, final_marker = extract_final_answer(completion, allow_fallback=args.allow_final_fallback)
                final_correct = normalize_answer(extracted) == normalize_answer(gold_answer)
                proc_valid, risk = e48_process_audit(task["task_id"], completion, final_correct)
                rows.append(
                    {
                        "created_at": datetime.now().isoformat(timespec="seconds"),
                        "backend": "vllm",
                        "model_key": args.model_key,
                        "task_id": task["task_id"],
                        "surface_family": task["surface_family"],
                        "problem": task["problem"],
                        "gold_answer": gold_answer,
                        "prompt_variant": job["variant"],
                        "sample_idx": sample_idx,
                        "used_chat_template": job["used_chat"],
                        "add_special_tokens": job["add_special"],
                        "gold_answer_in_prompt": False,
                        "known_error_span_in_prompt": False,
                        "completion": completion,
                        "extracted_final": extracted,
                        "final_marker_found": final_marker,
                        "manual_final_correct": final_correct,
                        "manual_process_valid": proc_valid,
                        "manual_risk": risk,
                        "is_acpi": bool(final_correct and proc_valid is False),
                    }
                )
            else:
                gold_answer = task["answer"]
                extracted, final_marker = extract_final_answer(completion, allow_fallback=args.allow_final_fallback, integer_only=True)
                final_correct = normalize_answer(extracted) == normalize_answer(gold_answer)
                rows.append(
                    {
                        "created_at": datetime.now().isoformat(timespec="seconds"),
                        "backend": "vllm",
                        "model_key": args.model_key,
                        "task_id": task["id"],
                        "problem": task["en"],
                        "gold_answer": gold_answer,
                        "trap_note_not_in_prompt": task.get("trap", ""),
                        "prompt_variant": job["variant"],
                        "sample_idx": sample_idx,
                        "used_chat_template": job["used_chat"],
                        "add_special_tokens": job["add_special"],
                        "thinking": thinking,
                        "gold_answer_in_prompt": job["gold_in_prompt"],
                        "known_trap_note_in_prompt": False,
                        "completion": completion,
                        "extracted_final": extracted,
                        "final_marker_found": final_marker,
                        "manual_final_correct": final_correct,
                        "manual_process_valid": None,
                        "manual_risk": "final_correct_needs_manual_process_audit" if final_correct else "not_final_correct",
                        "is_acpi": False,
                    }
                )

    by_variant = defaultdict(Counter)
    by_task = defaultdict(Counter)
    for r in rows:
        for bucket in (by_variant[r["prompt_variant"]], by_task[r["task_id"]]):
            bucket["n"] += 1
            bucket["final_correct"] += int(r["manual_final_correct"])
            bucket["acpi"] += int(r.get("is_acpi", False))
            bucket["gold_answer_in_prompt"] += int(r.get("gold_answer_in_prompt", False))
            bucket["needs_manual_process_audit"] += int(r["manual_risk"] in {"no_known_invalid_process_found_manual_review_required", "final_correct_needs_manual_process_audit"})
    summary = {
        "n": len(rows),
        "final_correct": sum(r["manual_final_correct"] for r in rows),
        "process_invalid_final_correct": sum(r.get("is_acpi", False) for r in rows),
        "not_final_correct": sum(not r["manual_final_correct"] for r in rows),
        "strict_final_marker_missing": sum(not r["final_marker_found"] for r in rows),
        "gold_answer_in_prompt_rows": sum(r.get("gold_answer_in_prompt", False) for r in rows),
        "by_variant": {k: dict(v) for k, v in sorted(by_variant.items())},
        "by_task": {k: dict(v) for k, v in sorted(by_task.items())},
    }
    out_dir = Path(args.out_dir) if args.out_dir else PROJECT / ("results/E48_natural_prevalence_official" if args.mode == "e48" else "results/E49_hard_task_conditioning_official")
    out = out_dir / f"{args.model_key}_{args.mode}_vllm_official_generation.json"
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "backend": "vllm",
        "tensor_parallel_size": args.tensor_parallel_size,
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "prompt_variants": allowed,
        "summary": summary,
        "rows": rows,
        "comparability_note_en": "Prompt content, chat-template rendering, final-answer filters, and post-hoc audit logic match the official HF generation scripts; the decoding engine is vLLM for higher throughput, so exact samples need not be token-identical to HF.",
        "comparability_note_zh": "提示内容、chat 模板渲染、final-answer 过滤和事后审计逻辑与官方 HF 生成脚本一致；解码引擎换成 vLLM 以提高吞吐，因此样本不要求与 HF 逐 token 完全相同。",
    }
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print("SUMMARY", summary, flush=True)


if __name__ == "__main__":
    main()
