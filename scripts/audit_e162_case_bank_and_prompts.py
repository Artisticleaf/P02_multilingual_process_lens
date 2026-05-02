#!/usr/bin/env python3
"""Static audit for E162 cases and prompt contents."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import run_e162_low_confidence_error_prompt_repair as e162  # noqa: E402

CASE_BANK = PROJECT / "data/processed/e162_low_confidence_error_prompt_cases_20260501.jsonl"
OUT = PROJECT / "reports/E162_LOW_CONFIDENCE_ERROR_PROMPT_STATIC_AUDIT_20260501.json"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--case-bank", default=str(CASE_BANK))
    p.add_argument("--out", default=str(OUT))
    p.add_argument("--variants", nargs="+", default=list(e162.PROMPT_VARIANTS))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_jsonl(Path(args.case_bank))
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
        for variant in args.variants:
            content = e162.render_content(row, variant)
            prompt_rows += 1
            forbidden = ["gold_answer", "manual_process_valid", "manual_error_type", "manual_has_error"]
            for token in forbidden:
                if token in content:
                    issues.append({"case_id": row.get("case_id"), "variant": variant, "issue": f"prompt_contains_metadata_token::{token}"})
            if variant != "baseline_regenerate" and row.get("source_trace") in content:
                issues.append({"case_id": row.get("case_id"), "variant": variant, "issue": "prompt_contains_full_source_trace"})
            if variant != "baseline_regenerate" and "Final answer:" in row.get("prefix_text", ""):
                issues.append({"case_id": row.get("case_id"), "variant": variant, "issue": "prompt_prefix_contains_final_answer"})
            if variant == "oracle_error_prompt" and str(row.get("gold_answer")) in row.get("oracle_hint", ""):
                issues.append({"case_id": row.get("case_id"), "variant": variant, "issue": "oracle_hint_contains_gold_answer_literal"})
    result = {
        "case_count": len(rows),
        "prompt_rows_checked": prompt_rows,
        "issues": issues,
        "passed": not issues,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
