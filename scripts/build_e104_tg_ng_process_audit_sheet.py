#!/usr/bin/env python3
"""Build E104 process-audit sheet from E103 TG/NG final-correct rows."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_IN = PROJECT / "results/E103_tg_ng_fair_hardtask/qwen35_27b_e103_tg_ng_fair_hardtask.json"
DEFAULT_OUT = PROJECT / "data/processed/e104_tg_ng_process_audit_sheet_20260429.jsonl"
DEFAULT_SUMMARY = PROJECT / "results/E104_tg_ng_process_audit/e104_tg_ng_process_audit_sheet_summary.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-json", default=str(DEFAULT_IN))
    ap.add_argument("--out-jsonl", default=str(DEFAULT_OUT))
    ap.add_argument("--summary-json", default=str(DEFAULT_SUMMARY))
    args = ap.parse_args()

    input_path = Path(args.input_json)
    data = load_json(input_path)
    audit_rows: list[dict[str, Any]] = []
    by_mode: dict[str, Counter[str]] = defaultdict(Counter)
    leakage = Counter()
    idx = 1040000

    for source_row_index, r in enumerate(data.get("rows", [])):
        mode = r.get("mode_label")
        by_mode[mode]["generated"] += 1
        by_mode[mode]["strict_final_correct"] += int(bool(r.get("strict_final_correct")))
        by_mode[mode]["fallback_final_correct"] += int(bool(r.get("fallback_final_correct")))
        by_mode[mode]["explicit_final_marker_found"] += int(bool(r.get("explicit_final_marker_found")))
        by_mode[mode]["hit_max_new_tokens"] += int(bool(r.get("hit_max_new_tokens")))
        leakage["gold_answer_in_prompt"] += int(bool(r.get("gold_answer_in_prompt")))
        leakage["known_trap_note_in_prompt"] += int(bool(r.get("known_trap_note_in_prompt")))
        if not (r.get("strict_final_correct") or r.get("fallback_final_correct")):
            continue
        idx += 1
        audit_rows.append(
            {
                "e104_audit_idx": idx,
                "source_file": str(input_path.resolve().relative_to(PROJECT)),
                "source_row_index": source_row_index,
                "model_key": r.get("model_key"),
                "mode_label": mode,
                "thinking": r.get("thinking"),
                "temperature": r.get("temperature"),
                "top_p": r.get("top_p"),
                "top_k": r.get("top_k"),
                "task_id": r.get("task_id"),
                "prompt_variant": r.get("prompt_variant"),
                "sample_idx": r.get("sample_idx"),
                "problem": r.get("problem"),
                "gold_answer": r.get("gold_answer"),
                "strict_extracted_final": r.get("strict_extracted_final"),
                "strict_final_correct": r.get("strict_final_correct"),
                "fallback_extracted_final": r.get("fallback_extracted_final"),
                "fallback_final_correct": r.get("fallback_final_correct"),
                "fallback_extraction_method": r.get("fallback_extraction_method"),
                "explicit_final_marker_found": r.get("explicit_final_marker_found"),
                "generated_tokens": r.get("generated_tokens"),
                "hit_max_new_tokens": r.get("hit_max_new_tokens"),
                "repair_marker_count": r.get("repair_marker_count"),
                "completion": r.get("completion"),
                "manual_process_valid_strict": None,
                "manual_process_valid_repaired": None,
                "manual_acpi_strict": None,
                "manual_repair_present": None,
                "manual_acpi_unrepaired": None,
                "manual_error_type": None,
                "manual_error_span": None,
                "manual_notes_zh": "TODO: audit whether the final-correct trace is strict-valid, repaired ACPI, or unrepaired ACPI.",
            }
        )

    write_jsonl(Path(args.out_jsonl), audit_rows)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_json": str(input_path.resolve().relative_to(PROJECT)),
        "out_jsonl": str(Path(args.out_jsonl).resolve().relative_to(PROJECT)),
        "generated_total": sum(v["generated"] for v in by_mode.values()),
        "audit_rows": len(audit_rows),
        "by_mode": {k: dict(v) for k, v in sorted(by_mode.items())},
        "leakage_audit": {
            "gold_answer_in_prompt_rows": leakage["gold_answer_in_prompt"],
            "known_trap_note_in_prompt_rows": leakage["known_trap_note_in_prompt"],
            "passed": leakage["gold_answer_in_prompt"] == 0 and leakage["known_trap_note_in_prompt"] == 0,
        },
        "note_zh": "E104 只列出 E103 中 strict 或 fallback final-correct 的 trace；strict 与 fallback 必须分开解释。",
    }
    summary_path = Path(args.summary_json)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
