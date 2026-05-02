# E42 E39 Objective Matrix Summary / E42：E39 目标矩阵汇总

Created / 创建时间: 2026-04-28T01:16:37

E42 tests the causal-chain link `verifier objective/threshold -> final decision` on the same 12 E39 surface-semantic families. / E42 在同一批 12 类 E39 表层语义陷阱上检验因果链中的 `verifier 目标/阈值 -> 最终决策` 环节。
The key question is not whether a model can ever detect the error; it is whether a pointwise Yes/No objective uses that evidence as reliably as contrastive or locate-then-judge objectives. / 关键问题不是模型能不能发现错误，而是单点 Yes/No 目标是否像对比式或先定位再判断目标一样可靠地使用这个证据。

## 1. Objective-level result / 目标层结果

| verifier | absolute process ACPI accept EN/ZH | training-candidate ACPI accept EN/ZH | invalid-masked process accept EN/ZH | invalid-wrong process accept EN/ZH | contrastive acc EN/ZH | locate-then-judge invalid span hit EN/ZH | locate-then-judge invalid reject EN/ZH |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen35_9b | 0.750/0.833 | 0.833/0.750 | 0.750/0.667 | 0.083/0.583 | 1.000/0.958 | 0.333/0.833 | 1.000/1.000 |
| qwen3_14b_base | 0.250/0.250 | 0.750/1.000 | 0.250/0.250 | 0.167/0.250 | 0.958/0.958 | 1.000/0.833 | 1.000/0.917 |
| qwen35_27b | 1.000/0.833 | 0.833/0.083 | 0.833/0.333 | 1.000/0.417 | 1.000/1.000 | 0.583/0.750 | 1.000/1.000 |
| gemma4_31b_it | 0.500/0.417 | 0.083/0.083 | 0.333/0.417 | 0.500/0.167 | 0.875/0.875 | 0.417/0.000 | 0.545/0.778 |

Plain-language read / 人话解释：absolute Yes/No often accepts answer-correct process-invalid traces, but contrastive sibling verification is much stronger on the same rows. Locate-then-judge is informative for Qwen models, while Gemma31's generated localization format is unstable. / 绝对式 Yes/No 经常接受答案正确但过程错误的 trace；同一批 row 换成 sibling 对比后明显更强。先定位再判断对 Qwen 模型有信息量，而 Gemma31 的定位生成格式不稳定。

## 2. Calibrated margin evidence / 连续边际证据

| verifier | process EN invalid-valid margin delta | accepted despite negative delta EN | process ZH invalid-valid margin delta | accepted despite negative delta ZH | meaning / 含义 |
|---|---:|---:|---:|---:|---|
| qwen35_9b | -2.594 | 9 / 12 | -1.589 | 10 / 12 | negative delta means the model has graded evidence against the invalid phrase even if the final binary answer accepts / 负 delta 表示模型对无效短语有连续负证据，即使最终二值判断仍接受 |
| qwen3_14b_base | -3.250 | 2 / 11 | -2.021 | 2 / 11 | negative delta means the model has graded evidence against the invalid phrase even if the final binary answer accepts / 负 delta 表示模型对无效短语有连续负证据，即使最终二值判断仍接受 |
| qwen35_27b | -2.458 | 12 / 12 | -2.104 | 10 / 12 | negative delta means the model has graded evidence against the invalid phrase even if the final binary answer accepts / 负 delta 表示模型对无效短语有连续负证据，即使最终二值判断仍接受 |
| gemma4_31b_it | -7.250 | 5 / 11 | -5.168 | 3 / 9 | negative delta means the model has graded evidence against the invalid phrase even if the final binary answer accepts / 负 delta 表示模型对无效短语有连续负证据，即使最终二值判断仍接受 |

## 3. Contrastive objective details / 对比式目标细节

| verifier | overall acc | mean target margin | EN pred-A rate | ZH pred-A rate | EN bad-A/bad-B acc | ZH bad-A/bad-B acc |
|---|---:|---:|---:|---:|---:|---:|
| qwen35_9b | 0.979 | 1.042 | 0.500 | 0.458 | 1.000/1.000 | 0.917/1.000 |
| qwen3_14b_base | 0.958 | 2.029 | 0.458 | 0.458 | 0.917/1.000 | 0.917/1.000 |
| qwen35_27b | 1.000 | 2.202 | 0.500 | 0.500 | 1.000/1.000 | 1.000/1.000 |
| gemma4_31b_it | 0.875 | 3.762 | 0.458 | 0.542 | 0.833/0.917 | 0.917/0.833 |

