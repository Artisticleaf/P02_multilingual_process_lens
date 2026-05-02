# E31 Non-Discount Error-Span Extraction Summary / E31 非折扣错误 span 抽取总结

Results / 结果目录: `results/E31_non_discount_error_span_verifier`.

E31 repeats error-span prompting on the five controlled non-discount traps. It asks whether a verifier can point to the local bad phrase, and whether adding an explicit `Process-valid` decision changes behavior. / E31 在 5 类受控非折扣陷阱上重复错误 span 提示，检查 verifier 能否指出局部坏短语，以及加入显式 `Process-valid` 判断后行为是否改变。

## Overall / 总体

| verifier | mode | prompt | n | span acc | invalid span hit | valid NONE rate | judgement coverage | judgement acc | invalid reject rate | located-but-accepted |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gemma4_e4b_it | locate_only | en | 30 | 0.267 | 0.200 | 0.333 | 0.000 |  |  | 0 |
| gemma4_e4b_it | locate_only | zh | 30 | 0.300 | 0.533 | 0.067 | 0.000 |  |  | 0 |
| gemma4_e4b_it | locate_then_judge | en | 30 | 0.267 | 0.533 | 0.000 | 0.267 | 0.500 | 0.333 | 1 |
| gemma4_e4b_it | locate_then_judge | zh | 30 | 0.033 | 0.067 | 0.000 | 0.033 | 1.000 | 1.000 | 0 |
| qwen35_27b | locate_only | en | 30 | 0.033 | 0.067 | 0.000 | 0.000 |  |  | 0 |
| qwen35_27b | locate_only | zh | 30 | 0.033 | 0.067 | 0.000 | 0.000 |  |  | 0 |
| qwen35_27b | locate_then_judge | en | 30 | 0.700 | 0.733 | 0.667 | 1.000 | 0.800 | 0.933 | 0 |
| qwen35_27b | locate_then_judge | zh | 30 | 0.600 | 0.800 | 0.400 | 1.000 | 0.700 | 1.000 | 0 |
| qwen35_9b | locate_only | en | 30 | 0.100 | 0.200 | 0.000 | 0.000 |  |  | 0 |
| qwen35_9b | locate_only | zh | 30 | 0.267 | 0.400 | 0.133 | 0.000 |  |  | 0 |
| qwen35_9b | locate_then_judge | en | 30 | 0.467 | 0.467 | 0.467 | 0.800 | 0.667 | 0.833 | 1 |
| qwen35_9b | locate_then_judge | zh | 30 | 0.667 | 0.667 | 0.667 | 1.000 | 0.800 | 1.000 | 0 |
| qwen3_14b_base | locate_only | en | 30 | 0.400 | 0.733 | 0.067 | 0.000 |  |  | 0 |
| qwen3_14b_base | locate_only | zh | 30 | 0.600 | 0.800 | 0.400 | 0.000 |  |  | 0 |
| qwen3_14b_base | locate_then_judge | en | 30 | 0.600 | 0.600 | 0.600 | 1.000 | 0.800 | 0.867 | 0 |
| qwen3_14b_base | locate_then_judge | zh | 30 | 0.533 | 0.533 | 0.533 | 1.000 | 0.700 | 0.867 | 0 |

## Invalid-Trace Localization by Task / 按任务看无效 trace 定位

