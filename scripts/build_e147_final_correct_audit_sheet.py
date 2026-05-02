#!/usr/bin/env python3
"""Build E147 final/fallback-correct process audit sheet.

This selects generated rows whose extracted final answer matches the offline
gold answer.  It does not assign process labels; the sheet is the structured
input for ACPI discovery.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import run_e49_hard_task_conditioning_official as e49  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT))
    except ValueError:
        return str(path)


def recompute(row: dict[str, Any]) -> dict[str, Any]:
    completion = row.get("completion", "")
    strict, strict_marker, strict_method = e49.extract_final_answer(completion, allow_fallback=False)
    fallback, fallback_marker, fallback_method = e49.extract_final_answer(completion, allow_fallback=True)
    gold = str(row.get("gold_answer", ""))
    return {
        **row,
        "strict_extracted_final": strict,
        "strict_extraction_method": strict_method,
        "strict_final_marker_found": strict_marker,
        "strict_final_correct": bool(strict_marker and e49.normalize_answer(strict) == e49.normalize_answer(gold)),
        "fallback_extracted_final": fallback,
        "fallback_extraction_method": fallback_method,
        "fallback_final_marker_found": fallback_marker,
        "fallback_final_correct": bool(fallback and e49.normalize_answer(fallback) == e49.normalize_answer(gold)),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--in-dir", default=str(PROJECT / "results/E147_unrepaired_acpi_induction"))
    p.add_argument("--out-jsonl", default=str(PROJECT / "data/processed/e147_final_correct_audit_sheet_20260430.jsonl"))
    p.add_argument("--summary-json", default=str(PROJECT / "results/E147_unrepaired_acpi_induction/e147_final_correct_audit_sheet_summary.json"))
    p.add_argument("--audit-index-start", type=int, default=1470000)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    in_dir = Path(args.in_dir)
    files = sorted(path for path in in_dir.glob("*_e147_*_induction_generation.json") if path.is_file())
    rows: list[dict[str, Any]] = []
    generated_total = 0
    by_model: dict[str, Counter[str]] = defaultdict(Counter)
    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    by_variant: dict[str, Counter[str]] = defaultdict(Counter)
    by_route: dict[str, Counter[str]] = defaultdict(Counter)
    generated_by_file: dict[str, int] = {}
    idx = args.audit_index_start
    for path in files:
        data = load_json(path)
        raw_rows = data.get("rows", [])
        generated_by_file[rel(path)] = len(raw_rows)
        generated_total += len(raw_rows)
        for source_i, raw in enumerate(raw_rows):
            row = recompute(raw)
            model = str(row.get("model_key", ""))
            family = str(row.get("family", ""))
            variant = str(row.get("prompt_variant", ""))
            route = str(row.get("route_id", ""))
            for bucket in (by_model[model], by_family[family], by_variant[variant], by_route[route]):
                bucket["generated"] += 1
                bucket["strict_final_correct"] += int(row["strict_final_correct"])
                bucket["fallback_final_correct"] += int(row["fallback_final_correct"])
                bucket["hit_max"] += int(bool(row.get("hit_max_new_tokens")))
                bucket["missing_strict_final_marker"] += int(not row["strict_final_marker_found"])
                bucket["gold_answer_in_prompt"] += int(bool(row.get("gold_answer_in_prompt")))
                bucket["known_trap_note_in_prompt"] += int(bool(row.get("known_trap_note_in_prompt")))
                bucket["manual_label_in_prompt"] += int(bool(row.get("manual_label_in_prompt")))
                bucket["error_span_in_prompt"] += int(bool(row.get("error_span_in_prompt")))
            if not (row["strict_final_correct"] or row["fallback_final_correct"]):
                continue
            idx += 1
            rows.append(
                {
                    "e147_audit_idx": idx,
                    "source_file": rel(path),
                    "source_row_index": source_i,
                    "model_key": model,
                    "task_id": row.get("task_id"),
                    "family": family,
                    "route_id": route,
                    "prompt_variant": variant,
                    "sample_idx": row.get("sample_idx"),
                    "problem": row.get("problem"),
                    "gold_answer": row.get("gold_answer"),
                    "risk_pattern_offline": row.get("risk_pattern_offline"),
                    "trap_note_not_in_prompt": row.get("trap_note_not_in_prompt"),
                    "completion": row.get("completion"),
                    "thinking": row.get("thinking"),
                    "generated_tokens": row.get("generated_tokens"),
                    "hit_max_new_tokens": row.get("hit_max_new_tokens"),
                    "strict_extracted_final": row["strict_extracted_final"],
                    "strict_extraction_method": row["strict_extraction_method"],
                    "strict_final_marker_found": row["strict_final_marker_found"],
                    "strict_final_correct": row["strict_final_correct"],
                    "fallback_extracted_final": row["fallback_extracted_final"],
                    "fallback_extraction_method": row["fallback_extraction_method"],
                    "fallback_final_correct": row["fallback_final_correct"],
                    "manual_audit_status": "needs_process_audit",
                    "manual_process_valid_strict": None,
                    "manual_process_valid_repaired": None,
                    "manual_acpi_strict": None,
                    "manual_repair_present": None,
                    "manual_acpi_unrepaired": None,
                    "manual_error_type": None,
                    "manual_error_span": None,
                    "manual_notes_zh": "TODO: classify strict-valid, repaired ACPI, unrepaired ACPI, or fallback/truncation boundary.",
                }
            )

    out_jsonl = Path(args.out_jsonl)
    write_jsonl(out_jsonl, rows)
    leakage = {
        "gold_answer_in_prompt_rows": sum(v["gold_answer_in_prompt"] for v in by_model.values()),
        "known_trap_note_in_prompt_rows": sum(v["known_trap_note_in_prompt"] for v in by_model.values()),
        "manual_label_in_prompt_rows": sum(v["manual_label_in_prompt"] for v in by_model.values()),
        "error_span_in_prompt_rows": sum(v["error_span_in_prompt"] for v in by_model.values()),
    }
    leakage["passed"] = all(v == 0 for v in leakage.values())
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "E147_final_correct_audit_sheet",
        "input_dir": rel(in_dir),
        "input_files": list(generated_by_file),
        "generated_by_file": generated_by_file,
        "generated_total": generated_total,
        "final_or_fallback_correct_rows_for_audit": len(rows),
        "audit_sheet": rel(out_jsonl),
        "by_model": {k: dict(v) for k, v in sorted(by_model.items())},
        "by_family": {k: dict(v) for k, v in sorted(by_family.items())},
        "by_variant": {k: dict(v) for k, v in sorted(by_variant.items())},
        "by_route": {k: dict(v) for k, v in sorted(by_route.items())},
        "leakage_audit": leakage,
        "note_zh": "本表只筛 final/fallback-correct 行；process 标签仍需后续结构化审计。",
    }
    write_json(Path(args.summary_json), summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

