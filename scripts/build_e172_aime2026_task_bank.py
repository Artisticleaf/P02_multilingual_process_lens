#!/usr/bin/env python3
"""Build the E172 MathArena AIME 2026 task bank.

The runtime prompts for E172 use only the problem statement.  The answer and
dataset metadata are kept for offline scoring and provenance.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]

OUT = PROJECT / "data/processed/e172_aime2026_matharena_task_bank_20260502.jsonl"
SUMMARY_JSON = PROJECT / "reports/E172_AIME2026_MATHARENA_TASK_BANK_20260502.json"
SUMMARY_MD = PROJECT / "reports/E172_AIME2026_MATHARENA_TASK_BANK_20260502.md"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def normalize_problem(text: str) -> str:
    return " ".join(text.strip().lower().split())


def dataset_revision(repo: str) -> dict[str, str]:
    try:
        from huggingface_hub import HfApi

        info = HfApi().dataset_info(repo)
        return {
            "dataset_id": str(info.id),
            "dataset_sha": str(info.sha),
            "dataset_last_modified": str(info.last_modified),
        }
    except Exception as exc:  # pragma: no cover - network metadata is best effort
        return {
            "dataset_id": repo,
            "dataset_sha": "unavailable",
            "dataset_last_modified": "unavailable",
            "metadata_error": f"{type(exc).__name__}: {exc}",
        }


def build_rows(repo: str, config: str, split: str, max_rows: int) -> tuple[list[dict[str, Any]], dict[str, str]]:
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("The `datasets` package is required to build E172. Activate passage_prep_py312.") from exc

    ds = load_dataset(repo, config, split=split)
    if max_rows > 0:
        ds = ds.select(range(min(max_rows, len(ds))))
    meta = dataset_revision(repo)
    created = datetime.now().isoformat(timespec="seconds")
    rows: list[dict[str, Any]] = []
    for raw in ds:
        idx = int(raw["problem_idx"])
        problem = str(raw["problem"]).strip()
        answer = str(raw["answer"]).strip()
        rows.append(
            {
                "created_at": created,
                "experiment": "E172_aime2026_matharena_task_bank",
                "task_id": f"e172_aime2026_p{idx:02d}",
                "source_task_id": f"aime2026_p{idx:02d}",
                "problem_idx": idx,
                "task_source": f"{repo}/{config}/{split}",
                "source_experiment": "MathArena_AIME_2026",
                "family": "matharena_aime2026",
                "difficulty_tier": "official_aime2026",
                "problem": problem,
                "gold_answer": answer,
                "source_material": repo,
                "dataset_repo": repo,
                "dataset_config": config,
                "dataset_split": split,
                "dataset_sha": meta.get("dataset_sha", ""),
                "dataset_last_modified": meta.get("dataset_last_modified", ""),
                "gold_answer_in_prompt_by_design": False,
                "manual_label_in_prompt_by_design": False,
                "trap_note_in_prompt_by_design": False,
                "notes": "MathArena AIME 2026 row. Runtime prompts use only the problem; answer is offline scoring metadata.",
            }
        )
    return rows, meta


def audit_rows(rows: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not rows:
        errors.append("task_bank_empty")
        return errors, warnings
    ids = [r["task_id"] for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_task_id")
    pairs = [(normalize_problem(r["problem"]), str(r["gold_answer"])) for r in rows]
    if len(pairs) != len(set(pairs)):
        warnings.append("duplicate_problem_answer_pair")
    problem_idxs = sorted(int(r["problem_idx"]) for r in rows)
    if problem_idxs != list(range(1, len(rows) + 1)):
        warnings.append(f"non_contiguous_problem_idx:{problem_idxs[:3]}..{problem_idxs[-3:]}")
    for row in rows:
        for key in ["task_id", "problem_idx", "problem", "gold_answer", "dataset_repo", "dataset_split"]:
            if row.get(key) in (None, ""):
                errors.append(f"missing_{key}:{row.get('task_id')}")
        if row.get("gold_answer_in_prompt_by_design"):
            errors.append(f"gold_answer_in_prompt_by_design:{row['task_id']}")
    return errors, warnings


def write_summary(rows: list[dict[str, Any]], meta: dict[str, str], args: argparse.Namespace) -> None:
    errors, warnings = audit_rows(rows)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "E172_aime2026_matharena_task_bank_summary",
        "task_bank": str(OUT.relative_to(PROJECT)),
        "dataset": {
            "repo": args.dataset_repo,
            "config": args.config,
            "split": args.split,
            **meta,
        },
        "tasks": len(rows),
        "problem_idx_min": min((int(r["problem_idx"]) for r in rows), default=None),
        "problem_idx_max": max((int(r["problem_idx"]) for r in rows), default=None),
        "answer_min": min((int(r["gold_answer"]) for r in rows if str(r["gold_answer"]).isdigit()), default=None),
        "answer_max": max((int(r["gold_answer"]) for r in rows if str(r["gold_answer"]).isdigit()), default=None),
        "by_family": dict(sorted(Counter(r["family"] for r in rows).items())),
        "leakage_policy": {
            "prompt_fields_allowed": ["problem"],
            "gold_answer_in_prompt": False,
            "trap_note_in_prompt": False,
            "manual_label_in_prompt": False,
            "source_metadata_in_prompt": False,
        },
        "errors": errors,
        "warnings": warnings,
        "passed": not errors,
    }
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# E172 AIME 2026 MathArena Task Bank / E172 AIME 2026 MathArena 题库",
        "",
        f"- Dataset / 数据集：`{args.dataset_repo}` `{args.config}` `{args.split}`",
        f"- Dataset SHA / 数据集版本：`{meta.get('dataset_sha', 'unavailable')}`",
        f"- Tasks / 题目数：{len(rows)}",
        f"- Passed / 通过：`{summary['passed']}`",
        f"- Errors / 错误：`{errors}`",
        f"- Warnings / 警告：`{warnings}`",
        "",
        "## Boundary / 边界",
        "",
        "- Runtime prompts contain only the original problem statement. / 运行时 prompt 只含原始题干。",
        "- `gold_answer`, dataset revision, and row metadata are offline scoring/provenance fields. / 答案、数据集版本和行元数据只用于离线评分和溯源。",
        "- This bank replaces the older local AIME2025-style rows for the next high-difficulty AIME 2026 test. / 这个题库用于下一轮 AIME 2026 高难测试，不再复用旧 AIME2025-style 题。",
        "",
        "## First Rows / 前几题",
        "",
    ]
    for row in rows[:5]:
        preview = " ".join(row["problem"].split())[:180]
        lines.append(f"- `{row['task_id']}` answer=`{row['gold_answer']}` problem=`{preview}`")
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if errors:
        raise SystemExit(f"E172 task-bank audit failed: {errors}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset-repo", default="MathArena/aime_2026")
    p.add_argument("--config", default="default")
    p.add_argument("--split", default="train")
    p.add_argument("--out", default=str(OUT))
    p.add_argument("--max-rows", type=int, default=0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    global OUT
    OUT = Path(args.out)
    rows, meta = build_rows(args.dataset_repo, args.config, args.split, args.max_rows)
    rows = sorted(rows, key=lambda r: int(r["problem_idx"]))
    write_jsonl(OUT, rows)
    write_summary(rows, meta, args)
    print(
        json.dumps(
            {
                "wrote": str(OUT.relative_to(PROJECT) if OUT.is_relative_to(PROJECT) else OUT),
                "tasks": len(rows),
                "dataset_sha": meta.get("dataset_sha", "unavailable"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
