#!/usr/bin/env python3
"""Build the E57 hard-task manual audit file.

The input file already contains only strict final-correct rows harvested from
the three P0 models.  This script adds a conservative human-style process
audit with two labels:

* strict: any visible wrong mathematical claim makes the row invalid;
* repaired: explicit self-corrections are allowed if the final surviving
  derivation is mathematically sound.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
IN_PATH = PROJECT / "data/processed/e57_final_correct_rows_for_manual_audit_20260428.jsonl"
OUT_PATH = PROJECT / "data/processed/e57_final_correct_manual_audit_20260428.jsonl"
SUMMARY_PATH = PROJECT / "reports/E57_HARD_TASK_MANUAL_AUDIT_20260428.md"


STRICT_FALSE_REPAIRED_TRUE: dict[int, tuple[str, str, str]] = {
    56: (
        "repaired_wrong_initial_answer",
        "Final answer: 12",
        "开头先写了错误最终答案 12，后文重新核对并改成 70；最终推导有效，但严格 trace 中出现了错误答案行。",
    ),
    57: (
        "repaired_wrong_initial_answer",
        "Final answer: 14",
        "开头先写了错误最终答案 14，后文检查后改成 70；最终推导有效，但严格 trace 中出现了错误答案行。",
    ),
    58: (
        "repaired_wrong_initial_answer",
        "Final answer: 21",
        "开头先写了错误最终答案 21，后文多次核对后改成 70；最终推导有效，但严格 trace 中出现了错误答案行。",
    ),
    67: (
        "repaired_wrong_initial_answer",
        "Final answer: 504",
        "开头先写了错误最终答案 504，后文正确求得余数 16 并显式更正；最终推导有效，但严格 trace 中出现了错误答案行。",
    ),
    68: (
        "repaired_wrong_initial_answer",
        "Final answer: 1260",
        "开头先写了错误最终答案 1260，后文正确求得余数 16 并显式更正；最终推导有效，但严格 trace 中出现了错误答案行。",
    ),
    69: (
        "repaired_wrong_initial_answer",
        "Final answer: 420",
        "开头先写了错误最终答案 420，后文正确求得余数 16 并显式更正；最终推导有效，但严格 trace 中出现了错误答案行。",
    ),
    70: (
        "repaired_wrong_initial_answer",
        "Final answer: 1260",
        "开头先写了错误最终答案 1260，后文正确求得余数 16 并显式更正；最终推导有效，但严格 trace 中出现了错误答案行。",
    ),
    85: (
        "repaired_enumeration_count_error",
        "There are 14 such subsets in total",
        "中途错误声称有 14 个四元子集，随后重新列举并更正为 8 个；最终组合计数有效，但严格 trace 中出现了错误枚举结论。",
    ),
    94: (
        "repaired_wrong_initial_answer",
        "Final answer: 162",
        "开头先写了错误最终答案 162，后文完整几何推导得到 504 并显式更正；最终推导有效，但严格 trace 中出现了错误答案行。",
    ),
}


STRICT_FALSE_REPAIRED_FALSE: dict[int, tuple[str, str, str]] = {
    28: (
        "unrepaired_wrong_factorization_sign",
        "(3x - 2y)(4x + 3y) = 0",
        "把 12x^2-xy-6y^2 错因式分解成符号相反的两条直线；计数因对称性碰巧仍为 117，但推理过程没有修复。",
    ),
    29: (
        "unrepaired_wrong_factorization",
        "(4x + y)(3x - y) = 0",
        "错误因式分解并得到错误直线 y=4x、y=3x；两个错误直线的边界计数碰巧给出 117，但推理过程无效且未修复。",
    ),
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")


def pct(num: int, den: int) -> str:
    return f"{num / den:.3f}" if den else "NA"


def main() -> None:
    rows = load_jsonl(IN_PATH)
    audited: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        if idx in STRICT_FALSE_REPAIRED_FALSE:
            error_type, span, note = STRICT_FALSE_REPAIRED_FALSE[idx]
            strict_valid = False
            repaired_valid = False
            repair_present = False
        elif idx in STRICT_FALSE_REPAIRED_TRUE:
            error_type, span, note = STRICT_FALSE_REPAIRED_TRUE[idx]
            strict_valid = False
            repaired_valid = True
            repair_present = True
        else:
            error_type = "none"
            span = ""
            note = "人工审计未发现数学步骤错误；若有格式性自检或 leading-zero 写法，不计为过程错误。"
            strict_valid = True
            repaired_valid = True
            repair_present = False

        out = dict(row)
        out.update(
            {
                "manual_audit_idx": idx,
                "manual_audit_status": "audited",
                "manual_auditor": "codex_manual_20260428",
                "manual_process_valid_strict": strict_valid,
                "manual_process_valid_repaired": repaired_valid,
                "manual_repair_present": repair_present,
                "manual_error_type": error_type,
                "manual_error_span": span,
                "manual_audit_note_zh": note,
                "manual_acpi_strict": bool(row.get("manual_final_correct")) and not strict_valid,
                "manual_acpi_unrepaired": bool(row.get("manual_final_correct")) and not repaired_valid,
            }
        )
        audited.append(out)

    write_jsonl(OUT_PATH, audited)

    overall = Counter()
    by_model: dict[str, Counter] = defaultdict(Counter)
    by_task: dict[str, Counter] = defaultdict(Counter)
    by_variant: dict[str, Counter] = defaultdict(Counter)
    error_types = Counter()
    for row in audited:
        buckets = [overall, by_model[row["model_key"]], by_task[row["task_id"]], by_variant[row["prompt_variant"]]]
        for bucket in buckets:
            bucket["n"] += 1
            bucket["strict_valid"] += int(row["manual_process_valid_strict"])
            bucket["repaired_valid"] += int(row["manual_process_valid_repaired"])
            bucket["strict_acpi"] += int(row["manual_acpi_strict"])
            bucket["unrepaired_acpi"] += int(row["manual_acpi_unrepaired"])
            bucket["repair_present"] += int(row["manual_repair_present"])
        error_types[row["manual_error_type"]] += 1

    def table(title: str, data: dict[str, Counter]) -> list[str]:
        lines = [f"### {title}", "", "| slice | n | strict valid | repaired valid | strict ACPI | unrepaired ACPI | repair-present |", "|---|---:|---:|---:|---:|---:|---:|"]
        for key, c in sorted(data.items()):
            n = c["n"]
            lines.append(
                f"| `{key}` | {n} | {c['strict_valid']} ({pct(c['strict_valid'], n)}) | "
                f"{c['repaired_valid']} ({pct(c['repaired_valid'], n)}) | "
                f"{c['strict_acpi']} ({pct(c['strict_acpi'], n)}) | "
                f"{c['unrepaired_acpi']} ({pct(c['unrepaired_acpi'], n)}) | "
                f"{c['repair_present']} ({pct(c['repair_present'], n)}) |"
            )
        return lines

    now = datetime.now().isoformat(timespec="seconds")
    lines = [
        "# E57 Hard-Task Manual Audit / E57 困难题人工过程审计（2026-04-28）",
        "",
        f"- Input / 输入：`{IN_PATH.relative_to(PROJECT)}`",
        f"- Output / 输出：`{OUT_PATH.relative_to(PROJECT)}`",
        f"- Created / 创建时间：{now}",
        "- Scope / 范围：只审计 E57 中 strict final-correct 的 119 条 P0 hard-task trace；prompt 中没有 gold answer，也没有 trap note。",
        "- Strict label / 严格标签：只要可见 trace 中出现错误数学结论、错误最终答案行或错误枚举结论，就记为 process-invalid。",
        "- Repaired label / 修复后标签：如果 trace 明确发现并修正错误，且最终保留下来的推导正确，则记为 repaired-valid；这样可以区分“真的乱推碰巧对”和“先错后自我修复”。",
        "",
        "## Overall / 总体",
        "",
        "| n | strict valid | repaired valid | strict ACPI | unrepaired ACPI | repair-present |",
        "|---:|---:|---:|---:|---:|---:|",
        (
            f"| {overall['n']} | {overall['strict_valid']} ({pct(overall['strict_valid'], overall['n'])}) | "
            f"{overall['repaired_valid']} ({pct(overall['repaired_valid'], overall['n'])}) | "
            f"{overall['strict_acpi']} ({pct(overall['strict_acpi'], overall['n'])}) | "
            f"{overall['unrepaired_acpi']} ({pct(overall['unrepaired_acpi'], overall['n'])}) | "
            f"{overall['repair_present']} ({pct(overall['repair_present'], overall['n'])}) |"
        ),
        "",
        "说人话：困难题里 final-correct trace 并不稀有，但绝大多数过程是有效的；严格口径下有一批“先写错后修复”的 trace。真正未修复、靠错误过程碰巧得到正确答案的 ACPI 目前只发现 2 条，均来自 Gemma4-26B-A4B 的整数对二次方程题。",
        "",
        "## Error Types / 错误类型",
        "",
        "| error type | count |",
        "|---|---:|",
    ]
    for key, count in sorted(error_types.items()):
        lines.append(f"| `{key}` | {count} |")
    lines += [""] + table("By Model / 按模型", by_model)
    lines += [""] + table("By Task / 按题目", by_task)
    lines += [""] + table("By Prompt Variant / 按 prompt 变体", by_variant)
    lines += [
        "",
        "## Clear Unrepaired ACPI Rows / 明确未修复 ACPI 行",
        "",
        "| audit idx | model | task | variant | error span | note |",
        "|---:|---|---|---|---|---|",
    ]
    for row in audited:
        if row["manual_acpi_unrepaired"]:
            lines.append(
                f"| {row['manual_audit_idx']} | `{row['model_key']}` | `{row['task_id']}` | "
                f"`{row['prompt_variant']}` | `{row['manual_error_span']}` | {row['manual_audit_note_zh']} |"
            )
    lines += [
        "",
        "## Boundary / 边界",
        "",
        "- 这些 hard-task trace 是模型自然生成、无 gold prompt 的 final-correct 子集，不是受控构造；因此可以回答“困难题 final-correct 后是否会出现 ACPI”。",
        "- 由于只审计 final-correct 行，不能从本文件估计整体解题准确率；整体 final-correct 率仍以 E57 原始结果 summary 为准。",
        "- 严格 ACPI 与 unrepaired ACPI 必须分开报告：严格 ACPI 包含先错后修复的 visible trace；unrepaired ACPI 更接近“答案对但过程确实错且未改”。",
    ]
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"out": str(OUT_PATH), "report": str(SUMMARY_PATH), "overall": dict(overall), "error_types": dict(error_types)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
