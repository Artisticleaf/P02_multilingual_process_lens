#!/usr/bin/env python3
"""Summarize E172 AIME2026 baseline, hidden-gate, and KG state.

This summary is intentionally conservative: complete result JSON files,
checkpoint JSONL rows, and smoke rows are reported separately so a partial
checkpoint cannot be mistaken for a completed 30-problem run.
"""
from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
TASK_BANK = PROJECT / "data/processed/e172_aime2026_matharena_task_bank_20260502.jsonl"
RESULT_DIR = PROJECT / "results/E172_aime2026_hidden_gate"
STATUS = PROJECT / "logs/e172_aime2026_hidden_gate_status_20260502.jsonl"
PARAM_AUDIT = PROJECT / "reports/E172_QWEN_PARAMETER_AND_GATE_EVAL_AUDIT_20260502.md"
OUT_JSON = PROJECT / "reports/E172_AIME2026_HIDDEN_GATE_STAGE_ANALYSIS_20260502.json"
OUT_MD = PROJECT / "reports/E172_AIME2026_HIDDEN_GATE_STAGE_ANALYSIS_20260502.md"
KG_JSON = PROJECT / "reports/E172_AIME2026_CLAIM_KG_20260502.json"
KG_SVG = PROJECT / "reports/E172_AIME2026_KG_20260502.svg"

MODELS = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def task_count() -> int:
    return len(read_jsonl(TASK_BANK))


def row_ok(row: dict[str, Any]) -> bool:
    return bool(row.get("manual_final_correct"))


def row_tokens(row: dict[str, Any]) -> int:
    return int(row.get("generated_tokens_total") or row.get("generated_tokens") or 0)


def row_summary(rows: list[dict[str, Any]], total_tasks: int) -> dict[str, Any]:
    tokens = [row_tokens(row) for row in rows]
    correct = sum(int(row_ok(row)) for row in rows)
    final_markers = sum(int(bool(row.get("final_marker_found"))) for row in rows)
    hit_max = sum(int(bool(row.get("hit_max_new_tokens"))) for row in rows)
    strict_complete = sum(int(bool(row.get("final_marker_found")) and not bool(row.get("hit_max_new_tokens"))) for row in rows)
    return {
        "n": len(rows),
        "expected_tasks": total_tasks,
        "coverage": len(rows) / total_tasks if total_tasks else None,
        "correct": correct,
        "accuracy_on_observed_rows": correct / len(rows) if rows else None,
        "completion_tokens": sum(tokens),
        "mean_tokens": mean(tokens) if tokens else None,
        "median_tokens": median(tokens) if tokens else None,
        "cost_per_correct": sum(tokens) / correct if correct else None,
        "final_marker_found": final_markers,
        "hit_max": hit_max,
        "strict_complete_rows": strict_complete,
        "problem_indices": [int(row["problem_idx"]) for row in sorted(rows, key=lambda r: int(r.get("problem_idx", 0))) if "problem_idx" in row],
    }


