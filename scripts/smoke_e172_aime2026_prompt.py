#!/usr/bin/env python3
"""Render the first E172 AIME 2026 baseline and hidden-gate prompts."""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
TASK_BANK = PROJECT / "data/processed/e172_aime2026_matharena_task_bank_20260502.jsonl"
OUT = PROJECT / "reports/E172_AIME2026_PROMPT_SMOKE_20260502.md"

BASELINE_TEMPLATE = (
    "Solve the following AIME 2026 problem carefully in non-thinking mode. "
    "Show only the reasoning needed to justify the answer; do not give the final answer before the reasoning. "
    "End with exactly one line `Final answer: <integer>`.\n\n"
    "Problem: {problem}"
)

HIDDEN_GATE_TEMPLATE = (
    "A hidden monitor flagged this visible span as potentially abnormal: `{localized_span}`. "
    "The signal came from hidden/component state while running non-thinking generation, not from a gold answer. "
    "Stay in non-thinking mode, do a short controlled check of the flagged span against the problem, correct it if needed, and continue. "
    "End with exactly one line `Final answer: <integer>`.\n\n"
    "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
)


def main() -> None:
    rows = [json.loads(line) for line in TASK_BANK.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise RuntimeError("empty E172 task bank")
    first = rows[0]
    baseline = BASELINE_TEMPLATE.format(problem=first["problem"])
    prefix = "Let Patrick's walking speed be p miles per hour, so Tanya's speed is p+2."
    gate = HIDDEN_GATE_TEMPLATE.format(problem=first["problem"], prefix=prefix, localized_span="Tanya's speed is p+2")
    offline_fields = {
        "gold_answer": str(first.get("gold_answer", "")),
        "dataset_sha": str(first.get("dataset_sha", "")),
        "task_source": str(first.get("task_source", "")),
    }
    baseline_hits = {k: v for k, v in offline_fields.items() if v and v in baseline}
    gate_hits = {k: v for k, v in offline_fields.items() if v and v in gate}
    lines = [
        "# E172 AIME2026 Prompt Smoke / E172 AIME2026 prompt smoke",
        "",
        f"- task_id: `{first['task_id']}`",
        f"- problem_idx: `{first['problem_idx']}`",
        f"- dataset_repo: `{first['dataset_repo']}`",
        f"- baseline_offline_field_hits: `{baseline_hits}`",
        f"- gate_offline_field_hits: `{gate_hits}`",
        f"- gold_answer_string_occurs_in_problem_text: `{str(first['gold_answer']) in first['problem']}`",
        "",
        "## Baseline Prompt / baseline prompt",
        "",
        "```text",
        baseline,
        "```",
        "",
        "## Hidden-Gate Prompt Shape / hidden-gate prompt 形状",
        "",
        "```text",
        gate,
        "```",
        "",
        "## Boundary / 边界",
        "",
        "- Baseline prompt uses only the problem. / baseline prompt 只使用题干。",
        "- Hidden-gate prompt uses problem, model-generated prefix, and hidden-derived visible span. / hidden-gate prompt 使用题干、模型已生成 prefix、hidden 导出的可见 span。",
        "- The gold answer and dataset revision are never rendered into runtime prompts. / 答案和数据集版本不进入运行时 prompt。",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
