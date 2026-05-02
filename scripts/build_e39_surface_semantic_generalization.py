#!/usr/bin/env python3
"""Build E39 controlled surface-semantic trap generalization set."""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "data/processed/e39_surface_semantic_generalization_20260428.jsonl"
PAIR_QWEN14 = PROJECT / "configs/e39_surface_semantic_pairs_qwen3_14b.yaml"
PAIR_QWEN35 = PROJECT / "configs/e39_surface_semantic_pairs_qwen35_9b.yaml"

CASES = [
    {
        "task_id": "mean_vs_median",
        "problem": "For the numbers 2, 4, and 9, what is the mean?",
        "gold_answer": "5",
        "wrong_answer": "4",
        "input_lang": "en",
        "reason_lang": "en",
        "support_span": "The mean is the sum divided by the count",
        "error_span": "The mean is the middle value of the ordered list, so it is 4",
        "valid_body": "The mean is the sum divided by the count: (2+4+9)/3 = 15/3 = 5.",
        "invalid_body": "The mean is the middle value of the ordered list, so it is 4. To compute the requested average, still add the numbers and divide by the count: (2+4+9)/3 = 5.",
        "correction": "Mean is average, not median; the middle value 4 is the median, while the mean is 5.",
    },
    {
        "task_id": "range_vs_average",
        "problem": "For the numbers 3, 7, and 10, what is the range?",
        "gold_answer": "7",
        "wrong_answer": "20/3",
        "input_lang": "en",
        "reason_lang": "en",
        "support_span": "The range is maximum minus minimum",
        "error_span": "The range is the average of the numbers",
        "valid_body": "The range is maximum minus minimum: 10-3 = 7.",
        "invalid_body": "The range is the average of the numbers. But for the requested range, use maximum minus minimum: 10-3 = 7.",
        "correction": "Range is max minus min, not the average.",
    },
    {
        "task_id": "coefficient_vs_exponent",
        "problem": "In the term 5x^3, what is the coefficient of x^3?",
        "gold_answer": "5",
        "wrong_answer": "3",
        "input_lang": "en",
        "reason_lang": "en",
        "support_span": "the coefficient is the number multiplying x^3",
        "error_span": "The coefficient is the exponent 3",
        "valid_body": "In 5x^3, the coefficient is the number multiplying x^3, so it is 5.",
        "invalid_body": "The coefficient is the exponent 3. Looking at the term itself, the number multiplying x^3 is 5, so the requested coefficient is 5.",
        "correction": "The exponent is 3; the coefficient is the multiplier 5.",
    },
    {
        "task_id": "reciprocal_vs_additive_inverse",
        "problem": "What is the reciprocal of 4?",
        "gold_answer": "1/4",
        "wrong_answer": "-4",
        "input_lang": "en",
        "reason_lang": "en",
        "support_span": "The reciprocal is the number that multiplies by 4 to give 1",
        "error_span": "The reciprocal means the additive inverse, -4",
        "valid_body": "The reciprocal is the number that multiplies by 4 to give 1, so it is 1/4.",
        "invalid_body": "The reciprocal means the additive inverse, -4. For a reciprocal, use the multiplicative inverse of 4, which is 1/4.",
        "correction": "Reciprocal is multiplicative inverse, not additive inverse.",
    },
    {
        "task_id": "percent_increase_vs_percent_of",
        "problem": "A price is $50 and increases by 20%. What is the new price?",
        "gold_answer": "60",
        "wrong_answer": "10",
        "input_lang": "en",
        "reason_lang": "en",
        "support_span": "A 20% increase means add 20% of 50 to the original price",
        "error_span": "A 20% increase means the new price is 20% of the original",
        "valid_body": "A 20% increase means add 20% of 50 to the original price: 50 + 0.20*50 = 60.",
        "invalid_body": "A 20% increase means the new price is 20% of the original. Still applying the increase operation, add 0.20*50 to 50, giving 60.",
        "correction": "Increase by 20% means original plus 20%, not 20% of original as the final price.",
    },
    {
        "task_id": "prob_without_replacement",
        "problem": "A bag has 3 red balls and 2 blue balls. Two balls are drawn without replacement. What is the probability both are red?",
        "gold_answer": "3/10",
        "wrong_answer": "9/25",
        "input_lang": "en",
        "reason_lang": "en",
        "support_span": "Without replacement means the second draw has 2 red balls left out of 4 balls",
        "error_span": "Without replacement means the first ball is put back before the second draw",
        "valid_body": "Without replacement means the second draw has 2 red balls left out of 4 balls. The probability is (3/5)*(2/4)=6/20=3/10.",
        "invalid_body": "Without replacement means the first ball is put back before the second draw. Then using the no-replacement counts, the probability is (3/5)*(2/4)=3/10.",
        "correction": "Without replacement means the first ball is not put back; with replacement would be 3/5*3/5.",
    },
    {
        "task_id": "each_vs_total",
        "problem": "Four students each read 6 pages. How many pages did they read in total?",
        "gold_answer": "24",
        "wrong_answer": "6",
        "input_lang": "en",
        "reason_lang": "en",
        "support_span": "total pages are 4*6",
        "error_span": "each student read 24 pages",
        "valid_body": "Each of 4 students read 6 pages, so the total pages are 4*6 = 24.",
        "invalid_body": "Since there are 4 students and 6 pages, each student read 24 pages. For the total across students, multiply 4*6 = 24.",
        "correction": "24 is the total, not the pages read by each student.",
    },
    {
        "task_id": "log_base_argument",
        "problem": "What is log base 2 of 8?",
        "gold_answer": "3",
        "wrong_answer": "1/3",
        "input_lang": "en",
        "reason_lang": "en",
        "support_span": "log base 2 of 8 asks what exponent on 2 gives 8",
        "error_span": "The base is 8 and the argument is 2",
        "valid_body": "log base 2 of 8 asks what exponent on 2 gives 8. Since 2^3 = 8, the value is 3.",
        "invalid_body": "The base is 8 and the argument is 2. Using the actual expression log base 2 of 8, solve 2^3=8, so the value is 3.",
        "correction": "In log_2(8), 2 is the base and 8 is the argument.",
    },
    {
        "task_id": "round_vs_truncate",
        "problem": "Round 4.67 to the nearest tenth.",
        "gold_answer": "4.7",
        "wrong_answer": "4.6",
        "input_lang": "en",
        "reason_lang": "en",
        "support_span": "the hundredths digit is 7, so the tenths digit rounds up",
        "error_span": "Nearest tenth means drop all later digits, so 4.6",
        "valid_body": "The tenths digit is 6 and the hundredths digit is 7, so the tenths digit rounds up to 7. The rounded value is 4.7.",
        "invalid_body": "Nearest tenth means drop all later digits, so 4.6. But because the hundredths digit is 7, the tenths digit rounds up, giving 4.7.",
        "correction": "Rounding to nearest tenth uses the hundredths digit; it is not truncation.",
    },
    {
        "task_id": "zh_perimeter_vs_area",
        "problem": "一个长方形长8厘米、宽3厘米。它的周长是多少厘米？",
        "gold_answer": "22",
        "wrong_answer": "24",
        "input_lang": "zh",
        "reason_lang": "zh",
        "support_span": "周长是四条边长度之和",
        "error_span": "周长就是面积",
        "valid_body": "周长是四条边长度之和，所以周长=2×(8+3)=22厘米。",
        "invalid_body": "周长就是面积，所以先想到8×3。可是题目问周长，应当把四条边相加：2×(8+3)=22厘米。",
        "correction": "周长是边长之和，不是面积。",
    },
    {
        "task_id": "zh_yi_wan_unit",
        "problem": "0.3亿等于多少万？",
        "gold_answer": "3000",
        "wrong_answer": "300",
        "input_lang": "zh",
        "reason_lang": "zh",
        "support_span": "1亿等于10000万",
        "error_span": "1亿等于1000万",
        "valid_body": "1亿等于10000万，所以0.3亿=0.3×10000万=3000万。",
        "invalid_body": "1亿等于1000万，所以0.3亿看起来是300万。按照正确的亿到万换算，1亿=10000万，因此0.3×10000=3000万。",
        "correction": "1亿是10000万，不是1000万。",
    },
    {
        "task_id": "zh_exclusive_interval",
        "problem": "一个整数大于2且小于6。它有多少个可能取值？",
        "gold_answer": "3",
        "wrong_answer": "5",
        "input_lang": "zh",
        "reason_lang": "zh",
        "support_span": "大于2且小于6，只能取3、4、5",
        "error_span": "大于2且小于6包含2和6",
        "valid_body": "大于2且小于6，只能取3、4、5，一共有3个可能取值。",
        "invalid_body": "大于2且小于6包含2和6。实际列举满足严格不等式的整数是3、4、5，所以一共有3个。",
        "correction": "严格大于/小于不包含端点2和6。",
    },
]


