#!/usr/bin/env python3
"""Render one E167 hidden-derived repair prompt for static inspection."""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
CASE_BANK = PROJECT / "data/processed/e167_hidden_derived_repair_cases_20260502.jsonl"
OUT = PROJECT / "reports/E167_HIDDEN_DERIVED_PROMPT_SMOKE_20260502.md"


PROMPTS = {
    "prefix_continue": (
        "Continue the partial solution below. Do not restart unless the partial solution itself requires revision. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
    "hidden_generic_warning": (
        "A hidden monitor raised a low-confidence warning somewhere in the partial solution below. "
        "Recheck the partial solution from the original problem, correct it if needed, and continue. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
    "hidden_localized_warning": (
        "A hidden monitor flagged this visible span as potentially abnormal: `{localized_span}`. "
        "{localized_hint} Correct the local step if needed, then continue. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
    "random_matched_warning": (
        "A hidden monitor flagged this visible span as potentially abnormal: `{random_span}`. "
        "Recheck only that location first; avoid changing unrelated correct steps. Then continue. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
    "oracle_manual_span": (
        "A hidden monitor flagged this visible span as abnormal: `{manual_span}`. "
        "Audit note: {oracle_hint} Correct the local step if needed, then continue. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
}


def load_first() -> dict:
    for line in CASE_BANK.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["hidden_policy"] == "high_precision" and not row["source_process_valid_strict"]:
            return row
    raise RuntimeError("No high_precision invalid E167 row found")


def render(row: dict, variant: str) -> str:
    return PROMPTS[variant].format(
        problem=row["problem"],
        prefix=row["prefix_text"],
        localized_span=row["localized_span"],
        localized_hint=row["localized_hint"],
        random_span=row["random_location_span"],
        manual_span=row["manual_error_span"],
        oracle_hint=row["oracle_hint"],
    )


def main() -> None:
    row = load_first()
    lines = [
        "# E167 Hidden-Derived Prompt Smoke / E167 hidden-derived prompt smoke",
        "",
        "## Selected Case / 抽样样本",
        "",
        f"- case_id: `{row['case_id']}`",
        f"- model_key_for_hidden_monitor: `{row['model_key_for_hidden_monitor']}`",
        f"- policy: `{row['hidden_policy']}`",
        f"- hidden_component_key: `{row['hidden_component_key']}`",
        f"- hidden_trigger_source: `{row['hidden_trigger_source']}`",
        f"- hidden_trigger_boundary_kind: `{row['hidden_trigger_boundary_kind']}`",
        f"- hidden_trigger_is_manual_target_offline: `{row['hidden_trigger_is_manual_target_offline']}`",
        f"- hidden_trigger_candidate_policy: `{row['hidden_trigger_candidate_policy']}`",
        f"- localized_span_used_by_non_oracle_prompt: `{row['localized_span']}`",
        "",
        "## Leakage Boundary / 泄漏边界",
        "",
        "- Non-oracle prompts use the hidden-derived `localized_span`, not `manual_error_span`. / 非 oracle prompt 使用 hidden-derived span，不使用人工 span。",
        "- The hidden trigger is selected from automatic boundaries only; manual error-span endpoints are excluded from trigger candidates. / hidden 触发点只从自动边界里选，人工错步末尾不进入候选集合。",
        "- Gold answer and manual labels are not included in any rendered prompt. / 答案和人工标签不进入任何 prompt。",
        "- `oracle_manual_span` is an upper-bound condition and may expose the offline manual span/hint. / oracle 条件是上界，可以暴露人工 span/hint。",
        "",
    ]
    for variant in PROMPTS:
        content = render(row, variant)
        lines.extend([f"## {variant}", "", "```text", content, "```", ""])
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
