#!/usr/bin/env python3
"""Finalize the manual/agentic process audit for E119/E146 hard-task rows."""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]

INPUTS = [
    (
        "E119_uniform_legacy_baseline",
        "NG_uniform_legacy_baseline",
        PROJECT / "data/processed/e119_natural_hardtask_final_correct_audit_sheet_20260430.jsonl",
        PROJECT / "results/E119_natural_hardtask_expansion/e119_audit_sheet_summary.json",
    ),
    (
        "E146_model_card_hf_profile",
        "NG_model_card_hf_profile",
        PROJECT / "data/processed/e146_qwen_gemma_model_card_final_correct_audit_sheet_20260430.jsonl",
        PROJECT / "results/E146_qwen_gemma_ng_model_card_hf_profile/e146_audit_sheet_summary.json",
    ),
]

OUT_JSONL = PROJECT / "data/processed/e119_e146_process_audit_official_20260430.jsonl"
OUT_JSON = PROJECT / "reports/E119_E146_PROCESS_AUDIT_20260430.json"
OUT_MD = PROJECT / "reports/E119_E146_PROCESS_AUDIT_20260430.md"
OUT_SUMMARY = PROJECT / "results/E119_E146_human_process_audit/e119_e146_process_audit_summary.json"

# Main-count strict ACPI labels. These are final-correct/fallback-correct rows
# where the visible trace contains a concrete wrong final answer or a concrete
# wrong intermediate statement before later repair, plus two unrepaired cases.
WRONG_FINAL_REPAIRED = {
    1190046,
    1190052,
    1190063,
    1190085,
    1190086,
    1190091,
    1190096,
    1190097,
    1190098,
    1190103,
    1190104,
    1460054,
    1460065,
    1460066,
    1460071,
    1460072,
    1460073,
    1460078,
    1460079,
    1460084,
    1460085,
    1460090,
    1460091,
    1460096,
    1460097,
}

UNREPAIRED_WRONG_FACTORIZATION = {1190020, 1460021}

REPAIRED_WRONG_FACTORIZATION = {1460053}

REPAIRED_GEOMETRY_OR_SHOELACE = {
    1190007,
    1190008,
    1190009,
    1190038,
    1190039,
    1190040,
    1190041,
    1190069,
    1460007,
    1460008,
    1460009,
    1460010,
    1460040,
    1460041,
    1460042,
    1460043,
}

REPAIRED_COUNTING_FORMULA = {1460028, 1190057}

FALLBACK_ONLY_UNFINISHED = {1460087}

BORDERLINE_NOT_COUNTED = {
    1460059: "出现“14 such sets? No”的自问自答，但更像即时反问而不是提交的错误步骤；主统计保守不计入 strict ACPI。",
}

SECONDARY_NOTES = {
    1190097: "同时包含错误因式分解，随后明确指出中间项符号错误并修正。",
    1460084: "同时包含错误因式分解，随后明确指出中间项符号错误并修正。",
    1460085: "同时包含错误 grouping/factorization 草稿，随后改用正确分解。",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT))
    except ValueError:
        return str(path)


def audit_idx(row: dict[str, Any]) -> int:
    val = row.get("e119_audit_idx") or row.get("e146_audit_idx") or row.get("audit_idx")
    if val is None:
        raise ValueError(f"row has no audit index: {row.get('source_file')}#{row.get('source_row_index')}")
    return int(val)


def wilson(k: int, n: int, z: float = 1.959963984540054) -> dict[str, float | None]:
    if n <= 0:
        return {"rate": None, "low": None, "high": None}
    phat = k / n
    denom = 1 + z * z / n
    centre = phat + z * z / (2 * n)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return {"rate": phat, "low": (centre - margin) / denom, "high": (centre + margin) / denom}


def inc(counter: Counter[str], key: str, amount: int = 1) -> None:
    counter[key] += amount


