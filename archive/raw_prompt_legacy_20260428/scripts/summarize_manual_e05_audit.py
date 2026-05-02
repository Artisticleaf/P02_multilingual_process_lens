#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def fmt_bool(x):
    if x is None:
        return "unknown"
    return str(bool(x)).lower()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manual-jsonl", default="data/processed/manual_e05_audit_seed_20260427.jsonl")
    p.add_argument("--out", default="reports/E05_manual_acpi_audit_summary.md")
    args = p.parse_args()
    rows = [json.loads(line) for line in Path(args.manual_jsonl).read_text(encoding="utf-8").splitlines() if line.strip()]
    lines = [
        "# E05 Manual ACPI Audit Summary",
        "",
        f"Manual labels: `{args.manual_jsonl}`.",
        "",
        "Policy: `manual_process_valid=false` is strict: any asserted mathematical or language-semantic error makes the process invalid. Self-corrected errors are tagged in `manual_risk`; `paper_grade_acpi` marks uncorrected/high-risk ACPI examples.",
        "",
        "## Overall Counts",
        "",
        "| slice | count |",
        "|---|---:|",
        f"| audited rows | {len(rows)} |",
        f"| process-valid | {sum(r['manual_process_valid'] is True for r in rows)} |",
        f"| process-invalid | {sum(r['manual_process_valid'] is False for r in rows)} |",
        f"| process-unknown | {sum(r['manual_process_valid'] is None for r in rows)} |",
        f"| final-correct | {sum(r['manual_final_correct'] is True for r in rows)} |",
        f"| final-wrong | {sum(r['manual_final_correct'] is False for r in rows)} |",
        f"| final-unknown | {sum(r['manual_final_correct'] is None for r in rows)} |",
        f"| format-clean | {sum(r['manual_format_valid'] is True for r in rows)} |",
        f"| format-broken | {sum(r['manual_format_valid'] is False for r in rows)} |",
        f"| strict ACPI | {sum(r['is_acpi'] for r in rows)} |",
        f"| paper-grade ACPI | {sum(r.get('paper_grade_acpi') for r in rows)} |",
        "",
        "## By Model",
        "",
        "| model | n | process invalid | final correct | format broken | strict ACPI | paper-grade ACPI |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    by_model = defaultdict(list)
    for r in rows:
        by_model[r["model_key"]].append(r)
    for model, g in sorted(by_model.items()):
        lines.append(
            f"| {model} | {len(g)} | {sum(r['manual_process_valid'] is False for r in g)} | "
            f"{sum(r['manual_final_correct'] is True for r in g)} | {sum(r['manual_format_valid'] is False for r in g)} | "
            f"{sum(r['is_acpi'] for r in g)} | {sum(r.get('paper_grade_acpi') for r in g)} |"
        )
    lines += [
        "",
        "## By Task",
        "",
        "| task | n | process invalid | final wrong | strict ACPI | top risk signal |",
        "|---|---:|---:|---:|---:|---|",
    ]
    by_task = defaultdict(list)
    for r in rows:
        by_task[r["task_id"]].append(r)
    for task, g in sorted(by_task.items()):
        risk = Counter(r["manual_risk"] for r in g).most_common(1)[0][0]
        lines.append(
            f"| {task} | {len(g)} | {sum(r['manual_process_valid'] is False for r in g)} | "
            f"{sum(r['manual_final_correct'] is False for r in g)} | {sum(r['is_acpi'] for r in g)} | {risk} |"
        )
    lines += [
        "",
        "## Strict ACPI Rows",
        "",
        "| idx | paper-grade | model | task | route | risk | earliest error | correction |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        if not r["is_acpi"]:
            continue
        correction = r["manual_correction"].replace("|", "/")[:180]
        earliest = (r.get("earliest_error") or "").replace("|", "/")[:80]
        lines.append(
            f"| {r['audit_idx']} | {bool(r.get('paper_grade_acpi'))} | {r['model_key']} | {r['task_id']} | "
            f"{r['input_lang']}->{r['reason_lang']} | {r['manual_risk']} | {earliest} | {correction} |"
        )
    lines += [
        "",
        "## Risk Distribution",
        "",
        "| risk | count |",
        "|---|---:|",
    ]
    for risk, n in Counter(r["manual_risk"] for r in rows).most_common():
        lines.append(f"| {risk} | {n} |")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}; rows={len(rows)}")


if __name__ == "__main__":
    main()
