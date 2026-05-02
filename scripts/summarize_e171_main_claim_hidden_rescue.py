#!/usr/bin/env python3
"""Summarize E171 main-claim hidden rescue results."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
RESULT_DIR = PROJECT / "results/E171_main_claim_hidden_rescue"
OUT_JSON = PROJECT / "reports/E171_MAIN_CLAIM_HIDDEN_RESCUE_STAGE_ANALYSIS_20260502.json"
OUT_MD = PROJECT / "reports/E171_MAIN_CLAIM_HIDDEN_RESCUE_STAGE_ANALYSIS_20260502.md"

MODELS = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"]
VARIANTS = [
    "baseline_regenerate",
    "prefix_continue",
    "hidden_generic_warning",
    "hidden_localized_warning",
    "random_matched_warning",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_result(model_key: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str, dict[str, Any]]:
    preferred = sorted(RESULT_DIR.glob(f"{model_key}_e171_hidden_rescue_max16384_20260502.json"))
    matches = preferred or sorted(p for p in RESULT_DIR.glob(f"{model_key}_e171_hidden_rescue*.json") if "smoke" not in p.name)
    if not matches:
        matches = sorted(RESULT_DIR.glob(f"{model_key}_e171_hidden_rescue*.json"))
    if matches:
        data = json.loads(matches[-1].read_text(encoding="utf-8"))
        return list(data.get("rows", [])), list(data.get("cases", [])), str(matches[-1].relative_to(PROJECT)), data.get("summary", {})
    ckpt = PROJECT / f"logs/e171_rescue_{model_key}_checkpoint_20260502.jsonl"
    rows = load_jsonl(ckpt)
    dedup = {(r["case_id"], r["prompt_variant"]): r for r in rows}
    case_path = PROJECT / f"data/processed/e171_hidden_rescue_cases_{model_key}_20260502.jsonl"
    cases = load_jsonl(case_path)
    return list(dedup.values()), cases, str(ckpt.relative_to(PROJECT)), {}


def row_ok(row: dict[str, Any]) -> bool:
    return bool(row.get("manual_final_correct"))


def row_tokens(row: dict[str, Any]) -> int:
    return int(row.get("generated_tokens") or 0)


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tokens = [row_tokens(r) for r in rows]
    correct = [r for r in rows if row_ok(r)]
    return {
        "n": len(rows),
        "correct": len(correct),
        "rescue_rate_among_baseline_wrong": len(correct) / len(rows) if rows else None,
        "completion_tokens": sum(tokens),
        "mean_completion_tokens": mean(tokens) if tokens else None,
        "median_completion_tokens": median(tokens) if tokens else None,
        "cost_per_success_completion_tokens": sum(tokens) / len(correct) if correct else None,
        "final_marker_found": sum(int(bool(r.get("final_marker_found"))) for r in rows),
        "hit_max_new_tokens": sum(int(bool(r.get("hit_max_new_tokens"))) for r in rows),
    }


def exact_sign_p_left_better(left_wins: int, right_wins: int) -> float | None:
    n = left_wins + right_wins
    if n == 0:
        return None
    return sum(comb(n, k) for k in range(left_wins, n + 1)) / (2**n)


def exact_sign_p_two_sided(left_wins: int, right_wins: int) -> float | None:
    n = left_wins + right_wins
    if n == 0:
        return None
    low = min(left_wins, right_wins)
    return min(1.0, 2.0 * sum(comb(n, k) for k in range(0, low + 1)) / (2**n))


def comb(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    k = min(k, n - k)
    out = 1
    for i in range(1, k + 1):
        out = out * (n - k + i) // i
    return out


def paired_deltas(rows: list[dict[str, Any]], left: str, right: str) -> dict[str, Any]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[row["case_id"]][row["prompt_variant"]] = row
    pairs = [(vals[left], vals[right]) for vals in grouped.values() if left in vals and right in vals]
    left_wins = sum(int(row_ok(a) and not row_ok(b)) for a, b in pairs)
    right_wins = sum(int(row_ok(b) and not row_ok(a)) for a, b in pairs)
    token_delta = [row_tokens(a) - row_tokens(b) for a, b in pairs]
    return {
        "left": left,
        "right": right,
        "pairs": len(pairs),
        "left_wins": left_wins,
        "right_wins": right_wins,
        "both_correct": sum(int(row_ok(a) and row_ok(b)) for a, b in pairs),
        "both_wrong": sum(int((not row_ok(a)) and (not row_ok(b))) for a, b in pairs),
        "discordant_pairs": left_wins + right_wins,
        "exact_sign_p_left_better_one_sided": exact_sign_p_left_better(left_wins, right_wins),
        "exact_sign_p_two_sided": exact_sign_p_two_sided(left_wins, right_wins),
        "accuracy_delta_left_minus_right": (left_wins - right_wins) / len(pairs) if pairs else None,
        "mean_completion_token_delta_left_minus_right": mean(token_delta) if token_delta else None,
        "median_completion_token_delta_left_minus_right": median(token_delta) if token_delta else None,
    }


def model_summary(model_key: str) -> dict[str, Any]:
    rows, cases, source, run_summary = load_result(model_key)
    by_variant = {v: summarize_rows([r for r in rows if r.get("prompt_variant") == v]) for v in VARIANTS}
    by_family_variant: dict[str, dict[str, Any]] = {}
    for family in sorted({r.get("family") for r in rows}):
        fam_rows = [r for r in rows if r.get("family") == family]
        by_family_variant[family] = {v: summarize_rows([r for r in fam_rows if r.get("prompt_variant") == v]) for v in VARIANTS}
    return {
        "model_key": model_key,
        "source": source,
        "rows": len(rows),
        "cases": len(cases),
        "complete_variant_sets": sum(1 for _case, vals in group_by_case(rows).items() if all(v in vals for v in VARIANTS)),
        "hidden_threshold_crossed_cases": sum(int(c.get("hidden_trigger_threshold_crossed")) for c in cases),
        "hidden_fallback_top_risk_cases": sum(int(c.get("hidden_trigger_source") == "fallback_top_risk_no_threshold_crossing") for c in cases),
        "by_variant": by_variant,
        "by_family_variant": by_family_variant,
        "paired_deltas": [
            paired_deltas(rows, "hidden_localized_warning", "prefix_continue"),
            paired_deltas(rows, "hidden_localized_warning", "hidden_generic_warning"),
            paired_deltas(rows, "hidden_localized_warning", "random_matched_warning"),
            paired_deltas(rows, "hidden_localized_warning", "baseline_regenerate"),
            paired_deltas(rows, "hidden_generic_warning", "prefix_continue"),
        ],
        "leakage_counts": {
            "gold_answer_in_prompt_rows": sum(int(bool(r.get("gold_answer_in_prompt"))) for r in rows),
            "manual_label_in_prompt_rows": sum(int(bool(r.get("manual_label_in_prompt"))) for r in rows),
            "localized_prompt_rows": sum(int(bool(r.get("localized_span_in_prompt"))) for r in rows),
            "random_prompt_rows": sum(int(bool(r.get("random_span_in_prompt"))) for r in rows),
        },
        "status_counts": {
            f"{variant}|final={final_marker}|hit_max={hit_max}": count
            for (variant, final_marker, hit_max), count in sorted(
                Counter((r.get("prompt_variant"), bool(r.get("final_marker_found")), bool(r.get("hit_max_new_tokens"))) for r in rows).items(),
                key=lambda kv: str(kv[0]),
            )
        },
        "run_summary": run_summary,
    }


def group_by_case(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    out: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        out[row["case_id"]][row["prompt_variant"]] = row
    return out


def fmt(v: Any) -> str:
    if v is None:
        return "NA"
    if isinstance(v, float):
        return f"{v:.3f}"
    return str(v)


def write_md(result: dict[str, Any]) -> None:
    lines = [
        "# E171 Main-Claim Hidden Rescue Stage Analysis / E171 主 claim hidden rescue 阶段分析",
        "",
        f"Created / 创建时间：`{result['created_at']}`.",
        "",
        "Scope / 范围：E171 keeps only original-problem non-thinking baseline failures, then uses a hidden monitor over the model's own wrong trace to choose a causal truncation point. / E171 只保留原题 non-thinking baseline 做错的题，再在模型自己的错误 trace 上用 hidden monitor 选择因果截断点。",
        "",
        "Claim boundary / claim 边界：`hidden_generic_warning` and `hidden_localized_warning` are text interventions derived from hidden signals. The hidden measurement itself is the teacher-forced component cache saved in `.pt`. / `hidden_generic_warning` 与 `hidden_localized_warning` 是由 hidden 信号导出的文字干预；真正的 hidden 测量是保存的 `.pt` component cache。",
        "",
    ]
    for model, info in result["by_model"].items():
        lines.extend(
            [
                f"## {model}",
                "",
                f"- Source / 来源：`{info['source']}`",
                f"- Baseline-wrong cases / baseline 错题 case：{info['cases']}; complete variant sets / 变体齐全：{info['complete_variant_sets']}.",
                f"- Hidden threshold crossed / hidden 阈值触发：{info['hidden_threshold_crossed_cases']}; fallback top-risk / 未触发时 top-risk fallback：{info['hidden_fallback_top_risk_cases']}.",
                f"- Leakage counts / 泄漏计数：`{info['leakage_counts']}`.",
                "",
                "| variant | n | rescued | rescue rate | completion tokens | cost/success | mean tokens | hit-max | final marker |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for variant in VARIANTS:
            row = info["by_variant"][variant]
            lines.append(
                f"| {variant} | {row['n']} | {row['correct']} | {fmt(row['rescue_rate_among_baseline_wrong'])} | "
                f"{row['completion_tokens']} | {fmt(row['cost_per_success_completion_tokens'])} | {fmt(row['mean_completion_tokens'])} | "
                f"{row['hit_max_new_tokens']} | {row['final_marker_found']} |"
            )
        lines.extend(["", "### Paired Deltas / 配对差异", ""])
        lines.append("| left vs right | pairs | left wins | right wins | p(left better) | two-sided p | acc delta | mean token delta |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for d in info["paired_deltas"]:
            lines.append(
                f"| {d['left']} - {d['right']} | {d['pairs']} | {d['left_wins']} | {d['right_wins']} | "
                f"{fmt(d['exact_sign_p_left_better_one_sided'])} | {fmt(d['exact_sign_p_two_sided'])} | "
                f"{fmt(d['accuracy_delta_left_minus_right'])} | {fmt(d['mean_completion_token_delta_left_minus_right'])} |"
            )
        lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    result = {
        "experiment": "E171_main_claim_hidden_rescue_stage_analysis",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "models": MODELS,
        "variants": VARIANTS,
        "by_model": {model: model_summary(model) for model in MODELS},
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_md(result)
    print(json.dumps({"wrote": [str(OUT_JSON.relative_to(PROJECT)), str(OUT_MD.relative_to(PROJECT))]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
