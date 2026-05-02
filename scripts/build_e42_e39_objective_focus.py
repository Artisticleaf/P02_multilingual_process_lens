#!/usr/bin/env python3
"""Build the E42 objective-matrix focus set from E39.

E42 focuses on the clean sibling comparison: valid_correct vs invalid_correct
for each E39 surface-semantic task.  The full E39 file remains the source for
answer-masked and wrong-answer variants.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def q(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")


def write_pairs_yaml(path: Path, pairs: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["pairs:"]
    for p in pairs:
        lines.extend(
            [
                f"  - id: {p['id']}",
                f"    task_id: {p['task_id']}",
                f"    model_key: {p['model_key']}",
                f"    bad_idx: {p['bad_idx']}",
                f"    valid_idx: {p['valid_idx']}",
                f"    problem: {q(p['problem'])}",
                f"    error_span: {q(p['error_span'])}",
                f"    support_span: {q(p['support_span'])}",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--e39-jsonl", default=str(PROJECT / "data/processed/e39_surface_semantic_generalization_20260428.jsonl"))
    p.add_argument("--out-jsonl", default=str(PROJECT / "data/processed/e42_e39_objective_focus_20260428.jsonl"))
    p.add_argument("--out-pairs", default=str(PROJECT / "configs/e42_e39_objective_pairs.yaml"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_jsonl(Path(args.e39_jsonl))
    by_task: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for r in rows:
        by_task[r["task_id"]][r["e39_variant"]] = r

    focus: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    for task_id in sorted(by_task):
        variants = by_task[task_id]
        valid = variants.get("valid_correct")
        bad = variants.get("invalid_correct")
        if valid is None or bad is None:
            raise SystemExit(f"Missing valid_correct/invalid_correct for {task_id}")
        if valid["problem"] != bad["problem"]:
            raise SystemExit(f"Problem mismatch for {task_id}")
        if not valid["manual_process_valid"] or bad["manual_process_valid"]:
            raise SystemExit(f"Process labels wrong for {task_id}")
        if valid["manual_final_correct"] is not True or bad["manual_final_correct"] is not True:
            raise SystemExit(f"Final-correct labels wrong for {task_id}")
        if bad.get("is_acpi") is not True:
            raise SystemExit(f"Bad row is not ACPI for {task_id}")
        if valid.get("support_span") not in valid["completion"]:
            raise SystemExit(f"Support span missing in valid completion for {task_id}")
        if bad.get("error_span") not in bad["completion"]:
            raise SystemExit(f"Error span missing in bad completion for {task_id}")
        focus.extend([valid, bad])
        pairs.append(
            {
                "id": f"e42_{task_id}_bad{bad['audit_idx']}_valid{valid['audit_idx']}",
                "task_id": task_id,
                "model_key": "e39_controlled",
                "bad_idx": bad["audit_idx"],
                "valid_idx": valid["audit_idx"],
                "problem": bad["problem"],
                "error_span": bad["error_span"],
                "support_span": valid["support_span"],
            }
        )

    if len(pairs) != 12 or len(focus) != 24:
        raise SystemExit(f"Unexpected E42 size: pairs={len(pairs)} focus={len(focus)}")
    write_jsonl(Path(args.out_jsonl), sorted(focus, key=lambda r: r["audit_idx"]))
    write_pairs_yaml(Path(args.out_pairs), pairs)
    print(f"wrote {args.out_jsonl} rows={len(focus)}")
    print(f"wrote {args.out_pairs} pairs={len(pairs)}")


if __name__ == "__main__":
    main()
