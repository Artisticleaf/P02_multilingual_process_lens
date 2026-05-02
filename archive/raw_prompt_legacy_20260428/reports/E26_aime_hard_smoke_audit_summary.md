# E26 AIME Hard-Task Smoke Audit / E26 AIME 困难任务 smoke 审计

Created / 创建时间: 2026-04-27T13:20:15

Scope: 3 AIME-2025 tasks, 2 routes (`en->en`, `zh->en`), 4 local models, two prompt variants (`fast`, `concise`), k=1 per variant. / 范围：3 道 AIME-2025，2 条 route，4 个本地模型，两个提示变体，每个变体每题 1 条样本。

## Aggregate / 汇总

| model | route | n | final marker | final correct strict | final wrong | no final marker | ACPI candidates |
|---|---|---:|---:|---:|---:|---:|---:|
| deepseek_r1_0528_qwen3_8b | en->en | 6 | 0 | 0 | 0 | 6 | 0 |
| deepseek_r1_0528_qwen3_8b | zh->en | 6 | 0 | 0 | 0 | 6 | 0 |
| phi4_mini_reasoning | en->en | 6 | 0 | 0 | 0 | 6 | 0 |
| phi4_mini_reasoning | zh->en | 6 | 0 | 0 | 0 | 6 | 0 |
| qwen35_9b | en->en | 6 | 0 | 0 | 0 | 6 | 0 |
| qwen35_9b | zh->en | 6 | 0 | 0 | 0 | 6 | 0 |
| qwen3_14b_base | en->en | 6 | 3 | 0 | 3 | 3 | 0 |
| qwen3_14b_base | zh->en | 6 | 2 | 0 | 2 | 4 | 0 |

## Manual Notes / 人工逐条备注

