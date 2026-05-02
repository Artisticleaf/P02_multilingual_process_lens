# E21 E18 Qwen14 New-Pair Contrastive Verifier Summary

The verifier sees a valid and an answer-correct/process-invalid sibling trace and must choose which trace has invalid reasoning. This separates absolute Yes-bias from pairwise error visibility.

## Overall

| verifier | n | acc | mean target margin |
|---|---:|---:|---:|
| qwen35_9b | 12 | 0.667 | 0.083 |
| qwen3_14b_base | 12 | 0.333 | -0.438 |

## Slices

| verifier | slice type | slice | n | acc | mean target margin |
|---|---|---|---:|---:|---:|
| qwen35_9b | pair | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | 4 | 0.500 | 0.094 |
| qwen35_9b | pair | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | 4 | 0.750 | 0.094 |
| qwen35_9b | pair | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | 4 | 0.750 | 0.062 |
| qwen35_9b | prompt_lang | en | 6 | 0.667 | 0.104 |
| qwen35_9b | prompt_lang | zh | 6 | 0.667 | 0.062 |
| qwen35_9b | trace_model | qwen3_14b_base | 12 | 0.667 | 0.083 |
| qwen3_14b_base | pair | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | 4 | 0.500 | 0.156 |
| qwen3_14b_base | pair | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | 4 | 0.000 | -0.969 |
| qwen3_14b_base | pair | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | 4 | 0.500 | -0.500 |
| qwen3_14b_base | prompt_lang | en | 6 | 0.333 | -0.312 |
| qwen3_14b_base | prompt_lang | zh | 6 | 0.333 | -0.563 |
| qwen3_14b_base | trace_model | qwen3_14b_base | 12 | 0.333 | -0.438 |

## Rows

| verifier | pair | prompt | order | target | pred | margin | bad risk |
|---|---|---|---|---|---|---:|---|
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | en | bad_A | A | A | 0.250 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | en | bad_B | B | B | 0.125 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | zh | bad_A | A | A | 0.000 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | zh | bad_B | B | A | 0.000 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | en | bad_A | A | A | 0.125 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | en | bad_B | B | A | -0.125 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | zh | bad_A | A | A | 0.125 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen35_9b | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | zh | bad_B | B | B | 0.125 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen35_9b | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | en | bad_A | A | B | -1.000 | semantic_drift_80pct_discount_final_wrong |
| qwen35_9b | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | en | bad_B | B | B | 1.250 | semantic_drift_80pct_discount_final_wrong |
| qwen35_9b | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | zh | bad_A | A | B | -0.500 | semantic_drift_80pct_discount_final_wrong |
| qwen35_9b | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | zh | bad_B | B | B | 0.625 | semantic_drift_80pct_discount_final_wrong |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | en | bad_A | A | B | -0.750 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | en | bad_B | B | A | -0.750 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | zh | bad_A | A | B | -1.500 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | zh | bad_B | B | A | -0.875 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | en | bad_A | A | A | 0.125 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | en | bad_B | B | A | -0.875 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | zh | bad_A | A | A | 0.125 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | zh | bad_B | B | A | -1.375 | acpi_unmarked_dabazhe_80pct_discount_word_mismatch |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | en | bad_A | A | B | -0.250 | semantic_drift_80pct_discount_final_wrong |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | en | bad_B | B | B | 0.625 | semantic_drift_80pct_discount_final_wrong |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | zh | bad_A | A | B | -0.375 | semantic_drift_80pct_discount_final_wrong |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | zh | bad_B | B | B | 0.625 | semantic_drift_80pct_discount_final_wrong |
