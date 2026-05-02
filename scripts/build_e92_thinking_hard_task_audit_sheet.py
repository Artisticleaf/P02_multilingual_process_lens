#!/usr/bin/env python3
"""Build E92 final-correct audit sheet from thinking hard-task generations."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT / "results/E92_thinking_hard_task_natural"
DATA_OUT = PROJECT / "data/processed/e92_thinking_hard_task_final_correct_audit_sheet_20260429.jsonl"
SUMMARY_OUT = OUT_DIR / "e92_thinking_hard_task_audit_sheet_summary.json"


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
    in_dir = Path(args.in_dir).resolve()
    files = sorted(in_dir.glob("*_hard_task_conditioning.json"))
    rows: list[dict[str, Any]] = []
    idx = 920000
    generated_total = 0
    leakage = Counter()
    by_model: dict[str, Counter[str]] = defaultdict(Counter)
    by_variant: dict[str, Counter[str]] = defaultdict(Counter)
    by_task: dict[str, Counter[str]] = defaultdict(Counter)

    for p in files:
        data = load_json(p)
        model_key = data.get("model_key") or p.name.split("_e49_")[0]
        for i, r in enumerate(data.get("rows", [])):
            generated_total += 1
            variant = r.get("prompt_variant")
            task_id = r.get("task_id")
            for bucket in (by_model[model_key], by_variant[variant], by_task[task_id]):
                bucket["generated"] += 1
                bucket["final_correct"] += int(bool(r.get("manual_final_correct")))
                bucket["thinking_true"] += int(bool(r.get("thinking")))
                bucket["gold_answer_in_prompt"] += int(bool(r.get("gold_answer_in_prompt")))
                bucket["known_trap_note_in_prompt"] += int(bool(r.get("known_trap_note_in_prompt")))
            leakage["gold_answer_in_prompt"] += int(bool(r.get("gold_answer_in_prompt")))
            leakage["known_trap_note_in_prompt"] += int(bool(r.get("known_trap_note_in_prompt")))
            leakage["thinking_false"] += int(not bool(r.get("thinking")))
            if not r.get("manual_final_correct"):
                continue
            idx += 1
            rows.append(
                {
                    "e92_audit_idx": idx,
                    "source_file": p.name,
                    "source_row_index": i,
                    "model_key": model_key,
                    "task_id": task_id,
                    "prompt_variant": variant,
                    "sample_idx": r.get("sample_idx"),
                    "thinking": r.get("thinking"),
                    "problem": r.get("problem"),
                    "gold_answer": r.get("gold_answer"),
                    "extracted_final": r.get("extracted_final"),
                    "extraction_method": r.get("extraction_method"),
                    "final_marker_found": r.get("final_marker_found"),
                    "completion": r.get("completion"),
                    "manual_final_correct": True,
                    "manual_process_valid_strict": None,
                    "manual_process_valid_repaired": None,
                    "manual_acpi_strict": None,
                    "manual_repair_present": None,
                    "manual_acpi_unrepaired": None,
                    "manual_error_type": None,
                    "manual_error_span": None,
                    "manual_notes_zh": "TODO: human/agent audit final-correct thinking trace",
                }
            )

    write_jsonl(Path(args.out_jsonl), rows)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_files": [str(p.resolve().relative_to(PROJECT)) for p in files],
        "audit_sheet": str(Path(args.out_jsonl).resolve().relative_to(PROJECT)),
        "generated_total": generated_total,
        "n_final_correct_rows": len(rows),
        "by_model": {k: dict(v) for k, v in sorted(by_model.items())},
        "by_variant": {k: dict(v) for k, v in sorted(by_variant.items())},
        "by_task": {k: dict(v) for k, v in sorted(by_task.items())},
        "leakage_audit": {
            "gold_answer_in_prompt_rows": leakage["gold_answer_in_prompt"],
            "known_trap_note_in_prompt_rows": leakage["known_trap_note_in_prompt"],
            "thinking_false_rows": leakage["thinking_false"],
            "passed": leakage["gold_answer_in_prompt"] == 0
            and leakage["known_trap_note_in_prompt"] == 0
            and leakage["thinking_false"] == 0,
            "note_zh": "E92 prompt 不含 gold answer 或 trap note；gold 只用于离线筛选 final-correct 行；所有源行应为 thinking=true。",
        },
    }
    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
