#!/usr/bin/env python3
"""Audit E162 localized failures and completion-token cost per success."""
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
OUT_JSON = PROJECT / "reports/E162_LOCALIZED_FAILURE_AND_COST_AUDIT_20260501.json"
OUT_MD = PROJECT / "reports/E162_LOCALIZED_FAILURE_AND_COST_AUDIT_20260501.md"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def adjusted_correct(row: dict[str, Any]) -> tuple[bool, str]:
    if row.get("manual_final_correct"):
        return True, "raw_correct"
    got = numeric_value(row.get("extracted_final"))
    gold = numeric_value(row.get("gold_answer"))
    if row.get("family") == "unit_roundtrip" and got is not None and gold is not None and abs(got - gold) < 1e-9:
        return True, "unit_numeric_equivalent_false_negative"
    return False, "raw_wrong"


def row_brief(row: dict[str, Any], model_key: str) -> dict[str, Any]:
    ok, reason = adjusted_correct(row)
    return {
        "model_key": model_key,
        "case_id": row.get("case_id"),
        "task_id": row.get("task_id"),
        "family": row.get("family"),
        "case_type": row.get("case_type"),
        "gold_answer": row.get("gold_answer"),
        "extracted_final": row.get("extracted_final"),
        "raw_manual_final_correct": bool(row.get("manual_final_correct")),
        "adjusted_final_correct": ok,
        "adjusted_reason": reason,
        "generated_tokens": int(row.get("generated_tokens") or 0),
        "hit_max_new_tokens": bool(row.get("hit_max_new_tokens")),
        "manual_error_span": row.get("manual_error_span_offline"),
        "localized_span": row.get("localized_span_in_prompt"),
        "source_model_key": row.get("source_model_key"),
        "source_extracted_final": row.get("source_extracted_final"),
        "completion_excerpt": (row.get("completion") or "")[:900],
    }


def cost_summary(rows: list[dict[str, Any]], *, adjusted: bool) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for variant in VARIANTS:
        rec = [r for r in rows if r.get("prompt_variant") == variant]
        tokens = [int(r.get("generated_tokens") or 0) for r in rec]
        if adjusted:
            correct = [r for r in rec if adjusted_correct(r)[0]]
        else:
            correct = [r for r in rec if r.get("manual_final_correct")]
        success_tokens = [int(r.get("generated_tokens") or 0) for r in correct]
        out[variant] = {
            "n": len(rec),
            "correct": len(correct),
            "accuracy": (len(correct) / len(rec)) if rec else 0.0,
            "total_completion_tokens": sum(tokens),
            "cost_per_success_completion_tokens": (sum(tokens) / len(correct)) if correct else None,
            "mean_success_completion_tokens": mean(success_tokens) if success_tokens else None,
            "median_success_completion_tokens": median(success_tokens) if success_tokens else None,
            "hit_max_new_tokens": sum(bool(r.get("hit_max_new_tokens")) for r in rec),
        }
    return out


