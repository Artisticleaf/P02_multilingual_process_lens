# E16 Expanded Contrastive Pair Verifier Summary

The verifier sees a valid and an invalid sibling trace from the expanded 11-pair bank and must choose which trace has invalid reasoning. This tests whether E12 generalizes beyond four hand-picked ACPI pairs.

## Overall

| verifier | n | acc | mean target margin |
|---|---:|---:|---:|
| deepseek_r1_0528_qwen3_8b | 44 | 0.477 | 0.095 |
| phi4_mini_reasoning | 44 | 0.568 | -0.181 |
| qwen35_9b | 44 | 0.750 | 0.681 |
| qwen3_14b_base | 44 | 0.818 | 1.195 |

## Slices

| verifier | slice type | slice | n | acc | mean target margin |
|---|---|---|---:|---:|---:|
| deepseek_r1_0528_qwen3_8b | pair | phi_deriv_en_zh_183_bad_182_valid | 4 | 0.500 | 0.688 |
| deepseek_r1_0528_qwen3_8b | pair | phi_deriv_zh_178_bad_182_valid | 4 | 0.500 | -0.031 |
| deepseek_r1_0528_qwen3_8b | pair | phi_frac_en_208_bad_209_valid | 4 | 0.750 | 1.469 |
| deepseek_r1_0528_qwen3_8b | pair | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | 4 | 0.500 | -0.563 |
| deepseek_r1_0528_qwen3_8b | pair | qwen14_dabazhe_zh_en_445_bad_442_valid | 4 | 0.250 | -0.125 |
| deepseek_r1_0528_qwen3_8b | pair | qwen14_deriv_sum_zh_402_bad_403_valid | 4 | 0.500 | 0.156 |
| deepseek_r1_0528_qwen3_8b | pair | qwen14_disc75_en_zh_358_bad_359_valid | 4 | 0.500 | -0.438 |
| deepseek_r1_0528_qwen3_8b | pair | qwen35_discount_zh_234_bad_235_valid | 4 | 0.500 | -0.219 |
| deepseek_r1_0528_qwen3_8b | pair | qwen35_product_en_296_bad_297_valid | 4 | 0.250 | -1.057 |
| deepseek_r1_0528_qwen3_8b | pair | qwen35_qiwuzhe_zh_en_229_bad_225_valid | 4 | 0.500 | -0.031 |
| deepseek_r1_0528_qwen3_8b | pair | qwen35_ratio_zh_en_261_bad_260_valid | 4 | 0.500 | 1.197 |
| deepseek_r1_0528_qwen3_8b | prompt_lang | en | 22 | 0.455 | 0.046 |
| deepseek_r1_0528_qwen3_8b | prompt_lang | zh | 22 | 0.500 | 0.145 |
| deepseek_r1_0528_qwen3_8b | trace_model | phi4_mini_reasoning | 12 | 0.583 | 0.708 |
| deepseek_r1_0528_qwen3_8b | trace_model | qwen35_9b | 16 | 0.438 | -0.027 |
| deepseek_r1_0528_qwen3_8b | trace_model | qwen3_14b_base | 16 | 0.438 | -0.242 |
| phi4_mini_reasoning | pair | phi_deriv_en_zh_183_bad_182_valid | 4 | 0.750 | 0.909 |
| phi4_mini_reasoning | pair | phi_deriv_zh_178_bad_182_valid | 4 | 0.750 | -0.314 |
| phi4_mini_reasoning | pair | phi_frac_en_208_bad_209_valid | 4 | 0.500 | -0.193 |
| phi4_mini_reasoning | pair | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | 4 | 0.250 | -3.157 |
| phi4_mini_reasoning | pair | qwen14_dabazhe_zh_en_445_bad_442_valid | 4 | 0.750 | 0.007 |
| phi4_mini_reasoning | pair | qwen14_deriv_sum_zh_402_bad_403_valid | 4 | 0.250 | -1.021 |
| phi4_mini_reasoning | pair | qwen14_disc75_en_zh_358_bad_359_valid | 4 | 0.250 | -2.300 |
| phi4_mini_reasoning | pair | qwen35_discount_zh_234_bad_235_valid | 4 | 0.750 | -0.421 |
| phi4_mini_reasoning | pair | qwen35_product_en_296_bad_297_valid | 4 | 0.750 | 1.345 |
| phi4_mini_reasoning | pair | qwen35_qiwuzhe_zh_en_229_bad_225_valid | 4 | 0.250 | -0.592 |
| phi4_mini_reasoning | pair | qwen35_ratio_zh_en_261_bad_260_valid | 4 | 1.000 | 3.747 |
| phi4_mini_reasoning | prompt_lang | en | 22 | 0.591 | -0.392 |
| phi4_mini_reasoning | prompt_lang | zh | 22 | 0.545 | 0.030 |
| phi4_mini_reasoning | trace_model | phi4_mini_reasoning | 12 | 0.667 | 0.134 |
| phi4_mini_reasoning | trace_model | qwen35_9b | 16 | 0.688 | 1.020 |
| phi4_mini_reasoning | trace_model | qwen3_14b_base | 16 | 0.375 | -1.618 |
| qwen35_9b | pair | phi_deriv_en_zh_183_bad_182_valid | 4 | 0.750 | 0.813 |
| qwen35_9b | pair | phi_deriv_zh_178_bad_182_valid | 4 | 0.500 | 0.000 |
| qwen35_9b | pair | phi_frac_en_208_bad_209_valid | 4 | 1.000 | 1.281 |
| qwen35_9b | pair | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | 4 | 0.500 | 0.656 |
| qwen35_9b | pair | qwen14_dabazhe_zh_en_445_bad_442_valid | 4 | 0.500 | 0.281 |
| qwen35_9b | pair | qwen14_deriv_sum_zh_402_bad_403_valid | 4 | 1.000 | 1.125 |
| qwen35_9b | pair | qwen14_disc75_en_zh_358_bad_359_valid | 4 | 0.500 | 0.437 |
| qwen35_9b | pair | qwen35_discount_zh_234_bad_235_valid | 4 | 1.000 | 0.750 |
| qwen35_9b | pair | qwen35_product_en_296_bad_297_valid | 4 | 1.000 | 0.199 |
| qwen35_9b | pair | qwen35_qiwuzhe_zh_en_229_bad_225_valid | 4 | 0.500 | -0.094 |
| qwen35_9b | pair | qwen35_ratio_zh_en_261_bad_260_valid | 4 | 1.000 | 2.039 |
| qwen35_9b | prompt_lang | en | 22 | 0.773 | 0.753 |
| qwen35_9b | prompt_lang | zh | 22 | 0.727 | 0.609 |
| qwen35_9b | trace_model | phi4_mini_reasoning | 12 | 0.750 | 0.698 |
| qwen35_9b | trace_model | qwen35_9b | 16 | 0.875 | 0.724 |
| qwen35_9b | trace_model | qwen3_14b_base | 16 | 0.625 | 0.625 |
| qwen3_14b_base | pair | phi_deriv_en_zh_183_bad_182_valid | 4 | 0.750 | 0.688 |
| qwen3_14b_base | pair | phi_deriv_zh_178_bad_182_valid | 4 | 0.500 | -0.125 |
| qwen3_14b_base | pair | phi_frac_en_208_bad_209_valid | 4 | 1.000 | 2.000 |
| qwen3_14b_base | pair | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | 4 | 1.000 | 0.594 |
| qwen3_14b_base | pair | qwen14_dabazhe_zh_en_445_bad_442_valid | 4 | 0.750 | 0.656 |
| qwen3_14b_base | pair | qwen14_deriv_sum_zh_402_bad_403_valid | 4 | 0.500 | 0.250 |
| qwen3_14b_base | pair | qwen14_disc75_en_zh_358_bad_359_valid | 4 | 0.500 | 0.156 |
| qwen3_14b_base | pair | qwen35_discount_zh_234_bad_235_valid | 4 | 1.000 | 2.488 |
| qwen3_14b_base | pair | qwen35_product_en_296_bad_297_valid | 4 | 1.000 | 2.280 |
| qwen3_14b_base | pair | qwen35_qiwuzhe_zh_en_229_bad_225_valid | 4 | 1.000 | 2.344 |
| qwen3_14b_base | pair | qwen35_ratio_zh_en_261_bad_260_valid | 4 | 1.000 | 1.812 |
| qwen3_14b_base | prompt_lang | en | 22 | 0.818 | 1.109 |
| qwen3_14b_base | prompt_lang | zh | 22 | 0.818 | 1.281 |
| qwen3_14b_base | trace_model | phi4_mini_reasoning | 12 | 0.750 | 0.854 |
| qwen3_14b_base | trace_model | qwen35_9b | 16 | 1.000 | 2.231 |
| qwen3_14b_base | trace_model | qwen3_14b_base | 16 | 0.688 | 0.414 |

