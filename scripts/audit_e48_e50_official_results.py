#!/usr/bin/env python3
"""Audit official E48/E49/E50 results for leakage and known logic risks."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]

E48_DIR = PROJECT / "results/E48_natural_prevalence_official"
E49_DIR = PROJECT / "results/E49_hard_task_conditioning_official"
E48_FILES = sorted(E48_DIR.glob("*_e48_natural_prevalence_official.json")) + sorted(E48_DIR.glob("*_e48_vllm_official_generation.json"))
E49_NOGOLD_FILES = sorted(E49_DIR.glob("*neutral_answer_first_no_gold_self_check*_hard_task_conditioning.json"))
E49_NOGOLD_FILES += sorted(E49_DIR.glob("*_e49_vllm_official_generation.json"))
E50_FILES = sorted((PROJECT / "results/E50_residual_probe_steering").glob("*_e50_residual_probe_steering.json"))
BACKEND_REQUIRED = [
    PROJECT / "reports/APPENDIX_BACKEND_COMPATIBILITY_AND_THROUGHPUT_20260428.md",
    PROJECT / "scripts/check_backend_compatibility.py",
    PROJECT / "logs/backend_compat_environment_project_pythonpath_20260428.json",
    PROJECT / "logs/backend_compat_local_model_configs_20260428.json",
    PROJECT / "logs/backend_compat_qwen35_9b_vllm_auto_20260428.json",
    PROJECT / "logs/backend_compat_qwen35_9b_vllm_transformers_20260428.json",
    PROJECT / "logs/backend_compat_gemma4_e4b_it_vllm_auto_20260428.json",
]
QUARANTINED_EXPECTED = [
    PROJECT / "archive/logic_error_quarantine_20260428/gemma4_26b_a4b_it_e48_false_positive_round_4p6.json",
    PROJECT / "archive/logic_error_quarantine_20260428/qwen35_9b_e50_residual_probe_steering.json",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def check_e48(path: Path) -> dict:
    item = {"path": str(path), "exists": path.exists(), "ok": False, "issues": []}
    if not path.exists():
        item["issues"].append("missing")
        return item
    data = read_json(path)
    rows = data.get("rows", [])
    summary = data.get("summary", {})
    if summary.get("gold_answer_in_prompt_rows") != 0:
        item["issues"].append("summary_gold_answer_in_prompt_nonzero")
    if summary.get("known_error_span_in_prompt_rows") != 0:
        item["issues"].append("summary_known_error_span_in_prompt_nonzero")
    for idx, row in enumerate(rows):
        if row.get("gold_answer_in_prompt"):
            item["issues"].append(f"row_{idx}_gold_answer_in_prompt")
        if row.get("known_error_span_in_prompt"):
            item["issues"].append(f"row_{idx}_known_error_span_in_prompt")
        if "prompt" in row:
            item["issues"].append(f"row_{idx}_stores_prompt_unexpectedly")
    item["n"] = len(rows)
    item["final_correct"] = summary.get("final_correct")
    item["acpi"] = summary.get("process_invalid_final_correct")
    item["ok"] = not item["issues"]
    return item


def check_e49_nogold(path: Path) -> dict:
    item = {"path": str(path), "exists": path.exists(), "ok": False, "issues": []}
    if not path.exists():
        item["issues"].append("missing")
        return item
    data = read_json(path)
    rows = data.get("rows", [])
    summary = data.get("summary", {})
    if summary.get("gold_answer_in_prompt_rows", 0) != 0:
        item["issues"].append("summary_gold_answer_in_prompt_nonzero")
    if summary.get("known_trap_note_in_prompt_rows", 0) != 0:
        item["issues"].append("summary_known_trap_note_in_prompt_nonzero")
    for idx, row in enumerate(rows):
        if row.get("gold_answer_in_prompt"):
            item["issues"].append(f"row_{idx}_gold_answer_in_prompt")
        if row.get("known_trap_note_in_prompt"):
            item["issues"].append(f"row_{idx}_known_trap_note_in_prompt")
    item["n"] = len(rows)
    item["final_correct"] = summary.get("final_correct")
    item["strict_final_marker_missing"] = summary.get("strict_final_marker_missing")
    item["ok"] = not item["issues"]
    return item


def check_e50(path: Path) -> dict:
    item = {"path": str(path), "exists": path.exists(), "ok": False, "issues": []}
    if not path.exists():
        item["issues"].append("missing")
        return item
    data = read_json(path)
    rows = data.get("rows", [])
    pairs = {}
    for row in rows:
        pairs.setdefault(row.get("task_id"), []).append(row.get("e39_variant"))
    for task_id, variants in pairs.items():
        if sorted(variants) != ["invalid_correct", "valid_correct"]:
            item["issues"].append(f"bad_pair_{task_id}_{variants}")
    args = data.get("args", {})
    if args.get("manual_jsonl") and "e42_e39_objective_focus" not in str(args.get("manual_jsonl")):
        item["issues"].append("unexpected_manual_jsonl")
    summary = data.get("summary", {})
    if not summary.get("best_probe_layer"):
        item["issues"].append("missing_best_probe_layer")
    if "scope_note_zh" not in data:
        item["issues"].append("missing_chinese_scope_note")
    item["n_rows"] = len(rows)
    item["best_probe_layer"] = summary.get("best_probe_layer")
    item["ok"] = not item["issues"]
    return item


def main() -> None:
    checks = {
        "e48": [check_e48(p) for p in E48_FILES],
        "e49_no_gold": [check_e49_nogold(p) for p in E49_NOGOLD_FILES],
        "e50": [check_e50(p) for p in E50_FILES],
        "backend_required": [{"path": str(p), "exists": p.exists(), "ok": p.exists()} for p in BACKEND_REQUIRED],
        "quarantine_expected": [{"path": str(p), "exists": p.exists(), "ok": p.exists()} for p in QUARANTINED_EXPECTED],
    }
    issues = []
    for group, items in checks.items():
        for item in items:
            if not item.get("ok"):
                issues.append({"group": group, "path": item.get("path"), "issues": item.get("issues", ["not_ok"])})
    out = {"passed": not issues, "issues": issues, "checks": checks}
    out_path = PROJECT / "logs/audit_e48_e50_official_results_20260428.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": out["passed"], "issues": issues, "out": str(out_path)}, ensure_ascii=False, indent=2))
    if issues:
        sys.exit(1)


if __name__ == "__main__":
    main()
