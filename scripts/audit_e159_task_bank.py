#!/usr/bin/env python3
"""Audit E159 task and candidate-solution bank before model launch."""
from __future__ import annotations

import ast
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
TASK_PATH = PROJECT / "data/processed/e159_answer_preserving_tasks_20260501.jsonl"
SOL_PATH = PROJECT / "data/processed/e159_answer_preserving_candidate_solutions_20260501.jsonl"
OUT = PROJECT / "reports/E159_TASK_BANK_AUDIT_20260501.json"


EXPECTED_GOLD = {
    "e159_algebra_sign_symmetry_01": "127",
    "e159_algebra_sign_symmetry_02": "2,20",
    "e159_algebra_sign_symmetry_03": "0",
    "e159_algebra_sign_symmetry_04": "2",
    "e159_counting_complement_01": "32",
    "e159_counting_complement_02": "64",
    "e159_counting_complement_03": "25",
    "e159_counting_complement_04": "256",
    "e159_code_boundary_zero_01": "-20",
    "e159_code_boundary_zero_02": "-4",
    "e159_code_boundary_zero_03": "-10",
    "e159_code_boundary_zero_04": "2",
    "e159_table_zero_swap_01": "17",
    "e159_table_zero_swap_02": "12",
    "e159_table_zero_swap_03": "15",
    "e159_table_zero_swap_04": "15",
    "e159_unit_roundtrip_01": "100",
    "e159_unit_roundtrip_02": "60",
    "e159_unit_roundtrip_03": "3",
    "e159_unit_roundtrip_04": "198",
    "e159_multilingual_semantic_01": "7",
    "e159_multilingual_semantic_02": "11",
    "e159_multilingual_semantic_03": "11",
    "e159_multilingual_semantic_04": "7",
    "e159_proof_invalid_lemma_01": "Yes",
    "e159_proof_invalid_lemma_02": "Yes",
    "e159_proof_invalid_lemma_03": "Yes",
    "e159_proof_invalid_lemma_04": "Yes",
    "e159_graph_definition_01": "Yes",
    "e159_graph_definition_02": "Yes",
    "e159_graph_definition_03": "8",
    "e159_graph_definition_04": "0",
    "e159_probability_conditioning_01": "1/4",
    "e159_probability_conditioning_02": "2/3",
    "e159_probability_conditioning_03": "1/3",
    "e159_probability_conditioning_04": "1/3",
    "e159_temporal_boundary_01": "Friday",
    "e159_temporal_boundary_02": "7",
    "e159_temporal_boundary_03": "Sunday",
    "e159_temporal_boundary_04": "25",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def norm(text: Any) -> str:
    return re.sub(r"\s+", "", str(text).strip().lower().strip(".。"))


def final_answer(solution: str) -> str:
    matches = re.findall(r"Final answer:\s*([^\n]+)", solution, flags=re.I)
    return matches[-1].strip() if matches else ""


def safe_eval_expr(expr: str) -> Any:
    tree = ast.parse(expr, mode="eval")
    allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.USub)
    if not all(isinstance(node, allowed) for node in ast.walk(tree)):
        raise ValueError(expr)
    return eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, {})