def load_result_run(model: str, kind: str, smoke: bool) -> dict[str, Any]:
    if kind == "baseline":
        if smoke:
            result_patterns = [f"{model}_e172_aime2026_baseline_smoke_20260502.json"]
            checkpoint = PROJECT / f"logs/e172_aime2026_baseline_{model}_smoke_checkpoint_20260502.jsonl"
        else:
            result_patterns = [f"{model}_e172_aime2026_baseline_max*_20260502.json"]
            checkpoint = PROJECT / f"logs/e172_aime2026_baseline_{model}_checkpoint_20260502.jsonl"
    else:
        if smoke:
            result_patterns = [f"{model}_e172_aime2026_hidden_gate_smoke_20260502.json"]
            checkpoint = PROJECT / f"logs/e172_aime2026_hidden_gate_{model}_smoke_checkpoint_20260502.jsonl"
        else:
            result_patterns = [f"{model}_e172_aime2026_hidden_gate_max*_20260502.json"]
            checkpoint = PROJECT / f"logs/e172_aime2026_hidden_gate_{model}_checkpoint_20260502.jsonl"

    matches: list[Path] = []
    for pattern in result_patterns:
        matches.extend(sorted(RESULT_DIR.glob(pattern)))
    if matches:
        path = matches[-1]
        data = read_json(path)
        rows = list(data.get("rows", []))
        source_type = "result_json_smoke" if smoke else "result_json"
        run_summary = data.get("summary", {})
    else:
        rows = read_jsonl(checkpoint)
        path = checkpoint
        source_type = "checkpoint_jsonl_smoke" if smoke else "checkpoint_jsonl"
        run_summary = {}
    dedup: dict[str, dict[str, Any]] = {}
    for row in rows:
        if "task_id" in row:
            dedup[row["task_id"]] = row
    rows = list(dedup.values())
    exists = path.exists()
    return {
        "source": str(path.relative_to(PROJECT)),
        "source_type": source_type if exists or rows else "missing",
        "exists": exists,
        "rows": rows,
        "run_summary": run_summary,
    }


def status_events() -> list[dict[str, Any]]:
    return read_jsonl(STATUS)


def step_state(events: list[dict[str, Any]], step: str) -> str:
    starts = sum(1 for event in events if event.get("step") == step and event.get("status") == "start")
    dones = sum(1 for event in events if event.get("step") == step and event.get("status") == "done")
    if dones:
        return "done"
    if starts:
        return "started_without_done"
    return "not_started"


def completion_state(rows: list[dict[str, Any]], expected_tasks: int, step: str, events: list[dict[str, Any]]) -> str:
    state = step_state(events, step)
    if len(rows) >= expected_tasks and expected_tasks > 0:
        return "complete_rows_present" if state != "done" else "complete_done"
    if rows:
        return "partial_checkpoint_without_done" if state == "started_without_done" else "partial_rows"
    return state


def observation_rows(model: str) -> dict[str, Any]:
    formal = PROJECT / f"logs/e172_aime2026_hidden_gate_{model}_observations_20260502.jsonl"
    smoke = PROJECT / f"logs/e172_aime2026_hidden_gate_{model}_observations_smoke_20260502.jsonl"
    path = formal if formal.exists() else smoke
    rows = read_jsonl(path)
    risks = [float(row.get("hidden_risk", 0.0)) for row in rows]
    crossed = [row for row in rows if row.get("hidden_threshold_crossed")]
    by_task: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_task[row.get("task_id", "")]["observations"] += 1
        by_task[row.get("task_id", "")]["triggered"] += int(bool(row.get("hidden_threshold_crossed")))
    return {
        "source": str(path.relative_to(PROJECT)),
        "source_type": "formal" if formal.exists() else "smoke" if smoke.exists() else "missing",
        "exists": path.exists(),
        "observations": len(rows),
        "trigger_observations": len(crossed),
        "mean_risk": mean(risks) if risks else None,
        "max_risk": max(risks) if risks else None,
        "by_task": {task: dict(counter) for task, counter in sorted(by_task.items()) if task},
        "rows": rows,
    }


def paired_compare(baseline: list[dict[str, Any]], gate: list[dict[str, Any]]) -> dict[str, Any]:
    b = {row["task_id"]: row for row in baseline if "task_id" in row}
    g = {row["task_id"]: row for row in gate if "task_id" in row}
    task_ids = sorted(set(b) & set(g))
    gate_wins = 0
    baseline_wins = 0
    both_correct = 0
    both_wrong = 0
    token_delta = []
    for task_id in task_ids:
        b_ok = row_ok(b[task_id])
        g_ok = row_ok(g[task_id])
        gate_wins += int(g_ok and not b_ok)
        baseline_wins += int(b_ok and not g_ok)
        both_correct += int(b_ok and g_ok)
        both_wrong += int((not b_ok) and (not g_ok))
        token_delta.append(row_tokens(g[task_id]) - row_tokens(b[task_id]))
    return {
        "pairs": len(task_ids),
        "gate_wins": gate_wins,
        "baseline_wins": baseline_wins,
        "both_correct": both_correct,
        "both_wrong": both_wrong,
        "accuracy_delta_gate_minus_baseline": (gate_wins - baseline_wins) / len(task_ids) if task_ids else None,
        "mean_token_delta_gate_minus_baseline": mean(token_delta) if token_delta else None,
        "median_token_delta_gate_minus_baseline": median(token_delta) if token_delta else None,
    }


