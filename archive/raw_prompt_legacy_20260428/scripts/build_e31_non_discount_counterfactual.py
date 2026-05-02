#!/usr/bin/env python3
"""Build E31 controlled non-discount counterfactual traces."""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "data/processed/e31_non_discount_counterfactual_20260427.jsonl"

FAMILIES = {
    "ratio_boys_girls_2_3": {
        "problem": "一个社团里男生和女生的人数比是2:3。如果社团共有30名学生，男生有多少名？",
        "gold": "12",
        "wrong": "20",
        "reason_lang": "zh",
        "valid": "男生和女生的人数比是2:3，所以总份数是2+3=5。男生占总人数的2/5。社团共有30名学生，所以男生人数是30×2/5=12。",
        "invalid": "男生和女生的人数比是2:3，所以男生占全班的2/3。为了计算男生人数，仍按比的总份数2+3=5，男生占2/5，得到30×2/5=12。",
        "error_span": "男生占全班的2/3",
        "correction": "boys:girls=2:3 是部分对部分；男生占总人数 2/(2+3)=2/5，不是 2/3。",
    },
    "inequality_no_more_than": {
        "problem": "一个数是大于3且不超过7的整数。它有多少个可能取值？",
        "gold": "4",
        "wrong": "5",
        "reason_lang": "en",
        "valid": "The condition is greater than 3 and no more than 7, so the integers are 4, 5, 6, and 7. Counting them gives 4 possible values.",
        "invalid": "The condition means the integer values are between 3 and 7, inclusive. Start by listing the integers greater than 3 and no more than 7: 4, 5, 6, and 7. Counting them gives 4 possible values.",
        "error_span": "between 3 and 7, inclusive",
        "correction": "Greater than 3 excludes 3; between 3 and 7 inclusive would include 3. The listed values are correct but the rephrasing is wrong.",
    },
    "unit_dozen_pairs": {
        "problem": "一家商店卖出3打袜子。相当于多少双袜子？",
        "gold": "18",
        "wrong": "36",
        "reason_lang": "zh",
        "valid": "一打等于12只袜子。3打袜子就是3×12=36只袜子。每双袜子有2只，所以36只袜子等于36÷2=18双。",
        "invalid": "一打袜子等于12双袜子，所以3打袜子是36双。接着把3打理解为36只袜子，每双有2只，因此36÷2=18双。",
        "error_span": "一打袜子等于12双袜子",
        "correction": "一打是12个/只，不是12双；3打袜子是36只，即18双。",
    },
    "geometry_diameter_area": {
        "problem": "一个圆的直径是10厘米。它的面积是多少（用π表示）？",
        "gold": "25π",
        "wrong": "100π",
        "reason_lang": "zh",
        "valid": "圆的直径是10厘米，所以半径是10÷2=5厘米。面积公式是πr²，因此面积是π×5²=25π。",
        "invalid": "圆的直径是10厘米，也就是说半径是10厘米。计算面积时仍取直径的一半作为半径5厘米，面积为π×5²=25π。",
        "error_span": "半径是10厘米",
        "correction": "直径10厘米意味着半径5厘米，不是半径10厘米。",
    },
    "comb_choose_unordered": {
        "problem": "从5名学生中选2名组成不区分顺序的委员会。有多少种选法？",
        "gold": "10",
        "wrong": "20",
        "reason_lang": "en",
        "valid": "The committee is unordered, so choosing A then B is the same as choosing B then A. Compute C(5,2)=5×4÷2=10.",
        "invalid": "Because two students are selected, the order matters. There are 5 choices for the first student and 4 for the second, then we divide by 2 for duplicate unordered pairs, giving 5×4÷2=10.",
        "error_span": "the order matters",
        "correction": "The committee is explicitly unordered, so order does not matter. The later division by 2 is correct but the phrase is wrong.",
    },
}

VARIANTS = [
    ("valid_correct", True, True, True, "gold"),
    ("invalid_correct", False, True, True, "gold"),
    ("valid_masked", True, False, False, "masked"),
    ("invalid_masked", False, False, False, "masked"),
    ("valid_wrong", True, False, True, "wrong"),
    ("invalid_wrong", False, False, True, "wrong"),
]


def main() -> None:
    rows = []
    idx = 310001
    for task_id, meta in FAMILIES.items():
        for variant, proc_valid, final_correct, format_valid, answer_kind in VARIANTS:
            trace = meta["valid"] if proc_valid else meta["invalid"]
            if answer_kind != "masked":
                ans = meta["gold"] if answer_kind == "gold" else meta["wrong"]
                trace = f"{trace}\nFinal answer: {ans}"
            is_acpi = (not proc_valid) and final_correct and format_valid
            rows.append({
                "audit_idx": idx,
                "e05_idx": idx,
                "model_key": "e31_counterfactual_manual",
                "task_id": task_id,
                "input_lang": "zh",
                "reason_lang": meta["reason_lang"],
                "route": f"zh->{meta['reason_lang']}",
                "sample_idx": idx,
                "problem": meta["problem"],
                "completion": trace,
                "gold_answer": meta["gold"],
                "manual_final_correct": final_correct,
                "manual_process_valid": proc_valid,
                "manual_format_valid": format_valid,
                "manual_route_valid": True,
                "manual_risk": f"e31_{variant}",
                "is_acpi": is_acpi,
                "paper_grade_acpi": is_acpi,
                "earliest_error": None if proc_valid else meta["error_span"],
                "known_error_spans": [] if proc_valid else [meta["error_span"]],
                "manual_correction": "" if proc_valid else meta["correction"],
                "e31_variant": variant,
                "e31_process_condition": "valid" if proc_valid else "invalid",
                "e31_answer_condition": answer_kind,
            })
            idx += 1
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    print(f"wrote {OUT}; rows={len(rows)}")


if __name__ == "__main__":
    main()
