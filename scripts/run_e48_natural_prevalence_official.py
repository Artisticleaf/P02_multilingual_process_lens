#!/usr/bin/env python3
"""E48 official natural-prevalence harvesting.

This script asks models to solve surface-semantic tasks without inserting gold
answers or known error spans into the prompt.  It estimates a budgeted natural
ACPI rate only after strict final-answer filtering and conservative process
audit.
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

import torch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402


PROMPT_VARIANTS = {
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


INVALID_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "mean_vs_median": [
        (r"\bmedian\b|middle value|中位数|中间值", "mean_median_confusion"),
    ],
    "range_vs_average": [
        (r"\baverage\b|\bmean\b|平均", "range_average_confusion"),
    ],
    "coefficient_vs_exponent": [
        # Mentioning the exponent while distinguishing it from the coefficient
        # is valid; only flag explicit coefficient=3 contradictions.
        (r"\bcoefficient\b.{0,40}\b(?:is|=|equals)\s*3\b", "coefficient_exponent_confusion"),
    ],
    "reciprocal_vs_additive_inverse": [
        (r"additive inverse|negative|-\s*4|change the sign|相反数|负数|变号", "reciprocal_additive_inverse_confusion"),
    ],
    "percent_increase_vs_percent_of": [
        (r"new price (?:is|=).{0,20}(?:20%|0\.2).*50|only\s+20%|multiply\s+by\s+0\.?20", "increase_percent_of_confusion"),
    ],
    "prob_without_replacement": [
        (r"with replacement|put back|replaced before|3/5\s*(?:again|twice)|same\s+3\s+red\s+(?:out of|among)\s+5", "without_replacement_confusion"),
    ],
    "each_vs_total": [
        (r"split|share|divide\s+6\s+by\s+4|class total is 6|whole group read 6|总共\s*6|平分", "each_total_confusion"),
    ],
    "log_base_argument": [
        (r"base\s+is\s+8|argument\s+is\s+2|8\s+as\s+the\s+base|以\s*8\s*为底|真数是\s*2", "log_base_argument_confusion"),
    ],
    "round_vs_truncate": [
        # Dropping remaining digits after applying the round-up rule is valid;
        # flag only explicit truncation/down-to-4.6 language.
        (r"truncate|truncation|round\s+down\s+to\s+4\.6|nearest\s+tenth\s+is\s+4\.6|舍去.*4\.6|截断", "round_truncate_confusion"),
    ],
    "zh_perimeter_vs_area": [
        (r"面积|长乘宽|8\s*[*×x]\s*3|24\s*平方", "perimeter_area_confusion"),
    ],
    "zh_yi_wan_unit": [
        (r"1000\s*万|一千\s*万|0\.3\s*[*×x]\s*1000", "yi_wan_unit_confusion"),
    ],
    "zh_exclusive_interval": [
        # Correct solutions may say "integers less than 6 include 3,4,5";
        # flag only explicit endpoint-inclusive language or lists with 2/6.
        (r"2\s*、\s*3\s*、\s*4\s*、\s*5\s*、\s*6|2\s*,\s*3\s*,\s*4\s*,\s*5\s*,\s*6|把边界|含端点|包括端点|包含端点|including endpoints|inclusive interval|from\s+2\s+to\s+6\s+inclusive", "exclusive_interval_endpoint_confusion"),
    ],
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


def extract_final_answer(text: str, *, allow_fallback: bool = False) -> tuple[str, bool]:
    matches = list(re.finditer(r"^\s*final\s*answer\s*[:：]\s*([^\n]+)", text, flags=re.IGNORECASE | re.MULTILINE))
    if matches:
        return matches[-1].group(1).strip(), True
    if not allow_fallback:
        return "", False
    tail = text[-240:]
    nums = re.findall(r"-?\d+\s*/\s*\d+|-?\d+(?:\.\d+)?", tail)
    return (nums[-1].strip() if nums else ""), False


def conservative_process_audit(task_id: str, completion: str, final_correct: bool) -> tuple[bool | None, str]:
    if not final_correct:
        return None, "not_final_correct_not_audited"
    patterns = INVALID_PATTERNS.get(task_id, [])
    for pattern, reason in patterns:
        if re.search(pattern, completion, flags=re.IGNORECASE | re.DOTALL):
            # Avoid marking valid percent-increase statements such as "20% of 50 is 10; add it".
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


def render_prompt(tokenizer, spec: dict[str, Any], problem: str, variant: str) -> tuple[str, bool, bool]:
    content = PROMPT_VARIANTS[variant].format(problem=problem)
    use_chat = should_use_chat(spec, tokenizer)
    if not use_chat:
        return content + "\nReasoning:", False, True
    messages = [{"role": "user", "content": content}]
    try:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    except TypeError:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return text, True, False


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--tasks-jsonl", default=str(PROJECT / "data/processed/e48_natural_prevalence_tasks_20260428.jsonl"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E48_natural_prevalence_official"))
    p.add_argument("--variants", nargs="+", default=list(PROMPT_VARIANTS))
    p.add_argument("--k", type=int, default=2)
    p.add_argument("--max-tasks", type=int, default=12)
    p.add_argument("--max-new-tokens", type=int, default=512)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--top-k", type=int, default=50)
    p.add_argument("--allow-final-fallback", action="store_true")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--seed", type=int, default=20260428)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    bad_variants = sorted(set(args.variants) - set(PROMPT_VARIANTS))
    if bad_variants:
        raise SystemExit(f"Unknown variants: {bad_variants}")
    torch.manual_seed(args.seed)
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    tasks = read_jsonl(Path(args.tasks_jsonl))[: args.max_tasks]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E48 natural prevalence", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)

    jobs: list[dict[str, Any]] = []
    for task in tasks:
        for variant in args.variants:
            prompt, used_chat, add_special = render_prompt(tok, spec, task["problem"], variant)
            for sample_idx in range(args.k):
                jobs.append({"task": task, "variant": variant, "sample_idx": sample_idx, "prompt": prompt, "used_chat": used_chat, "add_special": add_special})

    rows = []
    for start in range(0, len(jobs), args.batch_size):
        batch = jobs[start : start + args.batch_size]
        add_special_values = {j["add_special"] for j in batch}
        if len(add_special_values) != 1:
            raise RuntimeError("Mixed add_special values in one batch")
        enc = tok([j["prompt"] for j in batch], return_tensors="pt", padding=True, add_special_tokens=batch[0]["add_special"]).to(device)
        with torch.no_grad():
            out = model.generate(
                **enc,
                do_sample=True,
                temperature=args.temperature,
                top_p=args.top_p,
                top_k=args.top_k,
                max_new_tokens=args.max_new_tokens,
                pad_token_id=tok.eos_token_id,
            )
        for j, seq in zip(batch, out):
            completion = tok.decode(seq[enc["input_ids"].shape[1] :], skip_special_tokens=True).strip()
            extracted, final_marker = extract_final_answer(completion, allow_fallback=args.allow_final_fallback)
            final_correct = normalize_answer(extracted) == normalize_answer(j["task"]["gold_answer"])
            proc_valid, risk = conservative_process_audit(j["task"]["task_id"], completion, final_correct)
            rows.append(
                {
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                    "model_key": args.model_key,
                    "task_id": j["task"]["task_id"],
                    "surface_family": j["task"]["surface_family"],
                    "problem": j["task"]["problem"],
                    "gold_answer": j["task"]["gold_answer"],
                    "prompt_variant": j["variant"],
                    "sample_idx": j["sample_idx"],
                    "used_chat_template": j["used_chat"],
                    "add_special_tokens": j["add_special"],
                    "gold_answer_in_prompt": False,
                    "known_error_span_in_prompt": False,
                    "generation_params": {"temperature": args.temperature, "top_p": args.top_p, "top_k": args.top_k},
                    "completion": completion,
                    "extracted_final": extracted,
                    "final_marker_found": final_marker,
                    "manual_final_correct": final_correct,
                    "manual_process_valid": proc_valid,
                    "manual_risk": risk,
                    "is_acpi": bool(final_correct and proc_valid is False),
                }
            )
        print(f"generated {min(start + len(batch), len(jobs))}/{len(jobs)}", flush=True)

    by_variant = defaultdict(Counter)
    by_task = defaultdict(Counter)
    for r in rows:
        for bucket in (by_variant[r["prompt_variant"]], by_task[r["task_id"]]):
            bucket["n"] += 1
            bucket["final_correct"] += int(r["manual_final_correct"])
            bucket["acpi"] += int(r["is_acpi"])
            bucket["needs_manual_review"] += int(r["manual_risk"] == "no_known_invalid_process_found_manual_review_required")
    summary = {
        "n": len(rows),
        "final_correct": sum(r["manual_final_correct"] for r in rows),
        "process_invalid_final_correct": sum(r["is_acpi"] for r in rows),
        "not_final_correct": sum(not r["manual_final_correct"] for r in rows),
        "strict_final_marker_missing": sum(not r["final_marker_found"] for r in rows),
        "gold_answer_in_prompt_rows": sum(r["gold_answer_in_prompt"] for r in rows),
        "known_error_span_in_prompt_rows": sum(r["known_error_span_in_prompt"] for r in rows),
        "by_variant": {k: dict(v) for k, v in sorted(by_variant.items())},
        "by_task": {k: dict(v) for k, v in sorted(by_task.items())},
    }
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "prompt_variants": PROMPT_VARIANTS,
        "summary": summary,
        "rows": rows,
    }
    out = Path(args.out_dir) / f"{args.model_key}_e48_natural_prevalence_official.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print("SUMMARY", summary, flush=True)


if __name__ == "__main__":
    main()
