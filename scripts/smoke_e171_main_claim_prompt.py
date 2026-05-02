#!/usr/bin/env python3
"""Render E171 first baseline prompt for static inspection."""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
TASK_BANK = PROJECT / "data/processed/e171_main_claim_task_bank_20260502.jsonl"
OUT = PROJECT / "reports/E171_MAIN_CLAIM_PROMPT_SMOKE_20260502.md"

BASELINE_TEMPLATE = (
    "Solve the following problem carefully. Show the reasoning needed to justify the result. "
    "Do not give the final answer before the reasoning. End with exactly one line `Final answer: <answer>`.\n\n"
    "Problem: {problem}"
)


def main() -> None:
    rows = [json.loads(line) for line in TASK_BANK.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise RuntimeError("empty E171 task bank")
    first = rows[0]
    content = BASELINE_TEMPLATE.format(problem=first["problem"])
    offline_fields = {
        "gold_answer": str(first.get("gold_answer", "")),
        "trap_note_offline": str(first.get("trap_note_offline", "")),
        "source_material": str(first.get("source_material", "")),
    }
    leakage_hits = {key: value for key, value in offline_fields.items() if value and value in content and key != "gold_answer"}
    lines = [
        "# E171 Main-Claim Prompt Smoke / E171 主 claim prompt smoke",
        "",
        f"- task_id: `{first['task_id']}`",
        f"- family: `{first['family']}`",
        f"- task_source: `{first['task_source']}`",
        f"- prompt_variant: `baseline_nonthinking_original_problem`",
        f"- offline_non_problem_leakage_hits: `{leakage_hits}`",
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
        "- This prompt contains only a generic solve instruction and the original problem. / prompt 只含通用解题指令和原题。",
        "- It contains no hidden score, no repair prefix, no localized span, no random span, no oracle hint, no trap note, and no gold answer field. / 不包含 hidden 分数、修复 prefix、localized span、random span、oracle hint、陷阱说明或答案字段。",
        "- If the gold answer string appears in the problem as an ordinary number, it is recorded separately and not treated as leakage. / 如果答案字符串作为普通题干数字出现，单独记录，不算泄漏。",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
