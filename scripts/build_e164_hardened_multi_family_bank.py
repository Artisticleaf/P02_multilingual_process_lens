#!/usr/bin/env python3
"""Build the hardened E164 multi-family task, trace, and repair-case banks."""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
TASK_OUT = PROJECT / "data/processed/e164_hardened_multi_family_tasks_20260501.jsonl"
SOL_OUT = PROJECT / "data/processed/e164_hardened_multi_family_candidate_solutions_20260501.jsonl"
CASE_OUT = PROJECT / "data/processed/e165_hardened_multi_family_repair_cases_20260501.jsonl"
SUMMARY_OUT = PROJECT / "reports/E164_HARDENED_MULTI_FAMILY_BANK_SUMMARY_20260501.json"

NEUTRAL_RANDOM_SPAN = "Report only the requested value"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def final_answer(text: str) -> str:
    matches = re.findall(r"Final answer:\s*([^\n]+)", text, flags=re.I)
    return matches[-1].strip() if matches else ""


def sentence_end_after(text: str, start: int) -> int:
    candidates: list[int] = []
    for pat in [". ", ".\n", ". Final", "\n"]:
        pos = text.find(pat, start)
        if pos >= 0:
            candidates.append(pos + len(pat))
    return min(candidates) if candidates else min(len(text), start + 240)


def make_prefix(trace: str, span: str) -> tuple[str, str]:
    pos = trace.lower().find(span.lower())
    if pos < 0:
        return trace[: min(len(trace), 240)].strip(), "heuristic_early_cut_span_not_found"
    return trace[: sentence_end_after(trace, pos)].strip(), f"after_manual_span::{span}"


