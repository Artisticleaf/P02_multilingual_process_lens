#!/usr/bin/env python3
"""E51: split hard-task outcomes by final-answer parser strictness.

This is an analysis-only script. It does not alter E49 completions. It helps
separate three bottlenecks:
1) strict trace-selection format (`Final answer:` line),
2) benchmark-style boxed answer, and
3) very loose tail-number diagnostics.
"""
from __future__ import annotations

import json
import re
import socket
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
E49_DIR = PROJECT / "results/E49_hard_task_conditioning_official"
OUT_DIR = PROJECT / "results/E51_hard_task_parser_split"
REPORT = PROJECT / "reports/E51_HARD_TASK_PARSER_SPLIT_20260428.md"


def normalize_int(text: str) -> str:
    text = text.strip().lower()
    text = text.replace("$", "").replace("\\", "")
    text = re.sub(r"\s+", "", text)
    text = text.rstrip(".。,:;，；")
    if re.fullmatch(r"-?\d+\.0+", text):
        return str(int(float(text)))
    m = re.fullmatch(r"-?\d+", text)
    return m.group(0) if m else text


def strict_final(text: str) -> tuple[str, bool]:
    matches = list(re.finditer(r"^\s*final\s*answer\s*[:：]\s*([^\n]+)", text, flags=re.IGNORECASE | re.MULTILINE))
    if matches:
        return matches[-1].group(1).strip(), True
    return "", False


def boxed_answers(text: str) -> list[str]:
    vals = []
    # Simple non-nested boxed extraction is enough for current logs.
    for m in re.finditer(r"\\boxed\s*\{([^{}]{1,60})\}", text):
        nums = re.findall(r"-?\d+", m.group(1))
        if nums:
            vals.append(nums[-1])
    return vals


def tail_int(text: str) -> str:
    nums = re.findall(r"-?\d+", text[-700:])
    return nums[-1] if nums else ""


