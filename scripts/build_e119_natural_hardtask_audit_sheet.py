#!/usr/bin/env python3
"""Build E119 final-correct audit sheet from natural hard-task expansion."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]


def normalize_answer(text: str) -> str:
    text = text.strip().lower()
    text = text.replace("$", "").replace("\\", "")
    text = re.sub(r"\s+", "", text)
    text = text.rstrip(".。,:;，；")
    if re.fullmatch(r"-?\d+\.0+", text):
        return str(int(float(text)))
    return text


def extract_final_answer(text: str, *, allow_fallback: bool) -> tuple[str, bool, str]:
    matches = list(re.finditer(r"^\s*final\s*answer\s*[:：]\s*([^\n]+)", text, flags=re.IGNORECASE | re.MULTILINE))
    if matches:
        return matches[-1].group(1).strip(), True, "final_answer_line"
    boxed = list(re.finditer(r"\\boxed\s*\{\s*(-?\d+(?:\.\d+)?)\s*\}", text, flags=re.IGNORECASE))
    if boxed:
        return boxed[-1].group(1).strip(), True, "boxed_final_answer"
    if not allow_fallback:
        return "", False, "no_explicit_final"
    phrase_lines = [
        line
        for line in text.splitlines()
        if re.search(
            r"\bfinal\s+answer\b|\b(?:the\s+)?(?:sum|answer|result)\s*(?:is|=|:)|\bsum\s+of[^\n=]{0,80}=",
            line,
            flags=re.IGNORECASE,
        )
    ]
    for line in reversed(phrase_lines):
        nums = re.findall(r"-?\d+(?:\.\d+)?", line)
        if nums:
            return nums[-1].strip(), False, "answer_phrase_line_last_number"
    tail = text[-320:]
    nums = re.findall(r"-?\d+(?:\.\d+)?", tail)
    return (nums[-1].strip() if nums else ""), False, "tail_last_number"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def display_path(path: Path) -> str:
    path = path.resolve()
    try:
        return str(path.relative_to(PROJECT))
    except ValueError:
        return str(path)


def row_with_recomputed_final(row: dict[str, Any]) -> dict[str, Any]:
    completion = row.get("completion", "")
    strict, strict_marker, strict_method = extract_final_answer(completion, allow_fallback=False)
    fallback, fallback_marker, fallback_method = extract_final_answer(completion, allow_fallback=True)
    gold = row.get("gold_answer", "")
    return {
        **row,
        "strict_extracted_final": strict,
        "strict_extraction_method": strict_method,
        "strict_final_marker_found": strict_marker,
        "strict_final_correct": bool(strict_marker and normalize_answer(strict) == normalize_answer(gold)),
        "fallback_extracted_final": fallback,
        "fallback_extraction_method": fallback_method,
        "fallback_final_marker_found": fallback_marker,
        "fallback_final_correct": bool(fallback and normalize_answer(fallback) == normalize_answer(gold)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", default=str(PROJECT / "results/E119_natural_hardtask_expansion"))
    ap.add_argument("--out-jsonl", default=str(PROJECT / "data/processed/e119_natural_hardtask_final_correct_audit_sheet_20260430.jsonl"))
    ap.add_argument("--summary-json", default=str(PROJECT / "results/E119_natural_hardtask_expansion/e119_audit_sheet_summary.json"))
    ap.add_argument("--experiment-name", default="E119_natural_hardtask_audit_sheet")
    ap.add_argument("--audit-index-field", default="e119_audit_idx")
    ap.add_argument("--audit-index-start", type=int, default=1190000)
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    files = sorted(in_dir.glob("*_hard_task_conditioning.json"))
    rows: list[dict[str, Any]] = []
    generated_rows = 0
    generated_by_file = {}
    by_model: dict[str, Counter[str]] = defaultdict(Counter)
    by_variant: dict[str, Counter[str]] = defaultdict(Counter)
    by_task: dict[str, Counter[str]] = defaultdict(Counter)
    idx = args.audit_index_start
    for path in files:
        data = load_json(path)
        raw_rows = data.get("rows", [])
        generated_by_file[display_path(path)] = len(raw_rows)
        generated_rows += len(raw_rows)
        for source_i, raw in enumerate(raw_rows):
            r = row_with_recomputed_final(raw)
            model = r.get("model_key")
            variant = r.get("prompt_variant")
            task = r.get("task_id")
            for bucket in (by_model[model], by_variant[variant], by_task[task]):
                bucket["generated"] += 1
                bucket["strict_final_correct"] += int(r["strict_final_correct"])
                bucket["fallback_final_correct"] += int(r["fallback_final_correct"])
                bucket["hit_max"] += int(bool(r.get("hit_max_new_tokens")))
                bucket["missing_strict_final_marker"] += int(not r["strict_final_marker_found"])
                bucket["gold_answer_in_prompt"] += int(bool(r.get("gold_answer_in_prompt")))
                bucket["known_trap_note_in_prompt"] += int(bool(r.get("known_trap_note_in_prompt")))
            if not (r["strict_final_correct"] or r["fallback_final_correct"]):
                continue
            idx += 1
            rows.append(
                {
                    args.audit_index_field: idx,
                    "source_file": display_path(path),
                    "source_row_index": source_i,
                    "model_key": model,
                    "task_id": task,
                    "prompt_variant": variant,
                    "sample_idx": r.get("sample_idx"),
                    "problem": r.get("problem"),
                    "gold_answer": r.get("gold_answer"),
                    "completion": r.get("completion"),
                    "thinking": r.get("thinking"),
                    "generated_tokens": r.get("generated_tokens"),
                    "hit_max_new_tokens": r.get("hit_max_new_tokens"),
                    "strict_extracted_final": r["strict_extracted_final"],
                    "strict_extraction_method": r["strict_extraction_method"],
                    "strict_final_marker_found": r["strict_final_marker_found"],
                    "strict_final_correct": r["strict_final_correct"],
                    "fallback_extracted_final": r["fallback_extracted_final"],
                    "fallback_extraction_method": r["fallback_extraction_method"],
                    "fallback_final_correct": r["fallback_final_correct"],
                    "manual_audit_status": "needs_audit",
                    "manual_process_valid_strict": None,
                    "manual_process_valid_repaired": None,
                    "manual_acpi_strict": None,
                    "manual_repair_present": None,
                    "manual_acpi_unrepaired": None,
                    "manual_error_type": None,
                    "manual_error_span": None,
                    "manual_notes_zh": "TODO: human/agent audit final-correct trace.",
                }
            )

    write_jsonl(Path(args.out_jsonl), rows)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": args.experiment_name,
        "input_dir": display_path(in_dir),
        "input_files": list(generated_by_file),
        "generated_total": generated_rows,
        "final_correct_rows_for_audit": len(rows),
        "audit_sheet": display_path(Path(args.out_jsonl)),
        "generated_by_file": generated_by_file,
        "by_model": {k: dict(v) for k, v in sorted(by_model.items())},
        "by_variant": {k: dict(v) for k, v in sorted(by_variant.items())},
        "by_task": {k: dict(v) for k, v in sorted(by_task.items())},
        "leakage_audit": {
            "gold_answer_in_prompt_rows": sum(v["gold_answer_in_prompt"] for v in by_model.values()),
            "known_trap_note_in_prompt_rows": sum(v["known_trap_note_in_prompt"] for v in by_model.values()),
            "passed": all(v["gold_answer_in_prompt"] == 0 and v["known_trap_note_in_prompt"] == 0 for v in by_model.values()),
            "note_zh": "Gold answer is used only offline for final-correct filtering; prompt variants are no-gold.",
        },
    }
    summary_path = Path(args.summary_json)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
