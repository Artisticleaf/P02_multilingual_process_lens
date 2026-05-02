# E39 Surface-Semantic Generalization Summary / E39 表层语义泛化实验汇总

Created / 创建时间: 2026-04-28T00:40:49

E39 is a controlled diagnostic set with 12 surface-semantic trap families and 6 variants per family. / E39 是受控诊断集，包含 12 类表层语义陷阱，每类 6 个变体。
The central slice is `invalid_correct`: the local process semantics is wrong but the final answer is correct. / 核心切片是 `invalid_correct`：局部过程语义错误，但最终答案正确。

## Overall verifier behavior / 整体 verifier 行为

| verifier | mode | prompt | n | accuracy | yes rate | process-invalid false accept | ACPI false accept | mean margin |
|---|---|---|---:|---:|---:|---:|---:|---:|
| gemma4_31b_it | process_only | en | 72 | 0.708 | 0.653 | 0.444 | 0.500 | 3.059 |
| gemma4_31b_it | process_only | zh | 72 | 0.667 | 0.500 | 0.333 | 0.417 | 1.396 |
| gemma4_31b_it | training_candidate | en | 72 | 0.764 | 0.375 | 0.111 | 0.083 | 0.007 |
| gemma4_31b_it | training_candidate | zh | 72 | 0.750 | 0.278 | 0.083 | 0.083 | -4.638 |
| qwen35_27b | process_only | en | 72 | 0.528 | 0.972 | 0.944 | 1.000 | 2.339 |
| qwen35_27b | process_only | zh | 72 | 0.736 | 0.764 | 0.528 | 0.833 | 1.182 |
| qwen35_27b | training_candidate | en | 72 | 0.611 | 0.556 | 0.444 | 0.833 | 0.328 |
| qwen35_27b | training_candidate | zh | 72 | 0.792 | 0.347 | 0.056 | 0.083 | -0.864 |
| qwen35_9b | process_only | en | 72 | 0.667 | 0.694 | 0.528 | 0.750 | 1.288 |
| qwen35_9b | process_only | zh | 72 | 0.653 | 0.847 | 0.694 | 0.833 | 1.336 |
| qwen35_9b | training_candidate | en | 72 | 0.556 | 0.611 | 0.528 | 0.833 | 0.931 |
| qwen35_9b | training_candidate | zh | 72 | 0.611 | 0.556 | 0.417 | 0.750 | 0.576 |
| qwen3_14b_base | process_only | en | 72 | 0.806 | 0.528 | 0.222 | 0.250 | 0.681 |
| qwen3_14b_base | process_only | zh | 72 | 0.875 | 0.625 | 0.250 | 0.250 | 0.512 |
| qwen3_14b_base | training_candidate | en | 72 | 0.653 | 0.514 | 0.361 | 0.750 | 0.299 |
| qwen3_14b_base | training_candidate | zh | 72 | 0.472 | 0.694 | 0.639 | 1.000 | 0.572 |

## ACPI task-level false accepts / ACPI 任务级误接受

### gemma4_31b_it

| task / 任务 | input | process-only EN | process-only ZH | training-candidate EN | training-candidate ZH | margin EN/ZH process-only |
|---|---|---:|---:|---:|---:|---|
| coefficient_vs_exponent | en | True | False | False | False | 2.125 / -0.375 |
| each_vs_total | en | False | False | False | False | -1.250 / -4.125 |
| log_base_argument | en | True | True | False | False | 2.250 / 2.055 |
| mean_vs_median | en | False | True | False | False | -2.000 / 1.875 |
| percent_increase_vs_percent_of | en | True | True | False | False | 5.750 / 2.312 |
| prob_without_replacement | en | False | False | False | False | -6.250 / -8.438 |
| range_vs_average | en | False | False | False | False | -3.625 / -1.799 |
| reciprocal_vs_additive_inverse | en | True | True | False | False | 4.125 / 6.938 |
| round_vs_truncate | en | True | True | True | True | 11.938 / 9.250 |
| zh_exclusive_interval | zh | False | False | False | False | -5.250 / -2.688 |
| zh_perimeter_vs_area | zh | False | False | False | False | -5.500 / -2.500 |
| zh_yi_wan_unit | zh | True | False | False | False | 0.500 / -1.625 |

### qwen35_27b

