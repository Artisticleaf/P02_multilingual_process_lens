#!/usr/bin/env python3
"""No-GPU smoke for E153-E158 scaffold."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import run_e153_nonthinking_difficult_scenario_generation as gen  # noqa: E402
import run_e153_nonthinking_error_finding as ef  # noqa: E402

TASK_BANK = PROJECT / "data/processed/e153_difficult_scenario_tasks_20260501.jsonl"
SOL_BANK = PROJECT / "data/processed/e153_candidate_solution_bank_20260501.jsonl"
OUT = PROJECT / "results/E153_E158_scaffold_smoke/e153_e158_scaffold_smoke.json"


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    tasks = load_jsonl(TASK_BANK)
    sols = load_jsonl(SOL_BANK)
    failures: list[str] = []
    by_family = Counter(t["family"] for t in tasks)
    if len(tasks) != 32:
        failures.append(f"expected 32 tasks, got {len(tasks)}")
    for family, count in by_family.items():
        if count != 2:
            failures.append(f"family {family} expected 2 tasks, got {count}")
    if len(sols) != 64:
        failures.append(f"expected 64 candidate solutions, got {len(sols)}")
    if set(gen.PROMPT_VARIANTS) != {"solve_neutral", "solve_terse", "solve_self_check"}:
        failures.append(f"generation prompt variants mismatch: {sorted(gen.PROMPT_VARIANTS)}")
    if set(ef.PROMPT_VARIANTS) != {"find_problem_global", "find_problem_localize_only"}:
        failures.append(f"error-finding prompt variants mismatch: {sorted(ef.PROMPT_VARIANTS)}")
    first_task = tasks[0]
    first_prompt = gen.PROMPT_VARIANTS["solve_neutral"].format(problem=first_task["problem"])
    first_solution = sols[0]
    first_error_prompt = ef.PROMPT_VARIANTS["find_problem_global"].format(problem=first_solution["problem"], solution=first_solution["candidate_solution"])
    banned = ["manual_acpi", "manual_process", "error_span", "trap_note", "risk_pattern"]
    for text_name, text in [("first_generation_prompt", first_prompt), ("first_error_prompt", first_error_prompt)]:
        for word in banned:
            if word in text:
                failures.append(f"{word} leaked in {text_name}")
    summary = {
        "passed": not failures,
        "failures": failures,
        "task_bank": str(TASK_BANK.relative_to(PROJECT)),
        "solution_bank": str(SOL_BANK.relative_to(PROJECT)),
        "tasks": len(tasks),
        "solutions": len(sols),
        "by_family": dict(sorted(by_family.items())),
        "generation_prompt_variants": sorted(gen.PROMPT_VARIANTS),
        "error_finding_prompt_variants": sorted(ef.PROMPT_VARIANTS),
        "first_task": {k: first_task[k] for k in ["task_id", "family", "problem", "gold_answer"]},
        "first_generation_prompt": first_prompt,
        "first_solution": {k: first_solution[k] for k in ["solution_id", "candidate_variant", "manual_process_valid_strict", "manual_error_span"]},
        "first_error_prompt": first_error_prompt,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

