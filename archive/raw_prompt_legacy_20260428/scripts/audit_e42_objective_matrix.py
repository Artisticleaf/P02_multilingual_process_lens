#!/usr/bin/env python3
"""Audit E42 objective-matrix data and result integrity."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
EXPECTED_MODELS = {"qwen35_9b", "qwen3_14b_base", "qwen35_27b", "gemma4_31b_it"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--e39-jsonl", default=str(PROJECT / "data/processed/e39_surface_semantic_generalization_20260428.jsonl"))
    p.add_argument("--focus-jsonl", default=str(PROJECT / "data/processed/e42_e39_objective_focus_20260428.jsonl"))
    p.add_argument("--absolute-dir", default=str(PROJECT / "results/E39_surface_semantic_generalization_absolute_verifier"))
    p.add_argument("--contrastive-dir", default=str(PROJECT / "results/E42_e39_objective_matrix_contrastive"))
    p.add_argument("--error-dir", default=str(PROJECT / "results/E42_e39_objective_matrix_error_span"))
    p.add_argument("--summary-json", default=str(PROJECT / "results/E42_e39_objective_matrix_summary/summary.json"))
    p.add_argument("--out", default=str(PROJECT / "logs/audit_e42_objective_matrix_20260428.json"))
    args = p.parse_args()

    issues: list[str] = []
    e39 = load_jsonl(Path(args.e39_jsonl))
    focus = load_jsonl(Path(args.focus_jsonl))
    by_idx = {r["audit_idx"]: r for r in e39}

    if len(e39) != 72:
        issues.append(f"E39 row count expected 72, got {len(e39)}")
    if len(focus) != 24:
        issues.append(f"E42 focus row count expected 24, got {len(focus)}")
    if len({r["audit_idx"] for r in focus}) != len(focus):
        issues.append("E42 focus audit_idx duplicates")

    task_variants: dict[str, set[str]] = defaultdict(set)
    for r in focus:
        task_variants[r["task_id"]].add(r["e39_variant"])
        if r["audit_idx"] not in by_idx:
            issues.append(f"Focus idx not in E39: {r['audit_idx']}")
    if len(task_variants) != 12:
        issues.append(f"Expected 12 focus tasks, got {len(task_variants)}")
    for task, variants in sorted(task_variants.items()):
        if variants != {"valid_correct", "invalid_correct"}:
            issues.append(f"Task {task} variants wrong: {sorted(variants)}")

    for task in sorted(task_variants):
        rows = [r for r in focus if r["task_id"] == task]
        valid = next((r for r in rows if r["e39_variant"] == "valid_correct"), None)
        bad = next((r for r in rows if r["e39_variant"] == "invalid_correct"), None)
        if not valid or not bad:
            continue
        if valid["problem"] != bad["problem"]:
            issues.append(f"Problem mismatch: {task}")
        if valid["manual_process_valid"] is not True or bad["manual_process_valid"] is not False:
            issues.append(f"Process labels mismatch: {task}")
        if valid["manual_final_correct"] is not True or bad["manual_final_correct"] is not True:
            issues.append(f"Final-correct labels mismatch: {task}")
        if bad["is_acpi"] is not True or valid["is_acpi"] is not False:
            issues.append(f"ACPI labels mismatch: {task}")
        if valid.get("support_span") and valid["support_span"] not in valid["completion"]:
            issues.append(f"Support span absent from valid completion: {task}")
        if bad.get("error_span") and bad["error_span"] not in bad["completion"]:
            issues.append(f"Error span absent from bad completion: {task}")

    abs_files = sorted(Path(args.absolute_dir).glob("*_manual_trace_verifier.json"))
    con_files = sorted(Path(args.contrastive_dir).glob("*_e42_contrastive_objective.json"))
    err_files = sorted(Path(args.error_dir).glob("*_error_span_extraction_verifier.json"))
    found_abs, found_con, found_err = set(), set(), set()
    for f in abs_files:
        data = load_json(f)
        model = data.get("verifier_model_key")
        found_abs.add(model)
        if data.get("num_manual_rows") != 72:
            issues.append(f"Absolute {model} expected 72 manual rows, got {data.get('num_manual_rows')}")
        if data.get("num_eval_rows") != 288:
            issues.append(f"Absolute {model} expected 288 eval rows, got {data.get('num_eval_rows')}")
    for f in con_files:
        data = load_json(f)
        model = data.get("verifier_model_key")
        found_con.add(model)
        if len(data.get("rows", [])) != 48:
            issues.append(f"Contrastive {model} expected 48 rows, got {len(data.get('rows', []))}")
        counts = Counter((r["prompt_lang"], r["order"]) for r in data.get("rows", []))
        for lang in ["en", "zh"]:
            for order in ["bad_A", "bad_B"]:
                if counts[(lang, order)] != 12:
                    issues.append(f"Contrastive {model} count {lang}/{order} = {counts[(lang, order)]}")
    for f in err_files:
        data = load_json(f)
        model = data.get("verifier_model_key")
        found_err.add(model)
        if data.get("num_manual_rows") != 24:
            issues.append(f"Error-span {model} expected 24 manual rows, got {data.get('num_manual_rows')}")
        if data.get("num_eval_rows") != 96:
            issues.append(f"Error-span {model} expected 96 eval rows, got {data.get('num_eval_rows')}")
        for r in data.get("rows", []):
            if r.get("known_error_spans") and by_idx[r["audit_idx"]]["e39_variant"] == "valid_correct":
                issues.append(f"Valid row has known error spans in result: {model} {r['audit_idx']}")

    for name, found in [("absolute", found_abs), ("contrastive", found_con), ("error_span", found_err)]:
        missing = EXPECTED_MODELS - found
        if missing:
            issues.append(f"Missing {name} models: {sorted(missing)}")

    summary = load_json(Path(args.summary_json))
    agg = summary.get("aggregate", {})
    if not {"absolute", "contrastive", "error_span", "task_rows"}.issubset(agg):
        issues.append("Summary JSON missing aggregate sections")

    # Leakage/logic audit: scoring labels are used only after generation. The raw result rows should not store prompts.
    prompt_keys = []
    for f in con_files + err_files:
        data = load_json(f)
        for r in data.get("rows", []):
            prompt_keys.extend([k for k in r if "prompt" in k.lower() and k not in {"prompt_lang"}])
    if prompt_keys:
        issues.append(f"Unexpected prompt-like keys stored in result rows: {sorted(set(prompt_keys))}")

    out = {
        "passed": not issues,
        "issues": issues,
        "counts": {
            "e39_rows": len(e39),
            "focus_rows": len(focus),
            "tasks": len(task_variants),
            "absolute_files": len(abs_files),
            "contrastive_files": len(con_files),
            "error_span_files": len(err_files),
        },
        "found_models": {
            "absolute": sorted(found_abs),
            "contrastive": sorted(found_con),
            "error_span": sorted(found_err),
        },
        "leakage_logic_note": "Known error spans are used only for post-hoc scoring; prompts are generated from problem/completion only, and result rows do not store prompt text.",
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