| model | task | route | gold | extracted final | marker | final correct | manual risk |
|---|---|---|---:|---|---:|---:|---|
| deepseek_r1_0528_qwen3_8b | aime25_base_divisor_p1 | en->en | 70 |  | False | False | no_final_marker_truncated_or_unresolved |
| deepseek_r1_0528_qwen3_8b | aime25_base_divisor_p1 | zh->en | 70 |  | False | False | no_final_marker_truncated_or_unresolved |
| deepseek_r1_0528_qwen3_8b | aime25_geometry_reflection_p2 | en->en | 588 |  | False | False | no_final_marker_geometry_partial_or_unresolved |
| deepseek_r1_0528_qwen3_8b | aime25_geometry_reflection_p2 | zh->en | 588 |  | False | False | no_final_marker_truncated_or_unresolved |
| deepseek_r1_0528_qwen3_8b | aime25_icecream_ordered_assign_p3 | en->en | 16 |  | False | False | no_final_marker_truncated_or_unresolved |
| deepseek_r1_0528_qwen3_8b | aime25_icecream_ordered_assign_p3 | zh->en | 16 |  | False | False | no_final_marker_truncated_or_unresolved |
| phi4_mini_reasoning | aime25_base_divisor_p1 | en->en | 70 |  | False | False | no_final_marker_truncated_or_unresolved |
| phi4_mini_reasoning | aime25_base_divisor_p1 | zh->en | 70 |  | False | False | no_final_marker_invalid_base_notation_as_three_digit |
| phi4_mini_reasoning | aime25_geometry_reflection_p2 | en->en | 588 |  | False | False | no_final_marker_geometry_partial_or_unresolved |
| phi4_mini_reasoning | aime25_geometry_reflection_p2 | zh->en | 588 |  | False | False | no_final_marker_truncated_or_unresolved |
| phi4_mini_reasoning | aime25_icecream_ordered_assign_p3 | en->en | 16 |  | False | False | no_final_marker_truncated_or_unresolved |
| phi4_mini_reasoning | aime25_icecream_ordered_assign_p3 | zh->en | 16 |  | False | False | no_final_marker_truncated_or_unresolved |
| qwen35_9b | aime25_base_divisor_p1 | en->en | 70 |  | False | False | no_final_marker_partial_reasoning_often_on_track |
| qwen35_9b | aime25_base_divisor_p1 | zh->en | 70 |  | False | False | no_final_marker_partial_reasoning_often_on_track |
| qwen35_9b | aime25_geometry_reflection_p2 | en->en | 588 |  | False | False | no_final_marker_truncated_or_unresolved |
| qwen35_9b | aime25_geometry_reflection_p2 | zh->en | 588 |  | False | False | no_final_marker_truncated_or_unresolved |
| qwen35_9b | aime25_icecream_ordered_assign_p3 | en->en | 16 |  | False | False | no_final_marker_partial_reasoning_often_on_track |
| qwen35_9b | aime25_icecream_ordered_assign_p3 | zh->en | 16 |  | False | False | no_final_marker_partial_reasoning_often_on_track |
| qwen3_14b_base | aime25_base_divisor_p1 | en->en | 70 |  | False | False | no_final_marker_truncated_or_unresolved |
| qwen3_14b_base | aime25_base_divisor_p1 | zh->en | 70 |  | False | False | no_final_marker_truncated_or_unresolved |
| qwen3_14b_base | aime25_geometry_reflection_p2 | en->en | 588 |  | False | False | no_final_marker_truncated_or_unresolved |
| qwen3_14b_base | aime25_geometry_reflection_p2 | zh->en | 588 |  | False | False | no_final_marker_geometry_partial_or_unresolved |
| qwen3_14b_base | aime25_icecream_ordered_assign_p3 | en->en | 16 |  | False | False | no_final_marker_truncated_or_unresolved |
| qwen3_14b_base | aime25_icecream_ordered_assign_p3 | zh->en | 16 |  | False | False | no_final_marker_truncated_or_unresolved |
| deepseek_r1_0528_qwen3_8b | aime25_base_divisor_p1 | en->en | 70 |  | False | False | no_final_marker_truncated_or_unresolved |
| deepseek_r1_0528_qwen3_8b | aime25_base_divisor_p1 | zh->en | 70 |  | False | False | no_final_marker_truncated_or_unresolved |
| deepseek_r1_0528_qwen3_8b | aime25_geometry_reflection_p2 | en->en | 588 |  | False | False | no_final_marker_geometry_partial_or_unresolved |
| deepseek_r1_0528_qwen3_8b | aime25_geometry_reflection_p2 | zh->en | 588 |  | False | False | no_final_marker_truncated_or_unresolved |
| deepseek_r1_0528_qwen3_8b | aime25_icecream_ordered_assign_p3 | en->en | 16 |  | False | False | no_final_marker_truncated_or_unresolved |
| deepseek_r1_0528_qwen3_8b | aime25_icecream_ordered_assign_p3 | zh->en | 16 |  | False | False | no_final_marker_truncated_or_unresolved |
| phi4_mini_reasoning | aime25_base_divisor_p1 | en->en | 70 |  | False | False | no_final_marker_truncated_or_unresolved |
| phi4_mini_reasoning | aime25_base_divisor_p1 | zh->en | 70 |  | False | False | no_final_marker_invalid_base_notation_as_three_digit |
| phi4_mini_reasoning | aime25_geometry_reflection_p2 | en->en | 588 |  | False | False | no_final_marker_geometry_partial_or_unresolved |
| phi4_mini_reasoning | aime25_geometry_reflection_p2 | zh->en | 588 |  | False | False | no_final_marker_truncated_or_unresolved |
| phi4_mini_reasoning | aime25_icecream_ordered_assign_p3 | en->en | 16 |  | False | False | no_final_marker_truncated_or_unresolved |
| phi4_mini_reasoning | aime25_icecream_ordered_assign_p3 | zh->en | 16 |  | False | False | no_final_marker_truncated_or_unresolved |
| qwen35_9b | aime25_base_divisor_p1 | en->en | 70 |  | False | False | no_final_marker_partial_reasoning_often_on_track |
| qwen35_9b | aime25_base_divisor_p1 | zh->en | 70 |  | False | False | no_final_marker_partial_reasoning_often_on_track |
| qwen35_9b | aime25_geometry_reflection_p2 | en->en | 588 |  | False | False | no_final_marker_geometry_partial_or_unresolved |
| qwen35_9b | aime25_geometry_reflection_p2 | zh->en | 588 |  | False | False | no_final_marker_geometry_partial_or_unresolved |
| qwen35_9b | aime25_icecream_ordered_assign_p3 | en->en | 16 |  | False | False | no_final_marker_partial_reasoning_often_on_track |
| qwen35_9b | aime25_icecream_ordered_assign_p3 | zh->en | 16 |  | False | False | no_final_marker_partial_reasoning_often_on_track |
| qwen3_14b_base | aime25_base_divisor_p1 | en->en | 70 | 49. | True | False | final_wrong_no_acpi |
| qwen3_14b_base | aime25_base_divisor_p1 | zh->en | 70 |  | False | False | no_final_marker_truncated_or_unresolved |
| qwen3_14b_base | aime25_geometry_reflection_p2 | en->en | 588 | 576 | True | False | final_wrong_no_acpi |
| qwen3_14b_base | aime25_geometry_reflection_p2 | zh->en | 588 | 626. | True | False | final_wrong_no_acpi |
| qwen3_14b_base | aime25_icecream_ordered_assign_p3 | en->en | 16 | 120 | True | False | final_wrong_no_acpi |
| qwen3_14b_base | aime25_icecream_ordered_assign_p3 | zh->en | 16 | 120 | True | False | final_wrong_no_acpi |

## Interpretation / 解释

- Strict final-correct traces are zero in this smoke, so there are no ACPI candidates to run hidden-layer patching on. / 本 smoke 中严格 final-correct 为 0，因此没有可用于 hidden-layer patch 的 ACPI 候选。
- Hard tasks mainly expose final-wrong or no-final-marker failures; this is a boundary showing current simple-task ACPI rates should not be extrapolated to AIME. / 难题主要暴露答案错误或无 final marker，说明不能把简单任务 ACPI 频率外推到 AIME。
- `zh->en` routes degrade prompt comprehension for some models, which is a separate route robustness issue rather than clean ACPI. / `zh->en` 对部分模型造成题意理解下降，这是 route 鲁棒性问题，不是干净 ACPI。
- Next hard-task step should use stronger/larger models or verifier-guided sampling to obtain final-correct hard traces before mechanism probes. / 下一步应使用更强模型或 verifier-guided sampling 先获得 final-correct hard traces，再做机制 probe。