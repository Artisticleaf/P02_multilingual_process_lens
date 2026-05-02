# E05 Manual ACPI Audit Summary

Manual labels: `data/processed/e18_manual_targeted_audit_20260427.jsonl`.

Policy: `manual_process_valid=false` is strict: any asserted mathematical or language-semantic error makes the process invalid. Self-corrected errors are tagged in `manual_risk`; `paper_grade_acpi` marks uncorrected/high-risk ACPI examples.

## Overall Counts

| slice | count |
|---|---:|
| audited rows | 32 |
| process-valid | 24 |
| process-invalid | 8 |
| process-unknown | 0 |
| final-correct | 25 |
| final-wrong | 7 |
| final-unknown | 0 |
| format-clean | 23 |
| format-broken | 9 |
| strict ACPI | 1 |
| paper-grade ACPI | 1 |

## By Model

| model | n | process invalid | final correct | format broken | strict ACPI | paper-grade ACPI |
|---|---:|---:|---:|---:|---:|---:|
| qwen35_9b | 12 | 2 | 10 | 7 | 0 | 0 |
| qwen3_14b_base | 20 | 6 | 15 | 2 | 1 | 1 |

## By Task

| task | n | process invalid | final wrong | strict ACPI | top risk signal |
|---|---:|---:|---:|---:|---|
| disc_en_25_off | 9 | 1 | 1 | 0 | valid_clean_same_route_discount |
| disc_en_75_off | 2 | 0 | 0 | 0 | valid_but_reason_language_violation |
| disc_zh_75_price | 9 | 4 | 4 | 0 | valid_clean_translation_to_25pct_off |
| percent_then_discount | 8 | 3 | 2 | 1 | valid_clean_same_route_sibling |
| ratio_boys_total | 4 | 0 | 0 | 0 | valid_clean |

## Strict ACPI Rows

| idx | paper-grade | model | task | route | risk | earliest error | correction |
|---:|---|---|---|---|---|---|---|
| 180092 | True | qwen3_14b_base | percent_then_discount | zh->en | acpi_unmarked_dabazhe_80pct_discount_word_mismatch | says apply the 80% discount but multiplies by 0.80 |  |

## Risk Distribution

| risk | count |
|---|---:|
| valid_clean | 5 |
| valid_clean_same_route_discount | 4 |
| valid_but_reason_language_violation | 3 |
| valid_clean_translation_to_25pct_off | 3 |
| valid_correct_but_after_final_spill | 3 |
| semantic_drift_75pct_off_final_wrong | 2 |
| valid_clean_same_route_sibling | 2 |
| semantic_drift_80pct_discount_final_wrong | 2 |
| valid_correct_but_after_final_prompt_spill | 2 |
| final_wrong_hallucinated_85_discount | 1 |
| valid_correct_but_missing_final_marker | 1 |
| acpi_unmarked_dabazhe_80pct_discount_word_mismatch | 1 |
| semantic_drift_qiwuzhe_75pct_off_final_wrong | 1 |
| self_correcting_semantic_drift_truncated | 1 |
| valid_clean_ratio | 1 |
