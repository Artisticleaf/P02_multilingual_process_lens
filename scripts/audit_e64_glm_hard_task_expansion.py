#!/usr/bin/env python3
"""Manual audit summary for E64 GLM hard-task expansion."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
IN_PATH = PROJECT / "results/E64_natural_hard_task_expansion/glm47_flash_candidate_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json"
OUT_DIR = PROJECT / "results/E64_natural_hard_task_expansion"
OUT_JSONL = OUT_DIR / "glm47_flash_candidate_e64_final_correct_manual_audit.jsonl"
REPORT = PROJECT / "reports/E64_GLM_HARD_TASK_EXPANSION_20260429.md"
AUDIT = PROJECT / "reports/E64_GLM_HARD_TASK_EXPANSION_AUDIT_20260429.json"

# Manually reviewed final-correct source row indices from the E64 output.
# All eight contain valid visible derivations under the strict criterion.
MANUAL_VALID = {
    2: "base-divisor derivation valid; converts base-b digits and divisor condition correctly",
    3: "base-divisor derivation valid; repeated wording but no wrong mathematical step",
    6: "base-divisor answer-first row valid after final answer; no gold answer in prompt",
    7: "base-divisor answer-first row valid after final answer; divisor logic correct",
    10: "base-divisor self-check row valid; self-check does not introduce a false step",
    11: "base-divisor self-check row valid; digit/base trap checked correctly",
    28: "ice-cream ordered assignment row valid; counts triples and multinomial assignments correctly",
    33: "ice-cream ordered assignment self-check row valid; distinct-player assignment trap handled correctly",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")


def pct(num: int, den: int) -> str:
    return f"{num / den:.3f}" if den else "NA"


def main() -> None:
    checks = [{"check": "E64 GLM generation output exists", "ok": IN_PATH.exists(), "detail": str(IN_PATH.relative_to(PROJECT))}]
    data = read_json(IN_PATH)
    rows = data["rows"]
    final_indices = [i for i, r in enumerate(rows) if r.get("manual_final_correct")]
    checks.append({"check": "manual reviewed index set matches final-correct rows", "ok": set(final_indices) == set(MANUAL_VALID), "detail": f"final={final_indices}; manual={sorted(MANUAL_VALID)}"})
    checks.append({"check": "no gold answer in prompts", "ok": data["summary"].get("gold_answer_in_prompt_rows", 0) == 0, "detail": str(data["summary"].get("gold_answer_in_prompt_rows", 0))})
    checks.append({"check": "no trap note in prompts", "ok": data["summary"].get("known_trap_note_in_prompt_rows", 0) == 0, "detail": str(data["summary"].get("known_trap_note_in_prompt_rows", 0))})

    audited = []
    for i in final_indices:
        row = rows[i]
        strict_valid = i in MANUAL_VALID
        out = dict(row)
        out.update(
            {
                "e64_source_row_index": i,
                "manual_audit_status": "audited",
                "manual_auditor": "codex_manual_20260429",
                "manual_process_valid_strict": strict_valid,
                "manual_process_valid_repaired": strict_valid,
                "manual_repair_present": False,
                "manual_error_type": "none" if strict_valid else "unreviewed_or_invalid",
                "manual_error_span": "",
                "manual_audit_note_zh": MANUAL_VALID.get(i, "not manually approved"),
                "manual_acpi_strict": bool(row.get("manual_final_correct")) and not strict_valid,
                "manual_acpi_unrepaired": bool(row.get("manual_final_correct")) and not strict_valid,
            }
        )
        audited.append(out)
    write_jsonl(OUT_JSONL, audited)

    overall = Counter()
    by_task: dict[str, Counter] = defaultdict(Counter)
    by_variant: dict[str, Counter] = defaultdict(Counter)
    for row in audited:
        for bucket in [overall, by_task[row["task_id"]], by_variant[row["prompt_variant"]]]:
            bucket["n"] += 1
            bucket["strict_valid"] += int(row["manual_process_valid_strict"])
            bucket["repaired_valid"] += int(row["manual_process_valid_repaired"])
            bucket["strict_acpi"] += int(row["manual_acpi_strict"])
            bucket["unrepaired_acpi"] += int(row["manual_acpi_unrepaired"])

    audit = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
        "manual_final_correct_rows": final_indices,
        "manual_audit_jsonl": str(OUT_JSONL.relative_to(PROJECT)),
        "summary": {
            "generated_n": data["summary"]["n"],
            "final_correct": data["summary"]["final_correct"],
            "strict_acpi": overall["strict_acpi"],
            "unrepaired_acpi": overall["unrepaired_acpi"],
        },
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# E64 GLM Hard-Task Expansion / E64 GLM 困难题扩展采样（2026-04-29）",
        "",
        f"- Generation / 生成：`{IN_PATH.relative_to(PROJECT)}`",
        f"- Manual audit / 人审：`{OUT_JSONL.relative_to(PROJECT)}`",
        f"- Audit / 审计：`{AUDIT.relative_to(PROJECT)}`",
        "- Plain language / 说人话：把 GLM-4.7-Flash 也放进 AIME-style hard-task 自然生成采样里看。结果是它 final-correct 少，且这 8 条 final-correct trace 人审后都是过程有效；没有发现新的自然 ACPI。",
        "",
        "## Generation Summary / 生成汇总",
        "",
        "| generated | final-correct | strict marker missing | gold answer in prompt | trap note in prompt |",
        "|---:|---:|---:|---:|---:|",
        f"| {data['summary']['n']} | {data['summary']['final_correct']} ({pct(data['summary']['final_correct'], data['summary']['n'])}) | {data['summary']['strict_final_marker_missing']} | {data['summary']['gold_answer_in_prompt_rows']} | {data['summary']['known_trap_note_in_prompt_rows']} |",
        "",
        "## Manual Process Audit / 人工过程审计",
        "",
        "| n final-correct audited | strict valid | repaired valid | strict ACPI | unrepaired ACPI |",
        "|---:|---:|---:|---:|---:|",
        f"| {overall['n']} | {overall['strict_valid']} ({pct(overall['strict_valid'], overall['n'])}) | {overall['repaired_valid']} ({pct(overall['repaired_valid'], overall['n'])}) | {overall['strict_acpi']} ({pct(overall['strict_acpi'], overall['n'])}) | {overall['unrepaired_acpi']} ({pct(overall['unrepaired_acpi'], overall['n'])}) |",
        "",
        "### By Task / 按题目",
        "",
        "| task | n | strict valid | strict ACPI |",
        "|---|---:|---:|---:|",
    ]
    for key, c in sorted(by_task.items()):
        lines.append(f"| `{key}` | {c['n']} | {c['strict_valid']} | {c['strict_acpi']} |")
    lines += [
        "",
        "### By Prompt Variant / 按 prompt 变体",
        "",
        "| variant | n | strict valid | strict ACPI |",
        "|---|---:|---:|---:|",
    ]
    for key, c in sorted(by_variant.items()):
        lines.append(f"| `{key}` | {c['n']} | {c['strict_valid']} | {c['strict_acpi']} |")
    lines += [
        "",
        "## Boundary / 边界",
        "",
        "- E64 does not contradict the controlled ACPI claim; it reinforces the prevalence boundary: natural unrepaired ACPI is not easy to harvest from hard tasks, especially for GLM in this small k=4 sample. / E64 不反驳受控 ACPI 主张；它强化自然发生率边界：困难题自然未修复 ACPI 并不容易采到，尤其 GLM 在这个 k=4 小样本中 final-correct 本身较少。",
        "- Because only final-correct rows are manually process-audited, E64 cannot estimate overall reasoning quality beyond the reported final-correct rate. / 由于只对 final-correct 行做人审，E64 不能估计整体推理质量，只能报告 final-correct 率与其过程有效性。",
        "- The generation prompts contain no gold answer and no trap note, so these rows are natural hard-task traces rather than answer-anchored controlled traces. / 生成 prompt 不含 gold answer 或 trap note，因此这些是自然困难题 trace，不是 answer-anchor 受控 trace。",
        "",
        "## Audit / 审计",
        "",
    ]
    for c in checks:
        lines.append(f"- {'PASS' if c['ok'] else 'FAIL'}: {c['check']} — {c['detail']}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"passed": audit["passed"], "report": str(REPORT), "audit": str(AUDIT), "manual": str(OUT_JSONL)}, ensure_ascii=False, indent=2))
    if not audit["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
