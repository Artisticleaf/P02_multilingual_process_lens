# E31 Non-Discount Counterfactual Summary / E31 非折扣反事实总结

Labels / 标签: `data/processed/e31_non_discount_counterfactual_20260427.jsonl`.
Results / 结果: `results/E31_non_discount_counterfactual_absolute_verifier`.

E31 uses hand-controlled siblings for five non-discount traps. Each task has a valid process and an invalid local process phrase, crossed with correct, masked, and wrong final-answer lines. / E31 为 5 类非折扣陷阱构造人工受控 sibling：每题有有效过程和局部无效过程短语，并与正确、遮蔽、错误三种最终答案行交叉。

## Overall / 总体

| verifier | mode | prompt | n | acc | yes rate | process-invalid false accept | ACPI false accept | mean yes-no margin |
|---|---|---|---:|---:|---:|---:|---:|---:|
| gemma4_e4b_it | process_only | en | 30 | 0.500 | 0.933 | 0.933 | 1.000 | 4.346 |
| gemma4_e4b_it | process_only | zh | 30 | 0.500 | 1.000 | 1.000 | 1.000 | 5.167 |
| gemma4_e4b_it | training_candidate | en | 30 | 0.333 | 0.833 | 0.800 | 1.000 | 3.483 |
| gemma4_e4b_it | training_candidate | zh | 30 | 0.300 | 0.867 | 0.933 | 1.000 | 5.111 |
| qwen35_27b | process_only | en | 30 | 0.500 | 1.000 | 1.000 | 1.000 | 2.483 |
| qwen35_27b | process_only | zh | 30 | 0.667 | 0.833 | 0.667 | 0.800 | 1.358 |
| qwen35_27b | training_candidate | en | 30 | 0.567 | 0.600 | 0.533 | 0.800 | 0.358 |
| qwen35_27b | training_candidate | zh | 30 | 0.767 | 0.333 | 0.133 | 0.200 | -0.815 |
| qwen35_9b | process_only | en | 30 | 0.600 | 0.633 | 0.533 | 0.600 | 1.219 |
| qwen35_9b | process_only | zh | 30 | 0.567 | 0.933 | 0.867 | 0.800 | 1.442 |
| qwen35_9b | training_candidate | en | 30 | 0.633 | 0.533 | 0.400 | 0.600 | 0.796 |
| qwen35_9b | training_candidate | zh | 30 | 0.633 | 0.533 | 0.400 | 0.800 | 0.585 |
| qwen3_14b_base | process_only | en | 30 | 0.833 | 0.533 | 0.200 | 0.200 | 0.846 |
| qwen3_14b_base | process_only | zh | 30 | 0.833 | 0.667 | 0.333 | 0.600 | 0.667 |
| qwen3_14b_base | training_candidate | en | 30 | 0.600 | 0.567 | 0.467 | 0.800 | 0.604 |
| qwen3_14b_base | training_candidate | zh | 30 | 0.400 | 0.767 | 0.800 | 1.000 | 0.792 |

## Process-Only Variant Rates / 只审过程的变体接受率

