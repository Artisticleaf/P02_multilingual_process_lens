#!/usr/bin/env python3
"""Analyze and manually audit E52 hard-task strict-format forcing."""
from __future__ import annotations

import json
import re
import socket
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
IN_PATH = PROJECT / "results/E52_hard_task_strict_format_forcing/qwen25_math_7b_instruct_e52_hard_task_strict_format_forcing.json"
OUT_PATH = PROJECT / "results/E52_hard_task_strict_format_forcing/e52_manual_audit_20260428.json"
REPORT = PROJECT / "reports/E52_HARD_TASK_STRICT_FORMAT_FORCING_20260428.md"


# Manual audit of benchmark-style boxed-correct rows from the official E52 run.
# These labels are intentionally conservative: strict trace-selection evidence
# still requires a `Final answer:` line, so boxed-only candidates are diagnostic.
MANUAL_AUDIT: dict[int, dict[str, Any]] = {
    1: {
        "label": "valid_boxed_only",
        "process_valid": True,
        "reason_zh": "正确将 17_b、97_b 转成 b+7、9b+7，并枚举 9-k | 56 得到 b=49,21；但违反 final-line 格式。",
        "reason_en": "Correct base conversion and divisor enumeration; violates final-line format.",
    },
    5: {
        "label": "valid_boxed_only",
        "process_valid": True,
        "reason_zh": "与 row 1 同构：数学过程可接受，输出格式不合格。",
        "reason_en": "Same valid mathematical structure as row 1; format noncompliant.",
    },
    9: {
        "label": "valid_boxed_only",
        "process_valid": True,
        "reason_zh": "与 row 1 同构：过程有效，最后仍用 boxed。",
        "reason_en": "Same valid mathematical structure as row 1; uses boxed final answer.",
    },
    11: {
        "label": "valid_boxed_only",
        "process_valid": True,
        "reason_zh": "过程有效：枚举 56 的正负因子并筛掉 b<=9；格式不合格。",
        "reason_en": "Valid divisor enumeration and filtering; format noncompliant.",
    },
    13: {
        "label": "valid_boxed_only",
        "process_valid": True,
        "reason_zh": "过程有效：关键约束与答案一致；格式不合格。",
        "reason_en": "Valid key constraint and answer; format noncompliant.",
    },
    15: {
        "label": "valid_boxed_only",
        "process_valid": True,
        "reason_zh": "过程有效：得到 b=49,21；格式不合格。",
        "reason_en": "Valid derivation of b=49 and b=21; format noncompliant.",
    },
    67: {
        "label": "clear_process_invalid_boxed_correct",
        "process_valid": False,
        "reason_zh": "清楚的过程错误：先指出末位必须为偶数，但最终计数用 4!*4! 排列偶数位，没有约束最后一位为偶数；答案因未解释的抵消而碰巧正确。",
        "reason_en": "Clear process error: notes last digit must be even, then counts even-position arrangements as 4!*4! without enforcing the last digit parity; answer is accidentally correct.",
    },
    75: {
        "label": "clear_process_invalid_boxed_correct",
        "process_valid": False,
        "reason_zh": "与 row 67 同构：最终计数没有落实 divisibility-by-2 条件；boxed 答案正确但过程无效。",
        "reason_en": "Same as row 67: the divisibility-by-2 constraint is not implemented in the final count.",
    },
    80: {
        "label": "ambiguous_notational_collision_boxed_correct",
        "process_valid": None,
        "reason_zh": "主体几何推导正确，但把题中底边变量 r 与圆半径口头混用；保守记为“符号混杂/需二审”，不作为明确 invalid 计数。",
        "reason_en": "Main geometry derivation is correct, but base variable r and circle radius are verbally conflated; conservatively counted as ambiguous.",
    },
    81: {
        "label": "ambiguous_notational_collision_boxed_correct",
        "process_valid": None,
        "reason_zh": "主体推导正确，但开头把 radius 写成 r=3，同时 r 又是底边变量；保守记为 ambiguous。",
        "reason_en": "Main derivation is correct, but the opening conflates radius r=3 with the base variable r; conservatively ambiguous.",
    },
    88: {
        "label": "ambiguous_notational_collision_boxed_correct",
        "process_valid": None,
        "reason_zh": "主体推导正确，但存在半径/底边 r 的表层符号混用；不纳入明确 invalid。",
        "reason_en": "Main derivation is correct, but radius/base r notation is conflated; not counted as clear invalid.",
    },
    91: {
        "label": "ambiguous_notational_collision_boxed_correct",
        "process_valid": None,
        "reason_zh": "推导能到正确结论，但 A=r*s_p 中 r 是半径，随后 r 又指底边，符号链混杂；需二审。",
        "reason_en": "Derivation reaches the right result, but r denotes radius in A=r*s_p and later a base; needs second review.",
    },
    92: {
        "label": "ambiguous_notational_collision_boxed_correct",
        "process_valid": None,
        "reason_zh": "主体推导正确，仍有半径 r 与底边 r 的符号混杂；不作为明确 invalid。",
        "reason_en": "Main derivation is correct, with radius/base r notation collision; not counted as clear invalid.",
    },
    93: {
        "label": "ambiguous_notational_collision_boxed_correct",
        "process_valid": None,
        "reason_zh": "有符号混杂与一处不严谨的切线表述，但核心方程链可恢复；保守记为 ambiguous。",
        "reason_en": "Notation collision and one imprecise tangent statement, but the core equation chain is recoverable; conservatively ambiguous.",
    },
}


