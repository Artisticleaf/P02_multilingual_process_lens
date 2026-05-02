#!/usr/bin/env python3
"""Audit completed E162 files and the current Qwen checkpoint snapshot.

Final JSON files are treated as completed evidence. Checkpoint JSONL rows are
reported separately as provisional queue-health and early-behavior evidence.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
OUT_JSON = PROJECT / "reports/E162_COMPLETED_AND_CHECKPOINT_AUDIT_20260501.json"
OUT_MD = PROJECT / "reports/E162_COMPLETED_AND_CHECKPOINT_AUDIT_20260501.md"
OUT_ROWS = PROJECT / "data/processed/e162_completed_and_checkpoint_audit_20260501.jsonl"

SMOKE_JSON = PROJECT / (
    "results/E162_low_confidence_error_prompt_repair/"
    "gemma4_31b_it_e162_baseline_regenerate_prefix_continue_generic_error_prompt_"
    "localized_error_prompt_oracle_error_prompt_random_location_prompt_smoke_first_sample_20260501.json"
)
QWEN_CHECKPOINT = PROJECT / "logs/e162_repair_qwen35_27b_checkpoint_20260501.jsonl"
STATUS = PROJECT / "logs/e162_low_confidence_error_prompt_status_20260501.jsonl"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compact(text: str, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def mentions_error(text: str) -> bool:
    lower = (text or "").lower()
    needles = [
        "incorrect",
        "wrong",
        "error",
        "flawed",
        "mistake",
        "not correct",
        "contains a logical error",
        "contains an error",
        "不正确",
        "错误",
    ]
    return any(n in lower for n in needles)


def classify_row(row: dict[str, Any]) -> dict[str, Any]:
    variant = row["prompt_variant"]
    final_correct = bool(row["manual_final_correct"])
    hit_max = bool(row["hit_max_new_tokens"])
    marker = bool(row["final_marker_found"])
    repeated = bool(row["source_answer_repeated"])
    error_mentioned = mentions_error(row.get("completion", ""))
    source_wrong = not bool(row.get("source_final_correct"))
    source_invalid = not bool(row.get("source_process_valid_strict"))

    likely_repaired_answer = source_wrong and final_correct and not repeated
    likely_process_recheck = source_invalid and error_mentioned
    localized_success = variant in {"localized_error_prompt", "oracle_error_prompt"} and final_correct and not hit_max
    generic_or_random_recheck = variant in {"generic_error_prompt", "random_location_prompt", "prefix_continue"} and likely_process_recheck

    if hit_max or not marker:
        audit_label = "incomplete_generation"
    elif source_wrong and final_correct:
        audit_label = "answer_repaired_from_wrong_source"
    elif source_invalid and final_correct and likely_process_recheck:
        audit_label = "process_error_identified_or_repaired_final_correct"
    elif source_invalid and final_correct and not likely_process_recheck:
        audit_label = "final_correct_process_repair_not_visible"
    elif final_correct:
        audit_label = "final_correct"
    else:
        audit_label = "final_wrong"

    return {
        "audit_label": audit_label,
        "error_mentioned": error_mentioned,
        "likely_repaired_answer": likely_repaired_answer,
        "likely_process_recheck": likely_process_recheck,
        "localized_success": localized_success,
        "generic_or_random_recheck": generic_or_random_recheck,
    }


def load_smoke_rows() -> list[dict[str, Any]]:
    if not SMOKE_JSON.exists():
        return []
    obj = json.loads(SMOKE_JSON.read_text(encoding="utf-8"))
    return obj.get("rows", [])


def row_source_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_smoke_rows():
        rec = dict(row)
        rec["evidence_level"] = "completed_final_file"
        rec["source_file"] = str(SMOKE_JSON.relative_to(PROJECT))
        rows.append(rec)
    for row in load_jsonl(QWEN_CHECKPOINT):
        rec = dict(row)
        rec["evidence_level"] = "provisional_checkpoint"
        rec["source_file"] = str(QWEN_CHECKPOINT.relative_to(PROJECT))
        rows.append(rec)
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_level: dict[str, Counter[str]] = defaultdict(Counter)
    by_level_variant: dict[str, Counter[str]] = defaultdict(Counter)
    by_level_family: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        level = row["evidence_level"]
        variant = row["prompt_variant"]
        family = row["family"]
        label = row["audit_label"]
        by_level[level]["n"] += 1
        by_level[level]["final_correct"] += int(row["manual_final_correct"])
        by_level[level]["source_answer_repeated"] += int(row["source_answer_repeated"])
        by_level[level]["hit_max"] += int(row["hit_max_new_tokens"])
        by_level[level]["final_marker_found"] += int(row["final_marker_found"])
        by_level[level]["error_mentioned"] += int(row["error_mentioned"])
        by_level[level][f"label::{label}"] += 1
        key = f"{level}::{variant}"
        by_level_variant[key]["n"] += 1
        by_level_variant[key]["final_correct"] += int(row["manual_final_correct"])
        by_level_variant[key]["hit_max"] += int(row["hit_max_new_tokens"])
        by_level_variant[key]["error_mentioned"] += int(row["error_mentioned"])
        by_level_variant[key][f"label::{label}"] += 1
        fkey = f"{level}::{family}"
        by_level_family[fkey]["n"] += 1
        by_level_family[fkey]["final_correct"] += int(row["manual_final_correct"])
        by_level_family[fkey]["hit_max"] += int(row["hit_max_new_tokens"])
        by_level_family[fkey]["error_mentioned"] += int(row["error_mentioned"])
    return {
        "by_evidence_level": {k: dict(v) for k, v in sorted(by_level.items())},
        "by_evidence_level_and_variant": {k: dict(v) for k, v in sorted(by_level_variant.items())},
        "by_evidence_level_and_family": {k: dict(v) for k, v in sorted(by_level_family.items())},
    }


def make_audit_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for idx, row in enumerate(rows, 1):
        flags = classify_row(row)
        rec = {
            "audit_id": f"e162_audit_{idx:04d}",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "evidence_level": row["evidence_level"],
            "source_file": row["source_file"],
            "model_key": row["model_key"],
            "case_id": row["case_id"],
            "case_type": row["case_type"],
            "task_id": row["task_id"],
            "family": row["family"],
            "prompt_variant": row["prompt_variant"],
            "gold_answer": str(row["gold_answer"]),
            "extracted_final": str(row.get("extracted_final", "")),
            "manual_final_correct": bool(row["manual_final_correct"]),
            "source_extracted_final": str(row.get("source_extracted_final", "")),
            "source_final_correct": bool(row.get("source_final_correct")),
            "source_process_valid_strict": bool(row.get("source_process_valid_strict")),
            "source_answer_repeated": bool(row.get("source_answer_repeated")),
            "final_marker_found": bool(row.get("final_marker_found")),
            "hit_max_new_tokens": bool(row.get("hit_max_new_tokens")),
            "manual_error_span_offline": row.get("manual_error_span_offline", ""),
            "localized_span_in_prompt": row.get("localized_span_in_prompt", ""),
            "random_span_in_prompt": row.get("random_span_in_prompt", ""),
            "oracle_hint_in_prompt": bool(row.get("oracle_hint_in_prompt")),
            "gold_answer_in_prompt": bool(row.get("gold_answer_in_prompt")),
            "manual_label_in_prompt": bool(row.get("manual_label_in_prompt")),
            "completion_excerpt": compact(row.get("completion", "")),
        }
        rec.update(flags)
        out.append(rec)
    return out


def markdown_report(payload: dict[str, Any], audit_rows: list[dict[str, Any]]) -> str:
    smoke_rows = [r for r in audit_rows if r["evidence_level"] == "completed_final_file"]
    checkpoint_rows = [r for r in audit_rows if r["evidence_level"] == "provisional_checkpoint"]
    lines = [
        "# E162 Completed and Checkpoint Audit / E162 完成结果与 checkpoint 审计",
        "",
        f"Created / 生成时间：{payload['created_at']}",
        "",
        "## Scope / 范围",
        "",
        "- Completed final evidence / 完成 final 证据：Gemma dense first-sample smoke JSON only. / 目前只有 Gemma dense 首样本 smoke JSON 是完整 final 文件。",
        "- Provisional evidence / 临时证据：current Qwen checkpoint JSONL snapshot. / 当前 Qwen checkpoint 快照，只用于临时行为审计。",
        "- Running full E162 queue is not yet complete. / E162 全量队列尚未完成。",
        "",
        "## Summary / 汇总",
        "",
        "```json",
        json.dumps(payload["summary"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Completed Smoke Audit / 已完成 smoke 审计",
        "",
    ]
    for r in smoke_rows:
        lines.append(
            f"- `{r['prompt_variant']}`: final `{r['extracted_final']}` vs gold `{r['gold_answer']}`, "
            f"correct={r['manual_final_correct']}, label=`{r['audit_label']}`. "
            f"Excerpt / 摘要：{r['completion_excerpt']}"
        )
    lines.extend(
        [
            "",
            "Smoke interpretation / smoke 解释：baseline, prefix, generic warning, and random-location control repeated the source wrong answer; localized and oracle prompts repaired the answer. / baseline、续写、泛泛提示、随机位置都重复源错误答案；局部提示和 oracle 提示修复答案。",
            "",
            "## Qwen Checkpoint Provisional Audit / Qwen checkpoint 临时审计",
            "",
            "Important boundary / 重要边界：these rows are still checkpoint rows. Hit-max or no-final rows should not be counted as model failure until full rerun/longer-token handling is decided. / 这些仍是 checkpoint；达到 token 上限或缺 final marker 的行，不应在未处理截断前当作最终模型失败。",
            "",
        ]
    )
    interesting = [
        r
        for r in checkpoint_rows
        if r["hit_max_new_tokens"]
        or r["audit_label"] in {"answer_repaired_from_wrong_source", "process_error_identified_or_repaired_final_correct", "final_correct_process_repair_not_visible"}
        or r["prompt_variant"] in {"random_location_prompt", "localized_error_prompt", "oracle_error_prompt"}
    ][:40]
    for r in interesting:
        lines.append(
            f"- `{r['task_id']}` / `{r['prompt_variant']}`: final `{r['extracted_final']}` vs gold `{r['gold_answer']}`, "
            f"correct={r['manual_final_correct']}, hit_max={r['hit_max_new_tokens']}, label=`{r['audit_label']}`. "
            f"Excerpt / 摘要：{r['completion_excerpt']}"
        )
    lines.extend(
        [
            "",
            "## Current Reading / 当前解读",
            "",
            "1. Localized prompt is useful but not identical to hidden-layer correction. / 局部提示有效，但它仍不是隐藏层纠错本身。",
            "2. Qwen often repairs process errors even under prefix, generic, or random-location prompts, suggesting a generic re-solve/re-audit tendency. / Qwen 经常在续写、泛泛提示或随机位置提示下也修复过程，说明存在泛化重解/重审倾向。",
            "3. Hit-max rows cluster in long baseline or localized algebra/counting generations under max_new_tokens=1024; these need token-budget handling before final scoring. / 截断主要出现在 1024 token 下的长代数/计数生成，最终评分前需要处理 token budget。",
            "4. The smoke result remains the cleanest positive evidence so far: localized semantic span fixes Gemma dense where generic warning does not. / 目前最干净的正证据仍是 smoke：局部语义 span 能修复 Gemma dense，而泛泛提示不能。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    raw_rows = row_source_rows()
    audit_rows = make_audit_rows(raw_rows)
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "inputs": {
            "smoke_json": str(SMOKE_JSON.relative_to(PROJECT)),
            "qwen_checkpoint": str(QWEN_CHECKPOINT.relative_to(PROJECT)),
            "status_file": str(STATUS.relative_to(PROJECT)),
        },
        "running_status_tail": load_jsonl(STATUS)[-8:],
        "summary": summarize(audit_rows),
        "notes": [
            "Completed final files and checkpoint rows are separated by evidence_level.",
            "Checkpoint rows are provisional and should be replaced by final JSON summaries when the queue completes.",
        ],
    }
    write_jsonl(OUT_ROWS, audit_rows)
    write_json(OUT_JSON, {**payload, "row_count": len(audit_rows)})
    OUT_MD.write_text(markdown_report(payload, audit_rows), encoding="utf-8")
    print(json.dumps({"rows": len(audit_rows), "out_json": str(OUT_JSON), "out_md": str(OUT_MD), "out_rows": str(OUT_ROWS)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
