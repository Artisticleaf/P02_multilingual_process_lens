# E29 Error-Span Extraction Verifier Summary / E29 错误 span 抽取 verifier 总结

Results / 结果目录: `results/E29_error_span_extraction_verifier`.

E29 asks a verifier to name the first invalid phrase before, or together with, a process-validity decision. / E29 要求 verifier 先指出第一处无效短语，或同时给出过程是否有效的判断。

## Overall / 总体

| verifier | mode | prompt | n | span acc | invalid span hit | valid NONE rate | judgement coverage | judgement acc | invalid reject rate | located-but-accepted |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gemma4_e4b_it | locate_only | en | 24 | 0.458 | 0.333 | 0.583 | 0.000 |  |  | 0 |
| gemma4_e4b_it | locate_only | zh | 24 | 0.500 | 0.667 | 0.333 | 0.000 |  |  | 0 |
| gemma4_e4b_it | locate_then_judge | en | 24 | 0.333 | 0.667 | 0.000 | 0.042 | 1.000 |  | 0 |
| gemma4_e4b_it | locate_then_judge | zh | 24 | 0.167 | 0.333 | 0.000 | 0.042 | 0.000 | 0.000 | 1 |
| qwen35_27b | locate_only | en | 24 | 0.042 | 0.083 | 0.000 | 0.000 |  |  | 0 |
| qwen35_27b | locate_only | zh | 24 | 0.000 | 0.000 | 0.000 | 0.000 |  |  | 0 |
| qwen35_27b | locate_then_judge | en | 24 | 0.583 | 0.333 | 0.833 | 0.833 | 0.700 | 0.444 | 0 |
| qwen35_27b | locate_then_judge | zh | 24 | 0.500 | 0.417 | 0.583 | 0.833 | 0.650 | 0.600 | 0 |
| qwen35_9b | locate_only | en | 24 | 0.292 | 0.333 | 0.250 | 0.000 |  |  | 0 |
| qwen35_9b | locate_only | zh | 24 | 0.458 | 0.417 | 0.500 | 0.000 |  |  | 0 |
| qwen35_9b | locate_then_judge | en | 24 | 0.667 | 0.500 | 0.833 | 0.958 | 0.609 | 0.417 | 1 |
| qwen35_9b | locate_then_judge | zh | 24 | 0.667 | 0.500 | 0.833 | 1.000 | 0.708 | 0.583 | 0 |
| qwen3_14b_base | locate_only | en | 24 | 0.375 | 0.667 | 0.083 | 0.000 |  |  | 0 |
| qwen3_14b_base | locate_only | zh | 24 | 0.375 | 0.583 | 0.167 | 0.000 |  |  | 0 |
| qwen3_14b_base | locate_then_judge | en | 24 | 0.500 | 0.417 | 0.583 | 1.000 | 0.542 | 0.500 | 0 |
| qwen3_14b_base | locate_then_judge | zh | 24 | 0.417 | 0.250 | 0.583 | 1.000 | 0.500 | 0.417 | 0 |

## Invalid-Trace Localization by Task / 按任务看无效 trace 定位

