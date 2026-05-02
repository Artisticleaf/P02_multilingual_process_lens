# E15 Verifier Chain Disagreement Summary

This joins E06 absolute Yes/No process verification with E12 pairwise contrastive verification on the same bad traces.

## Summary

| slice type | slice | n | contrastive acc | contrastive margin | abs bad false-accept | abs bad margin |
|---|---|---:|---:|---:|---:|---:|
| all | all | 64 | 0.703 | 0.795 | 0.938 | 2.930 |
| pair | qwen14_dabazhe_zh_en_445_bad_442_valid | 16 | 0.562 | 0.205 | 1.000 | 3.266 |
| pair | qwen14_deriv_sum_zh_402_bad_403_valid | 16 | 0.562 | 0.128 | 1.000 | 4.109 |
| pair | qwen35_discount_zh_234_bad_235_valid | 16 | 0.812 | 0.649 | 0.750 | 1.031 |
| pair | qwen35_ratio_zh_en_261_bad_260_valid | 16 | 0.875 | 2.199 | 1.000 | 3.313 |
| verifier | deepseek_r1_0528_qwen3_8b | 16 | 0.438 | 0.252 | 1.000 | 3.141 |
| verifier | phi4_mini_reasoning | 16 | 0.688 | 0.578 | 1.000 | 6.305 |
| verifier | qwen35_9b | 16 | 0.875 | 1.049 | 1.000 | 1.023 |
| verifier | qwen3_14b_base | 16 | 0.812 | 1.302 | 0.750 | 1.250 |

## Key Joined Rows

