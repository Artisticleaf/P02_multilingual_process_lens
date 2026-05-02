#!/usr/bin/env python3
"""Build E134 trigger-window audit sheet from E132/E133 scored rows."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "data/processed/e132_suspicious_valid_controls_20260430.jsonl"
OUT = PROJECT / "data/processed/e134_trigger_window_audit_sheet_20260430.jsonl"
SUMMARY = PROJECT / "results/E134_trigger_window_audit/e134_trigger_window_audit_summary.json"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT))
    except ValueError:
        return str(path)


def preliminary_label(scored: dict[str, Any], source: dict[str, Any], triggered: bool) -> str:
    if scored["stage"] == "suspicion_marker_end":
        return "marker_only_prefix_control_not_policy_trigger"
    if not triggered:
        return "not_triggered_context"
    if source["manual_process_valid_strict"]:
        if source["variant"] in {"suspicious_valid_marker", "suspicious_valid_alternative", "low_conf_valid"}:
            return "false_trigger_suspicious_valid_candidate"
        return "false_trigger_clean_valid_candidate"
    if scored["stage"] in {"error_span_end", "first_claim_end", "post_error_240chars"}:
        return "true_error_near_error_candidate"
    if scored["stage"] in {"repair_or_contrast_marker_end", "completion_end"}:
        return "strict_invalid_after_repair_or_completion_candidate"
    return "true_error_candidate"


def build_window(text: str, char_end: int, radius: int) -> dict[str, Any]:
    start = max(0, char_end - radius)
    end = min(len(text), char_end + radius)
    return {
        "window_start": start,
        "window_end": end,
        "window_text": text[start:end],
        "window_left": text[start:char_end],
        "window_right": text[char_end:end],
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--scored-json", required=True, nargs="+")
    p.add_argument("--data-jsonl", default=str(DATA))
    p.add_argument("--out-jsonl", default=str(OUT))
    p.add_argument("--summary-json", default=str(SUMMARY))
    p.add_argument("--threshold", type=float, default=0.0)
    p.add_argument("--radius", type=int, default=240)
    p.add_argument("--include-near-threshold", action="store_true")
    p.add_argument("--near-threshold-abs", type=float, default=0.25)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    source_by_id = {int(r["audit_idx"]): r for r in load_jsonl(Path(args.data_jsonl))}
    audit_rows: list[dict[str, Any]] = []
    source_paths = []
    for scored_path_text in args.scored_json:
        scored_path = Path(scored_path_text)
        source_paths.append(rel(scored_path))
        scored_doc = json.loads(scored_path.read_text(encoding="utf-8"))
        for row in scored_doc["rows"]:
            score = float(row["best_component_score"])
            triggered = score < args.threshold
            near = abs(score - args.threshold) <= args.near_threshold_abs
            if not triggered and not (args.include_near_threshold and near):
                continue
            source = source_by_id[int(row["audit_idx"])]
            window = build_window(source["completion"], int(row["char_end"]), args.radius)
            audit_rows.append(
                {
                    "e134_audit_idx": 1340000 + len(audit_rows),
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                    "model_key": scored_doc["model_key"],
                    "source_audit_idx": int(row["audit_idx"]),
                    "source_task_name": row["source_task_name"],
                    "task_id": row["task_id"],
                    "family": row["family"],
                    "route_id": row["route_id"],
                    "variant": row["variant"],
                    "stage": row["stage"],
                    "detector": row["detector"],
                    "manual_process_valid_strict": row["manual_process_valid_strict"],
                    "manual_acpi_strict": row["manual_acpi_strict"],
                    "manual_error_span": row.get("manual_error_span"),
                    "best_component_key": row["best_component_key"],
                    "best_component_score": score,
                    "hidden_triggered": triggered,
                    "policy_trigger_eligible": row["stage"] != "suspicion_marker_end",
                    "near_threshold": near,
                    "strict_yes_minus_no": row["strict_yes_minus_no"],
                    "strict_readout_confidence": row["strict_readout_confidence"],
                    "plain_yes_minus_no": row["plain_yes_minus_no"],
                    "plain_readout_confidence": row["plain_readout_confidence"],
                    "preliminary_label": preliminary_label(row, source, triggered),
                    "problem": source["problem"],
                    "span_text": row.get("span_text", ""),
                    **window,
                    "manual_review_status": "needs_human_or_agent_audit",
                    "manual_review_questions_zh": [
                        "该窗口附近是否存在真实过程错误？",
                        "如果没有错误，触发是否只是犹豫/低置信/检查词导致？",
                        "如果有错误，trace 是否在后文显式修复？",
                        "模型是否表现出发现风险但没有行动的模式？",
                    ],
                }
            )
    out = Path(args.out_jsonl)
    write_jsonl(out, audit_rows)
    summary = {
        "experiment": "E134_trigger_window_audit",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_scored_json": source_paths,
        "out_jsonl": rel(out),
        "rows": len(audit_rows),
        "threshold": args.threshold,
        "radius": args.radius,
        "by_variant": dict(Counter(r["variant"] for r in audit_rows)),
        "by_stage": dict(Counter(r["stage"] for r in audit_rows)),
        "by_preliminary_label": dict(Counter(r["preliminary_label"] for r in audit_rows)),
        "note_zh": "E134 是窗口审计表，不把人工标签写回模型 prompt。preliminary_label 只用于审计排序，不是最终人工结论。",
    }
    summary_path = Path(args.summary_json)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
