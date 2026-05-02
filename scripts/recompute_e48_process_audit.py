#!/usr/bin/env python3
"""Recompute conservative E48 process-audit labels after regex fixes.

This does not change model generations or final-answer labels. It only updates
post-hoc process-validity labels and summaries, archiving the pre-fix JSON when
any row changes.
"""
from __future__ import annotations

import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
E48_DIR = PROJECT / "results/E48_natural_prevalence_official"
ARCHIVE_DIR = PROJECT / "archive/logic_error_quarantine_20260428"
LOG_PATH = PROJECT / "logs/recompute_e48_process_audit_20260428.json"

# Keep this in sync with the official E48 runners.
INVALID_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "mean_vs_median": [(r"\bmedian\b|middle value|中位数|中间值", "mean_median_confusion")],
    "range_vs_average": [(r"\baverage\b|\bmean\b|平均", "range_average_confusion")],
    "coefficient_vs_exponent": [(r"\bcoefficient\b.{0,40}\b(?:is|=|equals)\s*3\b", "coefficient_exponent_confusion")],
    "reciprocal_vs_additive_inverse": [(r"additive inverse|negative|-\s*4|change the sign|相反数|负数|变号", "reciprocal_additive_inverse_confusion")],
    "percent_increase_vs_percent_of": [(r"new price (?:is|=).{0,20}(?:20%|0\.2).*50|only\s+20%|multiply\s+by\s+0\.?20", "increase_percent_of_confusion")],
    "prob_without_replacement": [(r"with replacement|put back|replaced before|3/5\s*(?:again|twice)|same\s+3\s+red\s+(?:out of|among)\s+5", "without_replacement_confusion")],
    "each_vs_total": [(r"split|share|divide\s+6\s+by\s+4|class total is 6|whole group read 6|总共\s*6|平分", "each_total_confusion")],
    "log_base_argument": [(r"base\s+is\s+8|argument\s+is\s+2|8\s+as\s+the\s+base|以\s*8\s*为底|真数是\s*2", "log_base_argument_confusion")],
    "round_vs_truncate": [(r"truncate|truncation|round\s+down\s+to\s+4\.6|nearest\s+tenth\s+is\s+4\.6|舍去.*4\.6|截断", "round_truncate_confusion")],
    "zh_perimeter_vs_area": [(r"面积|长乘宽|8\s*[*×x]\s*3|24\s*平方", "perimeter_area_confusion")],
    "zh_yi_wan_unit": [(r"1000\s*万|一千\s*万|0\.3\s*[*×x]\s*1000", "yi_wan_unit_confusion")],
    "zh_exclusive_interval": [(r"2\s*、\s*3\s*、\s*4\s*、\s*5\s*、\s*6|2\s*,\s*3\s*,\s*4\s*,\s*5\s*,\s*6|把边界|含端点|包括端点|包含端点|including endpoints|inclusive interval|from\s+2\s+to\s+6\s+inclusive", "exclusive_interval_endpoint_confusion")],
}


def normalize_answer(text: str) -> str:
    text = text.strip().lower()
    text = text.replace("$", "").replace("\\", "")
    text = re.sub(r"\s+", "", text)
    text = text.rstrip(".。,:;，；")
    frac = re.fullmatch(r"(-?[0-9]+)\s*/\s*([0-9]+)", text)
    if frac:
        return f"{int(frac.group(1))}/{int(frac.group(2))}"
    if re.fullmatch(r"-?\d+\.0+", text):
        return str(int(float(text)))
    return text


def extract_final_answer(text: str):
    matches = list(re.finditer(r"^\s*final\s*answer\s*[:：]\s*([^\n]+)", text, flags=re.IGNORECASE | re.MULTILINE))
    if matches:
        return matches[-1].group(1).strip(), True
    return "", False