def normalize_int(text: str) -> str:
    text = text.strip().lower().replace("$", "").replace("\\", "")
    text = re.sub(r"\s+", "", text).rstrip(".。,:;，；")
    m = re.search(r"-?\d+", text)
    return m.group(0) if m else text


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counters = defaultdict(Counter)
    for row in rows:
        keys = [
            ("overall", "all"),
            ("variant", row["prompt_variant"]),
            ("task", row["task_id"]),
            ("audit_label", row["manual_audit_label"]),
        ]
        for group, key in keys:
            c = counters[(group, key)]
            c["n"] += 1
            c["strict_correct"] += int(row["strict_correct"])
            c["boxed_correct"] += int(row["boxed_correct"])
            c["strict_or_boxed_correct"] += int(row["strict_or_boxed_correct"])
            c["clear_process_invalid_boxed_correct"] += int(row["manual_audit_label"] == "clear_process_invalid_boxed_correct")
            c["ambiguous_notational_collision_boxed_correct"] += int(row["manual_audit_label"] == "ambiguous_notational_collision_boxed_correct")
            c["valid_boxed_only"] += int(row["manual_audit_label"] == "valid_boxed_only")
            c["format_noncompliant"] += int(row["boxed_correct"] and not row["strict_correct"])
    out: dict[str, dict[str, dict[str, int]]] = defaultdict(dict)
    for (group, key), counter in sorted(counters.items()):
        out[group][key] = dict(counter)
    return dict(out)


def check_no_gold_leak(rows: list[dict[str, Any]]) -> list[str]:
    issues = []
    for idx, row in enumerate(rows):
        prompt = row.get("prompt_content_no_gold", "")
        if row.get("gold_answer_in_prompt"):
            issues.append(f"row {idx}: gold_answer_in_prompt flag is true")
        if row.get("known_trap_note_in_prompt"):
            issues.append(f"row {idx}: known_trap_note_in_prompt flag is true")
        if re.search(r"given\s+final\s+answer\s*[:：]", prompt, flags=re.IGNORECASE):
            issues.append(f"row {idx}: prompt contains Given final answer")
        if row.get("trap_note_not_in_prompt", "") and row["trap_note_not_in_prompt"] in prompt:
            issues.append(f"row {idx}: trap note text appears in prompt")
    return issues