| verifier | pair | prompt | order | target | pred | contrast margin | abs false prompts | abs mean margin | risk |
|---|---|---|---|---|---|---:|---:|---:|---|
| deepseek_r1_0528_qwen3_8b | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_A | A | B | -0.125 | 2 | 3.938 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| deepseek_r1_0528_qwen3_8b | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_B | B | A | -0.125 | 2 | 3.938 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| deepseek_r1_0528_qwen3_8b | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_A | A | B | -1.250 | 2 | 3.938 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| deepseek_r1_0528_qwen3_8b | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_B | B | B | 1.000 | 2 | 3.938 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| deepseek_r1_0528_qwen3_8b | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_A | A | A | 0.375 | 2 | 5.188 | acpi_unmarked_wrong_derivative_rule |
| deepseek_r1_0528_qwen3_8b | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_B | B | A | -0.250 | 2 | 5.188 | acpi_unmarked_wrong_derivative_rule |
| deepseek_r1_0528_qwen3_8b | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_A | A | B | -0.500 | 2 | 5.188 | acpi_unmarked_wrong_derivative_rule |
| deepseek_r1_0528_qwen3_8b | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_B | B | B | 1.000 | 2 | 5.188 | acpi_unmarked_wrong_derivative_rule |
| deepseek_r1_0528_qwen3_8b | qwen35_discount_zh_234_bad_235_valid | en | bad_A | A | A | 0.125 | 2 | 1.250 | acpi_unmarked_discount_word_mismatch |
| deepseek_r1_0528_qwen3_8b | qwen35_discount_zh_234_bad_235_valid | en | bad_B | B | A | -0.875 | 2 | 1.250 | acpi_unmarked_discount_word_mismatch |
| deepseek_r1_0528_qwen3_8b | qwen35_discount_zh_234_bad_235_valid | zh | bad_A | A | B | -0.750 | 2 | 1.250 | acpi_unmarked_discount_word_mismatch |
| deepseek_r1_0528_qwen3_8b | qwen35_discount_zh_234_bad_235_valid | zh | bad_B | B | B | 0.625 | 2 | 1.250 | acpi_unmarked_discount_word_mismatch |
| deepseek_r1_0528_qwen3_8b | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_A | A | B | -0.375 | 2 | 2.188 | acpi_self_corrected_arithmetic_step |
| deepseek_r1_0528_qwen3_8b | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_B | B | B | 2.610 | 2 | 2.188 | acpi_self_corrected_arithmetic_step |
| deepseek_r1_0528_qwen3_8b | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_A | A | B | -0.750 | 2 | 2.188 | acpi_self_corrected_arithmetic_step |
| deepseek_r1_0528_qwen3_8b | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_B | B | B | 3.305 | 2 | 2.188 | acpi_self_corrected_arithmetic_step |
| phi4_mini_reasoning | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_A | A | A | 0.563 | 2 | 5.250 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| phi4_mini_reasoning | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_B | B | B | 0.375 | 2 | 5.250 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| phi4_mini_reasoning | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_A | A | A | 1.027 | 2 | 5.250 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| phi4_mini_reasoning | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_B | B | A | -1.938 | 2 | 5.250 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| phi4_mini_reasoning | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_A | A | B | -2.375 | 2 | 7.781 | acpi_unmarked_wrong_derivative_rule |
| phi4_mini_reasoning | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_B | B | A | -1.084 | 2 | 7.781 | acpi_unmarked_wrong_derivative_rule |
| phi4_mini_reasoning | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_A | A | A | 1.783 | 2 | 7.781 | acpi_unmarked_wrong_derivative_rule |
| phi4_mini_reasoning | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_B | B | A | -2.408 | 2 | 7.781 | acpi_unmarked_wrong_derivative_rule |
| phi4_mini_reasoning | qwen35_discount_zh_234_bad_235_valid | en | bad_A | A | A | 0.111 | 2 | 2.875 | acpi_unmarked_discount_word_mismatch |
| phi4_mini_reasoning | qwen35_discount_zh_234_bad_235_valid | en | bad_B | B | B | 0.270 | 2 | 2.875 | acpi_unmarked_discount_word_mismatch |
| phi4_mini_reasoning | qwen35_discount_zh_234_bad_235_valid | zh | bad_A | A | A | 1.246 | 2 | 2.875 | acpi_unmarked_discount_word_mismatch |
| phi4_mini_reasoning | qwen35_discount_zh_234_bad_235_valid | zh | bad_B | B | A | -3.312 | 2 | 2.875 | acpi_unmarked_discount_word_mismatch |
| phi4_mini_reasoning | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_A | A | A | 2.456 | 2 | 9.312 | acpi_self_corrected_arithmetic_step |
| phi4_mini_reasoning | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_B | B | B | 3.762 | 2 | 9.312 | acpi_self_corrected_arithmetic_step |
| phi4_mini_reasoning | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_A | A | A | 2.099 | 2 | 9.312 | acpi_self_corrected_arithmetic_step |
| phi4_mini_reasoning | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_B | B | B | 6.670 | 2 | 9.312 | acpi_self_corrected_arithmetic_step |
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_A | A | B | -0.500 | 2 | 1.937 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_B | B | B | 1.125 | 2 | 1.937 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_A | A | B | -0.125 | 2 | 1.937 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_B | B | B | 0.625 | 2 | 1.937 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_A | A | A | 0.250 | 2 | 1.469 | acpi_unmarked_wrong_derivative_rule |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_B | B | B | 2.750 | 2 | 1.469 | acpi_unmarked_wrong_derivative_rule |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_A | A | A | 0.000 | 2 | 1.469 | acpi_unmarked_wrong_derivative_rule |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_B | B | B | 1.500 | 2 | 1.469 | acpi_unmarked_wrong_derivative_rule |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | en | bad_A | A | A | 0.250 | 2 | 0.500 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | en | bad_B | B | B | 1.375 | 2 | 0.500 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | zh | bad_A | A | A | 0.375 | 2 | 0.500 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | zh | bad_B | B | B | 1.000 | 2 | 0.500 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_A | A | A | 2.251 | 1 | 0.188 | acpi_self_corrected_arithmetic_step |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_B | B | B | 1.406 | 1 | 0.188 | acpi_self_corrected_arithmetic_step |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_A | A | A | 2.750 | 1 | 0.188 | acpi_self_corrected_arithmetic_step |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_B | B | B | 1.750 | 1 | 0.188 | acpi_self_corrected_arithmetic_step |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_A | A | B | -0.125 | 2 | 1.938 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_B | B | B | 0.875 | 2 | 1.938 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_A | A | A | 1.125 | 2 | 1.938 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_B | B | B | 0.750 | 2 | 1.938 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_A | A | B | -0.250 | 2 | 2.000 | acpi_unmarked_wrong_derivative_rule |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_B | B | B | 0.625 | 2 | 2.000 | acpi_unmarked_wrong_derivative_rule |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_A | A | B | -0.750 | 2 | 2.000 | acpi_unmarked_wrong_derivative_rule |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_B | B | B | 1.375 | 2 | 2.000 | acpi_unmarked_wrong_derivative_rule |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | en | bad_A | A | A | 3.242 | 0 | -0.500 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | en | bad_B | B | B | 1.125 | 0 | -0.500 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | zh | bad_A | A | A | 3.708 | 0 | -0.500 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | zh | bad_B | B | B | 1.875 | 0 | -0.500 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_A | A | A | 2.125 | 2 | 1.563 | acpi_self_corrected_arithmetic_step |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_B | B | B | 1.500 | 2 | 1.563 | acpi_self_corrected_arithmetic_step |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_A | A | A | 2.000 | 2 | 1.563 | acpi_self_corrected_arithmetic_step |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_B | B | B | 1.625 | 2 | 1.563 | acpi_self_corrected_arithmetic_step |

## Reading

- A positive contrastive result together with absolute false-accept means the verifier can sometimes see the process difference when forced to compare siblings, but the absolute objective/threshold accepts the bad trace.
- Rows with both contrastive failure and absolute false-accept are the best candidates for mechanistic probing or manual prompt redesign.
- Qwen3.5 absolute E06 may still be running; this report should be regenerated after that file lands.
