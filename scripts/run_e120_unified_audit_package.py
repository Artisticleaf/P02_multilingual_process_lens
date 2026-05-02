#!/usr/bin/env python3
"""E120 unified audit package for official results."""
from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / den
    return center - half, center + half


def pct(x: float | None) -> str:
    return "NA" if x is None else f"{x:.3f}"


def load_e106() -> list[dict[str, Any]]:
    out = []
    root = PROJECT / "results/E106_E114_nonthinking_mechanism_suite"
    for path in sorted(root.glob("*_e106_e114_nonthinking_mechanism_suite.json")):
        data = read_json(path)
        e106 = data["sections"]["E106_E107_confidence_vs_process"]["summary"]
        e114_rows = {r["slice"]: r for r in data["sections"]["E114_hidden_gated_filter"]["summary"]}
        acpi = e114_rows["acpi_invalid"]
        valid = e114_rows["valid"]
        base_k = round(acpi["base_accept_rate"] * acpi["n"])
        gate_k = round(acpi["gated_accept_rate"] * acpi["n"])
        out.append(
            {
                "model_key": data["model_key"],
                "mode": "MI-DV",
                "hidden_auc": e106["hidden_process_auc_valid"],
                "confidence_auc": e106["readout_confidence_auc_valid"],
                "partial_corr": e106["hidden_label_partial_corr_controlling_readout_confidence_entropy"],
                "direction_cosine": e106["direction_cosine_mean"],
                "plain_yes_no_accuracy": e106["yes_no_accuracy"],
                "acpi_base_accept": acpi["base_accept_rate"],
                "acpi_base_accept_ci": wilson(base_k, acpi["n"]),
                "acpi_gated_accept": acpi["gated_accept_rate"],
                "acpi_gated_accept_ci": wilson(gate_k, acpi["n"]),
                "valid_base_accept": valid["base_accept_rate"],
                "valid_gated_accept": valid["gated_accept_rate"],
                "leakage_audit": data.get("leakage_audit", {}),
            }
        )
    return out


def load_e116() -> dict[str, Any]:
    path = PROJECT / "results/E116_E118_thinking_stop_signal/qwen35_27b_e116_e118_thinking_stop_signal_suite.json"
    if not path.exists():
        return {"available": False}
    data = read_json(path)
    return {
        "available": True,
        "mode": "MI-TG",
        "model_key": data["model_key"],
        "component_cache_shape": data["component_cache_shape"],
        "selected_stop_key": data["selected_stop_key"],
        "selected_stop_threshold": data["selected_stop_threshold"],
        "eos_threshold": data["eos_threshold"],
        "stop_direction_summary": data["stop_direction_summary"].get(data["selected_stop_key"], {}),
        "summary_E117_stop_policy": data["summary_E117_stop_policy"],
        "leakage_audit": data["leakage_audit"],
    }


def load_e83() -> dict[str, Any]:
    path = PROJECT / "results/E83_natural_hardtask_prevalence_audit/e83_natural_hardtask_prevalence_audit.json"
    if not path.exists():
        return {"available": False}
    data = read_json(path)
    return {"available": True, "path": str(path.relative_to(PROJECT)), **data}


def pass_leakage(audit: dict[str, Any]) -> bool:
    if not audit:
        return False
    numeric = [v for k, v in audit.items() if k.endswith("_rows") and isinstance(v, int)]
    return bool(audit.get("passed", True)) and all(v == 0 for v in numeric)


