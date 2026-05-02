# E23 E18 Clean-Sibling Qwen3.5 Contrastive Verifier Summary

The verifier sees a valid and an answer-correct/process-invalid sibling trace and must choose which trace has invalid reasoning. This separates absolute Yes-bias from pairwise error visibility.

## Overall

| verifier | n | acc | mean target margin |
|---|---:|---:|---:|
| qwen35_9b | 8 | 1.000 | 0.594 |
| qwen3_14b_base | 8 | 1.000 | 2.141 |

## Slices

| verifier | slice type | slice | n | acc | mean target margin |
|---|---|---|---:|---:|---:|
| qwen35_9b | pair | qwen35_e18_discount_234_bad_181000_valid | 4 | 1.000 | 0.563 |
| qwen35_9b | pair | qwen35_e18_discount_234_bad_181001_valid | 4 | 1.000 | 0.625 |
| qwen35_9b | prompt_lang | en | 4 | 1.000 | 0.688 |
| qwen35_9b | prompt_lang | zh | 4 | 1.000 | 0.500 |
| qwen35_9b | trace_model | qwen35_9b | 8 | 1.000 | 0.594 |
| qwen3_14b_base | pair | qwen35_e18_discount_234_bad_181000_valid | 4 | 1.000 | 2.125 |
| qwen3_14b_base | pair | qwen35_e18_discount_234_bad_181001_valid | 4 | 1.000 | 2.156 |
| qwen3_14b_base | prompt_lang | en | 4 | 1.000 | 1.906 |
| qwen3_14b_base | prompt_lang | zh | 4 | 1.000 | 2.375 |
| qwen3_14b_base | trace_model | qwen35_9b | 8 | 1.000 | 2.141 |

## Rows

| verifier | pair | prompt | order | target | pred | margin | bad risk |
|---|---|---|---|---|---|---:|---|
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | en | bad_A | A | A | 0.250 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | en | bad_B | B | B | 0.875 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | zh | bad_A | A | A | 0.250 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | zh | bad_B | B | B | 0.875 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | en | bad_A | A | A | 0.750 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | en | bad_B | B | B | 0.875 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | zh | bad_A | A | A | 0.250 | acpi_unmarked_discount_word_mismatch |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | zh | bad_B | B | B | 0.625 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181000_valid | en | bad_A | A | A | 2.125 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181000_valid | en | bad_B | B | B | 1.500 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181000_valid | zh | bad_A | A | A | 3.625 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181000_valid | zh | bad_B | B | B | 1.250 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181001_valid | en | bad_A | A | A | 2.125 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181001_valid | en | bad_B | B | B | 1.875 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181001_valid | zh | bad_A | A | A | 2.500 | acpi_unmarked_discount_word_mismatch |
| qwen3_14b_base | qwen35_e18_discount_234_bad_181001_valid | zh | bad_B | B | B | 2.125 | acpi_unmarked_discount_word_mismatch |
