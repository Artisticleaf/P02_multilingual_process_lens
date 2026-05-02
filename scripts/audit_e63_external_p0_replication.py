#!/usr/bin/env python3
"""Audit and summarize E63 expanded-P0 GLM replication outputs."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
MODEL = "glm47_flash_candidate"
REPORT = PROJECT / "reports/E63_GLM_EXPANDED_P0_REPLICATION_20260429.md"
AUDIT = PROJECT / "reports/E63_GLM_EXPANDED_P0_REPLICATION_AUDIT_20260429.json"


PATHS = {
    "e42": PROJECT / "results/E42_official_template_parity/glm47_flash_candidate_e42_official_template_parity_chat.json",
    "e60": PROJECT / "results/E60_objective_ladder/glm47_flash_candidate_e60_objective_ladder_chat.json",
    "e61": PROJECT / "results/E61_language_error_grid/glm47_flash_candidate_e61_language_error_grid_chat.json",
    "e55": PROJECT / "results/E55_residual_to_logit_mediation/glm47_flash_candidate_e55_residual_to_logit_mediation.json",
    "e56": PROJECT / "results/E56_component_decomposition/glm47_flash_candidate_e56_component_decomposition.json",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_summary(rows: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    for row in rows:
        if all(row.get(k) == v for k, v in kwargs.items()):
            return row
    return {}


def all_slice_summaries(result: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for row in result.get("summary", []):
        if row.get("slice") == "all" or row.get("slice_type") == "all":
            out.append(row)
    return out


def contrastive_bias(rows: list[dict[str, Any]], objective: str | None = None) -> dict[str, Any]:
    selected = []
    for row in rows:
        if row.get("objective_type") == "contrastive" or row.get("objective") == "contrastive":
            if objective is None or row.get("objective") == objective:
                selected.append(row)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in selected:
        groups[str(row.get("pair_id"))].append(row)
    pair_groups = [g for g in groups.values() if g]
    both = sum(all(bool(r.get("correct")) for r in g) for g in pair_groups)
    one = sum(sum(bool(r.get("correct")) for r in g) == 1 for g in pair_groups)
    none = sum(not any(bool(r.get("correct")) for r in g) for g in pair_groups)
    sum_margin_pos = sum(sum(float(r.get("margin_target_minus_other", 0.0)) for r in g) > 0 for g in pair_groups)
    pred_a = mean([1.0 if r.get("pred") == "A" else 0.0 for r in selected]) if selected else None
    acc = mean([1.0 if r.get("correct") else 0.0 for r in selected]) if selected else None
    return {
        "objective": objective or "contrastive",
        "n_rows": len(selected),
        "n_pairs": len(pair_groups),
        "row_accuracy": acc,
        "pred_A_rate": pred_a,
        "both_orders_correct_pairs": both,
        "one_order_correct_pairs": one,
        "no_order_correct_pairs": none,
        "pair_sum_target_margin_positive": sum_margin_pos,
    }


def fmt(x: Any) -> str:
    if x is None:
        return "NA"
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def main() -> None:
    checks = []
    results: dict[str, dict[str, Any]] = {}
    for name, path in PATHS.items():
        exists = path.exists()
        checks.append({"check": f"{name} output exists", "ok": exists, "detail": str(path.relative_to(PROJECT))})
        if exists:
            results[name] = read_json(path)

    for name in ["e42", "e60", "e61", "e55", "e56"]:
        if name not in results:
            continue
        r = results[name]
        key = r.get("model_key") or r.get("verifier_model_key")
        checks.append({"check": f"{name} model key", "ok": key == MODEL, "detail": str(key)})
        checks.append({"check": f"{name} uses official chat template", "ok": bool(r.get("used_chat_template")), "detail": str(r.get("used_chat_template"))})
        args = r.get("args", {})
        if "prompt_format" in args:
            checks.append({"check": f"{name} prompt format", "ok": args.get("prompt_format") == "official_if_chat", "detail": str(args.get("prompt_format"))})
        if "local_files_only" in args:
            checks.append({"check": f"{name} local files only", "ok": bool(args.get("local_files_only")), "detail": str(args.get("local_files_only"))})

    for name in ["e60", "e61"]:
        if name not in results:
            continue
        leak = results[name].get("leakage_audit", {})
        for field in [
            "gold_label_in_prompt_rows",
            "known_error_span_annotation_in_prompt_rows",
            "manual_correction_in_prompt_rows",
        ]:
            checks.append({"check": f"{name} leakage {field}", "ok": int(leak.get(field, 0)) == 0, "detail": str(leak.get(field, 0))})
        if name == "e61":
            checks.append({"check": "e61 leakage known_error_span_in_prompt_rows", "ok": int(leak.get("known_error_span_in_prompt_rows", 0)) == 0, "detail": str(leak.get("known_error_span_in_prompt_rows", 0))})

    e42_abs = find_summary(results.get("e42", {}).get("summary", []), objective="absolute_process", slice="all")
    e42_con = find_summary(results.get("e42", {}).get("summary", []), objective="contrastive", slice="all")
    e60_all = all_slice_summaries(results.get("e60", {}))
    e61_all = all_slice_summaries(results.get("e61", {}))
    e60_by_obj = {r["objective"]: r for r in e60_all if "objective" in r}
    e61_by_obj = {r["objective"]: r for r in e61_all if "objective" in r}

    e42_bias = contrastive_bias(results.get("e42", {}).get("rows", []))
    e60_bias = [contrastive_bias(results.get("e60", {}).get("rows", []), obj) for obj in ["sibling_comparison", "careful_sibling_comparison"]]
    e61_bias = [contrastive_bias(results.get("e61", {}).get("rows", []), obj) for obj in ["sibling_comparison", "careful_sibling_comparison"]]

    e55_summary = results.get("e55", {}).get("summary", {})
    e56_summary = results.get("e56", {}).get("summary", {})

    all_ok = all(c["ok"] for c in checks)
    audit = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "model_key": MODEL,
        "passed": all_ok,
        "checks": checks,
        "key_metrics": {
            "e42_absolute": e42_abs,
            "e42_contrastive": e42_con,
            "e42_contrastive_bias": e42_bias,
            "e60_all": e60_all,
            "e60_contrastive_bias": e60_bias,
            "e61_all": e61_all,
            "e61_contrastive_bias": e61_bias,
            "e55_summary": e55_summary,
            "e56_summary": e56_summary,
        },
        "interpretation_zh": (
            "GLM-4.7-Flash 复现了 pointwise absolute Yes/No 对 ACPI 的过度接受和更严格过程检查的风险降低，"
            "但 A/B sibling comparison 出现明显标签/位置偏置；因此它不是对核心 claim 的推翻，而是把 claim 边界收紧为："
            "contrastive sibling 需要做标签/位置校准，不能被报告成所有模型上天然可靠的 oracle。"
        ),
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# E63 GLM Expanded-P0 Replication / E63 GLM 扩展 P0 复现（2026-04-29）",
        "",
        f"- Audit / 审计：`{AUDIT.relative_to(PROJECT)}`",
        f"- Model / 模型：`{MODEL}` (`GLM-4.7-Flash`), admitted by E62. / 由 E62 准入的扩展 P0 模型。",
        "- Plain language / 说人话：GLM 证明“单条 trace 的 Yes/No 过程审查会过度接受 ACPI”这个现象能跨到第三个模型家族；但它也提醒我们，A/B sibling 不是无条件 oracle，因为这个模型有明显的 A/B 标签或位置偏置。",
        "",
        "## Main Metrics / 主结果",
        "",
        "| experiment | plain pointwise ACPI accept | valid accept | stricter pointwise best | sibling accuracy | careful sibling accuracy | note |",
        "|---|---:|---:|---:|---:|---:|---|",
        (
            f"| E42 controlled parity | {fmt(e42_abs.get('acpi_accept_rate'))} | {fmt(e42_abs.get('valid_accept_rate'))} | NA | "
            f"{fmt(e42_con.get('accuracy'))} | NA | E42 A/B pred_A_rate={fmt(e42_con.get('pred_A_rate'))} |"
        ),
        (
            f"| E60 objective ladder | {fmt(e60_by_obj.get('plain_yes_no', {}).get('acpi_accept_rate'))} | {fmt(e60_by_obj.get('plain_yes_no', {}).get('valid_accept_rate'))} | "
            f"answer-blind/careful={fmt(e60_by_obj.get('answer_blind_yes_no', {}).get('acpi_accept_rate'))}/{fmt(e60_by_obj.get('careful_yes_no', {}).get('acpi_accept_rate'))} | "
            f"{fmt(e60_by_obj.get('sibling_comparison', {}).get('accuracy'))} | {fmt(e60_by_obj.get('careful_sibling_comparison', {}).get('accuracy'))} | A/B bias remains, especially plain sibling |"
        ),
        (
            f"| E61 language/error grid | {fmt(e61_by_obj.get('plain_yes_no', {}).get('acpi_accept_rate'))} | {fmt(e61_by_obj.get('plain_yes_no', {}).get('valid_accept_rate'))} | "
            f"answer-blind/careful={fmt(e61_by_obj.get('answer_blind_yes_no', {}).get('acpi_accept_rate'))}/{fmt(e61_by_obj.get('careful_yes_no', {}).get('acpi_accept_rate'))} | "
            f"{fmt(e61_by_obj.get('sibling_comparison', {}).get('accuracy'))} | {fmt(e61_by_obj.get('careful_sibling_comparison', {}).get('accuracy'))} | broad grid reproduces pointwise risk |"
        ),
        "",
        "## Contrastive Label/Position Bias / 对比式标签/位置偏置",
        "",
        "| source | objective | row accuracy | pred_A_rate | pairs both orders correct | one-order-only pairs | pair summed target-margin > 0 |",
        "|---|---|---:|---:|---:|---:|---:|",
        f"| E42 | contrastive | {fmt(e42_bias['row_accuracy'])} | {fmt(e42_bias['pred_A_rate'])} | {e42_bias['both_orders_correct_pairs']}/{e42_bias['n_pairs']} | {e42_bias['one_order_correct_pairs']}/{e42_bias['n_pairs']} | {e42_bias['pair_sum_target_margin_positive']}/{e42_bias['n_pairs']} |",
    ]
    for name, biases in [("E60", e60_bias), ("E61", e61_bias)]:
        for b in biases:
            lines.append(
                f"| {name} | {b['objective']} | {fmt(b['row_accuracy'])} | {fmt(b['pred_A_rate'])} | "
                f"{b['both_orders_correct_pairs']}/{b['n_pairs']} | {b['one_order_correct_pairs']}/{b['n_pairs']} | {b['pair_sum_target_margin_positive']}/{b['n_pairs']} |"
            )
    lines += [
        "",
        "- Interpretation / 解释：如果模型真正稳定地比较过程，bad_A 和 bad_B 两个顺序都应选中 invalid trace；GLM 大量出现“只有 bad_A 正确、bad_B 错误”的情况，说明输出头/标签先验或位置先验会压过过程信号。 / If sibling comparison were fully reliable, both orders would be correct. GLM often gets only one order right, so label/position priors can overpower process evidence.",
        "- Claim update / 主张更新：E63 支持 `absolute pointwise over-acceptance` 与 `stricter process prompts reduce but do not eliminate risk`；同时要求论文把 sibling 写成“强诊断但需标签/位置校准”，不能写成所有模型上的天然 oracle。 / E63 supports pointwise over-acceptance and objective-ladder mitigation, but sibling must be described as a strong diagnostic requiring label/position calibration, not as an unconditional oracle.",
        "",
        "## Mechanism Smoke / 机制 smoke",
        "",
        f"- E55 layer-16 residual probe accuracy: absolute={fmt(next((r.get('accuracy') for r in e55_summary.get('probe', []) if r.get('objective') == 'absolute_yes_no'), None))}, contrastive={fmt(next((r.get('accuracy') for r in e55_summary.get('probe', []) if r.get('objective') == 'contrastive_ab'), None))}. / E55 第 16 层 residual 探针有弱到中等过程信号。",
        f"- E56 layer-16 component probe accuracy: residual={fmt(next((r.get('accuracy') for r in e56_summary.get('probe', []) if r.get('component') == 'residual_layer_output'), None))}, token-mixer={fmt(next((r.get('accuracy') for r in e56_summary.get('probe', []) if r.get('component') == 'token_mixer_output'), None))}, MLP={fmt(next((r.get('accuracy') for r in e56_summary.get('probe', []) if r.get('component') == 'mlp_output'), None))}. / E56 第 16 层组件探针显示 token-mixer/residual/MLP 都有一些线性可读信息。",
        "- Boundary / 边界：GLM 的第 16 层 patch 效应弱且不稳定，不能作为强因果机制证据；后续 E65/E66 应做层扫描和路径特异中介，寻找是否存在更强层位或是否确实是 GLM 的机制边界。 / Layer-16 patching is weak and unstable; E65/E66 should test whether stronger layers/path-specific mediation exist.",
        "",
        "## Audit / 审计",
        "",
    ]
    for c in checks:
        status = "PASS" if c["ok"] else "FAIL"
        lines.append(f"- {status}: {c['check']} — {c['detail']}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"passed": all_ok, "report": str(REPORT), "audit": str(AUDIT)}, ensure_ascii=False, indent=2))
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
