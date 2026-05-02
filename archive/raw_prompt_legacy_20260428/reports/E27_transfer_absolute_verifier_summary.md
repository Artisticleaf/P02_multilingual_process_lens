# E27 Transfer Absolute Verifier Summary / E27 跨模型绝对 verifier 汇总

Manual seed labels are in `data/processed/e27_transfer_probe_manual_subset_20260427.jsonl`.

Modes:

- `process_only`: judge mathematical process only; ignore truncation/format.
- `training_candidate`: keep only if final answer, process, and output hygiene are all acceptable.

## Overall

| verifier | mode | prompt | n | acc | yes rate | false accept | process-invalid false accept | ACPI false accept | mean margin |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| gemma4_e4b_it | process_only | en | 11 | 0.636 | 1.000 | 1.000 | 1.000 | 1.000 | 6.307 |
| gemma4_e4b_it | process_only | zh | 11 | 0.636 | 1.000 | 1.000 | 1.000 | 1.000 | 7.538 |
| gemma4_e4b_it | training_candidate | en | 11 | 0.545 | 1.000 | 1.000 | 1.000 | 1.000 | 6.352 |
| gemma4_e4b_it | training_candidate | zh | 11 | 0.545 | 1.000 | 1.000 | 1.000 | 1.000 | 6.915 |
| qwen35_27b | process_only | en | 11 | 0.636 | 1.000 | 1.000 | 1.000 | 1.000 | 3.847 |
| qwen35_27b | process_only | zh | 11 | 0.636 | 1.000 | 1.000 | 1.000 | 1.000 | 2.693 |
| qwen35_27b | training_candidate | en | 11 | 0.545 | 1.000 | 1.000 | 1.000 | 1.000 | 0.920 |
| qwen35_27b | training_candidate | zh | 11 | 0.727 | 0.818 | 0.600 | 0.500 | 0.500 | 0.693 |

## Error Rows

### gemma4_e4b_it

| idx | mode | prompt | trace model | task | route | risk | target | pred | margin |
|---:|---|---|---|---|---|---|---|---|---:|
| 234 | process_only | en | qwen35_9b | disc_en_25_off | zh->zh | acpi_unmarked_discount_word_mismatch | False | True | 6.000 |
| 402 | process_only | en | qwen3_14b_base | deriv_sum | zh->zh | acpi_unmarked_wrong_derivative_rule | False | True | 6.625 |
| 445 | process_only | en | qwen3_14b_base | percent_then_discount | zh->en | acpi_lexical_mismatch_dabazhe_80_percent_discount | False | True | 4.625 |
| 180092 | process_only | en | qwen3_14b_base | percent_then_discount | zh->en | acpi_unmarked_dabazhe_80pct_discount_word_mismatch | False | True | 3.000 |
| 234 | process_only | zh | qwen35_9b | disc_en_25_off | zh->zh | acpi_unmarked_discount_word_mismatch | False | True | 4.408 |
| 402 | process_only | zh | qwen3_14b_base | deriv_sum | zh->zh | acpi_unmarked_wrong_derivative_rule | False | True | 9.875 |
| 445 | process_only | zh | qwen3_14b_base | percent_then_discount | zh->en | acpi_lexical_mismatch_dabazhe_80_percent_discount | False | True | 5.750 |
| 180092 | process_only | zh | qwen3_14b_base | percent_then_discount | zh->en | acpi_unmarked_dabazhe_80pct_discount_word_mismatch | False | True | 6.125 |
| 234 | training_candidate | en | qwen35_9b | disc_en_25_off | zh->zh | acpi_unmarked_discount_word_mismatch | False | True | 5.000 |
| 235 | training_candidate | en | qwen35_9b | disc_en_25_off | zh->zh | valid_correct_but_raw_or_visible_spill | False | True | 8.250 |
| 402 | training_candidate | en | qwen3_14b_base | deriv_sum | zh->zh | acpi_unmarked_wrong_derivative_rule | False | True | 8.000 |
| 445 | training_candidate | en | qwen3_14b_base | percent_then_discount | zh->en | acpi_lexical_mismatch_dabazhe_80_percent_discount | False | True | 4.500 |
| 180092 | training_candidate | en | qwen3_14b_base | percent_then_discount | zh->en | acpi_unmarked_dabazhe_80pct_discount_word_mismatch | False | True | 3.000 |
| 234 | training_candidate | zh | qwen35_9b | disc_en_25_off | zh->zh | acpi_unmarked_discount_word_mismatch | False | True | 8.311 |
| 235 | training_candidate | zh | qwen35_9b | disc_en_25_off | zh->zh | valid_correct_but_raw_or_visible_spill | False | True | 5.038 |
| 402 | training_candidate | zh | qwen3_14b_base | deriv_sum | zh->zh | acpi_unmarked_wrong_derivative_rule | False | True | 8.250 |
| 445 | training_candidate | zh | qwen3_14b_base | percent_then_discount | zh->en | acpi_lexical_mismatch_dabazhe_80_percent_discount | False | True | 5.750 |
| 180092 | training_candidate | zh | qwen3_14b_base | percent_then_discount | zh->en | acpi_unmarked_dabazhe_80pct_discount_word_mismatch | False | True | 2.250 |

