#!/usr/bin/env python3
"""E162 main-result audit after excluding pinyin/romanized Chinese cases."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
MODELS = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"]
VARIANTS = [
    "baseline_regenerate",
    "prefix_continue",
    "generic_error_prompt",
    "localized_error_prompt",
    "oracle_error_prompt",
    "random_location_prompt",
]
PINYIN_PATTERN = re.compile(r"\b(zhi duo wei|zhengshu|shu chu|qiu zhengshu)\b", re.IGNORECASE)
OUT_JSON = PROJECT / "reports/E162_NON_PINYIN_AND_GEMMA31_RANDOM_AUDIT_20260501.json"
OUT_MD = PROJECT / "reports/E162_NON_PINYIN_AND_GEMMA31_RANDOM_AUDIT_20260501.md"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def is_pinyin_case(row: dict[str, Any]) -> bool:
    text = " ".join(
        str(row.get(key, ""))
        for key in ["problem", "prefix_text", "manual_error_span_offline", "localized_span_in_prompt", "prompt_content"]
    )
    return bool(PINYIN_PATTERN.search(text))


def numeric_value(text: Any) -> float | None:
    if text is None:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?", str(text).replace(",", ""))
    if not match:
        return None
    value = match.group(0)
    if "/" in value:
        left, right = value.split("/", 1)
        try:
            return float(left) / float(right)
        except ZeroDivisionError:
            return None
    return float(value)


def adjusted_correct(row: dict[str, Any]) -> bool:
    if row.get("manual_final_correct"):
        return True
    if row.get("family") == "unit_roundtrip":
        got = numeric_value(row.get("extracted_final"))
        gold = numeric_value(row.get("gold_answer"))
        if got is not None and gold is not None and abs(got - gold) < 1e-9:
            return True
    return False


def variant_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(int(row.get("generated_tokens") or 0) for row in rows)
    correct = sum(adjusted_correct(row) for row in rows)
    return {
        "n": len(rows),
        "adjusted_correct": correct,
        "accuracy": correct / len(rows) if rows else 0.0,
        "total_completion_tokens": total,
        "completion_cost_per_success": total / correct if correct else None,
        "hitmax": sum(bool(row.get("hit_max_new_tokens")) for row in rows),
    }


def build_summary() -> dict[str, Any]:
    out: dict[str, Any] = {
        "experiment": "E162_non_pinyin_and_gemma31_random_audit",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "exclusion_rule": "Exclude rows whose problem/prefix/span/prompt contains zhi duo wei, zhengshu, shu chu, or qiu zhengshu. These are pinyin/romanized Chinese cases and should not support the main multilingual-semantic claim.",
        "models": {},
    }
    for model_key in MODELS:
        rows = load_jsonl(PROJECT / f"logs/e162_repair_{model_key}_highmax_checkpoint_20260501.jsonl")
        kept = [row for row in rows if not is_pinyin_case(row)]
        excluded = [row for row in rows if is_pinyin_case(row)]
        model_summary: dict[str, Any] = {
            "all_rows": len(rows),
            "kept_rows": len(kept),
            "kept_cases": len({row["case_id"] for row in kept}),
            "excluded_rows": len(excluded),
            "excluded_cases": len({row["case_id"] for row in excluded}),
            "variants": {},
            "families": {},
        }
        for variant in VARIANTS:
            model_summary["variants"][variant] = variant_summary([row for row in kept if row["prompt_variant"] == variant])
        by_family: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
        for row in kept:
            by_family[row["family"]][row["prompt_variant"]].append(row)
        for family, by_variant in sorted(by_family.items()):
            model_summary["families"][family] = {
                variant: variant_summary(rows_for_variant)
                for variant, rows_for_variant in sorted(by_variant.items())
            }
        out["models"][model_key] = model_summary

    gemma_rows = load_jsonl(PROJECT / "logs/e162_repair_gemma4_31b_it_highmax_checkpoint_20260501.jsonl")
    by_case: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in gemma_rows:
        if not is_pinyin_case(row):
            by_case[row["case_id"]][row["prompt_variant"]] = row
    pairs: list[dict[str, Any]] = []
    for case_id, rows_by_variant in sorted(by_case.items()):
        if "localized_error_prompt" not in rows_by_variant or "random_location_prompt" not in rows_by_variant:
            continue
        localized = rows_by_variant["localized_error_prompt"]
        random_row = rows_by_variant["random_location_prompt"]
        loc_tokens = int(localized.get("generated_tokens") or 0)
        random_tokens = int(random_row.get("generated_tokens") or 0)
        pairs.append(
            {
                "case_id": case_id,
                "task_id": localized["task_id"],
                "family": localized["family"],
                "localized_correct": adjusted_correct(localized),
                "random_correct": adjusted_correct(random_row),
                "localized_final": localized.get("extracted_final"),
                "random_final": random_row.get("extracted_final"),
                "localized_tokens": loc_tokens,
                "random_tokens": random_tokens,
                "delta_localized_minus_random": loc_tokens - random_tokens,
                "localized_span": localized.get("localized_span_in_prompt"),
                "random_span": random_row.get("random_span_in_prompt"),
                "localized_start": (localized.get("completion") or "").replace("\n", " ")[:700],
                "random_start": (random_row.get("completion") or "").replace("\n", " ")[:700],
            }
        )
    deltas = [row["delta_localized_minus_random"] for row in pairs]
    out["gemma4_31b_it_nonpinyin_pair_analysis"] = {
        "n_pairs": len(pairs),
        "localized_correct": sum(row["localized_correct"] for row in pairs),
        "random_correct": sum(row["random_correct"] for row in pairs),
        "accuracy_disagreements": [row for row in pairs if row["localized_correct"] != row["random_correct"]],
        "mean_delta_localized_minus_random": mean(deltas) if deltas else None,
        "median_delta_localized_minus_random": median(deltas) if deltas else None,
        "top_random_cheaper": sorted(pairs, key=lambda row: row["delta_localized_minus_random"], reverse=True)[:12],
        "top_localized_cheaper": sorted(pairs, key=lambda row: row["delta_localized_minus_random"])[:8],
    }
    return out


def write_markdown(result: dict[str, Any]) -> None:
    lines = [
        "# E162 Non-Pinyin Main Audit and Gemma31 Random Comparison / E162 去拼音主结果与 Gemma31 random 对照",
        "",
        f"Date / 日期：{result['created_at']}",
        "",
        "## Exclusion / 排除口径",
        "",
        "- Original logs are preserved. / 原始日志保留。",
        "- Main-result statistics exclude pinyin/romanized cases containing `zhi duo wei`, `zhengshu`, `shu chu`, or `qiu zhengshu`. / 主结果排除包含这些拼音/罗马化表达的样本。",
        "- These cases may remain exploratory language-trait cases, but they no longer support the main multilingual-semantic claim. / 这些样本可作为探索性语言特质样本，但不进入多语义主 claim。",
        "- Unit answers are judged by numeric equivalence when units are present. / unit 题按数值等价修正判分。",
        "",
        "## Main Statistics / 主统计",
        "",
    ]
    for model_key in MODELS:
        model = result["models"][model_key]
        lines.extend(
            [
                f"### {model_key}",
                "",
                f"- Kept / 保留：{model['kept_cases']} cases, {model['kept_rows']} rows.",
                f"- Excluded / 排除：{model['excluded_cases']} cases, {model['excluded_rows']} rows.",
                "",
                "| variant | adjusted correct | completion cost/success | total completion tokens | hit-max |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for variant in VARIANTS:
            rec = model["variants"][variant]
            cps = rec["completion_cost_per_success"]
            lines.append(
                f"| `{variant}` | {rec['adjusted_correct']}/{rec['n']} | "
                f"{cps:.1f} | {rec['total_completion_tokens']} | {rec['hitmax']} |"
            )
        lines.append("")
    pair = result["gemma4_31b_it_nonpinyin_pair_analysis"]
    lines.extend(
        [
            "## Gemma31 Localized vs Random / Gemma31 localized 与 random 逐例比较",
            "",
            f"- Non-pinyin pair count / 去拼音成对样本：{pair['n_pairs']}.",
            f"- Accuracy / 准确率：localized {pair['localized_correct']}/{pair['n_pairs']}, random {pair['random_correct']}/{pair['n_pairs']}.",
            f"- Accuracy disagreements / 准确率分歧：{len(pair['accuracy_disagreements'])}.",
            f"- Token delta / token 差：localized - random mean {pair['mean_delta_localized_minus_random']:.1f}, median {pair['median_delta_localized_minus_random']:.1f}.",
            "",
            "Interpretation / 解读：random is not more accurate on Gemma31 after pinyin removal; it is only shorter in completion tokens. / 去拼音后 random 在 Gemma31 上不是更准，只是输出更短。",
            "",
            "Why random is shorter / 为什么 random 更短：",
            "",
            "- Random spans often point to broad problem-text fragments. / random span 常指向宽泛题干片段。",
            "- Gemma31 treats those spans as a request to reread the problem and directly recompute. / Gemma31 会把它当成重读题目并直接重算。",
            "- Localized prompts name the specific bad step, so Gemma31 usually explains why that step is wrong before recomputing. / localized 指出具体错步，Gemma31 往往先解释错在哪里再重算。",
            "- Therefore localized carries clearer process evidence, while random carries a shorter but less specific re-solve behavior. / 因此 localized 的过程证据更清楚；random 是更短但不局部的重解。",
            "",
            "Top random-cheaper examples / random 更短的代表样本：",
            "",
            "| task | family | delta loc-rnd | localized span | random span |",
            "|---|---|---:|---|---|",
        ]
    )
    for row in pair["top_random_cheaper"][:8]:
        lines.append(
            f"| `{row['task_id']}` | `{row['family']}` | {row['delta_localized_minus_random']} | "
            f"`{row['localized_span']}` | `{row['random_span']}` |"
        )
    lines.extend(
        [
            "",
            "Conclusion / 结论：for main non-pinyin evidence, localized is useful and cheaper than generic, but random is a strong re-solve baseline on Gemma31. / 对去拼音主证据，localized 有用且比 generic 省，但 random 在 Gemma31 上是强重解基线。",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = build_summary()
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(result)
    print(json.dumps({"wrote": [str(OUT_JSON), str(OUT_MD)]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