def process_audit(task_id: str, completion: str, final_correct: bool):
    if not final_correct:
        return None, "not_final_correct_not_audited"
    for pattern, reason in INVALID_PATTERNS.get(task_id, []):
        if re.search(pattern, completion, flags=re.IGNORECASE | re.DOTALL):
            if task_id == "percent_increase_vs_percent_of" and re.search(r"add|increase.{0,30}by|50\s*\+\s*10|1\.20|120%", completion, flags=re.IGNORECASE | re.DOTALL):
                continue
            return False, reason
    return True, "no_known_invalid_process_found_manual_review_required"


def recompute_summary(rows):
    by_variant = defaultdict(Counter)
    by_task = defaultdict(Counter)
    for r in rows:
        for bucket in (by_variant[r["prompt_variant"]], by_task[r["task_id"]]):
            bucket["n"] += 1
            bucket["final_correct"] += int(r["manual_final_correct"])
            bucket["acpi"] += int(r["is_acpi"])
            bucket["needs_manual_review"] += int(r["manual_risk"] == "no_known_invalid_process_found_manual_review_required")
    return {
        "n": len(rows),
        "final_correct": sum(r["manual_final_correct"] for r in rows),
        "process_invalid_final_correct": sum(r["is_acpi"] for r in rows),
        "not_final_correct": sum(not r["manual_final_correct"] for r in rows),
        "strict_final_marker_missing": sum(not r["final_marker_found"] for r in rows),
        "gold_answer_in_prompt_rows": sum(r["gold_answer_in_prompt"] for r in rows),
        "known_error_span_in_prompt_rows": sum(r["known_error_span_in_prompt"] for r in rows),
        "by_variant": {k: dict(v) for k, v in sorted(by_variant.items())},
        "by_task": {k: dict(v) for k, v in sorted(by_task.items())},
    }


def main() -> None:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    changes = []
    e48_paths = sorted(E48_DIR.glob("*_e48_natural_prevalence_official.json"))
    e48_paths += sorted(E48_DIR.glob("*_e48_vllm_official_generation.json"))
    for path in e48_paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        changed_rows = []
        for idx, row in enumerate(data.get("rows", [])):
            extracted, final_marker = extract_final_answer(row["completion"])
            final_correct = normalize_answer(extracted) == normalize_answer(row["gold_answer"])
            proc_valid, risk = process_audit(row["task_id"], row["completion"], final_correct)
            is_acpi = bool(row["manual_final_correct"] and proc_valid is False)
            is_acpi = bool(final_correct and proc_valid is False)
            old = (
                row.get("extracted_final"),
                row.get("final_marker_found"),
                row.get("manual_final_correct"),
                row.get("manual_process_valid"),
                row.get("manual_risk"),
                row.get("is_acpi"),
            )
            new = (extracted, final_marker, final_correct, proc_valid, risk, is_acpi)
            if old != new:
                changed_rows.append({"row_index": idx, "task_id": row["task_id"], "old": old, "new": new})
                row["extracted_final"] = extracted
                row["final_marker_found"] = final_marker
                row["manual_final_correct"] = final_correct
                row["manual_process_valid"] = proc_valid
                row["manual_risk"] = risk
                row["is_acpi"] = is_acpi
                row["posthoc_audit_note"] = "E48 final-answer and conservative process labels recomputed after human review of parser/regex false positives. / 人工复核 parser/regex 假阳性后重算最终答案与保守过程标签。"
        if changed_rows:
            dest = ARCHIVE_DIR / f"{path.stem}.pre_e48_regex_fix_20260428.json"
            if not dest.exists():
                shutil.copy2(path, dest)
            data["summary"] = recompute_summary(data["rows"])
            data.setdefault("posthoc_audit_history", []).append(
                {
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "script": "scripts/recompute_e48_process_audit.py",
                    "changed_rows": changed_rows,
                    "note_en": "Only post-hoc process labels were recomputed; completions and final-answer correctness were not changed.",
                    "note_zh": "只重算事后过程标签；模型输出和最终答案正确性未改动。",
                }
            )
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            changes.append({"path": str(path), "archive": str(dest), "changed_rows": changed_rows})
    out = {"created_at": datetime.now().isoformat(timespec="seconds"), "changes": changes, "changed_file_count": len(changes)}
    LOG_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
