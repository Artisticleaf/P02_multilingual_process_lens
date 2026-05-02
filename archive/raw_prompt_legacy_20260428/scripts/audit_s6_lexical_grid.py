#!/usr/bin/env python3
"""Manual-style audit for S6 lexical paraphrase grid generations.

This script encodes the sentence-level decisions made for the high-risk rows so
that the audit is reproducible. It is not a training labeler.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]

ANSWER_VARIANTS = {
    "60": ["60", "$60", "60美元", "60 dollars"],
    "20": ["20", "$20", "20美元", "20 dollars", "<answer>20</answer>"],
    "80": ["80", "$80", "80美元", "80 dollars"],
    "40": ["40", "40名", "40 girls"],
    "2x+3": ["2x+3", "2*x+3", "2x + 3"],
    "6x+1": ["6x+1", "6*x+1", "6x + 1"],
}

# Row keys are (model, task_id, route, sample_idx). These are the rows that were
# manually read because they contained high-risk lexical cues or final-wrong drift.
MANUAL_OVERRIDES: dict[tuple[str, str, str, int], dict[str, Any]] = {
    (
        "gemma4_e4b_it",
        "disc_25_off_direct",
        "zh->zh",
        1,
    ): {
        "manual_process_valid": False,
        "manual_risk": "acpi_wrong_dabazhe_equals_75pct_in_optional_step",
        "earliest_error": "或者，如果打八折（即支付 75% 的价格）",
        "manual_correction": "25% off can be computed as pay 75%, but calling that 打八折 is wrong because 八折 means pay 80%.",
        "paper_grade_acpi": True,
    },
    (
        "gemma4_e4b_it",
        "seq_dabazhe_pay80",
        "zh->en",
        0,
    ): {
        "manual_process_valid": False,
        "manual_risk": "acpi_dabazhe_translated_as_80pct_discount_but_multiplies_0p8",
        "earliest_error": "apply an 80% discount (or multiply by 0.8)",
        "manual_correction": "The computation uses pay 80%, but the English phrase 80% discount normally means pay 20%.",
        "paper_grade_acpi": True,
    },
    (
        "qwen3_14b_base",
        "disc_pay75_en",
        "zh->en",
        0,
    ): {
        "manual_process_valid": False,
        "manual_risk": "acpi_pay75_mistranslated_as_75pct_discount_but_multiplies_0p75",
        "earliest_error": "sold at a 75% discount of its original price",
        "manual_correction": "The Chinese/meaning is sold for 75% of original price; 75% discount would mean pay 25%. The trace then multiplies by 0.75 and gets the correct final answer.",
        "paper_grade_acpi": True,
    },
    (
        "qwen3_14b_base",
        "disc_pay75_en",
        "zh->zh",
        1,
    ): {
        "manual_process_valid": True,
        "manual_risk": "valid_but_lexically_ambiguous_zhekou75",
        "earliest_error": None,
        "manual_correction": "Chinese 折扣75% is ambiguous here but the computation and source meaning are pay 75%; not counted as paper-grade ACPI.",
        "paper_grade_acpi": False,
    },
}

SEMANTIC_DRIFT_FINAL_WRONG = {
    ("gemma4_e4b_it", "disc_zh_qiwu_price", "zh->en", 0): "treats 七五折/pay75 as 75% off/pay25",
    ("gemma4_e4b_it", "disc_zh_qiwu_price", "zh->en", 1): "treats 七五折/pay75 as 75% off/pay25",
    ("gemma4_e4b_it", "disc_pay25_explicit", "zh->zh", 0): "treats pay25 as 25% off/pay75",
    ("gemma4_e4b_it", "disc_pay25_explicit", "zh->zh", 1): "treats pay25 as 25% off/pay75",
    ("gemma4_e4b_it", "disc_pay25_explicit", "zh->en", 0): "treats pay25 as 25% off/pay75",
    ("gemma4_e4b_it", "disc_pay25_explicit", "zh->en", 1): "treats pay25 as 25% off/pay75",
    ("qwen3_14b_base", "disc_zh_qiwu_price", "zh->en", 1): "treats 七五折/pay75 as 75% off/pay25",
    ("qwen3_14b_base", "disc_pay25_explicit", "zh->zh", 0): "treats pay25 as 25% off/pay75",
    ("qwen3_14b_base", "disc_pay25_explicit", "zh->zh", 1): "treats pay25 as 25% off/pay75",
    ("qwen3_14b_base", "disc_pay25_explicit", "zh->en", 0): "treats pay25 as 25% off/pay75",
    ("qwen3_14b_base", "seq_dabazhe_pay80", "zh->en", 1): "treats 打八折/pay80 as 80% discount/pay20",
}


def normalize_answer(text: str) -> str:
    text = str(text).lower().strip()
    text = re.sub(r"\\boxed\{([^{}]+)\}", r"\1", text)
    text = text.replace("美元", "").replace("dollars", "").replace("dollar", "")
    text = text.replace(" ", "")
    text = re.sub(r"[^0-9a-z+*./<>-]", "", text)
    return text


def extract_final(text: str) -> tuple[str, bool]:
    matches = re.findall(r"final\s*answer\s*[:：]\s*([^\n\r]+)", text, flags=re.I)
    usable = []
    for m in matches:
        if "<answer>" in m.lower() and re.search(r"<answer>\s*\d+\s*</answer>", m, flags=re.I):
            usable.append(m.strip())
        elif "<answer" in m.lower() or "<答案" in m:
            continue
        else:
            usable.append(m.strip())
    if usable:
        return usable[-1], True
    return "", False


def final_correct(answer: str, gold: str) -> bool:
    variants = ANSWER_VARIANTS.get(str(gold), [str(gold)])
    n = normalize_answer(answer)
    for v in variants:
        nv = normalize_answer(v)
        if nv and (nv in n or n in nv):
            return True
    return False


def zh_chars(text: str) -> int:
    return sum("\u4e00" <= ch <= "\u9fff" for ch in text)


def latin_letters(text: str) -> int:
    return sum("a" <= ch.lower() <= "z" for ch in text)


def route_valid(text: str, reason_lang: str) -> bool:
    z = zh_chars(text)
    l = latin_letters(text)
    if z + l == 0:
        return False
    if reason_lang == "zh":
        return z / (z + l) >= 0.55
    return l / (z + l) >= 0.65


def read_rows(in_dir: Path) -> list[dict[str, Any]]:
    out = []
    for path in sorted(in_dir.glob("*trace_pool_smoke*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for i, row in enumerate(data["rows"]):
            item = dict(row)
            item["source_file"] = str(path)
            item["source_row"] = i
            out.append(item)
    return out


def audit_one(row: dict[str, Any], audit_idx: int) -> dict[str, Any]:
    text = row.get("completion", "")
    route = f"{row['input_lang']}->{row['reason_lang']}"
    key = (row["model_key"], row["task_id"], route, int(row["sample_idx"]))
    final, marker = extract_final(text)
    fc = final_correct(final, row["gold_answer"]) if marker else False
    rv = route_valid(text, row["reason_lang"])
    meta = text.lstrip().startswith("Thinking Process") or text.lstrip().startswith("<think>")

    process_valid: bool | None = True
    risk = "valid_clean_or_minor_style_issue"
    earliest_error = None
    correction = ""
    paper_grade = False
    semantic_drift = False

    if row["model_key"] == "deepseek_r1_0528_qwen3_8b":
        fc = False
        process_valid = None
        risk = "unusable_prompt_corruption_tokenizer_artifact"
        correction = "Completion is prompt-corrupted meta text, not an auditable reasoning trace."
    elif row["model_key"] == "qwen35_9b" and meta:
        fc = False
        process_valid = None
        risk = "unusable_meta_planning_thinking_process"
        correction = "Completion analyzes the prompt/instructions as a Thinking Process rather than giving a clean reasoning trace."
    elif key in MANUAL_OVERRIDES:
        o = MANUAL_OVERRIDES[key]
        process_valid = o["manual_process_valid"]
        risk = o["manual_risk"]
        earliest_error = o.get("earliest_error")
        correction = o.get("manual_correction", "")
        paper_grade = bool(o.get("paper_grade_acpi", False))
    elif key in SEMANTIC_DRIFT_FINAL_WRONG:
        process_valid = False
        risk = "semantic_drift_final_wrong"
        earliest_error = SEMANTIC_DRIFT_FINAL_WRONG[key]
        correction = "Surface lexicalization changed pay/off semantics and the final answer became wrong, so this is not ACPI."
        semantic_drift = True
    elif not marker:
        process_valid = None
        risk = "no_final_marker_or_unparsed"
    elif not fc:
        process_valid = False
        if row["task_id"] == "disc_zh_qiwu_price" and row["model_key"] == "qwen3_14b_base" and route == "zh->zh" and int(row["sample_idx"]) == 0:
            risk = "arithmetic_final_wrong_80_times_0p75_as_75"
            earliest_error = "80 * 0.75 = 75"
        else:
            risk = "final_wrong_no_acpi"
    elif not rv:
        process_valid = True
        risk = "final_correct_process_valid_but_route_violation"
    else:
        process_valid = True
        risk = "valid_clean"

    is_acpi = bool(fc and process_valid is False)
    return {
        "audit_idx": audit_idx,
        "source_file": row["source_file"],
        "source_row": row["source_row"],
        "model_key": row["model_key"],
        "task_id": row["task_id"],
        "input_lang": row["input_lang"],
        "reason_lang": row["reason_lang"],
        "route": route,
        "sample_idx": row["sample_idx"],
        "gold_answer": row["gold_answer"],
        "final_answer_extracted": final,
        "final_marker_present": marker,
        "manual_final_correct": fc,
        "manual_process_valid": process_valid,
        "manual_format_valid": bool(marker and not meta and not text.lstrip().startswith("<think>")),
        "manual_route_valid": rv,
        "manual_risk": risk,
        "earliest_error": earliest_error,
        "manual_correction": correction,
        "paper_grade_acpi": paper_grade,
        "is_acpi": is_acpi,
        "semantic_drift_final_wrong": semantic_drift,
        "completion_chars": len(text),
        "completion": text,
    }


def write_report(rows: list[dict[str, Any]], out_md: Path) -> None:
    by_model = defaultdict(list)
    by_task = defaultdict(list)
    for r in rows:
        by_model[r["model_key"]].append(r)
        by_task[r["task_id"]].append(r)

    lines = [
        "# S6 Lexical Paraphrase Grid Audit / S6 表层词汇改写网格审计",
        "",
        f"Created / 创建时间: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Scope / 范围: 4 generator models, 12 paraphrase/control tasks, 2 routes (`zh->zh`, `zh->en`), k=2. Total 192 rows. / 4 个生成模型、12 个改写/控制任务、2 条 route、每格 2 条样本，总计 192 行。",
        "",
        "## Model-Level Summary / 模型级汇总",
        "",
        "| model | n | usable trace | final correct | process invalid | ACPI | paper-grade ACPI | semantic drift final-wrong | route violations |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model, g in sorted(by_model.items()):
        usable = [r for r in g if r["manual_process_valid"] is not None and r["manual_format_valid"]]
        lines.append(
            f"| {model} | {len(g)} | {len(usable)} | "
            f"{sum(r['manual_final_correct'] for r in g)} | "
            f"{sum(r['manual_process_valid'] is False for r in g)} | "
            f"{sum(r['is_acpi'] for r in g)} | "
            f"{sum(r['paper_grade_acpi'] for r in g)} | "
            f"{sum(r['semantic_drift_final_wrong'] for r in g)} | "
            f"{sum(not r['manual_route_valid'] for r in usable)} |"
        )
    lines.extend([
        "",
        "## Human-Readable Findings / 人话发现",
        "",
        "- Qwen3.5-9B and DeepSeek-Qwen8B did not produce clean auditable traces in this prompt setting: Qwen3.5-9B mostly wrote meta `Thinking Process` plans; DeepSeek emitted prompt-corrupted `<think>` text. / 在此提示设置下，Qwen3.5-9B 主要输出元规划，DeepSeek 输出提示损坏文本，因此不纳入 ACPI 生成率。",
        "- Gemma4 produced two paper-grade ACPI rows: one says `打八折` means paying 75% on a 25%-off task, and one translates `打八折` as `80% discount` while multiplying by 0.8. / Gemma4 产生两条论文级 ACPI。",
        "- Qwen14 produced one paper-grade ACPI row: it translates `sold for 75% of original price` into `75% discount` but still multiplies by 0.75 and gets 60. / Qwen14 产生一条论文级 ACPI。",
        "- Several final-wrong semantic drifts also appeared: especially `七五折/pay75 -> 75% off/pay25`, `pay25 -> 25% off/pay75`, and `打八折/pay80 -> 80% discount/pay20`. / 另有多条答案错误的语义漂移。",
        "",
        "## Paper-Grade ACPI Rows / 论文级 ACPI 行",
        "",
        "| audit idx | model | task | route | sample | final | earliest error | why it matters |",
        "|---:|---|---|---|---:|---|---|---|",
    ])
    for r in rows:
        if r["paper_grade_acpi"]:
            err = str(r["earliest_error"] or "").replace("|", "\\|")
            corr = str(r["manual_correction"] or "").replace("|", "\\|")
            lines.append(
                f"| {r['audit_idx']} | {r['model_key']} | {r['task_id']} | {r['route']} | {r['sample_idx']} | "
                f"{str(r['final_answer_extracted']).replace('|','\\|')[:60]} | {err[:90]} | {corr[:160]} |"
            )
    lines.extend([
        "",
        "## Semantic-Drift Final-Wrong Rows / 语义漂移但答案错误行",
        "",
        "| audit idx | model | task | route | sample | gold | final | drift |",
        "|---:|---|---|---|---:|---|---|---|",
    ])
    for r in rows:
        if r["semantic_drift_final_wrong"]:
            lines.append(
                f"| {r['audit_idx']} | {r['model_key']} | {r['task_id']} | {r['route']} | {r['sample_idx']} | "
                f"{r['gold_answer']} | {str(r['final_answer_extracted']).replace('|','\\|')[:60]} | {str(r['earliest_error']).replace('|','\\|')[:120]} |"
            )
    lines.extend([
        "",
        "## Task-Level Signal / 任务级信号",
        "",
        "| task | n | final correct | ACPI | semantic drift final-wrong |",
        "|---|---:|---:|---:|---:|",
    ])
    for task, g in sorted(by_task.items()):
        lines.append(
            f"| {task} | {len(g)} | {sum(r['manual_final_correct'] for r in g)} | {sum(r['is_acpi'] for r in g)} | {sum(r['semantic_drift_final_wrong'] for r in g)} |"
        )
    lines.extend([
        "",
        "## Interpretation / 解释",
        "",
        "This S6 grid strengthens the lexical-causality story: the same arithmetic answers reappear under different surface forms, but specific pay/off lexicalizations flip the process semantics. / S6 网格强化了词汇因果故事：相同算术答案在不同表层形式下出现，但 pay/off 词汇化会翻转过程语义。",
        "",
        "This is still a targeted grid, not a population prevalence estimate. The usable generator rows are mainly Gemma4 and Qwen14 in this run; Qwen3.5-9B and DeepSeek need prompt/template fixes before generator-side conclusions. / 这仍是定向网格，不是总体发生率；本轮可用生成行主要来自 Gemma4 和 Qwen14。",
    ])
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--in-dir", default=str(PROJECT / "data/raw/s6_lexical_grid_trace_pool"))
    p.add_argument("--out-jsonl", default=str(PROJECT / "data/processed/s6_lexical_grid_manual_audit_20260427.jsonl"))
    p.add_argument("--out-md", default=str(PROJECT / "reports/S6_lexical_paraphrase_grid_audit.md"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    raw = read_rows(Path(args.in_dir))
    rows = [audit_one(r, 600000 + i) for i, r in enumerate(raw)]
    out = Path(args.out_jsonl)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    write_report(rows, Path(args.out_md))
    print(f"wrote {args.out_jsonl} and {args.out_md}; rows={len(rows)}")
    print(Counter(r["manual_risk"] for r in rows))


if __name__ == "__main__":
    main()
