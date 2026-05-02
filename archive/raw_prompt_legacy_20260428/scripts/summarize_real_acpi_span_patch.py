#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def score(r):
    return float(r.get("mean_valid_to_bad_effect", 0)) - float(r.get("mean_bad_to_valid_effect", 0))


def fmt(x):
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="results/E09_real_acpi_span_patch")
    p.add_argument("--out", default="reports/E09_real_acpi_span_patch_summary.md")
    args = p.parse_args()
    files = sorted(Path(args.results_dir).glob("*_real_acpi_span_patch.json"))
    lines = [
        "# E09 Real ACPI Span Patch Summary",
        "",
        "Clean direction: `valid->bad` should increase Yes-vs-No process-valid margin on the bad trace; `bad->valid` should decrease it on the valid trace.",
        "",
        "| model | pair | best clean/effect span | layer | v2b | b2v | abs |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    details = ["", "## Top Effects", "", "| model | pair | span | layer | v2b | b2v | clean |", "|---|---|---|---:|---:|---:|---|"]
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        model = data["model_key"]
        by_pair = {}
        for r in data.get("by_span_layer_pair", []):
            by_pair.setdefault(r["pair_id"], []).append(r)
        for pair_id, rows in sorted(by_pair.items()):
            clean = [r for r in rows if r["mean_valid_to_bad_effect"] > 0 and r["mean_bad_to_valid_effect"] < 0]
            best = max(clean or rows, key=lambda r: (score(r), r.get("mean_abs_effect", 0)))
            label = best["span"] + ("" if clean else "*")
            lines.append(
                f"| {model} | {pair_id} | {label} | {best['layer']} | {fmt(best['mean_valid_to_bad_effect'])} | "
                f"{fmt(best['mean_bad_to_valid_effect'])} | {fmt(best['mean_abs_effect'])} |"
            )
            for r in sorted(rows, key=score, reverse=True)[:12]:
                is_clean = r["mean_valid_to_bad_effect"] > 0 and r["mean_bad_to_valid_effect"] < 0
                details.append(
                    f"| {model} | {r['pair_id']} | {r['span']} | {r['layer']} | {fmt(r['mean_valid_to_bad_effect'])} | "
                    f"{fmt(r['mean_bad_to_valid_effect'])} | {is_clean} |"
                )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines + details) + "\n", encoding="utf-8")
    print(f"wrote {out}; models={len(files)}")


if __name__ == "__main__":
    main()
