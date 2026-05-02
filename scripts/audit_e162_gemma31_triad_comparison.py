#!/usr/bin/env python3
"""Compare Gemma31 localized/oracle/random E162 behavior after pinyin exclusion."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
PINYIN_PATTERN = re.compile(r"\b(zhi duo wei|zhengshu|shu chu|qiu zhengshu)\b", re.IGNORECASE)
OUT_JSON = PROJECT / "reports/E162_GEMMA31_LOCALIZED_ORACLE_RANDOM_TRIAD_20260501.json"
OUT_MD = PROJECT / "reports/E162_GEMMA31_LOCALIZED_ORACLE_RANDOM_TRIAD_20260501.md"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def is_pinyin_case(row: dict[str, Any]) -> bool:
    text = " ".join(
        str(row.get(key, ""))
        for key in ["problem", "prefix_text", "manual_error_span_offline", "localized_span_in_prompt", "prompt_content"]
    )
    return bool(PINYIN_PATTERN.search(text))


def numeric_value(text: Any) -> float | None:
    match = re.search(r"-?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?", str(text or "").replace(",", ""))
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


def brief(row: dict[str, Any]) -> str:
    return (row.get("completion") or "").strip().replace("\n", " ")[:1300]


def variant_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tokens = [int(row.get("generated_tokens") or 0) for row in rows]
    return {
        "n": len(rows),
        "correct": sum(adjusted_correct(row) for row in rows),
        "mean_tokens": mean(tokens),
        "median_tokens": median(tokens),
        "min_tokens": min(tokens),
        "max_tokens": max(tokens),
        "p90_tokens": sorted(tokens)[int(0.9 * (len(tokens) - 1))],
    }


def build_result() -> dict[str, Any]:
    rows = load_jsonl(PROJECT / "logs/e162_repair_gemma4_31b_it_highmax_checkpoint_20260501.jsonl")
    by_case: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        if not is_pinyin_case(row):
            by_case[row["case_id"]][row["prompt_variant"]] = row
    triples: list[dict[str, Any]] = []
    for case_id, by_variant in sorted(by_case.items()):
        needed = ["localized_error_prompt", "oracle_error_prompt", "random_location_prompt"]
        if not all(key in by_variant for key in needed):
            continue
        localized = by_variant["localized_error_prompt"]
        oracle = by_variant["oracle_error_prompt"]
        random = by_variant["random_location_prompt"]
        triples.append(
            {
                "case_id": case_id,
                "task_id": localized["task_id"],
                "family": localized["family"],
                "localized": {
                    "correct": adjusted_correct(localized),
                    "final": localized.get("extracted_final"),
                    "tokens": int(localized.get("generated_tokens") or 0),
                    "span": localized.get("localized_span_in_prompt"),
                    "completion_start": brief(localized),
                },
                "oracle": {
                    "correct": adjusted_correct(oracle),
                    "final": oracle.get("extracted_final"),
                    "tokens": int(oracle.get("generated_tokens") or 0),
                    "span": oracle.get("localized_span_in_prompt"),
                    "completion_start": brief(oracle),
                },
                "random": {
                    "correct": adjusted_correct(random),
                    "final": random.get("extracted_final"),
                    "tokens": int(random.get("generated_tokens") or 0),
                    "span": random.get("random_span_in_prompt"),
                    "completion_start": brief(random),
                },
            }
        )
    rows_by_variant = {
        "localized": [triple["localized"] for triple in triples],
        "oracle": [triple["oracle"] for triple in triples],
        "random": [triple["random"] for triple in triples],
    }
    # Reformat for stats helper.
    stat_rows = {
        key: [
            {"generated_tokens": row["tokens"], "manual_final_correct": row["correct"], "family": ""}
            for row in vals
        ]
        for key, vals in rows_by_variant.items()
    }
    deltas = {
        "localized_minus_oracle": [triple["localized"]["tokens"] - triple["oracle"]["tokens"] for triple in triples],
        "localized_minus_random": [triple["localized"]["tokens"] - triple["random"]["tokens"] for triple in triples],
        "oracle_minus_random": [triple["oracle"]["tokens"] - triple["random"]["tokens"] for triple in triples],
    }
    by_family: dict[str, Any] = {}
    fam_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for triple in triples:
        fam_groups[triple["family"]].append(triple)
    for family, vals in sorted(fam_groups.items()):
        by_family[family] = {
            "n": len(vals),
            "localized_mean_tokens": mean(v["localized"]["tokens"] for v in vals),
            "oracle_mean_tokens": mean(v["oracle"]["tokens"] for v in vals),
            "random_mean_tokens": mean(v["random"]["tokens"] for v in vals),
        }
    examples = [
        "e159_probability_conditioning_03",
        "e159_code_boundary_zero_04",
        "e159_proof_invalid_lemma_04",
        "e159_algebra_sign_symmetry_03",
        "e159_unit_roundtrip_02",
    ]
    return {
        "experiment": "E162_gemma31_localized_oracle_random_triad",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "n_triples": len(triples),
        "variant_stats": {key: variant_stats(vals) for key, vals in stat_rows.items()},
        "deltas": {
            key: {
                "mean": mean(vals),
                "median": median(vals),
                "min": min(vals),
                "max": max(vals),
                "abs_le_25": sum(abs(x) <= 25 for x in vals),
                "positive": sum(x > 0 for x in vals),
                "negative": sum(x < 0 for x in vals),
            }
            for key, vals in deltas.items()
        },
        "by_family": by_family,
        "representative_examples": [triple for triple in triples if triple["task_id"] in examples],
        "top_random_cheaper_than_oracle": sorted(
            triples,
            key=lambda triple: triple["oracle"]["tokens"] - triple["random"]["tokens"],
            reverse=True,
        )[:10],
        "interpretation": {
            "too_easy_for_differential_localization": True,
            "reason": "After pinyin removal, localized, oracle, and random all solve 38/38. Random often points at broad problem text, which triggers Gemma31 to reread and recompute. This makes the current bank too easy for measuring localized-vs-random differential advantage.",
            "next_step": "Build harder multi-family cases with broad random spans that are genuinely uninformative, plus longer/denser traces where restarting from the problem is costly.",
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    lines = [
        "# E162 Gemma31 Localized / Oracle / Random Triad Audit",
        "",
        f"Date / 日期：{result['created_at']}",
        "",
        "## Core Finding / 核心结论",
        "",
        "- After removing pinyin/romanized cases, Gemma31 gets localized, oracle, and random all correct on 38/38 cases. / 去掉拼音/罗马化样本后，Gemma31 在 localized、oracle、random 三组都是 38/38。",
        "- Oracle and random have very close completion length: oracle mean 207.4, random mean 202.1. / oracle 和 random 的 completion 长度非常接近：oracle 均值 207.4，random 均值 202.1。",
        "- This does indicate the current non-pinyin bank is too easy for measuring localized-vs-random differential advantage. / 这说明当前去拼音题库对衡量 localized 相对 random 的差分优势来说过于简单。",
        "- It does not mean localized is useless; it means random broad-problem reread is a strong baseline on these short cases. / 这不说明 localized 没用，而说明在这些短题上，random 宽泛题干重读是强基线。",
        "",
        "## Token Statistics / token 统计",
        "",
        "| variant | correct | mean tokens | median tokens | min | max | p90 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for key in ["localized", "oracle", "random"]:
        stat = result["variant_stats"][key]
        lines.append(
            f"| `{key}` | {stat['correct']}/{stat['n']} | {stat['mean_tokens']:.1f} | {stat['median_tokens']:.1f} | "
            f"{stat['min_tokens']} | {stat['max_tokens']} | {stat['p90_tokens']} |"
        )
    lines.extend(
        [
            "",
            "Deltas / 差值：",
            "",
            f"- localized - oracle: mean {result['deltas']['localized_minus_oracle']['mean']:.1f}, median {result['deltas']['localized_minus_oracle']['median']:.1f}.",
            f"- localized - random: mean {result['deltas']['localized_minus_random']['mean']:.1f}, median {result['deltas']['localized_minus_random']['median']:.1f}.",
            f"- oracle - random: mean {result['deltas']['oracle_minus_random']['mean']:.1f}, median {result['deltas']['oracle_minus_random']['median']:.1f}.",
            "",
            "## Why Localized Is Longer / 为什么 localized 更长",
            "",
            "Localized usually explains the exact bad step before recomputing; oracle gives a direct correction; random often says the broad problem span is fine and simply recomputes from the problem. / localized 通常先解释具体错步为什么错，再重算；oracle 直接给修正；random 往往说宽泛题干片段没错，然后从题目重算。",
            "",
            "Representative examples / 代表样本：",
            "",
        ]
    )
    for example in result["representative_examples"]:
        lines.extend(
            [
                f"### `{example['task_id']}` / `{example['family']}`",
                "",
                f"- localized: {example['localized']['tokens']} tokens, span `{example['localized']['span']}`. Excerpt: {example['localized']['completion_start']}",
                f"- oracle: {example['oracle']['tokens']} tokens, span `{example['oracle']['span']}`. Excerpt: {example['oracle']['completion_start']}",
                f"- random: {example['random']['tokens']} tokens, span `{example['random']['span']}`. Excerpt: {example['random']['completion_start']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Next Step / 下一步",
            "",
            "- Proceed to harder multi-family tasks. / 应进入更复杂的 multi-family 题目。",
            "- Random controls must avoid broad problem restatements. / random control 必须避免宽泛题干重述。",
            "- Harder cases should make full restart expensive: long tables, long code, multi-hop geometry, proof validity, graph definitions with hidden constraints, and multi-condition aggregation. / 更难样本应让从头重算代价高：长表格、长代码、多跳几何、证明有效性、带隐含条件的图定义、多条件聚合。",
            "- Use budget curves such as 128/256/512/1024 completion tokens. / 使用 128/256/512/1024 completion-token 预算曲线。",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = build_result()
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(result)
    print(json.dumps({"wrote": [str(OUT_JSON), str(OUT_MD)]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
