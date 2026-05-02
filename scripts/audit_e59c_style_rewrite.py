#!/usr/bin/env python3
"""Audit E59c style rewrites and build verifier-ready paired data."""
from __future__ import annotations

import json
import re
import sys
import yaml
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))


RAW_DIR = PROJECT / "results/E59_style_rewrite_raw"
OUT_DATA_DIR = PROJECT / "data/processed/e59c_style_rewrite_audited"
OUT_CFG_DIR = PROJECT / "configs/e59c_style_rewrite_pairs"
OUT_RESULT_DIR = PROJECT / "results/E59_style_rewrite_audited"
for d in [OUT_DATA_DIR, OUT_CFG_DIR, OUT_RESULT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

P0 = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def write_yaml(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(obj, allow_unicode=True, sort_keys=False), encoding="utf-8")


def norm(text: str) -> str:
    return re.sub(r"\s+", "", text.lower().replace("$", "").replace("\\", "")).strip(".。,:;")


def final_correct(text: str, gold: str) -> bool:
    if norm(gold) in norm(text):
        return True
    return False


def has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, flags=re.I | re.S) for p in patterns)


VALID_PATTERNS = {
    "mean_vs_median": [r"sum|add|average|mean", r"divide|/\s*3|count"],
    "range_vs_average": [r"max|maximum|largest|最大", r"min|minimum|smallest|最小|minus|subtract|减"],
    "coefficient_vs_exponent": [r"coefficient|系数", r"multiplying|multiplies|number before|5"],
    "reciprocal_vs_additive_inverse": [r"reciprocal|倒数", r"1\s*/\s*4|one[- ]?fourth|multipl(?:y|ies).*1"],
    "percent_increase_vs_percent_of": [r"increase|增加", r"add|original|50\s*\+\s*10|60"],
    "prob_without_replacement": [r"without replacement|不放回", r"2\s*red.*4|2/4|left|remaining|剩"],
    "each_vs_total": [r"each|每", r"4\s*(?:\*|x|×|times)\s*6|6\s*\+\s*6\s*\+\s*6\s*\+\s*6|24"],
    "log_base_argument": [r"base\s*2|以\s*2\s*为底", r"2\s*(?:\^|to the power|的).*3|exponent.*3|8"],
    "round_vs_truncate": [r"round|nearest tenth|四舍五入|最近的十分位", r"hundredths.*7|7.*rounds? up|4\.7"],
    "zh_perimeter_vs_area": [r"周长|perimeter", r"2\s*[*(（]?\s*8\s*\+\s*3|8\s*\+\s*3\s*\+\s*8\s*\+\s*3|22"],
    "zh_yi_wan_unit": [r"1\s*亿.*10000\s*万|一亿.*一万万|10000\s*万", r"0\.3.*3000\s*万|3000"],
    "zh_exclusive_interval": [r"大于\s*2.*小于\s*6|greater than 2.*less than 6", r"3.*4.*5|三个|3\s*,\s*4\s*,\s*5"],
}

INVALID_PATTERNS = {
    "mean_vs_median": [r"middle value|median|中位数|ordered list.*4"],
    "range_vs_average": [r"range.*average|range.*mean|平均数|平均值"],
    "coefficient_vs_exponent": [r"coefficient.*exponent|系数.*指数|exponent.*3.*coefficient"],
    "reciprocal_vs_additive_inverse": [r"additive inverse|相反数|negative|\-\s*4"],
    "percent_increase_vs_percent_of": [r"new price\s*(?:is|=|equals)?\s*20%\s*of\s*the\s*original|only\s*20%|新价格.*只是.*20%|新价格.*20%.*原价"],
    "prob_without_replacement": [r"with replacement|put back|replaced|returned\s+to\s+the\s+bag|放回|3/5\s*(?:again|twice|for the second)"],
    "each_vs_total": [r"each student.*24|每个学生.*24|each.*read\s*24"],
    "log_base_argument": [r"base.*8.*argument.*2|base is 8|argument is 2|底.*8.*真数.*2"],
    "round_vs_truncate": [r"drop|truncate|discard|截断|舍去|(?<![0-9.])4\.6(?![0-9])"],
    "zh_perimeter_vs_area": [r"周长.*面积|面积.*周长|长乘宽|8\s*[×x*]\s*3|24\s*平方"],
    "zh_yi_wan_unit": [r"1\s*亿.*1000\s*万|一亿.*1000\s*万|1000\s*万"],
    "zh_exclusive_interval": [r"包含\s*2|包含.*6|包括\s*2|包括.*6|include\s*2|include.*6"],
}