def build_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# E120 Unified Audit Package / 统一审计包（2026-04-30）",
        "",
        "## 1. Purpose / 目的",
        "",
        "This package summarizes official-facing audit facts after E106-E118. It is an appendix scaffold, not a new model experiment.",
        "",
        "本包汇总 E106-E118 后的官方审计事实。它是 appendix 草稿，不是新的模型实验。",
        "",
        "## 2. Mode Boundary / 模式边界",
        "",
        "| mode | meaning | current use |",
        "|---|---|---|",
        "| DV | direct/non-thinking verifier | E42/E60/E61/E106-E114 verifier results |",
        "| MI-DV | direct verifier mechanism inspection | E65/E78/E90/E106-E114 hidden/component probes |",
        "| NG | non-thinking generation | E57/E88 natural hard-task samples |",
        "| TG | thinking generation | E92/E103/E105 generation diagnostics |",
        "| MI-TG | thinking mechanism replay | E116-E118 stop-signal replay |",
        "| PM | post-hoc simulation/statistics | E58/E83/E89/E120 |",
        "",
        "## 3. E106-E114 Audit / non-thinking 机制审计",
        "",
        "| model | hidden AUC | confidence AUC | partial corr | cosine | ACPI base | ACPI gated | valid gated | leakage |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["E106_E114"]:
        lines.append(
            f"| `{row['model_key']}` | {pct(row['hidden_auc'])} | {pct(row['confidence_auc'])} | {pct(row['partial_corr'])} | "
            f"{pct(row['direction_cosine'])} | {pct(row['acpi_base_accept'])} | {pct(row['acpi_gated_accept'])} | "
            f"{pct(row['valid_gated_accept'])} | {'PASS' if pass_leakage(row['leakage_audit']) else 'CHECK'} |"
        )
    e116 = result["E116_E118"]
    lines += [
        "",
        "Key boundary / 关键边界：process signal and confidence are highly aligned; hidden gate works as a diagnostic filter, not a calibrated deployed verifier.",
        "",
        "## 4. E116-E118 Audit / thinking 收口审计",
        "",
    ]
    if e116.get("available"):
        s = e116["stop_direction_summary"]
        p = e116["summary_E117_stop_policy"]
        lines += [
            f"- Model / 模型：`{e116['model_key']}`",
            f"- Mode / 模式：`{e116['mode']}`",
            f"- Component cache shape / 激活缓存形状：`{e116['component_cache_shape']}`",
            f"- Selected stop key / stop 方向：`{e116['selected_stop_key']}`",
            f"- Stop positive mean / clean-stop 均值：`{pct(s.get('positive_mean'))}`",
            f"- Stop negative mean / continuation 均值：`{pct(s.get('negative_mean'))}`",
            f"- Stop threshold / 阈值：`{pct(e116['selected_stop_threshold'])}`",
            f"- Policy candidates / 候选点：`{p.get('n')}`",
            f"- Either-stop rate / 触发率：`{pct(p.get('either_stop_rate'))}`",
            f"- Stopped correct candidates / 早停且正确：`{p.get('final_correct_retained_if_either_stop')}/{p.get('final_correct_candidates')}`",
            f"- Mean token savings among stopped / 触发样本平均省 token：`{pct(p.get('mean_token_savings_if_either_stop'))}`",
            f"- Leakage / 泄露：`{'PASS' if pass_leakage(e116['leakage_audit']) else 'CHECK'}`",
            "",
            "Boundary / 边界：Qwen-only, post-hoc, small-sample; useful as a stop/commit signal, not a full causal circuit.",
        ]
    else:
        lines.append("- E116-E118 result not found.")
    lines += [
        "",
        "## 5. Remaining Risks / 剩余风险",
        "",
        "- Natural unrepaired ACPI prevalence still needs larger E119 harvesting. / 自然 unrepaired ACPI 仍需要 E119 扩样。",
        "- Thinking verifier (`TV`) remains separate from direct first-token verifier (`DV`). / thinking verifier 仍需和 direct first-token verifier 分开。",
        "- Hidden probes need threshold calibration and cross-model replication before being described as deployable filters. / hidden probe 需要阈值校准和跨模型复现。",
        "- E116 stop signal is distinct from process-validity signal; do not merge them into one claim. / E116 stop 信号不能和过程有效性信号混成一个 claim。",
        "",
        "## 6. Current Safe Claim / 当前安全 claim",
        "",
        "> Controlled strict ACPI trace-selection risk is robust in direct/non-thinking verifier settings. Hidden activations contain process-validity evidence, but confidence, objective, threshold, answer anchoring, repair-aware reading, long self-consistency, and output/readout format determine whether final decisions use it. Thinking adds a separate stop/commit bottleneck: a model can have valid process evidence and still fail to submit and stop cleanly.",
        "",
        "中文：",
        "",
        "> 在 direct/non-thinking verifier 中，受控 strict ACPI trace-selection 风险稳健存在。hidden activation 中有过程有效性证据，但最终决策是否使用它，取决于置信度、目标、阈值、答案锚定、repair-aware 阅读、长自洽后文和输出读出格式。thinking 又额外引入 stop/commit 瓶颈：模型可以已经有有效过程证据，却仍然不能稳定提交并停止。",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    result = {
        "experiment": "E120_unified_audit_package",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "E106_E114": load_e106(),
        "E116_E118": load_e116(),
        "E83": load_e83(),
        "notes": [
            "E120 is an appendix/audit synthesis, not a new model run.",
            "All mode labels must remain separated in paper-facing claims.",
        ],
    }
    out_json = PROJECT / "reports/E120_UNIFIED_AUDIT_PACKAGE_20260430.json"
    out_md = PROJECT / "reports/E120_UNIFIED_AUDIT_PACKAGE_20260430.md"
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    out_md.write_text(build_markdown(result), encoding="utf-8")
    print(json.dumps({"wrote": [str(out_json.relative_to(PROJECT)), str(out_md.relative_to(PROJECT))]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
