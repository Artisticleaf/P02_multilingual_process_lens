# E12 Contrastive ACPI Verifier Summary

The verifier sees a valid and an answer-correct/process-invalid sibling trace and must choose which trace has invalid reasoning. This separates absolute Yes-bias from pairwise error visibility.

## Overall

| verifier | n | acc | mean target margin |
|---|---:|---:|---:|
| deepseek_r1_0528_qwen3_8b | 16 | 0.438 | 0.252 |
| phi4_mini_reasoning | 16 | 0.688 | 0.578 |
| qwen35_9b | 16 | 0.875 | 1.049 |
| qwen3_14b_base | 16 | 0.812 | 1.302 |

## Slices

| verifier | slice type | slice | n | acc | mean target margin |
|---|---|---|---:|---:|---:|
| deepseek_r1_0528_qwen3_8b | pair | qwen14_dabazhe_zh_en_445_bad_442_valid | 4 | 0.250 | -0.125 |
| deepseek_r1_0528_qwen3_8b | pair | qwen14_deriv_sum_zh_402_bad_403_valid | 4 | 0.500 | 0.156 |
| deepseek_r1_0528_qwen3_8b | pair | qwen35_discount_zh_234_bad_235_valid | 4 | 0.500 | -0.219 |
| deepseek_r1_0528_qwen3_8b | pair | qwen35_ratio_zh_en_261_bad_260_valid | 4 | 0.500 | 1.197 |
| deepseek_r1_0528_qwen3_8b | prompt_lang | en | 8 | 0.375 | 0.170 |
| deepseek_r1_0528_qwen3_8b | prompt_lang | zh | 8 | 0.500 | 0.335 |
| deepseek_r1_0528_qwen3_8b | trace_model | qwen35_9b | 8 | 0.500 | 0.489 |
| deepseek_r1_0528_qwen3_8b | trace_model | qwen3_14b_base | 8 | 0.375 | 0.016 |
| phi4_mini_reasoning | pair | qwen14_dabazhe_zh_en_445_bad_442_valid | 4 | 0.750 | 0.007 |
| phi4_mini_reasoning | pair | qwen14_deriv_sum_zh_402_bad_403_valid | 4 | 0.250 | -1.021 |
| phi4_mini_reasoning | pair | qwen35_discount_zh_234_bad_235_valid | 4 | 0.750 | -0.421 |
| phi4_mini_reasoning | pair | qwen35_ratio_zh_en_261_bad_260_valid | 4 | 1.000 | 3.747 |
| phi4_mini_reasoning | prompt_lang | en | 8 | 0.750 | 0.510 |
| phi4_mini_reasoning | prompt_lang | zh | 8 | 0.625 | 0.646 |
| phi4_mini_reasoning | trace_model | qwen35_9b | 8 | 0.875 | 1.663 |
| phi4_mini_reasoning | trace_model | qwen3_14b_base | 8 | 0.500 | -0.507 |
| qwen35_9b | pair | qwen14_dabazhe_zh_en_445_bad_442_valid | 4 | 0.500 | 0.281 |
| qwen35_9b | pair | qwen14_deriv_sum_zh_402_bad_403_valid | 4 | 1.000 | 1.125 |
| qwen35_9b | pair | qwen35_discount_zh_234_bad_235_valid | 4 | 1.000 | 0.750 |
| qwen35_9b | pair | qwen35_ratio_zh_en_261_bad_260_valid | 4 | 1.000 | 2.039 |
| qwen35_9b | prompt_lang | en | 8 | 0.875 | 1.113 |
| qwen35_9b | prompt_lang | zh | 8 | 0.875 | 0.984 |
| qwen35_9b | trace_model | qwen35_9b | 8 | 1.000 | 1.395 |
| qwen35_9b | trace_model | qwen3_14b_base | 8 | 0.750 | 0.703 |
| qwen3_14b_base | pair | qwen14_dabazhe_zh_en_445_bad_442_valid | 4 | 0.750 | 0.656 |
| qwen3_14b_base | pair | qwen14_deriv_sum_zh_402_bad_403_valid | 4 | 0.500 | 0.250 |
| qwen3_14b_base | pair | qwen35_discount_zh_234_bad_235_valid | 4 | 1.000 | 2.488 |
| qwen3_14b_base | pair | qwen35_ratio_zh_en_261_bad_260_valid | 4 | 1.000 | 1.812 |
| qwen3_14b_base | prompt_lang | en | 8 | 0.750 | 1.140 |
| qwen3_14b_base | prompt_lang | zh | 8 | 0.875 | 1.464 |
| qwen3_14b_base | trace_model | qwen35_9b | 8 | 1.000 | 2.150 |
| qwen3_14b_base | trace_model | qwen3_14b_base | 8 | 0.625 | 0.453 |

## Rows

