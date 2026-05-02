# E25 Layerwise Verifier Lens Summary / E25 分层 verifier logit-lens 汇总

Created / 创建时间: 2026-04-27T13:10:05

The probe projects each hidden state at the verifier decision token through the final LM head. / 本 probe 将 verifier 决策位置的每层 hidden state 通过最终 LM head 投影。
It is a diagnostic lens, not a trained tuned-lens or a complete circuit proof. / 它是诊断性 lens，不是训练过的 tuned-lens，也不是完整 circuit 证明。

## Absolute Yes/No Lens / 绝对 Yes/No lens

| verifier | slice | n | final positive rate | middle positive rate | mean middle->final drop | note |
|---|---|---:|---:|---:|---:|---|
| qwen35_9b | ACPI | 10 | 0.800 | 0.500 | 5.096 | ACPI over-accept risk |
| qwen35_9b | non-ACPI | 18 | 1.000 | 0.500 | 3.579 |  |
| qwen3_14b_base | ACPI | 10 | 0.500 | 1.000 | 8.521 |  |
| qwen3_14b_base | non-ACPI | 18 | 0.500 | 1.000 | 8.551 |  |

### Absolute Rows / 绝对式逐行

| verifier | idx | risk | prompt | target valid | final margin | middle best | middle layer | tag |
|---|---:|---|---|---:|---:|---:|---:|---|
| qwen35_9b | 234 | acpi_unmarked_discount_word_mismatch | en | False | 1.125 | 11.742 | 22 | output/head re-entanglement candidate |
| qwen35_9b | 234 | acpi_unmarked_discount_word_mismatch | zh | False | -0.500 | 0.000 | 8 | no positive lens signal |
| qwen35_9b | 235 | valid_correct_but_raw_or_visible_spill | en | True | 4.750 | 14.148 | 23 | stable positive |
| qwen35_9b | 235 | valid_correct_but_raw_or_visible_spill | zh | True | 2.312 | 0.000 | 8 | late-only positive |
| qwen35_9b | 260 | valid_clean | en | True | 4.750 | 14.672 | 23 | stable positive |
| qwen35_9b | 260 | valid_clean | zh | True | 2.500 | 0.000 | 8 | late-only positive |
| qwen35_9b | 261 | acpi_self_corrected_arithmetic_step | en | False | 1.125 | 16.688 | 23 | output/head re-entanglement candidate |
| qwen35_9b | 261 | acpi_self_corrected_arithmetic_step | zh | False | -1.500 | 0.000 | 8 | no positive lens signal |
| qwen35_9b | 402 | acpi_unmarked_wrong_derivative_rule | en | False | 2.125 | 10.805 | 22 | output/head re-entanglement candidate |
| qwen35_9b | 402 | acpi_unmarked_wrong_derivative_rule | zh | False | 0.625 | 0.000 | 8 | output/head re-entanglement candidate |
| qwen35_9b | 403 | valid_clean | en | True | 4.500 | 12.953 | 23 | stable positive |
| qwen35_9b | 403 | valid_clean | zh | True | 2.500 | 0.000 | 8 | late-only positive |
| qwen35_9b | 442 | valid_clean | en | True | 3.375 | 11.273 | 22 | stable positive |
| qwen35_9b | 442 | valid_clean | zh | True | 2.125 | 0.000 | 8 | late-only positive |
| qwen35_9b | 445 | acpi_lexical_mismatch_dabazhe_80_percent_discount | en | False | 3.000 | 12.289 | 22 | output/head re-entanglement candidate |
| qwen35_9b | 445 | acpi_lexical_mismatch_dabazhe_80_percent_discount | zh | False | 0.750 | 0.000 | 8 | output/head re-entanglement candidate |
| qwen35_9b | 180091 | valid_clean_same_route_sibling | en | True | 4.000 | 13.844 | 23 | stable positive |
| qwen35_9b | 180091 | valid_clean_same_route_sibling | zh | True | 2.125 | 0.000 | 8 | late-only positive |
| qwen35_9b | 180092 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch | en | False | 3.625 | 11.938 | 23 | output/head re-entanglement candidate |
| qwen35_9b | 180092 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch | zh | False | 2.125 | 0.000 | 8 | output/head re-entanglement candidate |
| qwen35_9b | 180093 | semantic_drift_80pct_discount_final_wrong | en | False | 3.500 | 12.781 | 23 | output/head re-entanglement candidate |
| qwen35_9b | 180093 | semantic_drift_80pct_discount_final_wrong | zh | False | 2.000 | 0.000 | 8 | output/head re-entanglement candidate |
| qwen35_9b | 180094 | valid_clean_same_route_sibling | en | True | 4.250 | 14.336 | 23 | stable positive |
| qwen35_9b | 180094 | valid_clean_same_route_sibling | zh | True | 2.125 | 0.000 | 8 | late-only positive |
| qwen35_9b | 181000 | valid_clean_same_route_discount | en | True | 4.500 | 14.391 | 23 | stable positive |
| qwen35_9b | 181000 | valid_clean_same_route_discount | zh | True | 2.188 | 0.000 | 8 | late-only positive |
| qwen35_9b | 181001 | valid_clean_same_route_discount | en | True | 5.250 | 15.203 | 23 | stable positive |
| qwen35_9b | 181001 | valid_clean_same_route_discount | zh | True | 2.438 | 0.000 | 8 | late-only positive |
| qwen3_14b_base | 234 | acpi_unmarked_discount_word_mismatch | en | False | 10.000 | 14.594 | 29 | output/head re-entanglement candidate |
| qwen3_14b_base | 234 | acpi_unmarked_discount_word_mismatch | zh | False | -7.000 | 3.719 | 10 | mid-signal lost before output |
| qwen3_14b_base | 235 | valid_correct_but_raw_or_visible_spill | en | True | 12.625 | 19.219 | 29 | stable positive |
| qwen3_14b_base | 235 | valid_correct_but_raw_or_visible_spill | zh | True | -5.875 | 4.562 | 10 | mid-signal lost before output |
| qwen3_14b_base | 260 | valid_clean | en | True | 12.000 | 18.094 | 29 | stable positive |
| qwen3_14b_base | 260 | valid_clean | zh | True | -6.625 | 4.828 | 10 | mid-signal lost before output |
| qwen3_14b_base | 261 | acpi_self_corrected_arithmetic_step | en | False | 11.562 | 21.656 | 29 | output/head re-entanglement candidate |
| qwen3_14b_base | 261 | acpi_self_corrected_arithmetic_step | zh | False | -6.125 | 4.297 | 10 | mid-signal lost before output |
| qwen3_14b_base | 402 | acpi_unmarked_wrong_derivative_rule | en | False | 11.875 | 18.219 | 29 | output/head re-entanglement candidate |
| qwen3_14b_base | 402 | acpi_unmarked_wrong_derivative_rule | zh | False | -6.250 | 4.081 | 11 | mid-signal lost before output |
| qwen3_14b_base | 403 | valid_clean | en | True | 12.250 | 18.469 | 29 | stable positive |
| qwen3_14b_base | 403 | valid_clean | zh | True | -5.750 | 4.492 | 10 | mid-signal lost before output |
| qwen3_14b_base | 442 | valid_clean | en | True | 12.000 | 18.531 | 29 | stable positive |
| qwen3_14b_base | 442 | valid_clean | zh | True | -6.000 | 4.109 | 10 | mid-signal lost before output |
| qwen3_14b_base | 445 | acpi_lexical_mismatch_dabazhe_80_percent_discount | en | False | 12.375 | 18.656 | 29 | output/head re-entanglement candidate |
| qwen3_14b_base | 445 | acpi_lexical_mismatch_dabazhe_80_percent_discount | zh | False | -6.625 | 3.477 | 10 | mid-signal lost before output |
| qwen3_14b_base | 180091 | valid_clean_same_route_sibling | en | True | 10.875 | 16.406 | 29 | stable positive |
| qwen3_14b_base | 180091 | valid_clean_same_route_sibling | zh | True | -6.875 | 3.641 | 10 | mid-signal lost before output |
| qwen3_14b_base | 180092 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch | en | False | 11.500 | 17.500 | 29 | output/head re-entanglement candidate |
| qwen3_14b_base | 180092 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch | zh | False | -6.625 | 3.703 | 10 | mid-signal lost before output |
| qwen3_14b_base | 180093 | semantic_drift_80pct_discount_final_wrong | en | False | 11.500 | 18.750 | 29 | output/head re-entanglement candidate |
| qwen3_14b_base | 180093 | semantic_drift_80pct_discount_final_wrong | zh | False | -6.750 | 4.281 | 10 | mid-signal lost before output |
| qwen3_14b_base | 180094 | valid_clean_same_route_sibling | en | True | 11.000 | 17.219 | 29 | stable positive |
| qwen3_14b_base | 180094 | valid_clean_same_route_sibling | zh | True | -7.000 | 3.617 | 10 | mid-signal lost before output |
| qwen3_14b_base | 181000 | valid_clean_same_route_discount | en | True | 12.750 | 19.469 | 29 | stable positive |
| qwen3_14b_base | 181000 | valid_clean_same_route_discount | zh | True | -6.250 | 5.008 | 10 | mid-signal lost before output |
| qwen3_14b_base | 181001 | valid_clean_same_route_discount | en | True | 12.500 | 18.625 | 29 | stable positive |
| qwen3_14b_base | 181001 | valid_clean_same_route_discount | zh | True | -5.750 | 5.219 | 10 | mid-signal lost before output |

