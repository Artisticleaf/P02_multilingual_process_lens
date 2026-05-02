#!/usr/bin/env python3
"""Summarize E132-E134 suspicious-valid / confidence-matched probe results."""
from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
RESULT_DIR = PROJECT / "results/E132_E133_suspicious_confidence_probe"
E134_SUMMARY = PROJECT / "results/E134_trigger_window_audit/e134_trigger_window_audit_summary.json"
REPORT_MD = PROJECT / "reports/E132_E134_SUSPICIOUS_CONFIDENCE_PROBE_20260430.md"
REPORT_JSON = PROJECT / "reports/E132_E134_SUSPICIOUS_CONFIDENCE_PROBE_20260430.json"

MODEL_LABELS = {
    "qwen35_27b": "Qwen3.5-27B",
    "gemma4_31b_it": "Gemma4-31B-it",
    "gemma4_26b_a4b_it": "Gemma4-26B-A4B-it",
}


def wilson(k: int, n: int, z: float = 1.96) -> list[float | None]:
    if n == 0:
        return [None, None]
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return [max(0.0, center - half), min(1.0, center + half)]


def fmt(x: Any, d: int = 3) -> str:
    if x is None:
        return "NA"
    if isinstance(x, float):
        return f"{x:.{d}f}"
    return str(x)


def trigger_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    k = sum(float(r["best_component_score"]) < 0 for r in rows)
    n = len(rows)
    return {
        "n": n,
        "triggered": k,
        "trigger_rate": k / n if n else None,
        "trigger_wilson95": wilson(k, n),
        "mean_best_component_score": sum(float(r["best_component_score"]) for r in rows) / n if n else None,
        "strict_accept_rate": sum(bool(r["strict_pred_process_valid"]) for r in rows) / n if n else None,
        "plain_accept_rate": sum(bool(r["plain_pred_process_valid"]) for r in rows) / n if n else None,
    }


def compact_line(label: str, stats: dict[str, Any]) -> str:
    lo, hi = stats["trigger_wilson95"]
    return (
        f"| {label} | {stats['triggered']}/{stats['n']} = {fmt(stats['trigger_rate'])} "
        f"[{fmt(lo)}, {fmt(hi)}] | {fmt(stats['mean_best_component_score'])} | "
        f"{fmt(stats['strict_accept_rate'])} | {fmt(stats['plain_accept_rate'])} |"
    )