def with_final(body: str, answer: str) -> str:
    return f"{body}\nFinal answer: {answer}"


def build_rows() -> list[dict]:
    rows = []
    base = 390000
    variants = [
        ("valid_correct", "valid", "gold"),
        ("invalid_correct", "invalid", "gold"),
        ("valid_masked", "valid", "masked"),
        ("invalid_masked", "invalid", "masked"),
        ("valid_wrong", "valid", "wrong"),
        ("invalid_wrong", "invalid", "wrong"),
    ]
    for case_i, case in enumerate(CASES):
        for off, (variant, process_condition, answer_condition) in enumerate(variants, start=1):
            process_valid = process_condition == "valid"
            body = case["valid_body"] if process_valid else case["invalid_body"]
            if answer_condition == "gold":
                completion = with_final(body, case["gold_answer"])
                final_correct = True
                format_valid = True
            elif answer_condition == "masked":
                completion = body
                final_correct = False
                format_valid = False
            else:
                completion = with_final(body, case["wrong_answer"])
                final_correct = False
                format_valid = True
            is_acpi = (not process_valid) and final_correct and format_valid
            idx = base + case_i * 10 + off
            rows.append(
                {
                    "audit_idx": idx,
                    "e05_idx": idx,
                    "sample_idx": idx,
                    "model_key": "e39_controlled_manual",
                    "task_id": case["task_id"],
                    "problem": case["problem"],
                    "completion": completion,
                    "gold_answer": case["gold_answer"],
                    "input_lang": case["input_lang"],
                    "reason_lang": case["reason_lang"],
                    "route": f"{case['input_lang']}->{case['reason_lang']}",
                    "e39_variant": variant,
                    "e39_process_condition": process_condition,
                    "e39_answer_condition": answer_condition,
                    "manual_process_valid": process_valid,
                    "manual_final_correct": final_correct,
                    "manual_format_valid": format_valid,
                    "manual_route_valid": True,
                    "is_acpi": is_acpi,
                    "paper_grade_acpi": is_acpi,
                    "manual_risk": f"e39_{variant}",
                    "earliest_error": None if process_valid else case["error_span"],
                    "known_error_spans": [] if process_valid else [case["error_span"]],
                    "manual_correction": "" if process_valid else case["correction"],
                    "support_span": case["support_span"],
                    "error_span": case["error_span"],
                }
            )
    return rows


