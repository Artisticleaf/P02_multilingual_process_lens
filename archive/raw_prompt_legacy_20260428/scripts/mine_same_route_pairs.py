#!/usr/bin/env python3
"""Mine manually audited valid/bad sibling pairs for next causal probes.

This is intentionally label-driven: it does not create new ground truth.  It
turns the existing human audit into a pair bank and makes the confounds visible.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def route(row: dict[str, Any]) -> str:
    return f"{row['input_lang']}->{row['reason_lang']}"


def is_valid_control(row: dict[str, Any], require_format_clean: bool) -> bool:
    if row.get("manual_process_valid") is not True or row.get("manual_final_correct") is not True:
        return False
    if require_format_clean and row.get("manual_format_valid") is not True:
        return False
    return True


def is_bad_case(row: dict[str, Any], acpi_only: bool) -> bool:
    if row.get("manual_process_valid") is not False:
        return False
    if acpi_only and not row.get("is_acpi"):
        return False
    return True


def pair_scope(bad: dict[str, Any], valid: dict[str, Any]) -> str | None:
    if (bad["model_key"], bad["task_id"], bad["input_lang"], bad["reason_lang"]) == (
        valid["model_key"],
        valid["task_id"],
        valid["input_lang"],
        valid["reason_lang"],
    ):
        return "same_route"
    if (bad["model_key"], bad["task_id"], bad["reason_lang"]) == (
        valid["model_key"],
        valid["task_id"],
        valid["reason_lang"],
    ):
        return "same_reason_lang"
    if (bad["model_key"], bad["task_id"]) == (valid["model_key"], valid["task_id"]):
        return "same_task"
    return None


def score_pair(bad: dict[str, Any], valid: dict[str, Any], scope: str) -> float:
    score = {"same_route": 4.0, "same_reason_lang": 2.0, "same_task": 1.0}[scope]
    if bad.get("paper_grade_acpi"):
        score += 2.0
    if bad.get("manual_final_correct") is True:
        score += 1.0
    if bad.get("manual_format_valid") is True:
        score += 0.5
    if valid.get("manual_format_valid") is True:
        score += 1.0
    if valid.get("manual_risk") == "valid_clean":
        score += 0.5
    if bad.get("manual_risk", "").startswith("semantic_drift"):
        score += 0.5
    if "self_corrected" in bad.get("manual_risk", ""):
        score -= 0.5
    return score


def choose_pairs(rows: list[dict[str, Any]], acpi_only: bool) -> list[dict[str, Any]]:
    bad_rows = [r for r in rows if is_bad_case(r, acpi_only)]
    valid_rows = [r for r in rows if is_valid_control(r, require_format_clean=False)]
    candidates: list[dict[str, Any]] = []
    for bad in bad_rows:
        for valid in valid_rows:
            scope = pair_scope(bad, valid)
            if scope is None:
                continue
            candidates.append(
                {
                    "id": f"{bad['model_key']}_{bad['task_id']}_{route(bad).replace('->','_to_')}_{bad['e05_idx']}_bad_{valid['e05_idx']}_valid",
                    "scope": scope,
                    "score": score_pair(bad, valid, scope),
                    "model_key": bad["model_key"],
                    "task_id": bad["task_id"],
                    "route_bad": route(bad),
                    "route_valid": route(valid),
                    "bad_idx": bad["e05_idx"],
                    "valid_idx": valid["e05_idx"],
                    "bad_risk": bad["manual_risk"],
                    "valid_risk": valid["manual_risk"],
                    "bad_final_correct": bad.get("manual_final_correct"),
                    "bad_format_valid": bad.get("manual_format_valid"),
                    "valid_format_valid": valid.get("manual_format_valid"),
                    "paper_grade_acpi": bad.get("paper_grade_acpi"),
                    "bad_earliest_error": bad.get("earliest_error"),
                    "bad_sentence_labels": bad.get("sentence_labels", []),
                    "valid_sentence_labels": valid.get("sentence_labels", []),
                }
            )
    # Keep the best few controls per bad row, preserving alternatives for later.
    by_bad: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for c in candidates:
        by_bad[c["bad_idx"]].append(c)
    selected: list[dict[str, Any]] = []
    for _, group in sorted(by_bad.items()):
        group = sorted(
            group,
            key=lambda x: (
                x["scope"] != "same_route",
                x["scope"] != "same_reason_lang",
                -x["score"],
                x["valid_idx"],
            ),
        )
        selected.extend(group[:3])
    return sorted(selected, key=lambda x: (-x["score"], x["model_key"], x["task_id"], x["bad_idx"], x["valid_idx"]))


def write_report(rows: list[dict[str, Any]], pairs: list[dict[str, Any]], out: Path, label_file: Path) -> None:
    invalid = [r for r in rows if r.get("manual_process_valid") is False]
    acpi = [r for r in invalid if r.get("is_acpi")]
    paper = [r for r in invalid if r.get("paper_grade_acpi")]
    scope_counts = Counter(p["scope"] for p in pairs)
    lines = [
        "# E13 Same-Route Pair Mining Summary",
        "",
        f"Manual labels: `{label_file}`.",
        "",
        "Goal: convert human-audited rows into clean sibling pairs for contrastive verification and non-verdict span patching. This is not a prevalence estimate.",
        "",
        "## Audit Base",
        "",
        f"- audited rows: {len(rows)}",
        f"- process-invalid rows: {len(invalid)}",
        f"- ACPI/self-corrected final-correct invalid rows: {len(acpi)}",
        f"- paper-grade ACPI rows: {len(paper)}",
        f"- candidate pair records: {len(pairs)}",
        f"- scope counts: {dict(scope_counts)}",
        "",
        "## Best Pair Candidates",
        "",
        "| score | scope | bad | valid | model | task | routes | bad risk | valid risk | paper | earliest error |",
        "|---:|---|---:|---:|---|---|---|---|---|---|---|",
    ]
    for p in pairs[:40]:
        err = str(p.get("bad_earliest_error") or "").replace("|", "\\|")
        lines.append(
            f"| {p['score']:.1f} | {p['scope']} | {p['bad_idx']} | {p['valid_idx']} | "
            f"{p['model_key']} | {p['task_id']} | {p['route_bad']} / {p['route_valid']} | "
            f"{p['bad_risk']} | {p['valid_risk']} | {p['paper_grade_acpi']} | {err} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Strongest same-route causal pairs now include Qwen3-14B `disc_en_75_off` 358/359, Qwen3-14B `deriv_sum` 402/403, Qwen3.5 `ratio_boys_total` 261/260, and Qwen3.5 `disc_en_25_off` 234/235.",
            "- Qwen3-14B `percent_then_discount` 445 remains important but its cleanest existing sibling is same-task/same-input rather than same-route; treat it as lexicalization evidence, not a clean route-controlled pair.",
            "- Self-corrected rows are useful for safety/data-cleaning, but paper-grade method claims should prioritize unmarked ACPI or semantic-drift rows.",
            "- The next experiment should use this bank for expanded contrastive verification before any head/MLP localization.",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manual-jsonl", default="data/processed/manual_e05_audit_combined_20260427.jsonl")
    p.add_argument("--out-json", default="data/processed/e13_same_route_pair_bank_20260427.json")
    p.add_argument("--out-report", default="reports/E13_same_route_pair_mining_summary.md")
    p.add_argument("--acpi-only", action="store_true", help="Only mine final-correct process-invalid rows.")
    args = p.parse_args()

    label_file = Path(args.manual_jsonl)
    rows = load_jsonl(label_file)
    pairs = choose_pairs(rows, acpi_only=args.acpi_only)
    result = {
        "manual_jsonl": str(label_file),
        "args": vars(args),
        "summary": {
            "audited_rows": len(rows),
            "candidate_pairs": len(pairs),
            "scope_counts": dict(Counter(p["scope"] for p in pairs)),
        },
        "pairs": pairs,
    }
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(rows, pairs, Path(args.out_report), label_file)
    print(f"wrote {out_json}; pairs={len(pairs)}")
    print(f"wrote {args.out_report}")


if __name__ == "__main__":
    main()
