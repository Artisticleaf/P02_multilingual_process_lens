#!/usr/bin/env python3
"""Build E54 parameterized no-label-leak controlled generalization set."""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "data/processed/e54_parameterized_no_leak_generalization_20260428.jsonl"
PAIRS = PROJECT / "configs/e54_parameterized_no_leak_pairs.yaml"

CASES = [
    {
        "task_id": "weighted_vs_simple_average",
        "family": "aggregation",
        "problem": "A class has 2 quizzes scored 80 and 3 quizzes scored 90. What is the weighted average score?",
        "gold_answer": "86",
        "wrong_answer": "85",
        "support_span": "weighted average uses all 5 quizzes",
        "error_span": "weighted average is the simple average of 80 and 90",
        "valid_body": "The weighted average uses all 5 quizzes: (2*80 + 3*90) / 5 = (160+270)/5 = 86.",
        "invalid_body": "The weighted average is the simple average of 80 and 90, which would be 85. Using the actual quiz counts, compute (2*80 + 3*90) / 5 = 86.",
        "correction": "Weighted average must account for multiplicities, not just average the two distinct scores.",
    },
    {
        "task_id": "median_even_middle_pair",
        "family": "aggregation",
        "problem": "What is the median of the numbers 1, 5, 9, and 13?",
        "gold_answer": "7",
        "wrong_answer": "5",
        "support_span": "average the two middle values 5 and 9",
        "error_span": "the median is the first middle value 5",
        "valid_body": "There are four ordered values, so average the two middle values 5 and 9: (5+9)/2 = 7.",
        "invalid_body": "The median is the first middle value 5. But for an even number of values, average the two middle values 5 and 9, giving 7.",
        "correction": "For an even count, the median is the average of the two middle values.",
    },
    {
        "task_id": "percentage_point_vs_percent",
        "family": "percentage_base",
        "problem": "An interest rate rises from 10% by 5 percentage points. What is the new rate in percent?",
        "gold_answer": "15",
        "wrong_answer": "10.5",
        "support_span": "5 percentage points adds directly to 10%",
        "error_span": "5 percentage points means 5% of the old 10% rate",
        "valid_body": "A rise by 5 percentage points adds directly to 10%, so the new rate is 10% + 5% = 15%.",
        "invalid_body": "5 percentage points means 5% of the old 10% rate. However, percentage points add directly to the rate, so 10% + 5% = 15%.",
        "correction": "Percentage points are additive differences, not relative percent changes.",
    },
    {
        "task_id": "reverse_percent_original",
        "family": "percentage_base",
        "problem": "After a 20% increase, a value is 120. What was the original value?",
        "gold_answer": "100",
        "wrong_answer": "600",
        "support_span": "the final value is 1.2 times the original",
        "error_span": "a 20% increase means the final value is 20% of the original",
        "valid_body": "After a 20% increase, the final value is 1.2 times the original, so original = 120 / 1.2 = 100.",
        "invalid_body": "A 20% increase means the final value is 20% of the original. Using the correct increase relation, final = 1.2 times original, so 120/1.2 = 100.",
        "correction": "A 20% increase makes final 120% of original, not 20% of original.",
    },
    {
        "task_id": "meter_to_centimeter_scale",
        "family": "unit_scale",
        "problem": "How many centimeters are in 2.5 meters?",
        "gold_answer": "250",
        "wrong_answer": "25",
        "support_span": "1 meter is 100 centimeters",
        "error_span": "1 meter is 10 centimeters",
        "valid_body": "1 meter is 100 centimeters, so 2.5 meters is 2.5*100 = 250 centimeters.",
        "invalid_body": "1 meter is 10 centimeters, so 2.5 meters may look like 25 centimeters. Using the correct conversion, 1 meter is 100 centimeters, so 2.5*100 = 250.",
        "correction": "Meters convert to centimeters by multiplying by 100, not 10.",
    },
    {
        "task_id": "hours_to_minutes_decimal",
        "family": "unit_scale",
        "problem": "How many minutes are in 1.75 hours?",
        "gold_answer": "105",
        "wrong_answer": "175",
        "support_span": "1 hour is 60 minutes",
        "error_span": "1 hour is 100 minutes",
        "valid_body": "1 hour is 60 minutes, so 1.75 hours is 1.75*60 = 105 minutes.",
        "invalid_body": "1 hour is 100 minutes, so 1.75 hours looks like 175 minutes. With the correct conversion, multiply 1.75 by 60 to get 105 minutes.",
        "correction": "Hours use 60 minutes, not a decimal base of 100 minutes.",
    },
    {
        "task_id": "strict_vs_inclusive_english",
        "family": "quantifier_inequality",
        "problem": "How many integers are greater than 2 and at most 5?",
        "gold_answer": "3",
        "wrong_answer": "4",
        "support_span": "Greater than 2 excludes 2, and at most 5 includes 5",
        "error_span": "greater than 2 includes 2",
        "valid_body": "Greater than 2 excludes 2, and at most 5 includes 5, so the integers are 3, 4, and 5: three values.",
        "invalid_body": "Greater than 2 includes 2. Listing the values that actually satisfy the condition gives 3, 4, and 5, so there are 3.",
        "correction": "Strict greater-than excludes the endpoint 2.",
    },
    {
        "task_id": "no_more_than_boundary",
        "family": "quantifier_inequality",
        "problem": "How many positive integers are no more than 4?",
        "gold_answer": "4",
        "wrong_answer": "3",
        "support_span": "no more than 4 includes 4",
        "error_span": "no more than 4 means strictly less than 4",
        "valid_body": "No more than 4 includes 4, so the positive integers are 1, 2, 3, and 4: four values.",
        "invalid_body": "No more than 4 means strictly less than 4, so 4 should be excluded. But the phrase includes 4, giving 1, 2, 3, and 4: four values.",
        "correction": "No more than is inclusive of the upper bound.",
    },
    {
        "task_id": "before_after_weekday",
        "family": "order_comparison",
        "problem": "If today is Monday, what day is 3 days after today?",
        "gold_answer": "Thursday",
        "wrong_answer": "Friday",
        "support_span": "Thursday after 3 days",
        "error_span": "after today means counting Monday as the first day",
        "valid_body": "Three days after Monday is Tuesday after 1 day, Wednesday after 2 days, and Thursday after 3 days.",
        "invalid_body": "After today means counting Monday as the first day. Counting the days after Monday correctly gives Tuesday, Wednesday, then Thursday.",
        "correction": "After today starts with the next day, not today itself.",
    },
    {
        "task_id": "rate_time_distance",
        "family": "rate_ratio",
        "problem": "A car travels at 60 miles per hour for 1.5 hours. How many miles does it travel?",
        "gold_answer": "90",
        "wrong_answer": "40",
        "support_span": "distance equals speed times time",
        "error_span": "distance equals speed divided by time",
        "valid_body": "Distance equals speed times time, so 60*1.5 = 90 miles.",
        "invalid_body": "Distance equals speed divided by time, which would suggest 60/1.5. Using the correct relation, distance = speed*time = 60*1.5 = 90.",
        "correction": "For constant speed, distance is speed multiplied by time.",
    },
    {
        "task_id": "ratio_reversal",
        "family": "rate_ratio",
        "problem": "The ratio of cats to dogs is 2:3. If there are 12 dogs, how many cats are there?",
        "gold_answer": "8",
        "wrong_answer": "18",
        "support_span": "cats to dogs is 2 to 3",
        "error_span": "cats to dogs 2:3 means cats are 3/2 of dogs",
        "valid_body": "Cats to dogs is 2 to 3, so cats = (2/3)*12 = 8.",
        "invalid_body": "Cats to dogs 2:3 means cats are 3/2 of dogs. Using the actual order of the ratio, cats = (2/3)*12 = 8.",
        "correction": "The ratio order is cats/dogs = 2/3, not 3/2.",
    },
    {
        "task_id": "negative_inequality_flip",
        "family": "algebra_transform",
        "problem": "Solve the inequality -2x < 6. What inequality describes x?",
        "gold_answer": "x > -3",
        "wrong_answer": "x < -3",
        "support_span": "Dividing both sides by -2 flips the inequality",
        "error_span": "dividing by -2 keeps the inequality direction",
        "valid_body": "Dividing both sides by -2 flips the inequality, so x > -3.",
        "invalid_body": "Dividing by -2 keeps the inequality direction, so it would look like x < -3. Because division by a negative flips the sign, the correct result is x > -3.",
        "correction": "Inequality direction reverses when multiplying or dividing by a negative.",
    },
    {
        "task_id": "sqrt_extraneous_root",
        "family": "algebra_transform",
        "problem": "Solve sqrt(x+1) = x - 1.",
        "gold_answer": "3",
        "wrong_answer": "0 and 3",
        "support_span": "Checking in the original equation rejects x=0 and keeps x=3",
        "error_span": "squaring preserves all roots without needing a check",
        "valid_body": "Squaring gives x+1 = (x-1)^2, so x(x-3)=0. Checking in the original equation rejects x=0 and keeps x=3.",
        "invalid_body": "Squaring preserves all roots without needing a check, so x=0 and x=3 both arise. Checking the original equation rejects x=0 and keeps x=3.",
        "correction": "Squaring can introduce extraneous roots, so candidates must be checked.",
    },
    {
        "task_id": "combination_ordered_vs_unordered",
        "family": "counting_combinatorics",
        "problem": "How many ways are there to choose 2 students from 5 students?",
        "gold_answer": "10",
        "wrong_answer": "20",
        "support_span": "choosing 2 students is unordered",
        "error_span": "choosing 2 students is ordered",
        "valid_body": "Choosing 2 students is unordered, so the count is C(5,2)=5*4/2=10.",
        "invalid_body": "Choosing 2 students is ordered, so 5*4=20. Since the choice is unordered, divide by 2 to get C(5,2)=10.",
        "correction": "A chosen pair has no order, so permutations double-count.",
    },
    {
        "task_id": "table_row_column_total",
        "family": "table_interpretation",
        "problem": "A table shows apples sold: Monday 7, Tuesday 5, Wednesday 8. How many apples were sold in total?",
        "gold_answer": "20",
        "wrong_answer": "8",
        "support_span": "total apples are the sum across days",
        "error_span": "total apples means the largest single-day entry",
        "valid_body": "Total apples are the sum across days: 7+5+8 = 20.",
        "invalid_body": "Total apples means the largest single-day entry, which is 8. Adding across the days gives the actual total: 7+5+8 = 20.",
        "correction": "A total over days sums entries; it is not the maximum entry.",
    },
    {
        "task_id": "python_range_boundary",
        "family": "code_execution",
        "problem": "In Python, what is the value of s after: s=0; for i in range(1,4): s += i ?",
        "gold_answer": "6",
        "wrong_answer": "10",
        "support_span": "range(1,4) includes 1, 2, and 3, but excludes 4",
        "error_span": "range(1,4) includes 4",
        "valid_body": "range(1,4) includes 1, 2, and 3, but excludes 4, so s = 1+2+3 = 6.",
        "invalid_body": "range(1,4) includes 4, suggesting 1+2+3+4. But Python excludes the stop value, so the loop adds 1+2+3 = 6.",
        "correction": "Python range excludes the stop endpoint.",
    },
    {
        "task_id": "integer_division_floor",
        "family": "code_execution",
        "problem": "In Python, what is the value of 7//2?",
        "gold_answer": "3",
        "wrong_answer": "4",
        "support_span": "7//2 is floor division",
        "error_span": "integer division rounds to the nearest integer",
        "valid_body": "7//2 is floor division. Since 7/2 = 3.5, the floor is 3.",
        "invalid_body": "Integer division rounds to the nearest integer, which would be 4. In Python, // is floor division, so 7//2 = 3.",
        "correction": "Python // floors for positive numbers rather than rounding to nearest.",
    },
    {
        "task_id": "proof_invalid_converse",
        "family": "proof_validity",
        "problem": "A proof tries to show: if n is a multiple of 4, then n is even. Is the conclusion true? Give the final truth value.",
        "gold_answer": "true",
        "wrong_answer": "false",
        "support_span": "n=4k=2(2k), so n is even",
        "error_span": "all even numbers are multiples of 4",
        "valid_body": "If n is a multiple of 4, then n=4k=2(2k), so n is even. The conclusion is true.",
        "invalid_body": "All even numbers are multiples of 4, so the implication should hold. More directly, if n=4k then n=2(2k), so n is even; the conclusion is true.",
        "correction": "The converse 'all even numbers are multiples of 4' is false, even though the target implication is true.",
    },
]


