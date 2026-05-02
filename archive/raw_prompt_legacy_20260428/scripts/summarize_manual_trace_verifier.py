#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def fmt(x) -> str:
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="/home/Awei/P02_multilingual_process_lens/results/E04_manual_trace_verifier")
    p.add_argument("--out", default="/home/Awei/P02_multilingual_process_lens/reports/E04_manual_trace_verifier_summary.md")
    p.add_argument("--label-file", default="data/processed/manual_trace_audit_seed_20260427.jsonl")
    p.add_argument("--title", default="E04 Manual Trace Verifier Summary")
    args = p.parse_args()
    files = sorted(Path(args.results_dir).glob("*_manual_trace_verifier.json"))
    lines = [
        f"# {args.title}",
        "",
        f"Manual seed labels are in `{args.label_file}`.",
        "",
        "Modes:",
        "",
        "- `process_only`: judge mathematical process only; ignore truncation/format.",
        "- `training_candidate`: keep only if final answer, process, and output hygiene are all acceptable.",
        "",
        "## Overall",
        "",
        "| verifier | mode | prompt | n | acc | yes rate | false accept | process-invalid false accept | ACPI false accept | mean margin |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    detail = ["", "## Error Rows", ""]
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        model = data["verifier_model_key"]
        for s in data["summary"]:
            if s["slice"] != "all":
                continue
            lines.append(
                f"| {model} | {s['mode']} | {s['prompt_lang']} | {s['n']} | {fmt(s['accuracy'])} | "
                f"{fmt(s['yes_rate'])} | {fmt(s['false_accept_rate_target_false'])} | "
                f"{fmt(s['process_invalid_false_accept_rate'])} | {fmt(s['acpi_false_accept_rate'])} | {fmt(s['mean_margin'])} |"
            )
        errors = [r for r in data["rows"] if not r["correct"]]
        errors = sorted(errors, key=lambda r: (r["mode"], r["prompt_lang"], r["audit_idx"]))
        detail.append(f"### {model}")
        detail.append("")
        detail.append("| idx | mode | prompt | trace model | task | route | risk | target | pred | margin |")
        detail.append("|---:|---|---|---|---|---|---|---|---|---:|")
        for r in errors[:80]:
            detail.append(
                f"| {r['audit_idx']} | {r['mode']} | {r['prompt_lang']} | {r['trace_model_key']} | "
                f"{r['task_id']} | {r['input_lang']}->{r['reason_lang']} | {r['manual_risk']} | "
                f"{r['target']} | {r['pred']} | {fmt(r['yes_minus_no_logprob'])} |"
            )
        detail.append("")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines + detail) + "\n", encoding="utf-8")
    print(f"wrote {out}; models={len(files)}")


if __name__ == "__main__":
    main()
