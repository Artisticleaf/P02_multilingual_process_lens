# E53-E57 Leakage and Logic Audit / E53-E57 泄露与逻辑审计（2026-04-28）

- JSON / 机器可读结果：`reports/E53_E57_LEAKAGE_LOGIC_AUDIT_20260428.json`
- Overall / 总体：PASS
- Scope / 范围：检查 E53-E57 官方结果文件、prompt 构造、gold/trap 泄露、E57 人审标签、E56 superseded 文件归档和 E55/E56 LOTO 机制边界。

## Checklist / 检查表

| status | check | detail |
|---|---|---|
| PASS | E53_answer_anchor_ablation/qwen35_27b exists | results/E53_answer_anchor_ablation/qwen35_27b_e53_answer_anchor_ablation.json |
| PASS | E53_answer_anchor_ablation/gemma4_31b_it exists | results/E53_answer_anchor_ablation/gemma4_31b_it_e53_answer_anchor_ablation.json |
| PASS | E53_answer_anchor_ablation/gemma4_26b_a4b_it exists | results/E53_answer_anchor_ablation/gemma4_26b_a4b_it_e53_answer_anchor_ablation.json |
| PASS | E54_parameterized_no_leak_generalization/qwen35_27b exists | results/E54_parameterized_no_leak_generalization/qwen35_27b_e42_official_template_parity_chat.json |
| PASS | E54_parameterized_no_leak_generalization/gemma4_31b_it exists | results/E54_parameterized_no_leak_generalization/gemma4_31b_it_e42_official_template_parity_chat.json |
| PASS | E54_parameterized_no_leak_generalization/gemma4_26b_a4b_it exists | results/E54_parameterized_no_leak_generalization/gemma4_26b_a4b_it_e42_official_template_parity_chat.json |
| PASS | E55_residual_to_logit_mediation/qwen35_27b exists | results/E55_residual_to_logit_mediation/qwen35_27b_e55_residual_to_logit_mediation.json |
| PASS | E55_residual_to_logit_mediation/gemma4_31b_it exists | results/E55_residual_to_logit_mediation/gemma4_31b_it_e55_residual_to_logit_mediation.json |
| PASS | E55_residual_to_logit_mediation/gemma4_26b_a4b_it exists | results/E55_residual_to_logit_mediation/gemma4_26b_a4b_it_e55_residual_to_logit_mediation.json |
| PASS | E56_component_decomposition/qwen35_27b exists | results/E56_component_decomposition/qwen35_27b_e56_component_decomposition.json |
| PASS | E56_component_decomposition/gemma4_31b_it exists | results/E56_component_decomposition/gemma4_31b_it_e56_component_decomposition.json |
| PASS | E56_component_decomposition/gemma4_26b_a4b_it exists | results/E56_component_decomposition/gemma4_26b_a4b_it_e56_component_decomposition.json |
| PASS | E57_p0_hard_task_final_correct_harvesting/qwen35_27b exists | results/E57_p0_hard_task_final_correct_harvesting/qwen35_27b_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json |
| PASS | E57_p0_hard_task_final_correct_harvesting/gemma4_31b_it exists | results/E57_p0_hard_task_final_correct_harvesting/gemma4_31b_it_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json |
| PASS | E57_p0_hard_task_final_correct_harvesting/gemma4_26b_a4b_it exists | results/E57_p0_hard_task_final_correct_harvesting/gemma4_26b_a4b_it_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json |
| PASS | E53 data row count | rows=96 |
| PASS | E53 no gold label inserted | gold_label_in_prompt all false |
| PASS | E53 no error-span annotation inserted | known_error_span_in_prompt all false |
| PASS | E53 removed/masked final_correct is None | rows=48 |
| PASS | E53 gemma4_26b_a4b_it_e53_answer_anchor_ablation.json row count | rows=96 |
| PASS | E53 gemma4_26b_a4b_it_e53_answer_anchor_ablation.json prompt format official_if_chat | official_if_chat |
| PASS | E53 gemma4_26b_a4b_it_e53_answer_anchor_ablation.json chat template used | True |
| PASS | E53 gemma4_31b_it_e53_answer_anchor_ablation.json row count | rows=96 |
| PASS | E53 gemma4_31b_it_e53_answer_anchor_ablation.json prompt format official_if_chat | official_if_chat |
| PASS | E53 gemma4_31b_it_e53_answer_anchor_ablation.json chat template used | True |
| PASS | E53 qwen35_27b_e53_answer_anchor_ablation.json row count | rows=96 |
| PASS | E53 qwen35_27b_e53_answer_anchor_ablation.json prompt format official_if_chat | official_if_chat |
| PASS | E53 qwen35_27b_e53_answer_anchor_ablation.json chat template used | True |
| PASS | E54 data row count | rows=36 |
| PASS | E54 gold_label_in_prompt all false | gold_label_in_prompt |
| PASS | E54 known_error_span_in_prompt all false | known_error_span_in_prompt |
| PASS | E54 known_error_span_annotation_in_prompt all false | known_error_span_annotation_in_prompt |
| PASS | E54 one valid and one invalid per task | 18 paired tasks |
| PASS | E54 gemma4_31b_it_e42_official_template_parity_chat.json result row count | rows=72 |
| PASS | E54 gemma4_31b_it_e42_official_template_parity_chat.json prompt format official_if_chat | official_if_chat |
| PASS | E54 gemma4_31b_it_e42_official_template_parity_chat.json chat template used | True |
| PASS | E54 qwen35_27b_e42_official_template_parity_chat.json result row count | rows=72 |
| PASS | E54 qwen35_27b_e42_official_template_parity_chat.json prompt format official_if_chat | official_if_chat |
| PASS | E54 qwen35_27b_e42_official_template_parity_chat.json chat template used | True |
| PASS | E54 gemma4_26b_a4b_it_e42_official_template_parity_chat.json result row count | rows=72 |
| PASS | E54 gemma4_26b_a4b_it_e42_official_template_parity_chat.json prompt format official_if_chat | official_if_chat |
| PASS | E54 gemma4_26b_a4b_it_e42_official_template_parity_chat.json chat template used | True |
| PASS | E55_residual_to_logit_mediation gemma4_26b_a4b_it_e55_residual_to_logit_mediation.json LOTO scope note | E55 is a causal diagnostic over controlled E42 rows. Directions are built leave-one-task-out and labels/spans are not inserted in prompts. |
| PASS | E55_residual_to_logit_mediation gemma4_26b_a4b_it_e55_residual_to_logit_mediation.json chat template used | True |
| PASS | E55_residual_to_logit_mediation gemma4_31b_it_e55_residual_to_logit_mediation.json LOTO scope note | E55 is a causal diagnostic over controlled E42 rows. Directions are built leave-one-task-out and labels/spans are not inserted in prompts. |
| PASS | E55_residual_to_logit_mediation gemma4_31b_it_e55_residual_to_logit_mediation.json chat template used | True |
| PASS | E55_residual_to_logit_mediation qwen35_27b_e55_residual_to_logit_mediation.json LOTO scope note | E55 is a causal diagnostic over controlled E42 rows. Directions are built leave-one-task-out and labels/spans are not inserted in prompts. |
| PASS | E55_residual_to_logit_mediation qwen35_27b_e55_residual_to_logit_mediation.json chat template used | True |
| PASS | E56_component_decomposition gemma4_26b_a4b_it_e56_component_decomposition.json LOTO scope note | Component directions are leave-one-task-out diagnostics on E42 controlled rows; this is not a full circuit proof. |
| PASS | E56_component_decomposition gemma4_26b_a4b_it_e56_component_decomposition.json chat template used | True |
| PASS | E56 gemma4_26b_a4b_it_e56_component_decomposition.json has token_mixer | ['mlp_output', 'residual_layer_output', 'token_mixer_output'] |
| PASS | E56_component_decomposition gemma4_31b_it_e56_component_decomposition.json LOTO scope note | Component directions are leave-one-task-out diagnostics on E42 controlled rows; this is not a full circuit proof. |
| PASS | E56_component_decomposition gemma4_31b_it_e56_component_decomposition.json chat template used | True |
| PASS | E56 gemma4_31b_it_e56_component_decomposition.json has token_mixer | ['mlp_output', 'residual_layer_output', 'token_mixer_output'] |
| PASS | E56_component_decomposition qwen35_27b_e56_component_decomposition.json LOTO scope note | Component directions are leave-one-task-out diagnostics on E42 controlled rows; this is not a full circuit proof. |
| PASS | E56_component_decomposition qwen35_27b_e56_component_decomposition.json chat template used | True |
| PASS | E56 qwen35_27b_e56_component_decomposition.json has token_mixer | ['mlp_output', 'residual_layer_output', 'token_mixer_output'] |
| PASS | E56 stale Qwen missing-token-mixer archived | archive=True active=True |
| PASS | E57 qwen35_27b_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json no gold answer rows | 0 |
| PASS | E57 qwen35_27b_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json no trap note rows | 0 |
| PASS | E57 qwen35_27b_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json variants no answer_anchor | ['neutral', 'answer_first_no_gold', 'self_check'] |
| PASS | E57 qwen35_27b_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json thinking false | false |
| PASS | E57 qwen35_27b_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json k=4 | 4 |
| PASS | E57 qwen35_27b_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json max_tasks=6 | 6 |
| PASS | E57 qwen35_27b_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json row count | rows=72 |
| PASS | E57 gemma4_26b_a4b_it_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json no gold answer rows | 0 |
| PASS | E57 gemma4_26b_a4b_it_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json no trap note rows | 0 |
| PASS | E57 gemma4_26b_a4b_it_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json variants no answer_anchor | ['neutral', 'answer_first_no_gold', 'self_check'] |
| PASS | E57 gemma4_26b_a4b_it_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json thinking false | false |
| PASS | E57 gemma4_26b_a4b_it_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json k=4 | 4 |
| PASS | E57 gemma4_26b_a4b_it_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json max_tasks=6 | 6 |
| PASS | E57 gemma4_26b_a4b_it_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json row count | rows=72 |
| PASS | E57 gemma4_31b_it_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json no gold answer rows | 0 |
| PASS | E57 gemma4_31b_it_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json no trap note rows | 0 |
| PASS | E57 gemma4_31b_it_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json variants no answer_anchor | ['neutral', 'answer_first_no_gold', 'self_check'] |
| PASS | E57 gemma4_31b_it_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json thinking false | false |
| PASS | E57 gemma4_31b_it_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json k=4 | 4 |
| PASS | E57 gemma4_31b_it_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json max_tasks=6 | 6 |
| PASS | E57 gemma4_31b_it_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json row count | rows=72 |
| PASS | E57 aggregate row count | rows=216 |
| PASS | E57 aggregate no gold prompt | all rows false |
| PASS | E57 aggregate no trap prompt | all rows false |
| PASS | E57 no answer_anchor variant | Counter({'neutral': 72, 'answer_first_no_gold': 72, 'self_check': 72}) |
| PASS | E57 manual audit row count | rows=119 |
| PASS | E57 manual audit all final-correct | all manual_final_correct true |
| PASS | E57 manual strict+repaired labels present | labels present |
| PASS | E57 multiple-final rows documented | multiple_final_rows=13; parser uses last anchored line |
| PASS | static verifier prompt does not insert support_span | support_span |
| PASS | static verifier prompt does not insert error_span | error_span |
| PASS | static verifier prompt does not insert manual_correction | manual_correction |
| PASS | static verifier prompt does not insert manual_process_valid | manual_process_valid |

## Key Conclusions / 关键结论

- E53/E54 verifier prompt 只插入 problem 和 completion；人工标签、support span、error span、manual correction 没有进入 prompt。错误句子本身仍在 trace 里，这是实验对象，不是泄露。
- E57 官方 hard-task run 没有 answer-anchor、没有 gold answer、没有 trap note；strict final parser 使用最后一个行首 `Final answer:`，因此先写错后修正的 trace 会被计入 final-correct，但在人审中单独标记为 repaired。
- E55/E56 的方向学习是 leave-one-task-out 诊断，不把 held-out task 标签直接用于该 task 的 probe/patch 方向；结论边界仍是 causal diagnostic，不是完整 circuit proof。
- E56 Qwen 早期遗漏 token-mixer 的旧文件已经在 archive；active 文件包含 `token_mixer_output`。
