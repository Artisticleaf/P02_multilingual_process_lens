#!/usr/bin/env python3
"""Render the first E170 thinking-only prompt for static inspection."""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
TASK_BANK = PROJECT / "data/processed/e164_hardened_multi_family_tasks_20260501.jsonl"
OUT = PROJECT / "reports/E170_THINKING_ONLY_PROMPT_SMOKE_20260502.md"

TEMPLATE = (
    "Solve the following problem carefully. Show the reasoning needed to justify the result. "
    "Do not give the final answer before the reasoning. End with exactly one line `Final answer: <answer>`.\n\n"
    "Problem: {problem}"
)


def main() -> None:
    first = None
    for line in TASK_BANK.read_text(encoding="utf-8").splitlines():
        if line.strip():
            first = json.loads(line)
            break
    if first is None:
        raise RuntimeError("empty task bank")
    content = TEMPLATE.format(problem=first["problem"])
    offline_leakage_fields = {
        "answer_preserving_trap_type": str(first.get("answer_preserving_trap_type", "")),
        "hardening_note_zh": str(first.get("hardening_note_zh", "")),
    }
    leakage_hits = {key: value for key, value in offline_leakage_fields.items() if value and value in content}
    lines = [
        "# E170 Thinking-Only Prompt Smoke / E170 thinking-only prompt smoke",
        "",
        f"- task_id: `{first['task_id']}`",
        f"- family: `{first['family']}`",
        f"- prompt_variant: `thinking_only_template`",
        f"- leakage_hits_from_offline_non_problem_fields: `{leakage_hits}`",
        f"- gold_answer_string_occurs_in_problem_text: `{str(first['gold_answer']) in first['problem']}`",
        "",
        "## Rendered Prompt / 渲染 prompt",
        "",
        "```text",
        content,
        "```",
        "",
        "## Boundary / 边界",
        "",
        "- This prompt contains only the original problem and the generic solve template. / prompt 只包含原题和通用解题模板。",
        "- It contains no repair prefix, no localized span, no random span, no oracle hint, and no candidate trace. / 不包含修复 prefix、localized span、random span、oracle hint 或候选过程。",
        "- The gold answer string may appear as an ordinary number in the problem text; that is not counted as answer leakage for original-problem solving. / 答案字符串可能作为普通题干数字出现；原题解答中这不算答案泄漏。",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
