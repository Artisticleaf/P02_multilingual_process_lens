#!/usr/bin/env python3
"""No-GPU smoke for the Qwen/Gemma next-stage queue."""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT = Path(__file__).resolve().parents[1]
QUEUE = PROJECT / "configs/qwen_gemma_next_stage_queue_20260430.yaml"
PROFILES = PROJECT / "configs/qwen_gemma_parameter_profiles_20260430.yaml"
QG_AUDIT = PROJECT / "data/processed/e119_qwen_gemma_final_correct_audit_sheet_20260430.jsonl"
OUT_DIR = PROJECT / "results/E146_qwen_gemma_ng_model_card_hf_profile/_smoke"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def leakage_scan_prompt_stubs(queue: dict[str, Any]) -> dict[str, Any]:
    patterns = {
        "gold_answer": re.compile(r"Given final answer|gold answer|答案[:：]\s*\d+", re.IGNORECASE),
        "manual_label": re.compile(r"\bACPI\b|\bvalid\b|\binvalid\b|人工标签|过程无效", re.IGNORECASE),
        "trap_note": re.compile(r"\btrap\b|陷阱", re.IGNORECASE),
        "known_span": re.compile(r"known error span|错误 span|error span", re.IGNORECASE),
    }
    prompt_stub = (
        "Solve the following AIME-style problem carefully. Show the reasoning needed to justify the result. "
        "End with exactly one line `Final answer: <integer>`.\n\nProblem: <problem text only>"
    )
    hits = []
    for step in queue.get("active_steps", []):
        if "ng_model_card" not in step["id"]:
            continue
        for name, pat in patterns.items():
            if pat.search(prompt_stub):
                hits.append({"step": step["id"], "pattern": name})
    return {"hits": hits, "passed": not hits}


def main() -> None:
    queue = load_yaml(QUEUE)
    profiles = load_yaml(PROFILES)
    rows = load_jsonl(QG_AUDIT)
    errors: list[str] = []
    ids = [s["id"] for s in queue.get("active_steps", [])]
    if len(ids) != len(set(ids)):
        errors.append("duplicate active step ids")
    expected_models = {"qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"}
    profile_models = set(profiles.get("models", {}))
    if not expected_models <= profile_models:
        errors.append(f"missing model profiles: {sorted(expected_models - profile_models)}")
    model_counts = Counter(r.get("model_key") for r in rows)
    missing_qg = sorted(expected_models - set(model_counts))
    if missing_qg:
        errors.append(f"missing Qwen/Gemma E119 audit rows: {missing_qg}")
    leakage = leakage_scan_prompt_stubs(queue)
    if not leakage["passed"]:
        errors.append("prompt stub leakage scan failed")
    source_files = sorted({r.get("source_file") for r in rows if r.get("source_file")})
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "qwen_gemma_next_stage_queue_smoke",
        "queue_manifest": str(QUEUE.relative_to(PROJECT)),
        "parameter_profiles": str(PROFILES.relative_to(PROJECT)),
        "qg_audit_sheet": str(QG_AUDIT.relative_to(PROJECT)),
        "active_step_ids": ids,
        "qg_audit_rows": len(rows),
        "qg_audit_rows_by_model": dict(model_counts),
        "qg_source_files": source_files,
        "leakage_scan": leakage,
        "errors": errors,
        "passed": not errors,
        "note_zh": "No model is loaded; this smoke is safe while another GPU queue is running.",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "qwen_gemma_next_stage_queue_smoke.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "errors": errors, "out": str(out.relative_to(PROJECT))}, ensure_ascii=False, indent=2, sort_keys=True))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
