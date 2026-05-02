#!/usr/bin/env python3
"""Build E153 difficult-scenario task and candidate-solution banks.

The task bank is for reasoning-first non-thinking generation.  The solution
bank is for non-thinking error-finding probes; it contains valid and deliberately
invalid proposed solutions with offline labels.  Prompts must not expose those
labels, gold answers, risk notes, or error spans.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
TASK_OUT = PROJECT / "data/processed/e153_difficult_scenario_tasks_20260501.jsonl"
SOL_OUT = PROJECT / "data/processed/e153_candidate_solution_bank_20260501.jsonl"
SUMMARY_OUT = PROJECT / "results/E153_nonthinking_difficult_scenario_generation/_bank/e153_bank_summary.json"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def add_task(
    tasks: list[dict[str, Any]],
    solutions: list[dict[str, Any]],
    family: str,
    local_id: int,
    problem: str,
    answer: str,
    valid_solution: str,
    invalid_solution: str,
    error_span: str,
    error_type: str,
    material: str,
) -> None:
    task_id = f"e153_{family}_{local_id:02d}"
    created = datetime.now().isoformat(timespec="seconds")
    tasks.append(
        {
            "created_at": created,
            "experiment": "E153_nonthinking_difficult_scenario",
            "task_id": task_id,
            "family": family,
            "family_local_id": local_id,
            "problem": problem,
            "gold_answer": answer,
            "source_material": material,
            "gold_answer_in_prompt_by_design": False,
            "trap_note_in_prompt_by_design": False,
            "manual_label_in_prompt_by_design": False,
            "error_span_in_prompt_by_design": False,
        }
    )
    for variant, completion, valid, span, etype in [
        ("valid_reference", valid_solution, True, "", ""),
        ("invalid_reference", invalid_solution, False, error_span, error_type),
    ]:
        solutions.append(
            {
                "created_at": created,
                "experiment": "E153_candidate_solution_bank",
                "solution_id": f"{task_id}_{variant}",
                "task_id": task_id,
                "family": family,
                "problem": problem,
                "gold_answer": answer,
                "candidate_solution": completion,
                "candidate_variant": variant,
                "manual_process_valid_strict": valid,
                "manual_process_valid_repaired": valid,
                "manual_acpi_strict": (not valid),
                "manual_acpi_unrepaired": (not valid),
                "manual_repair_present": False,
                "manual_error_span": span,
                "manual_error_type": etype,
                "manual_notes_zh": "E153 手写候选解；标签/span 只作离线评估，不进入找错 prompt。",
            }
        )


def build() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tasks: list[dict[str, Any]] = []
    sols: list[dict[str, Any]] = []
    add = lambda family, local, problem, ans, valid, invalid, span, etype, material: add_task(
        tasks, sols, family, local, problem, ans, valid, invalid, span, etype, material
    )

    add(
        "algebra_sign_factor",
        1,
        "Find the number of ordered integer pairs (x,y), with -100 <= x,y <= 100, satisfying 12x^2 - xy - 6y^2 = 0.",
        "117",
        "Factor 12x^2 - xy - 6y^2 as (3x+2y)(4x-3y). Thus y=-3x/2 or y=4x/3. Counting integer pairs in the box, including (0,0), gives 117. Final answer: 117",
        "Factor 12x^2 - xy - 6y^2 as (3x-2y)(4x+3y). Thus y=3x/2 or y=-4x/3. Counting integer pairs in the symmetric box gives 117. Final answer: 117",
        "(3x-2y)(4x+3y)",
        "wrong_factorization_sign",
        "AIME-style algebra sign symmetry",
    )
    add(
        "algebra_sign_factor",
        2,
        "Solve for the sum of integer x in [-50,50] satisfying (x-6)(x+4)=0.",
        "2",
        "The roots are x=6 and x=-4, both in the interval. Their sum is 2. Final answer: 2",
        "The roots are x=-6 and x=4, both in the interval. Their sum is -2. Since the requested sum is taken by magnitude, the answer is 2. Final answer: 2",
        "Since the requested sum is taken by magnitude",
        "invented_magnitude_condition",
        "synthetic algebra root-set trap",
    )

    add(
        "counting_invariant",
        1,
        "How many ordered integer pairs (x,y) with -20 <= x,y <= 20 satisfy |x+y| = 5?",
        "72",
        "For x+y=5 there are 36 choices of x in [-15,20]. For x+y=-5 there are 36 choices. Total 72. Final answer: 72",
        "This is equivalent to |x-y|=5. There are 36 choices for x-y=5 and 36 for x-y=-5, so the total is 72. Final answer: 72",
        "equivalent to |x-y|=5",
        "wrong_invariant_substitution",
        "synthetic lattice counting",
    )
    add(
        "counting_invariant",
        2,
        "Let S be a subset of {1,2,3,4,5}. How many subsets S have sum(S) greater than half of 15?",
        "16",
        "The total sum is 15, and no subset has sum 7.5. Complement pairs split the 32 subsets evenly, so 16 have sum greater than 7.5. Final answer: 16",
        "The total sum is 15, so subsets with sum less than half are the desired subsets. Complement pairing gives 16 such subsets. Final answer: 16",
        "subsets with sum less than half are the desired subsets",
        "wrong_complement_direction",
        "synthetic subset complement symmetry",
    )

    add(
        "code_boundary",
        1,
        "What does this Python code print?\n```python\ntotal = 0\nfor k in range(1, 8):\n    total += k * (k - 7)\nprint(total)\n```",
        "-56",
        "range(1,8) uses k=1,...,7. The terms are -6,-10,-12,-12,-10,-6,0, summing to -56. Final answer: -56",
        "range(1,8) uses k=1,...,6. The terms are -6,-10,-12,-12,-10,-6, summing to -56. Final answer: -56",
        "range(1,8) uses k=1,...,6",
        "off_by_one_omits_zero_boundary",
        "synthetic Python boundary",
    )
    add(
        "code_boundary",
        2,
        "What does this Python code print?\n```python\ns = 0\nfor i in range(5):\n    s += i * (i - 4)\nprint(s)\n```",
        "-10",
        "range(5) gives i=0,1,2,3,4. The terms are 0,-3,-4,-3,0, summing to -10. Final answer: -10",
        "range(5) gives i=1,2,3,4. The terms are -3,-4,-3,0, summing to -10. Final answer: -10",
        "range(5) gives i=1,2,3,4",
        "off_by_one_omits_zero_boundary",
        "synthetic Python boundary",
    )

    add(
        "table_aggregation",
        1,
        "Using the table, sum values whose label is eligible.\nA eligible 7\nB eligible 0\nC not_eligible 0\nD eligible 9\nE not_eligible 4",
        "16",
        "Eligible rows are A, B, and D. Their values sum to 7+0+9=16. Final answer: 16",
        "Eligible rows are A, C, and D. Their values sum to 7+0+9=16. Final answer: 16",
        "Eligible rows are A, C, and D",
        "zero_value_misclassification",
        "synthetic table aggregation",
    )
    add(
        "table_aggregation",
        2,
        "A table lists rows P north 12, Q south 0, R north 8, S south 5, T north 0. Sum the values of north rows.",
        "20",
        "North rows are P, R, and T. Sum 12+8+0=20. Final answer: 20",
        "North rows are P, Q, and R. Sum 12+0+8=20. Final answer: 20",
        "North rows are P, Q, and R",
        "zero_value_misclassification",
        "synthetic table aggregation",
    )

    add(
        "unit_percentage",
        1,
        "A value starts at 80, increases by 25%, then the new value decreases by 20%. What is the final value?",
        "80",
        "After increasing by 25%, the value is 100. Decreasing the new value by 20% gives 80. Final answer: 80",
        "Increasing by 25 adds 20, and decreasing by 20 subtracts the same original 20, so it returns to 80. Final answer: 80",
        "decreasing by 20 subtracts the same original 20",
        "wrong_percentage_base",
        "synthetic percentage roundtrip",
    )
    add(
        "unit_percentage",
        2,
        "A cart moves at 3 meters per second for 40 seconds. Convert speed to centimeters per second, compute distance, then convert back to meters.",
        "120",
        "3 m/s is 300 cm/s. In 40 seconds this is 12000 cm, which is 120 m. Final answer: 120",
        "3 m/s is 30 cm/s. In 40 seconds this is 1200 cm, which is 120 m. Final answer: 120",
        "3 m/s is 30 cm/s",
        "wrong_unit_conversion_cancelled",
        "synthetic unit roundtrip",
    )

    add(
        "multilingual_semantic",
        1,
        "Qiu zhengshu x de geshu, manzu -9 <= x <= 9, bingqie |x| zhi duo wei 4.",
        "9",
        "`zhi duo wei 4` means at most 4, so x=-4,-3,-2,-1,0,1,2,3,4. There are 9 values. Final answer: 9",
        "`zhi duo wei 4` means at least 4 in magnitude, so count x=-4,-3,-2,-1,0,1,2,3,4. There are 9 values. Final answer: 9",
        "means at least 4 in magnitude",
        "romanized_semantic_flip",
        "romanized Chinese semantic trap",
    )
    add(
        "multilingual_semantic",
        2,
        "Count integers x with -3 <= x <= 7; 两个端点都包含.",
        "11",
        "Both endpoints are included, so the count is 7-(-3)+1=11. Final answer: 11",
        "Both endpoints are excluded, so the count is 7-(-3)+1=11. Final answer: 11",
        "Both endpoints are excluded",
        "mixed_language_inclusive_flip",
        "mixed English-Chinese semantic trap",
    )

    add(
        "proof_validity",
        1,
        "A proposed proof claims: If n^2 is even, then n is even. Is the claim true? Give the answer Yes or No.",
        "Yes",
        "If n were odd, n=2k+1, then n^2=4k^2+4k+1 is odd. Contrapositive proves n is even. Final answer: Yes",
        "Since n^2 is even, divide both sides by n to conclude n is even. Final answer: Yes",
        "divide both sides by n",
        "invalid_division_reasoning",
        "elementary proof validity",
    )
    add(
        "proof_validity",
        2,
        "A proposed proof claims: For all real x, if x^2=4 then x=2. Is the claim true? Give Yes or No.",
        "No",
        "The claim is false because x=-2 also satisfies x^2=4. Final answer: No",
        "Taking square roots gives x=2, so the claim is true. Final answer: No",
        "Taking square roots gives x=2",
        "lost_negative_root",
        "elementary proof validity",
    )

    add(
        "probability_conditioning",
        1,
        "A test catches a condition 90% of the time when present and has a 10% false positive rate when absent. The condition affects 1% of people. Among people who test positive, is the condition more likely than not? Answer Yes or No.",
        "No",
        "Out of 10000 people, about 100 have the condition and 90 test positive. Of 9900 without it, 990 test positive. Most positives are false, so No. Final answer: No",
        "The test is 90% accurate when present, so a positive means the condition is more likely than not. Final answer: No",
        "a positive means the condition is more likely than not",
        "base_rate_neglect",
        "synthetic probability conditioning",
    )
    add(
        "probability_conditioning",
        2,
        "A fair coin is flipped twice. Given that at least one flip is heads, what is the probability both flips are heads?",
        "1/3",
        "Possible outcomes with at least one head are HH, HT, TH. Only HH has both heads, so probability is 1/3. Final answer: 1/3",
        "Given one head, the other flip is equally likely heads or tails, so probability is 1/2. Final answer: 1/3",
        "probability is 1/2",
        "conditional_sample_space_error",
        "classic conditional probability",
    )

    add(
        "graph_path_constraints",
        1,
        "In a directed graph, edges are A->B, B->C, C->A, A->D. How many vertices are reachable from C following edge directions, including C?",
        "4",
        "From C go to A, then B and D from A, then C from B. Reachable vertices are C,A,B,D, so 4. Final answer: 4",
        "Treating edges as undirected, C connects to B and A, and A connects to D, so 4. Final answer: 4",
        "Treating edges as undirected",
        "directed_edge_ignored",
        "synthetic directed graph",
    )
    add(
        "graph_path_constraints",
        2,
        "A graph has degrees 1,1,2,2,2. Does it have an Euler trail? Answer Yes or No.",
        "Yes",
        "A connected graph with exactly two odd-degree vertices has an Euler trail. Degrees 1 and 1 are odd, so Yes. Final answer: Yes",
        "All vertices must have even degree for an Euler trail, so the graph has no Euler trail. Final answer: Yes",
        "All vertices must have even degree for an Euler trail",
        "euler_path_vs_circuit_confusion",
        "synthetic graph parity",
    )

    add(
        "geometry_constraints",
        1,
        "An isosceles trapezoid has an incircle tangent to all four sides. The bases are 8 and 18. What is the length of each leg?",
        "13",
        "In a tangential quadrilateral, sums of opposite sides match, so leg+leg=8+18=26. Each leg is 13. Final answer: 13",
        "For an isosceles trapezoid, the leg is the average of the bases, (8+18)/2=13. Final answer: 13",
        "leg is the average of the bases",
        "wrong_geometry_rule_right_answer",
        "synthetic tangential trapezoid",
    )
    add(
        "geometry_constraints",
        2,
        "A point reflection of (2,3) through the origin gives what point?",
        "(-2,-3)",
        "Point reflection through the origin maps (x,y) to (-x,-y), so (-2,-3). Final answer: (-2,-3)",
        "Reflection through the origin swaps coordinates and changes signs, giving (-2,-3). Final answer: (-2,-3)",
        "swaps coordinates",
        "wrong_reflection_description",
        "synthetic geometry transformation",
    )

    add(
        "recurrence_dp",
        1,
        "Let a_0=0 and a_n=a_{n-1}+n for n>=1. What is a_5?",
        "15",
        "a_1=1, a_2=3, a_3=6, a_4=10, a_5=15. Final answer: 15",
        "Start with a_1=0, then add 1,2,3,4,5 to get 15. Final answer: 15",
        "Start with a_1=0",
        "wrong_base_case_cancelled",
        "synthetic recurrence",
    )
    add(
        "recurrence_dp",
        2,
        "How many binary strings of length 4 have no adjacent 1s?",
        "8",
        "Let f(n)=f(n-1)+f(n-2), f(1)=2, f(2)=3. Then f(3)=5 and f(4)=8. Final answer: 8",
        "Use f(n)=2f(n-1)-f(n-2) with f(1)=2, f(2)=3, giving f(4)=8. Final answer: 8",
        "Use f(n)=2f(n-1)-f(n-2)",
        "wrong_recurrence",
        "synthetic DP counting",
    )

    add(
        "string_regex_parsing",
        1,
        "In Python, what is len('ababa'.replace('aba','X'))?",
        "3",
        "Python replace scans non-overlapping occurrences. 'ababa'.replace('aba','X') becomes 'Xba', whose length is 3. Final answer: 3",
        "There are two overlapping 'aba' substrings, so both are replaced and the length is 3. Final answer: 3",
        "two overlapping 'aba' substrings",
        "overlap_replace_error",
        "synthetic string parsing",
    )
    add(
        "string_regex_parsing",
        2,
        "In Python, what is 'abcdef'[1:4]?",
        "bcd",
        "Slice [1:4] includes indices 1,2,3 and excludes 4, so the result is bcd. Final answer: bcd",
        "Slice [1:4] includes both endpoints 1 through 4, giving bcd. Final answer: bcd",
        "includes both endpoints",
        "slice_endpoint_error",
        "synthetic string slicing",
    )

    add(
        "temporal_order",
        1,
        "A meeting starts at 23:30 UTC on Monday and lasts 90 minutes. In UTC, what day does it end?",
        "Tuesday",
        "23:30 plus 90 minutes is 01:00 the next day, Tuesday. Final answer: Tuesday",
        "Since it starts Monday and lasts less than two hours, it ends on Monday. Final answer: Tuesday",
        "it ends on Monday",
        "day_rollover_missed",
        "synthetic time reasoning",
    )
    add(
        "temporal_order",
        2,
        "If a task is due 3 days after Friday, counting Saturday as day 1, what day is it due?",
        "Monday",
        "Saturday is day 1, Sunday day 2, Monday day 3. Final answer: Monday",
        "Friday is day 1, Saturday day 2, Sunday day 3, so it is due Monday. Final answer: Monday",
        "Friday is day 1",
        "inclusive_counting_error",
        "synthetic temporal counting",
    )

    add(
        "causal_counterfactual",
        1,
        "A sign says: If the alarm is armed, then the door light is on. The door light is on. Can we conclude the alarm is armed? Answer Yes or No.",
        "No",
        "This is affirming the consequent; the light could be on for another reason. Final answer: No",
        "The implication says armed causes light on, and the light is on, so the alarm is armed. Final answer: No",
        "the light is on, so the alarm is armed",
        "affirming_consequent",
        "synthetic logic/causal wording",
    )
    add(
        "causal_counterfactual",
        2,
        "A rule says: A badge is required to enter the lab. Sam has a badge. Does that guarantee Sam enters the lab? Answer Yes or No.",
        "No",
        "A required condition is necessary, not sufficient. Having a badge does not guarantee entry. Final answer: No",
        "Since a badge is required and Sam has one, Sam must enter. Final answer: No",
        "Sam must enter",
        "necessary_vs_sufficient",
        "synthetic causal/logic wording",
    )

    add(
        "set_venn",
        1,
        "In a group of 30, 18 like tea, 16 like coffee, and 10 like both. How many like exactly one of tea or coffee?",
        "14",
        "Exactly one is (18-10)+(16-10)=8+6=14. Final answer: 14",
        "Exactly one is 18+16-10=24, then subtract the 10 both again to get 14. Final answer: 14",
        "18+16-10=24",
        "union_vs_exactly_one_confusion",
        "synthetic Venn counting",
    )
    add(
        "set_venn",
        2,
        "How many integers from 1 to 20 inclusive are divisible by 2 or 5?",
        "12",
        "Multiples of 2:10, of 5:4, overlap multiples of 10:2. Inclusion-exclusion gives 10+4-2=12. Final answer: 12",
        "Multiples of 2 or 5 are 10+4+2=16, but remove the four endpoint cases to get 12. Final answer: 12",
        "10+4+2=16",
        "inclusion_exclusion_sign_error",
        "synthetic set counting",
    )

    add(
        "optimization_constraints",
        1,
        "Maximize x(10-x) over integers x with 0 <= x <= 10. What is the maximum value?",
        "25",
        "The parabola is maximized at x=5, giving 5*5=25. Final answer: 25",
        "The product is largest at the boundary x=10, giving 25 after symmetry adjustment. Final answer: 25",
        "largest at the boundary x=10",
        "boundary_optimum_error",
        "synthetic optimization",
    )
    add(
        "optimization_constraints",
        2,
        "Minimize (x-3)^2+4 over integers x. What is the minimum value?",
        "4",
        "The square is minimized at x=3, giving 0+4=4. Final answer: 4",
        "The square is minimized at x=0, but adding 4 gives the same minimum 4. Final answer: 4",
        "minimized at x=0",
        "wrong_argmin_right_value_claim",
        "synthetic optimization",
    )

    return tasks, sols


def main() -> None:
    tasks, sols = build()
    tasks = sorted(tasks, key=lambda r: (r["family"], r["family_local_id"]))
    sols = sorted(sols, key=lambda r: (r["family"], r["solution_id"]))
    write_jsonl(TASK_OUT, tasks)
    write_jsonl(SOL_OUT, sols)
    leakage = {
        "gold_answer_in_prompt_by_design_rows": sum(bool(r["gold_answer_in_prompt_by_design"]) for r in tasks),
        "trap_note_in_prompt_by_design_rows": sum(bool(r["trap_note_in_prompt_by_design"]) for r in tasks),
        "manual_label_in_prompt_by_design_rows": sum(bool(r["manual_label_in_prompt_by_design"]) for r in tasks),
        "error_span_in_prompt_by_design_rows": sum(bool(r["error_span_in_prompt_by_design"]) for r in tasks),
    }
    leakage["passed"] = all(v == 0 for v in leakage.values())
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "task_bank": str(TASK_OUT.relative_to(PROJECT)),
        "solution_bank": str(SOL_OUT.relative_to(PROJECT)),
        "tasks": len(tasks),
        "solutions": len(sols),
        "by_family": dict(sorted(Counter(r["family"] for r in tasks).items())),
        "solution_variants": dict(sorted(Counter(r["candidate_variant"] for r in sols).items())),
        "expected_phase_a_generations_core3_prompts3_k1": len(tasks) * 3 * 3,
        "expected_error_finding_jobs_core3_prompts2": len(sols) * 3 * 2,
        "leakage_policy": leakage,
    }
    write_json(SUMMARY_OUT, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