This table is a direct objective intervention: trace content is unchanged, but the question changes from `is this trace valid?` to `which sibling is invalid?`. / 这张表是直接的目标干预：trace 内容不变，只把问题从“这条是否有效”换成“哪条 sibling 无效”。

## 4. Boundary tasks / 边界任务

| task | input | Qwen35-9B abs EN | Qwen14 abs EN | Qwen35-27B abs EN | Gemma31 abs EN | Qwen35-9B contrastive | Qwen14 contrastive | Gemma31 contrastive |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| coefficient_vs_exponent | en | True (3.062) | False (-0.750) | True (1.500) | True (2.125) | 0.750 | 1.000 | 0.750 |
| each_vs_total | en | False (-0.625) | False (-1.500) | True (0.875) | False (-1.250) | 1.000 | 1.000 | 1.000 |
| log_base_argument | en | True (2.125) | False (-0.250) | True (2.125) | True (2.250) | 1.000 | 1.000 | 1.000 |
| mean_vs_median | en | False (-0.500) | False (-0.750) | True (0.875) | False (-2.000) | 1.000 | 1.000 | 1.000 |
| percent_increase_vs_percent_of | en | True (0.875) | True (0.875) | True (1.750) | True (5.750) | 1.000 | 1.000 | 1.000 |
| prob_without_replacement | en | False (-1.250) | False (-1.875) | True (0.250) | False (-6.250) | 1.000 | 1.000 | 0.750 |
| range_vs_average | en | True (0.875) | False (-1.000) | True (1.625) | False (-3.625) | 1.000 | 1.000 | 1.000 |
| reciprocal_vs_additive_inverse | en | True (0.500) | False (-0.750) | True (1.000) | True (4.125) | 1.000 | 1.000 | 1.000 |
| round_vs_truncate | en | True (2.562) | True (2.375) | True (3.500) | True (11.938) | 1.000 | 0.500 | 0.750 |
| zh_exclusive_interval | zh | True (0.125) | False (-0.875) | True (2.000) | False (-5.250) | 1.000 | 1.000 | 0.500 |
| zh_perimeter_vs_area | zh | True (0.875) | False (-1.500) | True (1.625) | False (-5.500) | 1.000 | 1.000 | 1.000 |
| zh_yi_wan_unit | zh | True (0.375) | True (0.375) | True (2.500) | True (0.500) | 1.000 | 1.000 | 0.750 |

Boundary read / 边界解释：`round_vs_truncate` remains a hard boundary for Qwen14 in contrastive order `bad_A`, matching E40 where its residual patch was weak. Gemma31 has several contrastive position/format failures even though it often gives large margins when correct. / `round_vs_truncate` 对 Qwen14 仍是边界，尤其 bad_A 顺序；这和 E40 中 residual patch 弱一致。Gemma31 即使正确时 margin 很大，也有若干位置/格式失败。

## 5. Scientific update / 科学更新

- E42 strengthens the causal-chain claim: changing only the verifier objective sharply changes decisions on the same E39 traces. / E42 强化因果链主张：只改变 verifier 目标，同一批 E39 trace 的决策就明显改变。
- The failure is not pure blindness: Qwen35-27B accepts almost all ACPI under absolute English process prompts, yet reaches perfect contrastive accuracy and high locate-then-judge rejection. / 失败不是纯看不见：Qwen35-27B 在英文绝对式只审过程下几乎全接受 ACPI，但对比式达到满分，先定位再判断也能高比例拒绝。
- The objective fix is not automatic: locate-only often fails because models output chain-of-thought or malformed text; Gemma31's localization is especially unstable. / 换目标并不会自动解决：locate-only 常被思考文本或格式错误破坏；Gemma31 的定位输出尤其不稳。
- Answer masking/wrong-answer variants show that final-answer evidence contributes, but the magnitude is model/language dependent rather than a single universal answer-bias constant. / 答案遮蔽/错误答案变体显示最终答案确实参与决策，但强度依赖模型和提示语言，不是一个固定答案偏置常数。

## 6. What this means for next experiments / 下一步实验含义

1. Natural prevalence is now the largest empirical gap: E39/E42 are controlled and causal, but not population-frequency evidence. / 最大经验缺口是自然发生率：E39/E42 是受控因果证据，不是总体频率证据。
2. Mechanism needs to move from residual patch to semantic transfer and steering: E40/E41 show hidden evidence and MLP participation, but not reusable semantic features. / 机制需要从 residual patch 推进到语义迁移与 steering：E40/E41 显示 hidden evidence 和 MLP 参与，但还没证明可复用语义特征。
3. Hard tasks should be conditioned on final-correct traces before ACPI audit; otherwise they mostly measure generator difficulty. / 难题必须先条件化出 final-correct trace 再审 ACPI，否则主要测的是生成难度。
