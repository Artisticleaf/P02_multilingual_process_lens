# E27 Transfer Contrastive Verifier Summary / E27 跨模型对比 verifier 汇总

The verifier sees a valid and an answer-correct/process-invalid sibling trace and must choose which trace has invalid reasoning. This separates absolute Yes-bias from pairwise error visibility.

## Overall

| verifier | n | acc | mean target margin |
|---|---:|---:|---:|
| gemma4_e4b_it | 24 | 0.542 | 0.598 |
| qwen35_27b | 24 | 0.875 | 0.976 |

## Slices

| verifier | slice type | slice | n | acc | mean target margin |
|---|---|---|---:|---:|---:|
| gemma4_e4b_it | pair | qwen14_dabazhe_zh_en_445_bad_442_valid | 4 | 0.500 | 0.036 |
| gemma4_e4b_it | pair | qwen14_deriv_sum_zh_402_bad_403_valid | 4 | 0.500 | 0.550 |
| gemma4_e4b_it | pair | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | 4 | 0.750 | 0.796 |
| gemma4_e4b_it | pair | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | 4 | 0.500 | 0.801 |
| gemma4_e4b_it | pair | qwen35_e18_discount_234_bad_181000_valid | 4 | 0.500 | 0.443 |
| gemma4_e4b_it | pair | qwen35_e18_discount_234_bad_181001_valid | 4 | 0.500 | 0.960 |
| gemma4_e4b_it | prompt_lang | en | 12 | 0.500 | 0.473 |
| gemma4_e4b_it | prompt_lang | zh | 12 | 0.583 | 0.722 |
| gemma4_e4b_it | trace_model | qwen35_9b | 8 | 0.500 | 0.701 |
| gemma4_e4b_it | trace_model | qwen3_14b_base | 16 | 0.562 | 0.546 |
| qwen35_27b | pair | qwen14_dabazhe_zh_en_445_bad_442_valid | 4 | 1.000 | 0.812 |
| qwen35_27b | pair | qwen14_deriv_sum_zh_402_bad_403_valid | 4 | 1.000 | 2.734 |
| qwen35_27b | pair | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | 4 | 1.000 | 0.438 |
| qwen35_27b | pair | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | 4 | 0.500 | 0.031 |
| qwen35_27b | pair | qwen35_e18_discount_234_bad_181000_valid | 4 | 0.750 | 0.812 |
| qwen35_27b | pair | qwen35_e18_discount_234_bad_181001_valid | 4 | 1.000 | 1.031 |
| qwen35_27b | prompt_lang | en | 12 | 0.917 | 0.859 |
| qwen35_27b | prompt_lang | zh | 12 | 0.833 | 1.094 |
| qwen35_27b | trace_model | qwen35_9b | 8 | 0.875 | 0.922 |
| qwen35_27b | trace_model | qwen3_14b_base | 16 | 0.875 | 1.004 |

## Rows

