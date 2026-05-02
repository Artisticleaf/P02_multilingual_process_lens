# E28 Counterfactual Answer-Masking Summary / E28 反事实与答案遮蔽总结

Labels / 标签: `data/processed/e28_counterfactual_answer_masking_20260427.jsonl`.
Results / 结果: `results/E28_counterfactual_answer_masking_absolute_verifier`.

E28 holds the problem and most arithmetic text fixed, then changes only the local lexical process phrase and the final-answer line. / E28 固定题目和大部分算术文本，只改变局部词汇过程短语与最终答案行。

## Overall / 总体

| verifier | mode | prompt | n | acc | yes rate | process-invalid false accept | ACPI false accept | mean yes-no margin |
|---|---|---|---:|---:|---:|---:|---:|---:|
| gemma4_e4b_it | process_only | en | 18 | 0.500 | 0.889 | 0.889 | 1.000 | 3.722 |
| gemma4_e4b_it | process_only | zh | 18 | 0.556 | 0.944 | 0.889 | 1.000 | 5.607 |
| gemma4_e4b_it | training_candidate | en | 18 | 0.389 | 0.778 | 0.778 | 1.000 | 3.590 |
| gemma4_e4b_it | training_candidate | zh | 18 | 0.167 | 1.000 | 1.000 | 1.000 | 6.733 |
| qwen35_27b | process_only | en | 18 | 0.500 | 1.000 | 1.000 | 1.000 | 2.851 |
| qwen35_27b | process_only | zh | 18 | 0.667 | 0.833 | 0.667 | 0.667 | 1.653 |
| qwen35_27b | training_candidate | en | 18 | 0.500 | 0.667 | 0.667 | 1.000 | 0.556 |
| qwen35_27b | training_candidate | zh | 18 | 0.611 | 0.556 | 0.444 | 0.667 | -0.167 |
| qwen35_9b | process_only | en | 18 | 0.667 | 0.833 | 0.667 | 0.667 | 1.608 |
| qwen35_9b | process_only | zh | 18 | 0.611 | 0.889 | 0.778 | 0.667 | 1.687 |
| qwen35_9b | training_candidate | en | 18 | 0.500 | 0.667 | 0.556 | 0.667 | 1.247 |
| qwen35_9b | training_candidate | zh | 18 | 0.611 | 0.556 | 0.444 | 0.667 | 0.781 |
| qwen3_14b_base | process_only | en | 18 | 0.500 | 0.556 | 0.556 | 0.667 | 1.007 |
| qwen3_14b_base | process_only | zh | 18 | 0.611 | 0.889 | 0.778 | 1.000 | 0.861 |
| qwen3_14b_base | training_candidate | en | 18 | 0.556 | 0.611 | 0.556 | 1.000 | 0.625 |
| qwen3_14b_base | training_candidate | zh | 18 | 0.167 | 1.000 | 1.000 | 1.000 | 1.132 |

## Process-Only Variant Rates / 只审过程的变体接受率

| verifier | prompt | variant | yes rate | mean yes-no margin |
|---|---|---|---:|---:|
| gemma4_e4b_it | en | valid_correct | 1.000 | 6.125 |
| gemma4_e4b_it | en | invalid_correct | 1.000 | 5.750 |
| gemma4_e4b_it | en | valid_masked | 1.000 | 5.500 |
| gemma4_e4b_it | en | invalid_masked | 1.000 | 4.667 |
| gemma4_e4b_it | en | valid_wrong | 0.667 | 0.333 |
| gemma4_e4b_it | en | invalid_wrong | 0.667 | -0.042 |
| gemma4_e4b_it | zh | valid_correct | 1.000 | 8.106 |
| gemma4_e4b_it | zh | invalid_correct | 1.000 | 7.412 |
| gemma4_e4b_it | zh | valid_masked | 1.000 | 8.458 |
| gemma4_e4b_it | zh | invalid_masked | 1.000 | 6.917 |
| gemma4_e4b_it | zh | valid_wrong | 1.000 | 1.667 |
| gemma4_e4b_it | zh | invalid_wrong | 0.667 | 1.083 |
| qwen35_27b | en | valid_correct | 1.000 | 3.750 |
| qwen35_27b | en | invalid_correct | 1.000 | 2.792 |
| qwen35_27b | en | valid_masked | 1.000 | 3.854 |
| qwen35_27b | en | invalid_masked | 1.000 | 2.750 |
| qwen35_27b | en | valid_wrong | 1.000 | 2.375 |
| qwen35_27b | en | invalid_wrong | 1.000 | 1.583 |
| qwen35_27b | zh | valid_correct | 1.000 | 2.583 |
| qwen35_27b | zh | invalid_correct | 0.667 | 1.667 |
| qwen35_27b | zh | valid_masked | 1.000 | 2.333 |
| qwen35_27b | zh | invalid_masked | 0.667 | 1.167 |
| qwen35_27b | zh | valid_wrong | 1.000 | 1.458 |
| qwen35_27b | zh | invalid_wrong | 0.667 | 0.708 |
| qwen35_9b | en | valid_correct | 1.000 | 3.292 |
| qwen35_9b | en | invalid_correct | 0.667 | 1.479 |
| qwen35_9b | en | valid_masked | 1.000 | 2.542 |
| qwen35_9b | en | invalid_masked | 0.667 | 1.625 |
| qwen35_9b | en | valid_wrong | 1.000 | 0.500 |
| qwen35_9b | en | invalid_wrong | 0.667 | 0.208 |
| qwen35_9b | zh | valid_correct | 1.000 | 2.667 |
| qwen35_9b | zh | invalid_correct | 0.667 | 1.479 |
| qwen35_9b | zh | valid_masked | 1.000 | 2.021 |
| qwen35_9b | zh | invalid_masked | 0.667 | 1.271 |
| qwen35_9b | zh | valid_wrong | 1.000 | 1.646 |
| qwen35_9b | zh | invalid_wrong | 1.000 | 1.042 |
| qwen3_14b_base | en | valid_correct | 0.667 | 1.958 |
| qwen3_14b_base | en | invalid_correct | 0.667 | 1.125 |
| qwen3_14b_base | en | valid_masked | 0.667 | 2.250 |
| qwen3_14b_base | en | invalid_masked | 0.667 | 1.208 |
| qwen3_14b_base | en | valid_wrong | 0.333 | -0.125 |
| qwen3_14b_base | en | invalid_wrong | 0.333 | -0.375 |
| qwen3_14b_base | zh | valid_correct | 1.000 | 1.375 |
| qwen3_14b_base | zh | invalid_correct | 1.000 | 0.792 |
| qwen3_14b_base | zh | valid_masked | 1.000 | 1.084 |
| qwen3_14b_base | zh | invalid_masked | 0.667 | 0.500 |
| qwen3_14b_base | zh | valid_wrong | 1.000 | 0.875 |
| qwen3_14b_base | zh | invalid_wrong | 0.667 | 0.542 |

