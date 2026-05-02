#!/usr/bin/env python3
"""Recompute E49 final-answer labels with line-anchored Final answer parser.

This prevents echoed text such as "Given final answer: 16" from being counted as
an emitted final-answer line. It does not alter completions.
"""
from __future__ import annotations

import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
E49_DIR = PROJECT / "results/E49_hard_task_conditioning_official"
ARCHIVE_DIR = PROJECT / "archive/logic_error_quarantine_20260428"
LOG_PATH = PROJECT / "logs/recompute_e49_final_labels_20260428.json"


def normalize_answer(text: str) -> str:
    text = text.strip().lower()
    text = text.replace("$", "").replace("\\", "")
    text = re.sub(r"\s+", "", text)
    text = text.rstrip(".。,:;，；")
    if re.fullmatch(r"-?\d+\.0+", text):
        return str(int(float(text)))
    return text


def extract_final_answer(text: str) -> tuple[str, bool]:
    matches = list(re.finditer(r"^\s*final\s*answer\s*[:：]\s*([^\n]+)", text, flags=re.IGNORECASE | re.MULTILINE))
    if matches:
        return matches[-1].group(1).strip(), True
    return "", False


def summarize(rows):
    by_variant = defaultdict(Counter)
    by_task = defaultdict(Counter)
    for r in rows:
        for bucket in (by_variant[r["prompt_variant"]], by_task[r["task_id"]]):
            bucket["n"] += 1
            bucket["final_correct"] += int(r["manual_final_correct"])
            bucket["gold_answer_in_prompt"] += int(r.get("gold_answer_in_prompt", False))
            bucket["needs_manual_process_audit"] += int(r["manual_risk"] == "final_correct_needs_manual_process_audit")
            bucket["acpi"] += int(r.get("is_acpi", False))
    return {
        "n": len(rows),
        "final_correct": sum(r["manual_final_correct"] for r in rows),
        "process_invalid_final_correct": sum(r.get("is_acpi", False) for r in rows),
        "not_final_correct": sum(not r["manual_final_correct"] for r in rows),
        "strict_final_marker_missing": sum(not r["final_marker_found"] for r in rows),
        "gold_answer_in_prompt_rows": sum(r.get("gold_answer_in_prompt", False) for r in rows),
        "known_trap_note_in_prompt_rows": sum(r.get("known_trap_note_in_prompt", False) for r in rows),
        "needs_manual_process_audit": sum(r["manual_risk"] == "final_correct_needs_manual_process_audit" for r in rows),
        "by_variant": {k: dict(v) for k, v in sorted(by_variant.items())},
        "by_task": {k: dict(v) for k, v in sorted(by_task.items())},
    }


def main() -> None:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    changes = []
    for path in sorted(E49_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        changed_rows = []
        for idx, row in enumerate(data.get("rows", [])):
            extracted, marker = extract_final_answer(row.get("completion", ""))
            final_correct = normalize_answer(extracted) == normalize_answer(row["gold_answer"])
            old = (
                row.get("extracted_final"),
                row.get("final_marker_found"),
                row.get("manual_final_correct"),
                row.get("manual_process_valid"),
                row.get("manual_risk"),
                row.get("is_acpi"),
            )
            if final_correct:
                # Keep any existing human process audit; otherwise require one.
                proc_valid = row.get("manual_process_valid")
                risk = row.get("manual_risk") if proc_valid is not None else "final_correct_needs_manual_process_audit"
                is_acpi = bool(proc_valid is False)
            else:
                proc_valid = None
                risk = "not_final_correct"
                is_acpi = False
            new = (extracted, marker, final_correct, proc_valid, risk, is_acpi)
            if old != new:
                changed_rows.append({"row_index": idx, "task_id": row["task_id"], "old": old, "new": new})
                row["extracted_final"] = extracted
                row["final_marker_found"] = marker
                row["manual_final_correct"] = final_correct
                row["manual_process_valid"] = proc_valid
                row["manual_risk"] = risk
                row["is_acpi"] = is_acpi
                row["posthoc_audit_note"] = "E49 final-answer labels recomputed with line-anchored parser; echoed 'Given final answer' no longer counts. / E49 使用行首锚定 parser 重算，模型复述的 Given final answer 不再计入 final-answer 行。"
        if changed_rows:
            dest = ARCHIVE_DIR / f"{path.stem}.pre_e49_line_anchor_fix_20260428.json"
            if not dest.exists():
                shutil.copy2(path, dest)
            data["summary"] = summarize(data.get("rows", []))
            data.setdefault("posthoc_audit_history", []).append(
                {
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "script": "scripts/recompute_e49_final_labels.py",
                    "changed_rows": changed_rows,
                    "note_en": "Only parser-derived final-answer labels and dependent summary counters were recomputed; completions were not changed.",
                    "note_zh": "只重算 parser 派生的 final-answer 标签和相关 summary；模型输出未改动。",
                }
            )
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            changes.append({"path": str(path), "archive": str(dest), "changed_rows": changed_rows})
    out = {"created_at": datetime.now().isoformat(timespec="seconds"), "changes": changes, "changed_file_count": len(changes)}
    LOG_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