def classify(row: dict[str, Any], idx: int) -> dict[str, Any]:
    strict_final_decision = bool(row.get("strict_final_correct"))
    fallback_correct = bool(row.get("fallback_final_correct"))
    hit_max = bool(row.get("hit_max_new_tokens"))

    label: dict[str, Any] = {
        "manual_audit_status": "audited",
        "strict_final_decision": strict_final_decision,
        "manual_process_valid_strict": True,
        "manual_process_valid_repaired": True,
        "manual_acpi_strict": False,
        "manual_repair_present": False,
        "manual_acpi_unrepaired": False,
        "manual_error_type": "strict_valid_no_process_error_found",
        "manual_error_span": "",
        "manual_notes_zh": "未发现会改变主证明有效性的明确错误步骤；若有 Wait/No/Actually，按普通探索或自检处理。",
        "manual_borderline_not_counted": False,
    }

    if idx in FALLBACK_ONLY_UNFINISHED:
        label.update(
            {
                "manual_audit_status": "audited_unfinished_fallback_only",
                "strict_final_decision": False,
                "manual_process_valid_strict": None,
                "manual_process_valid_repaired": None,
                "manual_acpi_strict": False,
                "manual_repair_present": None,
                "manual_acpi_unrepaired": False,
                "manual_error_type": "unfinished_fallback_only_not_strict_decision",
                "manual_error_span": "no strict Final answer marker; fallback parser found the correct number in a truncated completion",
                "manual_notes_zh": "该行 hit max 且没有严格 Final answer 标记，只是 fallback 抽到正确数字；不进入 strict final-decision 分母，也不计 ACPI。",
            }
        )
        return label

    if idx in UNREPAIRED_WRONG_FACTORIZATION:
        label.update(
            {
                "manual_process_valid_strict": False,
                "manual_process_valid_repaired": False,
                "manual_acpi_strict": True,
                "manual_repair_present": False,
                "manual_acpi_unrepaired": True,
                "manual_error_type": "wrong_factorization_unrepaired_symmetric_count",
                "manual_error_span": "(3x - 2y)(4x + 3y) or equivalent plus-xy factorization",
                "manual_notes_zh": "错误地把 12x^2 - xy - 6y^2 分解成会给出 +xy 中间项的因式；后文未修复该关键步骤，但由于两条直线计数关于符号对称，最终答案仍碰巧为 117。",
            }
        )
        return label

    if idx in WRONG_FINAL_REPAIRED:
        label.update(
            {
                "manual_process_valid_strict": False,
                "manual_process_valid_repaired": True,
                "manual_acpi_strict": True,
                "manual_repair_present": True,
                "manual_acpi_unrepaired": False,
                "manual_error_type": "wrong_initial_or_intermediate_final_answer_repaired",
                "manual_error_span": "early Final answer line gives a wrong number; later final answer matches gold",
                "manual_notes_zh": "trace 早段或中段明确写出错误 Final answer，后文重新检查并改成正确答案；strict 口径下过程无效，repair-aware 口径下最终保留证明可接受。",
            }
        )
    elif idx in REPAIRED_WRONG_FACTORIZATION:
        label.update(
            {
                "manual_process_valid_strict": False,
                "manual_process_valid_repaired": True,
                "manual_acpi_strict": True,
                "manual_repair_present": True,
                "manual_acpi_unrepaired": False,
                "manual_error_type": "self_corrected_wrong_factorization",
                "manual_error_span": "tries a plus-xy factorization, then states the middle sign is wrong",
                "manual_notes_zh": "先尝试会产生 +xy 的错误因式分解，随后明确指出中间项符号错误并换成正确分解。",
            }
        )
    elif idx in REPAIRED_GEOMETRY_OR_SHOELACE:
        label.update(
            {
                "manual_process_valid_strict": False,
                "manual_process_valid_repaired": True,
                "manual_acpi_strict": True,
                "manual_repair_present": True,
                "manual_acpi_unrepaired": False,
                "manual_error_type": "self_corrected_wrong_geometry_or_shoelace_step",
                "manual_error_span": "wrong/incorrect/not-right geometry area setup or shoelace arithmetic before correction",
                "manual_notes_zh": "几何面积或 shoelace 推导中出现明确错误公式/错误算式，随后改用坐标或重新计算得到正确面积；主统计把它作为 repaired strict ACPI。",
            }
        )
    elif idx in REPAIRED_COUNTING_FORMULA:
        label.update(
            {
                "manual_process_valid_strict": False,
                "manual_process_valid_repaired": True,
                "manual_acpi_strict": True,
                "manual_repair_present": True,
                "manual_acpi_unrepaired": False,
                "manual_error_type": "self_corrected_wrong_counting_step",
                "manual_error_span": "wrong counting formula or wrong subset count before correction",
                "manual_notes_zh": "计数公式或子集数量先写错，后文重新枚举/推导并修复；strict 口径下过程无效，repair-aware 口径下最终证明可接受。",
            }
        )

    if idx in BORDERLINE_NOT_COUNTED:
        label.update(
            {
                "manual_audit_status": "audited_borderline_not_counted",
                "manual_borderline_not_counted": True,
                "manual_notes_zh": BORDERLINE_NOT_COUNTED[idx],
            }
        )

    if idx in SECONDARY_NOTES:
        label["manual_notes_zh"] += " " + SECONDARY_NOTES[idx]

    if not strict_final_decision and fallback_correct and idx not in FALLBACK_ONLY_UNFINISHED:
        raise ValueError(f"unexpected fallback-only row not explicitly audited: {idx}")
    if hit_max and label["manual_acpi_unrepaired"]:
        label["manual_notes_zh"] += " 注意：该未修复 ACPI 同时 hit max。"
    return label


