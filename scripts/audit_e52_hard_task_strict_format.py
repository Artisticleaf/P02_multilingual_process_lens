#!/usr/bin/env python3
"""Audit E52 hard-task strict-format forcing outputs."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
RAW = PROJECT / "results/E52_hard_task_strict_format_forcing/qwen25_math_7b_instruct_e52_hard_task_strict_format_forcing.json"
AUDIT = PROJECT / "results/E52_hard_task_strict_format_forcing/e52_manual_audit_20260428.json"
REPORT = PROJECT / "reports/E52_HARD_TASK_STRICT_FORMAT_FORCING_20260428.md"
OUT = PROJECT / "logs/audit_e52_hard_task_strict_format_20260428.json"


def normalize_int(text: str) -> str:
    text = text.strip().lower().replace("$", "").replace("\\", "")
    text = re.sub(r"\s+", "", text).rstrip(".。,:;，；")
    m = re.search(r"-?\d+", text)
    return m.group(0) if m else text


def recompute_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, int]]]:
    buckets = defaultdict(Counter)
    for row in rows:
        for group, key in [("overall", "all"), ("variant", row["prompt_variant"]), ("task", row["task_id"])]:
            b = buckets[(group, key)]
            b["n"] += 1
            b["strict_correct"] += int(row["strict_correct"])
            b["boxed_correct"] += int(row["boxed_correct"])
            b["strict_or_boxed_correct"] += int(row["strict_or_boxed_correct"])
            b["strict_marker_found"] += int(row["strict_marker_found"])
            b["strict_last_line"] += int(row["strict_last_line"])
    out: dict[str, dict[str, dict[str, int]]] = defaultdict(dict)
    for (group, key), c in buckets.items():
        out[group][key] = dict(c)
    return dict(out)


def main() -> None:
    issues = []
    checks: dict[str, Any] = {}
    for path in [RAW, AUDIT, REPORT]:
        checks[str(path.relative_to(PROJECT))] = {"exists": path.exists()}
        if not path.exists():
            issues.append(f"missing:{path.relative_to(PROJECT)}")
    if issues:
        OUT.write_text(json.dumps({"passed": False, "issues": issues, "checks": checks}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"passed": False, "issues": issues, "out": str(OUT)}, ensure_ascii=False, indent=2))
        sys.exit(1)

    raw = json.loads(RAW.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    rows = raw.get("rows", [])
    audit_rows = audit.get("rows", [])
    raw_counts = recompute_counts(rows)
    checks["shape"] = {
        "raw_rows": len(rows),
        "audit_rows": len(audit_rows),
        "raw_rows_expected": 96,
        "audit_rows_match": len(rows) == len(audit_rows),
        "ok": len(rows) == 96 and len(rows) == len(audit_rows),
    }
    if not checks["shape"]["ok"]:
        issues.append("shape")

    args = raw.get("args", {})
    checks["official_settings"] = {
        "model_key": raw.get("model_key"),
        "backend": raw.get("backend"),
        "tensor_parallel_size": raw.get("tensor_parallel_size"),
        "max_model_len": args.get("max_model_len"),
        "max_new_tokens": args.get("max_new_tokens"),
        "k": args.get("k"),
        "max_tasks": args.get("max_tasks"),
        "variants": args.get("variants"),
        "ok": raw.get("model_key") == "qwen25_math_7b_instruct"
        and raw.get("backend") == "vllm"
        and raw.get("tensor_parallel_size") == 4
        and args.get("max_model_len") == 4096
        and args.get("k") == 4
        and args.get("max_tasks") == 6
        and len(args.get("variants", [])) == 4,
    }
    if not checks["official_settings"]["ok"]:
        issues.append("official_settings")

    leak_issues = []
    for idx, row in enumerate(rows):
        prompt = row.get("prompt_content_no_gold", "")
        if row.get("gold_answer_in_prompt") or row.get("known_trap_note_in_prompt"):
            leak_issues.append(f"row {idx}: leak flag true")
        if re.search(r"given\s+final\s+answer\s*[:：]", prompt, flags=re.IGNORECASE):
            leak_issues.append(f"row {idx}: prompt contains Given final answer")
        if row.get("trap_note_not_in_prompt", "") and row["trap_note_not_in_prompt"] in prompt:
            leak_issues.append(f"row {idx}: trap note appears in prompt")
    checks["leakage"] = {"issues": leak_issues, "ok": not leak_issues}
    if leak_issues:
        issues.append("leakage")

    summary_all = raw.get("summary", {}).get("overall", {}).get("all", {})
    recomputed_all = raw_counts.get("overall", {}).get("all", {})
    checks["raw_summary"] = {
        "summary_all": summary_all,
        "recomputed_all": recomputed_all,
        "ok": all(summary_all.get(k) == recomputed_all.get(k) for k in ["n", "strict_correct", "boxed_correct", "strict_or_boxed_correct", "strict_marker_found", "strict_last_line"]),
    }
    if not checks["raw_summary"]["ok"]:
        issues.append("raw_summary")

    boxed_indices = [i for i, row in enumerate(rows) if row.get("boxed_correct")]
    audited_boxed_indices = [i for i, row in enumerate(audit_rows) if row.get("boxed_correct")]
    audit_summary = audit.get("summary", {}).get("overall", {}).get("all", {})
    checks["manual_audit"] = {
        "boxed_indices": boxed_indices,
        "audited_boxed_indices": audited_boxed_indices,
        "strict_correct": audit_summary.get("strict_correct"),
        "boxed_correct": audit_summary.get("boxed_correct"),
        "clear_process_invalid_boxed_correct": audit_summary.get("clear_process_invalid_boxed_correct"),
        "ambiguous_notational_collision_boxed_correct": audit_summary.get("ambiguous_notational_collision_boxed_correct"),
        "valid_boxed_only": audit_summary.get("valid_boxed_only"),
        "leak_check": audit.get("leak_check"),
        "ok": boxed_indices == audited_boxed_indices
        and audit_summary.get("strict_correct") == 0
        and audit_summary.get("boxed_correct") == 14
        and audit_summary.get("clear_process_invalid_boxed_correct") == 2
        and audit_summary.get("ambiguous_notational_collision_boxed_correct") == 6
        and audit_summary.get("valid_boxed_only") == 6
        and audit.get("leak_check", {}).get("passed") is True,
    }
    if not checks["manual_audit"]["ok"]:
        issues.append("manual_audit")

    # Verify boxed-correct rows are actually normalized-equal to the gold answer.
    boxed_norm_issues = []
    for idx in boxed_indices:
        row = rows[idx]
        gold = normalize_int(row["gold_answer"])
        if gold not in [normalize_int(x) for x in row.get("boxed_candidates", [])]:
            boxed_norm_issues.append(idx)
    checks["boxed_normalization"] = {"issues": boxed_norm_issues, "ok": not boxed_norm_issues}
    if boxed_norm_issues:
        issues.append("boxed_normalization")

    out = {"passed": not issues, "issues": issues, "checks": checks}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"passed": out["passed"], "issues": issues, "out": str(OUT)}, ensure_ascii=False, indent=2))
    if issues:
        sys.exit(1)


if __name__ == "__main__":
    main()
