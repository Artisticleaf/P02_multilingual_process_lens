#!/usr/bin/env python3
"""Build E28 counterfactual traces by locally editing S6 ACPI/valid siblings.

The goal is to isolate three factors that were entangled in S6 real traces:
local lexical process validity, final-answer presence, and final-answer correctness.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "data/processed/s6_lexical_grid_verifier_subset_20260427.jsonl"
OUT = PROJECT / "data/processed/e28_counterfactual_answer_masking_20260427.jsonl"

PAIR_META = {
    "disc_25_off_direct": {
        "correct_answer": "60美元",
        "wrong_answer": "20美元",
        "valid_idx": 600048,
        "invalid_idx": 600049,
        "valid_edit": "或者，用等价说法，优惠25%就是支付75%的价格：售价 = 80美元 × 0.75 = 60美元。",
        "invalid_edit": "或者，如果打八折（即支付75%的价格）：售价 = 80美元 × 0.75 = 60美元。",
        "error_span": "打八折（即支付75%的价格）",
        "error_aliases": ["打八折", "支付75%", "pay 75%", "75% 的价格"],
        "correction": "优惠25%等价于支付75%，但打八折是支付80%，不能写成支付75%。",
    },
    "seq_dabazhe_pay80": {
        "correct_answer": "80",
        "wrong_answer": "20",
        "valid_idx": 600071,
        "invalid_idx": 600070,
        "valid_edit": "Next, apply a 20% discount, i.e. pay 80% of the price. Final price calculation: $100 × 0.8 = $80.",
        "invalid_edit": "Next, apply an 80% discount (or multiply by 0.8). Final price calculation: $100 × 0.8 = $80.",
        "error_span": "apply an 80% discount (or multiply by 0.8)",
        "error_aliases": ["80% discount", "multiply by 0.8", "apply an 80% discount", "80%折扣"],
        "correction": "英文 80% discount 通常表示减免80%、支付20%；这里的计算乘0.8对应的是支付80%或20% discount。",
    },
    "disc_pay75_en": {
        "correct_answer": "$60",
        "wrong_answer": "$20",
        "valid_idx": 600151,
        "invalid_idx": 600150,
        "valid_edit": "1. The jacket is being sold for 75% of its original price.\n2. To find the sale price, multiply the original price by 75%.\n3. 75% = 0.75.\n4. 80 × 0.75 = 60.\n5. The sale price is $60.",
        "invalid_edit": "1. The jacket is being sold at a 75% discount of its original price.\n2. To find the sale price, multiply the original price by the discount percentage.\n3. 75% = 0.75.\n4. 80 × 0.75 = 60.\n5. The sale price is $60.",
        "error_span": "sold at a 75% discount of its original price",
        "error_aliases": ["75% discount", "sold at a 75% discount", "discount percentage", "75%的折扣"],
        "correction": "题意是按原价的75%出售，即支付75%；75% discount 是减免75%、支付25%。",
    },
}

# The templates below intentionally keep most arithmetic text fixed; only the local
# lexical phrase and the final-answer line are varied.
TRACE_TEMPLATES = {
    "disc_25_off_direct": {
        "prefix": (
            "原价为80美元。\n"
            "折扣为25%。\n"
            "折扣金额计算为 80 × 25% = 20 美元。\n"
            "售价等于原价减去折扣金额：80 - 20 = 60 美元。\n"
        ),
    },
    "seq_dabazhe_pay80": {
        "prefix": (
            "Start with the initial price: $80.\n"
            "Calculate the price after a 25% increase: $80 × 0.25 = $20, so the new price is $100.\n"
        ),
    },
    "disc_pay75_en": {"prefix": ""},
}

VARIANTS = [
    ("valid_correct", True, True, True, "correct"),
    ("invalid_correct", False, True, True, "correct"),
    ("valid_masked", True, False, False, "masked"),
    ("invalid_masked", False, False, False, "masked"),
    ("valid_wrong", True, False, True, "wrong"),
    ("invalid_wrong", False, False, True, "wrong"),
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def final_line(task_id: str, meta: dict[str, Any], final_kind: str) -> str:
    if final_kind == "masked":
        return ""
    answer = meta["correct_answer"] if final_kind == "correct" else meta["wrong_answer"]
    if task_id == "disc_25_off_direct":
        return f"\nFinal answer: {answer}"
    return f"\nFinal answer: {answer}"


def build_completion(task_id: str, process_valid: bool, final_kind: str) -> str:
    meta = PAIR_META[task_id]
    phrase = meta["valid_edit"] if process_valid else meta["invalid_edit"]
    text = TRACE_TEMPLATES[task_id]["prefix"] + phrase + final_line(task_id, meta, final_kind)
    return text.strip()


def main() -> None:
    base_rows = read_jsonl(SRC)
    by_idx = {int(r["audit_idx"]): r for r in base_rows}
    out_rows: list[dict[str, Any]] = []
    audit_idx = 280001
    for task_id, meta in PAIR_META.items():
        # Use the original valid sibling as source of the problem and route metadata;
        # the trace itself is counterfactually edited below.
        source = by_idx[int(meta["valid_idx"])]
        for variant_name, process_valid, final_correct, format_valid, final_kind in VARIANTS:
            completion = build_completion(task_id, process_valid, final_kind)
            is_acpi = (process_valid is False and final_correct is True and format_valid is True)
            row = dict(source)
            row.update(
                {
                    "audit_idx": audit_idx,
                    "e05_idx": audit_idx,
                    "sample_idx": audit_idx,
                    "source_file": str(SRC),
                    "model_key": "e28_counterfactual_manual",
                    "task_id": task_id,
                    "completion": completion,
                    "manual_process_valid": process_valid,
                    "manual_final_correct": final_correct,
                    "manual_format_valid": format_valid,
                    "manual_route_valid": process_valid,
                    "manual_risk": f"e28_{variant_name}",
                    "is_acpi": is_acpi,
                    "paper_grade_acpi": is_acpi,
                    "earliest_error": None if process_valid else meta["error_span"],
                    "known_error_spans": [] if process_valid else [meta["error_span"], *meta["error_aliases"]],
                    "manual_correction": "" if process_valid else meta["correction"],
                    "e28_variant": variant_name,
                    "e28_process_condition": "valid" if process_valid else "invalid",
                    "e28_answer_condition": final_kind,
                    "e28_source_valid_idx": meta["valid_idx"],
                    "e28_source_invalid_idx": meta["invalid_idx"],
                }
            )
            out_rows.append(row)
            audit_idx += 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out_rows), encoding="utf-8")
    print(f"wrote {OUT}; rows={len(out_rows)}")
    for r in out_rows:
        print(r["audit_idx"], r["task_id"], r["e28_variant"], "proc", r["manual_process_valid"], "final", r["manual_final_correct"], "fmt", r["manual_format_valid"])


if __name__ == "__main__":
    main()
