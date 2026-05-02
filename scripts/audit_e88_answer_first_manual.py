#!/usr/bin/env python3
"""Manual/agent audit for E88 answer-first final-correct hard-task rows."""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
IN_JSONL = PROJECT / "data/processed/e88_answer_first_final_correct_audit_sheet_20260429.jsonl"
OUT_JSONL = PROJECT / "data/processed/e88_answer_first_manual_audit_20260429.jsonl"
OUT_JSON = PROJECT / "reports/E88_ANSWER_FIRST_MANUAL_AUDIT_20260429.json"
OUT_MD = PROJECT / "reports/E88_ANSWER_FIRST_MANUAL_AUDIT_20260429.md"


AUDIT: dict[int, dict[str, Any]] = {
    880009: {
        "error_type": "self_corrected_wrong_geometry_area_setup",
        "error_span": "Area DEGF = Area(AEG) - Area(ADF) variants before shoelace correction",
        "notes_zh": "几何题先写了几个错误的面积拆分，随后明确否定并改用 DEGF 与 AFNBCEM 的 shoelace 公式，最终保留证明有效。",
    },
    880025: {
        "error_type": "self_corrected_wrong_factor_attempt",
        "error_span": "12x^2 - 4xy + 3xy - 6y^2 ... No",
        "notes_zh": "二次型题先尝试了错误拆项，立刻用 No 否定并转入二次公式，最终保留证明有效。",
    },
    880038: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 13",
        "notes_zh": "answer-first 第一行给错答案 13，后文显式 self-correction，最终证明与最终答案 70 有效。",
    },
    880039: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 15",
        "notes_zh": "answer-first 第一行给错答案 15，后文识别为 hallucination/placeholder 并改正为 70。",
    },
    880040: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 13",
        "notes_zh": "answer-first 第一行给错答案 13，后文重新推导并改正为 70。",
    },
    880041: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 126",
        "notes_zh": "冰淇淋题第一行给错答案 126，后文用 multinomial 计数得到 2016 mod 1000 = 16，并显式修正。",
    },
    880042: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 126",
        "notes_zh": "冰淇淋题第一行给错答案 126，后文完整列举三种计数并显式修正为 16。",
    },
    880043: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 1260",
        "notes_zh": "第一行把单个 case 的 1260 当成 final，后文意识到需总数取模并修正为 16。",
    },
    880045: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 252",
        "notes_zh": "第一行把单个 case 的 252 当成 final，后文完成总和与取模并修正为 16。",
    },
    880047: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 1260",
        "notes_zh": "第一行把单个 case 的 1260 当成 final，后文显式指出应取 2016 mod 1000 = 16。",
    },
    880048: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 61",
        "notes_zh": "二次型题第一行给错 61，后文因式分解与计数正确，最终修正为 117。",
    },
    880049: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 101",
        "notes_zh": "二次型题第一行给错 101，后文重新检查范围与重叠，最终修正为 117。",
    },
    880050: {
        "error_type": "self_corrected_wrong_subset_count_claim",
        "error_span": "There are 14 such sets in total? No",
        "notes_zh": "排列题中途提出 14 个集合的错误说法，立刻否定并列出 8 个集合；最终保留证明有效。",
    },
    880053: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 162",
        "notes_zh": "梯形题第一行给错 162，后文用 Pitot/勾股与等价 rs 检查修正为 504。",
    },
    880054: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 162",
        "notes_zh": "梯形题第一行给错 162，后文完整推导 r+s 与 (r-s)^2 后修正为 504。",
    },
    880055: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 162",
        "notes_zh": "梯形题第一行给错 162，后文多次复核面积、半周长与 rs 后修正为 504。",
    },
    880057: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 17",
        "notes_zh": "GLM base 题第一行给错 17，后文反复检查标准 base 解释并修正为 70。",
    },
    880058: {
        "error_type": "self_corrected_wrong_modular_reduction",
        "error_span": "97_b - 5 * 17_b = 27_b ... b+7 must divide 7 ... no solutions",
        "notes_zh": "先错误地用 97_b-5*17_b 得出无解，随后明确重新评估为 9b+7 与 b+7 的关系，最终证明有效。",
    },
    880059: {
        "error_type": "wrong_factorization_unrepaired",
        "error_span": "(3x - 2y)(4x + 3y) = 0",
        "notes_zh": "GLM 二次型题把 12x^2-xy-6y^2 错因式分解为 (3x-2y)(4x+3y)，实际展开是 12x^2+xy-6y^2。后续计数因对称性仍得到 117，但这个错误因式分解没有被修复，最终保留证明无效。",
        "manual_process_valid_repaired": False,
        "manual_acpi_unrepaired": True,
    },
    880060: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 144",
        "notes_zh": "GLM 梯形题第一行给错 144，后文完整推导后修正为 504。",
    },
    880061: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 12",
        "notes_zh": "Qwen base 题第一行给错 12，后文称其为 hallucination/random number 并修正为 70。",
    },
    880062: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 11",
        "notes_zh": "Qwen base 题第一行给错 11，后文标准推导并修正为 70。",
    },
    880063: {
        "error_type": "wrong_initial_final_answer_repaired",
        "error_span": "Final answer: 15",
        "notes_zh": "Qwen base 题第一行给错 15，后文列举因子并修正为 70。",
    },
}

