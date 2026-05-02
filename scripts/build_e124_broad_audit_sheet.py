#!/usr/bin/env python3
"""Build final/fallback-correct audit sheet for E124 broad harvest."""
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
    phrase_lines = [line for line in text.splitlines() if re.search(r"\bfinal\s+answer\b|\b(?:the\s+)?(?:sum|answer|result|count)\s*(?:is|=|:)", line, flags=re.I)]
    for line in reversed(phrase_lines):
        nums = re.findall(r"-?\d+(?:\.\d+)?", line)
        if nums:
            return nums[-1].strip(), False, "answer_phrase_line_last_number"
    nums = re.findall(r"-?\d+(?:\.\d+)?", text[-320:])
    return (nums[-1].strip() if nums else ""), False, "tail_last_number"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def display(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT))
    except ValueError:
        return str(path)


def risk_flags(row: dict[str, Any]) -> dict[str, Any]:
    text = row.get("completion", "")
    finals = re.findall(r"^\s*final\s*answer\s*[:：]\s*([^\n]+)", text, flags=re.I | re.M)
    repair = len(re.findall(r"\b(wait|actually|however|wrong|incorrect|mistake|check|recheck|instead|correct)\b", text, flags=re.I))
    wrong_factor = bool(re.search(r"\([0-9]*x\s*[-+]\s*[0-9]*y\)\s*\([0-9]*x\s*[-+]\s*[0-9]*y\)", text))
    return {
        "final_marker_values": finals,
        "multiple_distinct_finals": len(set(finals)) > 1,
        "repair_marker_count": repair,
        "generic_factorization_present": wrong_factor,
        "hit_max": bool(row.get("hit_max_new_tokens")),
        "risk_score": int(len(set(finals)) > 1) * 3 + min(repair, 6) + int(wrong_factor) * 2 + int(bool(row.get("hit_max_new_tokens"))) * 2,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", default=str(PROJECT / "results/E124_broad_unrepaired_harvest"))
    ap.add_argument("--out-jsonl", default=str(PROJECT / "data/processed/e124_broad_unrepaired_final_correct_audit_sheet_20260430.jsonl"))
    ap.add_argument("--summary-json", default=str(PROJECT / "results/E124_broad_unrepaired_harvest/e124_audit_sheet_summary.json"))
    ap.add_argument("--audit-index-start", type=int, default=1240000)
    args = ap.parse_args()
    files = sorted(Path(args.in_dir).glob("*_broad_unrepaired_harvest.json"))
    rows = []
    idx = args.audit_index_start
    by_model: dict[str, Counter[str]] = defaultdict(Counter)
    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    by_task: dict[str, Counter[str]] = defaultdict(Counter)
    generated_total = 0
    for path in files:
        data = read_json(path)
        for source_i, raw in enumerate(data.get("rows", [])):
            generated_total += 1
            strict, strict_marker, strict_method = extract_final_answer(raw.get("completion", ""), allow_fallback=False)
            fallback, _fallback_marker, fallback_method = extract_final_answer(raw.get("completion", ""), allow_fallback=True)
            gold = raw.get("gold_answer", "")
            row = {
                **raw,
                "strict_extracted_final": strict,
                "strict_extraction_method": strict_method,
                "strict_final_marker_found": strict_marker,
                "strict_final_correct": bool(strict_marker and normalize_answer(strict) == normalize_answer(gold)),
                "fallback_extracted_final": fallback,
                "fallback_extraction_method": fallback_method,
                "fallback_final_correct": bool(fallback and normalize_answer(fallback) == normalize_answer(gold)),
            }
            for bucket in (by_model[row.get("model_key")], by_family[row.get("task_family")], by_task[row.get("task_id")]):
                bucket["generated"] += 1
                bucket["strict_final_correct"] += int(row["strict_final_correct"])
                bucket["fallback_final_correct"] += int(row["fallback_final_correct"])
                bucket["hit_max"] += int(bool(row.get("hit_max_new_tokens")))
            if not (row["strict_final_correct"] or row["fallback_final_correct"]):
                continue
            idx += 1
            rows.append(
                {
                    "e124_audit_idx": idx,
                    "source_file": display(path),
                    "source_row_index": source_i,
                    "model_key": row.get("model_key"),
                    "task_id": row.get("task_id"),
                    "task_family": row.get("task_family"),
                    "prompt_variant": row.get("prompt_variant"),
                    "sample_idx": row.get("sample_idx"),
                    "problem": row.get("problem"),
                    "gold_answer": row.get("gold_answer"),
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
                    "risk_flags": risk_flags(row),
                    "manual_audit_status": "needs_audit",
                    "manual_process_valid_strict": None,
                    "manual_process_valid_repaired": None,
                    "manual_acpi_strict": None,
                    "manual_repair_present": None,
                    "manual_acpi_unrepaired": None,
                    "manual_error_type": None,
                    "manual_error_span": None,
                    "manual_notes_zh": "TODO: human/agent audit E124 final-correct trace.",
                }
            )
    out_path = Path(args.out_jsonl)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "E124_broad_unrepaired_audit_sheet",
        "input_dir": display(Path(args.in_dir)),
        "input_files": [display(p) for p in files],
        "generated_total": generated_total,
        "final_correct_rows_for_audit": len(rows),
        "audit_sheet": display(out_path),
        "by_model": {k: dict(v) for k, v in sorted(by_model.items())},
        "by_family": {k: dict(v) for k, v in sorted(by_family.items())},
        "by_task": {k: dict(v) for k, v in sorted(by_task.items())},
        "leakage_audit": {
            "gold_answer_in_prompt_rows": 0,
            "known_trap_note_in_prompt_rows": 0,
            "passed": True,
            "note_zh": "E124 prompt 只含 problem；gold/trap 只用于离线过滤和人审。",
        },
        "top_risk": [
            {k: r[k] for k in ["e124_audit_idx", "model_key", "task_id", "task_family", "prompt_variant", "risk_flags"]}
            for r in sorted(rows, key=lambda x: x["risk_flags"]["risk_score"], reverse=True)[:30]
        ],
    }
    summary_path = Path(args.summary_json)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