def main() -> None:
    by_model: dict[str, Any] = {}
    true_failures: list[dict[str, Any]] = []
    false_negative_rows: list[dict[str, Any]] = []
    for model_key in MODELS:
        path = PROJECT / f"logs/e162_repair_{model_key}_highmax_checkpoint_20260501.jsonl"
        rows = load_jsonl(path)
        localized_raw_failures = [
            r for r in rows if r.get("prompt_variant") == "localized_error_prompt" and not r.get("manual_final_correct")
        ]
        localized_true_failures = []
        localized_false_negatives = []
        for row in localized_raw_failures:
            ok, reason = adjusted_correct(row)
            brief = row_brief(row, model_key)
            if ok:
                localized_false_negatives.append(brief)
                false_negative_rows.append(brief)
            else:
                localized_true_failures.append(brief)
                true_failures.append(brief)
        by_model[model_key] = {
            "rows": len(rows),
            "raw_cost": cost_summary(rows, adjusted=False),
            "adjusted_cost": cost_summary(rows, adjusted=True),
            "localized_raw_failures": [row_brief(r, model_key) for r in localized_raw_failures],
            "localized_false_negative_rows": localized_false_negatives,
            "localized_true_failures": localized_true_failures,
        }

    result = {
        "experiment": "E162_localized_failure_and_completion_cost_audit",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "models": MODELS,
        "adjustment_rule": "For unit_roundtrip only, finals such as '100 m' and '3 km' are counted correct when their numeric value equals the scalar gold answer. This fixes answer-format false negatives; it does not change multilingual semantic failures.",
        "by_model": by_model,
        "localized_true_failures": true_failures,
        "localized_false_negative_rows": false_negative_rows,
        "hidden_followup_recommendation": {
            "needed": bool(true_failures),
            "target_rows": [
                {
                    "model_key": r["model_key"],
                    "case_id": r["case_id"],
                    "task_id": r["task_id"],
                    "family": r["family"],
                    "localized_span": r["localized_span"],
                }
                for r in true_failures
            ],
            "reason": "After format adjustment, all true localized failures are romanized multilingual semantic cases. Hidden-state replay should compare problem end, wrong-prefix end, localized-span prompt end, and completion end against oracle-repaired counterparts.",
        },
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# E162 Localized Failure and Completion Cost Audit / E162 localized 失败与 completion 成本审计",
        "",
        f"Date / 日期：{result['created_at']}",
        "",
        "## Adjustment / 修正口径",
        "",
        "- Prompt tokens are treated as nearly free because prompts are automatically generated. / 按用户要求，prompt tokens 基本不计入主要成本。",
        "- Primary cost is completion tokens. / 主要成本口径是 completion tokens。",
        "- Unit-format false negatives are corrected when numeric value matches gold. / unit 题如果 `100 m` 对 gold `100`、`3 km` 对 gold `3`，按数值等价修正为正确。",
        "",
        "## Cost Per Success / 单次成功 completion 成本",
        "",
    ]
    for model_key in MODELS:
        lines.append(f"### {model_key}")
        lines.append("")
        lines.append("| variant | raw correct | adjusted correct | total completion tokens | raw cost/success | adjusted cost/success | hit-max |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        raw = by_model[model_key]["raw_cost"]
        adj = by_model[model_key]["adjusted_cost"]
        for variant in VARIANTS:
            r = raw[variant]
            a = adj[variant]
            lines.append(
                "| {variant} | {rc}/{n} | {ac}/{n} | {tok} | {raw_cps} | {adj_cps} | {hit} |".format(
                    variant=variant,
                    rc=r["correct"],
                    ac=a["correct"],
                    n=r["n"],
                    tok=r["total_completion_tokens"],
                    raw_cps=f"{r['cost_per_success_completion_tokens']:.1f}"
                    if r["cost_per_success_completion_tokens"] is not None
                    else "NA",
                    adj_cps=f"{a['cost_per_success_completion_tokens']:.1f}"
                    if a["cost_per_success_completion_tokens"] is not None
                    else "NA",
                    hit=r["hit_max_new_tokens"],
                )
            )
        lines.append("")
    lines.extend(
        [
            "## Localized Failures / localized 失败",
            "",
            f"- Raw localized failures / 原始 localized 失败：{sum(len(by_model[m]['localized_raw_failures']) for m in MODELS)}.",
            f"- Unit-format false negatives / unit 格式假阴性：{len(false_negative_rows)}.",
            f"- Adjusted true localized failures / 修正后真实 localized 失败：{len(true_failures)}.",
            "",
        ]
    )
    for row in true_failures:
        lines.append(
            f"- `{row['model_key']}` `{row['task_id']}`: final `{row['extracted_final']}` vs gold `{row['gold_answer']}`, "
            f"span `{row['localized_span']}`, tokens {row['generated_tokens']}."
        )
    lines.extend(
        [
            "",
            "## Hidden Follow-Up / hidden 后续",
            "",
            "- Hidden deep-dive is not needed for unit-format rows; they are scoring false negatives. / unit 格式行不需要 hidden 深挖，它们是判分假阴性。",
            "- Hidden deep-dive is useful for the remaining romanized multilingual semantic failures. / 剩余罗马化多语言语义失败值得做 hidden 深挖。",
            "- Compare true-error localized prompts against oracle prompts at problem end, wrong-prefix end, localized prompt end, and completion end. / 比较 true-error localized 与 oracle，在题目末尾、错误前缀末尾、localized prompt 末尾、completion 末尾的 hidden 状态。",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": [str(OUT_JSON), str(OUT_MD)], "true_failures": len(true_failures)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