def main() -> None:
    data = json.loads(IN_PATH.read_text(encoding="utf-8"))
    rows = []
    for idx, row in enumerate(data["rows"]):
        row = dict(row)
        audit = MANUAL_AUDIT.get(idx)
        if row["boxed_correct"]:
            if audit is None:
                raise SystemExit(f"Missing manual audit for boxed-correct row {idx}")
            if normalize_int(row["gold_answer"]) not in [normalize_int(x) for x in row.get("boxed_candidates", [])]:
                raise SystemExit(f"Manual audit row {idx} is not boxed-correct after normalization")
            row["manual_audit_label"] = audit["label"]
            row["manual_process_valid_for_boxed_trace"] = audit["process_valid"]
            row["manual_audit_reason_zh"] = audit["reason_zh"]
            row["manual_audit_reason_en"] = audit["reason_en"]
        else:
            row["manual_audit_label"] = "not_boxed_correct_or_not_candidate"
            row["manual_process_valid_for_boxed_trace"] = None
            row["manual_audit_reason_zh"] = "不是 boxed-correct 候选；不做人审过程标签。"
            row["manual_audit_reason_en"] = "Not a boxed-correct candidate; no manual process label assigned."
        rows.append(row)

    leak_issues = check_no_gold_leak(rows)
    boxed_correct_indices = [i for i, row in enumerate(data["rows"]) if row["boxed_correct"]]
    audited_indices = sorted(MANUAL_AUDIT)
    if boxed_correct_indices != audited_indices:
        raise SystemExit(f"Manual audit index mismatch: boxed={boxed_correct_indices}, audited={audited_indices}")

    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "host": socket.gethostname(),
        "source": str(IN_PATH.relative_to(PROJECT)),
        "rows": rows,
        "summary": summarize(rows),
        "leak_check": {"passed": not leak_issues, "issues": leak_issues},
        "manual_audit_scope_en": "Manual labels are applied only to boxed-correct diagnostic candidates. Strict trace-selection correctness remains zero.",
        "manual_audit_scope_zh": "人工标签只用于 boxed-correct 诊断候选；strict trace-selection 正确数仍为 0。",
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    overall = result["summary"]["overall"]["all"]
    variant_lines = []
    for variant, c in result["summary"].get("variant", {}).items():
        variant_lines.append(
            f"| `{variant}` | {c['n']} | {c['strict_correct']} | {c['boxed_correct']} | "
            f"{c['clear_process_invalid_boxed_correct']} | {c['ambiguous_notational_collision_boxed_correct']} | {c['valid_boxed_only']} |"
        )
    task_lines = []
    for task_id, c in result["summary"].get("task", {}).items():
        task_lines.append(
            f"| `{task_id}` | {c['n']} | {c['strict_correct']} | {c['boxed_correct']} | "
            f"{c['clear_process_invalid_boxed_correct']} | {c['ambiguous_notational_collision_boxed_correct']} | {c['valid_boxed_only']} |"
        )

    report = "\n".join(
        [
            "# E52 Hard-Task Strict-Format Forcing / 困难题严格格式强制（2026-04-28）",
            "",
            "## Plain-language conclusion / 说人话结论",
            "",
            "- Stronger instructions did **not** solve the hard-task trace-selection bottleneck: strict `Final answer:` correct remains 0/96. / 更强格式指令没有解决困难题 trace-selection 瓶颈：strict `Final answer:` 正确仍是 0/96。",
            "- The same run produced 14/96 benchmark-style boxed-correct outputs, so some failures are not inability to solve the math problem; they are an objective/format mismatch. / 同一次运行有 14/96 个 benchmark-style boxed 正确输出，说明部分失败不是不会解题，而是目标/格式错配。",
            "- Manual audit found 2 clear answer-correct/process-invalid boxed-only traces on the divisibility-by-22 task, but these are not official strict trace-selection positives because the final-line contract is missing. / 人工审计发现 2 个明确的 boxed-only 答案正确但过程无效样本，出现在 22 整除题；但它们缺少 final-line，因此不能算官方 strict trace-selection 阳性。",
            "- Six trapezoid boxed-correct rows contain a radius/base-`r` notation collision; we mark them ambiguous rather than counting them as clear process-invalid evidence. / 6 个梯形 boxed-correct 行存在半径与底边 `r` 的符号混杂；保守记为 ambiguous，不纳入明确 process-invalid 计数。",
            "",
            "## Counts / 数量",
            "",
            f"- Rows / 行数: {overall['n']}",
            f"- Strict correct / strict 正确: {overall['strict_correct']}",
            f"- Boxed correct diagnostic / boxed 诊断正确: {overall['boxed_correct']}",
            f"- Clear process-invalid among boxed-correct / boxed-correct 中明确过程无效: {overall['clear_process_invalid_boxed_correct']}",
            f"- Ambiguous notation-collision boxed-correct / boxed-correct 中符号混杂 ambiguous: {overall['ambiguous_notational_collision_boxed_correct']}",
            f"- Valid boxed-only / 过程有效但格式不合格: {overall['valid_boxed_only']}",
            f"- Leak check / 泄漏检查: {'passed' if result['leak_check']['passed'] else 'failed'}",
            "",
            "## By prompt variant / 按 prompt 变体",
            "",
            "| Variant / 变体 | n | Strict correct | Boxed correct | Clear invalid boxed | Ambiguous boxed | Valid boxed-only |",
            "|---|---:|---:|---:|---:|---:|---:|",
            *variant_lines,
            "",
            "## By task / 按题目",
            "",
            "| Task / 题目 | n | Strict correct | Boxed correct | Clear invalid boxed | Ambiguous boxed | Valid boxed-only |",
            "|---|---:|---:|---:|---:|---:|---:|",
            *task_lines,
            "",
            "## Scientific interpretation / 科学解释",
            "",
            "- For hard tasks, final-correct acquisition and final-line compliance are separate variables. / 对困难题，拿到正确答案与遵守 final-line 是两个变量。",
            "- E52 strengthens the claim that verifier/selector objectives matter: a model can produce a correct answer under benchmark conventions while still being unusable for strict trace selection. / E52 强化了“verifier/selector objective 很关键”的说法：模型能按 benchmark 习惯给出正确答案，但仍不满足 strict trace selection。",
            "- E52 does **not** prove hard-task natural ACPI under the official strict parser; it exposes where the bottleneck is. / E52 没有证明官方 strict parser 下的困难题自然 ACPI；它定位了瓶颈。",
            "- The clear divisibility-by-22 rows are useful seed cases for the next causal experiment: build paired valid/invalid traces with the same final answer and patch residual/error spans. / 22 整除题的明确 invalid 行适合做下一步因果实验种子：构造同答案的 valid/invalid pair，再做 residual/error-span patch。",
            "",
            "## Files / 文件",
            "",
            f"- Raw E52 result / 原始 E52 结果: `{IN_PATH.relative_to(PROJECT)}`",
            f"- Manual audit JSON / 人工审计 JSON: `{OUT_PATH.relative_to(PROJECT)}`",
            "",
        ]
    )
    REPORT.write_text(report, encoding="utf-8")
    print(json.dumps({"out": str(OUT_PATH), "report": str(REPORT), "summary": overall, "leak_check": result["leak_check"]}, ensure_ascii=False, indent=2))
    if leak_issues:
        sys.exit(1)


if __name__ == "__main__":
    main()
