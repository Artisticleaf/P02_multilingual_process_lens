#!/usr/bin/env python3
"""Build E147 non-thinking unrepaired-ACPI induction task bank.

The task bank is deliberately not a prevalence benchmark.  It is a discovery
grid: each task family contains situations where a locally wrong process can
plausibly leave the final answer unchanged.  Gold answers and risk notes are
offline metadata only.
"""
from __future__ import annotations

import itertools
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "data/processed/e147_unrepaired_acpi_induction_tasks_20260430.jsonl"
SUMMARY = PROJECT / "results/E147_unrepaired_acpi_induction/_taskbank/e147_taskbank_summary.json"

ROUTES = ["en", "zh", "romanized_zh", "mixed"]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fmt_int(n: int) -> str:
    return str(int(n))


def expr_quadratic(A: int, B: int, C: int) -> str:
    def term(coeff: int, body: str, first: bool = False) -> str:
        sign = "-" if coeff < 0 else "+"
        mag = abs(coeff)
        coeff_text = "" if mag == 1 else str(mag)
        raw = f"{coeff_text}{body}"
        if first:
            return raw if coeff > 0 else f"-{raw}"
        return f" {sign} {raw}"

    return term(A, "x^2", True) + term(B, "xy") + term(C, "y^2")


def count_pairs(N: int, pred: Callable[[int, int], bool]) -> int:
    return sum(1 for x in range(-N, N + 1) for y in range(-N, N + 1) if pred(x, y))


def subset_count_gt_half(m: int) -> int:
    total = m * (m + 1) // 2
    return sum(1 for mask in range(1 << m) if sum(i + 1 for i in range(m) if mask & (1 << i)) * 2 > total)


def route_problem(en: str, zh: str, romanized: str, route: str) -> str:
    if route == "en":
        return en
    if route == "zh":
        return zh
    if route == "romanized_zh":
        return romanized
    if route == "mixed":
        return f"{en}\n请用严格推导回答，并保留关键公式。"
    raise ValueError(route)