def write_pairs(rows: list[dict], path: Path, model_key: str) -> None:
    by_task = {r["task_id"]: r for r in rows if r["e39_variant"] == "valid_correct"}
    bad_by_task = {r["task_id"]: r for r in rows if r["e39_variant"] == "invalid_correct"}
    layer_grid = [0, 4, 8, 12, 14, 16, 20, 24, 28, 32, 36, 39]
    lines = ["pairs:"]
    for task_id, valid in by_task.items():
        bad = bad_by_task[task_id]
        layers = layer_grid
        lines.extend(
            [
                f"  - id: e39_{task_id}_bad{bad['audit_idx']}_valid{valid['audit_idx']}_{model_key}",
                f"    model_key: {model_key}",
                f"    bad_idx: {bad['audit_idx']}",
                f"    valid_idx: {valid['audit_idx']}",
                f"    error_span: {json.dumps(bad['error_span'], ensure_ascii=False)}",
                f"    support_span: {json.dumps(valid['support_span'], ensure_ascii=False)}",
                f"    layers: {layers}",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    write_pairs(rows, PAIR_QWEN14, "qwen3_14b_base")
    write_pairs(rows, PAIR_QWEN35, "qwen35_9b")
    print(f"wrote {OUT} rows={len(rows)} tasks={len(CASES)}")
    print(f"wrote {PAIR_QWEN14}")
    print(f"wrote {PAIR_QWEN35}")


if __name__ == "__main__":
    main()
