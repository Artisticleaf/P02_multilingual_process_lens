#!/usr/bin/env python3
"""Finalize E104 manual process audit.

The judgments in MANUAL_AUDIT are the human/agent audit decisions made after
reading the E104 final-correct rows.  The source sheet is kept intact; this
script writes an audited copy and a compact summary for reports.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
IN_PATH = PROJECT / "data/processed/e104_tg_ng_process_audit_sheet_20260429.jsonl"
OUT_PATH = PROJECT / "data/processed/e104_tg_ng_process_audit_official_20260429.jsonl"
SUMMARY_PATH = PROJECT / "results/E104_tg_ng_process_audit/e104_tg_ng_process_audit_official_summary.json"


# strict_final_decision:
#   True  = explicit final marker gave the correct final answer.
#   False = no explicit correct final decision; fallback text may contain the gold number.
# strict-valid means no accepted wrong step is needed for the final solution.
# repaired_acpi means the trace is final-correct but contains an earlier explicit wrong final/conclusion later repaired.
MANUAL_AUDIT: dict[int, dict[str, Any]] = {
    1040001: {"status": "audited", "strict_valid": True, "repaired_valid": True, "strict_acpi": False, "repair": False, "unrepaired_acpi": False, "error_type": None, "span": None, "note": "base-divisor solution is algebraically valid; explicit final answer correct."},
    1040002: {"status": "audited", "strict_valid": True, "repaired_valid": True, "strict_acpi": False, "repair": False, "unrepaired_acpi": False, "error_type": None, "span": None, "note": "base-divisor self-check solution is valid; no committed wrong step found."},
    1040003: {"status": "audited", "strict_valid": False, "repaired_valid": True, "strict_acpi": True, "repair": True, "unrepaired_acpi": False, "error_type": "wrong_initial_final_answer_repaired", "span": "starts with `Final answer: 26`, later derives and states 70", "note": "answer-first row first gives wrong final answer 26, then corrects to 70; repaired ACPI under strict any-wrong-step policy."},
    1040004: {"status": "audited", "strict_valid": True, "repaired_valid": True, "strict_acpi": False, "repair": False, "unrepaired_acpi": False, "error_type": None, "span": None, "note": "integer-pairs factorization and inclusion-exclusion count are valid."},
    1040005: {"status": "audited", "strict_valid": True, "repaired_valid": True, "strict_acpi": False, "repair": False, "unrepaired_acpi": False, "error_type": None, "span": None, "note": "integer-pairs solution reaches correct factorization/count; hit-max continues after a valid final line but no process-invalid step was found in the audited span."},
    1040006: {"status": "audited", "strict_valid": True, "repaired_valid": True, "strict_acpi": False, "repair": False, "unrepaired_acpi": False, "error_type": None, "span": None, "note": "trapezoid tangential-quadrilateral and geometry derivation are valid."},
    1040007: {"status": "audited", "strict_valid": True, "repaired_valid": True, "strict_acpi": False, "repair": False, "unrepaired_acpi": False, "error_type": None, "span": None, "note": "trapezoid self-check solution is valid and explicitly checks the main traps."},
    1040008: {"status": "audited", "strict_valid": False, "repaired_valid": True, "strict_acpi": True, "repair": True, "unrepaired_acpi": False, "error_type": "wrong_initial_final_answer_repaired", "span": "starts with `Final answer: 136`, later derives and states 504", "note": "answer-first row first gives wrong final answer 136, then corrects to 504; repaired ACPI."},
    1040009: {"status": "audited", "strict_valid": True, "repaired_valid": True, "strict_acpi": False, "repair": False, "unrepaired_acpi": False, "error_type": None, "span": None, "note": "matched-sampling base-divisor neutral solution is valid."},
    1040010: {"status": "audited", "strict_valid": True, "repaired_valid": True, "strict_acpi": False, "repair": False, "unrepaired_acpi": False, "error_type": None, "span": None, "note": "matched-sampling base-divisor self-check solution is valid."},
    1040011: {"status": "audited", "strict_valid": True, "repaired_valid": True, "strict_acpi": False, "repair": False, "unrepaired_acpi": False, "error_type": None, "span": None, "note": "matched-sampling integer-pairs solution uses valid ratio/factor line count; hit-max occurs after valid reasoning."},
    1040012: {"status": "audited", "strict_valid": True, "repaired_valid": True, "strict_acpi": False, "repair": False, "unrepaired_acpi": False, "error_type": None, "span": None, "note": "initial factoring attempt is abandoned, then quadratic-form derivation is valid; not counted as process-invalid."},
    1040013: {"status": "audited", "strict_valid": True, "repaired_valid": True, "strict_acpi": False, "repair": False, "unrepaired_acpi": False, "error_type": None, "span": None, "note": "matched-sampling trapezoid neutral solution is valid."},
    1040014: {"status": "audited", "strict_valid": True, "repaired_valid": True, "strict_acpi": False, "repair": False, "unrepaired_acpi": False, "error_type": None, "span": None, "note": "matched-sampling trapezoid self-check solution is valid."},
    1040015: {"status": "audited", "strict_valid": False, "repaired_valid": True, "strict_acpi": True, "repair": True, "unrepaired_acpi": False, "error_type": "wrong_initial_final_answer_repaired", "span": "starts with `Final answer: 272`, later derives and states 504", "note": "answer-first row first gives wrong final answer 272, then corrects to 504; repaired ACPI."},
    1040016: {"status": "audited_unfinished_tg", "strict_valid": None, "repaired_valid": None, "strict_acpi": False, "repair": None, "unrepaired_acpi": False, "error_type": "no_explicit_final_decision", "span": "4096-token TG trace has no explicit final answer line", "note": "fallback sees correct number 70 in an unfinished thinking trace, but this is not a strict final decision."},
    1040017: {"status": "audited_unfinished_tg", "strict_valid": None, "repaired_valid": None, "strict_acpi": False, "repair": None, "unrepaired_acpi": False, "error_type": "no_explicit_final_decision", "span": "4096-token TG trace has no explicit final answer line", "note": "fallback sees correct number 70, but the TG trace is truncated/unclosed."},
    1040018: {"status": "audited_unfinished_tg", "strict_valid": None, "repaired_valid": None, "strict_acpi": False, "repair": None, "unrepaired_acpi": False, "error_type": "no_explicit_final_decision", "span": "4096-token TG trace has no explicit final answer line", "note": "fallback sees correct number 117 in a valid-looking but unfinished chain; not a strict final decision."},
    1040019: {"status": "audited_unfinished_tg", "strict_valid": None, "repaired_valid": None, "strict_acpi": False, "repair": None, "unrepaired_acpi": False, "error_type": "no_explicit_final_decision", "span": "4096-token TG trace has no explicit final answer line", "note": "fallback sees correct number 117, but the answer-first TG trace is still unclosed."},
    1040020: {"status": "audited_unfinished_tg", "strict_valid": None, "repaired_valid": None, "strict_acpi": False, "repair": None, "unrepaired_acpi": False, "error_type": "no_explicit_final_decision", "span": "4096-token TG trace has no explicit final answer line", "note": "fallback sees correct number 504, but the TG trace is truncated/unclosed."},
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def main() -> None:
    rows = load_jsonl(IN_PATH)
    missing = sorted(set(r["e104_audit_idx"] for r in rows) - set(MANUAL_AUDIT))
    extra = sorted(set(MANUAL_AUDIT) - set(r["e104_audit_idx"] for r in rows))
    if missing or extra:
        raise SystemExit(f"manual audit id mismatch missing={missing} extra={extra}")

    audited: list[dict[str, Any]] = []
    by_mode: dict[str, Counter[str]] = defaultdict(Counter)
    by_mode_variant: dict[str, Counter[str]] = defaultdict(Counter)
    for r in rows:
        a = MANUAL_AUDIT[r["e104_audit_idx"]]
        out = dict(r)
        out.update(
            {
                "manual_audit_status": a["status"],
                "manual_process_valid_strict": a["strict_valid"],
                "manual_process_valid_repaired": a["repaired_valid"],
                "manual_acpi_strict": a["strict_acpi"],
                "manual_repair_present": a["repair"],
                "manual_acpi_unrepaired": a["unrepaired_acpi"],
                "manual_error_type": a["error_type"],
                "manual_error_span": a["span"],
                "manual_notes_zh": a["note"],
                "manual_auditor": "codex_agent_manual_audit",
                "manual_audited_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
        audited.append(out)
        for key, bucket in [
            (out["mode_label"], by_mode[out["mode_label"]]),
            (f"{out['mode_label']}|{out['prompt_variant']}", by_mode_variant[f"{out['mode_label']}|{out['prompt_variant']}"]),
        ]:
            bucket["audit_rows"] += 1
            bucket["strict_final_correct"] += int(bool(out["strict_final_correct"]))
            bucket["fallback_final_correct"] += int(bool(out["fallback_final_correct"]))
            bucket["explicit_final_marker_found"] += int(bool(out["explicit_final_marker_found"]))
            bucket["hit_max_new_tokens"] += int(bool(out["hit_max_new_tokens"]))
            bucket["strict_valid"] += int(out["manual_process_valid_strict"] is True)
            bucket["strict_acpi"] += int(out["manual_acpi_strict"] is True)
            bucket["repaired_acpi"] += int(out["manual_repair_present"] is True and out["manual_acpi_strict"] is True)
            bucket["unrepaired_acpi"] += int(out["manual_acpi_unrepaired"] is True)
            bucket["unfinished_tg"] += int(out["manual_audit_status"] == "audited_unfinished_tg")

    write_jsonl(OUT_PATH, audited)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_sheet": str(IN_PATH.relative_to(PROJECT)),
        "audited_jsonl": str(OUT_PATH.relative_to(PROJECT)),
        "audit_rows": len(audited),
        "by_mode": {k: dict(v) for k, v in sorted(by_mode.items())},
        "by_mode_variant": {k: dict(v) for k, v in sorted(by_mode_variant.items())},
        "scope_note_zh": "TG fallback-correct 但无 explicit final marker 的行不计入 strict final-decision，也不计入 strict ACPI。",
        "scope_note_en": "TG fallback-correct rows without an explicit final marker are not strict final decisions and are not counted as strict ACPI.",
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