## Contrastive A/B Lens / 对比式 A/B lens

| verifier | pair | n | final target-positive rate | middle target-positive rate | mean middle->final drop |
|---|---|---:|---:|---:|---:|
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | 4 | 0.500 | 0.750 | 1.409 |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | 4 | 1.000 | 1.000 | 1.087 |
| qwen35_9b | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | 4 | 0.500 | 0.750 | 1.686 |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | 4 | 0.750 | 0.500 | 1.132 |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | 4 | 0.250 | 0.500 | 1.026 |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | 4 | 1.000 | 1.000 | 1.538 |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | 4 | 1.000 | 1.000 | 1.397 |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | 4 | 1.000 | 1.000 | 1.463 |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | 4 | 1.000 | 1.000 | 0.980 |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | 4 | 0.750 | 1.000 | 1.442 |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | 4 | 0.750 | 1.000 | 1.596 |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | 4 | 0.500 | 1.000 | 1.522 |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | 4 | 0.250 | 1.000 | 1.887 |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | 4 | 0.500 | 1.000 | 1.873 |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | 4 | 1.000 | 1.000 | 1.822 |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181000_valid | 4 | 0.750 | 1.000 | 1.961 |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181001_valid | 4 | 0.750 | 1.000 | 2.539 |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | 4 | 0.750 | 1.000 | 1.435 |

