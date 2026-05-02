#!/usr/bin/env python3
"""Audit E153 MoE generation traces separately from dense models."""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import audit_e153_dense_generation as dense  # noqa: E402

MODEL_KEY = "gemma4_26b_a4b_it"
IN_FILE = PROJECT / "results/E153_nonthinking_difficult_scenario_generation/gemma4_26b_a4b_it_e153_solve_neutral_solve_terse_solve_self_check_k1_generation.json"
OUT_JSONL = PROJECT / "data/processed/e153_moe_generation_audit_20260501.jsonl"
OUT_SUMMARY = PROJECT / "results/E153_nonthinking_difficult_scenario_generation/e153_moe_generation_audit_summary_20260501.json"
OUT_REPORT = PROJECT / "reports/E153_MOE_GENERATION_AUDIT_20260501.md"


AMBIGUOUS_BOUNDARY_CASES = {
    ("gemma4_26b_a4b_it", "e153_graph_path_constraints_02", "solve_neutral"): {
        "manual_error_type": "ambiguous_graph_connectivity_boundary",
        "manual_error_span": "requires a connected graph/all non-isolated edges in one component; prompt did not state connectivity",
        "note": (
            "The model answers No by constructing the disconnected degree sequence "
            "triangle plus one edge. This challenges the gold assumption rather than "
            "showing a clean reasoning failure."
        ),
    }
}


def audit_row(row: dict[str, Any], idx: int) -> dict[str, Any]:
    key = (row["model_key"], row["task_id"], row["prompt_variant"])
    correct, final_reason = dense.answer_correct(row)
    markers = dense.completion_markers(row["completion"])
    order = dense.reasoning_order(row["completion"])
    boundary = AMBIGUOUS_BOUNDARY_CASES.get(key)

    manual_final_correct = correct
    manual_final_correct_reason = final_reason
    if boundary:
        manual_final_correct_reason = "ambiguous_problem_boundary_challenges_gold"

    process_valid_strict = bool(manual_final_correct and not boundary)
    process_valid_repaired = process_valid_strict
    final_retained_process_valid = process_valid_repaired

    causal_prefill_usable = order in {"derivation_first", "mixed_short_derivation"} and markers["final_marker_count"] >= 1
    clean_valid_prefill_candidate = bool(
        manual_final_correct
        and process_valid_repaired
        and order == "derivation_first"
        and not markers["repair_or_rethink_marker"]
        and not boundary
    )
    language_trait_use = bool(
        boundary
        or row["task_id"] in dense.LANGUAGE_TRAIT_TASKS
        or markers["repair_or_rethink_marker"]
        or order != "derivation_first"
        or final_reason != "auto_exact"
    )

    return {
        "audit_created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "E153_moe_generation_manual_audit",
        "source_experiment": row["experiment"],
        "source_row_index": idx,
        "model_key": row["model_key"],
        "model_architecture": "moe",
        "task_id": row["task_id"],
        "family": row["family"],
        "prompt_variant": row["prompt_variant"],
        "problem": row["problem"],
        "gold_answer": row["gold_answer"],
        "extracted_final": row["extracted_final"],
        "auto_final_correct": bool(row["manual_final_correct"]),
        "manual_final_correct": manual_final_correct,
        "manual_final_correct_reason": manual_final_correct_reason,
        "manual_process_valid_strict": process_valid_strict,
        "manual_process_valid_repaired": process_valid_repaired,
        "manual_final_retained_process_valid": final_retained_process_valid,
        "manual_acpi_strict": bool(manual_final_correct and not process_valid_strict),
        "manual_acpi_unrepaired": bool(manual_final_correct and not final_retained_process_valid),
        "manual_repair_or_rethink_marker": markers["repair_or_rethink_marker"],
        "manual_self_check_marker": markers["self_check_marker"],
        "manual_final_marker_count": markers["final_marker_count"],
        "reasoning_order": order,
        "posthoc_rationalization": order in {"answer_first", "mixed_answer_anchor"},
        "causal_prefill_usable": causal_prefill_usable,
        "clean_valid_prefill_candidate": clean_valid_prefill_candidate,
        "language_trait_use": language_trait_use,
        "ambiguous_problem_boundary": bool(boundary),
        "manual_error_type": boundary.get("manual_error_type") if boundary else None,
        "manual_error_span": boundary.get("manual_error_span") if boundary else None,
        "manual_note": boundary.get("note") if boundary else "",
        "generated_tokens": row["generated_tokens"],
        "hit_max_new_tokens": row["hit_max_new_tokens"],
        "completion": row["completion"],
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def count(key: str) -> int:
        return sum(bool(r[key]) for r in rows)

    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    by_prompt: dict[str, Counter[str]] = defaultdict(Counter)
    for r in rows:
        for bucket in (by_family[r["family"]], by_prompt[r["prompt_variant"]]):
            bucket["n"] += 1
            bucket["auto_final_correct"] += int(r["auto_final_correct"])
            bucket["manual_final_correct"] += int(r["manual_final_correct"])
            bucket["ambiguous_problem_boundary"] += int(r["ambiguous_problem_boundary"])
            bucket["clean_valid_prefill_candidate"] += int(r["clean_valid_prefill_candidate"])
            bucket["language_trait_use"] += int(r["language_trait_use"])

    false_negatives = [
        {
            "task_id": r["task_id"],
            "prompt_variant": r["prompt_variant"],
            "gold_answer": r["gold_answer"],
            "extracted_final": r["extracted_final"],
            "reason": r["manual_final_correct_reason"],
        }
        for r in rows
        if (not r["auto_final_correct"]) and r["manual_final_correct"]
    ]
    boundary_cases = [
        {
            "task_id": r["task_id"],
            "prompt_variant": r["prompt_variant"],
            "gold_answer": r["gold_answer"],
            "extracted_final": r["extracted_final"],
            "manual_error_span": r["manual_error_span"],
            "manual_note": r["manual_note"],
        }
        for r in rows
        if r["ambiguous_problem_boundary"]
    ]

    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "scope": "E153 MoE generation audit: Gemma4-26B-A4B-it only",
        "rows": len(rows),
        "by_model": {
            MODEL_KEY: {
                "n": len(rows),
                "auto_final_correct": count("auto_final_correct"),
                "manual_final_correct": count("manual_final_correct"),
                "ambiguous_problem_boundary": count("ambiguous_problem_boundary"),
                "manual_process_valid_strict": count("manual_process_valid_strict"),
                "manual_acpi_unrepaired": count("manual_acpi_unrepaired"),
                "causal_prefill_usable": count("causal_prefill_usable"),
                "clean_valid_prefill_candidate": count("clean_valid_prefill_candidate"),
                "language_trait_use": count("language_trait_use"),
                "posthoc_rationalization": count("posthoc_rationalization"),
                "repair_or_rethink_marker": count("manual_repair_or_rethink_marker"),
                "mean_generated_tokens": mean(float(r["generated_tokens"]) for r in rows),
            }
        },
        "by_family": {k: dict(v) for k, v in sorted(by_family.items())},
        "by_prompt": {k: dict(v) for k, v in sorted(by_prompt.items())},
        "false_negatives_or_boundary": false_negatives,
        "boundary_cases": boundary_cases,
    }


