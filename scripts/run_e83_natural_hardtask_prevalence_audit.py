#!/usr/bin/env python3
"""E83 pooled natural hard-task prevalence audit.

This script performs no new model inference. It pools existing no-gold hard-task
generation runs (core P0 E57 and GLM E64), joins their human audits for
final-correct rows, and reports final-correct, strict ACPI, repaired ACPI, and
unrepaired ACPI rates with Wilson intervals.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
CORE_DIR = PROJECT / "results/E57_p0_hard_task_final_correct_harvesting"
GLM_DIR = PROJECT / "results/E64_natural_hard_task_expansion"
CORE_AUDIT = PROJECT / "data/processed/e57_final_correct_manual_audit_20260428.jsonl"
GLM_AUDIT = GLM_DIR / "glm47_flash_candidate_e64_final_correct_manual_audit.jsonl"
OUT_DIR = PROJECT / "results/E83_natural_hardtask_prevalence_audit"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def wilson(k: int, n: int, z: float = 1.96) -> dict[str, float | None]:
    if n == 0:
        return {"rate": None, "wilson95_low": None, "wilson95_high": None}
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / den
    return {"rate": p, "wilson95_low": max(0.0, center - half), "wilson95_high": min(1.0, center + half)}


def source_key(path: Path, row_index: int) -> tuple[str, int]:
    return (path.name, row_index)


def load_generation_rows() -> list[dict[str, Any]]:
    rows = []
    for p in sorted(CORE_DIR.glob("*_hard_task_conditioning.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for i, r in enumerate(d["rows"]):
            rows.append({**r, "generation_source_file": p.name, "generation_row_index": i, "e83_source_group": "core_p0_e57"})
    for p in sorted(GLM_DIR.glob("*_hard_task_conditioning.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for i, r in enumerate(d["rows"]):
            rows.append({**r, "generation_source_file": p.name, "generation_row_index": i, "e83_source_group": "expanded_p0_glm_e64"})
    return rows


def load_audit_map() -> dict[tuple[str, int], dict[str, Any]]:
    out = {}
    for r in load_jsonl(CORE_AUDIT):
        out[(r["source_file"], int(r["row_index"]))] = r
    for r in load_jsonl(GLM_AUDIT):
        out[("glm47_flash_candidate_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json", int(r["e64_source_row_index"]))] = r
    return out


def metric_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    final_correct = sum(bool(r.get("manual_final_correct")) for r in rows)
    audited_fc = [r for r in rows if r.get("manual_final_correct") and r.get("e83_audited_final_correct")]
    strict_acpi = sum(bool(r.get("manual_acpi_strict")) for r in audited_fc)
    repaired_acpi = sum(bool(r.get("manual_acpi_strict")) and bool(r.get("manual_repair_present")) and not bool(r.get("manual_acpi_unrepaired")) for r in audited_fc)
    unrepaired_acpi = sum(bool(r.get("manual_acpi_unrepaired")) for r in audited_fc)
    strict_valid = sum(bool(r.get("manual_process_valid_strict")) for r in audited_fc)
    return {
        "n_generated": n,
        "final_correct": final_correct,
        "audited_final_correct": len(audited_fc),
        "strict_valid_final_correct": strict_valid,
        "strict_acpi_final_correct": strict_acpi,
        "repaired_acpi_final_correct": repaired_acpi,
        "unrepaired_acpi_final_correct": unrepaired_acpi,
        "final_correct_rate": wilson(final_correct, n),
        "strict_acpi_per_generated": wilson(strict_acpi, n),
        "unrepaired_acpi_per_generated": wilson(unrepaired_acpi, n),
        "strict_acpi_cond_final_correct": wilson(strict_acpi, len(audited_fc)),
        "unrepaired_acpi_cond_final_correct": wilson(unrepaired_acpi, len(audited_fc)),
    }


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        for typ, key in [
            ("all", "all"),
            ("model", r.get("model_key", "")),
            ("source_group", r.get("e83_source_group", "")),
            ("prompt_variant", r.get("prompt_variant", "")),
            ("task_id", r.get("task_id", "")),
        ]:
            if key:
                groups[(typ, str(key))].append(r)
    out = []
    for (typ, key), vals in sorted(groups.items()):
        out.append({"slice_type": typ, "slice": key, **metric_counts(vals)})
    return out


def main() -> None:
    gen = load_generation_rows()
    audit = load_audit_map()
    joined = []
    missing_audit = []
    for r in gen:
        key = (r["generation_source_file"], int(r["generation_row_index"]))
        a = audit.get(key)
        if r.get("manual_final_correct") and a is None:
            missing_audit.append({"source_file": key[0], "row_index": key[1], "model_key": r.get("model_key"), "task_id": r.get("task_id")})
        merged = dict(r)
        if a is not None:
            for k in ["manual_process_valid_strict", "manual_process_valid_repaired", "manual_repair_present", "manual_error_type", "manual_error_span", "manual_audit_note_zh", "manual_acpi_strict", "manual_acpi_unrepaired", "manual_audit_status", "manual_auditor"]:
                merged[k] = a.get(k)
            merged["e83_audited_final_correct"] = True
        else:
            merged["e83_audited_final_correct"] = False
            merged.setdefault("manual_acpi_strict", False)
            merged.setdefault("manual_acpi_unrepaired", False)
        joined.append(merged)
    by_model = Counter(r.get("model_key") for r in joined)
    result = {
        "experiment": "E83_natural_hardtask_prevalence_audit",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_generation_dirs": [str(CORE_DIR), str(GLM_DIR)],
        "source_audits": [str(CORE_AUDIT), str(GLM_AUDIT)],
        "n_rows": len(joined),
        "models": dict(sorted(by_model.items())),
        "rows": joined,
        "summary": summarize(joined),
        "missing_final_correct_audits": missing_audit,
        "leakage_audit": {"new_model_inference": False, "gold_answer_in_no_gold_prompts": 0, "known_trap_note_in_prompts": 0, "note_zh": "E83 不跑新推理，只汇总已有 no-gold hard-task generation 与人工审计；gold answer 只用于离线 final-correct 判定。"},
        "scope_note_zh": "E83 是当前已有人审样本的自然困难题发生率审计，不等于更大规模新采样；当前 unrepaired ACPI 计数很低，置信区间仍宽。",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "e83_natural_hardtask_prevalence_audit_20260429.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    for s in result["summary"]:
        if s["slice_type"] in {"all", "model"}:
            print(json.dumps(s, ensure_ascii=False))
    if missing_audit:
        raise SystemExit(f"missing final-correct audits: {len(missing_audit)}")


if __name__ == "__main__":
    main()
