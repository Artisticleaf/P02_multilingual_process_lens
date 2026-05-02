#!/usr/bin/env python3
"""Summarize E131 E119/E146 hidden localization outputs."""
from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
RESULT_DIR = PROJECT / "results/E131_e119_e146_hidden_localization"
REPORT_MD = PROJECT / "reports/E131_E119_E146_HIDDEN_LOCALIZATION_20260430.md"
REPORT_JSON = PROJECT / "reports/E131_E119_E146_HIDDEN_LOCALIZATION_20260430.json"


MODEL_LABELS = {
    "qwen35_27b": "Qwen3.5-27B",
    "gemma4_31b_it": "Gemma4-31B-it",
    "gemma4_26b_a4b_it": "Gemma4-26B-A4B-it",
}


KEY_SLICES = {
    "trace_class": ["strict_valid", "repaired_acpi", "unrepaired_acpi"],
    "stage": [
        "first_final_answer_end",
        "detected_error_marker_end",
        "post_error_240chars",
        "repair_trigger_end",
        "post_repair_240chars",
        "completion_end",
    ],
}


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float | None, float | None]:
    if n <= 0:
        return None, None
    phat = k / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n) / denom
    return max(0.0, center - half), min(1.0, center + half)


def mean_ci(values: list[float]) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    mean = sum(values) / len(values)
    if len(values) == 1:
        return mean, mean
    sd = statistics.stdev(values)
    half = 1.96 * sd / math.sqrt(len(values))
    return mean - half, mean + half


def fmt(x: float | None, digits: int = 3) -> str:
    if x is None:
        return "NA"
    return f"{x:.{digits}f}"


def summarize_rows(rows: list[dict[str, Any]], best_key: str) -> dict[str, Any]:
    n = len(rows)
    accepted = sum(1 for r in rows if r.get("pred_process_valid"))
    acc_lo, acc_hi = wilson_ci(accepted, n)
    yes_values = [float(r["yes_minus_no"]) for r in rows if r.get("yes_minus_no") is not None]
    best_values = [
        float(r["component_validity_scores"][best_key])
        for r in rows
        if r.get("component_validity_scores") and best_key in r["component_validity_scores"]
    ]
    yes_lo, yes_hi = mean_ci(yes_values)
    best_lo, best_hi = mean_ci(best_values)
    return {
        "n": n,
        "accepted": accepted,
        "accept_rate": accepted / n if n else None,
        "accept_wilson_95": [acc_lo, acc_hi],
        "mean_yes_minus_no": sum(yes_values) / len(yes_values) if yes_values else None,
        "mean_yes_minus_no_ci95_normal": [yes_lo, yes_hi],
        "mean_best_component_score": sum(best_values) / len(best_values) if best_values else None,
        "mean_best_component_score_ci95_normal": [best_lo, best_hi],
    }


def component_means(rows: list[dict[str, Any]], component_keys: list[str]) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for key in component_keys:
        vals = [
            float(r["component_validity_scores"][key])
            for r in rows
            if r.get("component_validity_scores") and key in r["component_validity_scores"]
        ]
        out[key] = sum(vals) / len(vals) if vals else None
    return out


def display_component_name(component_key: str) -> str:
    return component_key.split(":", 1)[1].replace("_", " ")


def candidate_component_keys(data: dict[str, Any]) -> list[str]:
    best_layer = int(data["best_hidden_layer"])
    candidates = [
        f"{best_layer}:residual_hidden_state",
        f"{best_layer}:mlp_output",
        f"{best_layer}:token_mixer_output",
        f"{best_layer}:post_attention_norm_output",
        f"{best_layer}:post_feedforward_norm_output",
        f"{best_layer}:pre_mlp_norm_output",
    ]
    available = set(data.get("component_keys", []))
    return [key for key in candidates if key in available]


def group(rows: list[dict[str, Any]], key_fn) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = key_fn(row)
        if key:
            out[str(key)].append(row)
    return dict(out)


def compact_table_line(label: str, stats: dict[str, Any]) -> str:
    lo, hi = stats["accept_wilson_95"]
    return (
        f"| {label} | {stats['n']} | {stats['accepted']}/{stats['n']} "
        f"= {fmt(stats['accept_rate'])} [{fmt(lo)}, {fmt(hi)}] | "
        f"{fmt(stats['mean_yes_minus_no'])} | {fmt(stats['mean_best_component_score'])} |"
    )


