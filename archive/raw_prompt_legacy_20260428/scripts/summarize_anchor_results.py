#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="/home/Awei/P02_multilingual_process_lens/results/E01_anchor_matrix")
    p.add_argument("--out", default="/home/Awei/P02_multilingual_process_lens/reports/E01_anchor_matrix_summary.md")
    args = p.parse_args()
    rows = []
    for path in sorted(Path(args.results_dir).glob("*_anchor_smoke.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        bridge_obj = data.get("contextual_bridge", {})
        bridge = bridge_obj.get("best_layer", {})
        early = bridge_obj.get("early_bridge_layer") or {}
        proc = data.get("process_verifier", {})
        patch = data.get("residual_patching", {})
        patch_layers = patch.get("by_layer", []) if isinstance(patch, dict) else []
        if patch_layers:
            desired = [
                x
                for x in patch_layers
                if x.get("mean_valid_to_bad_effect", 0.0) > 0 and x.get("mean_bad_to_valid_effect", 0.0) < 0
            ]
            pool = desired or patch_layers
            best_patch = max(
                pool,
                key=lambda x: x.get("mean_valid_to_bad_effect", float("-inf"))
                - x.get("mean_bad_to_valid_effect", 0.0),
            )
            flag = "" if desired else "*"
            patch_text = f"{flag}L{best_patch['layer']} v2b={best_patch['mean_valid_to_bad_effect']:.3f} b2v={best_patch['mean_bad_to_valid_effect']:.3f}"
        else:
            patch_text = "skipped/failed"
        rows.append(
            {
                "model": data["model_key"],
                "family": data.get("model_spec", {}).get("family"),
                "class": data.get("model_spec", {}).get("class"),
                "bridge_layer": bridge.get("layer"),
                "early_bridge": early.get("layer"),
                "bridge_top1": bridge.get("top1"),
                "bridge_margin": bridge.get("mean_hard_margin"),
                "proc_acc": proc.get("accuracy"),
                "ifc_false_accept": proc.get("invalid_final_correct_false_accept_rate"),
                "patch": patch_text,
            }
        )
    lines = ["# E01 Anchor Matrix Summary", "", "| model | family | class | best bridge | early bridge | bridge top1 | hard margin | proc acc | IFC false accept | best patch |", "|---|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for r in rows:
        lines.append(
            f"| {r['model']} | {r['family']} | {r['class']} | {r['bridge_layer']} | "
            f"{r['early_bridge'] if r['early_bridge'] is not None else ''} | "
            f"{r['bridge_top1'] if r['bridge_top1'] is not None else ''} | "
            f"{r['bridge_margin'] if r['bridge_margin'] is not None else ''} | "
            f"{r['proc_acc'] if r['proc_acc'] is not None else ''} | "
            f"{r['ifc_false_accept'] if r['ifc_false_accept'] is not None else ''} | {r['patch']} |"
        )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}; models={len(rows)}")


if __name__ == "__main__":
    main()
