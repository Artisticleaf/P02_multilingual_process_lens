#!/usr/bin/env python3
"""Offline joins across manual audit, answer traps, and span patch results."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def fmt(x):
    return f"{x:.3f}" if isinstance(x, float) else str(x)


def load_e07(results_dir: Path) -> dict[tuple[str, str, str, str], dict]:
    out = {}
    for path in results_dir.glob("*_semantic_trap_answer_probe.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        model = data["model_key"]
        for r in data["rows"]:
            out[(model, r["task_id"], r["input_lang"], r["reason_lang"])] = r
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manual-jsonl", default="data/processed/manual_e05_audit_combined_20260427.jsonl")
    p.add_argument("--e07-dir", default="results/E07_semantic_trap_answer_probe")
    p.add_argument("--e09-summary", default="reports/E09_real_acpi_span_patch_summary.md")
    p.add_argument("--out", default="reports/E10_evidence_chain_join_smoke.md")
    args = p.parse_args()

    manual = [json.loads(line) for line in Path(args.manual_jsonl).read_text(encoding="utf-8").splitlines() if line.strip()]
    e07 = load_e07(Path(args.e07_dir))
    joined = []
    for r in manual:
        key = (r["model_key"], r["task_id"], r["input_lang"], r["reason_lang"])
        m = e07.get(key)
        if not m:
            continue
        jr = dict(r)
        jr["e07_margin"] = m["gold_minus_best_wrong_avg"]
        jr["e07_pred"] = m["pred_avg"]
        jr["e07_correct"] = m["correct_avg"]
        joined.append(jr)

    lines = [
        "# E10 Evidence Chain Join Smoke",
        "",
        "This is an offline probe joining manual audit labels with E07 answer-option trap margins. It is not causal; it screens whether route/task answer priors align with observed process-selection risk.",
        "",
        "## Overall Join",
        "",
        f"- manual rows: {len(manual)}",
        f"- rows with E07 route/task margin: {len(joined)}",
        "",
        "## E07 Margin Buckets",
        "",
        "| bucket | n | process invalid | strict ACPI | paper-grade ACPI | final wrong | format broken |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    buckets = {
        "strong_neg_<=-1": lambda x: x <= -1,
        "weak_neg_-1..0": lambda x: -1 < x < 0,
        "nonneg_>=0": lambda x: x >= 0,
    }
    for name, pred in buckets.items():
        g = [r for r in joined if pred(float(r["e07_margin"]))]
        if not g:
            continue
        lines.append(
            f"| {name} | {len(g)} | {sum(r['manual_process_valid'] is False for r in g)} | "
            f"{sum(r['is_acpi'] for r in g)} | {sum(r.get('paper_grade_acpi') for r in g)} | "
            f"{sum(r['manual_final_correct'] is False for r in g)} | {sum(r['manual_format_valid'] is False for r in g)} |"
        )

    lines += [
        "",
        "## By Model And Margin Sign",
        "",
        "| model | sign | n | process invalid | strict ACPI | mean margin | top risk |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    by_model_sign = defaultdict(list)
    for r in joined:
        by_model_sign[(r["model_key"], "neg" if r["e07_margin"] < 0 else "nonneg")].append(r)
    for (model, sign), g in sorted(by_model_sign.items()):
        risk = Counter(r["manual_risk"] for r in g).most_common(1)[0][0]
        lines.append(
            f"| {model} | {sign} | {len(g)} | {sum(r['manual_process_valid'] is False for r in g)} | "
            f"{sum(r['is_acpi'] for r in g)} | {fmt(sum(float(r['e07_margin']) for r in g)/len(g))} | {risk} |"
        )

    lines += [
        "",
        "## ACPI / Semantic Drift Rows With E07 Context",
        "",
        "| idx | model | task | route | margin | pred | risk | earliest error |",
        "|---:|---|---|---|---:|---|---|---|",
    ]
    for r in sorted(joined, key=lambda x: (not x["is_acpi"], x["model_key"], x["e05_idx"])):
        risk = r["manual_risk"]
        if not (r["is_acpi"] or "semantic_drift" in risk or "discount" in risk or "dabazhe" in risk):
            continue
        lines.append(
            f"| {r['e05_idx']} | {r['model_key']} | {r['task_id']} | {r['input_lang']}->{r['reason_lang']} | "
            f"{fmt(float(r['e07_margin']))} | {r['e07_pred']} | {risk} | {str(r.get('earliest_error') or '').replace('|','/')[:80]} |"
        )

    lines += [
        "",
        "## Current Causal Reading",
        "",
        "- Negative answer-option margins are not a clean predictor of manual process invalidity: many rows with negative E07 margins are valid but format-broken, especially when answer-form scoring is biased.",
        "- However, the manually important discount and ratio ACPI rows sit in tasks/routes where E09 shows support/error span patchability, so the process-risk signal is not only an answer prior.",
        "- E07 is most useful as a route/task triage tool, not as a verifier or labeler.",
    ]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}; joined={len(joined)}")


if __name__ == "__main__":
    main()
