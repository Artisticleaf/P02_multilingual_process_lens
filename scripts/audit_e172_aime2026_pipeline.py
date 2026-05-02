#!/usr/bin/env python3
"""Static audit for the E172 AIME2026 hidden-gate pipeline."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
TASK_BANK = PROJECT / "data/processed/e172_aime2026_matharena_task_bank_20260502.jsonl"
OUT_JSON = PROJECT / "reports/E172_AIME2026_PIPELINE_AUDIT_20260502.json"
OUT_MD = PROJECT / "reports/E172_AIME2026_PIPELINE_AUDIT_20260502.md"

REQUIRED_SCRIPTS = [
    "scripts/build_e172_aime2026_task_bank.py",
    "scripts/smoke_e172_aime2026_prompt.py",
    "scripts/audit_e172_aime2026_pipeline.py",
    "scripts/run_e172_aime2026_nonthinking_baseline.py",
    "scripts/run_e172_aime2026_hidden_gate_realtime.py",
    "scripts/summarize_e172_aime2026_hidden_gate.py",
    "scripts/launch_e172_aime2026_hidden_gate_queue_20260502.sh",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    rows = load_jsonl(TASK_BANK) if TASK_BANK.exists() else []
    errors: list[str] = []
    warnings: list[str] = []
    if not rows:
        errors.append("task_bank_empty_or_missing")
    for rel in REQUIRED_SCRIPTS:
        if not (PROJECT / rel).exists():
            errors.append(f"missing_script:{rel}")
    ids = [r.get("task_id") for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_task_id")
    if len(rows) != 30:
        warnings.append(f"expected_30_aime_rows_got_{len(rows)}")
    for row in rows:
        for key in ["task_id", "problem_idx", "problem", "gold_answer", "dataset_repo", "dataset_sha"]:
            if row.get(key) in (None, ""):
                errors.append(f"missing_{key}:{row.get('task_id')}")
        if row.get("dataset_repo") != "MathArena/aime_2026":
            warnings.append(f"unexpected_dataset_repo:{row.get('task_id')}:{row.get('dataset_repo')}")
        if row.get("gold_answer_in_prompt_by_design"):
            errors.append(f"gold_answer_in_prompt_by_design:{row.get('task_id')}")
        if row.get("manual_label_in_prompt_by_design"):
            errors.append(f"manual_label_in_prompt_by_design:{row.get('task_id')}")

    result = {
        "experiment": "E172_aime2026_hidden_gate_pipeline_audit",
        "task_bank": str(TASK_BANK.relative_to(PROJECT)),
        "tasks": len(rows),
        "required_scripts": REQUIRED_SCRIPTS,
        "errors": errors,
        "warnings": warnings,
        "passed": not errors,
        "definitions": {
            "baseline_nonthinking": "Chat template is requested with enable_thinking=False when supported; prompt contains only the problem.",
            "hidden_gate": "A teacher-forced component monitor scores the current generated prefix; crossing the calibrated E166 threshold triggers a non-thinking controlled-check branch.",
            "controlled_thinking": "The second branch is still rendered with enable_thinking=False; the control is a short visible check instruction derived from hidden risk, not long-CoT thinking mode.",
        },
        "guards": [
            "AIME 2026 answers are offline scoring metadata only.",
            "Hidden observations are made on causal prefixes of the model's own generation.",
            "The hidden gate records every observation with risk score, threshold, token count, and visible span.",
            "The gate can trigger only from hidden/component risk, never from comparing to the gold answer.",
            "Baseline, observed-prefix, and gated branch rows keep mode and prompt fields explicit for audit.",
        ],
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# E172 AIME2026 Pipeline Audit / E172 AIME2026 pipeline 审计",
        "",
        f"- Passed / 通过：`{result['passed']}`",
        f"- Tasks / 题目数：{len(rows)}",
        f"- Errors / 错误：`{errors}`",
        f"- Warnings / 警告：`{warnings}`",
        "",
        "## Definitions / 定义",
        "",
    ]
    lines.extend(f"- `{k}`: {v}" for k, v in result["definitions"].items())
    lines.extend(["", "## Guards / 防错点", ""])
    lines.extend(f"- {item}" for item in result["guards"])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