def with_final(body: str, answer: str) -> str:
    return f"{body}\nFinal answer: {answer}"


def q(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def main() -> None:
    rows = []
    pairs = []
    base = 540000
    for i, case in enumerate(CASES):
        valid_idx = base + i * 10 + 1
        bad_idx = base + i * 10 + 2
        common = {
            "task_id": case["task_id"],
            "family": case["family"],
            "problem": case["problem"],
            "gold_answer": case["gold_answer"],
            "manual_final_correct": True,
            "manual_format_valid": True,
            "support_span": case["support_span"],
            "error_span": case["error_span"],
            "manual_correction": case["correction"],
            "gold_label_in_prompt": False,
            "known_error_span_in_prompt": False,
            "known_error_span_annotation_in_prompt": False,
        }
        rows.append({**common, "audit_idx": valid_idx, "e39_variant": "valid_correct", "e54_variant": "valid_correct", "completion": with_final(case["valid_body"], case["gold_answer"]), "manual_process_valid": True, "is_acpi": False})
        rows.append({**common, "audit_idx": bad_idx, "e39_variant": "invalid_correct", "e54_variant": "invalid_correct", "completion": with_final(case["invalid_body"], case["gold_answer"]), "manual_process_valid": False, "is_acpi": True})
        pairs.append({"id": f"e54_{case['task_id']}_bad{bad_idx}_valid{valid_idx}", "task_id": case["task_id"], "model_key": "e54_controlled", "bad_idx": bad_idx, "valid_idx": valid_idx, "problem": case["problem"], "error_span": case["error_span"], "support_span": case["support_span"]})
    for row in rows:
        span = row["support_span"] if row["manual_process_valid"] else row["error_span"]
        if span.lower() not in row["completion"].lower():
            raise SystemExit(f"Span missing for {row['task_id']}: {span}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    PAIRS.parent.mkdir(parents=True, exist_ok=True)
    lines = ["pairs:"]
    for p in pairs:
        lines.extend([
            f"  - id: {p['id']}",
            f"    task_id: {p['task_id']}",
            f"    model_key: {p['model_key']}",
            f"    bad_idx: {p['bad_idx']}",
            f"    valid_idx: {p['valid_idx']}",
            f"    problem: {q(p['problem'])}",
            f"    error_span: {q(p['error_span'])}",
            f"    support_span: {q(p['support_span'])}",
        ])
    PAIRS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "pairs": len(pairs), "out": str(OUT), "pairs_yaml": str(PAIRS)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