def component_table_lines(
    grouped_rows: dict[str, list[dict[str, Any]]],
    row_keys: list[str],
    component_keys: list[str],
) -> list[str]:
    lines: list[str] = []
    if not component_keys:
        return lines
    header = "| Stage / 阶段 | n | " + " | ".join(display_component_name(k) for k in component_keys) + " |"
    sep = "|---|---:|" + "|".join("---:" for _ in component_keys) + "|"
    lines.append(header)
    lines.append(sep)
    for row_key in row_keys:
        rows = grouped_rows.get(row_key, [])
        if not rows:
            continue
        means = component_means(rows, component_keys)
        label = row_key.split("::", 1)[1] if "::" in row_key else row_key
        values = " | ".join(fmt(means[k]) for k in component_keys)
        lines.append(f"| {label} | {len(rows)} | {values} |")
    return lines


def display_path(path_text: str) -> str:
    path = Path(path_text)
    if path.is_absolute():
        try:
            return str(path.relative_to(PROJECT))
        except ValueError:
            return str(path)
    return str(path)


def main() -> None:
    files = sorted(RESULT_DIR.glob("*_e131_hidden_localization_mixed_chat.json"))
    if not files:
        raise SystemExit(f"No E131 result JSON files under {RESULT_DIR}")

    report: dict[str, Any] = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "E131_e119_e146_hidden_localization",
        "source_dir": str(RESULT_DIR),
        "outputs": {
            "markdown": str(REPORT_MD),
            "json": str(REPORT_JSON),
        },
        "models": {},
    }

    md: list[str] = []
    md.append("# E131 E119/E146 Hidden Localization / E119/E146 隐藏层定位")
    md.append("")
    md.append(f"- Created / 生成时间：`{report['created_at']}`")
    md.append("- Mode / 模式：`NG`, `thinking=false`, direct strict verifier replay。")
    md.append("- Source labels / 标签来源：`data/processed/e119_e146_process_audit_official_20260430.jsonl`。")
    md.append("- Verifier prompt / verifier prompt：只包含 problem 与可见 trace prefix；人工标签、gold answer、error span 只用于离线选行和截断点。")
    md.append("- Hidden signal / 隐藏信号：使用 E61 受控任务训练出的过程有效性方向，对 E119/E146 自然困难题 prefix 的 residual / MLP / token-mixer / norm 输出做 teacher-forced 投影。")
    md.append("")
    md.append("说人话：E131 问的是，模型 trace 里出现错步、修复标记、最终完成这些时间点时，verifier 内部状态是否跟着移动；以及有些未修复 ACPI 明明内部有“这一步不太对”的信号，最终 Yes/No 是否仍然放行。")
    md.append("")
    md.append("## Main Results / 主要结果")

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        model_key = data["model_key"]
        label = MODEL_LABELS.get(model_key, model_key)
        rows = data["rows"]
        best_key = data["best_component_key"]
        component_keys_for_table = candidate_component_keys(data)

        by_trace = {k: summarize_rows(v, best_key) for k, v in group(rows, lambda r: r.get("trace_class")).items()}
        by_stage = {k: summarize_rows(v, best_key) for k, v in group(rows, lambda r: r.get("stage")).items()}
        trace_stage_rows = group(rows, lambda r: f"{r.get('trace_class')}::{r.get('stage')}")
        by_trace_stage = {
            k: summarize_rows(v, best_key)
            for k, v in trace_stage_rows.items()
        }
        leakage = data.get("leakage_audit", {})
        model_summary = {
            "path": str(path),
            "component_cache_pt": data.get("component_cache_pt"),
            "best_hidden_layer": data.get("best_hidden_layer"),
            "best_component_key": best_key,
            "selected_hidden_layers": data.get("selected_hidden_layers"),
            "component_cache_shape": data.get("component_cache_shape"),
            "n_prefix_rows": len(rows),
            "leakage_audit": leakage,
            "by_trace_class": by_trace,
            "by_stage": by_stage,
            "by_trace_class_stage": by_trace_stage,
            "args": data.get("args", {}),
        }
        report["models"][model_key] = model_summary

        md.append("")
        md.append(f"### {label}")
        md.append("")
        md.append(f"- Result / 结果：`{path.relative_to(PROJECT)}`")
        md.append(f"- Cache / 激活缓存：`{display_path(data['component_cache_pt'])}`")
        md.append(f"- Best hidden/component / 最强方向：`{best_key}`；selected layers={data.get('selected_hidden_layers')}")
        md.append(
            "- Leakage audit / 泄露审计："
            f"error_span={leakage.get('error_spans_in_prompt_rows')}, "
            f"gold={leakage.get('gold_answer_in_prompt_rows')}, "
            f"labels={leakage.get('labels_in_prompt_rows')}."
        )
        md.append("")
        md.append("| Slice / 切片 | n | accept rate / 接受率, Wilson 95% CI | mean Yes-No | mean best component |")
        md.append("|---|---:|---:|---:|---:|")
        for slice_name in KEY_SLICES["trace_class"]:
            if slice_name in by_trace:
                md.append(compact_table_line(slice_name, by_trace[slice_name]))
        md.append("")
        md.append("| Stage / 阶段 | n | accept rate / 接受率, Wilson 95% CI | mean Yes-No | mean best component |")
        md.append("|---|---:|---:|---:|---:|")
        for slice_name in KEY_SLICES["stage"]:
            if slice_name in by_stage:
                md.append(compact_table_line(slice_name, by_stage[slice_name]))

        if "repaired_acpi::first_final_answer_end" in by_trace_stage:
            md.append("")
            md.append("Repaired ACPI stage movement / 已修复 ACPI 的阶段移动：")
            md.append("")
            md.append("| Stage / 阶段 | n | accept rate / 接受率, Wilson 95% CI | mean Yes-No | mean best component |")
            md.append("|---|---:|---:|---:|---:|")
            for stage in KEY_SLICES["stage"]:
                key = f"repaired_acpi::{stage}"
                if key in by_trace_stage:
                    md.append(compact_table_line(stage, by_trace_stage[key]))
            component_lines = component_table_lines(
                trace_stage_rows,
                [f"repaired_acpi::{stage}" for stage in KEY_SLICES["stage"]],
                component_keys_for_table,
            )
            if component_lines:
                md.append("")
                md.append("Component projection means for repaired ACPI / 已修复 ACPI 的组件投影均值：")
                md.append("")
                md.extend(component_lines)

        if "unrepaired_acpi::completion_end" in by_trace_stage:
            md.append("")
            md.append("Unrepaired ACPI stage movement / 未修复 ACPI 的阶段移动：")
            md.append("")
            md.append("| Stage / 阶段 | n | accept rate / 接受率, Wilson 95% CI | mean Yes-No | mean best component |")
            md.append("|---|---:|---:|---:|---:|")
            for stage in KEY_SLICES["stage"]:
                key = f"unrepaired_acpi::{stage}"
                if key in by_trace_stage:
                    md.append(compact_table_line(stage, by_trace_stage[key]))
            component_lines = component_table_lines(
                trace_stage_rows,
                [f"unrepaired_acpi::{stage}" for stage in KEY_SLICES["stage"]],
                component_keys_for_table,
            )
            if component_lines:
                md.append("")
                md.append("Component projection means for unrepaired ACPI / 未修复 ACPI 的组件投影均值：")
                md.append("")
                md.extend(component_lines)

    md.append("")
    md.append("## Interpretation / 解析")
    md.append("")
    md.append("- Qwen3.5-27B 与 Gemma4-31B-it：strict-valid rows 的 Yes/No margin 和 residual/component 投影为正；repaired ACPI 在 error/repair prefix 上明显转负，说明过程错误不是只在输出文字里，verifier 内部状态也有对应移动。")
    md.append("- Gemma4-26B-A4B-it：两条 unrepaired ACPI 在错误标记附近被拒绝，但 completion 阶段又被接受；best component score 仍低于 strict-valid。这是当前最有价值的错配证据：内部有较弱/负向过程信号，最终 Yes/No 仍被答案自洽和后文牵回。")
    md.append("- MLP/token-mixer/attention 相关组件的分数也随 prefix 变化，但本报告只把它们作为 component-level observability；真正的因果组件结论仍需要后续 E122/E126 做 activation steering 或 span patch。")
    md.append("- 本结果支持“过程证据存在但被 objective/threshold/readout/answer-anchor/repair-aware policy 错配使用”的链条；不支持把 hidden probe 写成完整机制电路，也不支持说自然 unrepaired ACPI 高频。")
    md.append("")
    md.append("## Audit Boundary / 审计边界")
    md.append("")
    md.append("- Direct/non-thinking verifier replay only；不代表 thinking verifier 的完整行为。")
    md.append("- E61 方向来自受控任务，E131 是跨任务投影诊断；这增强泛化证据，但不是因果干预。")
    md.append("- Error spans and manual labels are never included in verifier prompts; they are offline audit metadata used for selecting prefixes. / 错误 span 与人工标签没有进入 verifier prompt。")
    md.append("- Accept-rate CI uses Wilson 95%; mean Yes-No/component CI in JSON uses normal approximation and should be treated as descriptive. / 接受率用 Wilson 95%，均值 CI 只是描述性。")

    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"markdown": str(REPORT_MD), "json": str(REPORT_JSON)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
