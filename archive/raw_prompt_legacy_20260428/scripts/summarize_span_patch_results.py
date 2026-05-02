#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def clean_score(row: dict) -> float:
    return float(row.get("mean_valid_to_bad_effect", 0.0)) - float(row.get("mean_bad_to_valid_effect", 0.0))


def pick_best(rows: list[dict]) -> tuple[dict | None, bool]:
    clean = [
        r
        for r in rows
        if r.get("mean_valid_to_bad_effect", 0.0) > 0 and r.get("mean_bad_to_valid_effect", 0.0) < 0
    ]
    pool = clean or rows
    if not pool:
        return None, False
    return max(pool, key=lambda r: (clean_score(r), r.get("mean_abs_effect", 0.0))), bool(clean)


def fmt(x) -> str:
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="/home/Awei/P02_multilingual_process_lens/results/E03_span_patch_hard")
    p.add_argument("--out", default="/home/Awei/P02_multilingual_process_lens/reports/E03_span_patch_hard_summary.md")
    args = p.parse_args()
    result_dir = Path(args.results_dir)
    files = sorted(result_dir.glob("*_span_patch_hard.json"))
    lines = [
        "# E03 Span Patch Hard Summary",
        "",
        "Clean means `valid->bad` increases the process-valid margin and `bad->valid` decreases it.",
        "",
        "| model | best clean span/layer | v2b | b2v | strongest trace span | strongest support/error span | rows |",
        "|---|---|---:|---:|---|---|---:|",
    ]
    details = ["", "## Per-Model Top Effects", ""]
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data.get("by_span_layer", [])
        best, is_clean = pick_best(rows)
        trace_best, trace_clean = pick_best([r for r in rows if r.get("span") == "trace_span"])
        err_best, err_clean = pick_best([r for r in rows if r.get("span") == "support_error_span"])
        def label(row, clean):
            if not row:
                return ""
            suffix = "" if clean else "*"
            return f"{row['span']} L{row['layer']}{suffix}"

        lines.append(
            "| {model} | {best_label} | {v2b} | {b2v} | {trace_label} | {err_label} | {nrows} |".format(
                model=data.get("model_key", path.stem),
                best_label=label(best, is_clean),
                v2b=fmt(best.get("mean_valid_to_bad_effect") if best else None),
                b2v=fmt(best.get("mean_bad_to_valid_effect") if best else None),
                trace_label=label(trace_best, trace_clean),
                err_label=label(err_best, err_clean),
                nrows=len(data.get("rows", [])),
            )
        )
        details.append(f"### {data.get('model_key', path.stem)}")
        details.append("")
        top = sorted(rows, key=clean_score, reverse=True)[:12]
        details.append("| span | layer | v2b | b2v | abs | clean |")
        details.append("|---|---:|---:|---:|---:|---|")
        for r in top:
            clean = r.get("mean_valid_to_bad_effect", 0) > 0 and r.get("mean_bad_to_valid_effect", 0) < 0
            details.append(
                f"| {r.get('span')} | {r.get('layer')} | {fmt(r.get('mean_valid_to_bad_effect'))} | "
                f"{fmt(r.get('mean_bad_to_valid_effect'))} | {fmt(r.get('mean_abs_effect'))} | {clean} |"
            )
        details.append("")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines + details) + "\n", encoding="utf-8")
    print(f"wrote {out}; models={len(files)}")


if __name__ == "__main__":
    main()