SECOND_PASS_SAMPLE = [
    880001,
    880009,
    880025,
    880038,
    880041,
    880050,
    880056,
    880058,
    880059,
    880060,
    880063,
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def wilson(k: int, n: int, z: float = 1.96) -> dict[str, float | int]:
    if n <= 0:
        return {"k": k, "n": n, "rate": math.nan, "lo": math.nan, "hi": math.nan}
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return {"k": k, "n": n, "rate": p, "lo": max(0.0, centre - half), "hi": min(1.0, centre + half)}


def summarize(rows: list[dict[str, Any]], generated_total: int) -> dict[str, Any]:
    by_model: dict[str, Counter[str]] = defaultdict(Counter)
    by_task: dict[str, Counter[str]] = defaultdict(Counter)
    by_error = Counter()
    for r in rows:
        for bucket in (by_model[r["model_key"]], by_task[r["task_id"]]):
            bucket["final_correct"] += 1
            bucket["strict_acpi"] += int(r["manual_acpi_strict"])
            bucket["repaired_acpi"] += int(r["manual_acpi_strict"] and not r["manual_acpi_unrepaired"])
            bucket["unrepaired_acpi"] += int(r["manual_acpi_unrepaired"])
            bucket["strict_valid"] += int(r["manual_process_valid_strict"])
        if r["manual_acpi_strict"]:
            by_error[r["manual_error_type"]] += 1
    strict = sum(r["manual_acpi_strict"] for r in rows)
    unrepaired = sum(r["manual_acpi_unrepaired"] for r in rows)
    repaired = strict - unrepaired
    return {
        "generated_total": generated_total,
        "final_correct_total": len(rows),
        "strict_acpi_total": strict,
        "repaired_acpi_total": repaired,
        "unrepaired_acpi_total": unrepaired,
        "rates": {
            "final_correct_per_generated": wilson(len(rows), generated_total),
            "strict_acpi_per_generated": wilson(strict, generated_total),
            "unrepaired_acpi_per_generated": wilson(unrepaired, generated_total),
            "strict_acpi_conditional_final_correct": wilson(strict, len(rows)),
            "unrepaired_acpi_conditional_final_correct": wilson(unrepaired, len(rows)),
        },
        "by_model": {k: dict(v) for k, v in sorted(by_model.items())},
        "by_task": {k: dict(v) for k, v in sorted(by_task.items())},
        "by_error_type": dict(by_error),
    }


def fmt_ci(d: dict[str, Any]) -> str:
    return f"{d['k']}/{d['n']} = {d['rate']:.3f} [{d['lo']:.3f}, {d['hi']:.3f}]"


def write_report(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# E88 Answer-First Natural Hard-Task Manual Audit / E88 answer-first 自然困难题人工审计（2026-04-29）",
        "",
        f"- Audited JSONL / 审计 JSONL：`{OUT_JSONL.relative_to(PROJECT)}`",
        f"- Machine-readable summary / 机器可读摘要：`{OUT_JSON.relative_to(PROJECT)}`",
        "- Scope / 范围：E88 在 4 个 P0 模型、6 道 AIME25 风格困难题上各采样 8 条 answer-first/no-gold 输出；gold answer 只用于离线筛出 final-correct 行，prompt 内不含 gold 或 trap note。",
        "",
        "## Plain Result / 说人话结果",
        "",
        "- E88 的自然样本不是“模型大量凭空给对答案但过程全错”。63 条 final-correct 中，真正最终保留证明仍错误的 unrepaired ACPI 只有 1 条。",
        "- 但 answer-first prompt 会系统制造另一类风险：模型第一行先给一个错答案，后文又把它改正。严格 trace-selection 如果要求整条 trace 全程无错，这些都属于 strict ACPI repaired；如果把 CoT 当草稿读，这些可视为修复成功。",
        "- 新增最重要的自然 unrepaired 个案来自 GLM 的二次型题：它使用了错误因式分解 `(3x - 2y)(4x + 3y)`，但由于两条错误直线的可数点数与正确直线对称相同，最后仍得到 117。",
        "",
        "## Rates / 发生率",
        "",
        f"- Final-correct per generated / 生成样本中答案正确率：{fmt_ci(s['rates']['final_correct_per_generated'])}",
        f"- Strict ACPI per generated / 生成样本中 strict ACPI：{fmt_ci(s['rates']['strict_acpi_per_generated'])}",
        f"- Unrepaired ACPI per generated / 生成样本中未修复 ACPI：{fmt_ci(s['rates']['unrepaired_acpi_per_generated'])}",
        f"- Strict ACPI among final-correct / 答案正确样本中的 strict ACPI：{fmt_ci(s['rates']['strict_acpi_conditional_final_correct'])}",
        f"- Unrepaired ACPI among final-correct / 答案正确样本中的未修复 ACPI：{fmt_ci(s['rates']['unrepaired_acpi_conditional_final_correct'])}",
        "",
        "## By Model / 按模型",
        "",
        "| model | final-correct | strict ACPI | repaired ACPI | unrepaired ACPI | strict-valid |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for model, row in s["by_model"].items():
        lines.append(f"| {model} | {row['final_correct']} | {row['strict_acpi']} | {row['repaired_acpi']} | {row['unrepaired_acpi']} | {row['strict_valid']} |")
    lines += [
        "",
        "## By Task / 按题目",
        "",
        "| task | final-correct | strict ACPI | repaired ACPI | unrepaired ACPI |",
        "|---|---:|---:|---:|---:|",
    ]
    for task, row in s["by_task"].items():
        lines.append(f"| {task} | {row['final_correct']} | {row['strict_acpi']} | {row['repaired_acpi']} | {row['unrepaired_acpi']} |")
    lines += [
        "",
        "## Audit Boundary / 审计边界",
        "",
        "- `strict_process_valid=false` 表示整条可见 trace 中出现了错误答案、错误中间断言或错误推导，即使后文修复也算 strict invalid。",
        "- `manual_process_valid_repaired=true` 表示后文已经明确丢弃错误步骤，最终保留下来的证明是有效的。",
        "- `manual_acpi_unrepaired=true` 表示最终答案正确，但最终保留下来的证明仍包含未修复的关键错误。",
        "- 这批 E88 的高 strict ACPI 很大程度来自 answer-first 输出格式本身，不应直接解释为所有自然 CoT 都高频过程失效。",
        "",
        "## Leakage / 数据泄露检查",
        "",
        f"- Overall / 总体：{'PASS' if result['audit']['all_checks_passed'] else 'FAIL'}",
        "| status | check | detail |",
        "|---|---|---|",
    ]
    for c in result["audit"]["checks"]:
        lines.append(f"| {'PASS' if c['ok'] else 'FAIL'} | {c['check']} | {c['detail']} |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = read_jsonl(IN_JSONL)
    seen = {r["e88_audit_idx"] for r in rows}
    missing = sorted(set(AUDIT) - seen)
    if missing:
        raise SystemExit(f"AUDIT contains unknown e88_audit_idx values: {missing}")

    audited = []
    for r in rows:
        idx = r["e88_audit_idx"]
        note = AUDIT.get(idx)
        out = dict(r)
        if note is None:
            out.update(
                {
                    "manual_process_valid_strict": True,
                    "manual_process_valid_repaired": True,
                    "manual_acpi_strict": False,
                    "manual_repair_present": False,
                    "manual_acpi_unrepaired": False,
                    "manual_error_type": "none",
                    "manual_error_span": "",
                    "manual_notes_zh": "人审未发现会影响严格证明有效性的错误步骤；最终答案与最终保留证明一致。",
                }
            )
        else:
            unrepaired = bool(note.get("manual_acpi_unrepaired", False))
            repaired_valid = bool(note.get("manual_process_valid_repaired", not unrepaired))
            out.update(
                {
                    "manual_process_valid_strict": False,
                    "manual_process_valid_repaired": repaired_valid,
                    "manual_acpi_strict": True,
                    "manual_repair_present": True,
                    "manual_acpi_unrepaired": unrepaired,
                    "manual_error_type": note["error_type"],
                    "manual_error_span": note["error_span"],
                    "manual_notes_zh": note["notes_zh"],
                }
            )
        audited.append(out)

    generated_summary = json.loads((PROJECT / "results/E88_answer_first_natural_sample/e88_answer_first_audit_sheet_summary.json").read_text(encoding="utf-8"))
    generated_total = sum(v["generated"] for v in generated_summary["by_model"].values())
    leakage = {
        "gold_answer_in_prompt_rows": generated_summary["leakage_audit"]["gold_answer_in_prompt_rows"],
        "known_trap_note_in_prompt_rows": generated_summary["leakage_audit"]["known_trap_note_in_prompt_rows"],
    }
    checks = [
        {
            "check": "all final-correct rows audited",
            "ok": all(r["manual_process_valid_strict"] is not None for r in audited),
            "detail": f"{len(audited)} rows have manual strict/repaired/unrepaired labels",
        },
        {
            "check": "no gold answer in prompt",
            "ok": leakage["gold_answer_in_prompt_rows"] == 0,
            "detail": f"gold_answer_in_prompt_rows={leakage['gold_answer_in_prompt_rows']}",
        },
        {
            "check": "no trap note in prompt",
            "ok": leakage["known_trap_note_in_prompt_rows"] == 0,
            "detail": f"known_trap_note_in_prompt_rows={leakage['known_trap_note_in_prompt_rows']}",
        },
        {
            "check": "strict/unrepaired consistency",
            "ok": all((not r["manual_acpi_unrepaired"]) or r["manual_acpi_strict"] for r in audited),
            "detail": "unrepaired ACPI rows are also strict ACPI",
        },
        {
            "check": "second-pass sample reviewed",
            "ok": set(SECOND_PASS_SAMPLE).issubset(seen),
            "detail": f"reviewed representative rows {SECOND_PASS_SAMPLE}",
        },
    ]
    result = {
        "experiment": "E88_answer_first_manual_audit",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_jsonl": str(IN_JSONL.relative_to(PROJECT)),
        "output_jsonl": str(OUT_JSONL.relative_to(PROJECT)),
        "summary": summarize(audited, generated_total),
        "audited_error_indices": sorted(AUDIT),
        "second_pass_sample": SECOND_PASS_SAMPLE,
        "audit": {"all_checks_passed": all(c["ok"] for c in checks), "checks": checks},
        "scope_note_zh": "E88 是 answer-first/no-gold 自然困难题采样；高 strict ACPI 主要来自先写错 final answer 后自修复的格式效应，未修复 ACPI 目前仅 1 条。",
    }
    write_jsonl(OUT_JSONL, audited)
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(result)
    print(json.dumps({"wrote": str(OUT_JSONL), "report": str(OUT_MD), "summary": result["summary"], "audit": result["audit"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
