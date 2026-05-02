#!/usr/bin/env python3
"""Prompt-only static audit for the E165 hardened repair cases.

This deliberately avoids importing model runners or torch. It checks that the
case bank can be rendered into the six E162/E165 repair prompt variants without
leaking offline labels, final answers, or full source traces.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
CASE_BANK = PROJECT / "data/processed/e165_hardened_multi_family_repair_cases_20260501.jsonl"
OUT = PROJECT / "reports/E165_HARDENED_MULTI_FAMILY_REPAIR_PROMPT_STATIC_AUDIT_20260501.json"

PROMPT_VARIANTS = {
    "baseline_regenerate": (
        "Solve the following problem carefully. Do not give the final answer before the reasoning. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}"
    ),
    "prefix_continue": (
        "Continue the partial solution below. Do not restart unless the partial solution itself requires revision. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
    "generic_error_prompt": (
        "A hidden monitor raised a low-confidence warning somewhere in the partial solution below. "
        "Recheck the partial solution from the original problem, correct it if needed, and continue. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
    "localized_error_prompt": (
        "A hidden monitor flagged this visible span as potentially abnormal: `{localized_span}`. "
        "{localized_hint} Correct the local step if needed, then continue. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
    "oracle_error_prompt": (
        "A hidden monitor flagged this visible span as abnormal: `{localized_span}`. "
        "Audit note: {oracle_hint} Correct the local step if needed, then continue. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
    "random_location_prompt": (
        "A hidden monitor flagged this visible span as potentially abnormal: `{random_span}`. "
        "Recheck only that location first; avoid changing unrelated correct steps. Then continue. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def render_content(row: dict[str, Any], variant: str) -> str:
    return PROMPT_VARIANTS[variant].format(
        problem=row["problem"],
        prefix=row["prefix_text"],
        localized_span=row.get("localized_span") or row.get("manual_error_span") or "NONE",
        localized_hint=row.get("localized_hint") or "",
        oracle_hint=row.get("oracle_hint") or "",
        random_span=row.get("random_location_span") or "NONE",
    )


def main() -> None:
    rows = load_jsonl(CASE_BANK)
    issues: list[dict[str, Any]] = []
    prompt_rows = 0
    for row in rows:
        if not row.get("prefix_text"):
            issues.append({"case_id": row.get("case_id"), "issue": "empty_prefix"})
        if "Final answer:" in row.get("prefix_text", ""):
            issues.append({"case_id": row.get("case_id"), "issue": "prefix_contains_final_answer"})
        if row.get("gold_answer_in_prompt_by_design"):
            issues.append({"case_id": row.get("case_id"), "issue": "gold_answer_in_prompt_by_design"})
        if row.get("manual_label_in_prompt_by_design"):
            issues.append({"case_id": row.get("case_id"), "issue": "manual_label_in_prompt_by_design"})
        if row.get("random_location_span") != "Report only the requested value":
            issues.append({"case_id": row.get("case_id"), "issue": "random_span_not_neutral"})
        if row.get("localized_span") not in row.get("prefix_text", ""):
            issues.append({"case_id": row.get("case_id"), "issue": "localized_span_not_in_prefix"})
        for variant in PROMPT_VARIANTS:
            content = render_content(row, variant)
            prompt_rows += 1
            forbidden_tokens = [
                "gold_answer",
                "manual_process_valid",
                "manual_error_type",
                "manual_has_error",
                "candidate_variant",
                "source_final_correct",
            ]
            for token in forbidden_tokens:
                if token in content:
                    issues.append({"case_id": row.get("case_id"), "variant": variant, "issue": f"prompt_contains_metadata_token::{token}"})
            if variant != "baseline_regenerate" and row.get("source_trace") in content:
                issues.append({"case_id": row.get("case_id"), "variant": variant, "issue": "prompt_contains_full_source_trace"})
            if variant in {"baseline_regenerate", "prefix_continue", "generic_error_prompt", "localized_error_prompt", "random_location_prompt"}:
                if str(row.get("gold_answer")) in row.get("localized_hint", ""):
                    issues.append({"case_id": row.get("case_id"), "variant": variant, "issue": "localized_hint_contains_gold_answer_literal"})
            if variant == "oracle_error_prompt" and str(row.get("gold_answer")) in row.get("oracle_hint", ""):
                issues.append({"case_id": row.get("case_id"), "variant": variant, "issue": "oracle_hint_contains_gold_answer_literal"})
    result = {
        "passed": not issues,
        "case_count": len(rows),
        "prompt_rows_checked": prompt_rows,
        "variants": list(PROMPT_VARIANTS),
        "issues": issues,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
