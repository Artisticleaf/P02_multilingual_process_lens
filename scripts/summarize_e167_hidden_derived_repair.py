#!/usr/bin/env python3
"""Summarize E167 hidden-derived repair results.

The script is checkpoint-aware: while the long tmux queue is still running, it
can summarize completed checkpoint rows without waiting for the final JSON file.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
RESULT_DIR = PROJECT / "results/E167_hidden_derived_repair"
OUT_JSON = PROJECT / "reports/E167_HIDDEN_DERIVED_REPAIR_STAGE_ANALYSIS_20260502.json"
OUT_MD = PROJECT / "reports/E167_HIDDEN_DERIVED_REPAIR_STAGE_ANALYSIS_20260502.md"

MODELS = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"]
VARIANTS = [
    "baseline_regenerate",
    "prefix_continue",
    "hidden_generic_warning",
    "hidden_localized_warning",
    "random_matched_warning",
    "oracle_manual_span",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_result_rows(model_key: str) -> tuple[list[dict[str, Any]], str]:
    result_matches = sorted(RESULT_DIR.glob(f"{model_key}_e167_*_high_precision_20260502.json"))
    if result_matches:
        data = json.loads(result_matches[-1].read_text(encoding="utf-8"))
        return list(data.get("rows", [])), str(result_matches[-1].relative_to(PROJECT))
    checkpoint = PROJECT / f"logs/e167_repair_{model_key}_checkpoint_20260502.jsonl"
    rows = load_jsonl(checkpoint)
    dedup: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        dedup[(row["case_id"], row["prompt_variant"])] = row
    return list(dedup.values()), str(checkpoint.relative_to(PROJECT))


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
        "accuracy": len(correct) / len(rows) if rows else None,
        "final_marker_found": sum(int(bool(r.get("final_marker_found"))) for r in rows),
        "hit_max_new_tokens": sum(int(bool(r.get("hit_max_new_tokens"))) for r in rows),
        "total_completion_tokens": sum(tokens),
        "mean_completion_tokens": mean(tokens) if tokens else None,
        "median_completion_tokens": median(tokens) if tokens else None,
        "cost_per_success_completion_tokens": sum(tokens) / len(correct) if correct else None,
        "mean_success_completion_tokens": mean([row_tokens(r) for r in correct]) if correct else None,
        "source_answer_repeated": sum(int(bool(r.get("source_answer_repeated"))) for r in rows),
    }


def filter_rows(rows: list[dict[str, Any]], **matches: str) -> list[dict[str, Any]]:
    out = rows
    for key, value in matches.items():
        out = [r for r in out if r.get(key) == value]
    return out


def paired_deltas(rows: list[dict[str, Any]], left: str, right: str) -> dict[str, Any]:
    by_case: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_case[row["case_id"]][row["prompt_variant"]] = row
    pairs = [(v[left], v[right]) for v in by_case.values() if left in v and right in v]
    left_wins = sum(int(row_ok(a) and not row_ok(b)) for a, b in pairs)
    right_wins = sum(int(row_ok(b) and not row_ok(a)) for a, b in pairs)
    both_correct = sum(int(row_ok(a) and row_ok(b)) for a, b in pairs)
    both_wrong = sum(int((not row_ok(a)) and (not row_ok(b))) for a, b in pairs)
    token_delta = [row_tokens(a) - row_tokens(b) for a, b in pairs]
    return {
        "left": left,
        "right": right,
        "pairs": len(pairs),
        "left_wins": left_wins,
        "right_wins": right_wins,
        "both_correct": both_correct,
        "both_wrong": both_wrong,
        "discordant_pairs": left_wins + right_wins,
        "exact_sign_p_two_sided": exact_sign_p_two_sided(left_wins, right_wins),
        "exact_sign_p_left_better_one_sided": exact_sign_p_left_better(left_wins, right_wins),
        "interpretation": interpret_pair(left, right, len(pairs), left_wins, right_wins),
        "accuracy_delta_left_minus_right": (left_wins - right_wins) / len(pairs) if pairs else None,
        "mean_completion_token_delta_left_minus_right": mean(token_delta) if token_delta else None,
        "median_completion_token_delta_left_minus_right": median(token_delta) if token_delta else None,
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


def interpret_pair(left: str, right: str, pairs: int, left_wins: int, right_wins: int) -> str:
    if pairs == 0:
        return "no_pairs"
    if left_wins + right_wins == 0:
        return "no_accuracy_difference_observed"
    p_left = exact_sign_p_left_better(left_wins, right_wins)
    if left_wins > right_wins and p_left is not None and p_left < 0.05:
        return f"{left}_significantly_better_than_{right}_one_sided_p_lt_0.05"
    if left_wins > right_wins:
        return f"{left}_trend_better_than_{right}_not_significant"
    if right_wins > left_wins:
        return f"{right}_trend_better_than_{left}"
    return "tied_discordant_wins"


def model_summary(model_key: str) -> dict[str, Any]:
    rows, source = load_result_rows(model_key)
    by_variant = {variant: summarize_rows(filter_rows(rows, prompt_variant=variant)) for variant in VARIANTS}
    by_case_type = {k: summarize_rows([r for r in rows if r.get("case_type") == k]) for k in sorted({r.get("case_type") for r in rows})}
    by_family_variant: dict[str, dict[str, Any]] = {}
    for family in sorted({r.get("family") for r in rows}):
        fam_rows = [r for r in rows if r.get("family") == family]
        by_family_variant[family] = {variant: summarize_rows(filter_rows(fam_rows, prompt_variant=variant)) for variant in VARIANTS}
    invalid_wrong = [r for r in rows if "invalid_answer_wrong" in str(r.get("case_type"))]
    invalid_correct = [r for r in rows if "invalid_answer_correct" in str(r.get("case_type"))]
    valid_controls = [r for r in rows if str(r.get("case_type")).endswith("_valid")]
    return {
        "model_key": model_key,
        "source": source,
        "rows": len(rows),
        "cases": len({r.get("case_id") for r in rows}),
        "complete_variant_sets": sum(1 for _case, vals in group_by_case(rows).items() if all(v in vals for v in VARIANTS)),
        "by_variant": by_variant,
        "by_case_type": by_case_type,
        "by_family_variant": by_family_variant,
        "invalid_answer_wrong_by_variant": {variant: summarize_rows(filter_rows(invalid_wrong, prompt_variant=variant)) for variant in VARIANTS},
        "invalid_answer_correct_by_variant": {variant: summarize_rows(filter_rows(invalid_correct, prompt_variant=variant)) for variant in VARIANTS},
        "valid_control_by_variant": {variant: summarize_rows(filter_rows(valid_controls, prompt_variant=variant)) for variant in VARIANTS},
        "paired_deltas": [
            paired_deltas(rows, "hidden_localized_warning", "prefix_continue"),
            paired_deltas(rows, "hidden_localized_warning", "hidden_generic_warning"),
            paired_deltas(rows, "hidden_localized_warning", "random_matched_warning"),
            paired_deltas(rows, "hidden_localized_warning", "baseline_regenerate"),
            paired_deltas(rows, "oracle_manual_span", "hidden_localized_warning"),
        ],
        "leakage_counts": {
            "manual_span_used_as_non_oracle_warning_rows": sum(
                int(
                    bool(r.get("manual_error_span_offline"))
                    and r.get("manual_error_span_offline") in {r.get("localized_span_in_prompt"), r.get("random_span_in_prompt")}
                    and r.get("prompt_variant") != "oracle_manual_span"
                )
                for r in rows
            ),
            "manual_target_used_as_hidden_trigger_rows": sum(int(bool(r.get("hidden_trigger_is_manual_target_offline"))) for r in rows),
            "gold_answer_in_prompt_rows": sum(int(bool(r.get("gold_answer_in_prompt"))) for r in rows),
            "manual_label_in_prompt_rows": sum(int(bool(r.get("manual_label_in_prompt"))) for r in rows),
        },
        "status_counts": {
            f"{variant}|final={final_marker}|hit_max={hit_max}": count
            for (variant, final_marker, hit_max), count in sorted(
                Counter((r.get("prompt_variant"), bool(r.get("final_marker_found")), bool(r.get("hit_max_new_tokens"))) for r in rows).items(),
                key=lambda kv: str(kv[0]),
            )
        },
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
        "# E167 Hidden-Derived Repair Stage Analysis / E167 hidden-derived 修复阶段分析",
        "",
        f"Created / 创建时间：`{result['created_at']}`.",
        "",
        "Scope / 范围：strict `auto_boundary_only` E167. Non-oracle localized spans come from E166 hidden-triggered automatic sentence boundaries, not manual error-span endpoints. / 严格自动边界 E167；非 oracle localized span 来自 E166 hidden 触发的自动句子边界，不来自人工错步末尾。",
        "",
    ]
    for model_key, info in result["by_model"].items():
        lines.extend(
            [
                f"## {model_key}",
                "",
                f"- Source / 来源：`{info['source']}`.",
                f"- Rows / 行数：{info['rows']}; cases / case 数：{info['cases']}; complete variant sets / 六变体齐全 case：{info['complete_variant_sets']}.",
                f"- Leakage counts / 泄漏计数：`{info['leakage_counts']}`.",
                "",
                "| variant | n | correct | acc | total completion tokens | cost/success | mean tokens | hit-max | final marker |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for variant in VARIANTS:
            row = info["by_variant"][variant]
            lines.append(
                f"| {variant} | {row['n']} | {row['correct']} | {fmt(row['accuracy'])} | "
                f"{row['total_completion_tokens']} | {fmt(row['cost_per_success_completion_tokens'])} | "
                f"{fmt(row['mean_completion_tokens'])} | {row['hit_max_new_tokens']} | {row['final_marker_found']} |"
            )
        lines.extend(["", "### Invalid-Answer-Wrong Repair / 答案错样本修复", ""])
        lines.append("| variant | n | correct | acc | cost/success |")
        lines.append("|---|---:|---:|---:|---:|")
        for variant in VARIANTS:
            row = info["invalid_answer_wrong_by_variant"][variant]
            lines.append(f"| {variant} | {row['n']} | {row['correct']} | {fmt(row['accuracy'])} | {fmt(row['cost_per_success_completion_tokens'])} |")
        lines.extend(["", "### Paired Deltas / 配对差异", ""])
        lines.append("| left vs right | pairs | left wins | right wins | one-sided p(left better) | two-sided p | acc delta | mean token delta | interpretation |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|")
        for d in info["paired_deltas"]:
            lines.append(
                f"| {d['left']} - {d['right']} | {d['pairs']} | {d['left_wins']} | {d['right_wins']} | "
                f"{fmt(d['exact_sign_p_left_better_one_sided'])} | {fmt(d['exact_sign_p_two_sided'])} | "
                f"{fmt(d['accuracy_delta_left_minus_right'])} | {fmt(d['mean_completion_token_delta_left_minus_right'])} | {d['interpretation']} |"
            )
        lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    result = {
        "experiment": "E167_hidden_derived_repair_stage_analysis",
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