### qwen35_27b

| idx | mode | prompt | trace model | task | route | risk | target | pred | margin |
|---:|---|---|---|---|---|---|---|---|---:|
| 234 | process_only | en | qwen35_9b | disc_en_25_off | zh->zh | acpi_unmarked_discount_word_mismatch | False | True | 3.125 |
| 402 | process_only | en | qwen3_14b_base | deriv_sum | zh->zh | acpi_unmarked_wrong_derivative_rule | False | True | 3.250 |
| 445 | process_only | en | qwen3_14b_base | percent_then_discount | zh->en | acpi_lexical_mismatch_dabazhe_80_percent_discount | False | True | 3.500 |
| 180092 | process_only | en | qwen3_14b_base | percent_then_discount | zh->en | acpi_unmarked_dabazhe_80pct_discount_word_mismatch | False | True | 3.625 |
| 234 | process_only | zh | qwen35_9b | disc_en_25_off | zh->zh | acpi_unmarked_discount_word_mismatch | False | True | 2.000 |
| 402 | process_only | zh | qwen3_14b_base | deriv_sum | zh->zh | acpi_unmarked_wrong_derivative_rule | False | True | 2.125 |
| 445 | process_only | zh | qwen3_14b_base | percent_then_discount | zh->en | acpi_lexical_mismatch_dabazhe_80_percent_discount | False | True | 1.750 |
| 180092 | process_only | zh | qwen3_14b_base | percent_then_discount | zh->en | acpi_unmarked_dabazhe_80pct_discount_word_mismatch | False | True | 2.375 |
| 234 | training_candidate | en | qwen35_9b | disc_en_25_off | zh->zh | acpi_unmarked_discount_word_mismatch | False | True | 0.625 |
| 235 | training_candidate | en | qwen35_9b | disc_en_25_off | zh->zh | valid_correct_but_raw_or_visible_spill | False | True | 1.125 |
| 402 | training_candidate | en | qwen3_14b_base | deriv_sum | zh->zh | acpi_unmarked_wrong_derivative_rule | False | True | 0.750 |
| 445 | training_candidate | en | qwen3_14b_base | percent_then_discount | zh->en | acpi_lexical_mismatch_dabazhe_80_percent_discount | False | True | 0.625 |
| 180092 | training_candidate | en | qwen3_14b_base | percent_then_discount | zh->en | acpi_unmarked_dabazhe_80pct_discount_word_mismatch | False | True | 0.875 |
| 234 | training_candidate | zh | qwen35_9b | disc_en_25_off | zh->zh | acpi_unmarked_discount_word_mismatch | False | True | 0.375 |
| 235 | training_candidate | zh | qwen35_9b | disc_en_25_off | zh->zh | valid_correct_but_raw_or_visible_spill | False | True | 1.125 |
| 180092 | training_candidate | zh | qwen3_14b_base | percent_then_discount | zh->en | acpi_unmarked_dabazhe_80pct_discount_word_mismatch | False | True | 0.625 |

