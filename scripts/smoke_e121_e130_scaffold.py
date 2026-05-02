#!/usr/bin/env python3
"""No-GPU smoke for E121-E130 next-stage scaffolds."""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT = Path(__file__).resolve().parents[1]
MANIFEST = PROJECT / "configs/e121_e130_next_stage_manifest.yaml"
OUT_DIR = PROJECT / "results/E121_E130_scaffold_smoke"


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def build_prompt_stubs(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    sample_problem = "Find the sum of all integer bases b>9 for which 17_b divides 97_b."
    sample_trace = "17_b=b+7 and 97_b=9b+7. Since b+7 divides 9b+7, b+7 divides 56. Thus b=21 or 49, sum 70."
    stubs = []
    for exp in manifest["experiments"]:
        eid = exp["id"]
        mode = exp["mode"]
        if mode in {"DV", "TV", "MI_DV"}:
            prompt = (
                "Judge the visible reasoning trace. Do not use hidden annotations.\n"
                f"Problem: {sample_problem}\nTrace: {sample_trace}\n"
                "Final decision:"
            )
        elif mode in {"NG", "TG"}:
            prompt = (
                "Solve the following problem. End with exactly one line `Final answer: <integer>`.\n\n"
                f"Problem: {sample_problem}"
            )
        else:
            prompt = f"Post-hoc analysis placeholder for {eid}; no model prompt."
        stubs.append({"id": eid, "mode": mode, "prompt_stub": prompt})
    return stubs


def leakage_scan(stubs: list[dict[str, Any]]) -> dict[str, Any]:
    leak_patterns = {
        "gold_label_terms": re.compile(r"\b(valid|invalid|ACPI|label)\b", re.IGNORECASE),
        "known_trap_terms": re.compile(r"\btrap\b|陷阱", re.IGNORECASE),
    }
    counts = Counter()
    hits = []
    for stub in stubs:
        prompt = stub["prompt_stub"]
        for name, pattern in leak_patterns.items():
            if pattern.search(prompt):
                counts[name] += 1
                hits.append({"id": stub["id"], "pattern": name})
    return {"counts": dict(counts), "hits": hits, "passed": not hits}


def main() -> None:
    manifest = load_yaml(MANIFEST)
    ids = [e["id"] for e in manifest["experiments"]]
    modes = [e["mode"] for e in manifest["experiments"]]
    errors = []
    if len(ids) != len(set(ids)):
        errors.append("duplicate experiment ids")
    allowed_modes = {"DV", "TV", "NG", "TG", "MI_DV", "MI_TG", "PM"}
    unknown_modes = sorted(set(modes) - allowed_modes)
    if unknown_modes:
        errors.append(f"unknown modes: {unknown_modes}")
    stubs = build_prompt_stubs(manifest)
    leak = leakage_scan(stubs)
    # Prompt stubs deliberately contain no answer and no manual label.  The word
    # "label" appears only if a future template accidentally leaks rubric labels.
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "E121_E130_scaffold_smoke",
        "manifest": str(MANIFEST.relative_to(PROJECT)),
        "n_experiments": len(ids),
        "ids": ids,
        "mode_counts": dict(Counter(modes)),
        "prompt_stubs": stubs,
        "leakage_scan": leak,
        "errors": errors,
        "passed": not errors and leak["passed"],
        "note_zh": "No model loaded; safe to run while E119 occupies GPUs.",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "e121_e130_scaffold_smoke.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "out": str(out.relative_to(PROJECT)), "errors": errors, "leakage": leak}, ensure_ascii=False, indent=2, sort_keys=True))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
