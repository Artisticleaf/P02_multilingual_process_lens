#!/usr/bin/env python3
"""Static audit for E166 hidden-monitor prefix bank."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
PREFIX_PATH = PROJECT / "data/processed/e166_hardened_monitor_prefix_points_20260502.jsonl"
SOL_PATH = PROJECT / "data/processed/e164_hardened_multi_family_candidate_solutions_20260501.jsonl"
OUT_JSON = PROJECT / "reports/E166_HARDENED_MONITOR_PREFIX_STATIC_AUDIT_20260502.json"
OUT_MD = PROJECT / "reports/E166_HARDENED_MONITOR_PREFIX_STATIC_AUDIT_20260502.md"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# E166 Hidden-Monitor Prefix Bank Static Audit / E166 hidden monitor prefix 库静态审计",
        "",
        "Date / 日期：2026-05-02",
        "",
        f"- Passed / 通过：{result['passed']}",
        f"- Prefix points / prefix 点：{result['prefix_points']}",
        f"- Monitor targets / 监测目标点：{result['monitor_targets']}",
        f"- Valid control points / 正确过程控制点：{result['valid_control_points']}",
        "",
        "## Design Meaning / 设计含义",
        "",
        "- This bank is for hidden monitor calibration, not generation. / 这个库用于 hidden monitor 校准，不是生成结果。",
        "- Future hidden replay prompts may use only `problem` and `prefix_text`. / 后续 hidden replay prompt 只能使用 `problem` 和 `prefix_text`。",
        "- Manual error spans and gold answers are offline metadata for evaluation only. / 人工错步和答案只作离线评价元数据。",
        "- `monitor_target=true` marks exact manual error-span ends in invalid traces, used for calibration/audit. / `monitor_target=true` 是 invalid trace 中人工错步结束点，用于校准和审计。",
        "",
        "## Counts / 计数",
        "",
    ]
    for key in ["families", "trace_classes", "boundary_kinds"]:
        lines.append(f"### {key}")
        for k, v in result[key].items():
            lines.append(f"- `{k}`: {v}")
        lines.append("")
    if result["issues"]:
        lines.extend(["## Issues / 问题", ""])
        for issue in result["issues"][:100]:
            lines.append(f"- `{issue.get('prefix_id') or issue.get('solution_id') or issue.get('task_id')}`: {issue['issue']}")
    return "\n".join(lines)


def main() -> None:
    rows = load_jsonl(PREFIX_PATH)
    sols = load_jsonl(SOL_PATH)
    sol_by_id = {s["solution_id"]: s for s in sols}
    issues: list[dict[str, Any]] = []

    if not rows:
        issues.append({"issue": "empty_prefix_bank"})
    by_solution = defaultdict(list)
    for row in rows:
        by_solution[row["solution_id"]].append(row)
        sol = sol_by_id.get(row["solution_id"])
        if sol is None:
            issues.append({"prefix_id": row["prefix_id"], "issue": "missing_source_solution"})
            continue
        if not row.get("prefix_text"):
            issues.append({"prefix_id": row["prefix_id"], "issue": "empty_prefix_text"})
        if "Final answer:" in row.get("prefix_text", ""):
            issues.append({"prefix_id": row["prefix_id"], "issue": "prefix_contains_final_answer"})
        if row.get("prefix_text") not in sol["candidate_solution"]:
            issues.append({"prefix_id": row["prefix_id"], "issue": "prefix_not_substring_of_source_trace"})
        if row.get("visible_span") and row["visible_span"] not in row["prefix_text"]:
            issues.append({"prefix_id": row["prefix_id"], "issue": "visible_span_not_in_prefix"})
        for flag in ["gold_answer_in_prompt_by_design", "manual_error_span_in_prompt_by_design", "manual_label_in_prompt_by_design"]:
            if row.get(flag):
                issues.append({"prefix_id": row["prefix_id"], "issue": f"leakage_flag_true::{flag}"})
        if row["prompt_fields_allowed_for_hidden_replay"] != ["problem", "prefix_text"]:
            issues.append({"prefix_id": row["prefix_id"], "issue": "bad_allowed_prompt_fields"})
        if row["trace_valid_strict"] and row["monitor_target"]:
            issues.append({"prefix_id": row["prefix_id"], "issue": "valid_trace_marked_monitor_target"})
        if row["monitor_target"]:
            span = row.get("manual_error_span_offline") or ""
            if not span:
                issues.append({"prefix_id": row["prefix_id"], "issue": "monitor_target_missing_manual_span"})
            if not row["exact_manual_error_span_end"]:
                issues.append({"prefix_id": row["prefix_id"], "issue": "monitor_target_not_exact_span_end"})
            if span and not row["prefix_text"].endswith(span):
                issues.append({"prefix_id": row["prefix_id"], "issue": "monitor_target_prefix_not_ending_with_span"})

    for sol in sols:
        rows_for_sol = by_solution.get(sol["solution_id"], [])
        if not rows_for_sol:
            issues.append({"solution_id": sol["solution_id"], "issue": "solution_has_no_prefix_points"})
        if not sol["manual_process_valid_strict"]:
            targets = [r for r in rows_for_sol if r["monitor_target"]]
            if len(targets) != 1:
                issues.append({"solution_id": sol["solution_id"], "issue": "invalid_solution_expected_one_monitor_target", "got": len(targets)})
        else:
            if any(r["monitor_target"] for r in rows_for_sol):
                issues.append({"solution_id": sol["solution_id"], "issue": "valid_solution_has_monitor_target"})

    result = {
        "passed": not issues,
        "issues": issues,
        "prefix_points": len(rows),
        "solutions": len(by_solution),
        "tasks": len({r["task_id"] for r in rows}),
        "families": dict(sorted(Counter(r["family"] for r in rows).items())),
        "trace_classes": dict(sorted(Counter(r["trace_class"] for r in rows).items())),
        "boundary_kinds": dict(sorted(Counter(r["boundary_kind"] for r in rows).items())),
        "monitor_targets": sum(int(r["monitor_target"]) for r in rows),
        "valid_control_points": sum(int(r["trace_valid_strict"]) for r in rows),
        "invalid_non_target_points": sum(int((not r["trace_valid_strict"]) and (not r["monitor_target"])) for r in rows),
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
