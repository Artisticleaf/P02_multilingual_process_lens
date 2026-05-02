# E05 Manual ACPI Audit Summary

Manual labels: `data/processed/manual_e05_audit_combined_20260427.jsonl`.

Policy: `manual_process_valid=false` is strict: any asserted mathematical or language-semantic error makes the process invalid. Self-corrected errors are tagged in `manual_risk`; `paper_grade_acpi` marks uncorrected/high-risk ACPI examples.

## Overall Counts

| slice | count |
|---|---:|
| audited rows | 154 |
| process-valid | 132 |
| process-invalid | 18 |
| process-unknown | 4 |
| final-correct | 138 |
| final-wrong | 7 |
| final-unknown | 9 |
| format-clean | 77 |
| format-broken | 77 |
| strict ACPI | 9 |
| paper-grade ACPI | 4 |

## By Model

| model | n | process invalid | final correct | format broken | strict ACPI | paper-grade ACPI |
|---|---:|---:|---:|---:|---:|---:|
| deepseek_r1_0528_qwen3_8b | 20 | 2 | 20 | 20 | 2 | 0 |
| phi4_mini_reasoning | 17 | 7 | 12 | 17 | 3 | 1 |
| qwen35_9b | 83 | 5 | 75 | 38 | 2 | 1 |
| qwen3_14b_base | 34 | 4 | 31 | 2 | 2 | 2 |

## By Task

| task | n | process invalid | final wrong | strict ACPI | top risk signal |
|---|---:|---:|---:|---:|---|
| deriv_coeff | 13 | 3 | 2 | 0 | valid_clean |
| deriv_product_equiv | 8 | 1 | 1 | 0 | valid_correct_but_after_final_spill_or_trim |
| deriv_sum | 22 | 4 | 0 | 4 | valid_clean |
| disc_en_25_off | 8 | 1 | 0 | 1 | valid_correct_but_raw_or_visible_spill |
| disc_en_75_off | 20 | 1 | 1 | 0 | valid_clean |
| disc_zh_75_price | 20 | 4 | 2 | 2 | valid_clean |
| frac_simplify | 6 | 1 | 0 | 0 | valid_correct_but_after_final_spill_or_trim |
| percent_then_discount | 26 | 2 | 1 | 1 | valid_clean |
| ratio_boys_girls | 8 | 0 | 0 | 0 | valid_clean |
| ratio_boys_total | 12 | 1 | 0 | 1 | valid_clean |
| ratio_girls_boys | 8 | 0 | 0 | 0 | valid_correct_but_after_final_spill_or_trim |
| rem_137_9 | 3 | 0 | 0 | 0 | valid_correct_but_after_final_duplicate_reasoning |

## Strict ACPI Rows