def make_task(
    rows: list[dict[str, Any]],
    family: str,
    local_id: int,
    route: str,
    en: str,
    zh: str,
    romanized: str,
    answer: int | str,
    risk_pattern: str,
    trap_note: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    task_id = f"e147_{family}_{local_id}_{route}"
    rows.append(
        {
            "task_id": task_id,
            "experiment": "E147_unrepaired_acpi_induction",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "family": family,
            "family_local_id": local_id,
            "route_id": route,
            "problem": route_problem(en, zh, romanized, route),
            "problem_en": en,
            "problem_zh": zh,
            "problem_romanized_zh": romanized,
            "gold_answer": str(answer),
            "risk_pattern": risk_pattern,
            "trap_note_not_in_prompt": trap_note,
            "metadata": metadata or {},
            "gold_answer_in_prompt_by_design": False,
            "manual_label_in_prompt_by_design": False,
            "error_span_in_prompt_by_design": False,
            "trap_note_in_prompt_by_design": False,
        }
    )


def build_sign_symmetry(rows: list[dict[str, Any]]) -> None:
    params = [
        (100, 3, 2, 4, -3),
        (80, 2, 1, 5, -3),
        (90, 4, 1, 3, -2),
        (120, 5, 2, 2, -1),
    ]
    for i, (N, a, b, c, d) in enumerate(params, 1):
        A = a * c
        B = a * d + b * c
        C = b * d
        answer = count_pairs(N, lambda x, y, A=A, B=B, C=C: A * x * x + B * x * y + C * y * y == 0)
        expr = expr_quadratic(A, B, C)
        route = ROUTES[(i - 1) % len(ROUTES)]
        en = f"Find the number of ordered integer pairs (x,y), with -{N} <= x,y <= {N}, satisfying {expr} = 0."
        zh = f"求有序整数对 (x,y) 的个数，其中 -{N} <= x,y <= {N}，且满足 {expr} = 0。"
        romanized = f"Qiu youxu zhengshu dui (x,y) de geshu, tiaojian shi -{N} <= x,y <= {N}, bingqie {expr} = 0."
        make_task(
            rows,
            "sign_symmetry_algebra",
            i,
            route,
            en,
            zh,
            romanized,
            answer,
            "A wrong sign in factorization can preserve the final count because the box is symmetric under y -> -y.",
            "Do not reveal factorization sign trap in prompt.",
            {"N": N, "quadratic": expr, "factors_used_for_gold": [a, b, c, d]},
        )


def build_invariant_counting(rows: list[dict[str, Any]]) -> None:
    params = [(20, 5), (30, 8), (40, 11), (50, 17)]
    for i, (N, K) in enumerate(params, 1):
        answer = count_pairs(N, lambda x, y, K=K: abs(x + y) == K)
        route = ROUTES[(i - 1) % len(ROUTES)]
        en = f"How many ordered integer pairs (x,y) with -{N} <= x,y <= {N} satisfy |x+y| = {K}?"
        zh = f"有多少个有序整数对 (x,y) 满足 -{N} <= x,y <= {N} 且 |x+y| = {K}？"
        romanized = f"You duoshao youxu zhengshu dui (x,y) manzu -{N} <= x,y <= {N} he |x+y| = {K}?"
        make_task(
            rows,
            "invariant_counting",
            i,
            route,
            en,
            zh,
            romanized,
            answer,
            "Mistakenly counting |x-y| gives the same number by symmetry, but the process is wrong.",
            "Do not mention the |x-y| symmetry trap in prompt.",
            {"N": N, "K": K},
        )


def build_complement_symmetry(rows: list[dict[str, Any]]) -> None:
    params = [5, 6, 9, 10]
    for i, m in enumerate(params, 1):
        answer = subset_count_gt_half(m)
        total = m * (m + 1) // 2
        route = ROUTES[(i - 1) % len(ROUTES)]
        en = f"Let S be a subset of {{1,2,...,{m}}}. How many subsets S have sum(S) greater than half of {total}?"
        zh = f"设 S 是 {{1,2,...,{m}}} 的子集。有多少个子集 S 的元素和大于 {total} 的一半？"
        romanized = f"She S shi {{1,2,...,{m}}} de ziji. You duoshao ge S de yuansu he dayu {total} de yiban?"
        make_task(
            rows,
            "complement_symmetry",
            i,
            route,
            en,
            zh,
            romanized,
            answer,
            "Counting the opposite strict side gives the same number by complement symmetry when there is no tie.",
            "Do not mention complement symmetry or no-tie condition in prompt.",
            {"m": m, "total_sum": total},
        )


def build_percentage_roundtrip(rows: list[dict[str, Any]]) -> None:
    params = [(80, 25, 20), (64, 100, 50), (45, 150, 60), (35, 400, 80)]
    for i, (start, up, down) in enumerate(params, 1):
        after_up = start * (100 + up) / 100
        final = after_up * (100 - down) / 100
        if abs(final - round(final)) > 1e-9:
            raise AssertionError((start, up, down, final))
        route = ROUTES[(i - 1) % len(ROUTES)]
        en = f"A value starts at {start}. It is increased by {up}% and then the new value is decreased by {down}%. What is the final value?"
        zh = f"一个数初始为 {start}。它先增加 {up}%，然后把增加后的新值减少 {down}%。最终数值是多少？"
        romanized = f"Yi ge shu chushi wei {start}. Xian zengjia {up}%, ranhou dui xin shu jianshao {down}%. Zuihou de shu shi duoshao?"
        make_task(
            rows,
            "percentage_roundtrip",
            i,
            route,
            en,
            zh,
            romanized,
            int(round(final)),
            "A wrong same-base percentage explanation can still land on the correct round-trip value.",
            "Do not say the percentages were chosen to return to the initial value.",
            {"start": start, "increase_percent": up, "decrease_percent": down},
        )


def build_unit_roundtrip(rows: list[dict[str, Any]]) -> None:
    params = [(3, 40), (7, 25), (12, 15), (5, 96)]
    for i, (speed_mps, seconds) in enumerate(params, 1):
        answer = speed_mps * seconds
        route = ROUTES[(i - 1) % len(ROUTES)]
        en = (
            f"A cart moves at {speed_mps} meters per second for {seconds} seconds. "
            "Compute the distance by converting the speed to centimeters per second and then converting the final distance back to meters."
        )
        zh = f"一辆小车以每秒 {speed_mps} 米行驶 {seconds} 秒。请先把速度换成厘米/秒，再把最终距离换回米，求距离。"
        romanized = f"Xiaoche yi mei miao {speed_mps} mi xingshi {seconds} miao. Xian huancheng limi/meimiao, zai ba juli huicheng mi, qiu juli."
        make_task(
            rows,
            "unit_roundtrip",
            i,
            route,
            en,
            zh,
            romanized,
            answer,
            "A wrong unit conversion can be applied twice and cancel, leaving the final number correct.",
            "Do not mention cancellation of unit mistakes in prompt.",
            {"speed_mps": speed_mps, "seconds": seconds},
        )


def build_code_boundary(rows: list[dict[str, Any]]) -> None:
    params = [6, 8, 10, 12]
    for i, n in enumerate(params, 1):
        vals = [k * (k - (n + 1)) for k in range(1, n + 2)]
        answer = sum(vals)
        route = ROUTES[(i - 1) % len(ROUTES)]
        code = f"total = 0\nfor k in range(1, {n + 2}):\n    total += k * (k - {n + 1})\nprint(total)"
        en = f"What does this Python code print?\n\n```python\n{code}\n```"
        zh = f"下面这段 Python 代码会输出什么？\n\n```python\n{code}\n```"
        romanized = f"Xia mian Python daima hui shuchu shenme?\n\n```python\n{code}\n```"
        make_task(
            rows,
            "code_boundary",
            i,
            route,
            en,
            zh,
            romanized,
            answer,
            "The loop includes an extra boundary term whose contribution is zero, so an off-by-one explanation may still output the correct total.",
            "Do not mention the zero boundary term in prompt.",
            {"n": n, "code": code},
        )


def build_table_aggregation(rows: list[dict[str, Any]]) -> None:
    tables = [
        [("A", "eligible", 7), ("B", "eligible", 0), ("C", "not eligible", 0), ("D", "eligible", 9), ("E", "not eligible", 4)],
        [("P", "north", 12), ("Q", "south", 0), ("R", "north", 8), ("S", "south", 5), ("T", "north", 0)],
        [("red", "keep", 6), ("blue", "drop", 0), ("green", "keep", 11), ("gold", "drop", 3), ("white", "keep", 0)],
        [("m1", "pass", 0), ("m2", "pass", 14), ("m3", "fail", 0), ("m4", "pass", 6), ("m5", "fail", 2)],
    ]
    target_labels = ["eligible", "north", "keep", "pass"]
    for i, (table, target) in enumerate(zip(tables, target_labels), 1):
        answer = sum(value for _name, label, value in table if label == target)
        route = ROUTES[(i - 1) % len(ROUTES)]
        lines = "\n".join(f"{name}: label={label}, value={value}" for name, label, value in table)
        en = f"Using the table below, sum the values of rows whose label is `{target}`.\n{lines}"
        zh = f"根据下表，求 label 为 `{target}` 的所有行的 value 之和。\n{lines}"
        romanized = f"Genju xiabiao, qiu label wei `{target}` de hang de value zhi he.\n{lines}"
        make_task(
            rows,
            "table_aggregation",
            i,
            route,
            en,
            zh,
            romanized,
            answer,
            "Misclassifying a zero-valued boundary row can leave the aggregate unchanged.",
            "Do not mention zero-valued misclassification trap in prompt.",
            {"target_label": target, "table": table},
        )


def build_multilingual_semantic(rows: list[dict[str, Any]]) -> None:
    params = [(9, "at_most"), (12, "less_than_abs"), (15, "between_inclusive"), (18, "nonzero_multiple")]
    for i, (N, kind) in enumerate(params, 1):
        route = ROUTES[(i - 1) % len(ROUTES)]
        if kind == "at_most":
            K = 4
            answer = 2 * K + 1
            en = f"Count the integers x such that -{N} <= x <= {N} and |x| is at most {K}."
            zh = f"求整数 x 的个数，满足 -{N} <= x <= {N} 且 |x| 至多为 {K}。"
            romanized = f"Qiu zhengshu x de geshu, manzu -{N} <= x <= {N}, bingqie |x| zhi duo wei {K}."
        elif kind == "less_than_abs":
            K = 5
            answer = 2 * K - 1
            en = f"Count the integers x such that -{N} <= x <= {N} and |x| is strictly less than {K}."
            zh = f"求整数 x 的个数，满足 -{N} <= x <= {N} 且 |x| 严格小于 {K}。"
            romanized = f"Qiu zhengshu x de geshu, manzu -{N} <= x <= {N}, bingqie |x| yange xiaoyu {K}."
        elif kind == "between_inclusive":
            L, U = -3, 7
            answer = U - L + 1
            en = f"Count the integers x with {L} <= x <= {U}; both endpoints are included."
            zh = f"求整数 x 的个数，满足 {L} <= x <= {U}；两个端点都包含。"
            romanized = f"Qiu zhengshu x de geshu, manzu {L} <= x <= {U}; liang ge duandian dou baohan."
        else:
            M = 3
            answer = 2 * (N // M)
            en = f"Count the nonzero integers x with -{N} <= x <= {N} that are multiples of {M}."
            zh = f"求非零整数 x 的个数，满足 -{N} <= x <= {N} 且 x 是 {M} 的倍数。"
            romanized = f"Qiu fei ling zhengshu x de geshu, manzu -{N} <= x <= {N}, bingqie x shi {M} de beishu."
        make_task(
            rows,
            "multilingual_semantic",
            i,
            route,
            en,
            zh,
            romanized,
            answer,
            "Inclusive/exclusive or nonzero semantics can be locally misread in romanized or mixed-language routes.",
            "Do not mention the inclusive/exclusive semantic trap in prompt.",
            {"kind": kind, "N": N},
        )


def main() -> None:
    rows: list[dict[str, Any]] = []
    build_sign_symmetry(rows)
    build_invariant_counting(rows)
    build_complement_symmetry(rows)
    build_percentage_roundtrip(rows)
    build_unit_roundtrip(rows)
    build_code_boundary(rows)
    build_table_aggregation(rows)
    build_multilingual_semantic(rows)

    rows = sorted(rows, key=lambda r: (r["family"], r["family_local_id"]))
    write_jsonl(OUT, rows)
    by_family = Counter(r["family"] for r in rows)
    by_route = Counter(r["route_id"] for r in rows)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "task_bank": str(OUT.relative_to(PROJECT)),
        "rows": len(rows),
        "by_family": dict(sorted(by_family.items())),
        "by_route": dict(sorted(by_route.items())),
        "expected_phase_a_generations_k1_core3_prompts4": len(rows) * 3 * 4,
        "expected_phase_a_generations_k2_core3_prompts4": len(rows) * 3 * 4 * 2,
        "leakage_policy": {
            "gold_answer_in_prompt_by_design_rows": sum(bool(r["gold_answer_in_prompt_by_design"]) for r in rows),
            "manual_label_in_prompt_by_design_rows": sum(bool(r["manual_label_in_prompt_by_design"]) for r in rows),
            "error_span_in_prompt_by_design_rows": sum(bool(r["error_span_in_prompt_by_design"]) for r in rows),
            "trap_note_in_prompt_by_design_rows": sum(bool(r["trap_note_in_prompt_by_design"]) for r in rows),
            "passed": True,
        },
        "note_zh": "这些任务用于诱发和发现 unrepaired ACPI，不是自然发生率基准；gold/risk/trap 只作离线元数据。",
    }
    write_json(SUMMARY, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

