# E164 Hardened Multi-Family Ready Bank / E164 加难 multi-family 可用题库

Date / 日期：2026-05-01

## Status / 状态

- Static audit passed / 静态审计通过：True
- Tasks / 任务数：21
- Candidate traces / 候选过程数：63
- Repair cases / 修复 case 数：42
- Task bank / 题库：`data/processed/e164_hardened_multi_family_tasks_20260501.jsonl`
- Candidate trace bank / 候选过程库：`data/processed/e164_hardened_multi_family_candidate_solutions_20260501.jsonl`
- Repair case bank / 修复 case 库：`data/processed/e165_hardened_multi_family_repair_cases_20260501.jsonl`

## Plain-Language Design / 说人话设计

- Each original E164 case was hardened rather than discarded. / 每个原 E164 case 都按审计意见加难或替换，而不是直接丢弃。
- Every task has one valid trace, one invalid-answer-correct trace, and one invalid-answer-wrong trace. / 每题都有正确过程、过程错答案对、过程错答案错三类参考过程。
- The random control span is now a neutral instruction phrase: `Report only the requested value`. / random 对照统一使用中性指令 span，不再标关键题干数据。
- Pinyin cases were replaced by Chinese or Spanish semantic cases. / 拼音样本已替换为中文原文或西语语义样本。
- The bank is designed so full restart is more expensive: longer tables, longer code, larger graphs, multi-step geometry, and less obvious proof lemmas. / 题库让从头重做更贵：长表、长代码、大图、多步几何、更隐蔽证明 lemma。

## Family Distribution / family 分布

- `code_boundary`：3
- `geometry_constraints`：3
- `graph_definition`：3
- `long_table_aggregation`：3
- `multilingual_semantic`：3
- `proof_validity`：3
- `set_venn_counting`：3

## Case Inventory / 逐题清单

| task_id | family | gold | trap | hardened reason / 加难理由 | repair cases |
|---|---|---|---|---|---|
| e164_geo_01_multistep_sas_similarity | geometry_constraints | 24 | false_parallel_reason_same_similarity_ratio | 比原题多了相似判定和线段比例两步；从头重算比只修局部错因更贵。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_geo_02_midsegment_ratio_split | geometry_constraints | 8 | unsupported_perpendicular_midsegment_claim | 比原题多了 DE 内部分点，局部修复只需改错因，不必完整重做。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_geo_03_coordinate_collinearity_area | geometry_constraints | 0 | wrong_slope_value_preserved_collinearity | 从“一眼 y=0”改成坐标斜率/行列式；错的是局部斜率数值，结论因斜率相等仍保持。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_set_01_boundary_absent_mod_filter | set_venn_counting | 6 | inclusive_boundary_misread_boundary_absent | 边界值 10 不在列表中，所以“<10”这个错义不会改答案；同时加入模条件降低重算便利性。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_set_02_complement_wrong_universe_large | set_venn_counting | 32 | wrong_universe_endpoint_no_complement_effect | 从 12 个数扩到 60 个数和三集合；错全集 {1..59} 因 60 不在补集中而保答案。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_set_03_multiset_excluded_duplicate | set_venn_counting | 5 | duplicate_collapse_no_effect_after_filter | 重复项存在但被 label!=C 排除；错把 occurrences 当 distinct 不改变答案，但过程定义确实错。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_graph_01_directed_reachability_components | graph_definition | 6 | directed_edges_treated_undirected_same_component | 从 4 点扩到 10 点和多个强连通分量；把有向当无向仍不跨组件，因此答案碰巧不变。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_graph_02_outneighbor_incoming_duplicate | graph_definition | 3 | incoming_edge_misread_duplicate_neighbor | 替换原 self-loop 简单题；错误地把 b->v 当 v 的出边，但 b 已经由 v->b 出现，所以答案不变。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_graph_03_simple_paths_with_cycles | graph_definition | 5 | walk_path_definition_error_nonrepeated_list | 加入两个局部 cycle；random 从头枚举会更贵，localized 只需修 simple path 定义。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_table_01_long_filter_zero_rows | long_table_aggregation | 30 | zero_amount_match_excluded_no_sum_effect | 从 6 行扩到 20 行；零金额匹配行被错删但不影响和，random 重算成本明显更高。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_table_02_long_zero_match_false_row | long_table_aggregation | 0 | false_zero_row_match_empty_sum_preserved | 空匹配集仍为 0，但假匹配行混在多行零值里；比原 4 行版本更难从头审。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_table_03_long_percentage_denominator | long_table_aggregation | 50% | all_active_denominator_same_percentage | active West 与 all active 都是 50%，但 all West 是 60%；可区分局部 denominator 修复和从头重算。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_code_01_range_zero_endpoints_nested | code_boundary | 0 | range_endpoint_omission_zero_terms | 比原单循环多了奇偶分支；错删 0 和 7 两个端点不影响结果，因为端点项为 0。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_code_02_negative_index_symmetric_array | code_boundary | 26 | negative_index_rule_masked_by_symmetry | 负索引错读被对称数组值掩盖；比一行表达式更接近真实代码边界。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_code_03_short_circuit_zero_side_effect | code_boundary | 3 | short_circuit_call_zero_effect_preserved | 错以为 bump(0) 被调用不会改 x，因此保答案；第二个 or 分支仍能制造错误答案对照。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_multi_01_chinese_at_most_mod_filter | multilingual_semantic | 8 | chinese_at_most_boundary_absent | 用中文原文替代拼音；边界 12 不在列表中，错读为 <12 不改答案。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_multi_02_spanish_no_mas_de_filter | multilingual_semantic | 5 | spanish_no_more_than_boundary_absent | 使用真实西语短语而非拼音；70 不在列表中，严格小于的错义不改答案。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_multi_03_chinese_exactly_frequency | multilingual_semantic | 2 | chinese_exactly_misread_at_least_no_extra_even | 用中文“恰好”替代 qiahao；没有偶数出现超过 3 次，所以 at least 错义不改答案。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_proof_01_common_multiple_false_lcm | proof_validity | True | false_common_multiple_lemma_true_claim | 结论很真，但错误 lemma“6 和14 的公倍数都是84 的倍数”更隐蔽，接近 proof ACPI。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_proof_02_polynomial_divisibility_false_parity | proof_validity | True | false_parity_lemma_true_divisibility | 比 n^2+n 更难；真证明需要 mod/连续整数，错 lemma 局部可定位。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |
| e164_proof_03_repeated_root_illegal_division | proof_validity | True | illegal_division_repeated_root_preserved | 非法除以可能为 0 的因子仍推出同一个根集合，是高质量 proof ACPI。 | 2; invalid_answer_preserving_reference,invalid_answer_wrong_reference,valid_reference |

## Use Notes / 使用说明

1. E164 generation should use the task bank only; do not expose gold answers or trap notes in prompts. / E164 生成只用 task bank，不把答案或陷阱说明放入 prompt。
2. E165 repair can use the repair case bank with the existing E162 runner by passing `--case-bank data/processed/e165_hardened_multi_family_repair_cases_20260501.jsonl`. / E165 修复可复用 E162 runner。
3. First smoke should run one case from `long_table_aggregation` or `proof_validity`, not the easiest geometry/code case. / 首个 smoke 建议选长表或证明，不选最容易的几何/代码样本。
4. Full runs should include completion-token budgets 128/256/512/1024/2048/8192 to test localized cost advantage. / 全量建议加入 token 预算曲线。