def summarize_model(model: str, expected_tasks: int, events: list[dict[str, Any]]) -> dict[str, Any]:
    formal_baseline = load_result_run(model, "baseline", smoke=False)
    formal_gate = load_result_run(model, "hidden_gate", smoke=False)
    smoke_baseline = load_result_run(model, "baseline", smoke=True)
    smoke_gate = load_result_run(model, "hidden_gate", smoke=True)
    obs = observation_rows(model)
    formal_baseline_rows = formal_baseline["rows"]
    formal_gate_rows = formal_gate["rows"]
    smoke_baseline_rows = smoke_baseline["rows"]
    smoke_gate_rows = smoke_gate["rows"]
    return {
        "model_key": model,
        "planned_by_launcher": True,
        "participated": bool(formal_baseline_rows or formal_gate_rows or smoke_baseline_rows or smoke_gate_rows),
        "steps": {
            "baseline_smoke": step_state(events, f"e172_baseline_{model}_smoke"),
            "hidden_gate_smoke": step_state(events, f"e172_hidden_gate_{model}_smoke"),
            "baseline_formal": step_state(events, f"e172_baseline_{model}"),
            "hidden_gate_formal": step_state(events, f"e172_hidden_gate_{model}"),
        },
        "completion_state": {
            "baseline_formal": completion_state(formal_baseline_rows, expected_tasks, f"e172_baseline_{model}", events),
            "hidden_gate_formal": completion_state(formal_gate_rows, expected_tasks, f"e172_hidden_gate_{model}", events),
        },
        "baseline_formal": {k: v for k, v in formal_baseline.items() if k != "rows"} | {"summary": row_summary(formal_baseline_rows, expected_tasks)},
        "hidden_gate_formal": {k: v for k, v in formal_gate.items() if k != "rows"} | {"summary": row_summary(formal_gate_rows, expected_tasks)},
        "baseline_smoke": {k: v for k, v in smoke_baseline.items() if k != "rows"} | {"summary": row_summary(smoke_baseline_rows, 1)},
        "hidden_gate_smoke": {k: v for k, v in smoke_gate.items() if k != "rows"} | {"summary": row_summary(smoke_gate_rows, 1)},
        "paired_formal_gate_vs_baseline": paired_compare(formal_baseline_rows, formal_gate_rows),
        "paired_smoke_gate_vs_baseline": paired_compare(smoke_baseline_rows, smoke_gate_rows),
        "observation_file": {k: v for k, v in obs.items() if k != "rows"},
        "task_rows": {
            "baseline_formal": compact_task_rows(formal_baseline_rows),
            "hidden_gate_formal": compact_task_rows(formal_gate_rows),
            "baseline_smoke": compact_task_rows(smoke_baseline_rows),
            "hidden_gate_smoke": compact_task_rows(smoke_gate_rows),
        },
        "hidden_observations": compact_observations(obs["rows"]),
    }


def compact_task_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in sorted(rows, key=lambda r: int(r.get("problem_idx", 0))):
        out.append(
            {
                "problem_idx": int(row.get("problem_idx", 0)),
                "task_id": row.get("task_id", ""),
                "gold_answer": str(row.get("gold_answer", "")),
                "extracted_final": str(row.get("extracted_final", "")),
                "manual_final_correct": bool(row.get("manual_final_correct")),
                "final_marker_found": bool(row.get("final_marker_found")),
                "hit_max_new_tokens": bool(row.get("hit_max_new_tokens")),
                "tokens": row_tokens(row),
            }
        )
    return out


