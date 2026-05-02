#!/usr/bin/env python3
"""Audit E153 non-thinking error-finding outputs.

The runner records the first ERROR line for simple online metrics.  This audit
also records the last ERROR line because several non-thinking completions
naturally revise their own judgment.  The first/last split is part of the
behavioral evidence, not only a parser detail.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
IN_DIR = PROJECT / "results/E153_nonthinking_error_finding"
OUT_JSONL = PROJECT / "data/processed/e153_error_finding_audit_20260501.jsonl"
OUT_SUMMARY = PROJECT / "results/E153_nonthinking_error_finding/e153_error_finding_audit_summary_20260501.json"
OUT_REPORT = PROJECT / "reports/E153_ERROR_FINDING_AUDIT_20260501.md"

ERROR_RE = re.compile(r"ERROR\s*[:：]\s*(Yes|No)", re.IGNORECASE)
LOCATION_RE = re.compile(r"LOCATION\s*[:：]\s*(.+)", re.IGNORECASE)

MODEL_ARCH = {
    "qwen35_27b": "dense",
    "gemma4_31b_it": "dense",
    "gemma4_26b_a4b_it": "moe",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().strip("\"'`")).lower()


def location_matches(location: str, error_span: str | None) -> bool:
    if not error_span:
        return False
    loc = norm(location)
    span = norm(error_span)
    if not loc or loc == "none" or not span:
        return False
    return span in loc or loc in span


def all_error_preds(text: str) -> list[bool]:
    return [m.group(1).lower() == "yes" for m in ERROR_RE.finditer(text)]


def all_locations(text: str) -> list[str]:
    return [m.group(1).strip() for m in LOCATION_RE.finditer(text)]


def audit_row(row: dict[str, Any], source_path: Path, idx: int) -> dict[str, Any]:
    errors = all_error_preds(row.get("completion", ""))
    locs = all_locations(row.get("completion", ""))
    first_pred = errors[0] if errors else None
    last_pred = errors[-1] if errors else None
    first_loc = locs[0] if locs else ""
    last_loc = locs[-1] if locs else ""
    manual_has_error = bool(row["manual_has_error"])
    first_correct = first_pred is not None and bool(first_pred) == manual_has_error
    last_correct = last_pred is not None and bool(last_pred) == manual_has_error
    first_loc_match = location_matches(first_loc, row.get("manual_error_span_offline"))
    last_loc_match = location_matches(last_loc, row.get("manual_error_span_offline"))
    candidate = row["candidate_variant"]

    return {
        "audit_created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "E153_error_finding_audit",
        "source_file": str(source_path.relative_to(PROJECT)),
        "source_row_index": idx,
        "model_key": row["model_key"],
        "model_architecture": MODEL_ARCH.get(row["model_key"], "unknown"),
        "task_id": row["task_id"],
        "family": row["family"],
        "solution_id": row["solution_id"],
        "candidate_variant": candidate,
        "prompt_variant": row["prompt_variant"],
        "manual_has_error": manual_has_error,
        "manual_error_span_offline": row.get("manual_error_span_offline") or "",
        "runner_pred_error_first": row.get("pred_error"),
        "runner_pred_correct_first": bool(row.get("pred_correct")),
        "first_pred_error": first_pred,
        "last_pred_error": last_pred,
        "first_pred_correct": first_correct,
        "last_pred_correct": last_correct,
        "first_location": first_loc,
        "last_location": last_loc,
        "first_location_matches_error_span": first_loc_match,
        "last_location_matches_error_span": last_loc_match,
        "error_line_count": len(errors),
        "location_line_count": len(locs),
        "error_judgment_flip": bool(len(errors) >= 2 and errors[0] != errors[-1]),
        "strict_single_error_line": len(errors) == 1,
        "hit_max_new_tokens": bool(row.get("hit_max_new_tokens")),
        "parse_ok_first": bool(row.get("parse_ok")),
        "parse_ok_last": last_pred is not None,
        "false_positive_valid_first": candidate == "valid_reference" and first_pred is True,
        "false_positive_valid_last": candidate == "valid_reference" and last_pred is True,
        "false_negative_invalid_first": candidate == "invalid_reference" and first_pred is False,
        "false_negative_invalid_last": candidate == "invalid_reference" and last_pred is False,
        "invalid_location_miss_first": candidate == "invalid_reference" and first_pred is True and not first_loc_match,
        "invalid_location_miss_last": candidate == "invalid_reference" and last_pred is True and not last_loc_match,
        "completion": row.get("completion", ""),
        "problem": row.get("problem", ""),
        "candidate_solution": row.get("candidate_solution", ""),
    }


def discover_files(in_dir: Path) -> list[Path]:
    return sorted(in_dir.glob("*_e153_find_problem_global_find_problem_localize_only_error_finding.json"))


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def bool_sum(vals: list[dict[str, Any]], key: str) -> int:
        return sum(bool(v.get(key)) for v in vals)

    by_slice: dict[str, dict[str, Any]] = {}
    slice_keys: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        for key in [
            "all::all",
            f"model::{r['model_key']}",
            f"architecture::{r['model_architecture']}",
            f"candidate::{r['candidate_variant']}",
            f"prompt::{r['prompt_variant']}",
            f"family::{r['family']}",
            f"model_candidate::{r['model_key']}::{r['candidate_variant']}",
            f"model_prompt::{r['model_key']}::{r['prompt_variant']}",
            f"model_family::{r['model_key']}::{r['family']}",
        ]:
            slice_keys[key].append(r)

    for key, vals in sorted(slice_keys.items()):
        invalid = [v for v in vals if v["candidate_variant"] == "invalid_reference"]
        valid = [v for v in vals if v["candidate_variant"] == "valid_reference"]
        by_slice[key] = {
            "n": len(vals),
            "first_pred_correct": bool_sum(vals, "first_pred_correct"),
            "last_pred_correct": bool_sum(vals, "last_pred_correct"),
            "error_judgment_flip": bool_sum(vals, "error_judgment_flip"),
            "hit_max": bool_sum(vals, "hit_max_new_tokens"),
            "valid_n": len(valid),
            "valid_false_positive_first": bool_sum(valid, "false_positive_valid_first"),
            "valid_false_positive_last": bool_sum(valid, "false_positive_valid_last"),
            "invalid_n": len(invalid),
            "invalid_false_negative_first": bool_sum(invalid, "false_negative_invalid_first"),
            "invalid_false_negative_last": bool_sum(invalid, "false_negative_invalid_last"),
            "invalid_location_match_first": bool_sum(invalid, "first_location_matches_error_span"),
            "invalid_location_match_last": bool_sum(invalid, "last_location_matches_error_span"),
            "invalid_location_miss_first": bool_sum(invalid, "invalid_location_miss_first"),
            "invalid_location_miss_last": bool_sum(invalid, "invalid_location_miss_last"),
        }

    by_model = {k.split("::", 1)[1]: v for k, v in by_slice.items() if k.startswith("model::")}
    cases = {
        "judgment_flips": select_cases(rows, lambda r: r["error_judgment_flip"], 20),
        "valid_false_positive_last": select_cases(rows, lambda r: r["false_positive_valid_last"], 20),
        "invalid_false_negative_last": select_cases(rows, lambda r: r["false_negative_invalid_last"], 20),
        "invalid_location_miss_last": select_cases(rows, lambda r: r["invalid_location_miss_last"], 20),
    }
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "rows": len(rows),
        "completed_models": sorted({r["model_key"] for r in rows}),
        "by_model": by_model,
        "by_slice": by_slice,
        "cases": cases,
        "field_meanings": {
            "first_pred_correct": "Metric used by the online runner: first ERROR line.",
            "last_pred_correct": "Post-hoc behavioral metric: last ERROR line, useful when the model self-corrects.",
            "error_judgment_flip": "The completion contains multiple ERROR lines with different Yes/No decisions.",
            "invalid_location_match_last": "Among invalid reference rows, whether the last LOCATION overlaps the offline human error span.",
        },
    }


def select_cases(rows: list[dict[str, Any]], pred, limit: int) -> list[dict[str, Any]]:
    out = []
    for r in rows:
        if pred(r):
            out.append(
                {
                    "model_key": r["model_key"],
                    "task_id": r["task_id"],
                    "family": r["family"],
                    "candidate_variant": r["candidate_variant"],
                    "prompt_variant": r["prompt_variant"],
                    "manual_has_error": r["manual_has_error"],
                    "first_pred_error": r["first_pred_error"],
                    "last_pred_error": r["last_pred_error"],
                    "first_location": r["first_location"],
                    "last_location": r["last_location"],
                    "manual_error_span_offline": r["manual_error_span_offline"],
                    "hit_max_new_tokens": r["hit_max_new_tokens"],
                    "completion_excerpt": r["completion"][:700],
                }
            )
            if len(out) >= limit:
                break
    return out


def write_report(summary: dict[str, Any]) -> None:
    lines = [
        "# E153 Error-Finding Audit / E153 找错审计",
        "",
        "Scope / 范围：completed E153 non-thinking error-finding files. This report separates first-`ERROR` parsing from last-`ERROR` parsing because some outputs naturally revise their own judgment.",
        "",
        "Definitions / 定义：",
        "- `first_pred_correct`: online runner metric; it uses the first `ERROR:` line.",
        "- `last_pred_correct`: post-hoc behavioral metric; it uses the last `ERROR:` line, useful when the model says one decision and then revises it.",
        "- `invalid_location_match_last`: for invalid reference traces, whether the last reported location overlaps the offline human error span.",
        "- `valid_false_positive_last`: for valid reference traces, whether the model still claims an error at the end.",
        "",
        "Model summary / 模型摘要：",
        "",
        "| model | rows | first correct | last correct | flips | valid false+ first | valid false+ last | invalid false- first | invalid false- last | invalid loc match last |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model, m in sorted(summary["by_model"].items()):
        lines.append(
            f"| {model} | {m['n']} | {m['first_pred_correct']} | {m['last_pred_correct']} | {m['error_judgment_flip']} | "
            f"{m['valid_false_positive_first']} | {m['valid_false_positive_last']} | {m['invalid_false_negative_first']} | "
            f"{m['invalid_false_negative_last']} | {m['invalid_location_match_last']}/{m['invalid_n']} |"
        )

    lines += [
        "",
        "Key interpretation / 关键解释：",
        "- Binary error detection and exact localization must be reported separately. A model can say `ERROR: Yes` while pointing to the wrong step.",
        "- First-vs-last differences are scientifically meaningful here: they expose non-thinking self-correction or judgment instability.",
        "- Valid-reference false positives are not noise to discard; they measure over-suspicion and can become control cases for hidden-trigger policies.",
        "",
        "Selected cases / 代表样本：",
    ]
    for label, cases in summary["cases"].items():
        lines.append(f"## {label}")
        if not cases:
            lines.append("- None.")
            continue
        for c in cases[:8]:
            excerpt = c["completion_excerpt"].replace("\n", " | ")
            if len(excerpt) > 360:
                excerpt = excerpt[:360] + "..."
            lines.append(
                f"- {c['model_key']} {c['task_id']} {c['prompt_variant']} {c['candidate_variant']}: "
                f"manual_error={c['manual_has_error']}, first={c['first_pred_error']}, last={c['last_pred_error']}, "
                f"loc=`{c['last_location']}`; excerpt: {excerpt}"
            )
    lines += [
        "",
        f"Artifacts / 产物：`{OUT_JSONL.relative_to(PROJECT)}`, `{OUT_SUMMARY.relative_to(PROJECT)}`.",
    ]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--in-dir", default=str(IN_DIR))
    p.add_argument("--out-jsonl", default=str(OUT_JSONL))
    p.add_argument("--out-summary", default=str(OUT_SUMMARY))
    p.add_argument("--out-report", default=str(OUT_REPORT))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    in_dir = Path(args.in_dir)
    files = discover_files(in_dir)
    audited: list[dict[str, Any]] = []
    for path in files:
        data = load_json(path)
        for idx, row in enumerate(data.get("rows", [])):
            audited.append(audit_row(row, path, idx))
    out_jsonl = Path(args.out_jsonl)
    out_summary = Path(args.out_summary)
    out_report = Path(args.out_report)
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_jsonl.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in audited), encoding="utf-8")
    summary = summarize(audited)
    out_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(summary)
    print(json.dumps({"files": [str(f) for f in files], "out_jsonl": str(out_jsonl), "out_summary": str(out_summary), "out_report": str(out_report), "by_model": summary["by_model"]}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
