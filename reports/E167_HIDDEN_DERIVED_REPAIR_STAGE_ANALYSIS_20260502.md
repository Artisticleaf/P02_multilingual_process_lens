# E167 Hidden-Derived Repair Stage Analysis / E167 hidden-derived 修复阶段分析

Created / 创建时间：`2026-05-02T05:07:44`.

Scope / 范围：strict `auto_boundary_only` E167. Non-oracle localized spans come from E166 hidden-triggered automatic sentence boundaries, not manual error-span endpoints. / 严格自动边界 E167；非 oracle localized span 来自 E166 hidden 触发的自动句子边界，不来自人工错步末尾。

## qwen35_27b

- Source / 来源：`logs/e167_repair_qwen35_27b_checkpoint_20260502.jsonl`.
- Rows / 行数：93; cases / case 数：16; complete variant sets / 六变体齐全 case：15.
- Leakage counts / 泄漏计数：`{'manual_span_used_as_non_oracle_warning_rows': 0, 'manual_target_used_as_hidden_trigger_rows': 0, 'gold_answer_in_prompt_rows': 0, 'manual_label_in_prompt_rows': 0}`.

| variant | n | correct | acc | total completion tokens | cost/success | mean tokens | hit-max | final marker |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_regenerate | 16 | 15 | 0.938 | 18363 | 1224.200 | 1147.688 | 0 | 16 |
| prefix_continue | 16 | 15 | 0.938 | 7716 | 514.400 | 482.250 | 0 | 16 |
| hidden_generic_warning | 16 | 13 | 0.812 | 8649 | 665.308 | 540.562 | 0 | 16 |
| hidden_localized_warning | 15 | 14 | 0.933 | 8215 | 586.786 | 547.667 | 0 | 15 |
| random_matched_warning | 15 | 14 | 0.933 | 6800 | 485.714 | 453.333 | 0 | 15 |
| oracle_manual_span | 15 | 15 | 1.000 | 7466 | 497.733 | 497.733 | 0 | 15 |

### Invalid-Answer-Wrong Repair / 答案错样本修复

| variant | n | correct | acc | cost/success |
|---|---:|---:|---:|---:|
| baseline_regenerate | 0 | 0 | NA | NA |
| prefix_continue | 0 | 0 | NA | NA |
| hidden_generic_warning | 0 | 0 | NA | NA |
| hidden_localized_warning | 0 | 0 | NA | NA |
| random_matched_warning | 0 | 0 | NA | NA |
| oracle_manual_span | 0 | 0 | NA | NA |

### Paired Deltas / 配对差异

| left vs right | pairs | left wins | right wins | one-sided p(left better) | two-sided p | acc delta | mean token delta | interpretation |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| hidden_localized_warning - prefix_continue | 15 | 0 | 0 | NA | NA | 0.000 | 44 | no_accuracy_difference_observed |
| hidden_localized_warning - hidden_generic_warning | 15 | 2 | 0 | 0.250 | 0.500 | 0.133 | -3.333 | hidden_localized_warning_trend_better_than_hidden_generic_warning_not_significant |
| hidden_localized_warning - random_matched_warning | 15 | 0 | 0 | NA | NA | 0.000 | 94.333 | no_accuracy_difference_observed |
| hidden_localized_warning - baseline_regenerate | 15 | 0 | 0 | NA | NA | 0.000 | -639.800 | no_accuracy_difference_observed |
| oracle_manual_span - hidden_localized_warning | 15 | 1 | 0 | 0.500 | 1.000 | 0.067 | -49.933 | oracle_manual_span_trend_better_than_hidden_localized_warning_not_significant |

## gemma4_31b_it

- Source / 来源：`logs/e167_repair_gemma4_31b_it_checkpoint_20260502.jsonl`.
- Rows / 行数：0; cases / case 数：0; complete variant sets / 六变体齐全 case：0.
- Leakage counts / 泄漏计数：`{'manual_span_used_as_non_oracle_warning_rows': 0, 'manual_target_used_as_hidden_trigger_rows': 0, 'gold_answer_in_prompt_rows': 0, 'manual_label_in_prompt_rows': 0}`.