| verifier | pair | prompt | order | target | pred | margin | bad risk |
|---|---|---|---|---|---|---:|---|
| deepseek_r1_0528_qwen3_8b | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_A | A | A | 0.375 | acpi_unmarked_wrong_derivative_rule |
| deepseek_r1_0528_qwen3_8b | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_B | B | A | -0.250 | acpi_unmarked_wrong_derivative_rule |
| deepseek_r1_0528_qwen3_8b | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_A | A | B | -0.500 | acpi_unmarked_wrong_derivative_rule |
| deepseek_r1_0528_qwen3_8b | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_B | B | B | 1.000 | acpi_unmarked_wrong_derivative_rule |
| deepseek_r1_0528_qwen3_8b | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_A | A | B | -0.125 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| deepseek_r1_0528_qwen3_8b | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_B | B | A | -0.125 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| deepseek_r1_0528_qwen3_8b | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_A | A | B | -1.250 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| deepseek_r1_0528_qwen3_8b | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_B | B | B | 1.000 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| deepseek_r1_0528_qwen3_8b | qwen35_discount_zh_234_bad_235_valid | en | bad_A | A | A | 0.125 | acpi_unmarked_discount_word_mismatch |
| deepseek_r1_0528_qwen3_8b | qwen35_discount_zh_234_bad_235_valid | en | bad_B | B | A | -0.875 | acpi_unmarked_discount_word_mismatch |
| deepseek_r1_0528_qwen3_8b | qwen35_discount_zh_234_bad_235_valid | zh | bad_A | A | B | -0.750 | acpi_unmarked_discount_word_mismatch |
| deepseek_r1_0528_qwen3_8b | qwen35_discount_zh_234_bad_235_valid | zh | bad_B | B | B | 0.625 | acpi_unmarked_discount_word_mismatch |
| deepseek_r1_0528_qwen3_8b | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_A | A | B | -0.375 | acpi_self_corrected_arithmetic_step |
| deepseek_r1_0528_qwen3_8b | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_B | B | B | 2.610 | acpi_self_corrected_arithmetic_step |
| deepseek_r1_0528_qwen3_8b | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_A | A | B | -0.750 | acpi_self_corrected_arithmetic_step |
| deepseek_r1_0528_qwen3_8b | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_B | B | B | 3.305 | acpi_self_corrected_arithmetic_step |
| phi4_mini_reasoning | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_A | A | B | -2.375 | acpi_unmarked_wrong_derivative_rule |
| phi4_mini_reasoning | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_B | B | A | -1.084 | acpi_unmarked_wrong_derivative_rule |
| phi4_mini_reasoning | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_A | A | A | 1.783 | acpi_unmarked_wrong_derivative_rule |
| phi4_mini_reasoning | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_B | B | A | -2.408 | acpi_unmarked_wrong_derivative_rule |
| phi4_mini_reasoning | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_A | A | A | 0.563 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| phi4_mini_reasoning | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_B | B | B | 0.375 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| phi4_mini_reasoning | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_A | A | A | 1.027 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| phi4_mini_reasoning | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_B | B | A | -1.938 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| phi4_mini_reasoning | qwen35_discount_zh_234_bad_235_valid | en | bad_A | A | A | 0.111 | acpi_unmarked_discount_word_mismatch |
| phi4_mini_reasoning | qwen35_discount_zh_234_bad_235_valid | en | bad_B | B | B | 0.270 | acpi_unmarked_discount_word_mismatch |
| phi4_mini_reasoning | qwen35_discount_zh_234_bad_235_valid | zh | bad_A | A | A | 1.246 | acpi_unmarked_discount_word_mismatch |
| phi4_mini_reasoning | qwen35_discount_zh_234_bad_235_valid | zh | bad_B | B | A | -3.312 | acpi_unmarked_discount_word_mismatch |
| phi4_mini_reasoning | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_A | A | A | 2.456 | acpi_self_corrected_arithmetic_step |
| phi4_mini_reasoning | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_B | B | B | 3.762 | acpi_self_corrected_arithmetic_step |
| phi4_mini_reasoning | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_A | A | A | 2.099 | acpi_self_corrected_arithmetic_step |
| phi4_mini_reasoning | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_B | B | B | 6.670 | acpi_self_corrected_arithmetic_step |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_A | A | A | 0.250 | acpi_unmarked_wrong_derivative_rule |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_B | B | B | 2.750 | acpi_unmarked_wrong_derivative_rule |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_A | A | A | 0.000 | acpi_unmarked_wrong_derivative_rule |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_B | B | B | 1.500 | acpi_unmarked_wrong_derivative_rule |
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_A | A | B | -0.500 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_B | B | B | 1.125 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_A | A | B | -0.125 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_B | B | B | 0.625 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | en | bad_A | A | A | 0.250 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | en | bad_B | B | B | 1.375 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | zh | bad_A | A | A | 0.375 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | zh | bad_B | B | B | 1.000 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_A | A | A | 2.251 | acpi_self_corrected_arithmetic_step |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_B | B | B | 1.406 | acpi_self_corrected_arithmetic_step |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_A | A | A | 2.750 | acpi_self_corrected_arithmetic_step |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_B | B | B | 1.750 | acpi_self_corrected_arithmetic_step |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_A | A | B | -0.250 | acpi_unmarked_wrong_derivative_rule |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_B | B | B | 0.625 | acpi_unmarked_wrong_derivative_rule |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_A | A | B | -0.750 | acpi_unmarked_wrong_derivative_rule |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_B | B | B | 1.375 | acpi_unmarked_wrong_derivative_rule |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_A | A | B | -0.125 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_B | B | B | 0.875 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_A | A | A | 1.125 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_B | B | B | 0.750 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | en | bad_A | A | A | 3.242 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | en | bad_B | B | B | 1.125 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | zh | bad_A | A | A | 3.708 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | zh | bad_B | B | B | 1.875 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_A | A | A | 2.125 | acpi_self_corrected_arithmetic_step |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_B | B | B | 1.500 | acpi_self_corrected_arithmetic_step |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_A | A | A | 2.000 | acpi_self_corrected_arithmetic_step |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_B | B | B | 1.625 | acpi_self_corrected_arithmetic_step |
