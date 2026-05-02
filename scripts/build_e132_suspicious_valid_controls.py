#!/usr/bin/env python3
"""Build E132 suspicious-but-valid and invalid-control probe set.

The set reuses the E61 multilingual task grid, then creates additional valid
traces that look suspicious without containing a wrong step.  It is designed to
test whether hidden process-risk signals are true error signals or broad
uncertainty/hesitation signals.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_e61_language_error_grid as e61  # noqa: E402

OUT = PROJECT / "data/processed/e132_suspicious_valid_controls_20260430.jsonl"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def marker_text(route_id: str) -> dict[str, str]:
    zh_like = route_id in {"zh_zh", "en_zh", "mixed"}
    pinyin = route_id == "romanized_zh"
    if pinyin:
        return {
            "check": "Deng yixia, rang wo zai hedui yixia dingyi:",
            "alt": "Ling yige hedui fangfa ye shi kan tongyige guize:",
            "uncertain": "Wo keneng hui kan cuo, suoyi xian an dingyi manman hedui:",
        }
    if zh_like:
        return {
            "check": "等一下，我先核对定义：",
            "alt": "也可以换一个角度复核同一个规则：",
            "uncertain": "我不太确定自己有没有看错，所以按定义逐步核对：",
        }
    return {
        "check": "Wait, let me double-check the definition:",
        "alt": "As a second valid check, use the same rule from another angle:",
        "uncertain": "I might be mistaken, so I will verify the rule carefully:",
    }


def final_line(answer: str) -> str:
    return f"Final answer: {answer}"


def clean_valid_trace(valid_body: str, answer: str) -> str:
    return f"{valid_body}\n{final_line(answer)}"


def suspicious_marker_trace(route_id: str, valid_body: str, answer: str) -> str:
    text = marker_text(route_id)["check"]
    return f"{text} {valid_body}\n{final_line(answer)}"


def suspicious_alternative_trace(route_id: str, valid_body: str, answer: str) -> str:
    text = marker_text(route_id)["alt"]
    return f"{valid_body}\n{text} Repeating the same valid relationship gives the same result, {answer}.\n{final_line(answer)}"


def low_conf_valid_trace(route_id: str, valid_body: str, answer: str) -> str:
    text = marker_text(route_id)["uncertain"]
    return f"{text} {valid_body}\nEven with that caution, the computation is consistent.\n{final_line(answer)}"


def repaired_strict_invalid_trace(invalid_body: str, answer: str) -> str:
    return f"{invalid_body}\n{final_line(answer)}"


def marker_count(trace: str) -> int:
    markers = [
        "wait",
        "double-check",
        "verify",
        "mistaken",
        "carefully",
        "等一下",
        "核对",
        "不太确定",
        "hedui",
        "keneng",
    ]
    low = trace.lower()
    return sum(low.count(m.lower()) for m in markers)


def make_row(
    audit_idx: int,
    task: dict[str, Any],
    route_id: str,
    route_desc: str,
    problem: str,
    completion: str,
    variant: str,
    process_valid: bool,
    strict_acpi: bool,
    unrepaired: bool,
    known_error_span: str | None,
    note_zh: str,
) -> dict[str, Any]:
    return {
        "audit_idx": audit_idx,
        "experiment": "E132_suspicious_valid_controls",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "task_id": f"e132_{route_id}_{task['name']}_{variant}",
        "source_task_name": task["name"],
        "family": task["family"],
        "route_id": route_id,
        "route_desc": route_desc,
        "problem": problem,
        "completion": completion,
        "gold_answer": task["gold_answer"],
        "variant": variant,
        "manual_process_valid_strict": process_valid,
        "manual_process_valid_repaired": process_valid or (strict_acpi and not unrepaired),
        "manual_acpi_strict": strict_acpi,
        "manual_acpi_unrepaired": unrepaired,
        "manual_repair_present": strict_acpi and not unrepaired,
        "manual_error_span": known_error_span,
        "manual_error_type": None if process_valid else "controlled_repaired_strict_invalid",
        "manual_notes_zh": note_zh,
        "suspicion_marker_count": marker_count(completion),
        "contains_gold_in_prompt": False,
        "contains_error_label_in_prompt": False,
        "data_leakage_note_zh": "gold/manual labels/error span are metadata only; verifier prompts should contain only problem and completion prefix.",
    }


def main() -> None:
    rows: list[dict[str, Any]] = []
    base = 1320000
    idx = base
    for task in e61.TASKS:
        for route_id, _input_lang, _reason_lang, route_desc in e61.ROUTES:
            problem, valid_body, invalid_body = e61.select_text(task, route_id)
            variants = [
                (
                    "clean_valid",
                    clean_valid_trace(valid_body, task["gold_answer"]),
                    True,
                    False,
                    False,
                    None,
                    "干净正确过程。",
                ),
                (
                    "suspicious_valid_marker",
                    suspicious_marker_trace(route_id, valid_body, task["gold_answer"]),
                    True,
                    False,
                    False,
                    None,
                    "包含 wait/check/核对 等可疑词，但过程本身正确。",
                ),
                (
                    "suspicious_valid_alternative",
                    suspicious_alternative_trace(route_id, valid_body, task["gold_answer"]),
                    True,
                    False,
                    False,
                    None,
                    "包含第二种复核说法，但没有错误步骤。",
                ),
                (
                    "low_conf_valid",
                    low_conf_valid_trace(route_id, valid_body, task["gold_answer"]),
                    True,
                    False,
                    False,
                    None,
                    "包含低置信表达，但过程本身正确。",
                ),
                (
                    "repaired_strict_invalid",
                    repaired_strict_invalid_trace(invalid_body, task["gold_answer"]),
                    False,
                    True,
                    False,
                    task["error_span"],
                    "包含一个明确错误语义/公式，后文给出正确答案；strict trace-as-proof 下无效。",
                ),
            ]
            for variant, completion, valid, strict_acpi, unrepaired, err_span, note in variants:
                rows.append(
                    make_row(
                        audit_idx=idx,
                        task=task,
                        route_id=route_id,
                        route_desc=route_desc,
                        problem=problem,
                        completion=completion,
                        variant=variant,
                        process_valid=valid,
                        strict_acpi=strict_acpi,
                        unrepaired=unrepaired,
                        known_error_span=err_span,
                        note_zh=note,
                    )
                )
                idx += 1
    write_jsonl(OUT, rows)
    summary = {
        "out": str(OUT.relative_to(PROJECT)),
        "rows": len(rows),
        "by_variant": {},
        "by_route": {},
        "leakage_audit": {
            "contains_gold_in_prompt_rows": 0,
            "contains_error_label_in_prompt_rows": 0,
            "note_zh": "构造数据保存 gold/label/error span 作为离线元数据；运行 verifier 时不得放入 prompt。",
        },
    }
    for row in rows:
        summary["by_variant"][row["variant"]] = summary["by_variant"].get(row["variant"], 0) + 1
        summary["by_route"][row["route_id"]] = summary["by_route"].get(row["route_id"], 0) + 1
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
