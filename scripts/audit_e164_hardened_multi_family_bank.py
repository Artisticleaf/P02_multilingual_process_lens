#!/usr/bin/env python3
"""Static audit for the hardened E164/E165 multi-family banks."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
TASK_PATH = PROJECT / "data/processed/e164_hardened_multi_family_tasks_20260501.jsonl"
SOL_PATH = PROJECT / "data/processed/e164_hardened_multi_family_candidate_solutions_20260501.jsonl"
CASE_PATH = PROJECT / "data/processed/e165_hardened_multi_family_repair_cases_20260501.jsonl"
OUT_JSON = PROJECT / "reports/E164_HARDENED_MULTI_FAMILY_STATIC_AUDIT_20260501.json"
OUT_MD = PROJECT / "reports/E164_HARDENED_MULTI_FAMILY_READY_BANK_20260501.md"

EXPECTED_GOLD = {
    "e164_geo_01_multistep_sas_similarity": "24",
    "e164_geo_02_midsegment_ratio_split": "8",
    "e164_geo_03_coordinate_collinearity_area": "0",
    "e164_set_01_boundary_absent_mod_filter": "6",
    "e164_set_02_complement_wrong_universe_large": "32",
    "e164_set_03_multiset_excluded_duplicate": "5",
    "e164_graph_01_directed_reachability_components": "6",
    "e164_graph_02_outneighbor_incoming_duplicate": "3",
    "e164_graph_03_simple_paths_with_cycles": "5",
    "e164_table_01_long_filter_zero_rows": "30",
    "e164_table_02_long_zero_match_false_row": "0",
    "e164_table_03_long_percentage_denominator": "50%",
    "e164_code_01_range_zero_endpoints_nested": "0",
    "e164_code_02_negative_index_symmetric_array": "26",
    "e164_code_03_short_circuit_zero_side_effect": "3",
    "e164_multi_01_chinese_at_most_mod_filter": "8",
    "e164_multi_02_spanish_no_mas_de_filter": "5",
    "e164_multi_03_chinese_exactly_frequency": "2",
    "e164_proof_01_common_multiple_false_lcm": "True",
    "e164_proof_02_polynomial_divisibility_false_parity": "True",
    "e164_proof_03_repeated_root_illegal_division": "True",
}

EXPECTED_FAMILIES = {
    "geometry_constraints": 3,
    "set_venn_counting": 3,
    "graph_definition": 3,
    "long_table_aggregation": 3,
    "code_boundary": 3,
    "multilingual_semantic": 3,
    "proof_validity": 3,
}

KEY_RANDOM_FORBIDDEN = [
    "AB=",
    "BC=",
    "EF=",
    "row ",
    "rows ",
    "range(",
    "arr[",
    "bump",
    "至多",
    "恰好",
    "no más",
    "divides",
    "simple path",
    "out-neighbor",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def norm(text: Any) -> str:
    return re.sub(r"\s+", "", str(text).strip().lower().rstrip(".。"))


def final_answer(solution: str) -> str:
    matches = re.findall(r"Final answer:\s*([^\n]+)", solution, flags=re.I)
    return matches[-1].strip() if matches else ""


def render_markdown(payload: dict[str, Any], tasks: list[dict[str, Any]], sols: list[dict[str, Any]], cases: list[dict[str, Any]]) -> str:
    by_task_sols: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sol in sols:
        by_task_sols[sol["task_id"]].append(sol)
    by_task_cases: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        by_task_cases[case["task_id"]].append(case)

    lines = [
        "# E164 Hardened Multi-Family Ready Bank / E164 加难 multi-family 可用题库",
        "",
        "Date / 日期：2026-05-01",
        "",
        "## Status / 状态",
        "",
        f"- Static audit passed / 静态审计通过：{payload['passed']}",
        f"- Tasks / 任务数：{payload['tasks']}",
        f"- Candidate traces / 候选过程数：{payload['candidate_solutions']}",
        f"- Repair cases / 修复 case 数：{payload['repair_cases']}",
        "- Task bank / 题库：`data/processed/e164_hardened_multi_family_tasks_20260501.jsonl`",
        "- Candidate trace bank / 候选过程库：`data/processed/e164_hardened_multi_family_candidate_solutions_20260501.jsonl`",
        "- Repair case bank / 修复 case 库：`data/processed/e165_hardened_multi_family_repair_cases_20260501.jsonl`",
        "",
        "## Plain-Language Design / 说人话设计",
        "",
        "- Each original E164 case was hardened rather than discarded. / 每个原 E164 case 都按审计意见加难或替换，而不是直接丢弃。",
        "- Every task has one valid trace, one invalid-answer-correct trace, and one invalid-answer-wrong trace. / 每题都有正确过程、过程错答案对、过程错答案错三类参考过程。",
        "- The random control span is now a neutral instruction phrase: `Report only the requested value`. / random 对照统一使用中性指令 span，不再标关键题干数据。",
        "- Pinyin cases were replaced by Chinese or Spanish semantic cases. / 拼音样本已替换为中文原文或西语语义样本。",
        "- The bank is designed so full restart is more expensive: longer tables, longer code, larger graphs, multi-step geometry, and less obvious proof lemmas. / 题库让从头重做更贵：长表、长代码、大图、多步几何、更隐蔽证明 lemma。",
        "",
        "## Family Distribution / family 分布",
        "",
    ]
    for family, count in payload["families"].items():
        lines.append(f"- `{family}`：{count}")
    lines.extend(["", "## Case Inventory / 逐题清单", ""])
    lines.append("| task_id | family | gold | trap | hardened reason / 加难理由 | repair cases |")
    lines.append("|---|---|---|---|---|---|")
    for task in tasks:
        variants = ",".join(sorted(sol["candidate_variant"] for sol in by_task_sols[task["task_id"]]))
        case_count = len(by_task_cases[task["task_id"]])
        lines.append(
            f"| {task['task_id']} | {task['family']} | {task['gold_answer']} | {task['answer_preserving_trap_type']} | {task['hardening_note_zh']} | {case_count}; {variants} |"
        )
    lines.extend(
        [
            "",
            "## Use Notes / 使用说明",
            "",
            "1. E164 generation should use the task bank only; do not expose gold answers or trap notes in prompts. / E164 生成只用 task bank，不把答案或陷阱说明放入 prompt。",
            "2. E165 repair can use the repair case bank with the existing E162 runner by passing `--case-bank data/processed/e165_hardened_multi_family_repair_cases_20260501.jsonl`. / E165 修复可复用 E162 runner。",
            "3. First smoke should run one case from `long_table_aggregation` or `proof_validity`, not the easiest geometry/code case. / 首个 smoke 建议选长表或证明，不选最容易的几何/代码样本。",
            "4. Full runs should include completion-token budgets 128/256/512/1024/2048/8192 to test localized cost advantage. / 全量建议加入 token 预算曲线。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    tasks = load_jsonl(TASK_PATH)
    sols = load_jsonl(SOL_PATH)
    cases = load_jsonl(CASE_PATH)
    issues: list[dict[str, Any]] = []

    task_by_id = {task["task_id"]: task for task in tasks}
    if set(task_by_id) != set(EXPECTED_GOLD):
        issues.append({"issue": "task_id_set_mismatch", "expected": sorted(EXPECTED_GOLD), "got": sorted(task_by_id)})
    if len(tasks) != 21:
        issues.append({"issue": "expected_21_tasks", "got": len(tasks)})
    if len(sols) != 63:
        issues.append({"issue": "expected_63_candidate_solutions", "got": len(sols)})
    if len(cases) != 42:
        issues.append({"issue": "expected_42_repair_cases", "got": len(cases)})

    fams = Counter(task["family"] for task in tasks)
    if dict(sorted(fams.items())) != dict(sorted(EXPECTED_FAMILIES.items())):
        issues.append({"issue": "family_distribution_mismatch", "got": dict(fams)})

    for task in tasks:
        task_id = task["task_id"]
        expected = EXPECTED_GOLD.get(task_id)
        if norm(task["gold_answer"]) != norm(expected):
            issues.append({"task_id": task_id, "issue": "gold_mismatch", "expected": expected, "got": task["gold_answer"]})
        for flag in ["gold_answer_in_prompt_by_design", "trap_note_in_prompt_by_design", "manual_label_in_prompt_by_design", "error_span_in_prompt_by_design"]:
            if task.get(flag):
                issues.append({"task_id": task_id, "issue": f"leak_flag_true::{flag}"})
        random_span = task.get("random_location_span", "")
        if random_span != "Report only the requested value":
            issues.append({"task_id": task_id, "issue": "random_span_not_neutral", "random_span": random_span})
        if any(token.lower() in random_span.lower() for token in KEY_RANDOM_FORBIDDEN):
            issues.append({"task_id": task_id, "issue": "random_span_contains_key_token", "random_span": random_span})
        if random_span not in task["problem"]:
            issues.append({"task_id": task_id, "issue": "random_span_not_literal_in_problem"})
        if "pinyin" in task["source_material"].lower() or any(p in task["problem"].lower() for p in ["zhi duo", "qiahao", "zhengshu", "qiu "]):
            issues.append({"task_id": task_id, "issue": "pinyin_or_romanized_chinese_in_main_bank"})

    sols_by_task = defaultdict(list)
    for sol in sols:
        sols_by_task[sol["task_id"]].append(sol)
        if sol["task_id"] not in task_by_id:
            issues.append({"solution_id": sol["solution_id"], "issue": "missing_task"})
            continue
        task = task_by_id[sol["task_id"]]
        if norm(sol["gold_answer"]) != norm(task["gold_answer"]):
            issues.append({"solution_id": sol["solution_id"], "issue": "solution_gold_mismatch"})
        extracted = final_answer(sol["candidate_solution"])
        if norm(extracted) != norm(sol["source_extracted_final"]):
            issues.append({"solution_id": sol["solution_id"], "issue": "source_extracted_final_mismatch", "parsed": extracted, "stored": sol["source_extracted_final"]})
        source_final_correct = norm(extracted) == norm(task["gold_answer"])
        if source_final_correct != bool(sol["source_final_correct"]):
            issues.append({"solution_id": sol["solution_id"], "issue": "source_final_correct_flag_mismatch"})
        if sol["candidate_variant"] == "valid_reference":
            if not sol["manual_process_valid_strict"]:
                issues.append({"solution_id": sol["solution_id"], "issue": "valid_reference_marked_invalid"})
            if sol.get("manual_error_span"):
                issues.append({"solution_id": sol["solution_id"], "issue": "valid_reference_has_error_span"})
        else:
            if sol["manual_process_valid_strict"]:
                issues.append({"solution_id": sol["solution_id"], "issue": "invalid_reference_marked_valid"})
            span = sol.get("manual_error_span") or ""
            if not span:
                issues.append({"solution_id": sol["solution_id"], "issue": "missing_manual_error_span"})
            elif span not in sol["candidate_solution"]:
                issues.append({"solution_id": sol["solution_id"], "issue": "manual_error_span_not_literal"})

    for task_id, rows in sols_by_task.items():
        variants = sorted(sol["candidate_variant"] for sol in rows)
        if variants != ["invalid_answer_preserving_reference", "invalid_answer_wrong_reference", "valid_reference"]:
            issues.append({"task_id": task_id, "issue": "bad_candidate_variants", "variants": variants})

    cases_by_task = defaultdict(list)
    for case in cases:
        cases_by_task[case["task_id"]].append(case)
        task = task_by_id.get(case["task_id"])
        if not task:
            issues.append({"case_id": case["case_id"], "issue": "missing_task"})
            continue
        if "Final answer:" in case.get("prefix_text", ""):
            issues.append({"case_id": case["case_id"], "issue": "prefix_contains_final_answer"})
        span = case.get("manual_error_span") or ""
        if span and span not in case.get("source_trace", ""):
            issues.append({"case_id": case["case_id"], "issue": "manual_error_span_not_in_source_trace"})
        if span and span not in case.get("prefix_text", ""):
            issues.append({"case_id": case["case_id"], "issue": "prefix_does_not_include_error_span"})
        if case.get("random_location_span") != "Report only the requested value":
            issues.append({"case_id": case["case_id"], "issue": "case_random_span_not_neutral"})
        if case.get("gold_answer_in_prompt_by_design") or case.get("manual_label_in_prompt_by_design"):
            issues.append({"case_id": case["case_id"], "issue": "case_leakage_flag_true"})
        if case.get("case_type") == "controlled_invalid_answer_preserving_trace" and not case.get("source_final_correct"):
            issues.append({"case_id": case["case_id"], "issue": "answer_preserving_case_not_final_correct"})
        if case.get("case_type") == "controlled_invalid_answer_wrong_trace" and case.get("source_final_correct"):
            issues.append({"case_id": case["case_id"], "issue": "wrong_answer_case_final_correct"})

    for task_id, rows in cases_by_task.items():
        if len(rows) != 2:
            issues.append({"task_id": task_id, "issue": "expected_two_repair_cases", "got": len(rows)})
        types = sorted(case["case_type"] for case in rows)
        if types != ["controlled_invalid_answer_preserving_trace", "controlled_invalid_answer_wrong_trace"]:
            issues.append({"task_id": task_id, "issue": "bad_repair_case_types", "types": types})

    payload = {
        "passed": not issues,
        "issues": issues,
        "tasks": len(tasks),
        "candidate_solutions": len(sols),
        "repair_cases": len(cases),
        "families": dict(sorted(fams.items())),
        "candidate_variants": dict(sorted(Counter(sol["candidate_variant"] for sol in sols).items())),
        "repair_case_types": dict(sorted(Counter(case["case_type"] for case in cases).items())),
        "random_control_strategy": "neutral_instruction_span_not_key_data",
        "pinyin_removed_from_main_bank": True,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(payload, tasks, sols, cases), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