| variant | n | correct | acc | total completion tokens | cost/success | mean tokens | hit-max | final marker |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_regenerate | 0 | 0 | NA | 0 | NA | NA | 0 | 0 |
| prefix_continue | 0 | 0 | NA | 0 | NA | NA | 0 | 0 |
| hidden_generic_warning | 0 | 0 | NA | 0 | NA | NA | 0 | 0 |
| hidden_localized_warning | 0 | 0 | NA | 0 | NA | NA | 0 | 0 |
| random_matched_warning | 0 | 0 | NA | 0 | NA | NA | 0 | 0 |
| oracle_manual_span | 0 | 0 | NA | 0 | NA | NA | 0 | 0 |

### Invalid-Answer-Wrong Repair / 答案错样本修复

| variant | n | correct | acc | cost/success |
|---|---:|---:|---:|---:|
| baseline_regenerate | 0 | 0 | NA | NA |
| prefix_continue | 0 | 0 | NA | NA |
| hidden_generic_warning | 0 | 0 | NA | NA |
| hidden_localized_warning | 0 | 0 | NA | NA |
| random_matched_warning | 0 | 0 | NA | NA |
| oracle_manual_span | 0 | 0 | NA | NA |

### Paired Deltas / 配对差异

| left vs right | pairs | left wins | right wins | one-sided p(left better) | two-sided p | acc delta | mean token delta | interpretation |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| hidden_localized_warning - prefix_continue | 0 | 0 | 0 | NA | NA | NA | NA | no_pairs |
| hidden_localized_warning - hidden_generic_warning | 0 | 0 | 0 | NA | NA | NA | NA | no_pairs |
| hidden_localized_warning - random_matched_warning | 0 | 0 | 0 | NA | NA | NA | NA | no_pairs |
| hidden_localized_warning - baseline_regenerate | 0 | 0 | 0 | NA | NA | NA | NA | no_pairs |
| oracle_manual_span - hidden_localized_warning | 0 | 0 | 0 | NA | NA | NA | NA | no_pairs |

## gemma4_26b_a4b_it

- Source / 来源：`logs/e167_repair_gemma4_26b_a4b_it_checkpoint_20260502.jsonl`.
- Rows / 行数：0; cases / case 数：0; complete variant sets / 六变体齐全 case：0.
- Leakage counts / 泄漏计数：`{'manual_span_used_as_non_oracle_warning_rows': 0, 'manual_target_used_as_hidden_trigger_rows': 0, 'gold_answer_in_prompt_rows': 0, 'manual_label_in_prompt_rows': 0}`.

| variant | n | correct | acc | total completion tokens | cost/success | mean tokens | hit-max | final marker |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_regenerate | 0 | 0 | NA | 0 | NA | NA | 0 | 0 |
| prefix_continue | 0 | 0 | NA | 0 | NA | NA | 0 | 0 |
| hidden_generic_warning | 0 | 0 | NA | 0 | NA | NA | 0 | 0 |
| hidden_localized_warning | 0 | 0 | NA | 0 | NA | NA | 0 | 0 |
| random_matched_warning | 0 | 0 | NA | 0 | NA | NA | 0 | 0 |
| oracle_manual_span | 0 | 0 | NA | 0 | NA | NA | 0 | 0 |

### Invalid-Answer-Wrong Repair / 答案错样本修复

| variant | n | correct | acc | cost/success |
|---|---:|---:|---:|---:|
| baseline_regenerate | 0 | 0 | NA | NA |
| prefix_continue | 0 | 0 | NA | NA |
| hidden_generic_warning | 0 | 0 | NA | NA |
| hidden_localized_warning | 0 | 0 | NA | NA |
| random_matched_warning | 0 | 0 | NA | NA |
| oracle_manual_span | 0 | 0 | NA | NA |

### Paired Deltas / 配对差异

| left vs right | pairs | left wins | right wins | one-sided p(left better) | two-sided p | acc delta | mean token delta | interpretation |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| hidden_localized_warning - prefix_continue | 0 | 0 | 0 | NA | NA | NA | NA | no_pairs |
| hidden_localized_warning - hidden_generic_warning | 0 | 0 | 0 | NA | NA | NA | NA | no_pairs |
| hidden_localized_warning - random_matched_warning | 0 | 0 | 0 | NA | NA | NA | NA | no_pairs |
| hidden_localized_warning - baseline_regenerate | 0 | 0 | 0 | NA | NA | NA | NA | no_pairs |
| oracle_manual_span - hidden_localized_warning | 0 | 0 | 0 | NA | NA | NA | NA | no_pairs |