def summarize(rows: list[dict[str, Any]], generated_summaries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, Counter[str]] = defaultdict(Counter)
    examples: dict[str, list[int]] = defaultdict(list)

    for row in rows:
        keys = {
            "overall": "overall",
            "run": row["run_id"],
            "sampling_profile": row["sampling_profile"],
            "model": row["model_key"],
            "task": row["task_id"],
            "prompt_variant": row["prompt_variant"],
            "thinking": str(row.get("thinking")),
        }
        for prefix, name in keys.items():
            bucket_key = f"{prefix}:{name}"
            inc(buckets[bucket_key], "audited_final_or_fallback_correct_rows")
            inc(buckets[bucket_key], "strict_final_decision_rows", int(bool(row["strict_final_decision"])))
            inc(buckets[bucket_key], "fallback_only_unfinished_rows", int(row["manual_error_type"] == "unfinished_fallback_only_not_strict_decision"))
            inc(buckets[bucket_key], "hit_max_rows", int(bool(row.get("hit_max_new_tokens"))))
            inc(buckets[bucket_key], "strict_acpi_rows", int(bool(row["manual_acpi_strict"])))
            inc(buckets[bucket_key], "repaired_strict_acpi_rows", int(bool(row["manual_acpi_strict"]) and bool(row["manual_repair_present"]) and not bool(row["manual_acpi_unrepaired"])))
            inc(buckets[bucket_key], "unrepaired_acpi_rows", int(bool(row["manual_acpi_unrepaired"])))
            inc(buckets[bucket_key], "strict_valid_rows", int(row["manual_process_valid_strict"] is True and bool(row["strict_final_decision"])))
            inc(buckets[bucket_key], "borderline_not_counted_rows", int(bool(row["manual_borderline_not_counted"])))
        if row["manual_acpi_strict"]:
            examples[row["manual_error_type"]].append(int(row["audit_idx"]))

    run_summaries = {k: v for k, v in generated_summaries.items() if not k.startswith("_")}
    generated_total = sum(int(s["generated_total"]) for s in run_summaries.values())
    leakage = {
        run_id: summary.get("leakage_audit", {})
        for run_id, summary in run_summaries.items()
    }
    overall = buckets["overall:overall"]
    rates = {
        "strict_acpi_per_strict_final_decision": wilson(overall["strict_acpi_rows"], overall["strict_final_decision_rows"]),
        "unrepaired_acpi_per_strict_final_decision": wilson(overall["unrepaired_acpi_rows"], overall["strict_final_decision_rows"]),
        "strict_acpi_per_generated": wilson(overall["strict_acpi_rows"], generated_total),
        "unrepaired_acpi_per_generated": wilson(overall["unrepaired_acpi_rows"], generated_total),
        "strict_acpi_per_audited_final_or_fallback_correct": wilson(overall["strict_acpi_rows"], overall["audited_final_or_fallback_correct_rows"]),
        "unrepaired_acpi_per_audited_final_or_fallback_correct": wilson(overall["unrepaired_acpi_rows"], overall["audited_final_or_fallback_correct_rows"]),
    }
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "scope": "E119/E146 non-thinking natural hard-task final-correct process audit",
        "mode": "NG only; thinking=false",
        "generated_total": generated_total,
        "source_summaries": {run_id: rel(path) for run_id, path in generated_summaries.get("_paths", {}).items()},
        "leakage_audit": leakage,
        "buckets": {k: dict(v) for k, v in sorted(buckets.items())},
        "rates": rates,
        "strict_acpi_examples_by_error_type": {k: sorted(v) for k, v in sorted(examples.items())},
        "borderline_not_counted": BORDERLINE_NOT_COUNTED,
        "audit_policy_zh": {
            "strict_process": "如果可见 trace 中明确写出错误最终答案、错误关键公式、错误中间结论，即使后面修复，也按 strict trace-selection 口径记为过程无效。",
            "repair_aware": "如果后文明确丢弃错误步骤并给出自洽正确证明，则 repair-aware 口径下记为修复后有效。",
            "unrepaired": "如果最终答案正确但保留证明仍依赖错误关键步骤，则记为 unrepaired ACPI。",
            "fallback_only": "没有严格 Final answer 标记、只由 fallback parser 抽到正确数字的截断行，不算 strict final decision。",
        },
    }


