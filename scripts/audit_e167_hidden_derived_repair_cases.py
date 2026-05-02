#!/usr/bin/env python3
"""Static audit for E167 hidden-derived repair cases."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
CASE_BANK = PROJECT / "data/processed/e167_hidden_derived_repair_cases_20260502.jsonl"
OUT_JSON = PROJECT / "reports/E167_HIDDEN_DERIVED_REPAIR_CASES_STATIC_AUDIT_20260502.json"
OUT_MD = PROJECT / "reports/E167_HIDDEN_DERIVED_REPAIR_CASES_STATIC_AUDIT_20260502.md"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    rows = load_jsonl(CASE_BANK)
    issues: list[dict[str, Any]] = []
    for row in rows:
        cid = row.get("case_id")
        if row.get("manual_error_span_in_prompt_by_design"):
            issues.append({"case_id": cid, "issue": "manual_error_span_in_prompt_by_design"})
        if row.get("gold_answer_in_prompt_by_design"):
            issues.append({"case_id": cid, "issue": "gold_answer_in_prompt_by_design"})
        if row.get("manual_label_in_prompt_by_design"):
            issues.append({"case_id": cid, "issue": "manual_label_in_prompt_by_design"})
        if not row.get("hidden_span_in_prompt_by_design"):
            issues.append({"case_id": cid, "issue": "hidden_span_not_marked_for_prompt"})
        if row.get("localized_span") not in row.get("prefix_text", ""):
            issues.append({"case_id": cid, "issue": "localized_span_not_in_prefix"})
        if "Final answer:" in row.get("prefix_text", ""):
            issues.append({"case_id": cid, "issue": "prefix_contains_final_answer"})
        if not row.get("hidden_component_key"):
            issues.append({"case_id": cid, "issue": "missing_hidden_component_key"})
        if row.get("hidden_trigger_source") not in {"first_threshold_crossing", "fallback_top_risk_no_threshold_crossing"}:
            issues.append({"case_id": cid, "issue": "bad_hidden_trigger_source"})
        if row.get("hidden_trigger_source") == "fallback_top_risk_no_threshold_crossing" and row.get("source_process_valid_strict"):
            issues.append({"case_id": cid, "issue": "valid_case_uses_toprisk_fallback"})
        if row.get("random_location_span") != "Report only the requested value":
            issues.append({"case_id": cid, "issue": "random_span_not_neutral"})
        if row.get("hidden_trigger_boundary_kind") == "manual_error_span_end":
            issues.append({"case_id": cid, "issue": "manual_error_span_endpoint_used_as_hidden_trigger"})
        if row.get("hidden_trigger_is_manual_target_offline"):
            issues.append({"case_id": cid, "issue": "manual_target_used_as_hidden_trigger"})
        if row.get("hidden_trigger_candidate_policy") != "auto_boundary_only":
            issues.append({"case_id": cid, "issue": "hidden_trigger_candidate_policy_not_auto_boundary_only"})
        if not row.get("manual_error_span_end_excluded_from_trigger_candidates"):
            issues.append({"case_id": cid, "issue": "manual_error_span_end_not_marked_excluded"})

    result = {
        "passed": not issues,
        "cases": len(rows),
        "issues": issues,
        "by_model": dict(sorted(Counter(r["model_key_for_hidden_monitor"] for r in rows).items())),
        "by_policy": dict(sorted(Counter(r["hidden_policy"] for r in rows).items())),
        "by_case_type": dict(sorted(Counter(r["case_type"] for r in rows).items())),
        "hidden_trigger_sources": dict(sorted(Counter(r["hidden_trigger_source"] for r in rows).items())),
        "hidden_trigger_boundary_kinds": dict(sorted(Counter(r["hidden_trigger_boundary_kind"] for r in rows).items())),
        "manual_target_trigger_rows": sum(int(r["hidden_trigger_is_manual_target_offline"]) for r in rows),
        "offline_manual_span_equals_hidden_span_rows": sum(int(r["offline_manual_span_equals_hidden_span"]) for r in rows),
        "offline_hidden_span_contains_manual_span_rows": sum(int(r["offline_hidden_span_contains_manual_span"]) for r in rows),
        "offline_manual_span_contains_hidden_span_rows": sum(int(r["offline_manual_span_contains_hidden_span"]) for r in rows),
        "invalid_rows": sum(int(not r["source_process_valid_strict"]) for r in rows),
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# E167 Hidden-Derived Repair Case Static Audit / E167 hidden-derived 修复样本静态审计",
        "",
        f"- Passed / 通过：`{result['passed']}`.",
        f"- Cases / 样本数：{result['cases']}.",
        f"- By model / 按模型：`{result['by_model']}`.",
        f"- By policy / 按策略：`{result['by_policy']}`.",
        f"- Trigger sources / 触发来源：`{result['hidden_trigger_sources']}`.",
        f"- Trigger boundary kinds / hidden 触发边界类型：`{result['hidden_trigger_boundary_kinds']}`.",
        f"- Manual-target trigger rows / hidden 触发正好命中人工错步结束点：{result['manual_target_trigger_rows']}.",
        f"- Offline manual span equals hidden span rows / 离线人工 span 与 hidden span 完全相同：{result['offline_manual_span_equals_hidden_span_rows']}.",
        f"- Offline hidden span contains manual span rows / hidden span 包含人工 span：{result['offline_hidden_span_contains_manual_span_rows']}.",
        f"- Invalid rows / invalid trace rows：{result['invalid_rows']}.",
        "",
        "## Issues / 问题",
        "",
    ]
    if issues:
        for issue in issues[:100]:
            lines.append(f"- `{issue.get('case_id')}`: {issue.get('issue')}")
    else:
        lines.append("- None.")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
