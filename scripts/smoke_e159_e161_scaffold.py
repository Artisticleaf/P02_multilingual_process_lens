#!/usr/bin/env python3
"""Static smoke for E159-E161 scaffold without loading models."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_e159_answer_preserving_task_bank as bank  # noqa: E402

OUT = PROJECT / "results/E159_E161_scaffold_smoke/e159_e161_scaffold_smoke.json"

GEN_SOLVE_NEUTRAL = (
    "Solve the following problem carefully. Show the reasoning needed to justify the result. "
    "Do not give the final answer before the reasoning. End with exactly one line `Final answer: <answer>`.\n\nProblem: {problem}"
)
REPAIR_BLIND_GLOBAL = (
    "You are checking a proposed solution. Do not solve from scratch unless needed. "
    "State whether the proposed solution contains any wrong reasoning step. "
    "Use this exact final block:\nERROR: Yes or No\nLOCATION: <short quote or NONE>\nREASON: <one sentence>\n\n"
    "Problem: {problem}\nProposed solution:\n{solution}"
)
REPAIR_ORACLE = (
    "A separate hidden monitor flagged this visible span as potentially abnormal: `{span}`. "
    "Check whether that span is actually a wrong reasoning step. If it is wrong, give a minimal corrected step, "
    "but do not solve the entire problem from scratch. Use this exact final block:\n"
    "ERROR: Yes or No\nLOCATION: <short quote or NONE>\nCORRECTION: <minimal correction or NONE>\n\n"
    "Problem: {problem}\nProposed solution:\n{solution}"
)


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def leakage_text(text: str, row: dict) -> list[str]:
    leaks = []
    for key in ["gold_answer", "answer_preserving_trap_type"]:
        value = str(row.get(key, "")).strip()
        if value and value in text:
            leaks.append(key)
    return leaks


def main() -> None:
    tasks, sols = bank.build()
    assert_true(len(tasks) == 40, f"expected 40 tasks, got {len(tasks)}")
    assert_true(len(sols) == 80, f"expected 80 candidate solutions, got {len(sols)}")
    fams = Counter(t["family"] for t in tasks)
    assert_true(len(fams) == 10, f"expected 10 families, got {len(fams)}")
    assert_true(all(v == 4 for v in fams.values()), f"expected 4 tasks/family, got {dict(fams)}")

    first_task = sorted(tasks, key=lambda t: (t["family"], t["family_local_id"]))[0]
    content = GEN_SOLVE_NEUTRAL.format(problem=first_task["problem"])
    leaks = leakage_text(content, first_task)
    assert_true(not leaks, f"generation prompt leaks metadata: {leaks}")
    assert_true(first_task["problem"] in content, "generation prompt missing problem")
    assert_true("Final answer" in content, "generation prompt missing final-answer contract")

    first_invalid = [s for s in sols if s["candidate_variant"] == "invalid_answer_preserving_reference"][0]
    blind = REPAIR_BLIND_GLOBAL.format(
        problem=first_invalid["problem"],
        solution=first_invalid["candidate_solution"],
    )
    oracle = REPAIR_ORACLE.format(
        problem=first_invalid["problem"],
        solution=first_invalid["candidate_solution"],
        span=first_invalid["manual_error_span"],
    )
    assert_true("flagged this visible span" not in blind and "potentially abnormal" not in blind, "blind prompt contains oracle-span language")
    assert_true(first_invalid["manual_error_span"] in oracle and "flagged this visible span" in oracle, "oracle prompt missing explicit span")
    assert_true("Gold answer" not in blind and "Correct answer" not in blind, "blind prompt exposes an explicit gold-answer field")

    expected = {
        "e159_generation_per_model": len(tasks) * 3,
        "e160_thinking_generation_per_model": len(tasks) * 3,
        "e161_error_repair_per_model": len(sols) * 3,
        "core_models": ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"],
    }
    result = {
        "passed": True,
        "tasks": len(tasks),
        "candidate_solutions": len(sols),
        "families": dict(sorted(fams.items())),
        "first_generation_task": {
            "task_id": first_task["task_id"],
            "family": first_task["family"],
            "problem": first_task["problem"],
            "prompt_excerpt": content[:500],
        },
        "first_e161_invalid_candidate": {
            "solution_id": first_invalid["solution_id"],
            "family": first_invalid["family"],
            "manual_error_span_offline": first_invalid["manual_error_span"],
            "blind_prompt_has_oracle_language": "flagged this visible span" in blind,
            "oracle_prompt_has_span": first_invalid["manual_error_span"] in oracle,
        },
        "expected_jobs": expected,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
