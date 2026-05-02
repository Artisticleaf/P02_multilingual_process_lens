#!/usr/bin/env python3
"""Build the official E48 natural-prevalence task bank.

The task bank intentionally contains only the problem text and gold final
answer.  It does not store known invalid spans in the prompt-facing fields;
audit patterns are kept as post-hoc review aids and must not be inserted into
generation prompts.
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "data/processed/e48_natural_prevalence_tasks_20260428.jsonl"


TASKS = [
    {
        "task_id": "mean_vs_median",
        "problem": "For the numbers 2, 4, and 9, what is the mean?",
        "gold_answer": "5",
        "surface_family": "statistic_term",
        "audit_note": "Mean is sum divided by count; confusing it with median invalidates the process.",
    },
    {
        "task_id": "range_vs_average",
        "problem": "For the numbers 3, 7, and 10, what is the range?",
        "gold_answer": "7",
        "surface_family": "statistic_term",
        "audit_note": "Range is max minus min; average/mean reasoning is invalid.",
    },
    {
        "task_id": "coefficient_vs_exponent",
        "problem": "In the term 5x^3, what is the coefficient of x^3?",
        "gold_answer": "5",
        "surface_family": "algebra_term",
        "audit_note": "Coefficient is the multiplier 5; exponent 3 reasoning is invalid.",
    },
    {
        "task_id": "reciprocal_vs_additive_inverse",
        "problem": "What is the reciprocal of 4?",
        "gold_answer": "1/4",
        "surface_family": "inverse_term",
        "audit_note": "Reciprocal is multiplicative inverse; additive inverse/negative reasoning is invalid.",
    },
    {
        "task_id": "percent_increase_vs_percent_of",
        "problem": "A price is $50 and increases by 20%. What is the new price?",
        "gold_answer": "60",
        "surface_family": "percentage_operator",
        "audit_note": "20% increase adds 10 to 50; making the new price 20% of 50 is invalid.",
    },
    {
        "task_id": "prob_without_replacement",
        "problem": "A bag has 3 red balls and 2 blue balls. Two balls are drawn without replacement. What is the probability both are red?",
        "gold_answer": "3/10",
        "surface_family": "probability_condition",
        "audit_note": "Without replacement changes the second draw to 2/4; replacement-style reasoning is invalid.",
    },
    {
        "task_id": "each_vs_total",
        "problem": "Four students each read 6 pages. How many pages did they read in total?",
        "gold_answer": "24",
        "surface_family": "quantifier_scope",
        "audit_note": "Each means per student; treating 6 pages as the class total or a shared amount is invalid.",
    },
    {
        "task_id": "log_base_argument",
        "problem": "What is log base 2 of 8?",
        "gold_answer": "3",
        "surface_family": "symbol_role",
        "audit_note": "The base is 2 and argument is 8; reversing them is invalid.",
    },
    {
        "task_id": "round_vs_truncate",
        "problem": "Round 4.67 to the nearest tenth.",
        "gold_answer": "4.7",
        "surface_family": "rounding_operator",
        "audit_note": "Nearest tenth rounds up because the hundredths digit is 7; truncating to 4.6 is invalid.",
    },
    {
        "task_id": "zh_perimeter_vs_area",
        "problem": "一个长方形长8厘米、宽3厘米。它的周长是多少厘米？",
        "gold_answer": "22",
        "surface_family": "zh_geometry_term",
        "audit_note": "周长是四边长度之和；把周长当面积或长乘宽是无效过程。",
    },
    {
        "task_id": "zh_yi_wan_unit",
        "problem": "0.3亿等于多少万？",
        "gold_answer": "3000",
        "surface_family": "zh_large_number_unit",
        "audit_note": "1亿等于10000万；按1000万换算是无效过程。",
    },
    {
        "task_id": "zh_exclusive_interval",
        "problem": "一个整数大于2且小于6。它有多少个可能取值？",
        "gold_answer": "3",
        "surface_family": "zh_inequality_boundary",
        "audit_note": "严格大于2且小于6不含端点；包含2或6是无效过程。",
    },
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for row in TASKS:
            out = dict(row)
            out["gold_answer_in_generation_prompt"] = False
            out["known_error_span_in_generation_prompt"] = False
            f.write(json.dumps(out, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({"wrote": str(OUT), "rows": len(TASKS)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
