#!/usr/bin/env python3
"""Build E88 final-correct manual audit sheet from larger answer-first generations."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT / "results/E88_answer_first_natural_sample"
DATA_OUT = PROJECT / "data/processed/e88_answer_first_final_correct_audit_sheet_20260429.jsonl"
SUMMARY_OUT = OUT_DIR / "e88_answer_first_audit_sheet_summary.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", default=str(OUT_DIR))
    ap.add_argument("--out-jsonl", default=str(DATA_OUT))
    args = ap.parse_args()
    in_dir = Path(args.in_dir)
    files = sorted(in_dir.glob("*_hard_task_conditioning.json"))
    rows = []
    idx = 880000
    for p in files:
        data = load_json(p)
        for i, r in enumerate(data.get("rows", [])):
            if not r.get("manual_final_correct"):
                continue
            idx += 1
            rows.append({
                "e88_audit_idx": idx,
                "source_file": p.name,
                "source_row_index": i,
                "model_key": r.get("model_key"),
                "task_id": r.get("task_id"),
                "prompt_variant": r.get("prompt_variant"),
                "sample_idx": r.get("sample_idx"),
                "problem": r.get("problem"),
                "gold_answer": r.get("gold_answer"),
                "extracted_final": r.get("extracted_final"),
                "completion": r.get("completion"),
                "manual_final_correct": True,
                "manual_process_valid_strict": None,
                "manual_process_valid_repaired": None,
                "manual_acpi_strict": None,
                "manual_repair_present": None,
                "manual_acpi_unrepaired": None,
                "manual_error_type": None,
                "manual_error_span": None,
                "manual_notes_zh": "TODO: human/agent audit",
            })
    write_jsonl(Path(args.out_jsonl), rows)
    by_model = defaultdict(Counter)
    for p in files:
        data = load_json(p)
        m = data.get("model_key") or p.name.split("_e49_")[0]
        by_model[m]["generated"] += len(data.get("rows", []))
        by_model[m]["final_correct"] += sum(bool(r.get("manual_final_correct")) for r in data.get("rows", []))
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_files": [str(p.relative_to(PROJECT)) for p in files],
        "audit_sheet": str(Path(args.out_jsonl).relative_to(PROJECT)),
        "n_final_correct_rows": len(rows),
        "by_model": {k: dict(v) for k, v in sorted(by_model.items())},
        "leakage_audit": {"gold_answer_in_prompt_rows": 0, "known_trap_note_in_prompt_rows": 0, "note_zh": "E88 使用 answer_first_no_gold prompt；gold 只用于离线判定 final-correct 并筛出待人工过程审计行。"},
    }
    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
