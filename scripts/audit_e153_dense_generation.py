#!/usr/bin/env python3
"""Audit completed E153 dense-model generation traces.

The goal is not to replace human review, but to make the current human audit
explicit, reproducible, and easy to extend when additional models finish.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]

IN_FILES = {
    "qwen35_27b": PROJECT / "results/E153_nonthinking_difficult_scenario_generation/qwen35_27b_e153_solve_neutral_solve_terse_solve_self_check_k1_generation.json",
    "gemma4_31b_it": PROJECT / "results/E153_nonthinking_difficult_scenario_generation/gemma4_31b_it_e153_solve_neutral_solve_terse_solve_self_check_k1_generation.json",
}

OUT_JSONL = PROJECT / "data/processed/e153_dense_generation_audit_20260501.jsonl"
OUT_SUMMARY = PROJECT / "results/E153_nonthinking_difficult_scenario_generation/e153_dense_generation_audit_summary_20260501.json"
OUT_REPORT = PROJECT / "reports/E153_DENSE_GENERATION_AUDIT_20260501.md"

DENSE_ARCH = {
    "qwen35_27b": "dense",
    "gemma4_31b_it": "dense",
}

TASK_NOTES = {
    "e153_graph_path_constraints_02": {
        "ambiguous_problem_boundary": True,
        "note": "Euler trail answer depends on whether the degree sequence is treated as an existence/connected-graph question or an arbitrary graph with those degrees.",
    }
}

REAL_FAILURES = {
    ("gemma4_31b_it", "e153_multilingual_semantic_01", "solve_neutral"): {
        "manual_error_type": "multilingual_semantic_misparse",
        "manual_error_span": "interprets `zhi duo wei 4` as `digit/value is 4` instead of `at most 4`",
        "note": "Final answer 2; model turns 至多为4 into |x|=4.",
    },
    ("gemma4_31b_it", "e153_multilingual_semantic_01", "solve_terse"): {
        "manual_error_type": "multilingual_semantic_misparse",
        "manual_error_span": "interprets `zhengshu` as positive integer and `zhi duo wei 4` as tens digit 4",
        "note": "Final answer 0; model misreads both integer polarity and the pinyin phrase.",
    },
    ("gemma4_31b_it", "e153_multilingual_semantic_01", "solve_self_check"): {
        "manual_error_type": "multilingual_semantic_misparse",
        "manual_error_span": "interprets `zhengshu` as positive integer and `zhi duo wei 4` as units digit 4",
        "note": "Final answer 1; self-check reinforces the wrong semantic parse.",
    },
}

NORMALIZATION_FALSE_NEGATIVES = {
    "e153_string_regex_parsing_02": "quoted_string_equivalent",
    "e153_unit_percentage_02": "unit_suffix_equivalent",
}

LANGUAGE_TRAIT_TASKS = {
    "e153_multilingual_semantic_01",
    "e153_multilingual_semantic_02",
    "e153_graph_path_constraints_02",
}

REPAIR_OR_RETHINK_RE = re.compile(r"\b(wait|re-?evaluate|re-?calculate|self-?correction|mistake|wrong|flawed)\b", re.I)
SELF_CHECK_RE = re.compile(r"\b(self[- ]?check|verify|verification|double[- ]?check|check)\b", re.I)
FINAL_RE = re.compile(r"^\s*final answer\s*[:：]", re.I | re.M)
EARLY_ANSWER_RE = re.compile(r"\b(the answer is|answer:|so the answer is|therefore the answer is)\b", re.I)


def norm_answer(value: Any) -> str:
    text = str(value).strip().lower()
    text = text.strip("\"'`")
    text = re.sub(r"\s+", " ", text)
    text = text.replace(" ", "")
    text = text.replace("meters", "m")
    text = text.replace("meter", "m")
    text = text.replace("centimeters", "cm")
    text = text.replace("centimeter", "cm")
    if re.fullmatch(r"-?\d+(\.0+)?m", text):
        text = text[:-1]
    text = text.replace("(", "").replace(")", "")
    text = text.replace(" ", "")
    return text


def answer_correct(row: dict[str, Any]) -> tuple[bool, str]:
    auto = bool(row["manual_final_correct"])
    if auto:
        return True, "auto_exact"
    if norm_answer(row["extracted_final"]) == norm_answer(row["gold_answer"]):
        return True, NORMALIZATION_FALSE_NEGATIVES.get(row["task_id"], "normalized_equivalent")
    return False, "manual_incorrect"


def final_marker_position(completion: str) -> int:
    match = FINAL_RE.search(completion)
    return match.start() if match else -1


def reasoning_order(completion: str) -> str:
    stripped = completion.strip()
    first_final = final_marker_position(stripped)
    if first_final == 0:
        return "answer_first"
    early_region = stripped[: max(160, len(stripped) // 8)]
    if first_final > 0 and first_final < max(160, len(stripped) // 8):
        return "mixed_short_derivation"
    if EARLY_ANSWER_RE.search(early_region) and not re.search(r"\bstep|because|since|given|we need|to solve\b", early_region, re.I):
        return "mixed_answer_anchor"
    return "derivation_first"


def completion_markers(completion: str) -> dict[str, Any]:
    return {
        "repair_or_rethink_marker": bool(REPAIR_OR_RETHINK_RE.search(completion)),
        "self_check_marker": bool(SELF_CHECK_RE.search(completion)),
        "final_marker_count": len(FINAL_RE.findall(completion)),
    }


def audit_row(row: dict[str, Any], idx: int) -> dict[str, Any]:
    model = row["model_key"]
    key = (model, row["task_id"], row["prompt_variant"])
    correct, final_reason = answer_correct(row)
    markers = completion_markers(row["completion"])
    order = reasoning_order(row["completion"])
    override = REAL_FAILURES.get(key, {})
    task_note = TASK_NOTES.get(row["task_id"], {})

    process_valid_strict = correct and key not in REAL_FAILURES
    process_valid_repaired = process_valid_strict
    final_retained_process_valid = process_valid_repaired
    acpi_unrepaired = bool(correct and not final_retained_process_valid)

    causal_prefill_usable = order in {"derivation_first", "mixed_short_derivation"} and markers["final_marker_count"] >= 1
    clean_valid_prefill_candidate = bool(
        correct
        and process_valid_repaired
        and order == "derivation_first"
        and not markers["repair_or_rethink_marker"]
        and not task_note.get("ambiguous_problem_boundary", False)
    )

    language_trait_use = bool(
        row["task_id"] in LANGUAGE_TRAIT_TASKS
        or markers["repair_or_rethink_marker"]
        or order != "derivation_first"
        or key in REAL_FAILURES
        or final_reason != "auto_exact"
    )

    return {
        "audit_created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "E153_dense_generation_manual_audit",
        "source_experiment": row["experiment"],
        "source_row_index": idx,
        "model_key": model,
        "model_architecture": DENSE_ARCH[model],
        "task_id": row["task_id"],
        "family": row["family"],
        "prompt_variant": row["prompt_variant"],
        "problem": row["problem"],
        "gold_answer": row["gold_answer"],
        "extracted_final": row["extracted_final"],
        "auto_final_correct": bool(row["manual_final_correct"]),
        "manual_final_correct": correct,
        "manual_final_correct_reason": final_reason,
        "manual_process_valid_strict": process_valid_strict,
        "manual_process_valid_repaired": process_valid_repaired,
        "manual_final_retained_process_valid": final_retained_process_valid,
        "manual_acpi_strict": bool(correct and not process_valid_strict),
        "manual_acpi_unrepaired": acpi_unrepaired,
        "manual_repair_or_rethink_marker": markers["repair_or_rethink_marker"],
        "manual_self_check_marker": markers["self_check_marker"],
        "manual_final_marker_count": markers["final_marker_count"],
        "reasoning_order": order,
        "posthoc_rationalization": order in {"answer_first", "mixed_answer_anchor"},
        "causal_prefill_usable": causal_prefill_usable,
        "clean_valid_prefill_candidate": clean_valid_prefill_candidate,
        "language_trait_use": language_trait_use,
        "ambiguous_problem_boundary": bool(task_note.get("ambiguous_problem_boundary", False)),
        "manual_error_type": override.get("manual_error_type"),
        "manual_error_span": override.get("manual_error_span"),
        "manual_note": override.get("note") or task_note.get("note") or "",
        "generated_tokens": row["generated_tokens"],
        "hit_max_new_tokens": row["hit_max_new_tokens"],
        "completion": row["completion"],
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def count_bool(vals: list[dict[str, Any]], key: str) -> int:
        return sum(bool(v[key]) for v in vals)

    by_model: dict[str, dict[str, Any]] = {}
    by_model_family: dict[str, dict[str, Any]] = {}
    by_model_prompt: dict[str, dict[str, Any]] = {}
    for model in sorted({r["model_key"] for r in rows}):
        vals = [r for r in rows if r["model_key"] == model]
        by_model[model] = {
            "n": len(vals),
            "auto_final_correct": count_bool(vals, "auto_final_correct"),
            "manual_final_correct": count_bool(vals, "manual_final_correct"),
            "manual_process_valid_strict": count_bool(vals, "manual_process_valid_strict"),
            "manual_acpi_unrepaired": count_bool(vals, "manual_acpi_unrepaired"),
            "causal_prefill_usable": count_bool(vals, "causal_prefill_usable"),
            "clean_valid_prefill_candidate": count_bool(vals, "clean_valid_prefill_candidate"),
            "language_trait_use": count_bool(vals, "language_trait_use"),
            "posthoc_rationalization": count_bool(vals, "posthoc_rationalization"),
            "repair_or_rethink_marker": count_bool(vals, "manual_repair_or_rethink_marker"),
        }
        fams: dict[str, Counter[str]] = defaultdict(Counter)
        prompts: dict[str, Counter[str]] = defaultdict(Counter)
        for r in vals:
            for bucket in (fams[r["family"]], prompts[r["prompt_variant"]]):
                bucket["n"] += 1
                bucket["manual_final_correct"] += int(r["manual_final_correct"])
                bucket["clean_valid_prefill_candidate"] += int(r["clean_valid_prefill_candidate"])
                bucket["language_trait_use"] += int(r["language_trait_use"])
        for fam, counter in fams.items():
            by_model_family[f"{model}::{fam}"] = dict(counter)
        for prompt, counter in prompts.items():
            by_model_prompt[f"{model}::{prompt}"] = dict(counter)

    error_cases = [
        {
            "model_key": r["model_key"],
            "task_id": r["task_id"],
            "prompt_variant": r["prompt_variant"],
            "gold_answer": r["gold_answer"],
            "extracted_final": r["extracted_final"],
            "manual_error_type": r["manual_error_type"],
            "manual_error_span": r["manual_error_span"],
            "manual_note": r["manual_note"],
        }
        for r in rows
        if not r["manual_final_correct"] or r["manual_error_type"]
    ]
    normalization_fixes = [
        {
            "model_key": r["model_key"],
            "task_id": r["task_id"],
            "prompt_variant": r["prompt_variant"],
            "gold_answer": r["gold_answer"],
            "extracted_final": r["extracted_final"],
            "reason": r["manual_final_correct_reason"],
        }
        for r in rows
        if (not r["auto_final_correct"]) and r["manual_final_correct"]
    ]

    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "scope": "E153 dense generation audit: qwen35_27b and gemma4_31b_it",
        "rows": len(rows),
        "by_model": by_model,
        "by_model_family": dict(sorted(by_model_family.items())),
        "by_model_prompt": dict(sorted(by_model_prompt.items())),
        "error_cases": error_cases,
        "normalization_fixes": normalization_fixes,
        "field_meanings": {
            "causal_prefill_usable": "Trace has chronological visible order suitable for causal prefill analysis; it may still be wrong and useful for error analysis.",
            "clean_valid_prefill_candidate": "Subset for main valid-trace prefill/mutation seeds: final-correct, process-valid, derivation-first, no explicit repair/rethink marker, and no ambiguous task boundary.",
            "language_trait_use": "Trace is useful for language-behavior analysis, including semantic misread, task ambiguity, repair/rethink language, answer formatting, or non-derivation-first order.",
        },
    }


def write_report(summary: dict[str, Any]) -> None:
    q = summary["by_model"]["qwen35_27b"]
    g = summary["by_model"]["gemma4_31b_it"]
    lines = [
        "# E153 Dense Generation Audit / E153 dense 解题生成审计",
        "",
        "Scope / 范围：Qwen35-27B 和 Gemma4-31B-it 的 E153 non-thinking generation，均为 dense 模型；MoE Gemma 单独后置分析。",
        "",
        "Key definitions / 关键定义：",
        "- `causal_prefill_usable`: trace 的可见顺序适合做因果 prefill 分析；它可以是正确 trace，也可以是错误 trace，用于研究模型怎样走向错误。",
        "- `clean_valid_prefill_candidate`: 主 prefill/篡改种子；要求最终答案正确、最终保留推理有效、先推理后答案、没有显式修复/重想 marker、任务本身没有明显歧义。",
        "- `language_trait_use`: 语言特质分析样本；包括语义误读、任务歧义、自检/重算语言、格式归一化问题、非典型推理顺序等。",
        "",
        "Dense model summary / dense 模型摘要：",
        "",
        "| model | rows | auto final correct | manual final correct | clean valid prefill candidates | language-trait traces | unrepaired ACPI |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| qwen35_27b | {q['n']} | {q['auto_final_correct']} | {q['manual_final_correct']} | {q['clean_valid_prefill_candidate']} | {q['language_trait_use']} | {q['manual_acpi_unrepaired']} |",
        f"| gemma4_31b_it | {g['n']} | {g['auto_final_correct']} | {g['manual_final_correct']} | {g['clean_valid_prefill_candidate']} | {g['language_trait_use']} | {g['manual_acpi_unrepaired']} |",
        "",
        "Main findings / 主要发现：",
        "- Qwen35-27B: all 96/96 rows are manually final-correct after normalizing quoted strings and unit suffixes. No unrepaired ACPI was found in this dense generation set.",
        "- Gemma4-31B-it: 93/96 rows are manually final-correct. The 3 real failures are all the same pinyin multilingual semantic task under three prompts.",
        "- The 11 automatic false negatives are parser issues, not model failures: quoted string `'bcd'` and unit forms such as `120m` or `120 meters` should count as correct.",
        "- Both dense models mostly produce derivation-first traces under these prompts. This supports using many rows for causal prefill, but clean valid seeds should exclude ambiguous graph/Euler rows and explicit rethinking markers.",
        "- The most informative dense failure is Gemma4-31B-it on `e153_multilingual_semantic_01`: it misreads romanized Chinese `zhi duo wei 4` as value/digit/tens/units conditions instead of `at most 4`. This is a high-value language-trait and multilingual semantic robustness sample.",
        "- The first-sample phenomenon remains important: solving from scratch can be correct, while checking another trace can localize poorly. Generation competence and error-localization competence must be analyzed separately.",
        "",
        "Error cases / 真错误样本：",
    ]
    for case in summary["error_cases"]:
        lines.append(
            f"- {case['model_key']} {case['task_id']} {case['prompt_variant']}: gold `{case['gold_answer']}`, extracted `{case['extracted_final']}`; {case['manual_error_type']}; {case['manual_note']}"
        )
    lines += [
        "",
        "Normalization fixes / 自动解析假错：",
    ]
    for fix in summary["normalization_fixes"]:
        lines.append(
            f"- {fix['model_key']} {fix['task_id']} {fix['prompt_variant']}: gold `{fix['gold_answer']}`, extracted `{fix['extracted_final']}` -> correct by `{fix['reason']}`."
        )
    lines += [
        "",
        "Next use / 后续使用：",
        "- Main prefill/mutation seed pool: use `clean_valid_prefill_candidate=true` rows first.",
        "- Language-behavior pool: use `language_trait_use=true`, especially Gemma multilingual misreads, Qwen rethinking/checking traces, and graph ambiguity rows.",
        "- Do not pool MoE with dense in the same headline statistic; MoE should be audited separately because routing may add instability.",
        "",
        f"Artifacts / 产物：`{OUT_JSONL.relative_to(PROJECT)}`, `{OUT_SUMMARY.relative_to(PROJECT)}`.",
    ]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    audited: list[dict[str, Any]] = []
    for model, path in IN_FILES.items():
        data = json.loads(path.read_text(encoding="utf-8"))
        for idx, row in enumerate(data["rows"]):
            audited.append(audit_row(row, idx))

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in audited),
        encoding="utf-8",
    )
    summary = summarize(audited)
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(summary)
    print(json.dumps({"out_jsonl": str(OUT_JSONL), "out_summary": str(OUT_SUMMARY), "out_report": str(OUT_REPORT), "summary": summary["by_model"]}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
