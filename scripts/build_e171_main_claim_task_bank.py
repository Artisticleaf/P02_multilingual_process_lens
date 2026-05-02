#!/usr/bin/env python3
"""Build E171 original-problem task bank for the main hidden-rescue claim.

E171 is deliberately different from E167: it starts from original problems,
keeps only model baseline failures, and then asks whether a hidden monitor over
the model's own wrong trace can help non-thinking repair.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml  # noqa: E402

AIME_YAML = PROJECT / "configs/e26_aime_hard_tasks.yaml"
E153_TASKS = PROJECT / "data/processed/e153_difficult_scenario_tasks_20260501.jsonl"
E164_TASKS = PROJECT / "data/processed/e164_hardened_multi_family_tasks_20260501.jsonl"
OUT = PROJECT / "data/processed/e171_main_claim_task_bank_20260502.jsonl"
SUMMARY_JSON = PROJECT / "reports/E171_MAIN_CLAIM_TASK_BANK_SUMMARY_20260502.json"
SUMMARY_MD = PROJECT / "reports/E171_MAIN_CLAIM_TASK_BANK_SUMMARY_20260502.md"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def normalize_problem(text: str) -> str:
    return " ".join(text.strip().lower().split())


def aime_rows(created: str) -> list[dict[str, Any]]:
    data = read_yaml(AIME_YAML)
    rows = []
    for task in data.get("tasks", []):
        rows.append(
            {
                "created_at": created,
                "experiment": "E171_main_claim_task_bank",
                "task_id": f"e171_{task['id']}",
                "source_task_id": task["id"],
                "task_source": "configs/e26_aime_hard_tasks.yaml",
                "source_experiment": "E26_AIME_hard_tasks_yaml",
                "family": "aime25_mixed_hard",
                "difficulty_tier": "aime25_public_hard",
                "problem": task["en"],
                "gold_answer": str(task["answer"]),
                "source_material": task.get("source", ""),
                "trap_note_offline": task.get("trap", ""),
                "gold_answer_in_prompt_by_design": False,
                "manual_label_in_prompt_by_design": False,
                "trap_note_in_prompt_by_design": False,
                "notes": "AIME public hard-task row. The local config name is E26; the tasks are AIME2025 rows.",
            }
        )
    return rows


def passthrough_rows(path: Path, created: str, source_label: str) -> list[dict[str, Any]]:
    out = []
    for row in load_jsonl(path):
        out.append(
            {
                "created_at": created,
                "experiment": "E171_main_claim_task_bank",
                "task_id": f"e171_{row['task_id']}",
                "source_task_id": row["task_id"],
                "task_source": str(path.relative_to(PROJECT)),
                "source_experiment": row.get("experiment", source_label),
                "family": row["family"],
                "difficulty_tier": row.get("difficulty_tier", "hard_synthetic"),
                "problem": row["problem"],
                "gold_answer": str(row["gold_answer"]),
                "source_material": row.get("source_material", ""),
                "trap_note_offline": row.get("answer_preserving_trap_type", ""),
                "gold_answer_in_prompt_by_design": False,
                "manual_label_in_prompt_by_design": False,
                "trap_note_in_prompt_by_design": False,
                "notes": "Original-problem row reused only for baseline failure harvesting; offline trap metadata is never prompted.",
            }
        )
    return out


def dedupe_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    seen: set[tuple[str, str]] = set()
    kept = []
    dropped = []
    for row in rows:
        key = (normalize_problem(row["problem"]), str(row["gold_answer"]))
        if key in seen:
            dropped.append(row)
            continue
        seen.add(key)
        kept.append(row)
    return kept, dropped


def main() -> None:
    created = datetime.now().isoformat(timespec="seconds")
    rows = []
    rows.extend(aime_rows(created))
    rows.extend(passthrough_rows(E153_TASKS, created, "E153_nonthinking_difficult_scenario"))
    rows.extend(passthrough_rows(E164_TASKS, created, "E164_hardened_multi_family_bank"))
    rows, dropped = dedupe_rows(rows)
    rows = sorted(rows, key=lambda r: (r["task_source"], r["family"], r["task_id"]))
    write_jsonl(OUT, rows)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "E171_main_claim_task_bank_summary",
        "task_bank": str(OUT.relative_to(PROJECT)),
        "tasks": len(rows),
        "dropped_duplicate_problem_answer_rows": len(dropped),
        "by_task_source": dict(sorted(Counter(r["task_source"] for r in rows).items())),
        "by_family": dict(sorted(Counter(r["family"] for r in rows).items())),
        "leakage_policy": {
            "prompt_fields_allowed": ["problem"],
            "gold_answer_in_prompt": False,
            "trap_note_in_prompt": False,
            "manual_label_in_prompt": False,
        },
        "purpose_zh": "E171 只用原题做 non-thinking baseline，筛出模型自己做错的题，再在模型自己的错误 trace 上读取 hidden monitor。",
    }
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# E171 Main-Claim Task Bank / E171 主 claim 题库",
        "",
        f"- Created / 创建时间：`{summary['created_at']}`",
        f"- Tasks / 题目数：{summary['tasks']}",
        f"- Dropped duplicate problem+answer rows / 去重丢弃：{summary['dropped_duplicate_problem_answer_rows']}",
        "",
        "## Sources / 来源",
        "",
    ]
    for key, val in summary["by_task_source"].items():
        lines.append(f"- `{key}`: {val}")
    lines.extend(["", "## Boundary / 边界", ""])
    lines.append("- Runtime prompts contain only the original problem; gold answers, trap notes, and labels are offline. / 运行时 prompt 只含原题；答案、陷阱说明、标签只离线使用。")
    lines.append("- The AIME rows in `configs/e26_aime_hard_tasks.yaml` are AIME2025 rows; `E26` is an experiment id, not the AIME year. / `E26` 是实验编号，不是 AIME 年份。")
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
