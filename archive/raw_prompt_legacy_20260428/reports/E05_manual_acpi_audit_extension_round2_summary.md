# E05 Manual ACPI Audit Summary

Manual labels: `data/processed/manual_e05_audit_extension_round2_20260427.jsonl`.

Policy: `manual_process_valid=false` is strict: any asserted mathematical or language-semantic error makes the process invalid. Self-corrected errors are tagged in `manual_risk`; `paper_grade_acpi` marks uncorrected/high-risk ACPI examples.

## Overall Counts

| slice | count |
|---|---:|
| audited rows | 31 |
| process-valid | 29 |
| process-invalid | 1 |
| process-unknown | 1 |
| final-correct | 29 |
| final-wrong | 1 |
| final-unknown | 1 |
| format-clean | 14 |
| format-broken | 17 |
| strict ACPI | 0 |
| paper-grade ACPI | 0 |

## By Model

| model | n | process invalid | final correct | format broken | strict ACPI | paper-grade ACPI |
|---|---:|---:|---:|---:|---:|---:|
| qwen35_9b | 27 | 1 | 25 | 17 | 0 | 0 |
| qwen3_14b_base | 4 | 0 | 4 | 0 | 0 | 0 |

## By Task

| task | n | process invalid | final wrong | strict ACPI | top risk signal |
|---|---:|---:|---:|---:|---|
| deriv_coeff | 4 | 0 | 0 | 0 | valid_correct_but_after_final_new_problem_spill |
| deriv_product_equiv | 8 | 1 | 1 | 0 | valid_correct_but_after_final_spill_or_trim |
| frac_simplify | 4 | 0 | 0 | 0 | valid_correct_but_visible_empty_think_tag |
| percent_then_discount | 12 | 0 | 0 | 0 | valid_clean |
| rem_137_9 | 3 | 0 | 0 | 0 | valid_correct_but_after_final_duplicate_reasoning |

## Strict ACPI Rows

| idx | paper-grade | model | task | route | risk | earliest error | correction |
|---:|---|---|---|---|---|---|---|

## Risk Distribution

| risk | count |
|---|---:|
| valid_clean | 13 |
| valid_correct_but_after_final_spill_or_trim | 6 |
| visible_valid_but_truncated_hidden_plan_wrong_language | 2 |
| valid_correct_but_after_final_new_problem_spill | 2 |
| valid_correct_but_visible_empty_think_tag | 2 |
| wrong_derivative_final_wrong_after_final_spill | 1 |
| valid_correct_but_after_final_translation_spill | 1 |
| valid_correct_but_after_final_duplicate_reasoning | 1 |
| visible_valid_but_truncated_hidden_plan_no_final | 1 |
| valid_clean_minor_final_dollar_format | 1 |
| format_only_placeholder_final_answer_contains_think | 1 |
