# E10 Evidence Chain Join Smoke

This is an offline probe joining manual audit labels with E07 answer-option trap margins. It is not causal; it screens whether route/task answer priors align with observed process-selection risk.

## Overall Join

- manual rows: 154
- rows with E07 route/task margin: 154

## E07 Margin Buckets

| bucket | n | process invalid | strict ACPI | paper-grade ACPI | final wrong | format broken |
|---|---:|---:|---:|---:|---:|---:|
| strong_neg_<=-1 | 66 | 8 | 3 | 1 | 3 | 44 |
| weak_neg_-1..0 | 49 | 6 | 4 | 2 | 2 | 20 |
| nonneg_>=0 | 39 | 4 | 2 | 1 | 2 | 13 |

## By Model And Margin Sign

| model | sign | n | process invalid | strict ACPI | mean margin | top risk |
|---|---|---:|---:|---:|---:|---|
| deepseek_r1_0528_qwen3_8b | neg | 17 | 1 | 1 | -1.504 | truncated_valid_or_no_clean_final |
| deepseek_r1_0528_qwen3_8b | nonneg | 3 | 1 | 1 | 0.536 | truncated_valid_or_no_clean_final |
| phi4_mini_reasoning | neg | 13 | 7 | 3 | -1.622 | truncated_valid_or_no_clean_final |
| phi4_mini_reasoning | nonneg | 4 | 0 | 0 | 2.042 | truncated_valid_or_no_clean_final |
| qwen35_9b | neg | 75 | 5 | 2 | -1.177 | valid_clean |
| qwen35_9b | nonneg | 8 | 0 | 0 | 0.148 | valid_clean |
| qwen3_14b_base | neg | 10 | 1 | 1 | -0.828 | valid_clean |
| qwen3_14b_base | nonneg | 24 | 3 | 1 | 1.256 | valid_clean |

## ACPI / Semantic Drift Rows With E07 Context

| idx | model | task | route | margin | pred | risk | earliest error |
|---:|---|---|---|---:|---|---|---|
| 4 | deepseek_r1_0528_qwen3_8b | disc_zh_75_price | zh->en | -0.687 | 80 | self_corrected_discount_semantic_confusion | translates 七五折 as 75% discount |
| 6 | deepseek_r1_0528_qwen3_8b | disc_zh_75_price | en->zh | 0.500 | 60 | self_corrected_75_percent_surface_confusion | 折扣是75% off |
| 178 | phi4_mini_reasoning | deriv_sum | zh->zh | -0.726 | 2x + 3 | acpi_truncated_wrong_derivative_rule | x 的导数是0 |
| 179 | phi4_mini_reasoning | deriv_sum | zh->zh | -0.726 | 2x + 3 | self_corrected_derivative_rule_error_truncated | 3x的导数，因为3是常数项，所以导数是0 |
| 183 | phi4_mini_reasoning | deriv_sum | en->zh | -1.443 | 2x + 3 | late_confusion_constant_vs_linear_derivative_truncated | 如果函数中有一个常数项，比如3x，那它的导数就是0 |
| 234 | qwen35_9b | disc_en_25_off | zh->zh | -0.148 | 80 | acpi_unmarked_discount_word_mismatch | 打八折，即原价的75% |
| 261 | qwen35_9b | ratio_boys_total | zh->en | -1.469 | 24 | acpi_self_corrected_arithmetic_step | 64 - 2 = 62 |
| 402 | qwen3_14b_base | deriv_sum | zh->zh | -1.086 | 2x + 3 | acpi_unmarked_wrong_derivative_rule | 3 是常数，常数的导数为 0，所以 (3x)'=3 |
| 445 | qwen3_14b_base | percent_then_discount | zh->en | 1.021 | 80 | acpi_lexical_mismatch_dabazhe_80_percent_discount | apply an 80% discount |
| 228 | qwen35_9b | disc_zh_75_price | zh->en | -0.239 | 80 | semantic_drift_qiwuzhe_to_75off_final_wrong_repeated | discount rate is 75% off |
| 229 | qwen35_9b | disc_zh_75_price | zh->en | -0.239 | 80 | semantic_drift_qiwuzhe_to_75off_final_wrong | discount is 75% off |
| 358 | qwen3_14b_base | disc_en_75_off | en->zh | 1.750 | 20 | semantic_drift_75off_to_qiwuzhe_final_wrong | 打七五折，就是原价的75% |
| 444 | qwen3_14b_base | percent_then_discount | zh->en | 1.021 | 80 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong | apply an 80% discount |

## Current Causal Reading

- Negative answer-option margins are not a clean predictor of manual process invalidity: many rows with negative E07 margins are valid but format-broken, especially when answer-form scoring is biased.
- However, the manually important discount and ratio ACPI rows sit in tasks/routes where E09 shows support/error span patchability, so the process-risk signal is not only an answer prior.
- E07 is most useful as a route/task triage tool, not as a verifier or labeler.