def audit_row(row: dict[str, Any]) -> dict[str, Any]:
    text = row["rewritten_completion"]
    task = row["task_id"]
    is_valid = bool(row["manual_process_valid"])
    fc = final_correct(text, str(row["gold_answer"]))
    valid_hit = has_any(text, VALID_PATTERNS[task])
    invalid_hit = has_any(text, INVALID_PATTERNS[task])
    if is_valid:
        preserved = fc and valid_hit and not invalid_hit
        reason = "valid_rewrite_preserved" if preserved else "valid_rewrite_failed_or_ambiguous"
    else:
        preserved = fc and invalid_hit
        reason = "invalid_rewrite_preserved" if preserved else "invalid_rewrite_repaired_or_ambiguous"
    return {
        **row,
        "rewrite_final_correct_audit": fc,
        "rewrite_valid_pattern_hit": valid_hit,
        "rewrite_invalid_pattern_hit": invalid_hit,
        "rewrite_process_label_preserved": preserved,
        "rewrite_audit_reason": reason,
    }


def main() -> None:
    all_summary = []
    for source in P0:
        path = RAW_DIR / f"{source}_e59c_style_rewrite_raw.json"
        if not path.exists():
            print(f"missing {path}")
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        audited = [audit_row(r) for r in raw["rows"]]
        kept = [r for r in audited if r["rewrite_process_label_preserved"]]
        by_task: dict[str, dict[str, Any]] = {}
        for r in kept:
            by_task.setdefault(r["task_id"], {})[r["e39_variant"]] = r
        pair_rows = []
        pair_cfg = []
        audit_rows = []
        next_idx = int({"qwen35_27b": 590100, "gemma4_31b_it": 590200, "gemma4_26b_a4b_it": 590300}[source])
        for task in sorted(by_task):
            variants = by_task[task]
            if "valid_correct" not in variants or "invalid_correct" not in variants:
                continue
            valid = variants["valid_correct"]
            bad = variants["invalid_correct"]
            valid_idx = next_idx
            bad_idx = next_idx + 1
            next_idx += 10
            for idx, r in [(valid_idx, valid), (bad_idx, bad)]:
                row_out = {
                    "audit_idx": idx,
                    "source_model_key": source,
                    "original_audit_idx": r["original_audit_idx"],
                    "task_id": r["task_id"],
                    "problem": r["problem"],
                    "completion": r["rewritten_completion"],
                    "gold_answer": r["gold_answer"],
                    "e39_variant": r["e39_variant"],
                    "manual_process_valid": bool(r["manual_process_valid"]),
                    "manual_final_correct": True,
                    "manual_format_valid": True,
                    "is_acpi": (not bool(r["manual_process_valid"])),
                    "rewrite_audit_reason": r["rewrite_audit_reason"],
                    "original_completion": r["original_completion"],
                }
                pair_rows.append(row_out)
                audit_rows.append(r)
            pair_cfg.append(
                {
                    "id": f"e59c_{source}_{task}",
                    "task_id": task,
                    "source_model_key": source,
                    "bad_idx": bad_idx,
                    "valid_idx": valid_idx,
                    "problem": bad["problem"],
                }
            )
        data_path = OUT_DATA_DIR / f"{source}_e59c_style_rewrite_audited.jsonl"
        cfg_path = OUT_CFG_DIR / f"{source}_e59c_style_rewrite_pairs.yaml"
        write_jsonl(data_path, pair_rows)
        write_yaml(cfg_path, {"pairs": pair_cfg})
        summary = {
            "source_model_key": source,
            "raw_rows": len(audited),
            "preserved_rows": len(kept),
            "verifier_rows": len(pair_rows),
            "verifier_pairs": len(pair_cfg),
            "dropped_rows": len(audited) - len(kept),
            "dropped_by_reason": {},
            "data_path": str(data_path),
            "pairs_path": str(cfg_path),
        }
        for r in audited:
            if not r["rewrite_process_label_preserved"]:
                summary["dropped_by_reason"][r["rewrite_audit_reason"]] = summary["dropped_by_reason"].get(r["rewrite_audit_reason"], 0) + 1
        all_summary.append(summary)
        (OUT_RESULT_DIR / f"{source}_e59c_style_rewrite_audit_rows.json").write_text(json.dumps({"rows": audited, "summary": summary}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    out = OUT_RESULT_DIR / "summary.json"
    out.write_text(json.dumps({"summary": all_summary}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