def rows() -> list[dict[str, Any]]:
    """Return one dict per hardened task.

    Every task contains a valid reference, an answer-preserving invalid trace,
    and a wrong-answer invalid trace. The neutral random span is deliberately
    present in every problem and avoids key data.
    """
    return [
        {
            "task_id": "e164_geo_01_multistep_sas_similarity",
            "original_case_id": "geo_01_sas_similarity_false_parallel",
            "family": "geometry_constraints",
            "problem": "Use exact arithmetic. In triangle ABC, AB=24, AC=32, and angle BAC equals angle EDF in triangle DEF. In triangle DEF, DE=9, DF=12, and EF=15. Point G lies on BC with BG:GC=2:3. What is GC? Report only the requested value.",
            "gold_answer": "24",
            "trap_type": "false_parallel_reason_same_similarity_ratio",
            "source_material": "SAS similarity plus ratio split",
            "hardening_note_zh": "比原题多了相似判定和线段比例两步；从头重算比只修局部错因更贵。",
            "valid_trace": "Around the included angles, AB/DE=24/9=8/3 and AC/DF=32/12=8/3. With the included angle equal, triangles ABC and DEF are similar by SAS similarity. Therefore BC=(8/3)*15=40. Since BG:GC=2:3, GC is 3/5 of BC, so GC=24. Final answer: 24",
            "invalid_answer_correct_trace": "Because AB is parallel to DE and AC is parallel to DF, the triangles have AA similarity. The scale factor from DEF to ABC is 24/9=8/3, so BC=(8/3)*15=40. Since BG:GC=2:3, GC=3/5*40=24. Final answer: 24",
            "invalid_answer_correct_span": "AB is parallel to DE and AC is parallel to DF",
            "invalid_answer_wrong_trace": "The scale factor from DEF to ABC is DE/AB=9/24=3/8, so BC=15*(3/8)=45/8. Then GC=3/5*(45/8)=27/8. Final answer: 27/8",
            "invalid_answer_wrong_span": "scale factor from DEF to ABC is DE/AB=9/24=3/8",
            "localized_hint": "The parallel-side claim may not be stated in the problem. Recheck the similarity reason before continuing.",
            "oracle_hint": "The triangles are similar by SAS similarity from two side ratios and the included angle, not by parallel-side AA.",
        },
        {
            "task_id": "e164_geo_02_midsegment_ratio_split",
            "original_case_id": "geo_02_midsegment_false_congruence",
            "family": "geometry_constraints",
            "problem": "In triangle ABC, D is the midpoint of AB and E is the midpoint of AC. BC=28. Point H lies on DE with DH:HE=3:4. What is HE? Report only the requested value.",
            "gold_answer": "8",
            "trap_type": "unsupported_perpendicular_midsegment_claim",
            "source_material": "midsegment theorem plus internal ratio",
            "hardening_note_zh": "比原题多了 DE 内部分点，局部修复只需改错因，不必完整重做。",
            "valid_trace": "D and E are midpoints, so DE is a midsegment parallel to BC and DE=BC/2=14. The ratio DH:HE=3:4 makes HE equal to 4/7 of DE. Thus HE=(4/7)*14=8. Final answer: 8",
            "invalid_answer_correct_trace": "Segment DE is perpendicular to BC and is a midsegment, so DE=BC/2=14. The ratio DH:HE=3:4 makes HE equal to 4/7 of DE. Thus HE=8. Final answer: 8",
            "invalid_answer_correct_span": "Segment DE is perpendicular to BC",
            "invalid_answer_wrong_trace": "Since D and E are midpoints, DE has the same length as BC, so DE=28. With DH:HE=3:4, HE=(4/7)*28=16. Final answer: 16",
            "invalid_answer_wrong_span": "DE has the same length as BC",
            "localized_hint": "The perpendicular claim may be unsupported. Recheck what the midpoint theorem actually states.",
            "oracle_hint": "A midsegment is parallel to the third side and half its length; it is not necessarily perpendicular to that side.",
        },
        {
            "task_id": "e164_geo_03_coordinate_collinearity_area",
            "original_case_id": "geo_03_collinear_degenerate_false_horizontal",
            "family": "geometry_constraints",
            "problem": "Points A=(4,7), B=(16,15), C=(28,23), and D=(10,11) are given, with D the midpoint of AB. What is twice the area of triangle ACD? Report only the requested value.",
            "gold_answer": "0",
            "trap_type": "wrong_slope_value_preserved_collinearity",
            "source_material": "coordinate determinant and collinearity",
            "hardening_note_zh": "从“一眼 y=0”改成坐标斜率/行列式；错的是局部斜率数值，结论因斜率相等仍保持。",
            "valid_trace": "Vector AC is (24,16) and vector AD is (6,4). The determinant is 24*4-16*6=96-96=0. Thus A,C,D are collinear and twice the area is 0. Final answer: 0",
            "invalid_answer_correct_trace": "The slopes AC and AD are both 3/4, so A,C,D are collinear. Therefore triangle ACD is degenerate and twice its area is 0. Final answer: 0",
            "invalid_answer_correct_span": "The slopes AC and AD are both 3/4",
            "invalid_answer_wrong_trace": "The slope of AC is 3/4 and the slope of AD is 2/3, so the points are not collinear. Using a mistaken area sum gives twice the area 24*4+16*6=192. Final answer: 192",
            "invalid_answer_wrong_span": "slope of AC is 3/4",
            "localized_hint": "The slope values may be wrong. Recompute the coordinate differences directly.",
            "oracle_hint": "The actual slopes are both 16/24=4/6=2/3, equivalently the determinant is zero.",
        },
        {
            "task_id": "e164_set_01_boundary_absent_mod_filter",
            "original_case_id": "set_01_at_most_boundary",
            "family": "set_venn_counting",
            "problem": "From the listed integers -12,-9,-5,-1,0,2,4,6,8,11,13,17, how many are no more than 10 and congruent to 0 or 1 modulo 3? Report only the requested value.",
            "gold_answer": "6",
            "trap_type": "inclusive_boundary_misread_boundary_absent",
            "source_material": "boundary semantics plus modular filter",
            "hardening_note_zh": "边界值 10 不在列表中，所以“<10”这个错义不会改答案；同时加入模条件降低重算便利性。",
            "valid_trace": "No more than 10 means <=10. Among the listed values, those <=10 and congruent to 0 or 1 modulo 3 are -12,-9,-5,0,4,6. There are 6. Final answer: 6",
            "invalid_answer_correct_trace": "No more than 10 means strictly less than 10. Since 10 is not listed, the same listed candidates are considered: -12,-9,-5,0,4,6. There are 6. Final answer: 6",
            "invalid_answer_correct_span": "No more than 10 means strictly less than 10",
            "invalid_answer_wrong_trace": "No more than 10 means the negative values only. The matching negative values are -12,-9,-5, so there are 3. Final answer: 3",
            "invalid_answer_wrong_span": "No more than 10 means the negative values only",
            "localized_hint": "The boundary meaning of `no more than` may be wrong. Recheck whether equality would be included.",
            "oracle_hint": "`No more than 10` means <=10. The boundary happens not to change this answer because 10 is absent.",
        },
        {
            "task_id": "e164_set_02_complement_wrong_universe_large",
            "original_case_id": "set_02_complement_wrong_universe",
            "family": "set_venn_counting",
            "problem": "Let U={1,2,...,60}. Let A be multiples of 4 in U, B be multiples of 6 in U, and C be numbers congruent to 1 modulo 5 in U. How many elements of U are in none of A, B, or C? Report only the requested value.",
            "gold_answer": "32",
            "trap_type": "wrong_universe_endpoint_no_complement_effect",
            "source_material": "three-set complement with endpoint trap",
            "hardening_note_zh": "从 12 个数扩到 60 个数和三集合；错全集 {1..59} 因 60 不在补集中而保答案。",
            "valid_trace": "|A|=15, |B|=10, |C|=12. Intersections are |A∩B|=5, |A∩C|=3, |B∩C|=2, and |A∩B∩C|=1. The union has 15+10+12-5-3-2+1=28 elements, so the complement has 60-28=32. Final answer: 32",
            "invalid_answer_correct_trace": "Use universe {1,2,...,59}. Then |A|=14, |B|=9, |C|=12, |A∩B|=4, |A∩C|=3, |B∩C|=2, and |A∩B∩C|=1. The union has 27 elements, so the complement count is 59-27=32. Final answer: 32",
            "invalid_answer_correct_span": "Use universe {1,2,...,59}",
            "invalid_answer_wrong_trace": "Ignore all overlaps. The union size is 15+10+12=37, so the complement has 60-37=23 elements. Final answer: 23",
            "invalid_answer_wrong_span": "Ignore all overlaps",
            "localized_hint": "The universe endpoint may not match the problem. Recheck the definition of U before taking the complement.",
            "oracle_hint": "The universe is {1,...,60}; using {1,...,59} is wrong even though 60 is not in the final complement.",
        },
        {
            "task_id": "e164_set_03_multiset_excluded_duplicate",
            "original_case_id": "set_03_multiset_occurrences",
            "family": "set_venn_counting",
            "problem": "A bag has entries red-A, blue-X, red-B, green-Z, red-C, blue-Y, red-D, red-C, green-R, red-E, blue-Z, red-F. Counting occurrences, how many red entries have label not equal to C? Report only the requested value.",
            "gold_answer": "5",
            "trap_type": "duplicate_collapse_no_effect_after_filter",
            "source_material": "multiset occurrence counting with excluded duplicate",
            "hardening_note_zh": "重复项存在但被 label!=C 排除；错把 occurrences 当 distinct 不改变答案，但过程定义确实错。",
            "valid_trace": "Counting occurrences means each entry is counted separately. Red entries with label not C are red-A, red-B, red-D, red-E, and red-F. The two red-C entries are excluded, so the count is 5. Final answer: 5",
            "invalid_answer_correct_trace": "Counting occurrences means duplicate item IDs should be collapsed first. After collapsing, the red non-C labels are A,B,D,E,F because the only duplicate red label is C and it is excluded. The count is 5. Final answer: 5",
            "invalid_answer_correct_span": "Counting occurrences means duplicate item IDs should be collapsed first",
            "invalid_answer_wrong_trace": "Count all red entries, including both red-C entries. The red entries are A,B,C,D,C,E,F, so there are 7. Final answer: 7",
            "invalid_answer_wrong_span": "Count all red entries",
            "localized_hint": "The duplicate-counting rule may be wrong. Recheck what `Counting occurrences` means.",
            "oracle_hint": "Occurrences count duplicate entries separately; the duplicate C entries are excluded only because the filter says label not C.",
        },
        {
            "task_id": "e164_graph_01_directed_reachability_components",
            "original_case_id": "graph_01_directed_reachability",
            "family": "graph_definition",
            "problem": "A directed graph has vertices A,B,C,D,E,F,G,H,I,J and edges A->B, B->C, C->D, D->B, C->E, E->F, F->C, G->H, H->I, I->G, J->J. Counting A itself, how many vertices are reachable from A? Report only the requested value.",
            "gold_answer": "6",
            "trap_type": "directed_edges_treated_undirected_same_component",
            "source_material": "directed reachability with disconnected components",
            "hardening_note_zh": "从 4 点扩到 10 点和多个强连通分量；把有向当无向仍不跨组件，因此答案碰巧不变。",
            "valid_trace": "Starting from A, we reach A, then B, then C. From C we reach D and E; from E we reach F; F returns to C. No edge from this component reaches G,H,I,J. The reachable set is A,B,C,D,E,F, so the count is 6. Final answer: 6",
            "invalid_answer_correct_trace": "Treat the directed edges as undirected. The component containing A is A,B,C,D,E,F, while G,H,I and J are separate. Thus the reachable count is 6. Final answer: 6",
            "invalid_answer_correct_span": "Treat the directed edges as undirected",
            "invalid_answer_wrong_trace": "Every vertex that appears in any edge is reachable from A. That gives A,B,C,D,E,F,G,H,I,J, so the count is 10. Final answer: 10",
            "invalid_answer_wrong_span": "Every vertex that appears in any edge is reachable from A",
            "localized_hint": "The graph direction rule may be wrong. Recheck whether edges can be reversed.",
            "oracle_hint": "Reachability must follow directed edges; the undirected shortcut happens to leave the A component unchanged here.",
        },
        {
            "task_id": "e164_graph_02_outneighbor_incoming_duplicate",
            "original_case_id": "graph_02_self_loop_degree",
            "family": "graph_definition",
            "problem": "A directed graph has vertices v,a,b,c,d,e and edges v->a, v->b, v->c, b->v, a->d, d->a, c->c, e->d. Counting distinct out-neighbors of v only, how many are there? Report only the requested value.",
            "gold_answer": "3",
            "trap_type": "incoming_edge_misread_duplicate_neighbor",
            "source_material": "directed out-neighbor definition",
            "hardening_note_zh": "替换原 self-loop 简单题；错误地把 b->v 当 v 的出边，但 b 已经由 v->b 出现，所以答案不变。",
            "valid_trace": "Out-neighbors of v are the heads of edges leaving v. The outgoing edges from v are v->a, v->b, and v->c, so the distinct out-neighbors are a,b,c. The count is 3. Final answer: 3",
            "invalid_answer_correct_trace": "The incoming edge b->v also makes b an out-neighbor of v. Together with v->a, v->b, and v->c, the distinct out-neighbors are still a,b,c, so the count is 3. Final answer: 3",
            "invalid_answer_correct_span": "The incoming edge b->v also makes b an out-neighbor of v",
            "invalid_answer_wrong_trace": "Use the head of every edge in the graph as an out-neighbor of v. The heads are a,b,c,v,d,a,c,d, giving distinct values a,b,c,v,d. The count is 5. Final answer: 5",
            "invalid_answer_wrong_span": "Use the head of every edge in the graph as an out-neighbor of v",
            "localized_hint": "The incoming-edge claim may be wrong. Recheck the definition of out-neighbor.",
            "oracle_hint": "Only edges leaving v define out-neighbors of v; b->v is incoming and does not add anything.",
        },
        {
            "task_id": "e164_graph_03_simple_paths_with_cycles",
            "original_case_id": "graph_03_simple_path_vs_walk",
            "family": "graph_definition",
            "problem": "A directed graph has edges A->B, A->C, A->H, B->D, C->D, D->H, B->E, E->B, E->H, C->F, F->C, F->H. A simple path cannot repeat vertices. How many simple paths go from A to H? Report only the requested value.",
            "gold_answer": "5",
            "trap_type": "walk_path_definition_error_nonrepeated_list",
            "source_material": "simple path counting with two cycles",
            "hardening_note_zh": "加入两个局部 cycle；random 从头枚举会更贵，localized 只需修 simple path 定义。",
            "valid_trace": "The simple paths are A->H, A->B->D->H, A->C->D->H, A->B->E->H, and A->C->F->H. Walks like A->B->E->B->D->H repeat B, and A->C->F->C->D->H repeats C, so they are not simple. There are 5. Final answer: 5",
            "invalid_answer_correct_trace": "A simple path may repeat vertices. Listing the nonrepeating routes gives A->H, A->B->D->H, A->C->D->H, A->B->E->H, and A->C->F->H, so there are 5. Final answer: 5",
            "invalid_answer_correct_span": "A simple path may repeat vertices",
            "invalid_answer_wrong_trace": "A simple path may repeat vertices, so also include A->B->E->B->D->H and A->C->F->C->D->H. That gives 7 paths. Final answer: 7",
            "invalid_answer_wrong_span": "A simple path may repeat vertices",
            "localized_hint": "The definition of simple path may be wrong. Recheck whether repeated vertices are allowed.",
            "oracle_hint": "A simple path cannot repeat vertices, so the two cycle-containing walks must be excluded.",
        },
        {
            "task_id": "e164_table_01_long_filter_zero_rows",
            "original_case_id": "table_01_and_filter_zero_amount_exclusion",
            "family": "long_table_aggregation",
            "problem": "Rows are: 1 West paid Apr 12; 2 West unpaid Apr 9; 3 East paid Apr 7; 4 West paid Mar 5; 5 West paid Apr 6; 6 West paid Apr 0; 7 North paid Apr 10; 8 West paid Apr 9; 9 West refunded Apr -4; 10 West paid May 8; 11 East unpaid Apr 0; 12 West paid Apr 3; 13 South paid Apr 11; 14 West unpaid May 2; 15 West paid Mar 0; 16 West paid Apr 0; 17 East paid May 4; 18 North unpaid Apr 6; 19 West canceled Apr 5; 20 East paid Apr 2. Sum amount where region=West AND status=paid AND month=Apr. Report only the requested value.",
            "gold_answer": "30",
            "trap_type": "zero_amount_match_excluded_no_sum_effect",
            "source_material": "20-row table with AND filters and zero rows",
            "hardening_note_zh": "从 6 行扩到 20 行；零金额匹配行被错删但不影响和，random 重算成本明显更高。",
            "valid_trace": "Rows matching West, paid, and Apr are 1,5,6,8,12,16. Their amounts sum to 12+6+0+9+3+0=30. Final answer: 30",
            "invalid_answer_correct_trace": "Rows with amount 0 should be excluded before checking the filter. Then the matching positive rows are 1,5,8,12, with amounts 12,6,9,3. The sum is 30. Final answer: 30",
            "invalid_answer_correct_span": "Rows with amount 0 should be excluded before checking the filter",
            "invalid_answer_wrong_trace": "For West Apr rows, status does not matter once region and month match. Include rows 1,2,5,6,8,9,12,16,19, whose amounts sum to 40. Final answer: 40",
            "invalid_answer_wrong_span": "status does not matter once region and month match",
            "localized_hint": "The zero-amount row handling may be wrong. Recheck whether a zero amount can still satisfy the filter.",
            "oracle_hint": "Rows 6 and 16 satisfy all filters; excluding them as nonmatches is a process error even though they add 0.",
        },
        {
            "task_id": "e164_table_02_long_zero_match_false_row",
            "original_case_id": "table_02_zero_row_false_match",
            "family": "long_table_aggregation",
            "problem": "Rows are: 1 North paid 5; 2 South refunded 8; 3 East paid 0; 4 North paid 0; 5 West refunded 0; 6 North pending 7; 7 South paid 0; 8 East refunded 3; 9 North paid 12; 10 West paid 2; 11 North paid 0; 12 South refunded 0; 13 East pending 0; 14 West refunded 4; 15 North canceled 0; 16 East paid 6; 17 South refunded 5; 18 West pending 0. Sum amount for rows where region=North AND status=refunded. Report only the requested value.",
            "gold_answer": "0",
            "trap_type": "false_zero_row_match_empty_sum_preserved",
            "source_material": "18-row table with empty matching set",
            "hardening_note_zh": "空匹配集仍为 0，但假匹配行混在多行零值里；比原 4 行版本更难从头审。",
            "valid_trace": "No row has both region North and status refunded. The sum over an empty matching set is 0. Final answer: 0",
            "invalid_answer_correct_trace": "Row 11 is North refunded with amount 0. Using that row, the sum is 0. Final answer: 0",
            "invalid_answer_correct_span": "Row 11 is North refunded with amount 0",
            "invalid_answer_wrong_trace": "Region does not matter for refunded rows. Refunded rows 2,5,8,12,14,17 have amounts 8,0,3,0,4,5, summing to 20. Final answer: 20",
            "invalid_answer_wrong_span": "Region does not matter for refunded rows",
            "localized_hint": "The claimed matching row may not satisfy both filter conditions. Recheck row 11.",
            "oracle_hint": "Row 11 is North paid, not North refunded; there are no matching rows.",
        },
        {
            "task_id": "e164_table_03_long_percentage_denominator",
            "original_case_id": "table_03_percentage_denominator_swap",
            "family": "long_table_aggregation",
            "problem": "Rows are: 1 West active pass; 2 West active pass; 3 West active pass; 4 West active pass; 5 West active fail; 6 West active fail; 7 West active fail; 8 West active fail; 9 East active pass; 10 East active pass; 11 East active fail; 12 East active fail; 13 South active pass; 14 South active pass; 15 South active fail; 16 South active fail; 17 West inactive pass; 18 West inactive pass; 19 East inactive fail; 20 East inactive fail; 21 South inactive pass; 22 South inactive fail; 23 North active pass; 24 North active fail. Among active West rows, what percent pass? Report only the requested value.",
            "gold_answer": "50%",
            "trap_type": "all_active_denominator_same_percentage",
            "source_material": "24-row table with denominator trap",
            "hardening_note_zh": "active West 与 all active 都是 50%，但 all West 是 60%；可区分局部 denominator 修复和从头重算。",
            "valid_trace": "Active West rows are 1-8. Four pass and four fail, so the pass rate is 4/8=50%. Final answer: 50%",
            "invalid_answer_correct_trace": "The denominator should be all active rows. There are 18 active rows, with 9 pass and 9 fail, so the percentage is 9/18=50%. Final answer: 50%",
            "invalid_answer_correct_span": "The denominator should be all active rows",
            "invalid_answer_wrong_trace": "Use all West rows as the denominator. West rows are 1-8 and 17-18, with 6 pass out of 10, so the percentage is 60%. Final answer: 60%",
            "invalid_answer_wrong_span": "Use all West rows as the denominator",
            "localized_hint": "The denominator may not match `active West`. Recheck the conditioning group.",
            "oracle_hint": "The denominator is active West rows only; all-active happens to give the same percentage here but is the wrong process.",
        },
        {
            "task_id": "e164_code_01_range_zero_endpoints_nested",
            "original_case_id": "code_01_range_start_zero",
            "family": "code_boundary",
            "problem": "What does this Python code print?\n```python\n# audit tag: C1\ntotal = 0\nfor i in range(0, 8):\n    term = i * (i - 7)\n    if i % 2 == 0:\n        total += term\n    else:\n        total -= term\nprint(total)\n```\nReport only the requested value.",
            "gold_answer": "0",
            "trap_type": "range_endpoint_omission_zero_terms",
            "source_material": "Python range endpoints with signed accumulation",
            "hardening_note_zh": "比原单循环多了奇偶分支；错删 0 和 7 两个端点不影响结果，因为端点项为 0。",
            "valid_trace": "Python range(0,8) gives i=0,1,2,3,4,5,6,7. The terms are 0,-6,-10,-12,-12,-10,-6,0, with odd terms subtracted and even terms added. The accumulated total is 0. Final answer: 0",
            "invalid_answer_correct_trace": "Python range(0,8) skips the start 0 and stops before 7, so i=1,2,3,4,5,6. The omitted endpoint terms would be zero, and the signed accumulation over 1 through 6 is still 0. Final answer: 0",
            "invalid_answer_correct_span": "Python range(0,8) skips the start 0 and stops before 7",
            "invalid_answer_wrong_trace": "Python range(0,8) includes 8. The original total 0 then adds the extra even term 8*(8-7)=8, so the print value is 8. Final answer: 8",
            "invalid_answer_wrong_span": "Python range(0,8) includes 8",
            "localized_hint": "The Python range boundary rule may be wrong. Recheck whether the start and stop values are included.",
            "oracle_hint": "Python range(start, stop) includes the start value and excludes the stop value; in this loop the last visited value is one less than the stop.",
        },
        {
            "task_id": "e164_code_02_negative_index_symmetric_array",
            "original_case_id": "code_02_negative_index_symmetric_value",
            "family": "code_boundary",
            "problem": "What does this Python code print?\n```python\n# audit tag: C2\narr = [4, 9, 1, 9, 4]\ntotal = 0\nfor idx in [-1, 1, -5, 3]:\n    total += arr[idx]\nprint(total)\n```\nReport only the requested value.",
            "gold_answer": "26",
            "trap_type": "negative_index_rule_masked_by_symmetry",
            "source_material": "Python negative indexing with symmetric endpoints",
            "hardening_note_zh": "负索引错读被对称数组值掩盖；比一行表达式更接近真实代码边界。",
            "valid_trace": "arr[-1] is the last element 4, arr[1] is 9, arr[-5] is the first element 4, and arr[3] is 9. The total is 4+9+4+9=26. Final answer: 26",
            "invalid_answer_correct_trace": "arr[-1] is the first element in Python, so it is 4; arr[1] is 9; arr[-5] is the last element, also 4; arr[3] is 9. The total is 26. Final answer: 26",
            "invalid_answer_correct_span": "arr[-1] is the first element in Python",
            "invalid_answer_wrong_trace": "Negative indices are invalid in Python, so arr[-1] raises an error before printing a number. Final answer: Error",
            "invalid_answer_wrong_span": "Negative indices are invalid in Python",
            "localized_hint": "The negative-index rule may be wrong. Recheck how Python interprets index -1.",
            "oracle_hint": "In Python, arr[-1] is the last element, not the first; the endpoint values happen to match here.",
        },
        {
            "task_id": "e164_code_03_short_circuit_zero_side_effect",
            "original_case_id": "code_03_short_circuit_side_effect",
            "family": "code_boundary",
            "problem": "What does this Python code print?\n```python\n# audit tag: C3\nx = 0\ndef bump(n):\n    global x\n    x += n\n    return True\nif False and bump(0):\n    x += 100\nif True or bump(7):\n    x += 3\nprint(x)\n```\nReport only the requested value.",
            "gold_answer": "3",
            "trap_type": "short_circuit_call_zero_effect_preserved",
            "source_material": "Python short-circuit evaluation with side effects",
            "hardening_note_zh": "错以为 bump(0) 被调用不会改 x，因此保答案；第二个 or 分支仍能制造错误答案对照。",
            "valid_trace": "In False and bump(0), Python short-circuits, so bump(0) is not called and the first body does not run. In True or bump(7), Python short-circuits, so bump(7) is not called, but the if body runs and adds 3. The print value is 3. Final answer: 3",
            "invalid_answer_correct_trace": "bump(0) is called before the False and condition fails, but it adds 0, and the first body does not run. The True or bump(7) condition runs the second body, adding 3. The print value is 3. Final answer: 3",
            "invalid_answer_correct_span": "bump(0) is called before the False and condition fails",
            "invalid_answer_wrong_trace": "In True or bump(7), bump(7) is called before the condition succeeds, so x gains 7 and then the body adds 3. The print value is 10. Final answer: 10",
            "invalid_answer_wrong_span": "bump(7) is called before the condition succeeds",
            "localized_hint": "The short-circuit evaluation claim may be wrong. Recheck whether the function call is evaluated.",
            "oracle_hint": "False and ... does not evaluate the right side; True or ... also does not evaluate the right side.",
        },
        {
            "task_id": "e164_multi_01_chinese_at_most_mod_filter",
            "original_case_id": "multi_01_pinyin_zhi_duo_wei",
            "family": "multilingual_semantic",
            "problem": "给定整数列表 L=[-11,-8,-5,-2,1,4,7,10,13,16,19,22]. Count entries x such that x 至多 12, where 至多 means at most, and x is congruent to 1 modulo 3. Report only the requested value.",
            "gold_answer": "8",
            "trap_type": "chinese_at_most_boundary_absent",
            "source_material": "Chinese boundary semantics",
            "hardening_note_zh": "用中文原文替代拼音；边界 12 不在列表中，错读为 <12 不改答案。",
            "valid_trace": "至多 12 means at most 12, so x<=12. The listed entries congruent to 1 modulo 3 and <=12 are -11,-8,-5,-2,1,4,7,10. There are 8. Final answer: 8",
            "invalid_answer_correct_trace": "至多 12 means strictly less than 12. Since 12 is not in the list, the entries satisfying the filter are still -11,-8,-5,-2,1,4,7,10. There are 8. Final answer: 8",
            "invalid_answer_correct_span": "至多 12 means strictly less than 12",
            "invalid_answer_wrong_trace": "至多 12 means at least 12. The listed entries at least 12 and congruent to 1 modulo 3 are 13,16,19,22, so there are 4. Final answer: 4",
            "invalid_answer_wrong_span": "至多 12 means at least 12",
            "localized_hint": "The meaning of `至多` may be wrong. Recheck the Chinese boundary word.",
            "oracle_hint": "`至多 12` means at most 12, i.e. <=12; it does not mean strictly less or at least.",
        },
        {
            "task_id": "e164_multi_02_spanish_no_mas_de_filter",
            "original_case_id": "multi_02_no_more_than_boundary",
            "family": "multilingual_semantic",
            "problem": "Scores are 41,45,50,54,59,63,68,72,77,81,86. Count scores that are no más de 70, where Spanish no más de means no more than, and are at least 50. Report only the requested value.",
            "gold_answer": "5",
            "trap_type": "spanish_no_more_than_boundary_absent",
            "source_material": "Spanish-English boundary semantics",
            "hardening_note_zh": "使用真实西语短语而非拼音；70 不在列表中，严格小于的错义不改答案。",
            "valid_trace": "No más de 70 means no more than 70, so scores must be <=70. With the at-least-50 condition, the scores are 50,54,59,63,68. There are 5. Final answer: 5",
            "invalid_answer_correct_trace": "No más de 70 means strictly less than 70. Since 70 is not one of the scores, the scores satisfying both conditions are 50,54,59,63,68. There are 5. Final answer: 5",
            "invalid_answer_correct_span": "No más de 70 means strictly less than 70",
            "invalid_answer_wrong_trace": "No más de 70 means at least 70. With the at-least-50 condition, the scores are 72,77,81,86, so there are 4. Final answer: 4",
            "invalid_answer_wrong_span": "No más de 70 means at least 70",
            "localized_hint": "The Spanish boundary phrase may be wrong. Recheck `no más de` against `no more than`.",
            "oracle_hint": "`No más de 70` means no more than 70, i.e. <=70.",
        },
        {
            "task_id": "e164_multi_03_chinese_exactly_frequency",
            "original_case_id": "multi_03_mixed_exactly_qiahao",
            "family": "multilingual_semantic",
            "problem": "在列表 [2,2,2,3,5,5,8,8,8,11,14,17] 中, count distinct even values that appear 恰好 3 times. Here 恰好 means exactly. Report only the requested value.",
            "gold_answer": "2",
            "trap_type": "chinese_exactly_misread_at_least_no_extra_even",
            "source_material": "Chinese exact-frequency semantics",
            "hardening_note_zh": "用中文“恰好”替代 qiahao；没有偶数出现超过 3 次，所以 at least 错义不改答案。",
            "valid_trace": "恰好 means exactly. The even values are 2,8,14. Value 2 appears 3 times, value 8 appears 3 times, and value 14 appears once. Thus 2 distinct even values qualify. Final answer: 2",
            "invalid_answer_correct_trace": "恰好 means at least. No even value appears more than 3 times, so the even values appearing at least 3 times are still 2 and 8. The count is 2. Final answer: 2",
            "invalid_answer_correct_span": "恰好 means at least",
            "invalid_answer_wrong_trace": "恰好 means at most. The even values appearing at most 3 times are 2,8,14, so the count is 3. Final answer: 3",
            "invalid_answer_wrong_span": "恰好 means at most",
            "localized_hint": "The Chinese word `恰好` may be misread. Recheck the definition in the problem.",
            "oracle_hint": "`恰好` means exactly, not at least or at most.",
        },
        {
            "task_id": "e164_proof_01_common_multiple_false_lcm",
            "original_case_id": "proof_01_true_claim_false_converse",
            "family": "proof_validity",
            "problem": "Decide true or false: For every integer n, if 84 divides n, then 84 divides n^2. Report only the requested value.",
            "gold_answer": "True",
            "trap_type": "false_common_multiple_lemma_true_claim",
            "source_material": "divisibility proof with false lcm lemma",
            "hardening_note_zh": "结论很真，但错误 lemma“6 和14 的公倍数都是84 的倍数”更隐蔽，接近 proof ACPI。",
            "valid_trace": "If 84 divides n, write n=84k for an integer k. Then n^2=84*(84k^2), so 84 divides n^2. Final answer: True",
            "invalid_answer_correct_trace": "Since 6 divides n and 14 divides n, and any common multiple of 6 and 14 is a multiple of 84, n is a multiple of 84. Then n^2 is also a multiple of 84. Final answer: True",
            "invalid_answer_correct_span": "any common multiple of 6 and 14 is a multiple of 84",
            "invalid_answer_wrong_trace": "84 dividing n does not force 84 to divide n^2; for example, n=84 gives n^2 not divisible by 84. Final answer: False",
            "invalid_answer_wrong_span": "n=84 gives n^2 not divisible by 84",
            "localized_hint": "The common-multiple lemma may be false. Recheck the least common multiple of 6 and 14.",
            "oracle_hint": "The least common multiple of 6 and 14 is 42, not 84; the claim is true directly from n=84k.",
        },
        {
            "task_id": "e164_proof_02_polynomial_divisibility_false_parity",
            "original_case_id": "proof_02_even_square_false_lemma",
            "family": "proof_validity",
            "problem": "Decide true or false: For every integer n, n^4 - n^2 is divisible by 12. Report only the requested value.",
            "gold_answer": "True",
            "trap_type": "false_parity_lemma_true_divisibility",
            "source_material": "divisibility by 3 and 4 proof",
            "hardening_note_zh": "比 n^2+n 更难；真证明需要 mod/连续整数，错 lemma 局部可定位。",
            "valid_trace": "n^4-n^2=n^2(n-1)(n+1). Among n-1,n,n+1 one factor is divisible by 3. For divisibility by 4, if n is even then n^2 is divisible by 4; if n is odd then n-1 and n+1 are both even. Thus the product is divisible by 12. Final answer: True",
            "invalid_answer_correct_trace": "n^4-n^2=n^2(n-1)(n+1). Since n^2 is always even, the expression has enough factors of 2, and among n-1,n,n+1 one factor is divisible by 3. Therefore it is divisible by 12. Final answer: True",
            "invalid_answer_correct_span": "n^2 is always even",
            "invalid_answer_wrong_trace": "For n=2, n^4-n^2=16-4=12, and 12 is not divisible by 12, so the statement is false. Final answer: False",
            "invalid_answer_wrong_span": "12 is not divisible by 12",
            "localized_hint": "The parity lemma may be false. Recheck whether n^2 is always even.",
            "oracle_hint": "n^2 is not always even; the correct proof splits even and odd n for divisibility by 4.",
        },
        {
            "task_id": "e164_proof_03_repeated_root_illegal_division",
            "original_case_id": "proof_03_illegal_division_preserved_roots",
            "family": "proof_validity",
            "problem": "Decide true or false: For real x, if (x-2)^2(x+3)=0, then x=2 or x=-3. Report only the requested value.",
            "gold_answer": "True",
            "trap_type": "illegal_division_repeated_root_preserved",
            "source_material": "zero-product proof with repeated root",
            "hardening_note_zh": "非法除以可能为 0 的因子仍推出同一个根集合，是高质量 proof ACPI。",
            "valid_trace": "By the zero-product rule, (x-2)^2=0 or x+3=0. Thus x=2 or x=-3. Final answer: True",
            "invalid_answer_correct_trace": "Divide both sides by x-2 to get (x-2)(x+3)=0. Then x=2 or x=-3, so the statement is true. Final answer: True",
            "invalid_answer_correct_span": "Divide both sides by x-2",
            "invalid_answer_wrong_trace": "Divide by (x-2)^2 to get x+3=0, so only x=-3 is possible. The statement allowing x=2 is false. Final answer: False",
            "invalid_answer_wrong_span": "Divide by (x-2)^2",
            "localized_hint": "The algebraic division step may be invalid for one possible solution. Recheck zero factors.",
            "oracle_hint": "Dividing by x-2 can be invalid when x=2; use the zero-product rule instead.",
        },
    ]


