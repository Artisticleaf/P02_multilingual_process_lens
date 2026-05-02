#!/usr/bin/env python3
"""Manual-style audit for E30 non-discount lexical grid.

This is intentionally conservative: it promotes only explicitly reviewed rows to
paper-grade ACPI and records other rows as clean, final-wrong drift, format issues,
or prompt/template boundaries.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]

ANSWER_VARIANTS = {
    "3": ["3", "3个", "3 points"],
    "4": ["4", "4个", "4 integers", "4 possible", "四"],
    "5": ["5", "5个"],
    "6": ["6", "6个", "6 integers", "6.", "六"],
    "7": ["7"],
    "9": ["9"],
    "10": ["10", "10种"],
    "12": ["12", "12名", "12 students", "12 boys"],
    "18": ["18", "18双", "18 pairs"],
    "20": ["20", "20名", "20 students", "20 assignments", "20种"],
    "25pi": ["25pi", "25*pi", "25π", "25\\pi", "25 pi"],
    "30": ["30", "30名", "30 students", "30 million", "30个"],
    "36": ["36", "36只", "36 socks"],
    "100pi": ["100pi", "100*pi", "100π", "100\\pi", "100 pi"],
    "(-2,3)": ["(-2,3)", "(-2, 3)", "（-2，3）"],
}

# Manually reviewed rows that contain a local process-semantic error while the
# final answer is correct. Keep this list small and paper-grade.
MANUAL_ACPI = {
    (
        "qwen3_14b_base",
        "inequality_no_more_than",
        "zh->en",
        1,
    ): {
        "manual_risk": "acpi_strict_lower_rephrased_as_between_inclusive_but_list_excludes_3",
        "earliest_error": "between 3 and 7, inclusive",
        "manual_correction": "The original condition is greater than 3 and no more than 7, so 3 is excluded. Saying between 3 and 7 inclusive would include 3, even though the trace then lists 4,5,6,7 and gives the correct final count.",
        "paper_grade_acpi": True,
    },
}

# Final-wrong semantic drifts that were manually spot-checked.
SEMANTIC_DRIFT_FINAL_WRONG = {
    ("gemma4_e4b_it", "unit_dozen_pairs", "zh->zh", 0): "treats 36 individual socks as 36 pairs after correctly computing 3 dozen = 36 socks",
    ("gemma4_e4b_it", "unit_dozen_pairs", "zh->zh", 1): "treats 3 dozen socks as 36 pairs instead of 36 individual socks = 18 pairs",
    ("gemma4_e4b_it", "unit_dozen_pairs", "zh->en", 0): "treats 3 dozen socks as 36 pairs instead of 36 individual socks = 18 pairs",
    ("gemma4_e4b_it", "unit_dozen_pairs", "zh->en", 1): "treats 3 dozen socks as 36 pairs instead of 36 individual socks = 18 pairs",
    ("qwen25_math_7b_instruct", "unit_dozen_pairs", "zh->zh", 0): "states one dozen socks equals 12 pairs, causing 36 pairs instead of 18 pairs",
}

FORMAT_BOUNDARY_MODELS = {"phi4_mini_reasoning"}


def normalize_answer(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text)).lower().strip()
    text = re.sub(r"\\boxed\{([^{}]+)\}", r"\1", text)
    text = text.replace("π", "pi").replace("美元", "").replace("名", "").replace("个", "")
    text = text.replace("双", "").replace("只", "").replace("平方厘米", "")
    text = text.replace("students", "").replace("student", "").replace("pairs", "").replace("pair", "")
    text = text.replace("socks", "").replace("sock", "").replace(" ", "")
    text = text.replace("\\pi", "pi")
    text = re.sub(r"[^0-9a-z+*./(),-]", "", text)
    return text


def extract_final(text: str) -> tuple[str, str]:
    matches = re.findall(r"final\s*answer\s*[:：]\s*([^\n\r]+)", text, flags=re.I)
    if matches:
        return matches[-1].strip(), "final_answer"
    boxed = re.findall(r"\\boxed\{([^{}]+)\}", text)
    if boxed:
        return boxed[-1].strip(), "boxed"
    zh = re.findall(r"(?:最终答案|答案|结果)(?:是|为|：|:)\s*([^\n\r。]+)", text)
    if zh:
        return zh[-1].strip(), "zh_answer_phrase"
    return "", "none"


def final_correct(answer: str, gold: str) -> bool:
    n = normalize_answer(answer)
    for variant in ANSWER_VARIANTS.get(str(gold), [str(gold)]):
        nv = normalize_answer(variant)
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


def problem_from_prompt(prompt: str) -> str:
    """Recover the user-facing problem from the generation prompt."""
    m = re.search(r"题目[:：]\s*(.*?)\n推理[:：]", prompt, flags=re.S)
    if m:
        return m.group(1).strip()
    m = re.search(r"Problem:\s*(.*?)\nReasoning:", prompt, flags=re.S)
    if m:
        return m.group(1).strip()
    return prompt.strip()


def audit_one(row: dict[str, Any], audit_idx: int) -> dict[str, Any]:
    text = row.get("completion", "") or ""
    route = f"{row['input_lang']}->{row['reason_lang']}"
    key = (row["model_key"], row["task_id"], route, int(row["sample_idx"]))
    final, final_source = extract_final(text)
    fc = final_correct(final, row["gold_answer"]) if final_source != "none" else False
    rv = route_valid(text, row["reason_lang"])
    meta = text.lstrip().startswith("<think>") or text.lstrip().startswith("Thinking Process")

    process_valid: bool | None = True
    risk = "valid_clean"
    earliest_error = None
    correction = ""
    paper_grade = False
    semantic_drift = False

    if row["model_key"] in FORMAT_BOUNDARY_MODELS and meta and final_source == "none":
        process_valid = None
        risk = "format_boundary_hidden_think_no_final_marker"
        correction = "Reasoning is hidden/long <think> text and no parseable final answer was produced within the generation budget."
    elif final_source == "none":
        process_valid = None
        risk = "no_parseable_final_answer"
    elif key in MANUAL_ACPI:
        o = MANUAL_ACPI[key]
        process_valid = False
        risk = o["manual_risk"]
        earliest_error = o["earliest_error"]
        correction = o["manual_correction"]
        paper_grade = bool(o["paper_grade_acpi"])
    elif key in SEMANTIC_DRIFT_FINAL_WRONG:
        process_valid = False
        risk = "semantic_drift_final_wrong"
        earliest_error = SEMANTIC_DRIFT_FINAL_WRONG[key]
        correction = "Surface lexical/unit semantics changed the intended process and the final answer became wrong, so this is not ACPI."
        semantic_drift = True
    elif not fc:
        process_valid = False
        risk = "final_wrong_no_acpi"
    elif not rv:
        process_valid = True
        risk = "final_correct_process_valid_but_route_violation"
    elif final_source != "final_answer":
        process_valid = True
        risk = "valid_process_but_format_noncompliant"
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
        "problem": problem_from_prompt(str(row.get("prompt", ""))),
        "final_answer_extracted": final,
        "final_source": final_source,
        "manual_final_correct": fc,
        "manual_process_valid": process_valid,
        "manual_format_valid": bool(final_source == "final_answer" and not meta),
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
    by_family = defaultdict(list)
    for r in rows:
        by_model[r["model_key"]].append(r)
        by_task[r["task_id"]].append(r)
        by_family[r["task_id"].split("_")[0]].append(r)
    lines = [
        "# E30 Non-Discount Lexical Grid Audit / E30 非折扣词汇网格审计",
        "",
        f"Created / 创建时间: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Scope / 范围: 4 generator models, 24 non-discount lexical tasks, 2 routes (`zh->zh`, `zh->en`), k=2. Total 384 rows. / 4 个生成模型、24 个非折扣词汇任务、2 条 route、每格 2 条样本，总计 384 行。",
        "",
        "## Model-Level Summary / 模型级汇总",
        "",
        "| model | n | parseable final | final correct | format-valid usable | process invalid | ACPI | paper-grade ACPI | semantic drift final-wrong | route violations among usable |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model, g in sorted(by_model.items()):
        usable = [r for r in g if r["manual_process_valid"] is not None and r["manual_format_valid"]]
        lines.append(
            f"| {model} | {len(g)} | {sum(r['final_source'] != 'none' for r in g)} | "
            f"{sum(r['manual_final_correct'] for r in g)} | {len(usable)} | "
            f"{sum(r['manual_process_valid'] is False for r in g)} | {sum(r['is_acpi'] for r in g)} | "
            f"{sum(r['paper_grade_acpi'] for r in g)} | {sum(r['semantic_drift_final_wrong'] for r in g)} | "
            f"{sum(not r['manual_route_valid'] for r in usable)} |"
        )
    lines.extend([
        "",
        "## Human-Readable Findings / 人话发现",
        "",
        "- E30 broadened beyond discount into ratio, inequality, interval, average/total, geometry, unit, combinatorics, and operator-word tasks. / E30 从折扣扩展到比例、量词、区间、平均/总量、几何、单位、组合和算子词任务。",
        "- In this first natural-generation pass, clean non-discount ACPI was rare: one paper-grade Qwen14 inequality row was promoted. / 第一轮自然生成中，干净非折扣 ACPI 很少：目前只提升 1 条论文级 Qwen14 不等式样例。",
        "- The strongest non-discount natural drift was unit semantics: Gemma4 repeatedly treated 3 dozen individual socks as 36 pairs instead of 18 pairs, but those rows were final-wrong rather than ACPI. / 最强非折扣自然漂移来自单位语义：Gemma4 多次把 3 打袜子当成 36 双而不是 18 双，但这些是答案错误，不是 ACPI。",
        "- Phi4 and Qwen2.5-Math often produced hidden-think or non-`Final answer` formats, so they are boundary/control generators in this pass. / Phi4 与 Qwen2.5-Math 常输出 hidden-think 或非 `Final answer` 格式，本轮更适合作为边界/控制生成器。",
        "",
        "## Paper-Grade ACPI Rows / 论文级 ACPI 行",
        "",
        "| audit idx | model | task | route | sample | final | earliest error | why it matters |",
        "|---:|---|---|---|---:|---|---|---|",
    ])
    for r in rows:
        if r["paper_grade_acpi"]:
            lines.append(
                f"| {r['audit_idx']} | {r['model_key']} | {r['task_id']} | {r['route']} | {r['sample_idx']} | "
                f"{str(r['final_answer_extracted']).replace('|','/')[:80]} | {str(r['earliest_error']).replace('|','/')[:100]} | "
                f"{str(r['manual_correction']).replace('|','/')[:220]} |"
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
                f"{r['gold_answer']} | {str(r['final_answer_extracted']).replace('|','/')[:80]} | {str(r['earliest_error']).replace('|','/')[:160]} |"
            )
    lines.extend([
        "",
        "## Task-Level Signal / 任务级信号",
        "",
        "| task | n | final correct | ACPI | semantic drift final-wrong | major risk counts |",
        "|---|---:|---:|---:|---:|---|",
    ])
    for task, g in sorted(by_task.items()):
        risks = Counter(r["manual_risk"] for r in g)
        risk_text = "; ".join(f"{k}:{v}" for k, v in risks.most_common(3)).replace("|", "/")
        lines.append(
            f"| {task} | {len(g)} | {sum(r['manual_final_correct'] for r in g)} | {sum(r['is_acpi'] for r in g)} | "
            f"{sum(r['semantic_drift_final_wrong'] for r in g)} | {risk_text} |"
        )
    lines.extend([
        "",
        "## Interpretation / 解释",
        "",
        "E30 is important because it weakens a potential overclaim: the non-discount families did not automatically reproduce the same ACPI density as discount/pay-off wording. / E30 很重要，因为它削弱了一个潜在过度主张：非折扣族没有自动复现折扣/pay-off 那样高的 ACPI 密度。",
        "",
        "The result does not kill the main claim. It refines it: natural ACPI is most visible when a local lexical phrase has two common but conflicting operational meanings and the final arithmetic can remain numerically unchanged. / 这个结果不否定主张，而是细化主张：自然 ACPI 最容易出现在局部词汇有两个常见但冲突的操作含义、且最终算术数字仍可保持不变的场景。",
        "",
        "Next step: build controlled non-discount counterfactual siblings for the strongest families, especially unit words (`dozen`/pairs), inequality boundary paraphrases, ratio denominator wording, and operator words. / 下一步应为最强非折扣族构造受控反事实 sibling，尤其是单位词、边界量词、比例分母措辞和算子词。",
    ])
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--in-dir", default=str(PROJECT / "data/raw/e30_non_discount_lexical_grid_trace_pool"))
    p.add_argument("--out-jsonl", default=str(PROJECT / "data/processed/e30_non_discount_grid_manual_audit_20260427.jsonl"))
    p.add_argument("--out-md", default=str(PROJECT / "reports/E30_non_discount_lexical_grid_audit.md"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    raw = read_rows(Path(args.in_dir))
    rows = [audit_one(r, 300000 + i) for i, r in enumerate(raw)]
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