### Contrastive Rows / 对比式逐行

| verifier | pair | prompt | order | final margin | middle best | middle layer | tag |
|---|---|---|---|---:|---:|---:|---|
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_A | -0.625 | 3.199 | 17 | mid-signal lost before output |
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_B | 1.250 | 1.062 | 23 | stable positive |
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_A | 0.000 | 2.500 | 12 | mid-signal lost before output |
| qwen35_9b | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_B | 0.500 | 0.000 | 23 | late-only positive |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_A | 0.125 | 3.582 | 22 | stable positive |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_B | 3.125 | 2.531 | 23 | stable positive |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_A | 0.125 | 2.391 | 12 | stable positive |
| qwen35_9b | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_B | 1.625 | 0.844 | 23 | stable positive |
| qwen35_9b | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | en | bad_A | -1.125 | 3.238 | 17 | mid-signal lost before output |
| qwen35_9b | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | en | bad_B | 1.375 | 1.594 | 23 | stable positive |
| qwen35_9b | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | zh | bad_A | -0.500 | 2.350 | 14 | mid-signal lost before output |
| qwen35_9b | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | zh | bad_B | 0.625 | -0.062 | 23 | late-only positive |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | en | bad_A | 0.125 | 3.828 | 22 | stable positive |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | en | bad_B | 0.250 | -0.688 | 23 | late-only positive |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | zh | bad_A | 0.125 | 2.605 | 22 | stable positive |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | zh | bad_B | 0.000 | -0.719 | 21 | output/head re-entanglement candidate |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | en | bad_A | 0.000 | 3.633 | 22 | mid-signal lost before output |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | en | bad_B | -0.125 | -1.039 | 11 | output/head re-entanglement candidate |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | zh | bad_A | 0.250 | 2.293 | 22 | stable positive |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | zh | bad_B | 0.000 | -0.656 | 19 | output/head re-entanglement candidate |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | en | bad_A | 0.250 | 4.422 | 22 | stable positive |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | en | bad_B | 1.500 | 1.594 | 23 | stable positive |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | zh | bad_A | 0.500 | 2.512 | 22 | stable positive |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | zh | bad_B | 1.000 | 0.875 | 23 | stable positive |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | en | bad_A | 0.125 | 4.477 | 22 | stable positive |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | en | bad_B | 1.000 | 0.438 | 23 | stable positive |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | zh | bad_A | 0.375 | 2.488 | 22 | stable positive |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | zh | bad_B | 0.875 | 0.562 | 23 | stable positive |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | en | bad_A | 0.625 | 4.281 | 22 | stable positive |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | en | bad_B | 1.125 | 0.906 | 23 | stable positive |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | zh | bad_A | 0.375 | 2.760 | 16 | stable positive |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | zh | bad_B | 0.500 | 0.531 | 23 | stable positive |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_A | 2.875 | 5.859 | 23 | stable positive |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_B | 2.750 | 2.406 | 23 | stable positive |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_A | 3.375 | 4.469 | 23 | stable positive |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_B | 1.875 | 2.062 | 23 | stable positive |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_A | -1.781 | 1.664 | 27 | mid-signal lost before output |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_B | 2.219 | 1.684 | 10 | stable positive |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_A | 0.812 | 1.265 | 14 | stable positive |
| qwen3_14b_base | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_B | 0.250 | 2.656 | 29 | stable positive |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_A | -1.781 | 2.070 | 27 | mid-signal lost before output |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_B | 2.031 | 1.898 | 22 | stable positive |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_A | 0.125 | 1.445 | 27 | stable positive |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_B | 0.188 | 1.531 | 20 | stable positive |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | en | bad_A | -1.938 | 1.234 | 27 | mid-signal lost before output |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | en | bad_B | 2.094 | 1.602 | 22 | stable positive |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | zh | bad_A | 0.000 | 1.332 | 14 | mid-signal lost before output |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | zh | bad_B | 0.062 | 2.141 | 28 | stable positive |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | en | bad_A | -2.188 | 1.109 | 27 | mid-signal lost before output |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | en | bad_B | 1.281 | 1.910 | 13 | stable positive |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | zh | bad_A | -0.688 | 0.962 | 14 | mid-signal lost before output |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | zh | bad_B | -0.688 | 1.285 | 20 | mid-signal lost before output |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | en | bad_A | -1.688 | 1.891 | 27 | mid-signal lost before output |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | en | bad_B | 1.188 | 1.818 | 13 | stable positive |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | zh | bad_A | 0.125 | 1.223 | 14 | stable positive |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | zh | bad_B | -1.000 | 1.184 | 10 | mid-signal lost before output |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | en | bad_A | 0.094 | 4.750 | 29 | stable positive |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | en | bad_B | 2.375 | 1.633 | 10 | stable positive |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | zh | bad_A | 2.438 | 3.656 | 29 | stable positive |
| qwen3_14b_base | qwen35_discount_zh_234_bad_235_valid | zh | bad_B | 0.875 | 3.031 | 29 | stable positive |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181000_valid | en | bad_A | -0.625 | 3.656 | 29 | mid-signal lost before output |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181000_valid | en | bad_B | 2.625 | 2.500 | 29 | stable positive |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181000_valid | zh | bad_A | 2.375 | 3.812 | 29 | stable positive |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181000_valid | zh | bad_B | 0.500 | 2.750 | 29 | stable positive |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181001_valid | en | bad_A | -0.531 | 4.531 | 29 | mid-signal lost before output |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181001_valid | en | bad_B | 2.844 | 3.625 | 29 | stable positive |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181001_valid | zh | bad_A | 1.750 | 2.969 | 29 | stable positive |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181001_valid | zh | bad_B | 1.000 | 4.094 | 29 | stable positive |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_A | -0.406 | 3.938 | 29 | mid-signal lost before output |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | en | bad_B | 2.703 | 1.785 | 13 | stable positive |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_A | 1.375 | 2.078 | 29 | stable positive |
| qwen3_14b_base | qwen35_ratio_zh_en_261_bad_260_valid | zh | bad_B | 0.812 | 2.424 | 26 | stable positive |