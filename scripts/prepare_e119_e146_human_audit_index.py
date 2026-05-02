#!/usr/bin/env python3
"""Prepare a compact risk index for human process audit of E119/E146 rows."""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]

INPUTS = [
    ("E119_uniform_legacy", PROJECT / "data/processed/e119_natural_hardtask_final_correct_audit_sheet_20260430.jsonl"),
    ("E146_model_card_hf", PROJECT / "data/processed/e146_qwen_gemma_model_card_final_correct_audit_sheet_20260430.jsonl"),
]

OUT_JSONL = PROJECT / "data/processed/e119_e146_human_process_audit_index_20260430.jsonl"
OUT_SUMMARY = PROJECT / "results/E119_E146_human_process_audit/e119_e146_human_process_audit_index_summary.json"


REPAIR_RE = re.compile(
    r"\b(wait|however|actually|correction|correct|mistake|wrong|recheck|let me|instead|but|on second thought|i need to revise|revised)\b",
    flags=re.I,
)
FINAL_LINE_RE = re.compile(r"^\s*final\s*answer\s*[:：]\s*([^\n]+)", flags=re.I | re.M)
BOXED_RE = re.compile(r"\\boxed\s*\{\s*(-?\d+(?:\.\d+)?)\s*\}", flags=re.I)

RISK_PATTERNS = {
    "integer_wrong_factor_plus_xy": re.compile(r"\(3x\s*-\s*2y\)\s*\(4x\s*\+\s*3y\)|\(4x\s*\+\s*3y\)\s*\(3x\s*-\s*2y\)", re.I),
    "integer_wrong_factor_alt": re.compile(r"\(4x\s*\+\s*y\)\s*\(3x\s*-\s*y\)|\(3x\s*-\s*y\)\s*\(4x\s*\+\s*y\)", re.I),
    "icecream_missing_531_hint": re.compile(r"only valid triples?[^\\n]{0,200}\(6,\s*2,\s*1\)[^\\n]{0,200}\(4,\s*3,\s*2\)", re.I),
    "geometry_self_intersect_concern": re.compile(r"self[- ]intersect|shoelace|signed area|algebraic area|winding", re.I),
    "perm_suspicious_41472": re.compile(r"41472|39447|2919|919", re.I),
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def numbers_after_final(text: str) -> list[str]:
    vals = [m.group(1).strip() for m in FINAL_LINE_RE.finditer(text)]
    vals.extend(m.group(1).strip() for m in BOXED_RE.finditer(text))
    return vals


def risk_flags(row: dict[str, Any]) -> dict[str, Any]:
    text = row.get("completion", "")
    finals = numbers_after_final(text)
    flags: dict[str, Any] = {
        "hit_max": bool(row.get("hit_max_new_tokens")),
        "missing_strict_marker": not bool(row.get("strict_final_marker_found")),
        "repair_marker_count": len(REPAIR_RE.findall(text)),
        "final_marker_values": finals,
        "distinct_final_marker_values": sorted(set(finals)),
        "multiple_distinct_finals": len(set(finals)) > 1,
        "completion_chars": len(text),
        "generated_tokens": row.get("generated_tokens"),
    }
    for name, pat in RISK_PATTERNS.items():
        flags[name] = bool(pat.search(text))
    task = row.get("task_id", "")
    flags["high_risk_task"] = task in {"aime25_geometry_reflection_p2", "aime25_integer_pairs_quad_p4", "aime25_perm_div22_p5"}
    flags["risk_score"] = (
        int(flags["hit_max"]) * 2
        + int(flags["missing_strict_marker"]) * 2
        + int(flags["multiple_distinct_finals"]) * 3
        + min(int(flags["repair_marker_count"]), 5)
        + sum(int(flags[k]) * 3 for k in RISK_PATTERNS)
        + int(flags["high_risk_task"])
    )
    return flags


def audit_index(row: dict[str, Any]) -> int | None:
    for key in ("e119_audit_idx", "e146_audit_idx", "audit_idx"):
        val = row.get(key)
        if val is not None:
            return val
    return None


def main() -> None:
    rows = []
    for run_id, path in INPUTS:
        for row in load_jsonl(path):
            flags = risk_flags(row)
            rows.append(
                {
                    "run_id": run_id,
                    "audit_idx": audit_index(row),
                    "source_file": row.get("source_file"),
                    "source_row_index": row.get("source_row_index"),
                    "model_key": row.get("model_key"),
                    "task_id": row.get("task_id"),
                    "prompt_variant": row.get("prompt_variant"),
                    "sample_idx": row.get("sample_idx"),
                    "gold_answer": row.get("gold_answer"),
                    "strict_extracted_final": row.get("strict_extracted_final"),
                    "fallback_extracted_final": row.get("fallback_extracted_final"),
                    "strict_final_correct": row.get("strict_final_correct"),
                    "fallback_final_correct": row.get("fallback_final_correct"),
                    "flags": flags,
                    "snippet_head": row.get("completion", "")[:900],
                    "snippet_tail": row.get("completion", "")[-900:],
                }
            )
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    by_run = defaultdict(Counter)
    by_task = defaultdict(Counter)
    by_model = defaultdict(Counter)
    for r in rows:
        f = r["flags"]
        for bucket in (by_run[r["run_id"]], by_task[r["task_id"]], by_model[r["model_key"]]):
            bucket["n"] += 1
            bucket["hit_max"] += int(f["hit_max"])
            bucket["missing_strict_marker"] += int(f["missing_strict_marker"])
            bucket["multiple_distinct_finals"] += int(f["multiple_distinct_finals"])
            bucket["repair_marker_any"] += int(f["repair_marker_count"] > 0)
            bucket["risk_score_ge_6"] += int(f["risk_score"] >= 6)
    summary = {
        "rows": len(rows),
        "out_jsonl": str(OUT_JSONL.relative_to(PROJECT)),
        "by_run": {k: dict(v) for k, v in sorted(by_run.items())},
        "by_task": {k: dict(v) for k, v in sorted(by_task.items())},
        "by_model": {k: dict(v) for k, v in sorted(by_model.items())},
        "top_risk": [
            {
                "run_id": r["run_id"],
                "audit_idx": r["audit_idx"],
                "model_key": r["model_key"],
                "task_id": r["task_id"],
                "prompt_variant": r["prompt_variant"],
                "risk_score": r["flags"]["risk_score"],
                "flags": {k: v for k, v in r["flags"].items() if k != "final_marker_values"},
            }
            for r in sorted(rows, key=lambda x: x["flags"]["risk_score"], reverse=True)[:30]
        ],
    }
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
