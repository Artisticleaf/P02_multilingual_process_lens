#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def fmt(x):
    return f"{x:.3f}" if isinstance(x, float) else str(x)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="results/E12_contrastive_acpi_verifier")
    p.add_argument("--out", default="reports/E12_contrastive_acpi_verifier_summary.md")
    args = p.parse_args()
    files = sorted(Path(args.results_dir).glob("*_contrastive_acpi_verifier.json"))
    lines = [
        "# E12 Contrastive ACPI Verifier Summary",
        "",
        "The verifier sees a valid and an answer-correct/process-invalid sibling trace and must choose which trace has invalid reasoning. This separates absolute Yes-bias from pairwise error visibility.",
        "",
        "## Overall",
        "",
        "| verifier | n | acc | mean target margin |",
        "|---|---:|---:|---:|",
    ]
    slices = ["", "## Slices", "", "| verifier | slice type | slice | n | acc | mean target margin |", "|---|---|---|---:|---:|---:|"]
    rows_lines = ["", "## Rows", "", "| verifier | pair | prompt | order | target | pred | margin | bad risk |", "|---|---|---|---|---|---|---:|---|"]
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        verifier = data["verifier_model_key"]
        overall = next(s for s in data["summary"] if s["slice_type"] == "all")
        lines.append(f"| {verifier} | {overall['n']} | {fmt(overall['acc'])} | {fmt(overall['mean_margin'])} |")
        for s in data["summary"]:
            if s["slice_type"] == "all":
                continue
            slices.append(f"| {verifier} | {s['slice_type']} | {s['slice']} | {s['n']} | {fmt(s['acc'])} | {fmt(s['mean_margin'])} |")
        for r in data["rows"]:
            rows_lines.append(
                f"| {verifier} | {r['pair_id']} | {r['prompt_lang']} | {r['order']} | {r['target']} | {r['pred']} | "
                f"{fmt(r['margin_target_minus_other'])} | {str(r['bad_risk']).replace('|','/')} |"
            )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines + slices + rows_lines) + "\n", encoding="utf-8")
    print(f"wrote {out}; models={len(files)}")


if __name__ == "__main__":
    main()
