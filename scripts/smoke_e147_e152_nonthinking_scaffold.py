#!/usr/bin/env python3
"""No-GPU smoke for E147-E152 non-thinking unrepaired-ACPI scaffold."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import run_e147_unrepaired_acpi_induction_generation as e147  # noqa: E402

TASK_BANK = PROJECT / "data/processed/e147_unrepaired_acpi_induction_tasks_20260430.jsonl"
OUT = PROJECT / "results/E147_E152_scaffold_smoke/e147_e152_scaffold_smoke.json"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    rows = load_jsonl(TASK_BANK)
    by_family = Counter(r["family"] for r in rows)
    by_route = Counter(r["route_id"] for r in rows)
    failures: list[str] = []
    if len(rows) != 32:
        failures.append(f"expected 32 tasks, got {len(rows)}")
    for family, count in sorted(by_family.items()):
        if count != 4:
            failures.append(f"family {family} expected 4 tasks, got {count}")
    for route, count in sorted(by_route.items()):
        if count != 8:
            failures.append(f"route {route} expected 8 tasks, got {count}")
    expected_variants = {"neutral", "answer_first_no_gold", "terse_solution", "self_check_short"}
    if set(e147.PROMPT_VARIANTS) != expected_variants:
        failures.append(f"prompt variants mismatch: {sorted(e147.PROMPT_VARIANTS)}")
    for task in rows:
        if task.get("gold_answer_in_prompt_by_design"):
            failures.append(f"gold answer marked in prompt: {task['task_id']}")
        if task.get("trap_note_in_prompt_by_design"):
            failures.append(f"trap note marked in prompt: {task['task_id']}")
        if task.get("manual_label_in_prompt_by_design"):
            failures.append(f"manual label marked in prompt: {task['task_id']}")
        if task.get("error_span_in_prompt_by_design"):
            failures.append(f"error span marked in prompt: {task['task_id']}")
        for variant, template in e147.PROMPT_VARIANTS.items():
            prompt = template.format(problem=task["problem"])
            if str(task.get("trap_note_not_in_prompt", "")) and str(task["trap_note_not_in_prompt"]) in prompt:
                failures.append(f"trap note text leaked in prompt: {task['task_id']}::{variant}")
            for banned in ["manual_acpi", "unrepaired", "risk_pattern", "trap_note"]:
                if banned in prompt:
                    failures.append(f"metadata keyword leaked in prompt: {task['task_id']}::{variant}::{banned}")
    summary = {
        "passed": not failures,
        "failures": failures,
        "task_bank": str(TASK_BANK.relative_to(PROJECT)),
        "rows": len(rows),
        "by_family": dict(sorted(by_family.items())),
        "by_route": dict(sorted(by_route.items())),
        "prompt_variants": sorted(e147.PROMPT_VARIANTS),
        "expected_phase_a_generations_k1_core3_prompts4": len(rows) * 3 * 4,
        "expected_phase_a_generations_k2_core3_prompts4": len(rows) * 3 * 4 * 2,
        "note_zh": "无 GPU smoke：检查任务数、家族/语言路径分布、prompt 元数据泄露设计。",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