def compact_observations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        out.append(
            {
                "task_id": row.get("task_id", ""),
                "problem_idx": int(row.get("problem_idx", 0)),
                "observation_index": int(row.get("observation_index", 0)),
                "visible_span": row.get("visible_span", ""),
                "hidden_component_key": row.get("hidden_component_key", ""),
                "hidden_validity_score": row.get("hidden_validity_score"),
                "hidden_risk": row.get("hidden_risk"),
                "hidden_threshold": row.get("hidden_threshold"),
                "hidden_threshold_crossed": bool(row.get("hidden_threshold_crossed")),
                "pred_process_valid": row.get("pred_process_valid"),
                "yes_minus_no": row.get("yes_minus_no"),
                "next_token_entropy": row.get("next_token_entropy"),
            }
        )
    return out


def fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def write_md(result: dict[str, Any]) -> None:
    lines = [
        "# E172 AIME2026 Hidden-Gate Stage Analysis / E172 AIME2026 hidden-gate 阶段分析",
        "",
        f"Created / 创建时间：`{result['created_at']}`.",
        "",
        "Scope / 范围：MathArena `aime_2026` 30题；baseline 为 non-thinking 原题解答，hidden-gate 为分块生成时读取隐藏层风险，触发后进入 non-thinking controlled-check 分支。",
        "",
        "Status boundary / 状态边界：截至本次汇总，正式全量没有完成；只有 `qwen35_27b` 有正式 baseline 部分 checkpoint，hidden-gate 只有 `qwen35_27b` smoke。",
        "",
        "Claim boundary / claim 边界：hidden-gate 是受控思考触发机制，不是答案 oracle；答案只用于离线评分。partial checkpoint 不能外推为 30 题成绩。",
        "",
        f"Parameter/gate audit / 参数与 gate 审计：`{PARAM_AUDIT.relative_to(PROJECT)}` confirms E172 requested `enable_thinking=False`, but uses deterministic project-evaluation decoding (`do_sample=False`, `temperature=0`) rather than Qwen model-card sampling for benchmark-performance reporting. It also records that hidden-gate is a generation-time intervention, not a passive evaluator-side monitor.",
        "",
        "## Landing Summary / 落盘总览",
        "",
        "| model | participated | formal baseline state | formal baseline n/correct/acc | formal gate state | smoke gate n/correct/trigger | hidden obs |",
        "|---|---:|---|---:|---|---:|---:|",
    ]
    for model, info in result["by_model"].items():
        b = info["baseline_formal"]["summary"]
        g_smoke = info["hidden_gate_smoke"]["summary"]
        smoke_gate_rows = info["task_rows"]["hidden_gate_smoke"]
        smoke_trigger = sum(int(row.get("hidden_gate_triggered", False)) for row in [])  # kept for schema stability
        if smoke_gate_rows:
            raw_smoke_gate = load_result_run(model, "hidden_gate", smoke=True)["rows"]
            smoke_trigger = sum(int(bool(row.get("hidden_gate_triggered"))) for row in raw_smoke_gate)
        lines.append(
            f"| {model} | {info['participated']} | {info['completion_state']['baseline_formal']} | "
            f"{b['n']}/{b['correct']}/{fmt(b['accuracy_on_observed_rows'])} | "
            f"{info['completion_state']['hidden_gate_formal']} | {g_smoke['n']}/{g_smoke['correct']}/{smoke_trigger} | "
            f"{info['observation_file']['observations']} |"
        )
    lines.extend(
        [
            "",
            "## Formal Baseline Rows / 正式 baseline 已落盘题目",
            "",
            "Only `qwen35_27b` has formal checkpoint rows. / 只有 `qwen35_27b` 有正式 checkpoint 行。",
            "",
            "| idx | task | gold | extracted | correct | tokens | marker | hit max |",
            "|---:|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in result["by_model"]["qwen35_27b"]["task_rows"]["baseline_formal"]:
        lines.append(
            f"| {row['problem_idx']} | `{row['task_id']}` | {row['gold_answer']} | {row['extracted_final']} | "
            f"{row['manual_final_correct']} | {row['tokens']} | {row['final_marker_found']} | {row['hit_max_new_tokens']} |"
        )
    qwen = result["by_model"]["qwen35_27b"]
    lines.extend(
        [
            "",
            "## Hidden-Gate Smoke / hidden-gate smoke",
            "",
            "| idx | task | gold | extracted | correct | tokens | marker | hit max | trigger | top risk | threshold |",
            "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in qwen["task_rows"]["hidden_gate_smoke"]:
        obs = qwen["hidden_observations"][0] if qwen["hidden_observations"] else {}
        lines.append(
            f"| {row['problem_idx']} | `{row['task_id']}` | {row['gold_answer']} | {row['extracted_final']} | "
            f"{row['manual_final_correct']} | {row['tokens']} | {row['final_marker_found']} | {row['hit_max_new_tokens']} | "
            f"{bool(obs.get('hidden_threshold_crossed'))} | {fmt(obs.get('hidden_risk'))} | {fmt(obs.get('hidden_threshold'))} |"
        )
    lines.extend(
        [
            "",
            "## Hidden-State Observations / 隐藏层观测",
            "",
            "| model | source | component | visible span | validity score | risk | threshold | crossed | pred_process_valid | yes-minus-no | entropy |",
            "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for model, info in result["by_model"].items():
        for obs in info["hidden_observations"]:
            span = str(obs["visible_span"]).replace("|", "\\|")
            lines.append(
                f"| {model} | `{info['observation_file']['source']}` | `{obs['hidden_component_key']}` | {span} | "
                f"{fmt(obs['hidden_validity_score'])} | {fmt(obs['hidden_risk'])} | {fmt(obs['hidden_threshold'])} | "
                f"{obs['hidden_threshold_crossed']} | {obs['pred_process_valid']} | {fmt(obs['yes_minus_no'])} | {fmt(obs['next_token_entropy'])} |"
            )
    if not any(info["hidden_observations"] for info in result["by_model"].values()):
        lines.append("| NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |")
    lines.extend(
        [
            "",
            "## Interpretation / 综合解释",
            "",
            "- Formal AIME2026 completion / 正式题目完成：`qwen35_27b` completed only problems 1-10 in the formal baseline checkpoint, all 10 correct with final markers and no hit-max rows. This is `10/30` coverage, not a complete 30-question score.",
            "- Model coverage / 模型覆盖：`gemma4_31b_it` and `gemma4_26b_a4b_it` were planned in the launcher but have no E172 generated rows or status start events.",
            "- Hidden-gate evidence / hidden-gate 证据：the only hidden observation is the Qwen smoke row. The E166-calibrated `35:residual_hidden_state` risk crossed threshold (`1.810 >= 1.412`) on the valid-looking span `Let $t_P$ be`, which triggered the controlled branch.",
            "- Gate threshold boundary / gate 阈值边界：the imported E166 `high_precision` threshold is sensitive on this E172 smoke case; the later parameter/gate audit notes that the `budgeted` threshold would not have triggered this early span.",
            "- Controlled branch outcome / controlled 分支结果：the smoke controlled branch hit its 512-token cap, produced no final marker, and the fallback extraction was wrong (`5` vs gold `277`). This is a false-positive or over-early-trigger warning for the current E172 gate settings, not a repair success.",
            "- Runtime parameter boundary / 运行参数边界：current Qwen rows should be described as deterministic non-thinking project evaluation, not as official Qwen benchmark-performance evaluation or model-card sampling performance.",
            "- Claim status / 主张状态：E172 currently supports pipeline/task-bank readiness and partial Qwen baseline competence on the first 10 AIME2026 rows. It does not yet support any full-model comparison, AIME2026 30题 accuracy claim, or hidden-gate improvement claim.",
            "",
            f"Machine-readable KG / 机器可读 KG：`{KG_JSON.relative_to(PROJECT)}`. KG image / KG 图片：`{KG_SVG.relative_to(PROJECT)}`.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_kg(result: dict[str, Any]) -> None:
    qwen = result["by_model"]["qwen35_27b"]
    kg = {
        "created_at": result["created_at"],
        "scope": "E172 AIME2026 hidden-gate landing and claim-boundary KG",
        "stage_analysis_path": str(OUT_JSON.relative_to(PROJECT)),
        "kg_image_path": str(KG_SVG.relative_to(PROJECT)),
        "nodes": [
            {
                "id": "experiment.E172_task_bank",
                "type": "artifact",
                "status": "done",
                "zh": "MathArena AIME2026 30题题库已构造；运行时 prompt 只含原题。",
                "path": "data/processed/e172_aime2026_matharena_task_bank_20260502.jsonl",
            },
            {
                "id": "experiment.E172_pipeline_audit",
                "type": "audit",
                "status": "passed",
                "zh": "pipeline/prompt smoke 通过，无 gold answer 或 source metadata 进入 runtime prompt。",
                "path": "reports/E172_AIME2026_PIPELINE_AUDIT_20260502.json",
            },
            {
                "id": "audit.E172_qwen_parameter_gate",
                "type": "audit",
                "status": "done",
                "zh": "确认 Qwen E172 使用 enable_thinking=False，但采用 deterministic 项目评测解码；hidden-gate 是生成时 intervention，不是被动 evaluator。",
                "path": str(PARAM_AUDIT.relative_to(PROJECT)),
            },
            {
                "id": "run.qwen35_27b.baseline_formal",
                "type": "run",
                "status": qwen["completion_state"]["baseline_formal"],
                "zh": "Qwen35-27B 正式 baseline checkpoint 已落盘前 10/30 题，10/10 正确；无 final JSON 和 done 状态。",
                "summary": qwen["baseline_formal"]["summary"],
                "path": qwen["baseline_formal"]["source"],
            },
            {
                "id": "run.qwen35_27b.hidden_gate_smoke",
                "type": "run",
                "status": "smoke_done_failed_to_repair",
                "zh": "Qwen35-27B hidden-gate smoke 触发风险门，但 controlled branch hit max 且答案错误。",
                "summary": qwen["hidden_gate_smoke"]["summary"],
                "path": qwen["hidden_gate_smoke"]["source"],
            },
            {
                "id": "claim.E172_no_full_aime2026_score_yet",
                "type": "claim_boundary",
                "status": "active",
                "zh": "当前不能报告 30题 AIME2026 完整分数；只能报告 Qwen 前 10 题 partial checkpoint。",
            },
            {
                "id": "claim.E172_hidden_gate_not_supported_yet",
                "type": "claim_boundary",
                "status": "active",
                "zh": "当前 hidden-gate 只有 smoke，且该 smoke 过早触发并失败；不能声称 hidden-gate 提升。",
            },
            {
                "id": "claim.E172_not_official_qwen_benchmark_setting",
                "type": "claim_boundary",
                "status": "active",
                "zh": "当前 Qwen 结果是 deterministic non-thinking 项目评测，不应报告为 Qwen 官方推荐采样或官方 benchmark 性能。",
            },
            {
                "id": "planned.gemma4_31b_it",
                "type": "planned_run",
                "status": result["by_model"]["gemma4_31b_it"]["completion_state"]["baseline_formal"],
                "zh": "Gemma4-31B-it 在 launcher 中排队，但没有 E172 生成落盘。",
            },
            {
                "id": "planned.gemma4_26b_a4b_it",
                "type": "planned_run",
                "status": result["by_model"]["gemma4_26b_a4b_it"]["completion_state"]["baseline_formal"],
                "zh": "Gemma4-26B-A4B-it 在 launcher 中排队，但没有 E172 生成落盘。",
            },
        ],
        "edges": [
            {"source": "experiment.E172_task_bank", "relation": "feeds", "target": "run.qwen35_27b.baseline_formal"},
            {"source": "experiment.E172_pipeline_audit", "relation": "guards", "target": "run.qwen35_27b.hidden_gate_smoke"},
            {"source": "audit.E172_qwen_parameter_gate", "relation": "constrains", "target": "claim.E172_not_official_qwen_benchmark_setting"},
            {"source": "audit.E172_qwen_parameter_gate", "relation": "classifies", "target": "run.qwen35_27b.hidden_gate_smoke"},
            {"source": "run.qwen35_27b.baseline_formal", "relation": "constrains", "target": "claim.E172_no_full_aime2026_score_yet"},
            {"source": "run.qwen35_27b.hidden_gate_smoke", "relation": "constrains", "target": "claim.E172_hidden_gate_not_supported_yet"},
            {"source": "planned.gemma4_31b_it", "relation": "pending_for", "target": "claim.E172_no_full_aime2026_score_yet"},
            {"source": "planned.gemma4_26b_a4b_it", "relation": "pending_for", "target": "claim.E172_no_full_aime2026_score_yet"},
        ],
    }
    KG_JSON.write_text(json.dumps(kg, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_kg_svg(result)


def svg_box(x: int, y: int, w: int, h: int, title: str, body: str, fill: str, stroke: str = "#273142") -> str:
    title = html.escape(title)
    body = html.escape(body)
    body_lines = body.split("\n")
    text = [f'<text x="{x + 14}" y="{y + 26}" font-size="15" font-weight="700" fill="#111827">{title}</text>']
    for i, line in enumerate(body_lines):
        text.append(f'<text x="{x + 14}" y="{y + 52 + i * 18}" font-size="12" fill="#374151">{line}</text>')
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>'
        + "".join(text)
    )


def svg_arrow(x1: int, y1: int, x2: int, y2: int, label: str = "") -> str:
    label_svg = ""
    if label:
        label_svg = f'<text x="{(x1 + x2) / 2 - 26}" y="{(y1 + y2) / 2 - 8}" font-size="11" fill="#4b5563">{html.escape(label)}</text>'
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#374151" stroke-width="1.3" marker-end="url(#arrow)"/>'
        + label_svg
    )


def write_kg_svg(result: dict[str, Any]) -> None:
    qwen = result["by_model"]["qwen35_27b"]
    b = qwen["baseline_formal"]["summary"]
    obs = qwen["hidden_observations"][0] if qwen["hidden_observations"] else {}
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="780" viewBox="0 0 1280 780">',
        "<defs>",
        '<marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">',
        '<path d="M0,0 L0,6 L9,3 z" fill="#374151"/>',
        "</marker>",
        "</defs>",
        '<rect width="1280" height="780" fill="#f8fafc"/>',
        '<text x="40" y="46" font-size="24" font-weight="800" fill="#111827">E172 AIME2026 Landing KG</text>',
        f'<text x="40" y="72" font-size="13" fill="#4b5563">created {html.escape(result["created_at"])} | formal full run not complete</text>',
        svg_box(40, 112, 250, 118, "Task Bank", "MathArena aime_2026\n30 problems\nprompt = original problem only", "#dbeafe"),
        svg_box(360, 112, 250, 118, "Pipeline Audit", "py_compile + prompt smoke\npassed\nno gold/source metadata prompt leak", "#dcfce7"),
        svg_box(
            700,
            104,
            270,
            138,
            "Qwen Formal Baseline",
            f"state: {qwen['completion_state']['baseline_formal']}\ncompleted: {b['n']}/30\ncorrect: {b['correct']}/{b['n']}\ntokens: {b['completion_tokens']}",
            "#fef3c7",
        ),
        svg_box(
            700,
            306,
            270,
            138,
            "Qwen Hidden-Gate Smoke",
            f"1 smoke row\nrisk {fmt(obs.get('hidden_risk'))} >= {fmt(obs.get('hidden_threshold'))}\ntriggered, hit max\nwrong fallback answer",
            "#fee2e2",
        ),
        svg_box(1030, 112, 210, 118, "Gemma Planned", "gemma4_31b_it\nnot started\nno rows landed", "#e5e7eb"),
        svg_box(1030, 306, 210, 118, "Gemma MoE Planned", "gemma4_26b_a4b_it\nnot started\nno rows landed", "#e5e7eb"),
        svg_box(360, 520, 260, 118, "Boundary", "Do not report 30-problem score\nDo not compare models yet\nDo not claim gate improvement", "#fce7f3"),
        svg_box(700, 520, 270, 118, "Hidden-State Read", "only smoke observation\n35:residual_hidden_state\nvalid-looking span triggered\ncalibration needs E172 full run", "#ede9fe"),
        svg_box(40, 650, 410, 92, "Parameter Boundary", "Qwen rows: deterministic non-thinking project eval\nnot official Qwen benchmark sampling\nhidden-gate = generation-time intervention", "#ecfeff"),
        svg_arrow(290, 171, 360, 171, "guards"),
        svg_arrow(610, 171, 700, 171, "feeds"),
        svg_arrow(835, 242, 835, 306, "smoke"),
        svg_arrow(835, 444, 835, 520, "constrains"),
        svg_arrow(700, 590, 620, 590, "bounds"),
        svg_arrow(250, 650, 430, 638, "constrains"),
        svg_arrow(970, 171, 1030, 171, "pending"),
        svg_arrow(970, 375, 1030, 375, "pending"),
        "</svg>",
    ]
    KG_SVG.write_text("\n".join(svg) + "\n", encoding="utf-8")


def build_result() -> dict[str, Any]:
    expected_tasks = task_count()
    events = status_events()
    return {
        "experiment": "E172_aime2026_hidden_gate_stage_analysis",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "task_bank": str(TASK_BANK.relative_to(PROJECT)),
        "expected_tasks": expected_tasks,
        "status_path": str(STATUS.relative_to(PROJECT)),
        "parameter_gate_audit": {
            "path": str(PARAM_AUDIT.relative_to(PROJECT)),
            "exists": PARAM_AUDIT.exists(),
            "boundary": "Qwen E172 is deterministic non-thinking project evaluation, not official Qwen model-card sampling or benchmark-performance reporting; hidden-gate is a generation-time intervention.",
        },
        "status_events": events,
        "models": MODELS,
        "by_model": {model: summarize_model(model, expected_tasks, events) for model in MODELS},
        "claim_boundary": [
            "Formal run is incomplete: no model has a completed 30-task E172 hidden-gate result.",
            "qwen35_27b has a partial formal baseline checkpoint covering problems 1-10 only.",
            "qwen35_27b hidden-gate evidence is smoke-only and failed to repair the first problem.",
            "qwen35_27b results are deterministic non-thinking project-evaluation rows, not official Qwen recommended-sampling benchmark rows.",
            "hidden-gate is an intervention/treatment condition, not a passive evaluator-only monitor.",
            "gemma4_31b_it and gemma4_26b_a4b_it have no generated E172 rows landed yet.",
        ],
    }


def main() -> None:
    result = build_result()
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_kg(result)
    write_md(result)
    print(
        json.dumps(
            {
                "wrote": [
                    str(OUT_JSON.relative_to(PROJECT)),
                    str(OUT_MD.relative_to(PROJECT)),
                    str(KG_JSON.relative_to(PROJECT)),
                    str(KG_SVG.relative_to(PROJECT)),
                ],
                "qwen_baseline_formal": result["by_model"]["qwen35_27b"]["baseline_formal"]["summary"],
                "qwen_hidden_gate_smoke": result["by_model"]["qwen35_27b"]["hidden_gate_smoke"]["summary"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