| idx | paper-grade | model | task | route | risk | earliest error | correction |
|---:|---|---|---|---|---|---|---|
| 4 | False | deepseek_r1_0528_qwen3_8b | disc_zh_75_price | zh->en | self_corrected_discount_semantic_confusion | translates 七五折 as 75% discount | 先把“打七五折”翻成 75% discount/75% off，随后改正为“售价为原价75%”；答案正确但过程含语义假步。 |
| 6 | False | deepseek_r1_0528_qwen3_8b | disc_zh_75_price | en->zh | self_corrected_75_percent_surface_confusion | 折扣是75% off | 先写“折扣是75% off”，随后改成 sold at 75% of original；答案正确但包含中英语义混淆。 |
| 178 | True | phi4_mini_reasoning | deriv_sum | zh->zh | acpi_truncated_wrong_derivative_rule | x 的导数是0 | 最终文本中多次指向2x+3，但过程含“x 的导数是0所以3x导数为3”的错误理由，且正式答案截断。 |
| 179 | False | phi4_mini_reasoning | deriv_sum | zh->zh | self_corrected_derivative_rule_error_truncated | 3x的导数，因为3是常数项，所以导数是0 | 先把3x导数判为0并得到2x，随后发现矛盾并改到2x+3；无干净最终答案。 |
| 183 | False | phi4_mini_reasoning | deriv_sum | en->zh | late_confusion_constant_vs_linear_derivative_truncated | 如果函数中有一个常数项，比如3x，那它的导数就是0 | 前面定义法正确得到2x+3，但后面又混淆“常数项”和3x；截断前未完成纠错。 |
| 234 | True | qwen35_9b | disc_en_25_off | zh->zh | acpi_unmarked_discount_word_mismatch | 打八折，即原价的75% | 题目是优惠25%，最终60正确；但推理写“打八折，即原价的75%”，八折和75%不一致，属于表层折扣词错误。 |
| 261 | False | qwen35_9b | ratio_boys_total | zh->en | acpi_self_corrected_arithmetic_step | 64 - 2 = 62 | 先写女生=64-2=62，括号中自我纠正应为64-24=40；最终40正确，但轨迹包含显式错误步骤。 |
| 402 | True | qwen3_14b_base | deriv_sum | zh->zh | acpi_unmarked_wrong_derivative_rule | 3 是常数，常数的导数为 0，所以 (3x)'=3 | 最终 2x+3 正确，但第5步说“3 是常数，常数导数为0，所以 (3x)'=3”；把系数常数和整个 3x 混淆。 |
| 445 | True | qwen3_14b_base | percent_then_discount | zh->en | acpi_lexical_mismatch_dabazhe_80_percent_discount | apply an 80% discount | 最终表达式 80*1.25*0.80 等价于80，但文字说“apply an 80% discount”，与公式0.80/pay-80%冲突。 |

## Risk Distribution

| risk | count |
|---|---:|
| valid_clean | 68 |
| truncated_valid_or_no_clean_final | 27 |
| valid_correct_but_after_final_spill_or_trim | 17 |
| valid_correct_but_raw_or_visible_spill | 7 |
| valid_math_wrong_requested_reason_language | 3 |
| valid_correct_but_visible_empty_think_tag | 2 |
| self_corrected_discount_semantic_confusion | 1 |
| self_corrected_75_percent_surface_confusion | 1 |
| acpi_truncated_wrong_derivative_rule | 1 |
| self_corrected_derivative_rule_error_truncated | 1 |
| late_confusion_constant_vs_linear_derivative_truncated | 1 |
| wrong_derivative_x_to_x_final_wrong_truncated | 1 |
| contradictory_definition_derivative_omits_h_term | 1 |
| offtask_mvt_problem_generated | 1 |
| nonsense_spill_after_correct_fraction_start | 1 |
| truncated_valid_before_final_value | 1 |
| semantic_drift_qiwuzhe_to_75off_final_wrong_repeated | 1 |
| semantic_drift_qiwuzhe_to_75off_final_wrong | 1 |
| acpi_unmarked_discount_word_mismatch | 1 |
| format_only_no_solution_prompt_spill | 1 |
| format_only_placeholder_answer | 1 |
| valid_but_final_line_contains_reasoning | 1 |
| acpi_self_corrected_arithmetic_step | 1 |
| valid_with_variable_name_typo_and_trim | 1 |
| wrong_derivative_and_after_final_template | 1 |
| truncated_valid_planning_no_final | 1 |
| valid_correct_but_after_final_duplicate_reasoning | 1 |
| visible_valid_but_truncated_hidden_plan_wrong_language | 1 |
| truncated_valid_meta_reasoning_no_final | 1 |
| valid_clean_minor_final_dollar_format | 1 |
| format_only_placeholder_final_answer_contains_think | 1 |
| semantic_drift_75off_to_qiwuzhe_final_wrong | 1 |
| acpi_unmarked_wrong_derivative_rule | 1 |
| empty_generation | 1 |
| semantic_drift_dabazhe_as_80_percent_discount_final_wrong | 1 |
| acpi_lexical_mismatch_dabazhe_80_percent_discount | 1 |