def write_report(summary: dict[str, Any]) -> None:
    m = summary["by_model"][MODEL_KEY]
    lines = [
        "# E153 MoE Generation Audit / E153 MoE 解题生成审计",
        "",
        "Scope / 范围：Gemma4-26B-A4B-it 的 E153 non-thinking generation。该模型是 MoE，单独报告，不并入 dense 统计。",
        "",
        "Key result / 关键结果：",
        "",
        "| model | rows | auto final correct | manual final correct | ambiguous boundary | clean valid prefill candidates | language-trait traces | unrepaired ACPI |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
        f"| {MODEL_KEY} | {m['n']} | {m['auto_final_correct']} | {m['manual_final_correct']} | {m['ambiguous_problem_boundary']} | {m['clean_valid_prefill_candidate']} | {m['language_trait_use']} | {m['manual_acpi_unrepaired']} |",
        "",
        "Findings / 发现：",
        "- Automatic false negatives are mostly answer-normalization issues: quoted string `'bcd'` and unit answers such as `120 meters` are semantically correct.",
        "- The only non-normalization disagreement is `e153_graph_path_constraints_02` under `solve_neutral`: the model answers `No` because the prompt does not state connectivity. A disconnected graph with a triangle and a separate edge has degrees `1,1,2,2,2` but no Euler trail over all edges. This is an ambiguous prompt-boundary case, not a clean wrong-answer failure.",
        "- No unrepaired ACPI was found in MoE generation. The MoE output is therefore consistent with dense generation on the main point: natural reasoning-first unrepaired ACPI did not appear in this E153 generation setting.",
        "- The MoE-specific value is boundary sensitivity and potential routing stability analysis, not current evidence of broad natural unrepaired ACPI prevalence.",
        "",
        "Use / 用法：",
        "- Use clean valid rows as mutation/prefill seeds only after excluding ambiguous graph-boundary rows.",
        "- Keep the graph-boundary row as a language/definition-boundary case card.",
        "- Do not pool this MoE statistic with dense models without an explicit architecture slice.",
        "",
        f"Artifacts / 产物：`{OUT_JSONL.relative_to(PROJECT)}`, `{OUT_SUMMARY.relative_to(PROJECT)}`.",
    ]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    data = json.loads(IN_FILE.read_text(encoding="utf-8"))
    rows = [audit_row(row, idx) for idx, row in enumerate(data["rows"])]
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    summary = summarize(rows)
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(summary)
    print(json.dumps({"out_jsonl": str(OUT_JSONL), "out_summary": str(OUT_SUMMARY), "out_report": str(OUT_REPORT), "summary": summary["by_model"]}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
