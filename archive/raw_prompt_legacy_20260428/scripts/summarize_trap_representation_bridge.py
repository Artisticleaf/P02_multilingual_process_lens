#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def fmt(x):
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="results/E08_trap_representation_bridge")
    p.add_argument("--out", default="reports/E08_trap_representation_bridge_summary.md")
    args = p.parse_args()
    files = sorted(Path(args.results_dir).glob("*_trap_representation_bridge.json"))
    lines = [
        "# E08 Trap Representation Bridge Summary",
        "",
        "Layerwise contextual target-span cosine probe for discount and derivative semantic traps. Positive margin means the query term is closer to intended/equivalent concepts than to trap concepts.",
        "",
        "## Overall Best Layers",
        "",
        "| model | best layer | mean margin | min margin |",
        "|---|---:|---:|---:|",
    ]
    contrast_lines = ["", "## Best By Contrast", "", "| model | contrast | best layer | mean margin | hard margin | pos cos | neg cos |", "|---|---|---:|---:|---:|---:|---:|"]
    token_lines = ["", "## Target Tokenization", "", "| model | case | concept | target | n toks | tokens |", "|---|---|---|---|---:|---|"]
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        model = data["model_key"]
        best = data["best_overall_layer"]
        lines.append(f"| {model} | {best['layer']} | {fmt(best['mean_contrast_margin'])} | {fmt(best['min_contrast_margin'])} |")
        for c in data["best_by_contrast"]:
            contrast_lines.append(
                f"| {model} | {c['name']} | {c['layer']} | {fmt(c['mean_margin'])} | {fmt(c['hard_margin'])} | "
                f"{fmt(c['mean_positive_cos'])} | {fmt(c['mean_negative_cos'])} |"
            )
        for t in data["tokenization"]:
            toks = " ".join(str(x).replace("|", "/") for x in t["target_tokens"][:16])
            if len(t["target_tokens"]) > 16:
                toks += " ..."
            target = t["target"].replace("|", "/")
            token_lines.append(f"| {model} | {t['id']} | {t['concept']} | {target} | {t['num_target_tokens']} | `{toks}` |")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines + contrast_lines + token_lines) + "\n", encoding="utf-8")
    print(f"wrote {out}; models={len(files)}")


if __name__ == "__main__":
    main()
