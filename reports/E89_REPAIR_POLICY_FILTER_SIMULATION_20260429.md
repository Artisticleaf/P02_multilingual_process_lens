# E89 Repair-Policy Filter Simulation / 修复策略感知筛选模拟（2026-04-29）

- JSON: `results/E89_repair_policy_filter_simulation/e89_repair_policy_filter_simulation.json`
- Scope / 范围：不跑新模型；汇总 E71/E81/E86/E87/E88 已保存结果。
- Plain language / 说人话：同一条 trace 是否算坏，取决于评审口径。如果口径是“任何可见错步都不允许”，修复过的草稿也算 strict invalid；如果口径是“最后保留下来的证明是否有效”，显式修复可以被接受。因此我们必须分开报告 repaired ACPI 和 unrepaired ACPI。

## Main Retention Table / 主要保留率表

| experiment | pool | filter | trace class | mean retention | total n | total accepted | models |
|---|---|---|---|---:|---:|---:|---|
| E71 | E57_hard_task | outcome_only_final_correct | repaired_acpi | 1.000 | 36 | 36 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E71 | E57_hard_task | outcome_only_final_correct | unrepaired_acpi | 1.000 | 8 | 8 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E71 | E57_hard_task | pointwise_final_surviving_proof | repaired_acpi | 0.528 | 36 | 19 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E71 | E57_hard_task | pointwise_final_surviving_proof | unrepaired_acpi | 1.000 | 8 | 8 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E71 | E57_hard_task | pointwise_repair_aware | repaired_acpi | 0.944 | 36 | 34 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E71 | E57_hard_task | pointwise_repair_aware | unrepaired_acpi | 1.000 | 8 | 8 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E71 | E57_hard_task | pointwise_strict_process | repaired_acpi | 0.056 | 36 | 2 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E71 | E57_hard_task | pointwise_strict_process | unrepaired_acpi | 0.750 | 8 | 6 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E71 | E61_language_grid | outcome_only_final_correct | no_clear_repair_invalid | 1.000 | 108 | 108 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E71 | E61_language_grid | outcome_only_final_correct | repair_marker_invalid | 1.000 | 84 | 84 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E71 | E61_language_grid | pointwise_final_surviving_proof | no_clear_repair_invalid | 0.759 | 108 | 82 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E71 | E61_language_grid | pointwise_final_surviving_proof | repair_marker_invalid | 0.726 | 84 | 61 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E71 | E61_language_grid | pointwise_repair_aware | no_clear_repair_invalid | 0.806 | 108 | 87 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E71 | E61_language_grid | pointwise_repair_aware | repair_marker_invalid | 0.917 | 84 | 77 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E71 | E61_language_grid | pointwise_strict_process | no_clear_repair_invalid | 0.037 | 108 | 4 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E71 | E61_language_grid | pointwise_strict_process | repair_marker_invalid | 0.000 | 84 | 0 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E81 | E61_language_grid_pair_selection | sibling_AB | controlled_invalid_pair_selected_by_mistake | 0.117 | 384 | 45 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E81 | E61_language_grid_pair_selection | sibling_first_second | controlled_invalid_pair_selected_by_mistake | 0.133 | 384 | 51 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E81 | E61_language_grid_pair_selection | sibling_label_free_two_pass | controlled_invalid_pair_selected_by_mistake | 0.023 | 384 | 9 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E81 | E61_language_grid_pair_selection | sibling_one_two | controlled_invalid_pair_selected_by_mistake | 0.096 | 384 | 37 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E81 | E61_language_grid_pair_selection | sibling_trace1_trace2 | controlled_invalid_pair_selected_by_mistake | 0.500 | 384 | 192 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E86 | algebra_equivalence | outcome_only_final_correct | adversarial_algebra_acpi | 1.000 | 48 | 48 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E86 | algebra_equivalence | pointwise_strict_process | adversarial_algebra_acpi | 0.000 | 48 | 0 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E86 | algebra_equivalence_pair_selection | sibling_AB | adversarial_algebra_pair_selected_by_mistake | 0.312 | 96 | 30 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E86 | algebra_equivalence_pair_selection | sibling_label_free_two_pass | adversarial_algebra_pair_selected_by_mistake | 0.198 | 96 | 19 | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate |
| E87 | E61_language_grid_pair_selection | global_bias_centered_ab | controlled_invalid_pair_selected_by_mistake | 0.333 | 96 | 32 | glm47_flash_candidate |
| E87 | E61_language_grid_pair_selection | hidden_readout_replacement | controlled_invalid_pair_selected_by_mistake | 0.000 | 48 | 0 | glm47_flash_candidate |
| E87 | E61_language_grid_pair_selection | label_free_two_pass_replacement | controlled_invalid_pair_selected_by_mistake | 0.042 | 48 | 2 | glm47_flash_candidate |
| E87 | E61_language_grid_pair_selection | raw_ab_single_order | controlled_invalid_pair_selected_by_mistake | 0.458 | 96 | 44 | glm47_flash_candidate |
| E87 | E61_language_grid_pair_selection | two_order_antisymmetric_ab | controlled_invalid_pair_selected_by_mistake | 0.188 | 48 | 9 | glm47_flash_candidate |
| E88 | answer_first_no_gold_natural_final_correct | manual_repair_aware_filter | repaired_acpi | 1.000 | 22 | 22 | gemma4_26b_a4b_it, gemma4_31b_it, glm47_flash_candidate, qwen35_27b |
| E88 | answer_first_no_gold_natural_final_correct | manual_repair_aware_filter | unrepaired_acpi | 0.000 | 1 | 0 | glm47_flash_candidate |
| E88 | answer_first_no_gold_natural_final_correct | manual_strict_process_filter | repaired_acpi | 0.000 | 22 | 0 | gemma4_26b_a4b_it, gemma4_31b_it, glm47_flash_candidate, qwen35_27b |
| E88 | answer_first_no_gold_natural_final_correct | manual_strict_process_filter | unrepaired_acpi | 0.000 | 1 | 0 | glm47_flash_candidate |
| E88 | answer_first_no_gold_natural_final_correct | outcome_only_final_correct | repaired_acpi | 1.000 | 22 | 22 | gemma4_26b_a4b_it, gemma4_31b_it, glm47_flash_candidate, qwen35_27b |
| E88 | answer_first_no_gold_natural_final_correct | outcome_only_final_correct | unrepaired_acpi | 1.000 | 1 | 1 | glm47_flash_candidate |