def build() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    created = datetime.now().isoformat(timespec="seconds")
    tasks: list[dict[str, Any]] = []
    sols: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    for idx, row in enumerate(rows(), start=1):
        problem = row["problem"]
        if NEUTRAL_RANDOM_SPAN not in problem:
            raise ValueError(f"{row['task_id']} missing neutral random span")
        task = {
            "created_at": created,
            "experiment": "E164_hardened_multi_family_bank",
            "task_id": row["task_id"],
            "original_case_id": row["original_case_id"],
            "family": row["family"],
            "problem": problem,
            "gold_answer": row["gold_answer"],
            "source_material": row["source_material"],
            "difficulty_tier": "hardened_v2",
            "answer_preserving_trap_type": row["trap_type"],
            "hardening_note_zh": row["hardening_note_zh"],
            "random_location_span": NEUTRAL_RANDOM_SPAN,
            "random_control_strategy": "neutral_instruction_span_not_key_data",
            "gold_answer_in_prompt_by_design": False,
            "trap_note_in_prompt_by_design": False,
            "manual_label_in_prompt_by_design": False,
            "error_span_in_prompt_by_design": False,
        }
        tasks.append(task)
        variants = [
            ("valid_reference", row["valid_trace"], True, "", ""),
            (
                "invalid_answer_preserving_reference",
                row["invalid_answer_correct_trace"],
                False,
                row["invalid_answer_correct_span"],
                row["trap_type"],
            ),
            (
                "invalid_answer_wrong_reference",
                row["invalid_answer_wrong_trace"],
                False,
                row["invalid_answer_wrong_span"],
                row["trap_type"] + "_wrong_answer",
            ),
        ]
        for variant, trace, valid, span, error_type in variants:
            extracted = final_answer(trace)
            source_final_correct = extracted.strip().lower() == str(row["gold_answer"]).strip().lower()
            sol = {
                "created_at": created,
                "experiment": "E164_hardened_multi_family_candidate_solution_bank",
                "solution_id": f"{row['task_id']}_{variant}",
                "task_id": row["task_id"],
                "family": row["family"],
                "problem": problem,
                "gold_answer": row["gold_answer"],
                "candidate_solution": trace,
                "candidate_variant": variant,
                "source_extracted_final": extracted,
                "source_final_correct": source_final_correct,
                "manual_process_valid_strict": valid,
                "manual_process_valid_repaired": valid,
                "manual_acpi_strict": (not valid and source_final_correct),
                "manual_acpi_unrepaired": (not valid and source_final_correct),
                "manual_repair_present": False,
                "manual_error_span": span,
                "manual_error_type": error_type,
                "localized_hint": row["localized_hint"] if span else "",
                "oracle_hint": row["oracle_hint"] if span else "",
                "random_location_span": NEUTRAL_RANDOM_SPAN,
                "manual_notes_zh": "Hardened E164 v2 候选过程；标签、答案和错步 span 只离线使用，不进入 blind generation prompt。",
            }
            sols.append(sol)
            if variant != "valid_reference":
                prefix, cut_mode = make_prefix(trace, span)
                cases.append(
                    {
                        "created_at": created,
                        "experiment": "E165_hardened_multi_family_error_prompt_case_bank",
                        "case_id": f"e165_{row['task_id']}_{variant}",
                        "case_type": "controlled_invalid_answer_preserving_trace"
                        if source_final_correct
                        else "controlled_invalid_answer_wrong_trace",
                        "source_experiment": "E164_hardened_multi_family_candidate_solution_bank",
                        "source_model_key": "manual_reference",
                        "task_id": row["task_id"],
                        "family": row["family"],
                        "prompt_variant_source": variant,
                        "problem": problem,
                        "gold_answer": row["gold_answer"],
                        "source_trace": trace,
                        "source_extracted_final": extracted,
                        "source_final_correct": source_final_correct,
                        "source_process_valid_strict": False,
                        "manual_error_span": span,
                        "manual_error_type": error_type,
                        "trigger_kind": "human_audited_error_span",
                        "prefix_cut_mode": cut_mode,
                        "prefix_text": prefix,
                        "localized_span": span,
                        "localized_hint": row["localized_hint"],
                        "oracle_hint": row["oracle_hint"],
                        "random_location_span": NEUTRAL_RANDOM_SPAN,
                        "random_control_strategy": "neutral_instruction_span_not_key_data",
                        "gold_answer_in_prompt_by_design": False,
                        "manual_label_in_prompt_by_design": False,
                        "notes": "Hardened v2 repair case. Prefix is causal and stops after the local wrong step, before the final answer.",
                    }
                )
    return tasks, sols, cases


def main() -> None:
    tasks, sols, cases = build()
    write_jsonl(TASK_OUT, tasks)
    write_jsonl(SOL_OUT, sols)
    write_jsonl(CASE_OUT, cases)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "task_out": str(TASK_OUT.relative_to(PROJECT)),
        "solution_out": str(SOL_OUT.relative_to(PROJECT)),
        "repair_case_out": str(CASE_OUT.relative_to(PROJECT)),
        "tasks": len(tasks),
        "candidate_solutions": len(sols),
        "repair_cases": len(cases),
        "families": dict(sorted(Counter(t["family"] for t in tasks).items())),
        "candidate_variants": dict(sorted(Counter(s["candidate_variant"] for s in sols).items())),
        "repair_case_types": dict(sorted(Counter(c["case_type"] for c in cases).items())),
        "ready_requires_static_audit": True,
    }
    write_json(SUMMARY_OUT, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