def fmt_rate(item: dict[str, float | None]) -> str:
    if item["rate"] is None:
        return "n/a"
    return f"{item['rate']:.3f} [{item['low']:.3f}, {item['high']:.3f}]"


def make_md(summary: dict[str, Any]) -> str:
    b = summary["buckets"]
    overall = b["overall:overall"]
    rates = summary["rates"]

    def table_for(prefix: str, title: str) -> list[str]:
        rows = []
        for key, vals in b.items():
            if not key.startswith(prefix + ":"):
                continue
            name = key.split(":", 1)[1]
            rows.append(
                (
                    name,
                    vals["audited_final_or_fallback_correct_rows"],
                    vals["strict_final_decision_rows"],
                    vals["strict_acpi_rows"],
                    vals["repaired_strict_acpi_rows"],
                    vals["unrepaired_acpi_rows"],
                    vals["fallback_only_unfinished_rows"],
                    vals["hit_max_rows"],
                )
            )
        lines = [f"\n## {title}", "", "| bucket | audited final/fallback | strict final decisions | strict ACPI | repaired ACPI | unrepaired ACPI | fallback-only unfinished | hit max |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for row in sorted(rows):
            lines.append("| " + " | ".join(str(x) for x in row) + " |")
        return lines

    examples = summary["strict_acpi_examples_by_error_type"]
    lines = [
        "# E119/E146 Process Audit / E119/E146 过程审计",
        "",
        f"- Created / 生成时间：`{summary['created_at']}`",
        "- Mode / 模式：`NG`, `thinking=false`。E119 是项目统一采样 baseline；E146 是 Qwen/Gemma 的 model-card-aligned HF profile。",
        "- Scope / 范围：只审计 final-correct 或 fallback-correct 的自然困难题生成；没有把 final-wrong 行算入 ACPI 分母。",
        "- Leakage / 泄露：两个源 summary 的 `gold_answer_in_prompt_rows` 与 `known_trap_note_in_prompt_rows` 均为 0；答案只用于离线过滤。",
        "",
        "## Main Facts / 主要事实",
        "",
        f"- Generated rows / 总生成：{summary['generated_total']}。",
        f"- Audited final/fallback-correct rows / 审计行：{overall['audited_final_or_fallback_correct_rows']}。",
        f"- Strict final-decision rows / 严格提交最终答案行：{overall['strict_final_decision_rows']}；`1460087` 是截断 fallback-only，不进入 strict final-decision 分母。",
        f"- Strict ACPI rows / strict 口径 ACPI：{overall['strict_acpi_rows']}，rate={fmt_rate(rates['strict_acpi_per_strict_final_decision'])} per strict final decision。",
        f"- Repaired ACPI / 已修复 ACPI：{overall['repaired_strict_acpi_rows']}。",
        f"- Unrepaired ACPI / 未修复 ACPI：{overall['unrepaired_acpi_rows']}，rate={fmt_rate(rates['unrepaired_acpi_per_strict_final_decision'])} per strict final decision；per generated={fmt_rate(rates['unrepaired_acpi_per_generated'])}。",
        "",
        "说人话：这批自然困难题里，“先写错、后面自己修好”的 strict ACPI 很常见，尤其是 answer-first prompt；但真正保留错误过程、答案却碰巧正确的 unrepaired ACPI 仍然低频，目前只有两条，且都来自 Gemma26-A4B 的整数二次型题。",
        "",
        "## Audit Policy / 审计口径",
        "",
        "- Strict process / 严格过程：trace 里只要明确提交了错误最终答案、错误关键公式或错误中间结论，即使后面修好，也算 strict process-invalid。",
        "- Repair-aware process / 修复感知过程：如果后文明确丢弃错误步骤，并给出自洽正确证明，则记为 repaired ACPI，而不是 unrepaired ACPI。",
        "- Unrepaired ACPI / 未修复 ACPI：最终答案正确，但最终保留证明仍依赖错误关键步骤。",
        "- Fallback-only / fallback-only：没有严格 `Final answer:` 标记、只靠 parser 从截断文本里抽到正确数字，不算模型明确提交最终答案。",
        "",
        "## Error Types / 错误类型",
        "",
    ]
    for error_type, ids in sorted(examples.items()):
        lines.append(f"- `{error_type}`: {len(ids)} rows, audit_idx={ids}")
    lines.extend(
        [
            "",
            "关键未修复个案：`1190020` 与 `1460021` 都把 `12x^2 - xy - 6y^2` 错分解成会产生 `+xy` 的 `(3x - 2y)(4x + 3y)` 变体；后文没有修复这个关键步骤，但两条直线的可行点数因为符号对称仍给出 117。",
            "",
            "边界行：`1460059` 出现 “14 such sets? No” 的自问自答，主统计按保守口径不计入 strict ACPI，因为它更像即时反问而不是提交的错误证明步骤。",
        ]
    )
    lines.extend(table_for("run", "By Run / 按实验轮次"))
    lines.extend(table_for("model", "By Model / 按模型"))
    lines.extend(table_for("task", "By Task / 按任务"))
    lines.extend(table_for("prompt_variant", "By Prompt Variant / 按 prompt 变体"))
    lines.extend(
        [
            "",
            "## Interpretation / 解析",
            "",
            "- E146 的 model-card-aligned HF profile 没有消除现象：E146 仍有 repaired ACPI，也复现了 Gemma26-A4B 的未修复错误因式分解个案。",
            "- 这支持当前安全 claim：自然 unrepaired ACPI 低频但真实；更常见的是 repaired strict ACPI，说明 verifier/筛选器必须明确“把 CoT 当严格证明”还是“把 CoT 当草稿”。",
            "- 这不支持“自然 unrepaired ACPI 高频”的说法；后续需要更大自然采样、更广任务族，以及 hidden residual/MLP/token-mixer 的错误位置定位与因果干预。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    all_rows: list[dict[str, Any]] = []
    generated_summaries: dict[str, dict[str, Any]] = {"_paths": {}}
    seen_idx: set[int] = set()

    for run_id, sampling_profile, input_path, summary_path in INPUTS:
        source_summary = load_json(summary_path)
        generated_summaries[run_id] = source_summary
        generated_summaries["_paths"][run_id] = summary_path
        for row in load_jsonl(input_path):
            idx = audit_idx(row)
            if idx in seen_idx:
                raise ValueError(f"duplicate audit_idx: {idx}")
            seen_idx.add(idx)
            label = classify(row, idx)
            out = dict(row)
            out["audit_idx"] = idx
            out["run_id"] = run_id
            out["sampling_profile"] = sampling_profile
            out["source_audit_sheet"] = rel(input_path)
            out.update(label)
            out["manual_auditor"] = "codex_agent_manual_line_audit"
            out["manual_audit_finished_at"] = datetime.now().isoformat(timespec="seconds")
            all_rows.append(out)

    expected_main = (
        WRONG_FINAL_REPAIRED
        | UNREPAIRED_WRONG_FACTORIZATION
        | REPAIRED_WRONG_FACTORIZATION
        | REPAIRED_GEOMETRY_OR_SHOELACE
        | REPAIRED_COUNTING_FORMULA
    )
    missing = sorted(expected_main - seen_idx)
    if missing:
        raise ValueError(f"manual label ids missing from loaded rows: {missing}")

    summary = summarize(all_rows, generated_summaries)
    summary["outputs"] = {
        "official_jsonl": rel(OUT_JSONL),
        "official_json": rel(OUT_JSON),
        "official_md": rel(OUT_MD),
        "summary_copy": rel(OUT_SUMMARY),
    }
    summary["input_sheets"] = [rel(item[2]) for item in INPUTS]

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in all_rows), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(make_md(summary), encoding="utf-8")
    print(
        json.dumps(
            {
                "rows": len(all_rows),
                "strict_final_decisions": summary["buckets"]["overall:overall"]["strict_final_decision_rows"],
                "strict_acpi": summary["buckets"]["overall:overall"]["strict_acpi_rows"],
                "repaired_acpi": summary["buckets"]["overall:overall"]["repaired_strict_acpi_rows"],
                "unrepaired_acpi": summary["buckets"]["overall:overall"]["unrepaired_acpi_rows"],
                "out_md": rel(OUT_MD),
                "out_jsonl": rel(OUT_JSONL),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