def file_backend(data: dict[str, Any], path: Path) -> str:
    if data.get("backend"):
        return str(data["backend"])
    if "vllm" in path.name:
        return "vllm"
    return "hf"


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    buckets = defaultdict(Counter)
    for r in rows:
        keys = [
            ("overall", "all"),
            ("model", r["model_key"]),
            ("model_gold", f"{r['model_key']}|gold={r['gold_answer_in_prompt']}"),
            ("variant", r["prompt_variant"]),
        ]
        for group_name, key in keys:
            b = buckets[(group_name, key)]
            b["n"] += 1
            b["gold_answer_in_prompt"] += int(r["gold_answer_in_prompt"])
            b["strict_correct"] += int(r["strict_correct"])
            b["boxed_correct"] += int(r["boxed_correct"])
            b["strict_or_boxed_correct"] += int(r["strict_or_boxed_correct"])
            b["loose_tail_correct"] += int(r["loose_tail_correct"])
            b["strict_marker_found"] += int(r["strict_marker_found"])
            b["boxed_found"] += int(bool(r["boxed_candidates"]))
    out = {}
    for (group_name, key), c in sorted(buckets.items()):
        out.setdefault(group_name, {})[key] = dict(c)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(E49_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        backend = file_backend(data, path)
        for idx, row in enumerate(data.get("rows", [])):
            text = row.get("completion", "")
            strict, marker = strict_final(text)
            boxes = boxed_answers(text)
            loose = tail_int(text)
            gold = normalize_int(row["gold_answer"])
            strict_norm = normalize_int(strict)
            boxed_norms = [normalize_int(x) for x in boxes]
            loose_norm = normalize_int(loose)
            rows.append(
                {
                    "source_file": str(path.relative_to(PROJECT)),
                    "row_index": idx,
                    "backend": backend,
                    "model_key": row.get("model_key", data.get("model_key", "unknown")),
                    "task_id": row["task_id"],
                    "prompt_variant": row["prompt_variant"],
                    "gold_answer_in_prompt": bool(row.get("gold_answer_in_prompt", False)),
                    "gold_answer": row["gold_answer"],
                    "strict_extracted": strict,
                    "strict_marker_found": marker,
                    "strict_correct": strict_norm == gold,
                    "boxed_candidates": boxes,
                    "boxed_correct": any(x == gold for x in boxed_norms),
                    "strict_or_boxed_correct": strict_norm == gold or any(x == gold for x in boxed_norms),
                    "loose_tail_int": loose,
                    "loose_tail_correct": loose_norm == gold,
                    "scope_note_en": "Rows with gold_answer_in_prompt=True are answer-anchor diagnostics, not natural prevalence.",
                    "scope_note_zh": "gold_answer_in_prompt=True 的行是 answer-anchor 诊断，不是自然发生率。",
                }
            )
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "host": socket.gethostname(),
        "rows": rows,
        "summary": summarize(rows),
        "notes_en": [
            "Strict parser counts only line-start `Final answer:` outputs.",
            "Boxed parser approximates benchmark-style answer extraction and should not be mixed with trace-selection strict-format results.",
            "Loose tail-number match is diagnostic only and can be contaminated by intermediate arithmetic.",
        ],
        "notes_zh": [
            "strict parser 只计算行首 `Final answer:` 输出。",
            "boxed parser 近似 benchmark-style 答案抽取，不能与 trace-selection strict-format 结果混用。",
            "loose tail-number 只是诊断，可能被中间计算数字污染。",
        ],
    }
    out = OUT_DIR / "e51_hard_task_parser_split_20260428.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    overall = result["summary"].get("overall", {}).get("all", {})
    model_lines = []
    for key, c in result["summary"].get("model_gold", {}).items():
        model, gold_flag = key.split("|gold=")
        model_lines.append(
            f"| `{model}` | {gold_flag} | {c['n']} | {c['strict_correct']} | {c['boxed_correct']} | {c['strict_or_boxed_correct']} | {c['loose_tail_correct']} |"
        )
    report = "\n".join(
        [
            "# E51 Hard-Task Parser Split / 困难题解析器分流（2026-04-28）",
            "",
            "## Plain-language conclusion / 说人话结论",
            "",
            "- Strict `Final answer:` extraction remains the trace-selection format criterion. / strict `Final answer:` 仍是 trace-selection 格式标准。",
            "- Boxed extraction tests whether a model solved the benchmark-style problem but ignored our final-line format. / boxed 抽取用于检查模型是否做出了 benchmark-style 答案但没按 final-line 输出。",
            "- Loose tail-number matching is only a debugging diagnostic. / tail-number 只用于排错诊断。",
            "",
            "## Overall / 总体",
            "",
            f"- Rows / 行数: {overall.get('n', 0)}",
            f"- Strict correct / strict 正确: {overall.get('strict_correct', 0)}",
            f"- Boxed correct / boxed 正确: {overall.get('boxed_correct', 0)}",
            f"- Strict-or-boxed correct / strict 或 boxed 正确: {overall.get('strict_or_boxed_correct', 0)}",
            f"- Loose tail correct / tail 诊断正确: {overall.get('loose_tail_correct', 0)}",
            "",
            "## By model and gold-in-prompt / 按模型与是否含 gold 分组",
            "",
            "| Model / 模型 | Gold in prompt / prompt 含 gold | n | Strict correct | Boxed correct | Strict or boxed | Loose tail correct |",
            "|---|---:|---:|---:|---:|---:|---:|",
            *model_lines,
            "",
            "## Interpretation / 解释",
            "",
            "- If boxed correctness is high but strict correctness is low, the bottleneck is output formatting. / 如果 boxed 高但 strict 低，瓶颈是输出格式。",
            "- If both are low, the bottleneck is final-correct trace acquisition. / 如果两者都低，瓶颈是先获得答案正确 trace。",
            "- Current result should guide hard-task next steps: separate benchmark solving from trace-selection formatting. / 当前结果说明后续困难题必须把 benchmark 解题与 trace-selection 格式分开。",
            "",
            f"JSON result / JSON 结果: `{out.relative_to(PROJECT)}`",
            "",
        ]
    )
    REPORT.write_text(report, encoding="utf-8")
    print(json.dumps({"out": str(out), "report": str(REPORT), "overall": overall}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
