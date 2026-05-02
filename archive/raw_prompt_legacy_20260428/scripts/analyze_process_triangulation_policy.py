#!/usr/bin/env python3
"""Offline policy simulation for conservative process-consistency triangulation.

The policies use human labels as an oracle to estimate the coverage/safety
trade-off of different rejection radii.  They are not deployable detectors.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def route(row: dict[str, Any]) -> str:
    return f"{row['input_lang']}->{row['reason_lang']}"


def accepted_by_policy(row: dict[str, Any], rows: list[dict[str, Any]], policy: str) -> bool:
    if policy == "final_correct_only":
        return row.get("manual_final_correct") is True
    if policy == "format_and_final":
        return row.get("manual_final_correct") is True and row.get("manual_format_valid") is True
    if policy == "human_training_upper_bound":
        return (
            row.get("manual_process_valid") is True
            and row.get("manual_final_correct") is True
            and row.get("manual_format_valid") is True
        )
    if policy == "same_route_reject_if_any_invalid":
        peers = [
            r
            for r in rows
            if (r["model_key"], r["task_id"], r["input_lang"], r["reason_lang"])
            == (row["model_key"], row["task_id"], row["input_lang"], row["reason_lang"])
        ]
        return row.get("manual_final_correct") is True and row.get("manual_format_valid") is True and all(
            p.get("manual_process_valid") is not False for p in peers
        )
    if policy == "same_reason_reject_if_any_invalid":
        peers = [
            r
            for r in rows
            if (r["model_key"], r["task_id"], r["reason_lang"]) == (row["model_key"], row["task_id"], row["reason_lang"])
        ]
        return row.get("manual_final_correct") is True and row.get("manual_format_valid") is True and all(
            p.get("manual_process_valid") is not False for p in peers
        )
    if policy == "same_task_reject_if_any_invalid":
        peers = [r for r in rows if (r["model_key"], r["task_id"]) == (row["model_key"], row["task_id"])]
        return row.get("manual_final_correct") is True and row.get("manual_format_valid") is True and all(
            p.get("manual_process_valid") is not False for p in peers
        )
    raise KeyError(policy)


def summarize_policy(rows: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    accepted = [r for r in rows if accepted_by_policy(r, rows, policy)]
    bad_kept = [r for r in accepted if r.get("manual_process_valid") is False]
    acpi_kept = [r for r in accepted if r.get("is_acpi")]
    paper_kept = [r for r in accepted if r.get("paper_grade_acpi")]
    clean_kept = [
        r
        for r in accepted
        if r.get("manual_process_valid") is True and r.get("manual_final_correct") is True and r.get("manual_format_valid") is True
    ]
    clean_total = [
        r
        for r in rows
        if r.get("manual_process_valid") is True and r.get("manual_final_correct") is True and r.get("manual_format_valid") is True
    ]
    return {
        "policy": policy,
        "accepted": len(accepted),
        "coverage": len(accepted) / len(rows) if rows else 0.0,
        "clean_recall": len(clean_kept) / len(clean_total) if clean_total else 0.0,
        "process_invalid_kept": len(bad_kept),
        "process_invalid_keep_rate": len(bad_kept) / len(accepted) if accepted else 0.0,
        "acpi_kept": len(acpi_kept),
        "paper_grade_acpi_kept": len(paper_kept),
    }


def slice_summaries(rows: list[dict[str, Any]], policy: str) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        for key in [("model", r["model_key"]), ("task", r["task_id"]), ("route", route(r))]:
            groups[key].append(r)
    out = []
    for (slice_type, slice_name), group in sorted(groups.items()):
        s = summarize_policy(group, policy)
        s.update({"slice_type": slice_type, "slice": slice_name})
        out.append(s)
    return out


def fmt(x: Any) -> str:
    return f"{x:.3f}" if isinstance(x, float) else str(x)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manual-jsonl", default="data/processed/manual_e05_audit_combined_20260427.jsonl")
    p.add_argument("--out-json", default="results/E14_process_triangulation_policy/process_triangulation_policy.json")
    p.add_argument("--out-report", default="reports/E14_process_triangulation_policy_summary.md")
    args = p.parse_args()

    rows = load_jsonl(Path(args.manual_jsonl))
    policies = [
        "final_correct_only",
        "format_and_final",
        "same_route_reject_if_any_invalid",
        "same_reason_reject_if_any_invalid",
        "same_task_reject_if_any_invalid",
        "human_training_upper_bound",
    ]
    overall = [summarize_policy(rows, p) for p in policies]
    slices = {p: slice_summaries(rows, p) for p in policies}
    result = {"manual_jsonl": args.manual_jsonl, "overall": overall, "slices": slices}
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# E14 Process-Consistency Triangulation Policy Smoke",
        "",
        f"Manual labels: `{args.manual_jsonl}`.",
        "",
        "This is an oracle simulation over the selected/high-risk manual set. It asks how much safety a conservative rejection radius could buy, and how much clean data it would sacrifice. It is not a deployable detector.",
        "",
        "## Overall Policy Trade-Off",
        "",
        "| policy | accepted | coverage | clean recall | invalid kept | invalid keep rate | ACPI kept | paper-grade ACPI kept |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in overall:
        lines.append(
            f"| {s['policy']} | {s['accepted']} | {fmt(s['coverage'])} | {fmt(s['clean_recall'])} | "
            f"{s['process_invalid_kept']} | {fmt(s['process_invalid_keep_rate'])} | {s['acpi_kept']} | {s['paper_grade_acpi_kept']} |"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- `final_correct_only` estimates the old outcome-only selection risk: it keeps all answer-correct ACPI unless a process check catches them.",
            "- `format_and_final` is safer for training hygiene but still keeps cleanly formatted ACPI such as rows 234, 402, and 445.",
            "- Same-route rejection is the least destructive triangulation radius; same-task rejection is a high-precision but low-coverage upper-bound.",
            "- If expanded data shows same-route rejection catches most paper-grade ACPI while retaining enough clean rows, it becomes a plausible method branch.",
        ],
    )
    out_report = Path(args.out_report)
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_json}")
    print(f"wrote {out_report}")


if __name__ == "__main__":
    main()
