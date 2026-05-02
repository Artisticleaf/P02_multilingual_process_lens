#!/usr/bin/env python3
"""Summarize E136b suspicious-confidence adaptive checking results."""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
RESULT_DIR = PROJECT / "results/E136_suspicious_confidence_adaptive_check"
REPORT_MD = PROJECT / "reports/E136_SUSPICIOUS_CONFIDENCE_ADAPTIVE_CHECK_20260430.md"
REPORT_JSON = PROJECT / "reports/E136_SUSPICIOUS_CONFIDENCE_ADAPTIVE_CHECK_20260430.json"

POLICIES = [
    "plain_base_no_check",
    "plain_always_global_check",
    "plain_hidden_global_check",
    "plain_hidden_local_check",
    "strict_base_no_check",
    "strict_always_global_check",
    "strict_hidden_global_check",
    "strict_hidden_local_check",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT))
    except ValueError:
        return str(path)


def load_result(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    phat = k / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n) / denom
    return max(0.0, center - half), min(1.0, center + half)


def rate_ci(k: int, n: int) -> dict[str, Any]:
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": k / n if n else None, "wilson95": [lo, hi]}


def count_accept(rows: list[dict[str, Any]], policy: str) -> int:
    return sum(bool(r[f"{policy}_accept"]) for r in rows)


def slice_rows(rows: list[dict[str, Any]], key: str, value: str) -> list[dict[str, Any]]:
    return [r for r in rows if str(r.get(key)) == value]


def summarize_model(data: dict[str, Any]) -> dict[str, Any]:
    rows = list(data["rows"])
    valid = [r for r in rows if r["manual_process_valid_strict"]]
    invalid = [r for r in rows if not r["manual_process_valid_strict"]]
    out: dict[str, Any] = {
        "model_key": data["model_key"],
        "result_path": rel(RESULT_DIR / f"{data['model_key']}_e136_suspicious_confidence_adaptive_check_rowspervariant12.json"),
        "n_rows": len(rows),
        "n_valid": len(valid),
        "n_invalid": len(invalid),
        "leakage_audit": data["leakage_audit"],
        "policy_trigger": rate_ci(sum(bool(r["policy_trigger"]) for r in rows), len(rows)),
        "policy_trigger_valid": rate_ci(sum(bool(r["policy_trigger"]) for r in valid), len(valid)),
        "policy_trigger_invalid": rate_ci(sum(bool(r["policy_trigger"]) for r in invalid), len(invalid)),
        "completion_hidden_trigger": rate_ci(sum(bool(r["completion_hidden_trigger"]) for r in rows), len(rows)),
        "mean_completion_hidden_score_valid": mean(float(r["completion_hidden_score"]) for r in valid),
        "mean_completion_hidden_score_invalid": mean(float(r["completion_hidden_score"]) for r in invalid),
        "acceptance": {},
        "by_variant": {},
        "triggered_counts": dict(Counter(f"{r['validity_class']}::{r['variant']}" for r in rows if r["policy_trigger"])),
    }
    for policy in POLICIES:
        out["acceptance"][policy] = {
            "all": rate_ci(count_accept(rows, policy), len(rows)),
            "strict_valid": rate_ci(count_accept(valid, policy), len(valid)),
            "strict_invalid": rate_ci(count_accept(invalid, policy), len(invalid)),
        }
    for variant in sorted({str(r["variant"]) for r in rows}):
        vals = slice_rows(rows, "variant", variant)
        out["by_variant"][variant] = {
            "n": len(vals),
            "manual_strict_valid_rate": sum(bool(r["manual_process_valid_strict"]) for r in vals) / len(vals),
            "policy_trigger": rate_ci(sum(bool(r["policy_trigger"]) for r in vals), len(vals)),
            "plain_base_accept": rate_ci(count_accept(vals, "plain_base_no_check"), len(vals)),
            "plain_hidden_local_accept": rate_ci(count_accept(vals, "plain_hidden_local_check"), len(vals)),
            "strict_base_accept": rate_ci(count_accept(vals, "strict_base_no_check"), len(vals)),
            "strict_hidden_local_accept": rate_ci(count_accept(vals, "strict_hidden_local_check"), len(vals)),
        }
    invalid_rows = []
    for r in invalid:
        invalid_rows.append({
            "audit_idx": r["audit_idx"],
            "family": r["family"],
            "route_id": r["route_id"],
            "variant": r["variant"],
            "plain_base_accept": r["plain_base_no_check_accept"],
            "plain_hidden_local_accept": r["plain_hidden_local_check_accept"],
            "plain_always_global_accept": r["plain_always_global_check_accept"],
            "strict_base_accept": r["strict_base_no_check_accept"],
            "strict_hidden_local_accept": r["strict_hidden_local_check_accept"],
            "trigger_stage": (r.get("policy_trigger_meta") or {}).get("stage"),
            "trigger_detector": (r.get("policy_trigger_meta") or {}).get("detector"),
            "trigger_span_text": (r.get("policy_trigger_meta") or {}).get("span_text"),
            "completion_hidden_score": r["completion_hidden_score"],
        })
    out["invalid_rows"] = invalid_rows
    return out


