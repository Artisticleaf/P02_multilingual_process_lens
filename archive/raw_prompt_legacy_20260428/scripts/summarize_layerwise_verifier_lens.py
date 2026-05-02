#!/usr/bin/env python3
"""Summarize S4 layerwise verifier logit-lens probes."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]


def load_results(paths: list[Path]) -> list[dict[str, Any]]:
    out = []
    for path in paths:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_path"] = str(path)
            out.append(data)
    return out


def group_by(rows: list[dict[str, Any]], key_fn):
    groups: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[key_fn(row)].append(row)
    return groups


def fmt(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def boundary_tag(stats: dict[str, Any], *, expected_final_positive: bool) -> str:
    final_pos = bool(stats.get("final_positive"))
    mid_pos = bool(stats.get("middle_positive"))
    drop = float(stats.get("middle_to_final_drop", 0.0))
    if mid_pos and not final_pos:
        return "mid-signal lost before output"
    if final_pos != expected_final_positive and abs(drop) >= 0.5:
        return "output/head re-entanglement candidate"
    if final_pos == expected_final_positive and mid_pos:
        return "stable positive"
    if not mid_pos and not final_pos:
        return "no positive lens signal"
    return "late-only positive"


def summarize(results: list[dict[str, Any]]) -> tuple[list[str], dict[str, Any]]:
    lines = [
        "# E25 Layerwise Verifier Lens Summary / E25 分层 verifier logit-lens 汇总",
        "",
        f"Created / 创建时间: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "The probe projects each hidden state at the verifier decision token through the final LM head. / 本 probe 将 verifier 决策位置的每层 hidden state 通过最终 LM head 投影。",
        "It is a diagnostic lens, not a trained tuned-lens or a complete circuit proof. / 它是诊断性 lens，不是训练过的 tuned-lens，也不是完整 circuit 证明。",
        "",
    ]
    aggregate: dict[str, Any] = {"models": {}}
    abs_flat = []
    con_flat = []
    for data in results:
        model = data["verifier_model_key"]
        abs_rows = data.get("absolute_rows", [])
        con_rows = data.get("contrastive_rows", [])
        aggregate["models"][model] = {
            "absolute_n": len(abs_rows),
            "contrastive_n": len(con_rows),
        }
        for row in abs_rows:
            r = dict(row)
            r["verifier_model_key"] = model
            abs_flat.append(r)
        for row in con_rows:
            r = dict(row)
            r["verifier_model_key"] = model
            con_flat.append(r)
    lines.extend(["## Absolute Yes/No Lens / 绝对 Yes/No lens", ""])
    lines.extend(
        [
            "| verifier | slice | n | final positive rate | middle positive rate | mean middle->final drop | note |",
            "|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for key, group in sorted(group_by(abs_flat, lambda r: (r["verifier_model_key"], "ACPI" if r.get("is_acpi") else "non-ACPI")).items()):
        model, slice_name = key
        final_pos = mean(1.0 if r["stats"].get("final_positive") else 0.0 for r in group)
        mid_pos = mean(1.0 if r["stats"].get("middle_positive") else 0.0 for r in group)
        drop = mean(float(r["stats"].get("middle_to_final_drop", 0.0)) for r in group)
        note = "ACPI over-accept risk" if slice_name == "ACPI" and final_pos > 0.5 else ""
        lines.append(f"| {model} | {slice_name} | {len(group)} | {final_pos:.3f} | {mid_pos:.3f} | {drop:.3f} | {note} |")
    lines.extend(["", "### Absolute Rows / 绝对式逐行", ""])
    lines.extend(
        [
            "| verifier | idx | risk | prompt | target valid | final margin | middle best | middle layer | tag |",
            "|---|---:|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in sorted(abs_flat, key=lambda r: (r["verifier_model_key"], int(r["audit_idx"]), r["prompt_lang"])):
        st = row["stats"]
        expected = bool(row["target_process_valid"])
        lines.append(
            f"| {row['verifier_model_key']} | {row['audit_idx']} | {row.get('manual_risk','')} | {row['prompt_lang']} | "
            f"{expected} | {fmt(st.get('final_margin'))} | {fmt(st.get('middle_best_margin'))} | "
            f"{fmt(st.get('middle_best_layer'))} | {boundary_tag(st, expected_final_positive=expected)} |"
        )
    lines.extend(["", "## Contrastive A/B Lens / 对比式 A/B lens", ""])
    lines.extend(
        [
            "| verifier | pair | n | final target-positive rate | middle target-positive rate | mean middle->final drop |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for key, group in sorted(group_by(con_flat, lambda r: (r["verifier_model_key"], r["pair_id"])).items()):
        model, pair = key
        final_pos = mean(1.0 if r["stats"].get("final_positive") else 0.0 for r in group)
        mid_pos = mean(1.0 if r["stats"].get("middle_positive") else 0.0 for r in group)
        drop = mean(float(r["stats"].get("middle_to_final_drop", 0.0)) for r in group)
        lines.append(f"| {model} | {pair} | {len(group)} | {final_pos:.3f} | {mid_pos:.3f} | {drop:.3f} |")
    lines.extend(["", "### Contrastive Rows / 对比式逐行", ""])
    lines.extend(
        [
            "| verifier | pair | prompt | order | final margin | middle best | middle layer | tag |",
            "|---|---|---|---|---:|---:|---:|---|",
        ]
    )
    for row in sorted(con_flat, key=lambda r: (r["verifier_model_key"], r["pair_id"], r["prompt_lang"], r["order"])):
        st = row["stats"]
        lines.append(
            f"| {row['verifier_model_key']} | {row['pair_id']} | {row['prompt_lang']} | {row['order']} | "
            f"{fmt(st.get('final_margin'))} | {fmt(st.get('middle_best_margin'))} | "
            f"{fmt(st.get('middle_best_layer'))} | {boundary_tag(st, expected_final_positive=True)} |"
        )
    aggregate["absolute_n"] = len(abs_flat)
    aggregate["contrastive_n"] = len(con_flat)
    return lines, aggregate


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default=str(PROJECT / "results/E25_layerwise_verifier_lens"))
    p.add_argument("--out-md", default=str(PROJECT / "reports/E25_layerwise_verifier_lens_summary.md"))
    p.add_argument("--out-json", default=str(PROJECT / "results/E25_layerwise_verifier_lens/summary.json"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    paths = sorted(Path(args.results_dir).glob("*_layerwise_verifier_lens.json"))
    results = load_results(paths)
    lines, aggregate = summarize(results)
    Path(args.out_md).write_text("\n".join(lines), encoding="utf-8")
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps({"aggregate": aggregate, "inputs": [str(p) for p in paths]}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {args.out_md} and {args.out_json}")


if __name__ == "__main__":
    main()