| verifier | prompt | variant | yes rate | mean yes-no margin |
|---|---|---|---:|---:|
| gemma4_e4b_it | en | valid_correct | 1.000 | 6.125 |
| gemma4_e4b_it | en | invalid_correct | 1.000 | 5.575 |
| gemma4_e4b_it | en | valid_masked | 1.000 | 5.850 |
| gemma4_e4b_it | en | invalid_masked | 1.000 | 5.125 |
| gemma4_e4b_it | en | valid_wrong | 0.800 | 1.600 |
| gemma4_e4b_it | en | invalid_wrong | 0.800 | 1.800 |
| gemma4_e4b_it | zh | valid_correct | 1.000 | 6.768 |
| gemma4_e4b_it | zh | invalid_correct | 1.000 | 6.558 |
| gemma4_e4b_it | zh | valid_masked | 1.000 | 7.000 |
| gemma4_e4b_it | zh | invalid_masked | 1.000 | 5.425 |
| gemma4_e4b_it | zh | valid_wrong | 1.000 | 2.523 |
| gemma4_e4b_it | zh | invalid_wrong | 1.000 | 2.726 |
| qwen35_27b | en | valid_correct | 1.000 | 3.975 |
| qwen35_27b | en | invalid_correct | 1.000 | 2.025 |
| qwen35_27b | en | valid_masked | 1.000 | 4.150 |
| qwen35_27b | en | invalid_masked | 1.000 | 1.600 |
| qwen35_27b | en | valid_wrong | 1.000 | 1.950 |
| qwen35_27b | en | invalid_wrong | 1.000 | 1.200 |
| qwen35_27b | zh | valid_correct | 1.000 | 2.775 |
| qwen35_27b | zh | invalid_correct | 0.800 | 1.050 |
| qwen35_27b | zh | valid_masked | 1.000 | 2.450 |
| qwen35_27b | zh | invalid_masked | 0.400 | 0.250 |
| qwen35_27b | zh | valid_wrong | 1.000 | 1.350 |
| qwen35_27b | zh | invalid_wrong | 0.800 | 0.275 |
| qwen35_9b | en | valid_correct | 1.000 | 3.375 |
| qwen35_9b | en | invalid_correct | 0.600 | 0.687 |
| qwen35_9b | en | valid_masked | 1.000 | 3.013 |
| qwen35_9b | en | invalid_masked | 0.800 | 0.987 |
| qwen35_9b | en | valid_wrong | 0.200 | -0.175 |
| qwen35_9b | en | invalid_wrong | 0.200 | -0.575 |
| qwen35_9b | zh | valid_correct | 1.000 | 2.562 |
| qwen35_9b | zh | invalid_correct | 0.800 | 1.013 |
| qwen35_9b | zh | valid_masked | 1.000 | 2.075 |
| qwen35_9b | zh | invalid_masked | 1.000 | 0.800 |
| qwen35_9b | zh | valid_wrong | 1.000 | 1.538 |
| qwen35_9b | zh | invalid_wrong | 0.800 | 0.662 |
| qwen3_14b_base | en | valid_correct | 1.000 | 2.650 |
| qwen3_14b_base | en | invalid_correct | 0.200 | -0.000 |
| qwen3_14b_base | en | valid_masked | 1.000 | 2.900 |
| qwen3_14b_base | en | invalid_masked | 0.200 | -0.075 |
| qwen3_14b_base | en | valid_wrong | 0.600 | 0.350 |
| qwen3_14b_base | en | invalid_wrong | 0.200 | -0.750 |
| qwen3_14b_base | zh | valid_correct | 1.000 | 1.801 |
| qwen3_14b_base | zh | invalid_correct | 0.600 | 0.150 |
| qwen3_14b_base | zh | valid_masked | 1.000 | 1.626 |
| qwen3_14b_base | zh | invalid_masked | 0.200 | -0.325 |
| qwen3_14b_base | zh | valid_wrong | 1.000 | 0.950 |
| qwen3_14b_base | zh | invalid_wrong | 0.200 | -0.200 |

## Local-Error Margin Effect / 局部错误对边际的影响

Negative delta means the invalid phrase lowers the verifier's Yes-vs-No margin relative to the valid sibling. / delta 为负表示无效短语相对有效 sibling 压低 verifier 的 Yes 相对 No 边际。

