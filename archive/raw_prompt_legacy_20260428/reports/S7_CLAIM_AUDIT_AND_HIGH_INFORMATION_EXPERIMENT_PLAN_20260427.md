# S7 Claim Audit And High-Information Experiment Plan / S7 主张审计与高信息收益实验计划

Date / 日期: 2026-04-27 CST  
Purpose / 目的: record the stage-level reasoning before launching the next experiment round. / 在启动下一轮实验前，记录阶段性科学判断。

## 1. Current Causal Story / 当前因果故事

We currently model the phenomenon as: / 当前我们把现象建模为：

`surface lexicalization L -> process semantics P -> final answer A -> verifier hidden evidence H -> verifier decision V`

中文解释：表层词汇 `L`，例如 `打八折`、`75% off`、`sold for 75%`，会影响模型写出的过程语义 `P`；最终答案 `A` 有时仍然正确，因此按答案筛选会保留这条 trace；verifier 内部可能有过程错误证据 `H`，但最终 Yes/No 决策 `V` 常因目标/阈值错配而接受。

## 2. Strengths / 优势

- The failure family is concrete rather than generic: pay/off lexical semantics flips, e.g. `打八折/pay80` vs `80% discount/pay20`. / 失败族很具体，不是泛泛说模型会错。
- Real ACPI exists in selected traces: S6 found three paper-grade answer-correct/process-invalid rows. / 选择集真实 ACPI 已存在，S6 有三条论文级样例。
- Absolute verifier over-acceptance is strong: Gemma4, Qwen14, and Qwen3.5-27B accepted all selected S6 ACPI rows under English and Chinese process-only prompts. / 绝对式 verifier 过度接受证据强。
- Hidden-state causality has a strong anchor: Qwen14 support/error span L14 patch moved the margin in the expected direction (`valid->bad +2.750`, `bad->valid -1.000`). / hidden-state 因果证据有强锚点。
- Boundaries are explicit: contrastive position bias, AIME zero-final-correct, and generator prompt/template failures are recorded instead of hidden. / 边界明确，反而提高可信度。

## 3. Weaknesses / 薄弱点

- Current paper-grade ACPI count is small; it can look anecdotal without a larger controlled pair bank. / 当前论文级 ACPI 数量少，需更大受控 pair bank。
- Discount examples are clean but may look narrow; we need other surface-semantic families and hard-task analogues. / 折扣例子清楚但可能显得窄，需要其他表层语义族和难题对应形态。
- Hidden-layer evidence is mostly residual/span-level; it is not yet a head/MLP/feature-level mechanism. / 隐藏层证据主要是 span/residual 级，还不是 head/MLP/feature 级机制。
- Verifier failure is not fully decomposed: we need to separate inability, answer bias, Yes bias, prompt threshold, language prior, and position bias. / verifier 失败原因还没拆细。
- Sibling comparison is useful as a diagnostic but not yet a reliable mitigation policy because of order bias. / sibling 对比有诊断价值，但还不是可靠防护策略。
- Human audit needs a more formal rubric, second-pass sampling, and ideally blind agreement for publication. / 人工审计需要更正式的 rubric 和二次抽样/一致性。

## 4. High-Information Experiments / 高信息收益实验

1. Counterfactual trace editing / 反事实 trace 编辑：only change the local lexical phrase while holding the rest of the trace fixed. / 只改局部词汇短语，其余 trace 不变。
2. Answer masking / 最终答案遮蔽：remove or corrupt the final answer to quantify final-answer bias. / 删除或替换最终答案，量化答案偏置。
3. Error-span extraction verifier / 错误 span 抽取 verifier：ask the verifier to mark the first invalid phrase before or instead of Yes/No. / 要求 verifier 先标出第一处错误短语。
4. Larger lexical minimal-pair bank / 更大词汇最小对样本库：expand beyond discount and add negative controls. / 扩展出折扣外的表层语义族和负控。
5. Mechanism decomposition / 机制分解：decompose robust S6 Qwen14 L14 span into attention, MLP, and possibly SAE/transcoder features. / 把稳健 Qwen14 L14 span 分解到 attention、MLP 和可能的 SAE/transcoder 特征。
6. Objective re-entanglement lens / 目标再纠缠 lens：track process/operator margins from middle layers to output decision. / 追踪中层到输出层的 process/operator margin。
7. Hard-task final-correct conditioning / 难题 final-correct 条件化：sample AIME24/25 until final-correct traces exist, then audit process validity. / 先拿到 final-correct 难题 trace，再审计过程。
8. Order-balanced triangulation policy / 顺序平衡三角测量策略：use A/B order balancing and abstention to turn sibling comparison into a conservative risk filter. / 用顺序平衡和 abstention 把 sibling 对比变成保守风险过滤器。

## 5. Publication-Level Framing / 顶会级表述

Do not claim: “we discovered correct answers can have wrong reasoning.” / 不要声称“我们发现正确答案会有错误推理”。

Safer claim / 更安全主张：

> We isolate and causally test a multilingual surface-lexical ACPI trace-selection failure family. Local lexical semantics can flip the visible process while preserving the final answer; absolute Yes/No verifiers over-accept these traces due to objective/threshold mismatch; selected sibling comparisons and hidden support/error-span patching expose process-error signals that the final verifier decision underuses.
>
> 中文：我们隔离并因果检验一类多语言表层词汇 ACPI 轨迹选择失败。局部词汇语义会翻转可见过程但保留最终答案；绝对式 Yes/No verifier 因目标/阈值错配过度接受这些 trace；选择后的 sibling 对比和 hidden support/error-span patch 能暴露最终 verifier 决策未充分使用的过程错误信号。
