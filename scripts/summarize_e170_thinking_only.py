#!/usr/bin/env python3
"""Summarize E170 thinking-only hardened-task results."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
RESULT_DIR = PROJECT / "results/E170_thinking_only_hardened_tasks"
OUT_JSON = PROJECT / "reports/E170_THINKING_ONLY_STAGE_ANALYSIS_20260502.json"
OUT_MD = PROJECT / "reports/E170_THINKING_ONLY_STAGE_ANALYSIS_20260502.md"
MODELS = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_rows(model_key: str) -> tuple[list[dict[str, Any]], str]:
    results = sorted(RESULT_DIR.glob(f"{model_key}_e170_thinking_only*.json"))
    if results:
        data = json.loads(results[-1].read_text(encoding="utf-8"))
        return list(data.get("rows", [])), str(results[-1].relative_to(PROJECT))
    ckpt = PROJECT / f"logs/e170_thinking_only_{model_key}_checkpoint_20260502.jsonl"
    rows = load_jsonl(ckpt)
    dedup = {row["task_id"]: row for row in rows}
    return list(dedup.values()), str(ckpt.relative_to(PROJECT))


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tokens = [int(r.get("generated_tokens") or 0) for r in rows]
    correct = [r for r in rows if r.get("manual_final_correct")]
    return {
        "n": len(rows),
        "correct": len(correct),
        "accuracy": len(correct) / len(rows) if rows else None,
        "final_marker_found": sum(int(bool(r.get("final_marker_found"))) for r in rows),
        "hit_max_new_tokens": sum(int(bool(r.get("hit_max_new_tokens"))) for r in rows),
        "completion_tokens": sum(tokens),
        "mean_completion_tokens": mean(tokens) if tokens else None,
        "median_completion_tokens": median(tokens) if tokens else None,
    }


def fmt(v: Any) -> str:
    if v is None:
        return "NA"
    if isinstance(v, float):
        return f"{v:.3f}"
    return str(v)


def main() -> None:
    by_model = {}
    for model in MODELS:
        rows, source = load_rows(model)
        by_family = {}
        for family in sorted({r.get("family") for r in rows}):
            by_family[family] = summarize_rows([r for r in rows if r.get("family") == family])
        by_model[model] = {
            "source": source,
            "overall": summarize_rows(rows),
            "by_family": by_family,
            "leakage_counts": {
                "gold_answer_in_prompt_rows": sum(int(bool(r.get("gold_answer_in_prompt"))) for r in rows),
                "trap_note_in_prompt_rows": sum(int(bool(r.get("trap_note_in_prompt"))) for r in rows),
                "manual_label_in_prompt_rows": sum(int(bool(r.get("manual_label_in_prompt"))) for r in rows),
                "error_span_in_prompt_rows": sum(int(bool(r.get("error_span_in_prompt"))) for r in rows),
                "repair_prompt_in_prompt_rows": sum(int(bool(r.get("repair_prompt_in_prompt"))) for r in rows),
            },
            "status_counts": {
                f"final={final_marker}|hit_max={hit_max}": count
                for (final_marker, hit_max), count in sorted(
                    Counter((bool(r.get("final_marker_found")), bool(r.get("hit_max_new_tokens"))) for r in rows).items(),
                    key=lambda kv: str(kv[0]),
                )
            },
        }
    result = {
        "experiment": "E170_thinking_only_stage_analysis",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "models": MODELS,
        "by_model": by_model,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# E170 Thinking-Only Stage Analysis / E170 thinking-only 阶段分析",
        "",
        f"Created / 创建时间：`{result['created_at']}`.",
        "",
        "E170 gives only the original E164 hardened problem plus a generic thinking solve template. / E170 只给 E164 加难原题和通用 thinking 解题模板。",
        "",
        "| model | n | correct | acc | completion tokens | mean tokens | hit-max | final marker | source |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for model, info in by_model.items():
        row = info["overall"]
        lines.append(
            f"| {model} | {row['n']} | {row['correct']} | {fmt(row['accuracy'])} | {row['completion_tokens']} | "
            f"{fmt(row['mean_completion_tokens'])} | {row['hit_max_new_tokens']} | {row['final_marker_found']} | `{info['source']}` |"
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"wrote": [str(OUT_JSON.relative_to(PROJECT)), str(OUT_MD.relative_to(PROJECT))]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