| verifier | prompt | task | invalid n | span hit | reject coverage | reject rate | located-but-accepted n |
|---|---|---|---:|---:|---:|---:|---:|
| gemma4_e4b_it | en | disc_25_off_direct | 4 | 0.000 | 0.000 |  | 0 |
| gemma4_e4b_it | en | disc_pay75_en | 4 | 1.000 | 0.000 |  | 0 |
| gemma4_e4b_it | en | seq_dabazhe_pay80 | 4 | 1.000 | 0.000 |  | 0 |
| gemma4_e4b_it | zh | disc_25_off_direct | 4 | 0.000 | 0.000 |  | 0 |
| gemma4_e4b_it | zh | disc_pay75_en | 4 | 0.250 | 0.250 | 0.000 | 1 |
| gemma4_e4b_it | zh | seq_dabazhe_pay80 | 4 | 0.750 | 0.000 |  | 0 |
| qwen35_27b | en | disc_25_off_direct | 4 | 0.000 | 0.750 | 0.000 | 0 |
| qwen35_27b | en | disc_pay75_en | 4 | 1.000 | 1.000 | 1.000 | 0 |
| qwen35_27b | en | seq_dabazhe_pay80 | 4 | 0.000 | 0.500 | 0.000 | 0 |
| qwen35_27b | zh | disc_25_off_direct | 4 | 0.000 | 1.000 | 0.250 | 0 |
| qwen35_27b | zh | disc_pay75_en | 4 | 1.000 | 1.000 | 1.000 | 0 |
| qwen35_27b | zh | seq_dabazhe_pay80 | 4 | 0.250 | 0.500 | 0.500 | 0 |
| qwen35_9b | en | disc_25_off_direct | 4 | 0.250 | 1.000 | 0.000 | 1 |
| qwen35_9b | en | disc_pay75_en | 4 | 1.000 | 1.000 | 1.000 | 0 |
| qwen35_9b | en | seq_dabazhe_pay80 | 4 | 0.250 | 1.000 | 0.250 | 0 |
| qwen35_9b | zh | disc_25_off_direct | 4 | 0.250 | 1.000 | 0.500 | 0 |
| qwen35_9b | zh | disc_pay75_en | 4 | 1.000 | 1.000 | 1.000 | 0 |
| qwen35_9b | zh | seq_dabazhe_pay80 | 4 | 0.250 | 1.000 | 0.250 | 0 |
| qwen3_14b_base | en | disc_25_off_direct | 4 | 0.000 | 1.000 | 0.250 | 0 |
| qwen3_14b_base | en | disc_pay75_en | 4 | 0.500 | 1.000 | 0.500 | 0 |
| qwen3_14b_base | en | seq_dabazhe_pay80 | 4 | 0.750 | 1.000 | 0.750 | 0 |
| qwen3_14b_base | zh | disc_25_off_direct | 4 | 0.000 | 1.000 | 0.250 | 0 |
| qwen3_14b_base | zh | disc_pay75_en | 4 | 0.000 | 1.000 | 0.250 | 0 |
| qwen3_14b_base | zh | seq_dabazhe_pay80 | 4 | 0.750 | 1.000 | 0.750 | 0 |

## Located But Accepted Examples / 已定位但仍接受的例子

| verifier | idx | prompt | task | output excerpt |
|---|---:|---|---|---|
| gemma4_e4b_it | 280016 | zh | disc_pay75_en | $60 题目：一件80美元的夹克按原价75%出售，售价是多少？ 推理过程：1. The jacket is being sold at a 75% discount of its original price. 2. To find the sale price, multiply the original price by the discount per |
| qwen35_9b | 280006 | en | disc_25_off_direct | 售价等于原价减去折扣金额：80 - 20 = 60 美元。 Process-valid: Yes Span: 售价等于原价减去折扣金额：80 - 20 = 60 美元。 Process-valid: Yes Span: 或者，如果打八折（即支付75%的价格）：售价 = 80美元 × 0.75 = 60美元。 Process-valid: |

## Human-Readable Takeaways / 人话结论

- Error-span prompting is more informative than absolute Yes/No because it exposes false positives, wrong rationales, and parse/template failures. / 错误 span 提示比绝对 Yes/No 更有信息量，因为它暴露了误报、错误理由和模板解析失败。
- Qwen-family locate-then-judge prompts detect the `75% discount` trap most reliably, but the `打八折=支付75%` trap remains hard. / Qwen 系在 locate-then-judge 下最稳定识别 `75% discount` 陷阱，但 `打八折=支付75%` 仍难。
- Some models can name a suspicious span yet still mark the process valid, supporting the threshold/objective mismatch story; generation-format instability is a boundary for this experiment. / 有些模型能指出可疑 span 却仍判过程有效，支持阈值/目标错配；生成格式不稳定是本实验边界。
