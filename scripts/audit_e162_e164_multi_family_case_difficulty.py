#!/usr/bin/env python3
"""Manual difficulty audit for the E162/E164 concrete multi-family case spec."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SPEC = PROJECT / "reports/E162_E164_CONCRETE_FAMILY_CASE_SPEC_20260501.md"
OUT_MD = PROJECT / "reports/E162_E164_MULTI_FAMILY_CASE_DIFFICULTY_AUDIT_20260501.md"
OUT_JSON = PROJECT / "reports/E162_E164_MULTI_FAMILY_CASE_DIFFICULTY_AUDIT_20260501.json"


AUDITS = [
    {
        "case_id": "geo_01_sas_similarity_false_parallel",
        "family": "geometry_constraints",
        "difficulty": "low",
        "verdict": "revise_before_full",
        "audit_zh": "SAS 相似本身一眼可做，题干很短；错步“假平行”是真错，但从头重算几乎没有成本。",
        "random_zh": "`EF=5` 是关键边长，虽然不是错步，却会帮助模型直接重算。",
        "action_zh": "保留机制，改成多步几何链：加入两组三角形、隐含角等价、无关长度；random 改为中性标签或无关非关键条件。",
    },
    {
        "case_id": "geo_02_midsegment_false_congruence",
        "family": "geometry_constraints",
        "difficulty": "low",
        "verdict": "revise_before_full",
        "audit_zh": "中位线定理太直接；ACPI trace 里“全等所以一半”内部矛盾明显，模型很容易凭常识修正。",
        "random_zh": "`BC=10` 是决定答案的关键量，会触发重算。",
        "action_zh": "改成相似比例链或坐标几何，避免 trace 自相矛盾；random 不应标到唯一底边长度。",
    },
    {
        "case_id": "geo_03_collinear_degenerate_false_horizontal",
        "family": "geometry_constraints",
        "difficulty": "too_easy",
        "verdict": "smoke_only_too_easy",
        "audit_zh": "三点 (0,0),(3,4),(6,8) 的共线关系很显眼；错步“y 都是 0”过于明显。",
        "random_zh": "`A=(0,0)` 不是错步，但题目只有三个点，任意坐标 span 都会让模型重看全题。",
        "action_zh": "只适合作为 hidden replay/smoke；正式题应使用近似坐标、行列式、多个干扰点或变换后共线。",
    },
    {
        "case_id": "set_01_at_most_boundary",
        "family": "set_venn_counting",
        "difficulty": "too_easy",
        "verdict": "smoke_only_too_easy",
        "audit_zh": "边界词 `at most` 是单步语义题；错误 trace 说“严格小于”却又把 1 列进去，内部矛盾明显。",
        "random_zh": "random span 是整个集合，几乎等于让模型从题目重做。",
        "action_zh": "若做保答案 ACPI，应让边界值不在集合中，使错误规则自然但不改答案；当前只适合语义 smoke。",
    },
    {
        "case_id": "set_02_complement_wrong_universe",
        "family": "set_venn_counting",
        "difficulty": "low",
        "verdict": "revise_before_full",
        "audit_zh": "错全集是高质量机制，但 U=1..12 太小，补集可直接心算。",
        "random_zh": "`multiples of 3` 是核心条件之一，会帮助模型重构包含-排除。",
        "action_zh": "扩大 universe，加入三集合、例外元素或表格化成员；random 应避开集合定义核心词。",
    },
    {
        "case_id": "set_03_multiset_occurrences",
        "family": "set_venn_counting",
        "difficulty": "too_easy",
        "verdict": "revise_before_full",
        "audit_zh": "重复项只有一个，`Counting occurrences` 已直接给出规则；从头重做几乎零成本。",
        "random_zh": "`blue-A` 是无关项，random 设计相对干净，但题目太短仍会诱发全局重算。",
        "action_zh": "改成长 multiset：重复 ID、颜色、标签三条件组合，答案保持来自抵消或零贡献。",
    },
    {
        "case_id": "graph_01_directed_reachability",
        "family": "graph_definition",
        "difficulty": "low",
        "verdict": "revise_before_full",
        "audit_zh": "有向可达机制是对的，但图太小；把边当无向仍得到同一答案，模型从头 BFS 很快。",
        "random_zh": "`vertices A,B,C,D` 是宽泛题干片段，容易触发完整重解。",
        "action_zh": "改成 8-12 个节点、多个强连通分量、若干诱饵边；random 使用无关节点标签或标点 span。",
    },
    {
        "case_id": "graph_02_self_loop_degree",
        "family": "graph_definition",
        "difficulty": "too_easy",
        "verdict": "smoke_only_too_easy",
        "audit_zh": "题干明说 self-loop 贡献 2；错误 trace 又写 2+1+1=4，规则错和算式矛盾明显。",
        "random_zh": "`vertex v` 太泛，但题很短，仍足以触发重读题干。",
        "action_zh": "只适合检查模型是否读定义；正式题应加入多个自环、多重边、入度/出度或加权度。",
    },
    {
        "case_id": "graph_03_simple_path_vs_walk",
        "family": "graph_definition",
        "difficulty": "low",
        "verdict": "revise_before_full",
        "audit_zh": "simple path/walk 区分有价值，但图只有两条合法路径和一个诱饵 walk。",
        "random_zh": "`edge A->D` 是关键路径之一，会直接帮助枚举。",
        "action_zh": "扩成多分支图，让重复顶点 walk 数量多于 simple path；random 避开关键边。",
    },
    {
        "case_id": "table_01_and_filter_zero_amount_exclusion",
        "family": "long_table_aggregation",
        "difficulty": "moderate_low",
        "verdict": "revise_before_full",
        "audit_zh": "零金额行是否算匹配是好机制，且答案保持自然；但 6 行表太短。",
        "random_zh": "`row 6` 正好是争议行，random 不是干净无关对照。",
        "action_zh": "扩到 20-30 行，加入重复行、缺失值和多个零贡献项；random 使用无关行或列名。",
    },
    {
        "case_id": "table_02_zero_row_false_match",
        "family": "long_table_aggregation",
        "difficulty": "too_easy",
        "verdict": "smoke_only_too_easy",
        "audit_zh": "空匹配集求和为 0 是好概念，但只有 4 行；row 4 是 paid 不是 refunded，一眼可见。",
        "random_zh": "`amount 0` 会把注意力引到零值陷阱，不够随机。",
        "action_zh": "改成长表零行聚合，加入多个 0、refunded/paid 近邻和重复区域名。",
    },
    {
        "case_id": "table_03_percentage_denominator_swap",
        "family": "long_table_aggregation",
        "difficulty": "moderate_low",
        "verdict": "revise_before_full",
        "audit_zh": "分母错但答案仍 50% 是高质量保答案机制；问题是表只有 7 行，重算太便宜。",
        "random_zh": "`row 7` 虽不是 active West，但仍是题干数据行，会诱发全表重读。",
        "action_zh": "扩成长表，设计多个分母候选都给相同或相近百分比；用预算曲线测试 localized 是否省 token。",
    },
    {
        "case_id": "code_01_range_start_zero",
        "family": "code_boundary",
        "difficulty": "low",
        "verdict": "smoke_only_too_easy",
        "audit_zh": "`range(0,6)` 边界错且 skipped term 为 0，是干净 ACPI；但循环很短，可直接手算。",
        "random_zh": "`total=0` 是较干净的无关初始化 span。",
        "action_zh": "保留为 executable smoke；正式题加入嵌套循环、切片或分支，使从头执行成本更高。",
    },
    {
        "case_id": "code_02_negative_index_symmetric_value",
        "family": "code_boundary",
        "difficulty": "too_easy",
        "verdict": "revise_before_full",
        "audit_zh": "负索引误读被对称数组值掩盖，机制好；但一行代码太容易。",
        "random_zh": "`arr[1]` 是参与结果的表达式，不算完全无关。",
        "action_zh": "改成长一点的索引链，用抵消项保答案；random 选变量赋值或未参与分支。",
    },
    {
        "case_id": "code_03_short_circuit_side_effect",
        "family": "code_boundary",
        "difficulty": "moderate_low",
        "verdict": "revise_before_full",
        "audit_zh": "短路副作用是高质量代码边界机制；当前程序仍太短，模型可很快从头模拟。",
        "random_zh": "`x+=10` 在未执行分支内，相对更干净，但也提示了控制流核心。",
        "action_zh": "加入多个函数、副作用计数器、or/and 组合和异常分支，保持可执行 verifier。",
    },
    {
        "case_id": "multi_01_pinyin_zhi_duo_wei",
        "family": "multilingual_semantic",
        "difficulty": "low",
        "verdict": "exploratory_not_main_claim",
        "audit_zh": "它曾产生有趣的 Gemma dense failure，但 `zhi duo wei` 是拼音/罗马化中文，不应作为主多语义证据。",
        "random_zh": "`-8 <= x <= 8` 是核心范围，容易帮助从头重算。",
        "action_zh": "从主结果和正式 E164 中移出；可放入语言特质附录或 hidden replay 探索。",
    },
    {
        "case_id": "multi_02_no_more_than_boundary",
        "family": "multilingual_semantic",
        "difficulty": "too_easy",
        "verdict": "smoke_only_too_easy",
        "audit_zh": "`no more than` 单步边界题太简单；错误 trace 说严格小于却把 70 算进去，内部矛盾明显。",
        "random_zh": "random span 是完整分数列表，等同重做题。",
        "action_zh": "只作边界语义 smoke；正式多语义应使用真实双语/多语条件和更长筛选列表。",
    },
    {
        "case_id": "multi_03_mixed_exactly_qiahao",
        "family": "multilingual_semantic",
        "difficulty": "low",
        "verdict": "exploratory_not_main_claim",
        "audit_zh": "`qiahao` 仍是拼音，并且题干直接定义 exactly；主 claim 价值弱。",
        "random_zh": "random span 是整个列表，帮助直接计数。",
        "action_zh": "不放主证据；替换为中文原文、英文释义、符号约束混合的真实多语言样本。",
    },
    {
        "case_id": "proof_01_true_claim_false_converse",
        "family": "proof_validity",
        "difficulty": "low",
        "verdict": "smoke_only_too_easy",
        "audit_zh": "假逆命题是真正过程错，最接近 ACPI；但 6|n=>3|n 过于基础。",
        "random_zh": "`integer n` 是宽泛变量 span；题太短，random 也会让模型直接证明。",
        "action_zh": "保留为 proof smoke；正式题换成多步定理，其中假逆命题只影响中间 lemma。",
    },
    {
        "case_id": "proof_02_even_square_false_lemma",
        "family": "proof_validity",
        "difficulty": "low",
        "verdict": "revise_before_full",
        "audit_zh": "“n 和 n^2 都是偶数”是假 lemma，ACPI 质量高；但反例 n=1 很显眼。",
        "random_zh": "`n^2+n` 是核心表达式，会触发直接因式分解。",
        "action_zh": "扩成组合数/同余/不变量证明，让假 lemma 更隐蔽且可局部定位。",
    },
    {
        "case_id": "proof_03_illegal_division_preserved_roots",
        "family": "proof_validity",
        "difficulty": "moderate_low",
        "verdict": "revise_before_full",
        "audit_zh": "非法除以可能为 0 的因子是高质量证明错误；但 x^2=1 仍是教材级短题。",
        "random_zh": "`real x` 是中性但题太短，random 会触发全题重证。",
        "action_zh": "改成多根方程、参数条件或等价变形链，要求模型在局部步骤修复而不是从头秒解。",
    },
]


def extract_case_ids() -> list[str]:
    ids = []
    for line in SPEC.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            ids.append(line.removeprefix("### ").strip())
    return ids


def render_markdown(summary: dict[str, object]) -> str:
    by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    for item in AUDITS:
        by_family[item["family"]].append(item)

    lines = [
        "# E162/E164 Multi-Family Case Difficulty Audit / 多 family 题库难度审计",
        "",
        "Date / 日期：2026-05-01",
        "",
        "Scope / 范围：audit the 21 concrete cases in `reports/E162_E164_CONCRETE_FAMILY_CASE_SPEC_20260501.md`. / 审计 E164 规格文档中的 21 个具体样本。",
        "",
        "## Plain-Language Bottom Line / 说人话结论",
        "",
        "- Yes, a multi-family bank has already been designed, but it is a case spec, not a runnable JSONL task bank yet. / 我们已经设计了 multi-family 题库，但它目前是规格文档，还不是可直接全量运行的 JSONL。",
        "- The family coverage is good: geometry, set/Venn, graph, long table, code, multilingual semantics, and proof validity. / 覆盖面是对的：几何、集合/Venn、图、长表、代码、多语言语义、证明有效性。",
        "- The current cases are mostly too easy for a publication-grade localized-vs-random claim. / 这些题大多太简单，不足以支撑顶刊顶会级别的 localized-vs-random 差分 claim。",
        "- `localized` means the model is told the suspicious visible span. It can lower completion-token cost by avoiding a full re-solve, especially relative to a generic warning. / `localized` 指告诉模型可疑的可见局部 span；它能减少 completion token，尤其相对泛泛 warning。",
        "- But if the task is short, a random broad problem span also triggers a cheap full re-solve. Then random looks strong for the wrong reason. / 但题太短时，random 标到宽泛题干也会触发低成本重做，于是 random 会因为题简单而显得强。",
        "",
        "## Summary Counts / 汇总计数",
        "",
        f"- Cases audited / 审计样本数：{summary['case_count']}",
        f"- Families / family 数：{summary['family_count']}",
    ]
    for verdict, count in summary["verdict_counts"].items():
        lines.append(f"- `{verdict}`：{count}")
    lines.extend(
        [
            "",
            "Interpretation / 解读：`revise_before_full` means the mechanism is useful but must be hardened before full E164. `smoke_only_too_easy` means it can test pipeline logic or hidden replay but should not be headline evidence. `exploratory_not_main_claim` means it should be removed from the main claim, usually because it is pinyin/romanized Chinese rather than robust multilingual semantics.",
            "",
            "## Case-by-Case Audit / 逐条审计",
            "",
        ]
    )

    for family, items in by_family.items():
        lines.append(f"### {family}")
        lines.append("")
        lines.append("| case | difficulty | verdict | audit / 审计 | random control / 随机对照 | action / 修改建议 |")
        lines.append("|---|---|---|---|---|---|")
        for item in items:
            lines.append(
                "| {case_id} | {difficulty} | {verdict} | {audit_zh} | {random_zh} | {action_zh} |".format(
                    **item
                )
            )
        lines.append("")

    lines.extend(
        [
            "## Design Consequences / 对后续设计的影响",
            "",
            "1. Do not launch full E164 directly from the current spec. / 不要直接把当前规格全量转成 E164 正式实验。",
            "2. Keep the current 21 cases as smoke, hidden replay seeds, and mechanism examples. / 当前 21 题可保留作 smoke、hidden replay 种子和机制示例。",
            "3. Build a hardened v2 bank before full runs: longer tables/code/graphs, multi-step geometry, and proof tasks with less obvious false lemmas. / 正式全量前先做加难 v2：长表、长代码、复杂图、多步几何、更隐蔽的证明假 lemma。",
            "4. Redesign random controls into subconditions: neutral formatting span, unrelated non-critical data span, and matched-length different-sentence span. / random 对照拆成：中性格式 span、无关非关键数据 span、等长异句 span。",
            "5. Remove pinyin/romanized Chinese from the main multilingual claim; keep it only as exploratory language-trait evidence. / 主多语义 claim 移除拼音/罗马化中文，只作探索性语言特质证据。",
            "6. Add completion-token budget curves, e.g. 128/256/512/1024, because localized should help most when full restart is too expensive. / 加 completion-token 预算曲线；localized 的优势应该在从头重做太贵时最明显。",
            "",
            "## Updated Claim Boundary / 更新后的 claim 边界",
            "",
            "- Current evidence supports: localized visible error spans can be useful and can reduce completion-token cost relative to generic warnings. / 当前证据支持：局部可见错步提示有用，且相对泛泛 warning 可降低 completion-token 成本。",
            "- Current evidence does not yet support: localized universally beats random controls. / 当前证据还不支持：localized 全面优于 random 对照。",
            "- Main reason: current task banks are too easy, so random broad spans often induce a cheap full re-solve. / 主要原因：当前题库太简单，random 宽泛 span 常诱发低成本从头重做。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    spec_case_ids = extract_case_ids()
    audit_case_ids = [item["case_id"] for item in AUDITS]
    missing = sorted(set(spec_case_ids) - set(audit_case_ids))
    extra = sorted(set(audit_case_ids) - set(spec_case_ids))
    if missing or extra:
        raise SystemExit(f"Case ID mismatch: missing={missing}, extra={extra}")

    verdict_counts = Counter(item["verdict"] for item in AUDITS)
    summary = {
        "case_count": len(AUDITS),
        "family_count": len({item["family"] for item in AUDITS}),
        "verdict_counts": dict(verdict_counts),
        "all_cases_ready_for_full_run": False,
        "recommendation": "harden_before_jsonl_full_run",
    }
    payload = {
        "created_at": "2026-05-01T00:00:00+08:00",
        "spec": str(SPEC.relative_to(PROJECT)),
        "summary": summary,
        "audits": AUDITS,
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps({"wrote": [str(OUT_MD), str(OUT_JSON)], "summary": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
