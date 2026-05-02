# E30 Non-Discount Verifier Summary / E30 非折扣 verifier 总结

Subset / 子集: `data/processed/e30_non_discount_verifier_subset_20260427.jsonl` contains one valid sibling and one ACPI sibling for the inequality-boundary row. / 子集包含一个有效 sibling 与一个不等式边界 ACPI sibling。

## Absolute Verifier / 绝对式 verifier

| verifier | mode | prompt | n | acc | yes rate | ACPI false accept | mean margin |
|---|---|---|---:|---:|---:|---:|---:|
| gemma4_e4b_it | process_only | en | 2 | 0.500 | 1.000 | 1.000 | 6.875 |
| gemma4_e4b_it | process_only | zh | 2 | 0.500 | 1.000 | 1.000 | 8.781 |
| gemma4_e4b_it | training_candidate | en | 2 | 0.500 | 1.000 | 1.000 | 7.125 |
| gemma4_e4b_it | training_candidate | zh | 2 | 0.500 | 1.000 | 1.000 | 7.250 |
| qwen35_27b | process_only | en | 2 | 0.500 | 1.000 | 1.000 | 3.594 |
| qwen35_27b | process_only | zh | 2 | 0.500 | 1.000 | 1.000 | 1.937 |
| qwen35_27b | training_candidate | en | 2 | 0.500 | 1.000 | 1.000 | 0.938 |
| qwen35_27b | training_candidate | zh | 2 | 0.500 | 1.000 | 1.000 | 0.500 |
| qwen35_9b | process_only | en | 2 | 0.500 | 1.000 | 1.000 | 2.781 |
| qwen35_9b | process_only | zh | 2 | 0.500 | 1.000 | 1.000 | 1.969 |
| qwen35_9b | training_candidate | en | 2 | 0.500 | 1.000 | 1.000 | 2.281 |
| qwen35_9b | training_candidate | zh | 2 | 0.500 | 1.000 | 1.000 | 1.625 |
| qwen3_14b_base | process_only | en | 2 | 0.500 | 1.000 | 1.000 | 2.062 |
| qwen3_14b_base | process_only | zh | 2 | 0.500 | 1.000 | 1.000 | 0.938 |
| qwen3_14b_base | training_candidate | en | 2 | 0.500 | 1.000 | 1.000 | 2.687 |
| qwen3_14b_base | training_candidate | zh | 2 | 0.500 | 1.000 | 1.000 | 0.563 |

## Contrastive Verifier / 对比式 verifier

| verifier | rows | acc | mean target margin | order behavior |
|---|---:|---:|---:|---|
| gemma4_e4b_it | 4 | 0.500 | -0.078 | en/bad_A->A, en/bad_B->A, zh/bad_A->A, zh/bad_B->A |
| qwen35_27b | 4 | 0.500 | 0.239 | en/bad_A->A, en/bad_B->A, zh/bad_A->A, zh/bad_B->A |
| qwen35_9b | 4 | 1.000 | 0.188 | en/bad_A->A, en/bad_B->B, zh/bad_A->A, zh/bad_B->B |
| qwen3_14b_base | 4 | 0.500 | -0.062 | en/bad_A->B, en/bad_B->B, zh/bad_A->B, zh/bad_B->B |

## Human-Readable Takeaways / 人话结论

- All four absolute verifiers accepted the non-discount ACPI row under both English and Chinese prompts. / 四个绝对式 verifier 在中英提示下都接受了这条非折扣 ACPI。
- Contrastive verification was mixed: Qwen3.5-9B selected the invalid sibling in both orders, while Gemma4 and Qwen3.5-27B showed A-position bias and Qwen14 showed B-position bias. / 对比式结果混合：Qwen3.5-9B 两种顺序都能选中无效 sibling，Gemma4 与 Qwen3.5-27B 有 A 位置偏置，Qwen14 有 B 位置偏置。
- This mirrors S6: absolute Yes/No is over-permissive, while sibling comparison can reveal signal but must be order-balanced. / 这与 S6 一致：绝对 Yes/No 过宽，对比式能暴露信号但必须做顺序平衡。

## Error-Span Extraction / 错误 span 抽取

| verifier | best useful signal | main failure |
|---|---|---|
| qwen3_14b_base | locate-only in English/Chinese correctly quoted `between 3 and 7, inclusive` on the invalid row. / 仅定位提示能正确引用无效短语。 | locate-then-judge switched back to `NONE Process-valid: Yes`, so explicit judgement still over-accepted. / 定位后判断又回到接受。 |
| qwen35_9b | Chinese locate-only correctly identified `between 3 and 7, inclusive`. / 中文仅定位能指出错误。 | English locate-only produced meta text; locate-then-judge accepted. / 英文仅定位输出元文本，定位后判断接受。 |
| gemma4_e4b_it | English locate-then-judge surfaced the bad phrase once. / 英文定位后判断有一次暴露坏短语。 | Most outputs were format-unstable or judged the trace correct. / 多数输出格式不稳或判为正确。 |
| qwen35_27b | Valid sibling was usually marked `NONE`. / 有效 sibling 通常被标为 `NONE`。 | Invalid sibling was also marked `NONE` or meta text; it did not localize this non-discount error. / 无效 sibling 也被标为 `NONE` 或元文本，未定位错误。 |

Human-readable point / 人话解释：for the non-discount inequality ACPI, span localization can expose the precise phrase under locate-only prompting, but adding a final `Process-valid` judgement again pulls the model toward accepting the trace. This is the same “local evidence exists, final decision underuses it” pattern as E28/E29, but on a non-discount task. / 对这条非折扣不等式 ACPI，单独要求定位时可以暴露精确短语；但一旦要求最终 `Process-valid` 判断，模型又倾向接受。这与 E28/E29 的“局部证据存在但最终决策未充分使用”模式一致，只是任务不再是折扣。
