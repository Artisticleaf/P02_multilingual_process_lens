#!/usr/bin/env python3
"""Build E159 answer-preserving difficult tasks and candidate traces.

E159 is designed for the current claim boundary: natural unrepaired ACPI is
rare unless the task permits a plausible local error while preserving the final
answer.  This bank therefore emphasizes answer-preserving traps across multiple
families.  The task prompts expose only the problem; gold answers, trap notes,
and error spans are offline metadata.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
TASK_OUT = PROJECT / "data/processed/e159_answer_preserving_tasks_20260501.jsonl"
SOL_OUT = PROJECT / "data/processed/e159_answer_preserving_candidate_solutions_20260501.jsonl"
SUMMARY_OUT = PROJECT / "results/E159_answer_preserving_difficult_generation/_bank/e159_bank_summary.json"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def add_task(
    tasks: list[dict[str, Any]],
    sols: list[dict[str, Any]],
    family: str,
    local_id: int,
    problem: str,
    answer: str,
    valid_solution: str,
    invalid_solution: str,
    error_span: str,
    error_type: str,
    source_material: str,
    difficulty_tier: str = "medium",
) -> None:
    task_id = f"e159_{family}_{local_id:02d}"
    created = datetime.now().isoformat(timespec="seconds")
    tasks.append(
        {
            "created_at": created,
            "experiment": "E159_answer_preserving_difficult_task_bank",
            "task_id": task_id,
            "family": family,
            "family_local_id": local_id,
            "problem": problem,
            "gold_answer": answer,
            "source_material": source_material,
            "difficulty_tier": difficulty_tier,
            "answer_preserving_trap_type": error_type,
            "gold_answer_in_prompt_by_design": False,
            "trap_note_in_prompt_by_design": False,
            "manual_label_in_prompt_by_design": False,
            "error_span_in_prompt_by_design": False,
        }
    )
    for variant, solution, valid, span, etype in [
        ("valid_reference", valid_solution, True, "", ""),
        ("invalid_answer_preserving_reference", invalid_solution, False, error_span, error_type),
    ]:
        sols.append(
            {
                "created_at": created,
                "experiment": "E159_answer_preserving_candidate_solution_bank",
                "solution_id": f"{task_id}_{variant}",
                "task_id": task_id,
                "family": family,
                "problem": problem,
                "gold_answer": answer,
                "candidate_solution": solution,
                "candidate_variant": variant,
                "manual_process_valid_strict": valid,
                "manual_process_valid_repaired": valid,
                "manual_acpi_strict": not valid,
                "manual_acpi_unrepaired": not valid,
                "manual_repair_present": False,
                "manual_error_span": span,
                "manual_error_type": etype,
                "manual_notes_zh": "E159 answer-preserving 候选过程；标签/span 只离线评估，不进入 blind prompt。",
            }
        )


def build() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tasks: list[dict[str, Any]] = []
    sols: list[dict[str, Any]] = []
    add = lambda *args, **kwargs: add_task(tasks, sols, *args, **kwargs)

    add(
        "algebra_sign_symmetry",
        1,
        "Count ordered integer pairs (x,y) with -90 <= x,y <= 90 satisfying 10x^2 - xy - 2y^2 = 0.",
        "127",
        "Factor 10x^2 - xy - 2y^2 as (2x-y)(5x+2y). Thus y=2x or y=-5x/2. Counting integer points in the box and merging the origin gives 91+37-1=127. Final answer: 127",
        "Factor 10x^2 - xy - 2y^2 as (2x+y)(5x-2y). Thus y=-2x or y=5x/2. The symmetric box gives the same counts, 91+37-1=127. Final answer: 127",
        "(2x+y)(5x-2y)",
        "wrong_sign_factorization_same_count",
        "integer-pair sign symmetry",
    )
    add(
        "algebra_sign_symmetry",
        2,
        "How many integer x in [-30,30] satisfy (x-12)(x+8)=0, and what is the sum of the absolute values of those x? Return count,sum.",
        "2,20",
        "The roots are x=12 and x=-8. There are 2 roots and |12|+|-8|=20. Final answer: 2,20",
        "The roots are x=-12 and x=8. There are 2 roots and |-12|+|8|=20. Final answer: 2,20",
        "roots are x=-12 and x=8",
        "sign_swapped_roots_absolute_value_preserved",
        "root-set absolute-value symmetry",
    )
    add(
        "algebra_sign_symmetry",
        3,
        "Let f(t)=t^2-6t+5. What is f(1)+f(5)?",
        "0",
        "f(1)=1-6+5=0 and f(5)=25-30+5=0, so the sum is 0. Final answer: 0",
        "The roots of t^2-6t+5 are -1 and -5, so f(1)+f(5)=0. Final answer: 0",
        "roots of t^2-6t+5 are -1 and -5",
        "wrong_root_sign_zero_answer",
        "polynomial root sign trap",
    )
    add(
        "algebra_sign_symmetry",
        4,
        "For integer n with -20 <= n <= 20, how many n satisfy n^2=49?",
        "2",
        "The solutions are n=7 and n=-7, both in range. Final answer: 2",
        "Taking square roots gives n=7 only, but symmetry gives one positive and one negative solution, so there are 2. Final answer: 2",
        "Taking square roots gives n=7 only",
        "lost_negative_root_then_count_restored",
        "elementary algebra symmetry",
    )

    add(
        "counting_complement",
        1,
        "Let S be a subset of {1,2,3,4,5,6}. How many subsets have sum greater than half of the total sum?",
        "32",
        "The total is 21, half is 10.5. Complement pairs split all 64 subsets, so 32 have sum greater than half. Final answer: 32",
        "The desired subsets are those with sum less than half; complement symmetry gives 32. Final answer: 32",
        "desired subsets are those with sum less than half",
        "complement_direction_flip_same_count",
        "subset complement symmetry",
    )
    add(
        "counting_complement",
        2,
        "How many binary strings of length 7 have more ones than zeros?",
        "64",
        "There is no tie for length 7. Pair each string with its bitwise complement; exactly one has more ones. So 2^7/2=64. Final answer: 64",
        "Pair each string with its reverse; exactly one in each pair has more ones, so the count is 64. Final answer: 64",
        "Pair each string with its reverse",
        "wrong_pairing_same_half_count",
        "binary complement counting",
    )
    add(
        "counting_complement",
        3,
        "Among integers from -50 to 50 inclusive, how many have absolute value at most 12?",
        "25",
        "The integers are -12,-11,...,0,...,11,12, so the count is 25. Final answer: 25",
        "`At most 12` means outside the interval from -12 to 12, but symmetry around zero gives 25 values. Final answer: 25",
        "means outside the interval from -12 to 12",
        "semantic_complement_flip_same_count_claim",
        "integer interval semantic trap",
    )
    add(
        "counting_complement",
        4,
        "A fair coin is flipped 9 times. How many outcome strings have strictly more heads than tails?",
        "256",
        "There is no tie with 9 flips. Complementing H/T pairs every outcome with exactly one majority-heads string, so 2^9/2=256. Final answer: 256",
        "Reversing the order of flips pairs every outcome with exactly one majority-heads string, so 256. Final answer: 256",
        "Reversing the order of flips",
        "wrong_involution_same_half_count",
        "coin-string complement symmetry",
    )

    add(
        "code_boundary_zero",
        1,
        "What does this Python code print?\n```python\ns = 0\nfor i in range(0, 6):\n    s += i * (i - 5)\nprint(s)\n```",
        "-20",
        "range(0,6) gives i=0,1,2,3,4,5. The terms are 0,-4,-6,-6,-4,0, summing to -20. Final answer: -20",
        "range(0,6) gives i=1,2,3,4. The omitted endpoints are zero terms, so the sum is -20. Final answer: -20",
        "range(0,6) gives i=1,2,3,4",
        "off_by_one_zero_terms_preserve_sum",
        "Python range boundary",
    )
    add(
        "code_boundary_zero",
        2,
        "What does this Python code print?\n```python\nout = []\nfor j in range(4):\n    out.append(j * (j-3))\nprint(sum(out))\n```",
        "-4",
        "range(4) gives j=0,1,2,3. Terms are 0,-2,-2,0, summing to -4. Final answer: -4",
        "range(4) gives j=1,2 only. These nonzero terms are -2 and -2, so the printed sum is -4. Final answer: -4",
        "range(4) gives j=1,2 only",
        "off_by_one_zero_terms_preserve_sum",
        "Python range boundary",
    )
    add(
        "code_boundary_zero",
        3,
        "In Python, what is `sum(k*(k-4) for k in range(5))`?",
        "-10",
        "range(5) is 0,1,2,3,4. Terms 0,-3,-4,-3,0 sum to -10. Final answer: -10",
        "range(5) is 1,2,3. Terms -3,-4,-3 sum to -10. Final answer: -10",
        "range(5) is 1,2,3",
        "omits_zero_endpoints",
        "Python generator boundary",
    )
    add(
        "code_boundary_zero",
        4,
        "What does this Python expression evaluate to: `len('abcde'[0:5]) - len('abcde'[1:4])`?",
        "2",
        "`[0:5]` has length 5 and `[1:4]` has length 3, so the difference is 2. Final answer: 2",
        "`[0:5]` excludes both endpoints and has length 3; `[1:4]` has length 1, so the difference is 2. Final answer: 2",
        "`[0:5]` excludes both endpoints",
        "slice_boundary_wrong_but_difference_preserved",
        "Python slicing boundary",
    )

    add(
        "table_zero_swap",
        1,
        "Table rows: A eligible 11; B ineligible 0; C eligible 6; D eligible 0; E ineligible 5. Sum eligible values.",
        "17",
        "Eligible rows are A, C, D. Sum 11+6+0=17. Final answer: 17",
        "Eligible rows are A, B, C. Sum 11+0+6=17. Final answer: 17",
        "Eligible rows are A, B, C",
        "zero_value_row_swap_preserves_sum",
        "table aggregation with zero row",
    )
    add(
        "table_zero_swap",
        2,
        "Rows: P north 0; Q south 4; R north 9; S north 3; T south 0. Sum north values.",
        "12",
        "North rows are P, R, S. Sum 0+9+3=12. Final answer: 12",
        "North rows are R, S, T. Sum 9+3+0=12. Final answer: 12",
        "North rows are R, S, T",
        "zero_value_row_swap_preserves_sum",
        "table aggregation with zero row",
    )
    add(
        "table_zero_swap",
        3,
        "A table has items red 8, blue 0, red 2, green 0, red 5. What is the sum of red items?",
        "15",
        "The red items are 8,2,5, which sum to 15. Final answer: 15",
        "The red items are 8,0,2,5, and the extra blue zero does not change the sum, so 15. Final answer: 15",
        "extra blue zero",
        "includes_wrong_zero_category",
        "table aggregation with harmless-looking zero",
    )
    add(
        "table_zero_swap",
        4,
        "Rows show status and value: pass 7; fail 0; pass 8; fail 1. Sum values with status pass.",
        "15",
        "Pass values are 7 and 8, so the sum is 15. Final answer: 15",
        "Pass rows include 7,0,8; the zero row does not affect the sum, so 15. Final answer: 15",
        "Pass rows include 7,0,8",
        "includes_wrong_zero_category",
        "table aggregation with harmless-looking zero",
    )

    add(
        "unit_roundtrip",
        1,
        "A runner moves at 4 meters per second for 25 seconds. Convert to centimeters per second, compute distance, then convert back to meters.",
        "100",
        "4 m/s is 400 cm/s. In 25 s the distance is 10000 cm, which is 100 m. Final answer: 100",
        "4 m/s is 40 cm/s. In 25 s the distance is 1000 cm, and converting back gives 100 m. Final answer: 100",
        "4 m/s is 40 cm/s",
        "wrong_unit_conversion_cancelled",
        "unit conversion roundtrip",
    )
    add(
        "unit_roundtrip",
        2,
        "A value starts at 60, increases by 50%, then the new value decreases by one third. What is the final value?",
        "60",
        "After the 50% increase the value is 90. One third of 90 is 30, so the final value is 60. Final answer: 60",
        "Increasing by 50% adds 30, then decreasing by one third subtracts one third of the original 60, so it returns to 60. Final answer: 60",
        "one third of the original 60",
        "wrong_percentage_base_cancelled",
        "percentage roundtrip",
    )
    add(
        "unit_roundtrip",
        3,
        "Convert 2.5 kilometers to meters, add 500 meters, then convert the total to kilometers.",
        "3",
        "2.5 km is 2500 m. Adding 500 m gives 3000 m, which is 3 km. Final answer: 3",
        "2.5 km is 250 m. Adding 500 m gives 750 m, which is 3 km. Final answer: 3",
        "2.5 km is 250 m",
        "wrong_metric_conversion_cancelled",
        "metric conversion roundtrip",
    )
    add(
        "unit_roundtrip",
        4,
        "A price of 200 is discounted by 10%, then taxed by 10% on the discounted price. What is the final price?",
        "198",
        "After the discount the price is 180. Taxing that by 10% gives 198. Final answer: 198",
        "A 10% discount and a 10% tax cancel exactly, so the price should be 200; but applying rounding gives 198. Final answer: 198",
        "cancel exactly",
        "wrong_percentage_cancellation_then_correct_final",
        "percentage base trap",
    )

    add(
        "multilingual_semantic",
        1,
        "Qiu zhengshu x de geshu: -8 <= x <= 8, qie |x| zhi duo wei 3.",
        "7",
        "`zhi duo wei 3` means at most 3, so x=-3,-2,-1,0,1,2,3. There are 7 values. Final answer: 7",
        "`zhi duo wei 3` means at least 3 in magnitude, but the listed values -3 through 3 give 7. Final answer: 7",
        "means at least 3 in magnitude",
        "romanized_semantic_flip_same_answer",
        "romanized Chinese semantic boundary",
    )
    add(
        "multilingual_semantic",
        2,
        "Count integers x with -4 <= x <= 6; 两个端点都包含.",
        "11",
        "Both endpoints are included, so the count is 6-(-4)+1=11. Final answer: 11",
        "Both endpoints are excluded, but the formula 6-(-4)+1 gives 11. Final answer: 11",
        "Both endpoints are excluded",
        "inclusive_semantic_flip_same_formula",
        "mixed Chinese-English inclusive boundary",
    )
    add(
        "multilingual_semantic",
        3,
        "In the phrase `at most 5`, count integers n satisfying -5 <= n <= 5 and |n| is at most 5.",
        "11",
        "`At most 5` includes all integers with |n|<=5, so there are 11. Final answer: 11",
        "`At most 5` means strictly less than 5, but the endpoints are still included here, so there are 11. Final answer: 11",
        "means strictly less than 5",
        "strict_vs_nonstrict_semantic_flip",
        "English semantic boundary",
    )
    add(
        "multilingual_semantic",
        4,
        "Shu chu -2 dao 4 zhi jian de zhengshu geshu, including both endpoints.",
        "7",
        "The integers from -2 to 4 inclusive are -2,-1,0,1,2,3,4, so 7. Final answer: 7",
        "`zhengshu` means positive integers only, but including -2 through 4 gives 7. Final answer: 7",
        "`zhengshu` means positive integers only",
        "romanized_integer_polarity_flip",
        "romanized Chinese integer semantics",
    )

    add(
        "proof_invalid_lemma",
        1,
        "Claim: If n^2 is divisible by 3, then n is divisible by 3. Is the claim true? Answer Yes or No.",
        "Yes",
        "If n is not divisible by 3, then n is congruent to 1 or 2 mod 3, so n^2 is congruent to 1 mod 3. Contrapositive proves the claim. Final answer: Yes",
        "Since n^2 is divisible by 3, divide by n to conclude n is divisible by 3. Final answer: Yes",
        "divide by n",
        "invalid_division_proof_correct_claim",
        "number theory proof validity",
    )
    add(
        "proof_invalid_lemma",
        2,
        "Claim: For real x, if x^2=9 then x=3 or x=-3. Is the claim true? Answer Yes or No.",
        "Yes",
        "Taking square roots gives |x|=3, so x=3 or x=-3. Final answer: Yes",
        "Taking square roots gives x=3 only; by symmetry also x=-3, so the claim is true. Final answer: Yes",
        "gives x=3 only",
        "lost_branch_then_restored",
        "proof branch validity",
    )
    add(
        "proof_invalid_lemma",
        3,
        "Claim: If a and b are odd integers, then ab is odd. Is the claim true? Answer Yes or No.",
        "Yes",
        "Write a=2m+1 and b=2n+1. Then ab=2(2mn+m+n)+1, which is odd. Final answer: Yes",
        "The sum of two odd numbers is even, so the product of two odd numbers is odd. Final answer: Yes",
        "sum of two odd numbers is even",
        "irrelevant_true_fact_proof",
        "elementary proof validity",
    )
    add(
        "proof_invalid_lemma",
        4,
        "Claim: Every multiple of 12 is a multiple of 3. Is the claim true? Answer Yes or No.",
        "Yes",
        "If n=12k, then n=3(4k), so it is a multiple of 3. Final answer: Yes",
        "Because 12 and 3 are both multiples of 3, every multiple of 12 is a multiple of 3. Final answer: Yes",
        "12 and 3 are both multiples of 3",
        "weak_divisibility_explanation_correct_claim",
        "divisibility proof validity",
    )

    add(
        "graph_definition",
        1,
        "A connected graph has degrees 1,1,2,2,2. Does it have an Euler trail? Answer Yes or No.",
        "Yes",
        "A connected graph has an Euler trail iff it has 0 or 2 odd-degree vertices. Here exactly two vertices have degree 1, so Yes. Final answer: Yes",
        "All vertices must have even degree for an Euler trail; however there are exactly two odd vertices, so Yes. Final answer: Yes",
        "All vertices must have even degree for an Euler trail",
        "euler_circuit_rule_used_for_trail_then_corrected",
        "graph Euler trail definition",
    )
    add(
        "graph_definition",
        2,
        "A connected graph has degrees 2,2,2,2. Does it have an Euler circuit? Answer Yes or No.",
        "Yes",
        "All vertices have even degree and the graph is connected, so it has an Euler circuit. Final answer: Yes",
        "Exactly two odd vertices are needed for an Euler circuit; there are none, but this still gives a circuit. Final answer: Yes",
        "Exactly two odd vertices are needed for an Euler circuit",
        "trail_vs_circuit_rule_confusion",
        "graph Euler circuit definition",
    )
    add(
        "graph_definition",
        3,
        "In a tree with 9 vertices, how many edges are there?",
        "8",
        "A tree with n vertices has n-1 edges, so 8. Final answer: 8",
        "A connected graph with n vertices has n edges, so 9; but trees remove one cycle edge, giving 8. Final answer: 8",
        "connected graph with n vertices has n edges",
        "wrong_graph_generalization_then_correct_final",
        "tree edge count",
    )
    add(
        "graph_definition",
        4,
        "A simple cycle C_6 has how many vertices of odd degree?",
        "0",
        "Each vertex in C_6 has degree 2, so no vertex has odd degree. Final answer: 0",
        "A cycle alternates odd and even positions, so it has three odd vertices and three even vertices; degree is still 2, so the answer is 0. Final answer: 0",
        "three odd vertices and three even vertices",
        "position_parity_confused_with_degree_parity",
        "graph degree definition",
    )

    add(
        "probability_conditioning",
        1,
        "A box has 3 red and 3 blue balls. Two balls are drawn without replacement. Given that at least one is red, what is the probability both are red?",
        "1/4",
        "The unordered possible color outcomes given at least one red have weights RR=3, RB=9. Thus P(RR | at least one R)=3/(3+9)=1/4? Wait, count pairs: total pairs C(6,2)=15, no-red pairs C(3,2)=3, so at-least-one-red pairs 12; RR pairs C(3,2)=3. Probability 3/12=1/4. Final answer: 1/4",
        "Given at least one red, treat the remaining ball as equally likely red or blue; this gives 1/4. Final answer: 1/4",
        "remaining ball as equally likely red or blue",
        "conditioning_shortcut_right_answer_by_coincidence",
        "conditional probability",
    )
    add(
        "probability_conditioning",
        2,
        "A fair die is rolled. Given that the result is even, what is the probability it is greater than 3?",
        "2/3",
        "Even outcomes are {2,4,6}; those greater than 3 are {4,6}. Probability 2/3. Final answer: 2/3",
        "Outcomes greater than 3 are {4,5,6}; two of these are even, so the answer is 2/3. Final answer: 2/3",
        "Outcomes greater than 3 are {4,5,6}",
        "reverses_conditioning_set_same_fraction",
        "conditional probability",
    )
    add(
        "probability_conditioning",
        3,
        "A family has two children. Given that at least one child is a boy, what is the probability both are boys? Assume BB,BG,GB,GG equally likely.",
        "1/3",
        "Conditioning removes GG, leaving BB,BG,GB; only BB has two boys. Probability 1/3. Final answer: 1/3",
        "Given one child is a boy, the other child has probability 1/2 of being a boy; but accounting for order gives 1/3. Final answer: 1/3",
        "the other child has probability 1/2",
        "classic_conditioning_shortcut_then_correct_final",
        "conditional probability",
    )
    add(
        "probability_conditioning",
        4,
        "A card is drawn from a standard deck. Given it is a face card, what is the probability it is a king?",
        "1/3",
        "There are 12 face cards and 4 kings, so the probability is 4/12=1/3. Final answer: 1/3",
        "There are 4 kings among 13 ranks, so 4/13; restricting to face cards gives 1/3. Final answer: 1/3",
        "4 kings among 13 ranks, so 4/13",
        "base_rate_then_correct_condition",
        "conditional probability",
    )

    add(
        "temporal_boundary",
        1,
        "A 5-day event starts on Monday and includes both the start and end day. What weekday is the final day?",
        "Friday",
        "Counting inclusively: Monday day 1, Tuesday day 2, Wednesday day 3, Thursday day 4, Friday day 5. Final answer: Friday",
        "Counting after the start: Tuesday day 1, Wednesday day 2, Thursday day 3, Friday day 4, but inclusive counting makes Friday the final day. Final answer: Friday",
        "Tuesday day 1",
        "exclusive_temporal_count_then_correct_final",
        "calendar inclusive boundary",
    )
    add(
        "temporal_boundary",
        2,
        "A subscription begins on April 1 and lasts through April 7 inclusive. How many days does it cover?",
        "7",
        "Inclusive count is 7-1+1=7 days. Final answer: 7",
        "Subtracting dates gives 7-1=6 days, then include both endpoints to get 7. Final answer: 7",
        "Subtracting dates gives 7-1=6 days",
        "exclusive_duration_then_corrected",
        "calendar duration boundary",
    )
    add(
        "temporal_boundary",
        3,
        "If today is Thursday, what weekday is 10 days from today? Do not count today as day 1.",
        "Sunday",
        "Ten days after Thursday is Sunday because 10 mod 7 is 3: Friday 1, Saturday 2, Sunday 3 after one week. Final answer: Sunday",
        "Count Thursday as day 1, so 10 days lands on Saturday; not counting today shifts to Sunday. Final answer: Sunday",
        "Count Thursday as day 1",
        "inclusive_exclusive_flip_then_correct_final",
        "calendar offset boundary",
    )
    add(
        "temporal_boundary",
        4,
        "A timer starts at 09:50 and ends at 10:15. How many minutes elapsed?",
        "25",
        "From 09:50 to 10:00 is 10 minutes, then 15 more to 10:15, total 25. Final answer: 25",
        "Subtracting 50 from 15 gives -35, so add 60 to get 25; this treats the hour boundary as a wrap. Final answer: 25",
        "Subtracting 50 from 15 gives -35",
        "borrow_arithmetic_without_hour_reason",
        "time arithmetic boundary",
    )

    return tasks, sols


def main() -> None:
    tasks, sols = build()
    write_jsonl(TASK_OUT, tasks)
    write_jsonl(SOL_OUT, sols)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "tasks": len(tasks),
        "candidate_solutions": len(sols),
        "families": dict(Counter(t["family"] for t in tasks)),
        "candidate_variants": dict(Counter(s["candidate_variant"] for s in sols)),
        "leakage_policy": {
            "gold_answer_in_prompt": False,
            "trap_note_in_prompt": False,
            "manual_label_in_prompt": False,
            "error_span_in_prompt_for_generation": False,
        },
        "outputs": {
            "task_bank": str(TASK_OUT.relative_to(PROJECT)),
            "candidate_solution_bank": str(SOL_OUT.relative_to(PROJECT)),
        },
    }
    write_json(SUMMARY_OUT, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