| verifier | pair | prompt | order | target | pred | margin | bad risk |
|---|---|---|---|---|---|---:|---|
| gemma4_e4b_it | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_A | A | A | 3.393 | acpi_unmarked_wrong_derivative_rule |
| gemma4_e4b_it | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_B | B | A | -2.088 | acpi_unmarked_wrong_derivative_rule |
| gemma4_e4b_it | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_A | A | A | 1.023 | acpi_unmarked_wrong_derivative_rule |
| gemma4_e4b_it | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_B | B | A | -0.129 | acpi_unmarked_wrong_derivative_rule |
| gemma4_e4b_it | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_A | A | A | 1.133 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| gemma4_e4b_it | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_B | B | A | -1.205 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| gemma4_e4b_it | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_A | A | A | 0.424 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| gemma4_e4b_it | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_B | B | A | -0.208 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| gemma4_e4b_it | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | en | bad_A | A | A | 1.527 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| gemma4_e4b_it | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | en | bad_B | B | A | -0.779 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| gemma4_e4b_it | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | zh | bad_A | A | A | 1.056 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| gemma4_e4b_it | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | zh | bad_B | B | B | 1.379 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| gemma4_e4b_it | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | en | bad_A | A | A | 3.056 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| gemma4_e4b_it | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | en | bad_B | B | A | -1.527 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| gemma4_e4b_it | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | zh | bad_A | A | A | 1.743 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| gemma4_e4b_it | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | zh | bad_B | B | A | -0.067 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| gemma4_e4b_it | qwen35_e18_discount_234_bad_181000_valid | en | bad_A | A | A | 4.132 | acpi_unmarked_discount_word_mismatch |
| gemma4_e4b_it | qwen35_e18_discount_234_bad_181000_valid | en | bad_B | B | A | -2.677 | acpi_unmarked_discount_word_mismatch |
| gemma4_e4b_it | qwen35_e18_discount_234_bad_181000_valid | zh | bad_A | A | A | 0.720 | acpi_unmarked_discount_word_mismatch |
| gemma4_e4b_it | qwen35_e18_discount_234_bad_181000_valid | zh | bad_B | B | A | -0.404 | acpi_unmarked_discount_word_mismatch |
| gemma4_e4b_it | qwen35_e18_discount_234_bad_181001_valid | en | bad_A | A | A | 3.736 | acpi_unmarked_discount_word_mismatch |
| gemma4_e4b_it | qwen35_e18_discount_234_bad_181001_valid | en | bad_B | B | A | -3.021 | acpi_unmarked_discount_word_mismatch |
| gemma4_e4b_it | qwen35_e18_discount_234_bad_181001_valid | zh | bad_A | A | A | 3.125 | acpi_unmarked_discount_word_mismatch |
| gemma4_e4b_it | qwen35_e18_discount_234_bad_181001_valid | zh | bad_B | B | A | 0.000 | acpi_unmarked_discount_word_mismatch |
| qwen35_27b | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_A | A | A | 1.890 | acpi_unmarked_wrong_derivative_rule |
| qwen35_27b | qwen14_deriv_sum_zh_402_bad_403_valid | en | bad_B | B | B | 2.671 | acpi_unmarked_wrong_derivative_rule |
| qwen35_27b | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_A | A | A | 3.125 | acpi_unmarked_wrong_derivative_rule |
| qwen35_27b | qwen14_deriv_sum_zh_402_bad_403_valid | zh | bad_B | B | B | 3.250 | acpi_unmarked_wrong_derivative_rule |
| qwen35_27b | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_A | A | A | 0.875 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen35_27b | qwen14_dabazhe_zh_en_445_bad_442_valid | en | bad_B | B | B | 0.375 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen35_27b | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_A | A | A | 0.625 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen35_27b | qwen14_dabazhe_zh_en_445_bad_442_valid | zh | bad_B | B | B | 1.375 | acpi_lexical_mismatch_dabazhe_80_percent_discount |
| qwen35_27b | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | en | bad_A | A | A | 0.375 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen35_27b | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | en | bad_B | B | B | 0.250 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen35_27b | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | zh | bad_A | A | A | 0.500 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen35_27b | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | zh | bad_B | B | B | 0.625 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen35_27b | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | en | bad_A | A | A | 0.625 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen35_27b | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | en | bad_B | B | A | -0.375 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen35_27b | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | zh | bad_A | A | A | 0.625 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen35_27b | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | zh | bad_B | B | A | -0.750 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen35_27b | qwen35_e18_discount_234_bad_181000_valid | en | bad_A | A | A | 1.250 | acpi_unmarked_discount_word_mismatch |
| qwen35_27b | qwen35_e18_discount_234_bad_181000_valid | en | bad_B | B | B | 0.500 | acpi_unmarked_discount_word_mismatch |
| qwen35_27b | qwen35_e18_discount_234_bad_181000_valid | zh | bad_A | A | A | 1.500 | acpi_unmarked_discount_word_mismatch |
| qwen35_27b | qwen35_e18_discount_234_bad_181000_valid | zh | bad_B | B | A | 0.000 | acpi_unmarked_discount_word_mismatch |
| qwen35_27b | qwen35_e18_discount_234_bad_181001_valid | en | bad_A | A | A | 1.000 | acpi_unmarked_discount_word_mismatch |
| qwen35_27b | qwen35_e18_discount_234_bad_181001_valid | en | bad_B | B | B | 0.875 | acpi_unmarked_discount_word_mismatch |
| qwen35_27b | qwen35_e18_discount_234_bad_181001_valid | zh | bad_A | A | A | 1.500 | acpi_unmarked_discount_word_mismatch |
| qwen35_27b | qwen35_e18_discount_234_bad_181001_valid | zh | bad_B | B | B | 0.750 | acpi_unmarked_discount_word_mismatch |
