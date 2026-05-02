#!/usr/bin/env python3
"""Build E166 prefix points for hidden-monitor calibration.

The output is model-agnostic. It contains causal visible prefixes from the
hardened E164 candidate traces. Gold answers and manual error spans remain
offline metadata; future hidden replay prompts should use only problem+prefix.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
SOL_PATH = PROJECT / "data/processed/e164_hardened_multi_family_candidate_solutions_20260501.jsonl"
OUT = PROJECT / "data/processed/e166_hardened_monitor_prefix_points_20260502.jsonl"
SUMMARY_OUT = PROJECT / "reports/E166_HARDENED_MONITOR_PREFIX_BANK_SUMMARY_20260502.json"

FINAL_RE = re.compile(r"\bFinal answer\s*[:：]", re.IGNORECASE)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def trace_body(trace: str) -> str:
    m = FINAL_RE.search(trace)
    return trace[: m.start()].strip() if m else trace.strip()


def sentence_boundaries(text: str) -> list[tuple[int, str]]:
    """Return plausible step ends plus the preceding visible span."""
    boundaries: list[tuple[int, str]] = []
    start = 0
    for m in re.finditer(r"(?<=[.!?。])\s+", text):
        end = m.start() + 1
        span = text[start:end].strip()
        if span:
            boundaries.append((end, span))
        start = m.end()
    tail = text[start:].strip()
    if tail:
        boundaries.append((len(text), tail))
    return boundaries


def add_unique(points: list[dict[str, Any]], rec: dict[str, Any]) -> None:
    key = (rec["prefix_char_end"], rec["boundary_kind"])
    if not any((p["prefix_char_end"], p["boundary_kind"]) == key for p in points):
        points.append(rec)


def build_rows() -> list[dict[str, Any]]:
    created = datetime.now().isoformat(timespec="seconds")
    rows: list[dict[str, Any]] = []
    for sol in load_jsonl(SOL_PATH):
        trace = sol["candidate_solution"]
        body = trace_body(trace)
        span = sol.get("manual_error_span") or ""
        is_invalid = not bool(sol["manual_process_valid_strict"])
        points: list[dict[str, Any]] = []

        for idx, (end, visible_span) in enumerate(sentence_boundaries(body), start=1):
            includes_error = bool(span and span in body[:end])
            is_exact_error_end = bool(span and end == body.find(span) + len(span))
            add_unique(
                points,
                {
                    "boundary_kind": "sentence_end",
                    "sentence_index": idx,
                    "prefix_char_end": end,
                    "visible_span": visible_span,
                    "monitor_target": False,
                    "prefix_includes_manual_error_span": includes_error,
                    "exact_manual_error_span_end": is_exact_error_end,
                },
            )

        if span:
            pos = body.find(span)
            if pos < 0:
                raise ValueError(f"{sol['solution_id']} span not found: {span}")
            end = pos + len(span)
            add_unique(
                points,
                {
                    "boundary_kind": "manual_error_span_end",
                    "sentence_index": None,
                    "prefix_char_end": end,
                    "visible_span": span,
                    "monitor_target": True,
                    "prefix_includes_manual_error_span": True,
                    "exact_manual_error_span_end": True,
                },
            )

        for point in sorted(points, key=lambda p: (p["prefix_char_end"], p["boundary_kind"])):
            prefix = body[: int(point["prefix_char_end"])].strip()
            if not prefix:
                continue
            row = {
                "created_at": created,
                "experiment": "E166_hardened_hidden_monitor_prefix_bank",
                "prefix_id": f"e166_{sol['solution_id']}_{point['boundary_kind']}_{point['prefix_char_end']}",
                "solution_id": sol["solution_id"],
                "task_id": sol["task_id"],
                "family": sol["family"],
                "candidate_variant": sol["candidate_variant"],
                "trace_valid_strict": bool(sol["manual_process_valid_strict"]),
                "trace_final_correct": bool(sol["source_final_correct"]),
                "trace_class": "valid"
                if sol["manual_process_valid_strict"]
                else ("invalid_answer_correct" if sol["source_final_correct"] else "invalid_answer_wrong"),
                "problem": sol["problem"],
                "prefix_text": prefix,
                "prefix_char_end": point["prefix_char_end"],
                "visible_span": point["visible_span"],
                "boundary_kind": point["boundary_kind"],
                "sentence_index": point["sentence_index"],
                "manual_error_span_offline": span,
                "manual_error_type_offline": sol.get("manual_error_type") or "",
                "monitor_target": bool(point["monitor_target"] and is_invalid),
                "prefix_includes_manual_error_span": bool(point["prefix_includes_manual_error_span"]),
                "exact_manual_error_span_end": bool(point["exact_manual_error_span_end"]),
                "gold_answer_offline": sol["gold_answer"],
                "source_extracted_final_offline": sol["source_extracted_final"],
                "prompt_fields_allowed_for_hidden_replay": ["problem", "prefix_text"],
                "gold_answer_in_prompt_by_design": False,
                "manual_error_span_in_prompt_by_design": False,
                "manual_label_in_prompt_by_design": False,
            }
            rows.append(row)
    return sorted(rows, key=lambda r: (r["family"], r["task_id"], r["candidate_variant"], r["prefix_char_end"], r["boundary_kind"]))


def main() -> None:
    rows = build_rows()
    write_jsonl(OUT, rows)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "out": str(OUT.relative_to(PROJECT)),
        "prefix_points": len(rows),
        "tasks": len({r["task_id"] for r in rows}),
        "solutions": len({r["solution_id"] for r in rows}),
        "families": dict(sorted(Counter(r["family"] for r in rows).items())),
        "trace_classes": dict(sorted(Counter(r["trace_class"] for r in rows).items())),
        "boundary_kinds": dict(sorted(Counter(r["boundary_kind"] for r in rows).items())),
        "monitor_targets": sum(int(r["monitor_target"]) for r in rows),
        "valid_control_points": sum(int(r["trace_valid_strict"]) for r in rows),
        "invalid_non_target_points": sum(int((not r["trace_valid_strict"]) and (not r["monitor_target"])) for r in rows),
        "leakage_policy": "future hidden replay prompts may use only problem and prefix_text",
    }
    write_json(SUMMARY_OUT, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
