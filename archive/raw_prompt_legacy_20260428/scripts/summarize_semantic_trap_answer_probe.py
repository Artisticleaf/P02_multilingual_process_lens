#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def fmt(x):
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="results/E07_semantic_trap_answer_probe")
    p.add_argument("--out", default="reports/E07_semantic_trap_answer_probe_summary.md")
    args = p.parse_args()
    files = sorted(Path(args.results_dir).glob("*_semantic_trap_answer_probe.json"))
    lines = [
        "# E07 Semantic Trap Answer Probe Summary",
        "",
        "This probe scores candidate final answers without generation. Primary metric uses per-token average logprob to reduce length bias.",
        "",
        "## Overall",
        "",
        "| model | n | acc avg | acc sum | mean gold-vs-best-wrong avg | mean gold-vs-best-wrong sum |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    details = ["", "## Most Negative Gold Margins", "", "| model | task | route | gold | pred avg | margin avg | trap |", "|---|---|---|---|---|---:|---|"]
    route_lines = ["", "## Route Slices", "", "| model | slice | n | acc avg | margin avg |", "|---|---|---:|---:|---:|"]
    task_lines = ["", "## Task Slices", "", "| model | task | n | acc avg | margin avg |", "|---|---|---:|---:|---:|"]
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        model = data["model_key"]
        overall = next(s for s in data["summary"] if s["slice_type"] == "all")
        lines.append(
            f"| {model} | {overall['n']} | {fmt(overall['acc_avg'])} | {fmt(overall['acc_sum'])} | "
            f"{fmt(overall['mean_gold_minus_best_wrong_avg'])} | {fmt(overall['mean_gold_minus_best_wrong_sum'])} |"
        )
        for s in data["summary"]:
            if s["slice_type"] == "route":
                route_lines.append(f"| {model} | {s['slice']} | {s['n']} | {fmt(s['acc_avg'])} | {fmt(s['mean_gold_minus_best_wrong_avg'])} |")
            if s["slice_type"] == "task":
                task_lines.append(f"| {model} | {s['slice']} | {s['n']} | {fmt(s['acc_avg'])} | {fmt(s['mean_gold_minus_best_wrong_avg'])} |")
        worst = sorted(data["rows"], key=lambda r: r["gold_minus_best_wrong_avg"])[:18]
        for r in worst:
            details.append(
                f"| {model} | {r['task_id']} | {r['input_lang']}->{r['reason_lang']} | {r['gold_answer']} | "
                f"{r['pred_avg']} | {fmt(r['gold_minus_best_wrong_avg'])} | {str(r.get('trap','')).replace('|','/')} |"
            )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines + route_lines + task_lines + details) + "\n", encoding="utf-8")
    print(f"wrote {out}; models={len(files)}")


if __name__ == "__main__":
    main()