def main() -> None:
    files = sorted(RESULT_DIR.glob("*_e132_e133_all_chat.json"))
    report: dict[str, Any] = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "E132_E134_suspicious_confidence_probe",
        "models": {},
        "e134_summary": json.loads(E134_SUMMARY.read_text(encoding="utf-8")) if E134_SUMMARY.exists() else None,
    }
    md = [
        "# E132-E134 Suspicious/Confidence Probe / 可疑但正确与置信度匹配探针",
        "",
        f"- Created / 生成时间：`{report['created_at']}`",
        "- Scope / 范围：Qwen3.5-27B、Gemma4-31B-it、Gemma4-26B-A4B-it；`thinking=false` direct verifier replay。",
        "- Dataset / 数据：E132 240-row controlled set; this first probe uses 60 rows per model, 12 per variant. / E132 共 240 条，本次小探针每模型 60 条，每变体 12 条。",
        "- Variants / 变体：`clean_valid`, `suspicious_valid_marker`, `suspicious_valid_alternative`, `low_conf_valid`, `repaired_strict_invalid`。",
        "- Leakage / 泄露：gold answer、manual label、manual error span 只作为离线元数据；verifier prompt 只含 problem 与 visible trace prefix。",
        "",
        "说人话：这个实验直接问 reviewer 会问的问题：hidden 的“错误/风险信号”是不是只是在看到 Wait、maybe、double-check 这些犹豫词时乱报警？当前小探针答案是：Qwen/Gemma31 基本不是；Gemma26 有更多误触发，必须如实写成阈值/模型边界。",
        "",
        "## Main Results / 主要结果",
    ]
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        model = data["model_key"]
        rows = [r for r in data["rows"] if r["stage"] == "completion_end"]
        valid = [r for r in rows if r["manual_process_valid_strict"]]
        suspicious = [r for r in valid if r["variant"] != "clean_valid"]
        invalid = [r for r in rows if not r["manual_process_valid_strict"]]
        by_variant = {variant: trigger_stats([r for r in rows if r["variant"] == variant]) for variant in sorted({r["variant"] for r in rows})}
        model_report = {
            "path": str(path),
            "source_rows": data["source_rows"],
            "prefix_rows": data["prefix_rows"],
            "best_component_key": data["best_component_key"],
            "hidden_auc_valid_vs_invalid_completion": data["analysis"]["hidden_auc_valid_vs_invalid_completion"],
            "strict_confidence_auc_valid_vs_invalid_completion": data["analysis"]["strict_confidence_auc_valid_vs_invalid_completion"],
            "plain_accept_auc_valid_vs_invalid_completion": data["analysis"]["plain_accept_auc_valid_vs_invalid_completion"],
            "matched_analysis_completion": {
                k: v for k, v in data["analysis"]["matched_analysis_completion"].items() if k != "pairs"
            },
            "completion_trigger_stats": {
                "valid_all": trigger_stats(valid),
                "suspicious_valid": trigger_stats(suspicious),
                "invalid": trigger_stats(invalid),
                "by_variant": by_variant,
            },
            "leakage_audit": data["leakage_audit"],
        }
        report["models"][model] = model_report

        md.append("")
        md.append(f"### {MODEL_LABELS.get(model, model)}")
        md.append("")
        md.append(f"- Result / 结果：`{path.relative_to(PROJECT)}`")
        md.append(f"- Best component / 最强组件：`{data['best_component_key']}`")
        md.append(
            f"- AUC / AUC：hidden={fmt(model_report['hidden_auc_valid_vs_invalid_completion'])}, "
            f"strict confidence={fmt(model_report['strict_confidence_auc_valid_vs_invalid_completion'])}, "
            f"plain Yes-No={fmt(model_report['plain_accept_auc_valid_vs_invalid_completion'])}."
        )
        ma = model_report["matched_analysis_completion"]
        md.append(
            f"- Matched pairs / 置信度匹配对：n={ma.get('n_pairs')}, "
            f"hidden valid>invalid accuracy={fmt(ma.get('hidden_pair_accuracy_valid_gt_invalid'))}, "
            f"mean distance={fmt(ma.get('mean_match_distance'))}."
        )
        md.append("")
        md.append("| Completion slice / completion 切片 | hidden trigger rate score<0, Wilson 95% CI | mean score | strict accept | plain accept |")
        md.append("|---|---:|---:|---:|---:|")
        md.append(compact_line("valid_all", model_report["completion_trigger_stats"]["valid_all"]))
        md.append(compact_line("suspicious_valid", model_report["completion_trigger_stats"]["suspicious_valid"]))
        md.append(compact_line("invalid", model_report["completion_trigger_stats"]["invalid"]))
        for variant in ["clean_valid", "suspicious_valid_marker", "suspicious_valid_alternative", "low_conf_valid", "repaired_strict_invalid"]:
            if variant in by_variant:
                md.append(compact_line(variant, by_variant[variant]))

    md.extend(
        [
            "",
            "## Interpretation / 解析",
            "",
            "- Qwen 与 Gemma31：hidden residual score 在 valid/suspicious-valid 和 repaired strict-invalid 之间分离很强；可疑但正确 completion 的误触发很低。说明信号不是简单看到 `Wait/check/maybe` 就报警。",
            "- Gemma26：invalid 仍 12/12 触发，但 valid false trigger 更高。这和 E78/E131 里 Gemma26 的 valid false rejection 一致，说明它的过程方向边界更脆，需要阈值校准和 suspicious-valid 控制组。",
            "- Confidence-matched pair 在三个模型上都是 12/12 hidden valid>invalid，但当前匹配距离还不够小，属于第一版探针证据。下一版要扩大样本并做更严格的 matching/regression。",
            "- Plain Yes/No 对 invalid 的接受仍存在，尤其 Gemma26 plain accept 6/12；hidden score 在这些 case 上给出更强拒绝信号，支持 adaptive checking trigger 的必要性。",
            "",
            "## E134 Window Audit / E134 窗口审计",
            "",
        ]
    )
    if report["e134_summary"]:
        s = report["e134_summary"]
        md.append(f"- Audit sheet / 审计表：`{s['out_jsonl']}`")
        md.append(f"- Rows / 行数：{s['rows']}；threshold={s['threshold']}；radius={s['radius']}.")
        md.append(f"- Preliminary labels / 初步标签：`{s['by_preliminary_label']}`")
        md.append("- Note / 注意：`suspicion_marker_end` 是 marker-only prefix control，不应作为部署策略误触发率；真正 policy trigger 应从 post_suspicion、error、final、completion 等有语义内容的边界算。")
    md.extend(
        [
            "",
            "## Boundary / 边界",
            "",
            "- This is a 60-row-per-model probe, not final prevalence. / 这是小探针，不是最终发生率估计。",
            "- E132 variants are controlled/synthetic; next expansion must add more task families and natural hard-task suspicious-valid rows. / E132 是受控构造，后续要扩到更多任务和自然样本。",
            "- Hidden score threshold 0 is inherited from E61 direction centering; it is not deployment-calibrated. / 0 阈值来自 E61 方向中心化，不是部署校准阈值。",
            "- Manual labels and spans were not used in prompts. / 人工标签和 span 没有进入 prompt。",
        ]
    )
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"markdown": str(REPORT_MD), "json": str(REPORT_JSON)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