| verifier | prompt | task | invalid n | span hit | reject coverage | reject rate | located-but-accepted n |
|---|---|---|---:|---:|---:|---:|---:|
| gemma4_e4b_it | en | comb_choose_unordered | 3 | 1.000 | 0.333 | 0.000 | 1 |
| gemma4_e4b_it | en | geometry_diameter_area | 3 | 0.000 | 0.000 |  | 0 |
| gemma4_e4b_it | en | inequality_no_more_than | 3 | 0.667 | 1.000 | 0.667 | 0 |
| gemma4_e4b_it | en | ratio_boys_girls_2_3 | 3 | 1.000 | 0.000 |  | 0 |
| gemma4_e4b_it | en | unit_dozen_pairs | 3 | 0.000 | 0.667 | 0.000 | 0 |
| gemma4_e4b_it | zh | comb_choose_unordered | 3 | 0.000 | 0.000 |  | 0 |
| gemma4_e4b_it | zh | geometry_diameter_area | 3 | 0.000 | 0.000 |  | 0 |
| gemma4_e4b_it | zh | inequality_no_more_than | 3 | 0.333 | 0.333 | 1.000 | 0 |
| gemma4_e4b_it | zh | ratio_boys_girls_2_3 | 3 | 0.000 | 0.000 |  | 0 |
| gemma4_e4b_it | zh | unit_dozen_pairs | 3 | 0.000 | 0.000 |  | 0 |
| qwen35_27b | en | comb_choose_unordered | 3 | 1.000 | 1.000 | 1.000 | 0 |
| qwen35_27b | en | geometry_diameter_area | 3 | 1.000 | 1.000 | 1.000 | 0 |
| qwen35_27b | en | inequality_no_more_than | 3 | 0.667 | 1.000 | 0.667 | 0 |
| qwen35_27b | en | ratio_boys_girls_2_3 | 3 | 1.000 | 1.000 | 1.000 | 0 |
| qwen35_27b | en | unit_dozen_pairs | 3 | 0.000 | 1.000 | 1.000 | 0 |
| qwen35_27b | zh | comb_choose_unordered | 3 | 1.000 | 1.000 | 1.000 | 0 |
| qwen35_27b | zh | geometry_diameter_area | 3 | 1.000 | 1.000 | 1.000 | 0 |
| qwen35_27b | zh | inequality_no_more_than | 3 | 1.000 | 1.000 | 1.000 | 0 |
| qwen35_27b | zh | ratio_boys_girls_2_3 | 3 | 1.000 | 1.000 | 1.000 | 0 |
| qwen35_27b | zh | unit_dozen_pairs | 3 | 0.000 | 1.000 | 1.000 | 0 |
| qwen35_9b | en | comb_choose_unordered | 3 | 0.667 | 0.667 | 0.500 | 1 |
| qwen35_9b | en | geometry_diameter_area | 3 | 0.667 | 1.000 | 1.000 | 0 |
| qwen35_9b | en | inequality_no_more_than | 3 | 0.000 | 0.333 | 0.000 | 0 |
| qwen35_9b | en | ratio_boys_girls_2_3 | 3 | 1.000 | 1.000 | 1.000 | 0 |
| qwen35_9b | en | unit_dozen_pairs | 3 | 0.000 | 1.000 | 1.000 | 0 |
| qwen35_9b | zh | comb_choose_unordered | 3 | 0.667 | 1.000 | 1.000 | 0 |
| qwen35_9b | zh | geometry_diameter_area | 3 | 1.000 | 1.000 | 1.000 | 0 |
| qwen35_9b | zh | inequality_no_more_than | 3 | 0.667 | 1.000 | 1.000 | 0 |
| qwen35_9b | zh | ratio_boys_girls_2_3 | 3 | 1.000 | 1.000 | 1.000 | 0 |
| qwen35_9b | zh | unit_dozen_pairs | 3 | 0.000 | 1.000 | 1.000 | 0 |
| qwen3_14b_base | en | comb_choose_unordered | 3 | 1.000 | 1.000 | 1.000 | 0 |
| qwen3_14b_base | en | geometry_diameter_area | 3 | 1.000 | 1.000 | 1.000 | 0 |
| qwen3_14b_base | en | inequality_no_more_than | 3 | 0.000 | 1.000 | 0.333 | 0 |
| qwen3_14b_base | en | ratio_boys_girls_2_3 | 3 | 1.000 | 1.000 | 1.000 | 0 |
| qwen3_14b_base | en | unit_dozen_pairs | 3 | 0.000 | 1.000 | 1.000 | 0 |
| qwen3_14b_base | zh | comb_choose_unordered | 3 | 0.667 | 1.000 | 1.000 | 0 |
| qwen3_14b_base | zh | geometry_diameter_area | 3 | 1.000 | 1.000 | 1.000 | 0 |
| qwen3_14b_base | zh | inequality_no_more_than | 3 | 0.000 | 1.000 | 0.333 | 0 |
| qwen3_14b_base | zh | ratio_boys_girls_2_3 | 3 | 1.000 | 1.000 | 1.000 | 0 |
| qwen3_14b_base | zh | unit_dozen_pairs | 3 | 0.000 | 1.000 | 1.000 | 0 |

## Located But Accepted Examples / 已定位但仍接受的例子

| verifier | idx | prompt | task | output excerpt |
|---|---:|---|---|---|
| gemma4_e4b_it | 310026 | en | comb_choose_unordered | 10 Process-valid: Yes Problem: 从5名学生中选2名组成不区分顺序的委员会。有多少种选法？ Reasoning trace: Because two students are selected, the order matters. There are 5 choices for the first student and 4 f |
| qwen35_9b | 310028 | en | comb_choose_unordered | "Because two students are selected, the order matters." Process-valid: Yes  Problem: 从5名学生中选2名组成不区分顺序的委员会。有多少种选法？ Reasoning trace: Because two students are selected, the order matt |

## Human-Readable Takeaways / 人话结论

- The controlled non-discount errors are often localizable under a stronger objective: Qwen3.5-27B locate-then-judge hits 0.733/0.800 invalid spans and rejects 0.933/1.000 invalid rows in English/Chinese prompts. / 在更强的“先定位再判断”目标下，受控非折扣错误常能被定位：Qwen3.5-27B 中英提示的无效 span 命中率为 0.733/0.800，无效行拒绝率为 0.933/1.000。
- This contrasts with E31 absolute verification, where the same Qwen3.5-27B process-only verifier still accepts all English ACPI rows and 0.800 Chinese ACPI rows. / 这和 E31 绝对式验证形成对照：同一个 Qwen3.5-27B 的 process-only 绝对式 verifier 仍接受全部英文 ACPI 行和 0.800 中文 ACPI 行。
- Qwen14 is the cleanest smaller diagnostic model here: locate-then-judge rejects most invalid rows and gives usable span evidence, while absolute verification is already stricter than Gemma4/Qwen3.5-27B. / Qwen14 是本轮最干净的小模型诊断器：定位后判断能拒绝多数无效行并给出可用 span，而它的绝对式验证也比 Gemma4/Qwen3.5-27B 更严格。
- Locate-only prompting is not a stable benchmark for the post-trained Qwen3.5 models because outputs often include hidden-thinking scaffolds or copied task text; it is a diagnostic, not a final metric. / 对后训练 Qwen3.5 模型，纯 locate-only 不是稳定基准，因为输出常夹带 hidden-thinking 脚手架或复制题干；它更适合作为诊断而非最终指标。
- Unit semantics (`dozen`/pairs) remain hard to localize automatically: many models reject the trace but quote the downstream arithmetic rather than the earliest bad unit phrase. / 单位语义（打/双）仍难自动定位：很多模型能拒绝 trace，但引用的是后续算术而不是最早的坏单位短语。
