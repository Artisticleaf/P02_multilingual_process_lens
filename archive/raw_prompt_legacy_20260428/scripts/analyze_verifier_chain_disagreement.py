#!/usr/bin/env python3
"""Join absolute verifier and contrastive verifier evidence."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fmt(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manual-jsonl", default="data/processed/manual_e05_audit_combined_20260427.jsonl")
    p.add_argument("--absolute-dir", default="results/E06_e05_manual_trace_verifier")
    p.add_argument("--contrastive-dir", default="results/E12_contrastive_acpi_verifier")
    p.add_argument("--out-json", default="results/E15_verifier_chain/verifier_chain_disagreement.json")
    p.add_argument("--out-report", default="reports/E15_verifier_chain_disagreement_summary.md")
    args = p.parse_args()

    manual_rows = load_jsonl(Path(args.manual_jsonl))
    manual_by_idx = {r["e05_idx"]: r for r in manual_rows}
    abs_rows = []
    for path in sorted(Path(args.absolute_dir).glob("*_manual_trace_verifier.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for r in data.get("rows", []):
            idx = r.get("audit_idx")
            # Older E06 used audit_idx == e05_idx for this label file.
            m = manual_by_idx.get(idx)
            if not m:
                continue
            abs_rows.append({**r, "verifier_model_key": data["verifier_model_key"], "e05_idx": idx})
    con_rows = []
    for path in sorted(Path(args.contrastive_dir).glob("*_contrastive_acpi_verifier.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for r in data.get("rows", []):
            con_rows.append({**r, "verifier_model_key": data["verifier_model_key"]})

    # Absolute process-only decisions on the bad rows used by contrastive pairs.
    abs_keyed = defaultdict(list)
    for r in abs_rows:
        if r["mode"] == "process_only":
            abs_keyed[(r["verifier_model_key"], r["e05_idx"])].append(r)

    contrastive_join = []
    for r in con_rows:
        bad_idx = r["bad_idx"]
        bad = manual_by_idx.get(bad_idx, {})
        abs_for_bad = abs_keyed.get((r["verifier_model_key"], bad_idx), [])
        false_accept_prompts = [a for a in abs_for_bad if a.get("pred") is True]
        mean_abs_margin = (
            sum(a["yes_minus_no_logprob"] for a in abs_for_bad) / len(abs_for_bad) if abs_for_bad else None
        )
        contrastive_join.append(
            {
                **r,
                "bad_manual_risk": bad.get("manual_risk"),
                "bad_paper_grade_acpi": bad.get("paper_grade_acpi"),
                "absolute_process_prompts": len(abs_for_bad),
                "absolute_false_accept_prompts": len(false_accept_prompts),
                "absolute_mean_yes_minus_no": mean_abs_margin,
            }
        )

    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in contrastive_join:
        for key in [
            ("verifier", r["verifier_model_key"]),
            ("pair", r["pair_id"]),
            ("risk", r.get("bad_manual_risk", "")),
            ("all", "all"),
        ]:
            groups[key].append(r)
    summary = []
    for (slice_type, slice_name), g in sorted(groups.items()):
        with_abs = [r for r in g if r["absolute_process_prompts"]]
        summary.append(
            {
                "slice_type": slice_type,
                "slice": slice_name,
                "n": len(g),
                "contrastive_acc": sum(r["correct"] for r in g) / len(g),
                "contrastive_mean_margin": sum(r["margin_target_minus_other"] for r in g) / len(g),
                "absolute_bad_false_accept_rate": (
                    sum(r["absolute_false_accept_prompts"] > 0 for r in with_abs) / len(with_abs) if with_abs else None
                ),
                "absolute_mean_bad_margin": (
                    sum(r["absolute_mean_yes_minus_no"] for r in with_abs if r["absolute_mean_yes_minus_no"] is not None) / len(with_abs)
                    if with_abs
                    else None
                ),
            }
        )

    result = {
        "manual_jsonl": args.manual_jsonl,
        "absolute_files": [str(p) for p in sorted(Path(args.absolute_dir).glob("*_manual_trace_verifier.json"))],
        "contrastive_files": [str(p) for p in sorted(Path(args.contrastive_dir).glob("*_contrastive_acpi_verifier.json"))],
        "summary": summary,
        "rows": contrastive_join,
    }
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# E15 Verifier Chain Disagreement Summary",
        "",
        "This joins E06 absolute Yes/No process verification with E12 pairwise contrastive verification on the same bad traces.",
        "",
        "## Summary",
        "",
        "| slice type | slice | n | contrastive acc | contrastive margin | abs bad false-accept | abs bad margin |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for s in summary:
        if s["slice_type"] in {"all", "verifier", "pair"}:
            lines.append(
                f"| {s['slice_type']} | {s['slice']} | {s['n']} | {fmt(s['contrastive_acc'])} | "
                f"{fmt(s['contrastive_mean_margin'])} | {fmt(s['absolute_bad_false_accept_rate'])} | {fmt(s['absolute_mean_bad_margin'])} |"
            )
    lines.extend(
        [
            "",
            "## Key Joined Rows",
            "",
            "| verifier | pair | prompt | order | target | pred | contrast margin | abs false prompts | abs mean margin | risk |",
            "|---|---|---|---|---|---|---:|---:|---:|---|",
        ]
    )
    for r in sorted(contrastive_join, key=lambda x: (x["verifier_model_key"], x["pair_id"], x["prompt_lang"], x["order"])):
        lines.append(
            f"| {r['verifier_model_key']} | {r['pair_id']} | {r['prompt_lang']} | {r['order']} | {r['target']} | {r['pred']} | "
            f"{fmt(r['margin_target_minus_other'])} | {r['absolute_false_accept_prompts']} | {fmt(r['absolute_mean_yes_minus_no'])} | {r['bad_manual_risk']} |"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- A positive contrastive result together with absolute false-accept means the verifier can sometimes see the process difference when forced to compare siblings, but the absolute objective/threshold accepts the bad trace.",
            "- Rows with both contrastive failure and absolute false-accept are the best candidates for mechanistic probing or manual prompt redesign.",
            "- Qwen3.5 absolute E06 may still be running; this report should be regenerated after that file lands.",
        ]
    )
    out_report = Path(args.out_report)
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_json}; joined_rows={len(contrastive_join)}")
    print(f"wrote {out_report}")


if __name__ == "__main__":
    main()
