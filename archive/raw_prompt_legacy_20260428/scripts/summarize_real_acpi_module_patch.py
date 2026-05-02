#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="results/E19_real_acpi_module_patch")
    p.add_argument("--out", default="reports/E19_real_acpi_module_patch_summary.md")
    args = p.parse_args()
    files = sorted(Path(args.results_dir).glob("*_real_acpi_module_patch.json"))
    lines = [
        "# E19 Real ACPI Module Patch Summary",
        "",
        "Goal: decompose robust residual-span effects into attention-output vs MLP-output replacement on the same verifier prompt. This remains a smoke test: module output replacement is not a full circuit proof.",
        "",
        "| model | pair | best module | span | layer | v2b effect | b2v effect | clean direction |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        model = data["model_key"]
        rows = [r for r in data.get("rows", []) if r.get("error") is None]
        for pair_id in sorted({r["pair_id"] for r in rows}):
            sub = [r for r in rows if r["pair_id"] == pair_id]
            if not sub:
                continue
            clean = [r for r in sub if r["valid_to_bad_effect"] > 0 and r["bad_to_valid_effect"] < 0]
            best_pool = clean or sub
            best = max(best_pool, key=lambda r: (r["valid_to_bad_effect"] - r["bad_to_valid_effect"], abs(r["valid_to_bad_effect"]) + abs(r["bad_to_valid_effect"])))
            lines.append(
                f"| {model} | {pair_id} | {best['module']} | {best['span']} | {best['layer']} | "
                f"{best['valid_to_bad_effect']:.3f} | {best['bad_to_valid_effect']:.3f} | {len(clean)}/{len(sub)} |"
            )
    lines += [
        "",
        "## Interpretation Guardrails",
        "",
        "- A clean direction means valid-to-bad increases the bad trace's Yes-No margin and bad-to-valid decreases the valid trace's margin.",
        "- If attention and MLP both move the margin, the result localizes below residual stream but not to a single head/neuron.",
        "- Strong effects on `problem_span` indicate surface semantics can be encoded before the reasoning trace is read; they need same-problem and paraphrase controls before mechanistic overclaiming.",
    ]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}; files={len(files)}")


if __name__ == "__main__":
    main()
