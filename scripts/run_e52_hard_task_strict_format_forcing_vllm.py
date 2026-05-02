#!/usr/bin/env python3
"""E52: hard-task strict-format forcing with vLLM.

This experiment targets the E51 bottleneck: Qwen2.5-Math sometimes gives a
benchmark-style boxed answer on AIME-style tasks, but does not obey the
trace-selection `Final answer:` line contract.  E52 keeps gold answers out of
the prompt and tests whether stronger output contracts can convert
benchmark-style correctness into auditable strict-final traces.
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


PROMPT_VARIANTS = {
    "strict_contract": (
        "Solve the following AIME-style problem. Follow this output contract exactly:\n"
        "1. Give concise reasoning.\n"
        "2. Do not use \\boxed{{}} or boxed notation anywhere.\n"
        "3. The last non-empty line must be exactly `Final answer: <integer>`.\n"
        "4. Do not write any text after the final-answer line.\n\n"
        "Problem: {problem}"
    ),
    "format_guard": (
        "Solve the following AIME-style problem. The scientific evaluator only accepts a line that starts with "
        "`Final answer:`; it rejects \\boxed{{}}, 'the answer is', and missing final lines. "
        "Use enough reasoning to justify the result, then finish with one final line in this exact form:\n"
        "Final answer: <integer>\n\n"
        "Problem: {problem}"
    ),
    "first_and_last": (
        "Solve the following AIME-style problem yourself; no answer is provided. "
        "First write your best answer on one line as `Final answer: <integer>`. "
        "Then give a concise derivation. End by repeating the same line `Final answer: <integer>`. "
        "Never use \\boxed{{}}.\n\n"
        "Problem: {problem}"
    ),
    "short_solution": (
        "Give a short solution to the following AIME-style problem in at most 12 lines. "
        "Avoid boxed notation. The final line must be the only line beginning with `Final answer:` "
        "and must contain only the integer answer after the colon.\n\n"
        "Problem: {problem}"
    ),
}


def normalize_int(text: str) -> str:
    text = text.strip().lower()
    text = text.replace("$", "").replace("\\", "")
    text = re.sub(r"\s+", "", text)
    text = text.rstrip(".。,:;，；")
    if re.fullmatch(r"-?\d+\.0+", text):
        return str(int(float(text)))
    m = re.search(r"-?\d+", text)
    return m.group(0) if m else text


def strict_final(text: str) -> tuple[str, bool, bool, int]:
    matches = list(re.finditer(r"^\s*final\s*answer\s*[:：]\s*([^\n]+)", text, flags=re.IGNORECASE | re.MULTILINE))
    if not matches:
        return "", False, False, 0
    extracted = matches[-1].group(1).strip()
    nonempty = [line.strip() for line in text.splitlines() if line.strip()]
    last_is_final = bool(nonempty and re.match(r"^final\s*answer\s*[:：]", nonempty[-1], flags=re.IGNORECASE))
    return extracted, True, last_is_final, len(matches)


def boxed_answers(text: str) -> list[str]:
    vals = []
    for m in re.finditer(r"\\boxed\s*\{([^{}]{1,80})\}", text):
        nums = re.findall(r"-?\d+", m.group(1))
        if nums:
            vals.append(nums[-1])
    return vals


def tail_int(text: str) -> str:
    nums = re.findall(r"-?\d+", text[-700:])
    return nums[-1] if nums else ""


def should_use_chat(spec: dict[str, Any], tokenizer) -> bool:
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return bool(getattr(tokenizer, "chat_template", None)) and (
        fam in {"qwen", "qwen25_math", "qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls
    )


def render_prompt(tokenizer, spec: dict[str, Any], content: str) -> tuple[dict[str, list[int]], bool]:
    use_chat = should_use_chat(spec, tokenizer)
    if use_chat:
        messages = [{"role": "user", "content": content}]
        try:
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=True)
        except TypeError:
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        token_ids = tokenizer.encode(text, add_special_tokens=False)
    else:
        text = content + "\nReasoning:"
        token_ids = tokenizer.encode(text, add_special_tokens=True)
    return {"prompt_token_ids": token_ids}, use_chat


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    buckets = defaultdict(Counter)
    for row in rows:
        keys = [
            ("overall", "all"),
            ("variant", row["prompt_variant"]),
            ("task", row["task_id"]),
        ]
        for group, key in keys:
            b = buckets[(group, key)]
            b["n"] += 1
            b["strict_marker_found"] += int(row["strict_marker_found"])
            b["strict_last_line"] += int(row["strict_last_line"])
            b["strict_correct"] += int(row["strict_correct"])
            b["boxed_found"] += int(bool(row["boxed_candidates"]))
            b["boxed_correct"] += int(row["boxed_correct"])
            b["strict_or_boxed_correct"] += int(row["strict_or_boxed_correct"])
            b["loose_tail_correct"] += int(row["loose_tail_correct"])
            b["finished_stop"] += int(row.get("finish_reason") == "stop")
            b["finished_length"] += int(row.get("finish_reason") == "length")
    return {g: {k: dict(c) for k, c in sorted(v.items())} for g, v in _nest_buckets(buckets).items()}


def _nest_buckets(buckets: dict[tuple[str, str], Counter]) -> dict[str, dict[str, Counter]]:
    nested: dict[str, dict[str, Counter]] = defaultdict(dict)
    for (group, key), counter in sorted(buckets.items()):
        nested[group][key] = counter
    return nested


def write_report(out_json: Path, result: dict[str, Any]) -> Path:
    out_report = PROJECT / "reports/E52_HARD_TASK_STRICT_FORMAT_FORCING_20260428.md"
    overall = result["summary"].get("overall", {}).get("all", {})
    variant_lines = []
    for variant, c in result["summary"].get("variant", {}).items():
        variant_lines.append(
            f"| `{variant}` | {c['n']} | {c['strict_marker_found']} | {c['strict_last_line']} | "
            f"{c['strict_correct']} | {c['boxed_correct']} | {c['strict_or_boxed_correct']} | {c['loose_tail_correct']} | {c['finished_length']} |"
        )
    task_lines = []
    for task_id, c in result["summary"].get("task", {}).items():
        task_lines.append(
            f"| `{task_id}` | {c['n']} | {c['strict_correct']} | {c['boxed_correct']} | "
            f"{c['strict_or_boxed_correct']} | {c['loose_tail_correct']} |"
        )

    report = "\n".join(
        [
            "# E52 Hard-Task Strict-Format Forcing / 困难题严格格式强制（2026-04-28）",
            "",
            "## Purpose / 实验目的",
            "",
            "- E51 found that hard-task strict `Final answer:` correctness was zero, while Qwen2.5-Math had some benchmark-style `\\boxed{}` correctness. / E51 发现困难题 strict `Final answer:` 正确为 0，但 Qwen2.5-Math 有少量 benchmark-style `\\boxed{}` 正确。",
            "- E52 tests whether stronger no-gold output contracts can turn solved hard-task traces into strict trace-selection candidates. / E52 测试更强的、无 gold 的输出契约能否把已解出的困难题转成 strict trace-selection 候选。",
            "",
            "## Overall / 总体",
            "",
            f"- Rows / 行数: {overall.get('n', 0)}",
            f"- Strict marker found / 找到 strict 标记: {overall.get('strict_marker_found', 0)}",
            f"- Strict last-line compliant / strict 且位于最后一行: {overall.get('strict_last_line', 0)}",
            f"- Strict correct / strict 正确: {overall.get('strict_correct', 0)}",
            f"- Boxed correct / boxed 正确: {overall.get('boxed_correct', 0)}",
            f"- Strict-or-boxed correct / strict 或 boxed 正确: {overall.get('strict_or_boxed_correct', 0)}",
            f"- Length-truncated / 因长度停止: {overall.get('finished_length', 0)}",
            "",
            "## By prompt variant / 按 prompt 变体",
            "",
            "| Variant / 变体 | n | Marker | Last-line | Strict correct | Boxed correct | Strict or boxed | Loose tail correct | Length stop |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            *variant_lines,
            "",
            "## By task / 按题目",
            "",
            "| Task / 题目 | n | Strict correct | Boxed correct | Strict or boxed | Loose tail correct |",
            "|---|---:|---:|---:|---:|---:|",
            *task_lines,
            "",
            "## Interpretation stub / 解释占位",
            "",
            "- This report is generated immediately after decoding. Rows counted as strict-correct still require manual process audit before they can be used as answer-correct/process-invalid evidence. / 本报告在解码后立即生成；strict-correct 行仍需人工过程审计，才能作为答案正确但过程无效的证据。",
            "- Boxed and loose-tail correctness remain diagnostics, not official trace-selection success criteria. / boxed 和 loose-tail 仍只是诊断，不是官方 trace-selection 成功标准。",
            "",
            f"JSON result / JSON 结果: `{out_json.relative_to(PROJECT)}`",
            "",
        ]
    )
    out_report.write_text(report, encoding="utf-8")
    return out_report


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", default="qwen25_math_7b_instruct")
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--tasks-yaml", default=str(PROJECT / "configs/e26_aime_hard_tasks.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E52_hard_task_strict_format_forcing"))
    p.add_argument("--variants", nargs="+", default=list(PROMPT_VARIANTS))
    p.add_argument("--k", type=int, default=4)
    p.add_argument("--max-tasks", type=int, default=6)
    p.add_argument("--max-new-tokens", type=int, default=2048)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--top-k", type=int, default=50)
    p.add_argument("--tensor-parallel-size", type=int, default=4)
    p.add_argument("--gpu-memory-utilization", type=float, default=0.88)
    p.add_argument("--max-model-len", type=int, default=4096)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--seed", type=int, default=20260428)
    p.add_argument("--enforce-eager", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    if not is_local_model(spec):
        raise SystemExit(f"Model is not local; refusing network load for official run: {args.model_key}")
    unknown = sorted(set(args.variants) - set(PROMPT_VARIANTS))
    if unknown:
        raise SystemExit(f"Unknown variants: {unknown}")

    tokenizer = load_tokenizer(spec["path"], local_files_only=True)
    tasks = read_yaml(args.tasks_yaml)["tasks"][: args.max_tasks]
    prompt_inputs = []
    jobs = []
    for task in tasks:
        for variant in args.variants:
            content = PROMPT_VARIANTS[variant].format(problem=task["en"])
            prompt_input, used_chat = render_prompt(tokenizer, spec, content)
            prompt_inputs.append(prompt_input)
            jobs.append(
                {
                    "task": task,
                    "prompt_variant": variant,
                    "prompt_content": content,
                    "used_chat_template": used_chat,
                    "prompt_tokens": len(prompt_input["prompt_token_ids"]),
                }
            )

    started = datetime.now().isoformat(timespec="seconds")
    print(
        f"[{started}] E52 vLLM loading {args.model_key} prompts={len(prompt_inputs)} k={args.k} tp={args.tensor_parallel_size}",
        flush=True,
    )
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
        task = job["task"]
        gold = normalize_int(task["answer"])
        for sample_idx, item in enumerate(request_output.outputs):
            completion = item.text.strip()
            strict_value, marker, last_line, marker_count = strict_final(completion)
            boxes = boxed_answers(completion)
            loose = tail_int(completion)
            strict_norm = normalize_int(strict_value)
            boxed_norms = [normalize_int(x) for x in boxes]
            loose_norm = normalize_int(loose)
            strict_correct = strict_norm == gold
            boxed_correct = any(x == gold for x in boxed_norms)
            rows.append(
                {
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                    "backend": "vllm",
                    "model_key": args.model_key,
                    "task_id": task["id"],
                    "problem": task["en"],
                    "gold_answer": task["answer"],
                    "trap_note_not_in_prompt": task.get("trap", ""),
                    "prompt_variant": job["prompt_variant"],
                    "prompt_content_no_gold": job["prompt_content"],
                    "sample_idx": sample_idx,
                    "used_chat_template": job["used_chat_template"],
                    "prompt_tokens": job["prompt_tokens"],
                    "gold_answer_in_prompt": False,
                    "known_trap_note_in_prompt": False,
                    "completion": completion,
                    "finish_reason": getattr(item, "finish_reason", None),
                    "stop_reason": getattr(item, "stop_reason", None),
                    "output_tokens": len(getattr(item, "token_ids", []) or []),
                    "strict_extracted": strict_value,
                    "strict_marker_found": marker,
                    "strict_marker_count": marker_count,
                    "strict_last_line": last_line,
                    "strict_correct": strict_correct,
                    "boxed_candidates": boxes,
                    "boxed_correct": boxed_correct,
                    "strict_or_boxed_correct": strict_correct or boxed_correct,
                    "loose_tail_int": loose,
                    "loose_tail_correct": loose_norm == gold,
                    "manual_process_valid": None,
                    "manual_risk": "strict_final_correct_needs_manual_process_audit" if strict_correct else "not_strict_final_correct",
                    "is_acpi": False,
                    "scope_note_en": "No gold answer or trap note is included in the prompt; boxed/tail correctness are diagnostics only.",
                    "scope_note_zh": "prompt 中不含 gold answer 或 trap note；boxed/tail 正确只作诊断。",
                }
            )

    out_dir = Path(args.out_dir)
    out = out_dir / f"{args.model_key}_e52_hard_task_strict_format_forcing.json"
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
        "prompt_variants": PROMPT_VARIANTS,
        "summary": summarize(rows),
        "rows": rows,
        "notes_en": [
            "Gold answers are not present in the prompts.",
            "Strict correctness counts only line-start `Final answer:` extraction.",
            "Boxed and loose-tail parsers are diagnostics for benchmark-style solving and must not be mixed with strict trace-selection results.",
        ],
        "notes_zh": [
            "prompt 中不包含 gold answer。",
            "strict correctness 只计算行首 `Final answer:` 抽取。",
            "boxed 与 loose-tail parser 只是 benchmark-style 解题诊断，不能与 strict trace-selection 结果混用。",
        ],
    }
    write_json(out, result)
    report = write_report(out, result)
    print(json.dumps({"out": str(out), "report": str(report), "summary": result["summary"].get("overall", {})}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
