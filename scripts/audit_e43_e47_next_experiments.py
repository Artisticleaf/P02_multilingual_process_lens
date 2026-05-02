#!/usr/bin/env python3
"""Integrity audit for E43-E47 pilot experiments."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parents[1]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    issues = []
    checks = {}

    e43_rows = read_jsonl(PROJECT / "data/processed/e43_paraphrase_transfer_20260428.jsonl")
    pair_cfg = yaml.safe_load((PROJECT / "configs/e43_paraphrase_transfer_pairs.yaml").read_text(encoding="utf-8"))["pairs"]
    counts = Counter((r["task_id"], r["paraphrase_tag"], r["manual_process_valid"]) for r in e43_rows)
    span_ok = True
    for p in pair_cfg:
        valid = next(r for r in e43_rows if r["audit_idx"] == p["valid_idx"])
        bad = next(r for r in e43_rows if r["audit_idx"] == p["bad_idx"])
        span_ok = span_ok and p["support_span"] in valid["completion"] and p["error_span"] in bad["completion"]
    e43_data_ok = len(e43_rows) == 24 and len(pair_cfg) == 12 and all(v == 1 for v in counts.values()) and span_ok
    checks["e43_data"] = {"rows": len(e43_rows), "pairs": len(pair_cfg), "balanced_cells": len(counts), "span_ok": span_ok, "ok": e43_data_ok}
    if not e43_data_ok:
        issues.append("e43_data")

    e43_results = {}
    for key, expected_chat in [("qwen35_9b", True), ("qwen3_14b_base", False)]:
        paths = sorted((PROJECT / "results/E43_paraphrase_transfer_patch").glob(f"{key}_e43_paraphrase_transfer_*.json"))
        if not paths:
            e43_results[key] = {"ok": False, "missing": True}
            issues.append(f"e43_result:{key}")
            continue
        d = read_json(paths[-1])
        ok = d.get("used_chat_template") == expected_chat and d.get("add_special_tokens") is (not expected_chat) and len(d.get("rows", [])) > 0
        controls = {s["control"] for s in d.get("summary", [])}
        ok = ok and controls == {"same_family", "mismatched_family"}
        e43_results[key] = {"path": str(paths[-1]), "used_chat_template": d.get("used_chat_template"), "add_special_tokens": d.get("add_special_tokens"), "rows": len(d.get("rows", [])), "controls": sorted(controls), "ok": ok}
        if not ok:
            issues.append(f"e43_result:{key}")
    checks["e43_results"] = e43_results

    e44_results = {}
    for key, expected_chat in [
        ("qwen35_9b", True),
        ("qwen35_27b", True),
        ("qwen3_14b_base", False),
        ("gemma4_31b_it", True),
        ("gemma4_26b_a4b_it", True),
    ]:
        paths = sorted((PROJECT / "results/E44_mlp_direction_steering").glob(f"{key}_e44_mlp_direction_steering_*.json"))
        if not paths:
            e44_results[key] = {"ok": False, "missing": True}
            issues.append(f"e44_result:{key}")
            continue
        d = read_json(paths[-1])
        heldout = {r["heldout_task"] for r in d.get("rows", [])}
        controls = {r["control"] for r in d.get("rows", [])}
        ok = d.get("used_chat_template") == expected_chat and d.get("add_special_tokens") is (not expected_chat) and len(heldout) == 6 and {"process_direction", "random_same_norm", "opposite_direction"}.issubset(controls)
        e44_results[key] = {"path": str(paths[-1]), "used_chat_template": d.get("used_chat_template"), "add_special_tokens": d.get("add_special_tokens"), "rows": len(d.get("rows", [])), "heldout_tasks": sorted(heldout), "controls": sorted(controls), "ok": ok}
        if not ok:
            issues.append(f"e44_result:{key}")
    checks["e44_results"] = e44_results

    gen_results = {}
    gen_paths = sorted((PROJECT / "results/E46_E47_conditioned_generation").glob("*.json"))
    required_prefixes = ["e46_qwen35_27b", "e46_gemma4_31b_it", "e47_qwen35_27b"]
    for prefix in required_prefixes:
        if not any(p.name.startswith(prefix) for p in gen_paths):
            issues.append(f"generation_missing:{prefix}")
    for path in gen_paths:
        name = path.stem
        d = read_json(path)
        rows = d["rows"]
        # Chat models should use rendered templates without adding special tokens twice.
        chat_ok = all(r["used_chat_template"] and not r["add_special_tokens"] for r in rows)
        final_consistent = all((r["manual_final_correct"] and r["extracted_final"]) or (not r["manual_final_correct"]) for r in rows)
        gold_in_prompt = sum(bool(r.get("gold_answer_in_prompt", False)) for r in rows)
        natural_no_gold_ok = gold_in_prompt == 0 or "answer_anchor" in name
        # E46 prompts are generated inside the script from problem only; known error spans are not prompt inputs.
        gen_results[name] = {
            "path": str(path),
            "summary": d["summary"],
            "chat_tokenization_ok": chat_ok,
            "final_flags_consistent": final_consistent,
            "gold_answer_in_prompt_rows": gold_in_prompt,
            "natural_no_gold_ok_or_answer_anchor": natural_no_gold_ok,
            "ok": chat_ok and final_consistent and natural_no_gold_ok,
        }
        if not (chat_ok and final_consistent):
            issues.append(f"generation:{name}")
        if not natural_no_gold_ok:
            issues.append(f"gold_leakage:{name}")
    checks["generation_results"] = gen_results

    out = {"passed": not issues, "issues": issues, "checks": checks}
    out_path = PROJECT / "logs/audit_e43_e47_next_experiments_20260428.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": out["passed"], "issues": issues, "out": str(out_path)}, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
