#!/usr/bin/env python3
"""Build E162 low-confidence truncation repair cases.

E162 starts from already audited traces.  Each case stores a causal prefix that
ends after a suspected local error, plus offline hints used by intervention
conditions.  The gold answer and labels are metadata only; blind prompts never
expose them.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]

E159_GENERATION_AUDIT = PROJECT / "data/processed/e159_generation_process_acpi_audit_20260501.jsonl"
E159_CANDIDATE_BANK = PROJECT / "data/processed/e159_answer_preserving_candidate_solutions_20260501.jsonl"
E159_TASK_BANK = PROJECT / "data/processed/e159_answer_preserving_tasks_20260501.jsonl"
OUT = PROJECT / "data/processed/e162_low_confidence_error_prompt_cases_20260501.jsonl"
SUMMARY_OUT = PROJECT / "results/E162_low_confidence_error_prompt_repair/_case_bank/e162_case_bank_summary_20260501.json"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def sentence_end_after(text: str, start: int) -> int:
    candidates = []
    for pat in [".\n", ". ", ".)", ")\n", "\n\n"]:
        pos = text.find(pat, start)
        if pos >= 0:
            candidates.append(pos + len(pat))
    if not candidates:
        return min(len(text), start + 240)
    return min(candidates)


def infer_error_quote(row: dict[str, Any], trace: str) -> str:
    spans = row.get("manual_invalid_step_spans") or []
    if row.get("manual_error_span"):
        return str(row["manual_error_span"])
    if row.get("family") == "multilingual_semantic" and "zhi duo wei" in row.get("problem", ""):
        for needle in [
            "must be a multiple of 3",
            "is a multiple of 3",
            "is divisible by 3",
            "multiple of 3",
        ]:
            if needle.lower() in trace.lower():
                return needle
        return "zhi duo wei 3"
    return str(spans[0]) if spans else ""


def make_prefix(trace: str, quote: str) -> tuple[str, str]:
    """Return prefix ending after the first likely wrong step and a cut reason."""
    if not trace:
        return "", "empty_trace"
    lower = trace.lower()
    needles = [quote] if quote else []
    if "zhi duo wei" in trace or "multiple of 3" in lower or "divisible by 3" in lower:
        needles.extend(["multiple of 3", "divisible by 3", "zhi duo wei 3"])
    for needle in needles:
        if not needle:
            continue
        pos = lower.find(needle.lower())
        if pos >= 0:
            end = sentence_end_after(trace, pos)
            return trace[:end].strip(), f"after_quote::{needle}"
    end = sentence_end_after(trace, min(200, len(trace) // 3))
    return trace[:end].strip(), "heuristic_early_sentence"


def random_span(problem: str, error_quote: str) -> str:
    candidates = re.findall(r"`[^`]+`|\$[^$]+\$|[-+]?\d+(?:\.\d+)?\s*(?:<=|<|>=|>)?\s*[A-Za-z]*|[A-Za-z][A-Za-z0-9_ -]{2,40}", problem)
    error_norm = normalize(error_quote).lower()
    for cand in candidates:
        c = normalize(cand)
        if c and c.lower() not in error_norm and error_norm not in c.lower():
            return c
    return normalize(problem[:40])


def oracle_hint(row: dict[str, Any], quote: str) -> str:
    problem = row.get("problem", "")
    if "zhi duo wei" in problem:
        return "`zhi duo wei 3` means at most 3, i.e. <= 3; it does not mean multiple of 3 or divisible by 3."
    if row.get("manual_error_type"):
        return f"The flagged span is the actual local error type: {row['manual_error_type']}. Replace that local step before continuing."
    return "The flagged span is the actual local error. Replace only that local step before continuing."


def localized_hint(row: dict[str, Any], quote: str) -> str:
    if "zhi duo wei" in row.get("problem", ""):
        return "The interpretation of `zhi duo wei 3` may be wrong. Recheck it from the original wording before continuing."
    return f"The step `{quote}` may be wrong. Recheck that step from the original problem before continuing."


def generated_wrong_cases(created: str) -> list[dict[str, Any]]:
    rows = load_jsonl(E159_GENERATION_AUDIT)
    tasks = {r["task_id"]: r for r in load_jsonl(E159_TASK_BANK)}
    cases: list[dict[str, Any]] = []
    for row in rows:
        final_ok = bool(row.get("manual_final_correct_audit"))
        process_ok = bool(row.get("manual_process_valid_strict"))
        if final_ok or process_ok:
            continue
        trace = row["completion"]
        problem = tasks[row["task_id"]]["problem"]
        row_for_hint = {**row, "problem": problem}
        quote = infer_error_quote(row_for_hint, trace)
        prefix, cut_reason = make_prefix(trace, quote)
        case_id = f"e162_generated_wrong_{row['model_key']}_{row['task_id']}_{row['prompt_variant']}"
        cases.append(
            {
                "created_at": created,
                "experiment": "E162_low_confidence_error_prompt_case_bank",
                "case_id": case_id,
                "case_type": "generated_wrong_trace",
                "source_experiment": "E159_answer_preserving_generation_process_audit",
                "source_model_key": row["model_key"],
                "task_id": row["task_id"],
                "family": row["family"],
                "prompt_variant_source": row["prompt_variant"],
                "problem": problem,
                "gold_answer": str(row["gold_answer"]),
                "source_trace": trace,
                "source_extracted_final": str(row.get("runner_extracted_final") or ""),
                "source_final_correct": final_ok,
                "source_process_valid_strict": process_ok,
                "manual_error_span": quote,
                "manual_error_type": "generated_wrong_semantic_or_process_error",
                "trigger_kind": "human_audited_error_span",
                "prefix_cut_mode": cut_reason,
                "prefix_text": prefix,
                "localized_span": quote,
                "localized_hint": localized_hint(row_for_hint, quote),
                "oracle_hint": oracle_hint(row_for_hint, quote),
                "random_location_span": random_span(problem, quote),
                "gold_answer_in_prompt_by_design": False,
                "manual_label_in_prompt_by_design": False,
                "notes": "Generated final-wrong/process-wrong trace. Prefix is causal and stops before the original final answer.",
            }
        )
    return sorted(cases, key=lambda r: (r["family"], r["case_id"]))


def invalid_reference_cases(created: str) -> list[dict[str, Any]]:
    rows = load_jsonl(E159_CANDIDATE_BANK)
    cases: list[dict[str, Any]] = []
    for row in rows:
        if row["candidate_variant"] != "invalid_answer_preserving_reference":
            continue
        trace = row["candidate_solution"]
        quote = infer_error_quote(row, trace)
        prefix, cut_reason = make_prefix(trace, quote)
        cases.append(
            {
                "created_at": created,
                "experiment": "E162_low_confidence_error_prompt_case_bank",
                "case_id": f"e162_controlled_acpi_{row['solution_id']}",
                "case_type": "controlled_invalid_answer_preserving_trace",
                "source_experiment": "E159_answer_preserving_candidate_solution_bank",
                "source_model_key": "manual_reference",
                "task_id": row["task_id"],
                "family": row["family"],
                "prompt_variant_source": "candidate_solution",
                "problem": row["problem"],
                "gold_answer": str(row["gold_answer"]),
                "source_trace": trace,
                "source_extracted_final": str(row["gold_answer"]),
                "source_final_correct": True,
                "source_process_valid_strict": False,
                "manual_error_span": quote,
                "manual_error_type": row.get("manual_error_type") or "controlled_answer_preserving_process_error",
                "trigger_kind": "human_audited_error_span",
                "prefix_cut_mode": cut_reason,
                "prefix_text": prefix,
                "localized_span": quote,
                "localized_hint": localized_hint(row, quote),
                "oracle_hint": oracle_hint(row, quote),
                "random_location_span": random_span(row["problem"], quote),
                "gold_answer_in_prompt_by_design": False,
                "manual_label_in_prompt_by_design": False,
                "notes": "Controlled invalid answer-preserving trace. Prefix is causal and does not include labels.",
            }
        )
    return sorted(cases, key=lambda r: (r["family"], r["case_id"]))


def main() -> None:
    created = datetime.now().isoformat(timespec="seconds")
    cases = generated_wrong_cases(created) + invalid_reference_cases(created)
    write_jsonl(OUT, cases)
    by_type = Counter(r["case_type"] for r in cases)
    by_family = Counter(r["family"] for r in cases)
    summary = {
        "created_at": created,
        "case_count": len(cases),
        "out": str(OUT),
        "by_type": dict(sorted(by_type.items())),
        "by_family": dict(sorted(by_family.items())),
        "causal_prefix_without_final_answer_count": sum("Final answer:" not in r["prefix_text"] for r in cases),
        "gold_answer_in_prompt_by_design_rows": sum(int(r["gold_answer_in_prompt_by_design"]) for r in cases),
        "manual_label_in_prompt_by_design_rows": sum(int(r["manual_label_in_prompt_by_design"]) for r in cases),
    }
    write_json(SUMMARY_OUT, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
