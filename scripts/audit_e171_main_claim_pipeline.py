#!/usr/bin/env python3
"""Static audit for the E171 main-claim hidden-rescue pipeline."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
TASK_BANK = PROJECT / "data/processed/e171_main_claim_task_bank_20260502.jsonl"
OUT_JSON = PROJECT / "reports/E171_MAIN_CLAIM_PIPELINE_AUDIT_20260502.json"
OUT_MD = PROJECT / "reports/E171_MAIN_CLAIM_PIPELINE_AUDIT_20260502.md"

REQUIRED_SCRIPTS = [
    "scripts/build_e171_main_claim_task_bank.py",
    "scripts/smoke_e171_main_claim_prompt.py",
    "scripts/run_e171_baseline_nonthinking.py",
    "scripts/run_e171_hidden_rescue_from_baseline.py",
    "scripts/summarize_e171_main_claim_hidden_rescue.py",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    rows = load_jsonl(TASK_BANK)
    errors = []
    warnings = []
    if not rows:
        errors.append("task_bank_empty")
    for rel in REQUIRED_SCRIPTS:
        if not (PROJECT / rel).exists():
            errors.append(f"missing_script:{rel}")
    ids = [r.get("task_id") for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_task_id")
    problem_answer = [(r.get("problem"), str(r.get("gold_answer"))) for r in rows]
    if len(problem_answer) != len(set(problem_answer)):
        warnings.append("duplicate_problem_answer_rows_present")
    for row in rows:
        for key in ["task_id", "task_source", "family", "problem", "gold_answer"]:
            if not row.get(key):
                errors.append(f"missing_{key}:{row.get('task_id')}")
        if row.get("gold_answer_in_prompt_by_design"):
            errors.append(f"gold_answer_in_prompt_by_design:{row.get('task_id')}")
        if row.get("manual_label_in_prompt_by_design"):
            errors.append(f"manual_label_in_prompt_by_design:{row.get('task_id')}")
        if row.get("trap_note_in_prompt_by_design"):
            errors.append(f"trap_note_in_prompt_by_design:{row.get('task_id')}")

    result = {
        "experiment": "E171_main_claim_pipeline_audit",
        "task_bank": str(TASK_BANK.relative_to(PROJECT)),
        "tasks": len(rows),
        "errors": errors,
        "warnings": warnings,
        "passed": not errors,
        "required_scripts": REQUIRED_SCRIPTS,
        "definition_cleanup": {
            "hidden_signal_zh": "hidden signal 是 teacher-forced causal prefill 后读取的 residual/MLP/token-mixer(attention)/norm component 状态及其 E61 validity-direction 风险分数。",
            "hidden_signal_en": "A hidden signal is the component-state risk score read after teacher-forced causal prefill over residual, MLP, token-mixer/attention, and norm outputs.",
            "hidden_generic_warning_zh": "hidden_generic_warning 是由 hidden monitor 触发导出的文字条件，只说 prefix 某处有风险，不给位置。",
            "hidden_localized_warning_zh": "hidden_localized_warning 是由 hidden monitor 选出的自动边界可见 span，再把该 span 作为文字提醒给模型。",
            "not_proven_by_e167_zh": "E167 不能直接证明 hidden signal 能让模型做对原本不会做的题；E171 才以原题 baseline 错误为入口检验这个 claim。",
        },
        "pipeline_guards": [
            "Baseline prompts use only the original problem and a generic non-thinking solve template.",
            "Rescue cases are built only from same-model original-problem baseline failures.",
            "Hidden trigger selection uses the E166 calibrated component key and threshold on the model's own wrong trace.",
            "No oracle/manual span is included in E171 repair variants.",
            "The .pt cache stores component vectors, directions, centers, and prefix metadata for later residual/MLP/attention/norm analysis.",
        ],
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# E171 Main-Claim Pipeline Audit / E171 主 claim pipeline 审计",
        "",
        f"- Passed / 通过：`{result['passed']}`",
        f"- Tasks / 题目数：{result['tasks']}",
        f"- Errors / 错误：`{errors}`",
        f"- Warnings / 警告：`{warnings}`",
        "",
        "## Definitions / 定义",
        "",
        "- Hidden signal / 隐藏层信号：teacher-forced causal prefill 后读取的 residual、MLP、token-mixer/attention、norm component 状态，以及沿 E61 validity direction 计算出的风险分数。",
        "- `hidden_generic_warning` / hidden 泛泛提醒：hidden monitor 触发后转成文字，只告诉模型“prefix 某处风险高”，不告诉具体位置。",
        "- `hidden_localized_warning` / hidden 局部提醒：hidden monitor 在自动边界上选出一个可见 span，再把这个 span 作为文字提醒给模型。",
        "- E171 的主 claim 入口：只用模型原题 non-thinking 自己做错的题，检验 hidden-derived 提醒能否救回，并统计 completion-token cost per success。",
        "",
        "## Guards / 防错点",
        "",
    ]
    lines.extend(f"- {item}" for item in result["pipeline_guards"])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