def fmt_rate(stat: dict[str, Any]) -> str:
    rate = stat["rate"]
    if rate is None:
        return "NA"
    lo, hi = stat["wilson95"]
    return f"{stat['k']}/{stat['n']} = {rate:.3f} [{lo:.3f}, {hi:.3f}]"


def md_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    header = "| " + " | ".join(rows[0]) + " |"
    sep = "| " + " | ".join(["---"] * len(rows[0])) + " |"
    body = ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join([header, sep, *body])


def build_markdown(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# E136 Suspicious-Confidence Adaptive Check / 可疑-置信度自适应检查")
    lines.append("")
    lines.append(f"- Created / 生成时间：`{summary['created_at']}`")
    lines.append("- Scope / 范围：stage-1 post-hoc policy simulation on E132/E133 controlled rows, `thinking=false`, 60 rows per model. / 在 E132/E133 受控行上做第一阶段后验策略模拟，每模型 60 条。")
    lines.append("- Data / 数据：`data/processed/e132_suspicious_valid_controls_20260430.jsonl`; source scored rows in `results/E132_E133_suspicious_confidence_probe/`. / 人工标签、gold、error span 只作离线评估，不进入 prompt。")
    lines.append("- Policy / 策略：base means use the original pointwise Yes/No decision; always-global rechecks every trace; hidden-global/local rechecks only when a hidden process-risk prefix triggers. / base 是原始 Yes/No；always-global 每条都复查；hidden-global/local 只在 hidden 过程风险触发时复查。")
    lines.append("- Cost note / 成本说明：脚本为了公平比较预计算了 global check；真实策略成本看 `hidden_*_check_call_rate`，等于 policy-trigger rate。")
    lines.append("")
    lines.append("## Main Results / 主要结果")
    table = [[
        "Model / 模型",
        "Hidden trigger all / 总触发",
        "Hidden trigger valid / 正确触发",
        "Hidden trigger invalid / 错误触发",
        "Plain base invalid accept / 普通基线放过错误",
        "Plain hidden-local invalid accept / hidden-local 放过错误",
        "Valid accept after hidden-local / hidden-local 保留正确",
    ]]
    for model in summary["models"]:
        acc = model["acceptance"]
        table.append([
            model["model_key"],
            fmt_rate(model["policy_trigger"]),
            fmt_rate(model["policy_trigger_valid"]),
            fmt_rate(model["policy_trigger_invalid"]),
            fmt_rate(acc["plain_base_no_check"]["strict_invalid"]),
            fmt_rate(acc["plain_hidden_local_check"]["strict_invalid"]),
            fmt_rate(acc["plain_hidden_local_check"]["strict_valid"]),
        ])
    lines.append(md_table(table))
    lines.append("")
    lines.append("## Strict-Prompt Diagnostic / strict 口径诊断")
    table = [[
        "Model / 模型",
        "Strict base invalid accept / strict 基线放过错误",
        "Strict hidden-local invalid accept / strict hidden-local 放过错误",
        "Strict valid accept after hidden-local / strict hidden-local 保留正确",
    ]]
    for model in summary["models"]:
        acc = model["acceptance"]
        table.append([
            model["model_key"],
            fmt_rate(acc["strict_base_no_check"]["strict_invalid"]),
            fmt_rate(acc["strict_hidden_local_check"]["strict_invalid"]),
            fmt_rate(acc["strict_hidden_local_check"]["strict_valid"]),
        ])
    lines.append(md_table(table))
    lines.append("")
    lines.append("## Interpretation / 说人话解释")
    lines.append("")
    lines.append("- Qwen3.5-27B: hidden trigger caught all 12 repaired strict-invalid traces while only touching 2/48 valid traces. Plain absolute base accepted 4/12 invalid traces; hidden-local reduced that to 1/12 with 47/48 valid retained. / Qwen 的 hidden 触发很像低成本检查开关：大部分正确题不加检查，错误题被集中复查。")
    lines.append("- Gemma4-31B-it: the cleanest case. It triggered on 12/12 invalid and 0/48 valid. Hidden-local reduced plain invalid acceptance from 3/12 to 2/12 while preserving 48/48 valid. / Gemma31 的触发边界最干净。")
    lines.append("- Gemma4-26B-A4B-it: hidden trigger still catches all invalid traces, but also triggers 6/48 valid traces. Local check accepts 5/12 invalid under both plain and strict policy, worse than strict base. / Gemma26 说明 hidden signal 不能单独当 oracle；局部复查 prompt 会出现 repair-aware 或语义误读。")
    lines.append("- The useful scientific fact is not “adaptive checking solved the task.” It is narrower: hidden process-risk can select most risky rows at low call rate, but whether the second pass uses that evidence depends on the check objective and model family. / 这不是说自适应检查已经解决问题，而是说 hidden 风险信号能低成本选中高风险行；二次检查是否有效仍受 objective 和模型族影响。")
    lines.append("")
    lines.append("## Boundary / 边界")
    lines.append("")
    lines.append("- E136 is a post-hoc filter/recheck simulation, not online generation-time intervention. / E136 是后验筛选模拟，不是在线生成时激活干预。")
    lines.append("- The invalid rows are controlled repaired strict-invalid traces, not natural unrepaired ACPI. / 这里的错误行是受控 repaired strict-invalid，不是自然未修复 ACPI。")
    lines.append("- Local excerpt selection is hidden-trigger based and visible-text only, but it still uses a second prompt. This supports adaptive checking, not direct proof that the base decoder would self-correct without a prompt. / 局部片段由 hidden 触发选择且只含可见文本，但仍是二次 prompt；它支持自适应检查，不等于证明原 decoder 会自动纠错。")
    lines.append("")
    lines.append("## Next / 下一步")
    lines.append("")
    lines.append("- E136-stage2: online semantic-boundary hidden monitoring during generation, then inject a short local-check instruction only at triggered boundaries. / 在线生成中监控语义边界 hidden 信号，只在触发时追加短检查。")
    lines.append("- E137: calibrate threshold per model, especially Gemma26, using suspicious-valid controls and confidence-matched rows. / 按模型校准阈值，特别是 Gemma26。")
    lines.append("- E138: test natural E119/E146 repaired/unrepaired ACPI with hidden-trigger checking, to see whether this transfers beyond controlled rows. / 把策略迁移到自然 E119/E146 repaired/unrepaired ACPI。")
    lines.append("- E139: compare local-check prompt variants: strict any-wrong-step, repair-aware final proof, and error-local-only. / 比较局部检查 prompt 的不同评价口径。")
    lines.append("")
    lines.append("## Artifacts / 文件")
    lines.append("")
    lines.append("- Runner / 运行脚本：`scripts/run_e136_suspicious_confidence_adaptive_check.py`")
    lines.append("- Queue / 队列：`scripts/launch_e136_suspicious_confidence_adaptive_check_queue_20260430.sh`")
    lines.append("- Status / 状态：`logs/e136_suspicious_confidence_adaptive_check_status_20260430.jsonl`")
    lines.append("- Results / 结果：`results/E136_suspicious_confidence_adaptive_check/`")
    lines.append("- JSON summary / 机器可读汇总：`reports/E136_SUSPICIOUS_CONFIDENCE_ADAPTIVE_CHECK_20260430.json`")
    return "\n".join(lines) + "\n"


def main() -> None:
    paths = sorted(RESULT_DIR.glob("*_e136_suspicious_confidence_adaptive_check_rowspervariant12.json"))
    if not paths:
        raise FileNotFoundError(f"No E136b result JSONs found in {RESULT_DIR}")
    models = [summarize_model(load_result(path)) for path in paths]
    summary = {
        "experiment": "E136_suspicious_confidence_adaptive_check",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "result_dir": rel(RESULT_DIR),
        "models": models,
        "scope_note_zh": "第一阶段后验自适应检查：hidden process-risk 触发低成本二次检查；不是在线激活干预。",
        "leakage_all_passed": all(m["leakage_audit"].get("passed") for m in models),
    }
    REPORT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_MD.write_text(build_markdown(summary), encoding="utf-8")
    print(json.dumps({"md": rel(REPORT_MD), "json": rel(REPORT_JSON), "models": [m["model_key"] for m in models]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