| task / 任务 | input | process-only EN | process-only ZH | training-candidate EN | training-candidate ZH | margin EN/ZH process-only |
|---|---|---:|---:|---:|---:|---|
| coefficient_vs_exponent | en | True | True | True | False | 1.500 / 1.000 |
| each_vs_total | en | True | False | True | False | 0.875 / 0.000 |
| log_base_argument | en | True | True | True | False | 2.125 / 1.375 |
| mean_vs_median | en | True | True | False | False | 0.875 / 0.375 |
| percent_increase_vs_percent_of | en | True | True | True | False | 1.750 / 0.250 |
| prob_without_replacement | en | True | False | False | False | 0.250 / -0.875 |
| range_vs_average | en | True | True | True | False | 1.625 / 0.500 |
| reciprocal_vs_additive_inverse | en | True | True | True | False | 1.000 / 0.125 |
| round_vs_truncate | en | True | True | True | True | 3.500 / 2.375 |
| zh_exclusive_interval | zh | True | True | True | False | 2.000 / 1.375 |
| zh_perimeter_vs_area | zh | True | True | True | False | 1.625 / 0.875 |
| zh_yi_wan_unit | zh | True | True | True | False | 2.500 / 1.750 |

### qwen35_9b

| task / 任务 | input | process-only EN | process-only ZH | training-candidate EN | training-candidate ZH | margin EN/ZH process-only |
|---|---|---:|---:|---:|---:|---|
| coefficient_vs_exponent | en | True | True | True | True | 3.062 / 2.312 |
| each_vs_total | en | False | True | True | False | -0.625 / 0.375 |
| log_base_argument | en | True | True | True | True | 2.125 / 2.062 |
| mean_vs_median | en | False | False | True | False | -0.500 / -0.250 |
| percent_increase_vs_percent_of | en | True | True | True | True | 0.875 / 1.438 |
| prob_without_replacement | en | False | False | False | False | -1.250 / -0.125 |
| range_vs_average | en | True | True | True | True | 0.875 / 1.250 |
| reciprocal_vs_additive_inverse | en | True | True | True | True | 0.500 / 0.500 |
| round_vs_truncate | en | True | True | True | True | 2.562 / 2.500 |
| zh_exclusive_interval | zh | True | True | False | True | 0.125 / 0.625 |
| zh_perimeter_vs_area | zh | True | True | True | True | 0.875 / 1.250 |
| zh_yi_wan_unit | zh | True | True | True | True | 0.375 / 0.500 |

### qwen3_14b_base

| task / 任务 | input | process-only EN | process-only ZH | training-candidate EN | training-candidate ZH | margin EN/ZH process-only |
|---|---|---:|---:|---:|---:|---|
| coefficient_vs_exponent | en | False | False | True | True | -0.750 / -0.625 |
| each_vs_total | en | False | False | False | True | -1.500 / -0.875 |
| log_base_argument | en | False | False | True | True | -0.250 / -0.500 |
| mean_vs_median | en | False | False | True | True | -0.750 / -0.250 |
| percent_increase_vs_percent_of | en | True | True | True | True | 0.875 / 0.750 |
| prob_without_replacement | en | False | False | False | True | -1.875 / -0.750 |
| range_vs_average | en | False | False | True | True | -1.000 / -0.875 |
| reciprocal_vs_additive_inverse | en | False | False | False | True | -0.750 / -1.125 |
| round_vs_truncate | en | True | True | True | True | 2.375 / 1.501 |
| zh_exclusive_interval | zh | False | False | True | True | -0.875 / -0.125 |
| zh_perimeter_vs_area | zh | False | False | True | True | -1.500 / -1.000 |
| zh_yi_wan_unit | zh | True | True | True | True | 0.375 / 0.125 |

## Plain-language read / 人话结论

- If a verifier accepts many `invalid_correct` rows, it is using the correct final answer or downstream self-correction too strongly relative to the local process error. / 如果 verifier 接受很多 `invalid_correct` 行，说明它过度依赖最终答案或后续自我修正，而没有足够惩罚局部过程错误。
- If `training_candidate` reduces acceptance relative to `process_only`, the same model has some usable evidence but the absolute process-only objective/threshold is too permissive. / 如果 `training_candidate` 比 `process_only` 更少接受，说明同一模型有可用证据，但绝对只审过程目标/阈值太宽。
- Task-level rows identify which semantic families should be promoted to hidden-state patching in E40/E41. / 任务级表格用于挑选 E40/E41 hidden-state patch 的候选语义族。
