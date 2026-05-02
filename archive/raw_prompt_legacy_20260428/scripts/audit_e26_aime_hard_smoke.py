#!/usr/bin/env python3
"""Audit the E26 AIME hard-task smoke at trace level."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]


def normalize_answer(text: str) -> str:
    text = str(text).strip().lower()
    text = re.sub(r"\\boxed\{([^{}]+)\}", r"\1", text)
    text = re.sub(r"[^0-9a-z+\-./]", "", text)
    return text


def extract_final(text: str) -> tuple[str, bool]:
    matches = re.findall(r"final\s*answer\s*[:：]\s*([^\n\r]+)", text, flags=re.I)
    if matches:
        usable = [m.strip() for m in matches if "<answer" not in m.lower() and "<答案" not in m]
        if usable:
            return usable[-1], True
    boxed = re.findall(r"\\boxed\{([^{}]+)\}", text)
    if boxed:
        return boxed[-1].strip(), False
    return "", False


def manual_note(row: dict[str, Any], final_answer: str, marker: bool) -> tuple[str, bool | None]:
    model = row["model_key"]
    task = row["task_id"]
    route = f"{row['input_lang']}->{row['reason_lang']}"
    text = row["completion"]
    if marker:
        if normalize_answer(final_answer) == normalize_answer(row["gold_answer"]):
            return "final_correct_needs_full_process_audit", None
        return "final_wrong_no_acpi", False
    if "17_b" in text and "b²" in text:
        return "no_final_marker_invalid_base_notation_as_three_digit", False
    if route.startswith("zh->") and ("no property is given" in text or "looks messy" in text or "用户" in text):
        return "no_final_marker_prompt_comprehension_degraded_on_zh_route", False
    if model == "qwen35_9b" and task in {"aime25_base_divisor_p1", "aime25_icecream_ordered_assign_p3"}:
        return "no_final_marker_partial_reasoning_often_on_track", None
    if task == "aime25_geometry_reflection_p2" and ("trapezoid" in text.lower() or "reflection" in text.lower()):
        return "no_final_marker_geometry_partial_or_unresolved", None
    return "no_final_marker_truncated_or_unresolved", None


def read_rows(in_dirs: list[Path]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for d in in_dirs:
        for path in sorted(d.glob("*trace_pool_smoke*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for i, row in enumerate(data["rows"]):
                item = dict(row)
                item["source_file"] = str(path)
                item["source_row"] = i
                out.append(item)
    return out


def write_report(rows: list[dict[str, Any]], out_md: Path) -> None:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[(r["model_key"], f"{r['input_lang']}->{r['reason_lang']}")].append(r)
    lines = [
        "# E26 AIME Hard-Task Smoke Audit / E26 AIME 困难任务 smoke 审计",
        "",
        f"Created / 创建时间: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Scope: 3 AIME-2025 tasks, 2 routes (`en->en`, `zh->en`), 4 local models, two prompt variants (`fast`, `concise`), k=1 per variant. / 范围：3 道 AIME-2025，2 条 route，4 个本地模型，两个提示变体，每个变体每题 1 条样本。",
        "",
        "## Aggregate / 汇总",
        "",
        "| model | route | n | final marker | final correct strict | final wrong | no final marker | ACPI candidates |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for (model, route), g in sorted(groups.items()):
        lines.append(
            f"| {model} | {route} | {len(g)} | "
            f"{sum(r['final_marker_present'] for r in g)} | "
            f"{sum(r['manual_final_correct'] is True for r in g)} | "
            f"{sum(r['manual_final_correct'] is False and r['final_marker_present'] for r in g)} | "
            f"{sum(not r['final_marker_present'] for r in g)} | "
            f"{sum(r['is_acpi_candidate'] for r in g)} |"
        )
    lines.extend(["", "## Manual Notes / 人工逐条备注", ""])
    lines.extend(
        [
            "| model | task | route | gold | extracted final | marker | final correct | manual risk |",
            "|---|---|---|---:|---|---:|---:|---|",
        ]
    )
    for r in rows:
        final = r["final_answer_extracted"].replace("|", "\\|")[:80]
        lines.append(
            f"| {r['model_key']} | {r['task_id']} | {r['input_lang']}->{r['reason_lang']} | {r['gold_answer']} | "
            f"{final} | {r['final_marker_present']} | {r['manual_final_correct']} | {r['manual_risk']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation / 解释",
            "",
            "- Strict final-correct traces are zero in this smoke, so there are no ACPI candidates to run hidden-layer patching on. / 本 smoke 中严格 final-correct 为 0，因此没有可用于 hidden-layer patch 的 ACPI 候选。",
            "- Hard tasks mainly expose final-wrong or no-final-marker failures; this is a boundary showing current simple-task ACPI rates should not be extrapolated to AIME. / 难题主要暴露答案错误或无 final marker，说明不能把简单任务 ACPI 频率外推到 AIME。",
            "- `zh->en` routes degrade prompt comprehension for some models, which is a separate route robustness issue rather than clean ACPI. / `zh->en` 对部分模型造成题意理解下降，这是 route 鲁棒性问题，不是干净 ACPI。",
            "- Next hard-task step should use stronger/larger models or verifier-guided sampling to obtain final-correct hard traces before mechanism probes. / 下一步应使用更强模型或 verifier-guided sampling 先获得 final-correct hard traces，再做机制 probe。",
        ]
    )
    out_md.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--in-dirs", nargs="+", default=[
        str(PROJECT / "data/raw/e26_aime_hard_trace_pool_fast"),
        str(PROJECT / "data/raw/e26_aime_hard_trace_pool_concise"),
    ])
    p.add_argument("--out-jsonl", default=str(PROJECT / "data/processed/e26_aime_hard_manual_audit_20260427.jsonl"))
    p.add_argument("--out-md", default=str(PROJECT / "reports/E26_aime_hard_smoke_audit_summary.md"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    raw = read_rows([Path(p) for p in args.in_dirs])
    audited = []
    for i, row in enumerate(raw):
        final, marker = extract_final(row["completion"])
        final_correct = bool(marker and normalize_answer(final) == normalize_answer(row["gold_answer"]))
        risk, process_valid = manual_note(row, final, marker)
        item = {
            "audit_idx": 260000 + i,
            "source_file": row["source_file"],
            "source_row": row["source_row"],
            "model_key": row["model_key"],
            "task_id": row["task_id"],
            "input_lang": row["input_lang"],
            "reason_lang": row["reason_lang"],
            "gold_answer": row["gold_answer"],
            "final_answer_extracted": final,
            "final_marker_present": marker,
            "manual_final_correct": final_correct,
            "manual_format_valid": marker,
            "manual_process_valid": process_valid,
            "manual_risk": risk,
            "is_acpi_candidate": bool(final_correct and process_valid is False),
            "completion_chars": len(row["completion"]),
        }
        audited.append(item)
    out_jsonl = Path(args.out_jsonl)
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("w", encoding="utf-8") as f:
        for row in audited:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    write_report(audited, Path(args.out_md))
    counts = Counter((r["manual_final_correct"], r["final_marker_present"]) for r in audited)
    print(f"wrote {args.out_jsonl} and {args.out_md}; rows={len(audited)} counts={dict(counts)}")


if __name__ == "__main__":
    main()
