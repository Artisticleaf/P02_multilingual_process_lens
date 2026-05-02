#!/usr/bin/env python3
"""Audit E166 hidden-monitor calibration results.

The main question is whether causal hidden/component scores can localize known
wrong-step prefix boundaries without using manual spans in the prompt.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
RESULT_DIR = PROJECT / "results/E166_hardened_hidden_monitor_replay"
OUT_JSON = PROJECT / "reports/E166_HIDDEN_MONITOR_CALIBRATION_AUDIT_20260502.json"
OUT_MD = PROJECT / "reports/E166_HIDDEN_MONITOR_CALIBRATION_AUDIT_20260502.md"
MODELS = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def auc(pos: list[float], neg: list[float]) -> float | None:
    if not pos or not neg:
        return None
    wins = 0.0
    for p in pos:
        for n in neg:
            if p > n:
                wins += 1.0
            elif p == n:
                wins += 0.5
    return wins / (len(pos) * len(neg))


def quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    vals = sorted(values)
    idx = min(len(vals) - 1, max(0, int(round(q * (len(vals) - 1)))))
    return vals[idx]


def risk_for(row: dict[str, Any], key: str) -> float:
    if key == "yes_no_diagnostic":
        return -float(row["yes_minus_no"])
    return -float(row["component_validity_scores"][key])


def threshold_eval(rows: list[dict[str, Any]], key: str, threshold: float) -> dict[str, Any]:
    target = [r for r in rows if r["monitor_target_offline"]]
    valid = [r for r in rows if r["trace_class"] == "valid"]
    invalid_non_target = [r for r in rows if r["trace_class"] != "valid" and not r["monitor_target_offline"]]
    all_non_target = [r for r in rows if not r["monitor_target_offline"]]
    def rate(vals: list[dict[str, Any]]) -> float | None:
        if not vals:
            return None
        return sum(risk_for(r, key) >= threshold for r in vals) / len(vals)
    return {
        "threshold": threshold,
        "target_recall": rate(target),
        "valid_false_trigger_rate": rate(valid),
        "invalid_non_target_trigger_rate": rate(invalid_non_target),
        "all_non_target_trigger_rate": rate(all_non_target),
        "overall_trigger_rate": rate(rows),
    }


def per_solution_localization(rows: list[dict[str, Any]], key: str, threshold: float | None) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["solution_id"]].append(row)
    ranks = []
    exact_top1 = 0
    exact_top2 = 0
    exact_top3 = 0
    first_trigger_exact = 0
    first_trigger_before = 0
    first_trigger_after = 0
    first_trigger_none = 0
    considered = 0
    examples = []
    for solution_id, vals in groups.items():
        targets = [r for r in vals if r["monitor_target_offline"]]
        if not targets:
            continue
        target = targets[0]
        considered += 1
        ranked = sorted(vals, key=lambda r: risk_for(r, key), reverse=True)
        rank = 1 + next(i for i, r in enumerate(ranked) if r["prefix_id"] == target["prefix_id"])
        ranks.append(rank)
        exact_top1 += int(rank == 1)
        exact_top2 += int(rank <= 2)
        exact_top3 += int(rank <= 3)
        if threshold is not None:
            ordered = sorted(vals, key=lambda r: (r["prefix_char_end"], r["prefix_id"]))
            fired = next((r for r in ordered if risk_for(r, key) >= threshold), None)
            if fired is None:
                first_trigger_none += 1
            elif fired["prefix_id"] == target["prefix_id"]:
                first_trigger_exact += 1
            elif fired["prefix_char_end"] < target["prefix_char_end"]:
                first_trigger_before += 1
            else:
                first_trigger_after += 1
        if len(examples) < 8 and rank > 1:
            examples.append(
                {
                    "solution_id": solution_id,
                    "target_prefix_id": target["prefix_id"],
                    "target_family": target["family"],
                    "target_trace_class": target["trace_class"],
                    "target_visible_span": target["visible_span"],
                    "target_risk": risk_for(target, key),
                    "target_rank": rank,
                    "top_prefix_id": ranked[0]["prefix_id"],
                    "top_boundary_kind": ranked[0]["boundary_kind"],
                    "top_visible_span": ranked[0]["visible_span"],
                    "top_risk": risk_for(ranked[0], key),
                }
            )
    return {
        "solutions_with_target": considered,
        "target_rank_mean": mean(ranks) if ranks else None,
        "target_rank_median": median(ranks) if ranks else None,
        "target_top1_rate": exact_top1 / considered if considered else None,
        "target_top2_rate": exact_top2 / considered if considered else None,
        "target_top3_rate": exact_top3 / considered if considered else None,
        "first_trigger_exact_rate": first_trigger_exact / considered if considered and threshold is not None else None,
        "first_trigger_before_rate": first_trigger_before / considered if considered and threshold is not None else None,
        "first_trigger_after_rate": first_trigger_after / considered if considered and threshold is not None else None,
        "first_trigger_none_rate": first_trigger_none / considered if considered and threshold is not None else None,
        "rank_miss_examples": examples,
    }


def family_metrics(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_family[row["family"]].append(row)
    out = {}
    for family, vals in sorted(by_family.items()):
        target = [risk_for(r, key) for r in vals if r["monitor_target_offline"]]
        valid = [risk_for(r, key) for r in vals if r["trace_class"] == "valid"]
        nontarget = [risk_for(r, key) for r in vals if not r["monitor_target_offline"]]
        out[family] = {
            "n": len(vals),
            "targets": len(target),
            "valid_controls": len(valid),
            "target_vs_valid_auc": auc(target, valid),
            "target_vs_non_target_auc": auc(target, nontarget),
            "mean_target_risk": mean(target) if target else None,
            "mean_valid_risk": mean(valid) if valid else None,
        }
    return out


def analyze_model(path: Path) -> dict[str, Any]:
    data = read_json(path)
    rows = data["rows"]
    target = [r for r in rows if r["monitor_target_offline"]]
    valid = [r for r in rows if r["trace_class"] == "valid"]
    non_target = [r for r in rows if not r["monitor_target_offline"]]
    keys = list(data["component_keys"]) + ["yes_no_diagnostic"]
    component_records = []
    for key in keys:
        target_risk = [risk_for(r, key) for r in target]
        valid_risk = [risk_for(r, key) for r in valid]
        non_target_risk = [risk_for(r, key) for r in non_target]
        valid_90 = quantile(valid_risk, 0.90)
        all_non_target_75 = quantile(non_target_risk, 0.75)
        rec = {
            "key": key,
            "target_vs_valid_auc": auc(target_risk, valid_risk),
            "target_vs_non_target_auc": auc(target_risk, non_target_risk),
            "mean_target_risk": mean(target_risk) if target_risk else None,
            "mean_valid_risk": mean(valid_risk) if valid_risk else None,
            "mean_non_target_risk": mean(non_target_risk) if non_target_risk else None,
            "high_precision_threshold": valid_90,
            "high_precision_eval": threshold_eval(rows, key, valid_90) if valid_90 is not None else None,
            "budgeted_threshold": all_non_target_75,
            "budgeted_eval": threshold_eval(rows, key, all_non_target_75) if all_non_target_75 is not None else None,
        }
        # Primary sort favors valid false-trigger control, then exact/non-target localization.
        rec["primary_score"] = (
            (rec["target_vs_valid_auc"] or 0.0)
            + 0.5 * (rec["target_vs_non_target_auc"] or 0.0)
            + 0.25 * ((rec["high_precision_eval"] or {}).get("target_recall") or 0.0)
        )
        component_records.append(rec)
    ranked = sorted(component_records, key=lambda r: r["primary_score"], reverse=True)
    best = ranked[0]
    return {
        "model_key": data["model_key"],
        "path": str(path.relative_to(PROJECT)),
        "component_cache_pt": data.get("component_cache_pt"),
        "component_cache_shape": data.get("component_cache_shape"),
        "rows": len(rows),
        "target_rows": len(target),
        "valid_control_rows": len(valid),
        "non_target_rows": len(non_target),
        "best_key": best["key"],
        "best_key_record": best,
        "top_keys": ranked[:8],
        "localization_best_high_precision": per_solution_localization(
            rows,
            best["key"],
            (best["high_precision_eval"] or {}).get("threshold"),
        ),
        "localization_best_budgeted": per_solution_localization(
            rows,
            best["key"],
            (best["budgeted_eval"] or {}).get("threshold"),
        ),
        "family_metrics_best_key": family_metrics(rows, best["key"]),
        "leakage_audit": data.get("leakage_audit", {}),
    }


def pct(x: float | None) -> str:
    if x is None:
        return "NA"
    return f"{100*x:.1f}%"


def num(x: float | None) -> str:
    if x is None:
        return "NA"
    return f"{x:.3f}"


def render_md(result: dict[str, Any]) -> str:
    lines = [
        "# E166 Hidden-Monitor Calibration Audit / E166 hidden monitor 校准审计",
        "",
        f"Date / 日期：`{result['created_at']}`.",
        "",
        "## Plain-Language Result / 说人话结论",
        "",
        "- E166 now has full three-model causal replay results. / E166 已有三模型全量因果 replay 结果。",
        "- The prompt uses only the problem and the current prefix; manual error spans are offline labels only. / prompt 只含题目和当前 prefix；人工错步只作离线标签。",
        "- Qwen35 and Gemma31 show strong hidden/component separation between true error-span ends and valid prefixes. / Qwen35 和 Gemma31 的隐藏/组件信号能强地区分真实错步结束点和正确 prefix。",
        "- Gemma MoE also has usable signal, but it is weaker and should be reported separately. / Gemma MoE 也有可用信号，但更弱，应单独报告。",
        "- Yes/No diagnostic logits are not enough for MoE; component states are the main evidence. / Yes/No 诊断 logit 对 MoE 不够，component state 才是主要证据。",
        "",
        "## Best Monitor Per Model / 每个模型的最佳 monitor",
        "",
        "| model | best key | target-vs-valid AUC | target-vs-non-target AUC | high-precision target recall | valid false-trigger | target top1 | target top2 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model in result["models"]:
        best = model["best_key_record"]
        hp = best["high_precision_eval"]
        loc = model["localization_best_high_precision"]
        lines.append(
            f"| `{model['model_key']}` | `{model['best_key']}` | {num(best['target_vs_valid_auc'])} | "
            f"{num(best['target_vs_non_target_auc'])} | {pct(hp['target_recall'])} | "
            f"{pct(hp['valid_false_trigger_rate'])} | {pct(loc['target_top1_rate'])} | {pct(loc['target_top2_rate'])} |"
        )
    lines.extend(["", "## Top Component Keys / 组件信号排序", ""])
    for model in result["models"]:
        lines.append(f"### {model['model_key']}")
        lines.append("")
        lines.append("| key | target-vs-valid AUC | target-vs-non-target AUC | target recall @valid90 | valid false-trigger |")
        lines.append("|---|---:|---:|---:|---:|")
        for rec in model["top_keys"]:
            hp = rec["high_precision_eval"]
            lines.append(
                f"| `{rec['key']}` | {num(rec['target_vs_valid_auc'])} | {num(rec['target_vs_non_target_auc'])} | "
                f"{pct(hp['target_recall'])} | {pct(hp['valid_false_trigger_rate'])} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Interpretation / 解释",
            "",
            "- `target-vs-valid AUC` asks: do true wrong-step endpoints look riskier than correct prefixes? / `target-vs-valid AUC` 问的是：真实错步结束点是否比正确 prefix 更像高风险。",
            "- `target-vs-non-target AUC` asks: can the monitor localize the exact wrong boundary rather than merely saying the whole trace is bad? / `target-vs-non-target AUC` 问的是：monitor 是否能定位具体错步，而不是只知道这条 trace 整体不对。",
            "- High-precision threshold is set at the 90th percentile of valid controls, so valid false-trigger is capped near 10% on this calibration set. / 高精度阈值取正确 prefix 的 90 分位，因此本校准集上正确 prefix 误触发约 10%。",
            "- E167 should use these hidden-derived thresholds/spans and keep oracle manual spans only as an upper bound. / E167 应使用这些 hidden-derived 阈值/span，人工 oracle span 只能当上界。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    models = []
    for model_key in MODELS:
        path = RESULT_DIR / f"{model_key}_e166_generation_prefill_full_20260502.json"
        models.append(analyze_model(path))
    result = {
        "experiment": "E166_hidden_monitor_calibration_audit",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "models": models,
        "method_note": "Risk is -component_validity_score, because E61 directions are valid-minus-invalid. All prompts use only problem and prefix_text; labels are offline.",
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(result), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(PROJECT)}")
    print(f"wrote {OUT_MD.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