## Interpretation / 解释

- Outcome-only is intentionally permissive: in controlled final-correct pools it retains all ACPI traces. / 只看答案一定最宽松：受控 final-correct 池里 ACPI 会全被保留。
- Strict pointwise should reject both repaired and unrepaired visible wrong steps, but E71/E86 show it can still retain invalid traces depending on model/objective. / strict 单点口径应该拒绝修复前错步和未修复错步，但 E71/E86 显示不同模型仍会漏过。
- Repair-aware/final-surviving objectives are not 'wrong'; they answer a different scientific question: whether the final retained proof is valid. / repair-aware 或 final-surviving 不是错，而是在回答另一个问题：最终保留下来的证明是否有效。
- Sibling and label-free filters are pair-selection diagnostics, not single-trace production filters; their accepted-ACPI rate means selecting the bad sibling by mistake. / sibling/label-free 是成对诊断，不是单条生产筛选器；accepted-ACPI 指错选坏 sibling 的概率。

## Audit / 审计

- Overall / 总体：PASS
| status | check | detail |
|---|---|---|
| PASS | has E71 repair-policy records | E71 rows provide strict/repaired/unrepaired trace classes |
| PASS | has E81 sibling records | E81 rows provide raw and label-free sibling selection |
| PASS | has E88 natural manual audit records | E88 rows provide answer-first/no-gold natural hard-task repaired/unrepaired labels |
| PASS | no new model inference | E89 is a post-hoc aggregation over saved official outputs |
| PASS | retention rates bounded | all rates in [0,1] |
