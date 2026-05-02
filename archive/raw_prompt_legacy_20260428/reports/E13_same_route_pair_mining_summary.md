# E13 Same-Route Pair Mining Summary

Manual labels: `data/processed/manual_e05_audit_combined_20260427.jsonl`.

Goal: convert human-audited rows into clean sibling pairs for contrastive verification and non-verdict span patching. This is not a prevalence estimate.

## Audit Base

- audited rows: 154
- process-invalid rows: 18
- ACPI/self-corrected final-correct invalid rows: 9
- paper-grade ACPI rows: 4
- candidate pair records: 41
- scope counts: {'same_route': 7, 'same_reason_lang': 21, 'same_task': 13}

## Best Pair Candidates

| score | scope | bad | valid | model | task | routes | bad risk | valid risk | paper | earliest error |
|---:|---|---:|---:|---|---|---|---|---|---|---|
| 9.0 | same_route | 402 | 403 | qwen3_14b_base | deriv_sum | zh->zh / zh->zh | acpi_unmarked_wrong_derivative_rule | valid_clean | True | 3 是常数，常数的导数为 0，所以 (3x)'=3 |
| 7.5 | same_route | 234 | 235 | qwen35_9b | disc_en_25_off | zh->zh / zh->zh | acpi_unmarked_discount_word_mismatch | valid_correct_but_raw_or_visible_spill | True | 打八折，即原价的75% |
| 7.0 | same_reason_lang | 402 | 406 | qwen3_14b_base | deriv_sum | zh->zh / en->zh | acpi_unmarked_wrong_derivative_rule | valid_clean | True | 3 是常数，常数的导数为 0，所以 (3x)'=3 |
| 7.0 | same_reason_lang | 402 | 407 | qwen3_14b_base | deriv_sum | zh->zh / en->zh | acpi_unmarked_wrong_derivative_rule | valid_clean | True | 3 是常数，常数的导数为 0，所以 (3x)'=3 |
| 7.0 | same_reason_lang | 445 | 440 | qwen3_14b_base | percent_then_discount | zh->en / en->en | acpi_lexical_mismatch_dabazhe_80_percent_discount | valid_clean | True | apply an 80% discount |
| 7.0 | same_reason_lang | 445 | 441 | qwen3_14b_base | percent_then_discount | zh->en / en->en | acpi_lexical_mismatch_dabazhe_80_percent_discount | valid_clean | True | apply an 80% discount |
| 6.5 | same_route | 358 | 359 | qwen3_14b_base | disc_en_75_off | en->zh / en->zh | semantic_drift_75off_to_qiwuzhe_final_wrong | valid_clean | False | 打七五折，就是原价的75% |
| 6.0 | same_task | 234 | 232 | qwen35_9b | disc_en_25_off | zh->zh / en->en | acpi_unmarked_discount_word_mismatch | valid_clean | True | 打八折，即原价的75% |
| 6.0 | same_route | 261 | 260 | qwen35_9b | ratio_boys_total | zh->en / zh->en | acpi_self_corrected_arithmetic_step | valid_clean | False | 64 - 2 = 62 |
| 6.0 | same_task | 445 | 442 | qwen3_14b_base | percent_then_discount | zh->en / zh->zh | acpi_lexical_mismatch_dabazhe_80_percent_discount | valid_clean | True | apply an 80% discount |
| 5.5 | same_reason_lang | 234 | 238 | qwen35_9b | disc_en_25_off | zh->zh / en->zh | acpi_unmarked_discount_word_mismatch | valid_correct_but_raw_or_visible_spill | True | 打八折，即原价的75% |
| 5.0 | same_reason_lang | 178 | 182 | phi4_mini_reasoning | deriv_sum | zh->zh / en->zh | acpi_truncated_wrong_derivative_rule | truncated_valid_or_no_clean_final | True | x 的导数是0 |
| 5.0 | same_route | 183 | 182 | phi4_mini_reasoning | deriv_sum | en->zh / en->zh | late_confusion_constant_vs_linear_derivative_truncated | truncated_valid_or_no_clean_final | False | 如果函数中有一个常数项，比如3x，那它的导数就是0 |
| 4.5 | same_reason_lang | 229 | 225 | qwen35_9b | disc_zh_75_price | zh->en / en->en | semantic_drift_qiwuzhe_to_75off_final_wrong | valid_clean | False | discount is 75% off |
| 4.5 | same_reason_lang | 358 | 354 | qwen3_14b_base | disc_en_75_off | en->zh / zh->zh | semantic_drift_75off_to_qiwuzhe_final_wrong | valid_clean | False | 打七五折，就是原价的75% |
| 4.5 | same_reason_lang | 358 | 355 | qwen3_14b_base | disc_en_75_off | en->zh / zh->zh | semantic_drift_75off_to_qiwuzhe_final_wrong | valid_clean | False | 打七五折，就是原价的75% |
| 4.0 | same_task | 178 | 180 | phi4_mini_reasoning | deriv_sum | zh->zh / zh->en | acpi_truncated_wrong_derivative_rule | truncated_valid_or_no_clean_final | True | x 的导数是0 |
| 4.0 | same_task | 178 | 181 | phi4_mini_reasoning | deriv_sum | zh->zh / zh->en | acpi_truncated_wrong_derivative_rule | truncated_valid_or_no_clean_final | True | x 的导数是0 |
| 4.0 | same_route | 208 | 209 | phi4_mini_reasoning | frac_simplify | en->en / en->en | nonsense_spill_after_correct_fraction_start | truncated_valid_or_no_clean_final | False | 615-02-1208 |
| 4.0 | same_route | 296 | 297 | qwen35_9b | deriv_product_equiv | en->en / en->en | wrong_derivative_and_after_final_template | valid_correct_but_after_final_spill_or_trim | False | Final answer: $3x^2 + 6x$ |
| 4.0 | same_reason_lang | 228 | 225 | qwen35_9b | disc_zh_75_price | zh->en / en->en | semantic_drift_qiwuzhe_to_75off_final_wrong_repeated | valid_clean | False | discount rate is 75% off |
| 4.0 | same_reason_lang | 261 | 257 | qwen35_9b | ratio_boys_total | zh->en / en->en | acpi_self_corrected_arithmetic_step | valid_clean | False | 64 - 2 = 62 |
| 4.0 | same_reason_lang | 444 | 440 | qwen3_14b_base | percent_then_discount | zh->en / en->en | semantic_drift_dabazhe_as_80_percent_discount_final_wrong | valid_clean | False | apply an 80% discount |
| 4.0 | same_reason_lang | 444 | 441 | qwen3_14b_base | percent_then_discount | zh->en / en->en | semantic_drift_dabazhe_as_80_percent_discount_final_wrong | valid_clean | False | apply an 80% discount |
| 3.5 | same_task | 229 | 226 | qwen35_9b | disc_zh_75_price | zh->en / zh->zh | semantic_drift_qiwuzhe_to_75off_final_wrong | valid_clean | False | discount is 75% off |
| 3.0 | same_task | 228 | 226 | qwen35_9b | disc_zh_75_price | zh->en / zh->zh | semantic_drift_qiwuzhe_to_75off_final_wrong_repeated | valid_clean | False | discount rate is 75% off |
| 3.0 | same_reason_lang | 229 | 224 | qwen35_9b | disc_zh_75_price | zh->en / en->en | semantic_drift_qiwuzhe_to_75off_final_wrong | valid_correct_but_raw_or_visible_spill | False | discount is 75% off |
| 3.0 | same_task | 444 | 442 | qwen3_14b_base | percent_then_discount | zh->en / zh->zh | semantic_drift_dabazhe_as_80_percent_discount_final_wrong | valid_clean | False | apply an 80% discount |
| 2.5 | same_reason_lang | 4 | 0 | deepseek_r1_0528_qwen3_8b | disc_zh_75_price | zh->en / en->en | self_corrected_discount_semantic_confusion | truncated_valid_or_no_clean_final | False | translates 七五折 as 75% discount |
| 2.5 | same_reason_lang | 6 | 2 | deepseek_r1_0528_qwen3_8b | disc_zh_75_price | en->zh / zh->zh | self_corrected_75_percent_surface_confusion | truncated_valid_or_no_clean_final | False | 折扣是75% off |
| 2.5 | same_reason_lang | 179 | 182 | phi4_mini_reasoning | deriv_sum | zh->zh / en->zh | self_corrected_derivative_rule_error_truncated | truncated_valid_or_no_clean_final | False | 3x的导数，因为3是常数项，所以导数是0 |
| 2.5 | same_reason_lang | 228 | 224 | qwen35_9b | disc_zh_75_price | zh->en / en->en | semantic_drift_qiwuzhe_to_75off_final_wrong_repeated | valid_correct_but_raw_or_visible_spill | False | discount rate is 75% off |
| 2.5 | same_reason_lang | 261 | 256 | qwen35_9b | ratio_boys_total | zh->en / en->en | acpi_self_corrected_arithmetic_step | valid_correct_but_after_final_spill_or_trim | False | 64 - 2 = 62 |
| 2.0 | same_task | 183 | 180 | phi4_mini_reasoning | deriv_sum | en->zh / zh->en | late_confusion_constant_vs_linear_derivative_truncated | truncated_valid_or_no_clean_final | False | 如果函数中有一个常数项，比如3x，那它的导数就是0 |
| 2.0 | same_task | 183 | 181 | phi4_mini_reasoning | deriv_sum | en->zh / zh->en | late_confusion_constant_vs_linear_derivative_truncated | truncated_valid_or_no_clean_final | False | 如果函数中有一个常数项，比如3x，那它的导数就是0 |
| 2.0 | same_reason_lang | 296 | 300 | qwen35_9b | deriv_product_equiv | en->en / zh->en | wrong_derivative_and_after_final_template | valid_correct_but_after_final_spill_or_trim | False | Final answer: $3x^2 + 6x$ |
| 2.0 | same_reason_lang | 296 | 301 | qwen35_9b | deriv_product_equiv | en->en / zh->en | wrong_derivative_and_after_final_template | valid_correct_but_after_final_spill_or_trim | False | Final answer: $3x^2 + 6x$ |
| 1.5 | same_task | 4 | 2 | deepseek_r1_0528_qwen3_8b | disc_zh_75_price | zh->en / zh->zh | self_corrected_discount_semantic_confusion | truncated_valid_or_no_clean_final | False | translates 七五折 as 75% discount |
| 1.5 | same_task | 6 | 0 | deepseek_r1_0528_qwen3_8b | disc_zh_75_price | en->zh / en->en | self_corrected_75_percent_surface_confusion | truncated_valid_or_no_clean_final | False | 折扣是75% off |
| 1.5 | same_task | 179 | 180 | phi4_mini_reasoning | deriv_sum | zh->zh / zh->en | self_corrected_derivative_rule_error_truncated | truncated_valid_or_no_clean_final | False | 3x的导数，因为3是常数项，所以导数是0 |

## Interpretation

- Strongest same-route causal pairs now include Qwen3-14B `disc_en_75_off` 358/359, Qwen3-14B `deriv_sum` 402/403, Qwen3.5 `ratio_boys_total` 261/260, and Qwen3.5 `disc_en_25_off` 234/235.
- Qwen3-14B `percent_then_discount` 445 remains important but its cleanest existing sibling is same-task/same-input rather than same-route; treat it as lexicalization evidence, not a clean route-controlled pair.
- Self-corrected rows are useful for safety/data-cleaning, but paper-grade method claims should prioritize unmarked ACPI or semantic-drift rows.
- The next experiment should use this bank for expanded contrastive verification before any head/MLP localization.