| verifier | prompt | answer condition | valid yes | invalid yes | invalid-valid margin delta |
|---|---|---|---:|---:|---:|
| gemma4_e4b_it | en | correct | 1.000 | 1.000 | -0.550 |
| gemma4_e4b_it | en | masked | 1.000 | 1.000 | -0.725 |
| gemma4_e4b_it | en | wrong | 0.800 | 0.800 | 0.200 |
| gemma4_e4b_it | zh | correct | 1.000 | 1.000 | -0.210 |
| gemma4_e4b_it | zh | masked | 1.000 | 1.000 | -1.575 |
| gemma4_e4b_it | zh | wrong | 1.000 | 1.000 | 0.203 |
| qwen35_27b | en | correct | 1.000 | 1.000 | -1.950 |
| qwen35_27b | en | masked | 1.000 | 1.000 | -2.550 |
| qwen35_27b | en | wrong | 1.000 | 1.000 | -0.750 |
| qwen35_27b | zh | correct | 1.000 | 0.800 | -1.725 |
| qwen35_27b | zh | masked | 1.000 | 0.400 | -2.200 |
| qwen35_27b | zh | wrong | 1.000 | 0.800 | -1.075 |
| qwen35_9b | en | correct | 1.000 | 0.600 | -2.688 |
| qwen35_9b | en | masked | 1.000 | 0.800 | -2.025 |
| qwen35_9b | en | wrong | 0.200 | 0.200 | -0.400 |
| qwen35_9b | zh | correct | 1.000 | 0.800 | -1.550 |
| qwen35_9b | zh | masked | 1.000 | 1.000 | -1.275 |
| qwen35_9b | zh | wrong | 1.000 | 0.800 | -0.875 |
| qwen3_14b_base | en | correct | 1.000 | 0.200 | -2.650 |
| qwen3_14b_base | en | masked | 1.000 | 0.200 | -2.975 |
| qwen3_14b_base | en | wrong | 0.600 | 0.200 | -1.100 |
| qwen3_14b_base | zh | correct | 1.000 | 0.600 | -1.651 |
| qwen3_14b_base | zh | masked | 1.000 | 0.200 | -1.950 |
| qwen3_14b_base | zh | wrong | 1.000 | 0.200 | -1.150 |

## ACPI False Accept by Trap / 按陷阱看 ACPI 误接受

This table uses only `invalid_correct` rows: the final answer is right but one local process phrase is wrong. / 本表只看 `invalid_correct` 行：最终答案正确，但局部过程短语错误。

| prompt | task | accepted / total | accept rate | mean yes-no margin | bad phrase in the controlled trace |
|---|---|---:|---:|---:|---|
| en | comb_choose_unordered | 3 / 4 | 0.750 | 2.344 | the order matters |
| en | geometry_diameter_area | 3 / 4 | 0.750 | 1.859 | 半径是10厘米 |
| en | inequality_no_more_than | 4 / 4 | 1.000 | 3.719 | between 3 and 7, inclusive |
| en | ratio_boys_girls_2_3 | 2 / 4 | 0.500 | 1.812 | 男生占全班的2/3 |
| en | unit_dozen_pairs | 2 / 4 | 0.500 | 0.625 | 一打袜子等于12双袜子 |
| zh | comb_choose_unordered | 3 / 4 | 0.750 | 2.202 | the order matters |
| zh | geometry_diameter_area | 4 / 4 | 1.000 | 2.168 | 半径是10厘米 |
| zh | inequality_no_more_than | 4 / 4 | 1.000 | 3.300 | between 3 and 7, inclusive |
| zh | ratio_boys_girls_2_3 | 4 / 4 | 1.000 | 2.956 | 男生占全班的2/3 |
| zh | unit_dozen_pairs | 1 / 4 | 0.250 | 0.337 | 一打袜子等于12双袜子 |

## Human-Readable Takeaways / 人话结论

- E31 confirms that the phenomenon is not discount-only: controlled ratio-denominator, inequality-boundary, unit, geometry, and combinatorics traps can produce answer-correct but process-invalid rows. / E31 证明现象不只属于折扣题：受控的比例分母、边界量词、单位、几何和组合陷阱都能构成“答案对但过程错”的行。
- The model split is scientifically useful: Gemma4 and Qwen3.5-27B still over-accept heavily; Qwen14 is much stricter on these controlled non-discount errors. / 模型分化本身有价值：Gemma4 与 Qwen3.5-27B 仍明显过度接受；Qwen14 对这些受控非折扣错误严格得多。
- The invalid phrase usually lowers the Yes-vs-No margin even when it is still accepted, so the verifier often has graded evidence but the final threshold/objective does not use it cleanly. / 无效短语通常会压低 Yes-vs-No 边际，即使最终仍被接受；这说明 verifier 常有连续证据，但最终阈值/目标没有干净使用它。
- Natural prevalence and controlled possibility must be separated: E30 found few natural non-discount ACPI rows, while E31 shows many controlled non-discount ACPI rows are accepted by verifiers. / 需要区分自然发生率和受控可行性：E30 的自然非折扣 ACPI 较少，E31 则显示受控非折扣 ACPI 仍常被 verifier 接受。
