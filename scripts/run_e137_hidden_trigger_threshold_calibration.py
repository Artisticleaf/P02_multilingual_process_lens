#!/usr/bin/env python3
"""E137 hidden-trigger threshold calibration on E132/E133 rows.

This is an offline calibration step. It uses existing E132/E133 hidden scores
and manual labels only for evaluation. It does not load a model and does not
feed labels/spans/gold answers to prompts.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
E132_DIR = PROJECT / "results/E132_E133_suspicious_confidence_probe"
OUT_DIR = PROJECT / "results/E137_hidden_trigger_threshold_calibration"

MODELS = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"]
EXCLUDED_STAGES = {"completion_end", "suspicion_marker_end"}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT))
    except ValueError:
        return str(path)


def wilson(k: int, n: int, z: float = 1.96) -> list[float | None]:
    if n <= 0:
        return [None, None]
    phat = k / n
    den = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / den
    half = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n) / den
    return [center - half, center + half]


def source_path(model_key: str, root: Path) -> Path:
    path = root / f"{model_key}_e132_e133_all_chat.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def load_rows(model_key: str, root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = source_path(model_key, root)
    obj = json.loads(path.read_text(encoding="utf-8"))
    return obj, list(obj["rows"])


def candidate_thresholds(scores: list[float]) -> list[float]:
    if not scores:
        return [0.0]
    vals = sorted(set(float(x) for x in scores))
    mids: list[float] = [vals[0] - 1e-6]
    mids.extend((a + b) / 2 for a, b in zip(vals, vals[1:]))
    mids.append(vals[-1] + 1e-6)
    if 0.0 not in mids:
        mids.append(0.0)
    return sorted(set(mids))


def trace_rows(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    out = {}
    for row in rows:
        if row.get("stage") == "completion_end":
            out[int(row["audit_idx"])] = row
    return out


def prefix_rows_by_trace(rows: list[dict[str, Any]], include_suspicion_marker: bool) -> dict[int, list[dict[str, Any]]]:
    excluded = {"completion_end"}
    if not include_suspicion_marker:
        excluded.add("suspicion_marker_end")
    by_idx: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if str(row.get("stage")) in excluded:
            continue
        by_idx[int(row["audit_idx"])].append(row)
    for idx in by_idx:
        by_idx[idx].sort(key=lambda r: (int(r.get("char_end") or 0), str(r.get("stage", ""))))
    return by_idx


def trace_score(prefixes: list[dict[str, Any]], mode: str) -> float:
    vals = [float(r["best_component_score"]) for r in prefixes]
    if not vals:
        return float("inf")
    if mode == "min_prefix":
        return min(vals)
    if mode == "first_prefix":
        return vals[0]
    if mode == "completion":
        raise ValueError("completion handled separately")
    raise ValueError(mode)


def class_name(row: dict[str, Any]) -> str:
    if bool(row.get("manual_process_valid_strict")):
        variant = str(row.get("variant", ""))
        if variant.startswith("suspicious_valid"):
            return "suspicious_valid"
        if variant == "low_conf_valid":
            return "low_conf_valid"
        return "clean_or_other_valid"
    if bool(row.get("manual_repair_present")):
        return "repaired_strict_invalid"
    if bool(row.get("manual_acpi_unrepaired")):
        return "unrepaired_acpi"
    return "strict_invalid"


def evaluate_threshold(records: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    total = len(records)
    valid = [r for r in records if r["label_valid"]]
    invalid = [r for r in records if not r["label_valid"]]
    suspicious = [r for r in valid if r["class"] == "suspicious_valid"]
    low_conf = [r for r in valid if r["class"] == "low_conf_valid"]
    triggered = [r for r in records if r["score"] < threshold]
    inv_tr = [r for r in invalid if r["score"] < threshold]
    val_tr = [r for r in valid if r["score"] < threshold]
    susp_tr = [r for r in suspicious if r["score"] < threshold]
    low_tr = [r for r in low_conf if r["score"] < threshold]
    precision = len(inv_tr) / len(triggered) if triggered else None
    return {
        "threshold": threshold,
        "n": total,
        "trigger_n": len(triggered),
        "trigger_rate": len(triggered) / total if total else None,
        "invalid_n": len(invalid),
        "invalid_trigger_n": len(inv_tr),
        "invalid_recall": len(inv_tr) / len(invalid) if invalid else None,
        "valid_n": len(valid),
        "valid_trigger_n": len(val_tr),
        "valid_false_trigger_rate": len(val_tr) / len(valid) if valid else None,
        "suspicious_valid_n": len(suspicious),
        "suspicious_valid_trigger_n": len(susp_tr),
        "suspicious_valid_false_trigger_rate": len(susp_tr) / len(suspicious) if suspicious else None,
        "low_conf_valid_n": len(low_conf),
        "low_conf_valid_trigger_n": len(low_tr),
        "low_conf_valid_false_trigger_rate": len(low_tr) / len(low_conf) if low_conf else None,
        "precision_invalid_among_triggered": precision,
        "f1_invalid": (2 * precision * (len(inv_tr) / len(invalid)) / (precision + (len(inv_tr) / len(invalid)))) if precision is not None and invalid and (precision + len(inv_tr) / len(invalid)) > 0 else None,
        "valid_false_trigger_ci": wilson(len(val_tr), len(valid)),
        "invalid_recall_ci": wilson(len(inv_tr), len(invalid)),
    }


def pick_threshold(evals: list[dict[str, Any]], min_recall: float, max_valid_fp: float, max_suspicious_fp: float) -> dict[str, Any]:
    feasible = [
        e for e in evals
        if e["invalid_recall"] is not None
        and e["valid_false_trigger_rate"] is not None
        and e["suspicious_valid_false_trigger_rate"] is not None
        and e["invalid_recall"] >= min_recall
        and e["valid_false_trigger_rate"] <= max_valid_fp
        and e["suspicious_valid_false_trigger_rate"] <= max_suspicious_fp
    ]
    if feasible:
        return max(feasible, key=lambda e: (e["invalid_recall"], -(e["valid_false_trigger_rate"] or 0), -(e["trigger_rate"] or 0), -(abs(e["threshold"])))) | {"selection_rule": "feasible_min_recall_max_fp"}
    return max(evals, key=lambda e: ((e["f1_invalid"] or -1), -(e["valid_false_trigger_rate"] or 0), e["invalid_recall"] or 0)) | {"selection_rule": "best_f1_no_feasible_threshold"}


def make_records(rows: list[dict[str, Any]], score_mode: str, include_suspicion_marker: bool) -> list[dict[str, Any]]:
    completion = trace_rows(rows)
    prefixes = prefix_rows_by_trace(rows, include_suspicion_marker=include_suspicion_marker)
    records: list[dict[str, Any]] = []
    for idx, comp in sorted(completion.items()):
        if score_mode == "completion":
            score = float(comp["best_component_score"])
            trigger_stage = "completion_end"
            trigger_span = comp.get("span_text", "")
        else:
            prs = prefixes.get(idx, [])
            score = trace_score(prs, score_mode)
            chosen = min(prs, key=lambda r: float(r["best_component_score"])) if prs else None
            trigger_stage = chosen.get("stage") if chosen else None
            trigger_span = chosen.get("span_text") if chosen else ""
        records.append({
            "audit_idx": idx,
            "score": score,
            "trigger_stage_at_min": trigger_stage,
            "trigger_span_at_min": trigger_span,
            "label_valid": bool(comp["manual_process_valid_strict"]),
            "class": class_name(comp),
            "variant": comp.get("variant"),
            "family": comp.get("family"),
            "route_id": comp.get("route_id"),
            "task_id": comp.get("task_id"),
            "strict_yes_minus_no": comp.get("strict_yes_minus_no"),
            "plain_yes_minus_no": comp.get("plain_yes_minus_no"),
            "suspicion_marker_count": comp.get("suspicion_marker_count", 0),
        })
    return records


def summarize_scores(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        groups["all"].append(r)
        groups[f"class={r['class']}"].append(r)
        groups[f"variant={r.get('variant')}"] .append(r)
        groups[f"route={r.get('route_id')}"] .append(r)
        groups[f"family={r.get('family')}"] .append(r)
    out = []
    for key, vals in sorted(groups.items()):
        scores = [float(v["score"]) for v in vals if math.isfinite(float(v["score"]))]
        out.append({
            "slice": key,
            "n": len(vals),
            "mean_score": mean(scores) if scores else None,
            "min_score": min(scores) if scores else None,
            "max_score": max(scores) if scores else None,
            "trigger_at_zero_rate": sum(v["score"] < 0 for v in vals) / len(vals),
        })
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--models", default=",".join(MODELS))
    p.add_argument("--e132-dir", default=str(E132_DIR))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--score-mode", choices=["min_prefix", "completion", "first_prefix"], default="min_prefix")
    p.add_argument("--include-suspicion-marker", action="store_true")
    p.add_argument("--min-recall", type=float, default=0.95)
    p.add_argument("--max-valid-fp", type=float, default=0.05)
    p.add_argument("--max-suspicious-fp", type=float, default=0.05)
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    result: dict[str, Any] = {
        "experiment": "E137_hidden_trigger_threshold_calibration",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "args": vars(args),
        "models": {},
        "scope_note_zh": "E137 是离线阈值校准：使用 E132/E133 已有 hidden scores 和人工标签评估触发阈值，不加载模型，不把标签/答案/span 输入 prompt。",
    }
    for model in models:
        source, rows = load_rows(model, Path(args.e132_dir))
        records = make_records(rows, args.score_mode, args.include_suspicion_marker)
        scores = [r["score"] for r in records if math.isfinite(r["score"])]
        evals = [evaluate_threshold(records, t) for t in candidate_thresholds(scores)]
        chosen = pick_threshold(evals, args.min_recall, args.max_valid_fp, args.max_suspicious_fp)
        zero = evaluate_threshold(records, 0.0)
        result["models"][model] = {
            "source": rel(source_path(model, Path(args.e132_dir))),
            "source_best_component_key": source.get("best_component_key"),
            "source_best_hidden_layer": source.get("best_hidden_layer"),
            "records": records,
            "score_summary": summarize_scores(records),
            "threshold_evaluations": evals,
            "threshold_at_zero": zero,
            "chosen_threshold": chosen,
            "class_counts": dict(Counter(r["class"] for r in records)),
        }
        print(json.dumps({"model": model, "zero": zero, "chosen": chosen}, ensure_ascii=False), flush=True)

    out = out_dir / "e137_hidden_trigger_threshold_calibration.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": rel(out), "models": models}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