## Lexical-Error Margin Effect / 词汇错误对边际的影响

Negative delta means the invalid lexical phrase lowers the verifier's Yes-vs-No margin, even if it does not cross the rejection threshold. / delta 为负表示无效词汇短语降低了 verifier 的 Yes 相对 No 边际，即使没有越过拒绝阈值。

| verifier | prompt | answer condition | valid yes | invalid yes | invalid-valid margin delta |
|---|---|---|---:|---:|---:|
| gemma4_e4b_it | en | correct | 1.000 | 1.000 | -0.375 |
| gemma4_e4b_it | en | masked | 1.000 | 1.000 | -0.833 |
| gemma4_e4b_it | en | wrong | 0.667 | 0.667 | -0.375 |
| gemma4_e4b_it | zh | correct | 1.000 | 1.000 | -0.694 |
| gemma4_e4b_it | zh | masked | 1.000 | 1.000 | -1.542 |
| gemma4_e4b_it | zh | wrong | 1.000 | 0.667 | -0.583 |
| qwen35_27b | en | correct | 1.000 | 1.000 | -0.958 |
| qwen35_27b | en | masked | 1.000 | 1.000 | -1.104 |
| qwen35_27b | en | wrong | 1.000 | 1.000 | -0.792 |
| qwen35_27b | zh | correct | 1.000 | 0.667 | -0.917 |
| qwen35_27b | zh | masked | 1.000 | 0.667 | -1.167 |
| qwen35_27b | zh | wrong | 1.000 | 0.667 | -0.750 |
| qwen35_9b | en | correct | 1.000 | 0.667 | -1.812 |
| qwen35_9b | en | masked | 1.000 | 0.667 | -0.917 |
| qwen35_9b | en | wrong | 1.000 | 0.667 | -0.292 |
| qwen35_9b | zh | correct | 1.000 | 0.667 | -1.187 |
| qwen35_9b | zh | masked | 1.000 | 0.667 | -0.750 |
| qwen35_9b | zh | wrong | 1.000 | 1.000 | -0.604 |
| qwen3_14b_base | en | correct | 0.667 | 0.667 | -0.833 |
| qwen3_14b_base | en | masked | 0.667 | 0.667 | -1.042 |
| qwen3_14b_base | en | wrong | 0.333 | 0.333 | -0.250 |
| qwen3_14b_base | zh | correct | 1.000 | 1.000 | -0.584 |
| qwen3_14b_base | zh | masked | 1.000 | 0.667 | -0.583 |
| qwen3_14b_base | zh | wrong | 1.000 | 0.667 | -0.333 |

## Human-Readable Takeaways / 人话结论

- The local lexical error almost always lowers the Yes-vs-No margin, so the verifier state is not completely blind to the error. / 局部词汇错误几乎总会压低 Yes-vs-No 边际，说明 verifier 状态并非完全看不见错误。
- The margin reduction often does not cross zero, especially when the final answer remains correct; this is the threshold/objective mismatch. / 但边际下降经常没有跨过 0，尤其最终答案仍正确时；这就是阈值/目标错配。
- Wrong or missing final-answer lines change process-only margins, so even a prompt that says 'judge process only' still partly uses answer-format evidence. / 错误或缺失答案行会改变只审过程的边际，说明“只审过程”的提示仍会混入答案/格式证据。