## Rows

| verifier | pair | prompt | order | target | pred | margin | bad risk |
|---|---|---|---|---|---|---:|---|
| deepseek_r1_0528_qwen3_8b | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_A | A | A | 0.375 | acpi_unmarked_wrong_derivative_rule |
| deepseek_r1_0528_qwen3_8b | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_B | B | A | -0.250 | acpi_unmarked_wrong_derivative_rule |
| deepseek_r1_0528_qwen3_8b | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_A | A | B | -0.500 | acpi_unmarked_wrong_derivative_rule |
| deepseek_r1_0528_qwen3_8b | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_B | B | B | 1.000 | acpi_unmarked_wrong_derivative_rule |
| deepseek_r1_0528_qwen3_8b | qwen14_disc75_en_zh_358_bad_359_valid | en | bad_A | A | B | -0.875 | semantic_drift_75off_to_qiwuzhe_final_wrong |
| deepseek_r1_0528_qwen3_8b | qwen14_disc75_en_zh_358_bad_359_valid | en | bad_B | B | B | 0.125 | semantic_drift_75off_to_qiwuzhe_final_wrong |
| deepseek_r1_0528_qwen3_8b | qwen14_disc75_en_zh_358_bad_359_valid | zh | bad_A | A | B | -3.000 | semantic_drift_75off_to_qiwuzhe_final_wrong |
| deepseek_r1_0528_qwen3_8b | qwen14_disc75_en_zh_358_bad_359_valid | zh | bad_B | B | B | 2.000 | semantic_drift_75off_to_qiwuzhe_final_wrong |
| deepseek_r1_0528_qwen3_8b | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_A | A | B | -0.125 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| deepseek_r1_0528_qwen3_8b | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_B | B | A | -0.125 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| deepseek_r1_0528_qwen3_8b | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_A | A | B | -1.250 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| deepseek_r1_0528_qwen3_8b | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_B | B | B | 1.000 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| deepseek_r1_0528_qwen3_8b | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | en | bad_A | A | B | -0.875 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong |
| deepseek_r1_0528_qwen3_8b | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | en | bad_B | B | B | 0.125 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong |
| deepseek_r1_0528_qwen3_8b | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | zh | bad_A | A | B | -2.250 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong |
| deepseek_r1_0528_qwen3_8b | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | zh | bad_B | B | B | 0.750 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong |
| deepseek_r1_0528_qwen3_8b | qwen35_discount_zh_234_bad_235_valid | en | bad_A | A | A | 0.125 | acpi_unmarked_discount_word_mismatch |
| deepseek_r1_0528_qwen3_8b | qwen35_discount_zh_234_bad_235_valid | en | bad_B | B | A | -0.875 | acpi_unmarked_discount_word_mismatch |
| deepseek_r1_0528_qwen3_8b | qwen35_discount_zh_234_bad_235_valid | zh | bad_A | A | B | -0.750 | acpi_unmarked_discount_word_mismatch |
| deepseek_r1_0528_qwen3_8b | qwen35_discount_zh_234_bad_235_valid | zh | bad_B | B | B | 0.625 | acpi_unmarked_discount_word_mismatch |
| deepseek_r1_0528_qwen3_8b | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_A | A | B | -0.375 | acpi_self_corrected_arithmetic_step |
| deepseek_r1_0528_qwen3_8b | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_B | B | B | 2.610 | acpi_self_corrected_arithmetic_step |
| deepseek_r1_0528_qwen3_8b | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_A | A | B | -0.750 | acpi_self_corrected_arithmetic_step |
| deepseek_r1_0528_qwen3_8b | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_B | B | B | 3.305 | acpi_self_corrected_arithmetic_step |
| deepseek_r1_0528_qwen3_8b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | en | bad_A | A | B | -0.875 | semantic_drift_qiwuzhe_to_75off_final_wrong |
| deepseek_r1_0528_qwen3_8b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | en | bad_B | B | B | 0.625 | semantic_drift_qiwuzhe_to_75off_final_wrong |
| deepseek_r1_0528_qwen3_8b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | zh | bad_A | A | B | -1.250 | semantic_drift_qiwuzhe_to_75off_final_wrong |
| deepseek_r1_0528_qwen3_8b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | zh | bad_B | B | B | 1.375 | semantic_drift_qiwuzhe_to_75off_final_wrong |
| deepseek_r1_0528_qwen3_8b | qwen35_product_en_296_bad_297_valid | en | bad_A | A | B | -2.000 | wrong_derivative_and_after_final_template |
| deepseek_r1_0528_qwen3_8b | qwen35_product_en_296_bad_297_valid | en | bad_B | B | A | -2.477 | wrong_derivative_and_after_final_template |
| deepseek_r1_0528_qwen3_8b | qwen35_product_en_296_bad_297_valid | zh | bad_A | A | B | -1.625 | wrong_derivative_and_after_final_template |
| deepseek_r1_0528_qwen3_8b | qwen35_product_en_296_bad_297_valid | zh | bad_B | B | B | 1.875 | wrong_derivative_and_after_final_template |
| deepseek_r1_0528_qwen3_8b | phi_deriv_zh_178_bad_182_valid | en | bad_A | A | B | -0.125 | acpi_truncated_wrong_derivative_rule |
| deepseek_r1_0528_qwen3_8b | phi_deriv_zh_178_bad_182_valid | en | bad_B | B | B | 0.500 | acpi_truncated_wrong_derivative_rule |
| deepseek_r1_0528_qwen3_8b | phi_deriv_zh_178_bad_182_valid | zh | bad_A | A | B | -1.500 | acpi_truncated_wrong_derivative_rule |
| deepseek_r1_0528_qwen3_8b | phi_deriv_zh_178_bad_182_valid | zh | bad_B | B | B | 1.000 | acpi_truncated_wrong_derivative_rule |
| deepseek_r1_0528_qwen3_8b | phi_deriv_en_zh_183_bad_182_valid | en | bad_A | A | B | -0.250 | late_confusion_constant_vs_linear_derivative_truncated |
| deepseek_r1_0528_qwen3_8b | phi_deriv_en_zh_183_bad_182_valid | en | bad_B | B | B | 2.250 | late_confusion_constant_vs_linear_derivative_truncated |
| deepseek_r1_0528_qwen3_8b | phi_deriv_en_zh_183_bad_182_valid | zh | bad_A | A | B | -1.625 | late_confusion_constant_vs_linear_derivative_truncated |
| deepseek_r1_0528_qwen3_8b | phi_deriv_en_zh_183_bad_182_valid | zh | bad_B | B | B | 2.375 | late_confusion_constant_vs_linear_derivative_truncated |
| deepseek_r1_0528_qwen3_8b | phi_frac_en_208_bad_209_valid | en | bad_A | A | A | 0.875 | nonsense_spill_after_correct_fraction_start |
| deepseek_r1_0528_qwen3_8b | phi_frac_en_208_bad_209_valid | en | bad_B | B | B | 2.625 | nonsense_spill_after_correct_fraction_start |
| deepseek_r1_0528_qwen3_8b | phi_frac_en_208_bad_209_valid | zh | bad_A | A | B | -0.750 | nonsense_spill_after_correct_fraction_start |
| deepseek_r1_0528_qwen3_8b | phi_frac_en_208_bad_209_valid | zh | bad_B | B | B | 3.125 | nonsense_spill_after_correct_fraction_start |
| phi4_mini_reasoning | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_A | A | B | -2.375 | acpi_unmarked_wrong_derivative_rule |
| phi4_mini_reasoning | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_B | B | A | -1.084 | acpi_unmarked_wrong_derivative_rule |
| phi4_mini_reasoning | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_A | A | A | 1.783 | acpi_unmarked_wrong_derivative_rule |
| phi4_mini_reasoning | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_B | B | A | -2.408 | acpi_unmarked_wrong_derivative_rule |
| phi4_mini_reasoning | qwen14_disc75_en_zh_358_bad_359_valid | en | bad_A | A | B | -5.392 | semantic_drift_75off_to_qiwuzhe_final_wrong |
| phi4_mini_reasoning | qwen14_disc75_en_zh_358_bad_359_valid | en | bad_B | B | B | 1.117 | semantic_drift_75off_to_qiwuzhe_final_wrong |
| phi4_mini_reasoning | qwen14_disc75_en_zh_358_bad_359_valid | zh | bad_A | A | B | -3.739 | semantic_drift_75off_to_qiwuzhe_final_wrong |
| phi4_mini_reasoning | qwen14_disc75_en_zh_358_bad_359_valid | zh | bad_B | B | A | -1.185 | semantic_drift_75off_to_qiwuzhe_final_wrong |
| phi4_mini_reasoning | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_A | A | A | 0.563 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| phi4_mini_reasoning | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_B | B | B | 0.375 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| phi4_mini_reasoning | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_A | A | A | 1.027 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| phi4_mini_reasoning | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_B | B | A | -1.938 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| phi4_mini_reasoning | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | en | bad_A | A | B | -8.570 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong |
| phi4_mini_reasoning | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | en | bad_B | B | B | 2.125 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong |
| phi4_mini_reasoning | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | zh | bad_A | A | B | -3.870 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong |
| phi4_mini_reasoning | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | zh | bad_B | B | A | -2.312 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong |
| phi4_mini_reasoning | qwen35_discount_zh_234_bad_235_valid | en | bad_A | A | A | 0.111 | acpi_unmarked_discount_word_mismatch |
| phi4_mini_reasoning | qwen35_discount_zh_234_bad_235_valid | en | bad_B | B | B | 0.270 | acpi_unmarked_discount_word_mismatch |
| phi4_mini_reasoning | qwen35_discount_zh_234_bad_235_valid | zh | bad_A | A | A | 1.246 | acpi_unmarked_discount_word_mismatch |
| phi4_mini_reasoning | qwen35_discount_zh_234_bad_235_valid | zh | bad_B | B | A | -3.312 | acpi_unmarked_discount_word_mismatch |
| phi4_mini_reasoning | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_A | A | A | 2.456 | acpi_self_corrected_arithmetic_step |
| phi4_mini_reasoning | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_B | B | B | 3.762 | acpi_self_corrected_arithmetic_step |
| phi4_mini_reasoning | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_A | A | A | 2.099 | acpi_self_corrected_arithmetic_step |
| phi4_mini_reasoning | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_B | B | B | 6.670 | acpi_self_corrected_arithmetic_step |
| phi4_mini_reasoning | qwen35_qiwuzhe_zh_en_229_bad_225_valid | en | bad_A | A | B | -3.885 | semantic_drift_qiwuzhe_to_75off_final_wrong |
| phi4_mini_reasoning | qwen35_qiwuzhe_zh_en_229_bad_225_valid | en | bad_B | B | B | 4.467 | semantic_drift_qiwuzhe_to_75off_final_wrong |
| phi4_mini_reasoning | qwen35_qiwuzhe_zh_en_229_bad_225_valid | zh | bad_A | A | B | -1.445 | semantic_drift_qiwuzhe_to_75off_final_wrong |
| phi4_mini_reasoning | qwen35_qiwuzhe_zh_en_229_bad_225_valid | zh | bad_B | B | A | -1.504 | semantic_drift_qiwuzhe_to_75off_final_wrong |
| phi4_mini_reasoning | qwen35_product_en_296_bad_297_valid | en | bad_A | A | B | -5.367 | wrong_derivative_and_after_final_template |
| phi4_mini_reasoning | qwen35_product_en_296_bad_297_valid | en | bad_B | B | B | 4.626 | wrong_derivative_and_after_final_template |
| phi4_mini_reasoning | qwen35_product_en_296_bad_297_valid | zh | bad_A | A | A | 2.206 | wrong_derivative_and_after_final_template |
| phi4_mini_reasoning | qwen35_product_en_296_bad_297_valid | zh | bad_B | B | B | 3.913 | wrong_derivative_and_after_final_template |
| phi4_mini_reasoning | phi_deriv_zh_178_bad_182_valid | en | bad_A | A | B | -4.007 | acpi_truncated_wrong_derivative_rule |
| phi4_mini_reasoning | phi_deriv_zh_178_bad_182_valid | en | bad_B | B | B | 2.375 | acpi_truncated_wrong_derivative_rule |
| phi4_mini_reasoning | phi_deriv_zh_178_bad_182_valid | zh | bad_A | A | A | 0.000 | acpi_truncated_wrong_derivative_rule |
| phi4_mini_reasoning | phi_deriv_zh_178_bad_182_valid | zh | bad_B | B | B | 0.375 | acpi_truncated_wrong_derivative_rule |
| phi4_mini_reasoning | phi_deriv_en_zh_183_bad_182_valid | en | bad_A | A | B | -1.625 | late_confusion_constant_vs_linear_derivative_truncated |
| phi4_mini_reasoning | phi_deriv_en_zh_183_bad_182_valid | en | bad_B | B | B | 3.636 | late_confusion_constant_vs_linear_derivative_truncated |
| phi4_mini_reasoning | phi_deriv_en_zh_183_bad_182_valid | zh | bad_A | A | A | 0.625 | late_confusion_constant_vs_linear_derivative_truncated |
| phi4_mini_reasoning | phi_deriv_en_zh_183_bad_182_valid | zh | bad_B | B | B | 1.000 | late_confusion_constant_vs_linear_derivative_truncated |
| phi4_mini_reasoning | phi_frac_en_208_bad_209_valid | en | bad_A | A | B | -5.500 | nonsense_spill_after_correct_fraction_start |
| phi4_mini_reasoning | phi_frac_en_208_bad_209_valid | en | bad_B | B | B | 3.305 | nonsense_spill_after_correct_fraction_start |
| phi4_mini_reasoning | phi_frac_en_208_bad_209_valid | zh | bad_A | A | A | 1.750 | nonsense_spill_after_correct_fraction_start |
| phi4_mini_reasoning | phi_frac_en_208_bad_209_valid | zh | bad_B | B | A | -0.326 | nonsense_spill_after_correct_fraction_start |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_A | A | A | 0.250 | acpi_unmarked_wrong_derivative_rule |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_B | B | B | 2.750 | acpi_unmarked_wrong_derivative_rule |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_A | A | A | 0.000 | acpi_unmarked_wrong_derivative_rule |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_B | B | B | 1.500 | acpi_unmarked_wrong_derivative_rule |
| qwen35_9b | qwen14_disc75_en_zh_358_bad_359_valid | en | bad_A | A | B | -1.625 | semantic_drift_75off_to_qiwuzhe_final_wrong |
| qwen35_9b | qwen14_disc75_en_zh_358_bad_359_valid | en | bad_B | B | B | 2.500 | semantic_drift_75off_to_qiwuzhe_final_wrong |
| qwen35_9b | qwen14_disc75_en_zh_358_bad_359_valid | zh | bad_A | A | B | -0.375 | semantic_drift_75off_to_qiwuzhe_final_wrong |
| qwen35_9b | qwen14_disc75_en_zh_358_bad_359_valid | zh | bad_B | B | B | 1.250 | semantic_drift_75off_to_qiwuzhe_final_wrong |
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_A | A | B | -0.500 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_B | B | B | 1.125 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_A | A | B | -0.125 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_B | B | B | 0.625 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen35_9b | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | en | bad_A | A | B | -0.625 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong |
| qwen35_9b | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | en | bad_B | B | B | 2.000 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong |
| qwen35_9b | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | zh | bad_A | A | B | -0.125 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong |
| qwen35_9b | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | zh | bad_B | B | B | 1.375 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | en | bad_A | A | A | 0.250 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | en | bad_B | B | B | 1.375 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | zh | bad_A | A | A | 0.375 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | zh | bad_B | B | B | 1.000 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_A | A | A | 2.251 | acpi_self_corrected_arithmetic_step |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_B | B | B | 1.406 | acpi_self_corrected_arithmetic_step |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_A | A | A | 2.750 | acpi_self_corrected_arithmetic_step |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_B | B | B | 1.750 | acpi_self_corrected_arithmetic_step |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | en | bad_A | A | B | -1.875 | semantic_drift_qiwuzhe_to_75off_final_wrong |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | en | bad_B | B | B | 1.750 | semantic_drift_qiwuzhe_to_75off_final_wrong |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | zh | bad_A | A | B | -1.500 | semantic_drift_qiwuzhe_to_75off_final_wrong |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | zh | bad_B | B | B | 1.250 | semantic_drift_qiwuzhe_to_75off_final_wrong |
| qwen35_9b | qwen35_product_en_296_bad_297_valid | en | bad_A | A | A | 0.250 | wrong_derivative_and_after_final_template |
| qwen35_9b | qwen35_product_en_296_bad_297_valid | en | bad_B | B | B | 0.031 | wrong_derivative_and_after_final_template |
| qwen35_9b | qwen35_product_en_296_bad_297_valid | zh | bad_A | A | A | 0.500 | wrong_derivative_and_after_final_template |
| qwen35_9b | qwen35_product_en_296_bad_297_valid | zh | bad_B | B | B | 0.014 | wrong_derivative_and_after_final_template |
| qwen35_9b | phi_deriv_zh_178_bad_182_valid | en | bad_A | A | B | -0.750 | acpi_truncated_wrong_derivative_rule |
| qwen35_9b | phi_deriv_zh_178_bad_182_valid | en | bad_B | B | B | 0.875 | acpi_truncated_wrong_derivative_rule |
| qwen35_9b | phi_deriv_zh_178_bad_182_valid | zh | bad_A | A | B | -1.250 | acpi_truncated_wrong_derivative_rule |
| qwen35_9b | phi_deriv_zh_178_bad_182_valid | zh | bad_B | B | B | 1.125 | acpi_truncated_wrong_derivative_rule |
| qwen35_9b | phi_deriv_en_zh_183_bad_182_valid | en | bad_A | A | A | 0.250 | late_confusion_constant_vs_linear_derivative_truncated |
| qwen35_9b | phi_deriv_en_zh_183_bad_182_valid | en | bad_B | B | B | 2.000 | late_confusion_constant_vs_linear_derivative_truncated |
| qwen35_9b | phi_deriv_en_zh_183_bad_182_valid | zh | bad_A | A | B | -0.375 | late_confusion_constant_vs_linear_derivative_truncated |
| qwen35_9b | phi_deriv_en_zh_183_bad_182_valid | zh | bad_B | B | B | 1.375 | late_confusion_constant_vs_linear_derivative_truncated |
| qwen35_9b | phi_frac_en_208_bad_209_valid | en | bad_A | A | A | 0.500 | nonsense_spill_after_correct_fraction_start |
| qwen35_9b | phi_frac_en_208_bad_209_valid | en | bad_B | B | B | 2.375 | nonsense_spill_after_correct_fraction_start |
| qwen35_9b | phi_frac_en_208_bad_209_valid | zh | bad_A | A | A | 0.125 | nonsense_spill_after_correct_fraction_start |
| qwen35_9b | phi_frac_en_208_bad_209_valid | zh | bad_B | B | B | 2.125 | nonsense_spill_after_correct_fraction_start |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_A | A | B | -0.250 | acpi_unmarked_wrong_derivative_rule |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_B | B | B | 0.625 | acpi_unmarked_wrong_derivative_rule |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_A | A | B | -0.750 | acpi_unmarked_wrong_derivative_rule |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_B | B | B | 1.375 | acpi_unmarked_wrong_derivative_rule |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | en | bad_A | A | B | -1.500 | semantic_drift_75off_to_qiwuzhe_final_wrong |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | en | bad_B | B | B | 1.625 | semantic_drift_75off_to_qiwuzhe_final_wrong |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | zh | bad_A | A | B | -1.375 | semantic_drift_75off_to_qiwuzhe_final_wrong |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | zh | bad_B | B | B | 1.875 | semantic_drift_75off_to_qiwuzhe_final_wrong |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_A | A | B | -0.125 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_B | B | B | 0.875 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_A | A | A | 1.125 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_B | B | B | 0.750 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen3_14b_base | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | en | bad_A | A | A | 0.125 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong |
| qwen3_14b_base | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | en | bad_B | B | B | 1.000 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong |
| qwen3_14b_base | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | zh | bad_A | A | A | 0.750 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong |
| qwen3_14b_base | qwen14_dabazhe_wrong_zh_en_444_bad_440_valid | zh | bad_B | B | B | 0.500 | semantic_drift_dabazhe_as_80_percent_discount_final_wrong |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | en | bad_A | A | A | 3.242 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | en | bad_B | B | B | 1.125 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | zh | bad_A | A | A | 3.708 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | zh | bad_B | B | B | 1.875 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_A | A | A | 2.125 | acpi_self_corrected_arithmetic_step |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_B | B | B | 1.500 | acpi_self_corrected_arithmetic_step |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_A | A | A | 2.000 | acpi_self_corrected_arithmetic_step |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_B | B | B | 1.625 | acpi_self_corrected_arithmetic_step |
| qwen3_14b_base | qwen35_qiwuzhe_zh_en_229_bad_225_valid | en | bad_A | A | A | 2.125 | semantic_drift_qiwuzhe_to_75off_final_wrong |
| qwen3_14b_base | qwen35_qiwuzhe_zh_en_229_bad_225_valid | en | bad_B | B | B | 2.250 | semantic_drift_qiwuzhe_to_75off_final_wrong |
| qwen3_14b_base | qwen35_qiwuzhe_zh_en_229_bad_225_valid | zh | bad_A | A | A | 2.250 | semantic_drift_qiwuzhe_to_75off_final_wrong |
| qwen3_14b_base | qwen35_qiwuzhe_zh_en_229_bad_225_valid | zh | bad_B | B | B | 2.750 | semantic_drift_qiwuzhe_to_75off_final_wrong |
| qwen3_14b_base | qwen35_product_en_296_bad_297_valid | en | bad_A | A | A | 1.875 | wrong_derivative_and_after_final_template |
| qwen3_14b_base | qwen35_product_en_296_bad_297_valid | en | bad_B | B | B | 2.370 | wrong_derivative_and_after_final_template |
| qwen3_14b_base | qwen35_product_en_296_bad_297_valid | zh | bad_A | A | A | 2.125 | wrong_derivative_and_after_final_template |
| qwen3_14b_base | qwen35_product_en_296_bad_297_valid | zh | bad_B | B | B | 2.750 | wrong_derivative_and_after_final_template |
| qwen3_14b_base | phi_deriv_zh_178_bad_182_valid | en | bad_A | A | B | -0.625 | acpi_truncated_wrong_derivative_rule |
| qwen3_14b_base | phi_deriv_zh_178_bad_182_valid | en | bad_B | B | B | 0.250 | acpi_truncated_wrong_derivative_rule |
| qwen3_14b_base | phi_deriv_zh_178_bad_182_valid | zh | bad_A | A | B | -0.250 | acpi_truncated_wrong_derivative_rule |
| qwen3_14b_base | phi_deriv_zh_178_bad_182_valid | zh | bad_B | B | B | 0.125 | acpi_truncated_wrong_derivative_rule |
| qwen3_14b_base | phi_deriv_en_zh_183_bad_182_valid | en | bad_A | A | A | 1.375 | late_confusion_constant_vs_linear_derivative_truncated |
| qwen3_14b_base | phi_deriv_en_zh_183_bad_182_valid | en | bad_B | B | B | 0.375 | late_confusion_constant_vs_linear_derivative_truncated |
| qwen3_14b_base | phi_deriv_en_zh_183_bad_182_valid | zh | bad_A | A | A | 1.125 | late_confusion_constant_vs_linear_derivative_truncated |
| qwen3_14b_base | phi_deriv_en_zh_183_bad_182_valid | zh | bad_B | B | A | -0.125 | late_confusion_constant_vs_linear_derivative_truncated |
| qwen3_14b_base | phi_frac_en_208_bad_209_valid | en | bad_A | A | A | 1.832 | nonsense_spill_after_correct_fraction_start |
| qwen3_14b_base | phi_frac_en_208_bad_209_valid | en | bad_B | B | B | 2.199 | nonsense_spill_after_correct_fraction_start |
| qwen3_14b_base | phi_frac_en_208_bad_209_valid | zh | bad_A | A | A | 2.593 | nonsense_spill_after_correct_fraction_start |
| qwen3_14b_base | phi_frac_en_208_bad_209_valid | zh | bad_B | B | B | 1.375 | nonsense_spill_after_correct_fraction_start |