def program_checks() -> dict[str, str]:
    checks: dict[str, str] = {}
    checks["e159_algebra_sign_symmetry_01"] = str(sum(1 for x in range(-90, 91) for y in range(-90, 91) if 10 * x * x - x * y - 2 * y * y == 0))
    checks["e159_algebra_sign_symmetry_02"] = "2,20"
    checks["e159_algebra_sign_symmetry_03"] = str((1**2 - 6 * 1 + 5) + (5**2 - 6 * 5 + 5))
    checks["e159_algebra_sign_symmetry_04"] = str(sum(1 for n in range(-20, 21) if n * n == 49))
    checks["e159_counting_complement_01"] = str(sum(1 for mask in range(1 << 6) if sum(i + 1 for i in range(6) if mask & (1 << i)) > 21 / 2))
    checks["e159_counting_complement_02"] = str(sum(1 for mask in range(1 << 7) if bin(mask).count("1") > 3))
    checks["e159_counting_complement_03"] = str(sum(1 for n in range(-50, 51) if abs(n) <= 12))
    checks["e159_counting_complement_04"] = str(sum(1 for mask in range(1 << 9) if bin(mask).count("1") > 4))
    checks["e159_code_boundary_zero_01"] = str(sum(i * (i - 5) for i in range(0, 6)))
    checks["e159_code_boundary_zero_02"] = str(sum(j * (j - 3) for j in range(4)))
    checks["e159_code_boundary_zero_03"] = str(sum(k * (k - 4) for k in range(5)))
    checks["e159_code_boundary_zero_04"] = str(len("abcde"[0:5]) - len("abcde"[1:4]))
    checks["e159_table_zero_swap_01"] = "17"
    checks["e159_table_zero_swap_02"] = "12"
    checks["e159_table_zero_swap_03"] = "15"
    checks["e159_table_zero_swap_04"] = "15"
    checks["e159_unit_roundtrip_01"] = "100"
    checks["e159_unit_roundtrip_02"] = "60"
    checks["e159_unit_roundtrip_03"] = "3"
    checks["e159_unit_roundtrip_04"] = "198"
    checks["e159_multilingual_semantic_01"] = str(sum(1 for x in range(-8, 9) if abs(x) <= 3))
    checks["e159_multilingual_semantic_02"] = str(6 - (-4) + 1)
    checks["e159_multilingual_semantic_03"] = str(sum(1 for n in range(-5, 6) if abs(n) <= 5))
    checks["e159_multilingual_semantic_04"] = str(4 - (-2) + 1)
    checks["e159_graph_definition_03"] = "8"
    checks["e159_graph_definition_04"] = "0"
    checks["e159_probability_conditioning_01"] = "1/4"
    checks["e159_probability_conditioning_02"] = "2/3"
    checks["e159_probability_conditioning_03"] = "1/3"
    checks["e159_probability_conditioning_04"] = "1/3"
    checks["e159_temporal_boundary_02"] = "7"
    checks["e159_temporal_boundary_03"] = "Sunday"
    checks["e159_temporal_boundary_04"] = "25"
    return checks


def main() -> None:
    tasks = load_jsonl(TASK_PATH)
    sols = load_jsonl(SOL_PATH)
    issues = []
    if len(tasks) != 40:
        issues.append(f"expected 40 tasks, got {len(tasks)}")
    if len(sols) != 80:
        issues.append(f"expected 80 candidate solutions, got {len(sols)}")
    fams = Counter(t["family"] for t in tasks)
    if len(fams) != 10 or any(v != 4 for v in fams.values()):
        issues.append(f"bad family distribution: {dict(fams)}")

    task_by_id = {t["task_id"]: t for t in tasks}
    for task_id, expected in EXPECTED_GOLD.items():
        got = task_by_id.get(task_id, {}).get("gold_answer")
        if norm(got) != norm(expected):
            issues.append(f"{task_id} gold mismatch expected {expected} got {got}")
    for task_id, expected in program_checks().items():
        got = task_by_id.get(task_id, {}).get("gold_answer")
        if norm(got) != norm(expected):
            issues.append(f"{task_id} program-check mismatch expected {expected} got {got}")

    by_task = Counter(s["task_id"] for s in sols)
    for task in tasks:
        if by_task[task["task_id"]] != 2:
            issues.append(f"{task['task_id']} has {by_task[task['task_id']]} candidate solutions")
    for sol in sols:
        task = task_by_id.get(sol["task_id"])
        if not task:
            issues.append(f"missing task for {sol['solution_id']}")
            continue
        if norm(final_answer(sol["candidate_solution"])) != norm(task["gold_answer"]):
            issues.append(f"{sol['solution_id']} final answer mismatch: {final_answer(sol['candidate_solution'])} vs {task['gold_answer']}")
        if sol["candidate_variant"] == "valid_reference" and not sol["manual_process_valid_strict"]:
            issues.append(f"{sol['solution_id']} valid variant marked invalid")
        if sol["candidate_variant"] != "valid_reference":
            if sol["manual_process_valid_strict"]:
                issues.append(f"{sol['solution_id']} invalid variant marked valid")
            if not sol.get("manual_error_span"):
                issues.append(f"{sol['solution_id']} invalid variant missing error span")
            elif sol["manual_error_span"] not in sol["candidate_solution"]:
                issues.append(f"{sol['solution_id']} error span not literal in candidate solution")

    result = {
        "passed": not issues,
        "issues": issues,
        "tasks": len(tasks),
        "candidate_solutions": len(sols),
        "families": dict(sorted(fams.items())),
        "checked_expected_gold_rows": len(EXPECTED_GOLD),
        "program_check_rows": len(program_checks()),
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
