#!/usr/bin/env python3
"""Build E167 hidden-derived repair cases from E166 monitor outputs.

Unlike E165, non-oracle localized spans are selected only from automatic
sentence/step boundaries. The E166 calibration bank contains manual error-span
endpoints for offline evaluation, but E167 repair prompts must not use those
manual endpoints as candidate trigger locations.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
E166_DIR = PROJECT / "results/E166_hardened_hidden_monitor_replay"
CALIBRATION = PROJECT / "reports/E166_HIDDEN_MONITOR_CALIBRATION_AUDIT_20260502.json"
SOLUTIONS = PROJECT / "data/processed/e164_hardened_multi_family_candidate_solutions_20260501.jsonl"
PREFIX_BANK = PROJECT / "data/processed/e166_hardened_monitor_prefix_points_20260502.jsonl"
OUT = PROJECT / "data/processed/e167_hidden_derived_repair_cases_20260502.jsonl"
SUMMARY = PROJECT / "reports/E167_HIDDEN_DERIVED_REPAIR_CASES_SUMMARY_20260502.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def risk(row: dict[str, Any], key: str) -> float:
    return -float(row["component_validity_scores"][key])


def eligible_trigger_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("boundary_kind") != "manual_error_span_end"]


def first_trigger(rows: list[dict[str, Any]], key: str, threshold: float) -> dict[str, Any] | None:
    for row in sorted(rows, key=lambda r: (r["prefix_char_end"], r["prefix_id"])):
        if risk(row, key) >= threshold:
            return row
    return None


def top_trigger(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    return max(rows, key=lambda r: risk(r, key))


def hidden_hint(row: dict[str, Any], policy: str) -> str:
    return (
        f"The hidden monitor crossed the E166 {policy} threshold at this causal prefix. "
        "Recheck the flagged span against the original problem before continuing."
    )


def main() -> None:
    created = datetime.now().isoformat(timespec="seconds")
    calibration = load_json(CALIBRATION)
    solution_by_id = {r["solution_id"]: r for r in load_jsonl(SOLUTIONS)}
    prefix_by_id = {r["prefix_id"]: r for r in load_jsonl(PREFIX_BANK)}
    rows_out: list[dict[str, Any]] = []
    model_summaries = {}

    for model in calibration["models"]:
        model_key = model["model_key"]
        best_key = model["best_key"]
        hp_threshold = model["best_key_record"]["high_precision_eval"]["threshold"]
        budget_threshold = model["best_key_record"]["budgeted_eval"]["threshold"]
        replay = load_json(E166_DIR / f"{model_key}_e166_generation_prefill_full_20260502.json")
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in replay["rows"]:
            groups[row["solution_id"]].append(row)

        counts: Counter[str] = Counter()
        for solution_id, vals in sorted(groups.items()):
            sol = solution_by_id[solution_id]
            is_valid = bool(sol["manual_process_valid_strict"])
            trace_class = "valid" if is_valid else ("invalid_answer_correct" if sol["source_final_correct"] else "invalid_answer_wrong")
            policies = [
                ("high_precision", hp_threshold),
                ("budgeted", budget_threshold),
            ]
            candidates = eligible_trigger_rows(vals)
            if not candidates:
                counts["solutions_without_auto_boundary_candidates"] += 1
                continue
            for policy, threshold in policies:
                trig = first_trigger(candidates, best_key, threshold)
                if trig is None and not is_valid:
                    trig = top_trigger(candidates, best_key)
                    trigger_source = "fallback_top_risk_no_threshold_crossing"
                elif trig is None:
                    counts[f"{policy}_valid_no_trigger"] += 1
                    continue
                else:
                    trigger_source = "first_threshold_crossing"

                manual_span = sol.get("manual_error_span") or ""
                prefix_row = prefix_by_id[trig["prefix_id"]]
                hidden_span = trig["visible_span"]
                ranked = sorted(vals, key=lambda r: risk(r, best_key), reverse=True)
                trigger_rank = 1 + next(i for i, r in enumerate(ranked) if r["prefix_id"] == trig["prefix_id"])
                rows_out.append(
                    {
                        "created_at": created,
                        "experiment": "E167_hidden_derived_repair_case_bank",
                        "case_id": f"e167_{model_key}_{policy}_{solution_id}",
                        "case_type": f"hidden_{policy}_{trace_class}",
                        "model_key_for_hidden_monitor": model_key,
                        "hidden_policy": policy,
                        "hidden_component_key": best_key,
                        "hidden_threshold": threshold,
                        "hidden_trigger_source": trigger_source,
                        "hidden_trigger_risk": risk(trig, best_key),
                        "hidden_trigger_prefix_id": trig["prefix_id"],
                        "hidden_trigger_boundary_kind": trig["boundary_kind"],
                        "hidden_trigger_prefix_char_end": trig["prefix_char_end"],
                        "hidden_trigger_is_manual_target_offline": bool(trig["monitor_target_offline"]),
                        "hidden_trigger_rank_by_risk_offline": trigger_rank,
                        "task_id": sol["task_id"],
                        "solution_id": solution_id,
                        "family": sol["family"],
                        "problem": sol["problem"],
                        "gold_answer": sol["gold_answer"],
                        "prefix_text": prefix_row["prefix_text"],
                        "localized_span": hidden_span,
                        "localized_hint": hidden_hint(trig, policy),
                        "random_location_span": sol.get("random_location_span") or "Report only the requested value",
                        "oracle_hint": sol.get("oracle_hint") or "Use the offline human span only as an oracle upper bound.",
                        "manual_error_span": manual_span,
                        "manual_error_type": sol.get("manual_error_type") or "",
                        "trigger_kind": "hidden_monitor_threshold",
                        "source_experiment": "E166_hardened_hidden_monitor_replay",
                        "source_model_key": "manual_reference",
                        "source_trace": sol["candidate_solution"],
                        "source_extracted_final": sol["source_extracted_final"],
                        "source_final_correct": bool(sol["source_final_correct"]),
                        "source_process_valid_strict": bool(sol["manual_process_valid_strict"]),
                        "gold_answer_in_prompt_by_design": False,
                        "manual_label_in_prompt_by_design": False,
                        "manual_error_span_in_prompt_by_design": False,
                        "hidden_span_in_prompt_by_design": True,
                        "hidden_trigger_candidate_policy": "auto_boundary_only",
                        "manual_error_span_end_excluded_from_trigger_candidates": True,
                        "offline_manual_span_equals_hidden_span": bool(manual_span and manual_span == hidden_span),
                        "offline_hidden_span_contains_manual_span": bool(manual_span and manual_span in hidden_span),
                        "offline_manual_span_contains_hidden_span": bool(manual_span and hidden_span in manual_span),
                        "notes": (
                            "E167 strict-auto case. localized_span and prefix_text are hidden-derived from E166 "
                            "causal replay over automatic sentence/step boundaries only. manual_error_span/oracle_hint "
                            "are offline or oracle-upper-bound fields only."
                        ),
                    }
                )
                counts[f"{policy}_cases"] += 1
                counts[f"{policy}_manual_target_trigger"] += int(bool(trig["monitor_target_offline"]))
                counts[f"{policy}_invalid_cases"] += int(not is_valid)
                counts[f"{policy}_valid_cases"] += int(is_valid)

        model_rows = [r for r in rows_out if r["model_key_for_hidden_monitor"] == model_key]
        model_summaries[model_key] = {
            "best_key": best_key,
            "high_precision_threshold": hp_threshold,
            "budgeted_threshold": budget_threshold,
            "counts": dict(counts),
            "cases": len(model_rows),
            "families": dict(sorted(Counter(r["family"] for r in model_rows).items())),
            "manual_target_trigger_rate": (
                mean([int(r["hidden_trigger_is_manual_target_offline"]) for r in model_rows if not r["source_process_valid_strict"]])
                if any(not r["source_process_valid_strict"] for r in model_rows)
                else None
            ),
        }

    rows_out = sorted(rows_out, key=lambda r: (r["model_key_for_hidden_monitor"], r["hidden_policy"], r["case_type"], r["family"], r["case_id"]))
    write_jsonl(OUT, rows_out)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "out": str(OUT.relative_to(PROJECT)),
        "cases": len(rows_out),
        "models": model_summaries,
        "trigger_candidate_policy": "auto_boundary_only",
        "leakage_policy": "Runtime repair prompts may use problem, prefix_text, localized_span, localized_hint, random_location_span; gold answer/manual labels remain offline. oracle_hint is allowed only in oracle condition. manual_error_span_end E166 points are excluded from E167 non-oracle trigger candidates.",
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
