# Absolute Verifier, Language-Mixing Evolution, and Next Plan / 绝对式 verifier、语言混合演进与下一步规划

Date / 日期: 2026-04-28 CST

Status / 状态: discussion-only planning; no new experiment launched. / 仅讨论与规划；未启动新实验。

## 1. Can absolute Yes/No make the model ignore process and only look at the final answer? / absolute Yes/No 是否会让模型忽略过程、只看最终答案？

Short answer / 简短结论：yes, it can encourage final-answer anchoring, but the current evidence does not support a pure "only final answer" story. It supports a weaker and more precise claim: under a pointwise Yes/No objective, the verifier underweights local process errors when the final answer is correct and the trace is fluent. / 会，它可能鼓励最终答案锚定；但现有证据不支持“模型完全只看最终答案”。更准确的说法是：在单点 Yes/No 目标下，当最终答案正确且 trace 表面流畅时，verifier 会低估局部过程错误。

The official E42 absolute prompt already tells the model to check process, not answer only. / E42 官方 absolute prompt 已经明确要求检查过程，而不是只看答案：

```text
You are auditing a mathematical reasoning trace. Judge only whether the mathematical reasoning steps are valid; do not penalize missing final-answer formatting, truncation, or extra text after the answer. If any mathematical step is wrong, answer No. If the visible reasoning steps are mathematically valid, answer Yes. Answer only Yes or No.
Problem: ...
Reasoning trace: ...
Are the visible reasoning steps mathematically valid? Answer:
```

中文解释：这个 prompt 已经说了“只判断数学推理步骤是否有效”“任何数学步骤错就回答 No”“不要因为 final-answer 格式问题惩罚”。所以 E42 的 over-accept 不是因为我们没有要求它看过程，而是在已经要求看过程的情况下，它仍然会被最终答案正确、后续修正、语言流畅性或 Yes 阈值牵引。 / 中文解释：这个 prompt 已经说了“只判断数学推理步骤是否有效”“任何数学步骤错就回答 No”“不要因为 final-answer 格式问题惩罚”。所以 E42 的过度接受不是因为我们没有要求它看过程，而是在已经要求看过程的情况下，它仍会被最终答案正确、后续修正、语言流畅性或 Yes 阈值牵引。

Observed E42 P0 facts / 已观察到的 E42 P0 事实：

- P0 core models accept 50% of invalid-correct controlled traces under absolute Yes/No, while accepting 100% of valid traces. / P0 核心模型在 absolute Yes/No 下接受 50% 的 invalid-correct 受控 trace，同时接受 100% valid trace。
- The same P0 models reach 100% contrastive sibling accuracy on the same controlled pairs. / 同一批 P0 模型在同一批受控 pair 上 sibling comparison 达到 100%。
- If the model used final answer only, it should accept all invalid-correct traces; it does not. Some errors such as mean/median-like rows are rejected. / 如果模型完全只看最终答案，它应该接受所有 invalid-correct trace；但事实不是这样，一些错误如 mean/median 类会被拒绝。
- Therefore the failure is better described as final-answer anchoring plus process-signal underuse, not pure process blindness. / 因此失败更应描述为“最终答案锚定 + 过程信号未充分使用”，不是纯粹过程失明。

## 2. If we ask the model to check more carefully, can it find all errors? / 如果让模型更仔细检查过程，能否找出所有错误？

Current answer / 当前回答：not guaranteed. Asking more carefully can help, but it changes the objective and can introduce new failures such as malformed outputs, self-correction, verbosity bias, or parser instability. / 不能保证。更仔细的 prompt 可能有帮助，但它改变了 objective，也可能引入格式坏、自我修正、冗长偏差或解析不稳定。

What we already know / 已知事实：

- The absolute prompt is already strict and process-focused, yet over-acceptance remains. / absolute prompt 已经很严格、聚焦过程，但过度接受仍存在。
- Sibling comparison is a stronger objective because it removes final-answer and task-context confounds by placing valid and invalid same-answer traces side by side. / sibling comparison 是更强目标，因为它把同答案 valid/invalid trace 并排，抵消最终答案和题目上下文混杂。
- Locate-only or locate-then-judge objectives are useful diagnostics, but historical runs show formatting artifacts and model-specific instability, so they should be reported as diagnostic, not as the only mitigation. / 仅定位或先定位再判断有诊断价值，但历史运行显示格式 artifact 和模型不稳定，所以应作为诊断结果，而不是唯一缓解方案。

Plain-language interpretation / 说人话解释：

Asking "Is this solution valid? Yes or No" is like asking a tired grader to pass/fail one answer sheet. Even if the instruction says to check every step, a correct final answer and a plausible-looking explanation can push the grader toward pass. Asking "Which of these two same-answer solutions has the bad step?" makes the local difference visible and forces the grader to compare process, so the hidden process signal is easier to use. / 问“这份解答对不对？Yes/No”像让一个疲劳阅卷人单独给一份作业判及格/不及格。即使要求检查每一步，最终答案正确、解释看起来顺，也可能把判断推向“通过”。问“这两份同答案解答哪份步骤错？”会让局部差异变得显眼，迫使模型比较过程，因此更容易调用隐藏的过程信号。

Next implication / 下一步含义：we need an objective ladder, not just one stronger prompt. The ladder should compare pointwise Yes/No, strict step checklist, span localization, locate-then-judge, sibling comparison, and calibrated thresholds on the same rows. / 我们需要一条 objective 梯度，而不是只换一个“更仔细”的 prompt。应在同一批样本上比较单点 Yes/No、逐步 checklist、错误 span 定位、先定位再判断、sibling comparison 和校准阈值。

## 3. How language-mixing evolved into the current project / language mixing 如何发展到今天

Stage 1: natural multilingual lexical ACPI seeds / 阶段 1：自然多语言词汇 ACPI 种子

- Early evidence centered on real generated traces such as Chinese discount wording `打八折`, where a model lexicalized the phrase as an English-like "80% discount" while computing a pay-80% answer. / 早期证据集中在真实生成 trace，例如中文 `打八折` 被模型词汇化成类似英文的 “80% discount”，但计算却按支付 80% 走。
- This made the project about surface lexicalization and language route, not only arithmetic mistakes. / 这让项目主题从普通算错变成表层词汇化与语言路径问题。

Stage 2: sibling and hidden-span diagnostics / 阶段 2：sibling 与 hidden-span 诊断

- The project then built valid/invalid sibling pairs and used absolute verifier, contrastive verifier, and residual/module span patching to ask whether process/error-span signals exist. / 随后项目构造 valid/invalid sibling pair，用 absolute verifier、contrastive verifier 和 residual/module span patch 检查过程/错误 span 信号是否存在。
- Some same-route lexical cases were hard, showing that language and process semantics can be entangled rather than cleanly separated. / 一些同语言路径词汇样例很难，说明语言和过程语义会混杂，而不是总能干净分离。

Stage 3: non-discount and controlled counterfactuals / 阶段 3：非折扣与受控反事实

- E30/E31 moved beyond discount into ratio denominator, inequality boundary, unit semantics, geometry, and combinatorics. / E30/E31 从折扣扩展到比例分母、不等式边界、单位语义、几何和组合。
- This showed the risk was not purely a discount artifact, but also showed uneven behavior across error families. / 这说明风险不是纯折扣 artifact，但也显示不同错误族强弱不均。

Stage 4: E39/E42 official controlled generalization / 阶段 4：E39/E42 官方受控泛化

- E39 created 12 controlled surface-semantic trap families with valid/invalid and final-correct/final-masked/final-wrong variants. / E39 构造 12 类受控表层语义陷阱，每类有 valid/invalid 与最终答案正确/遮盖/错误变体。
- E42 fixed the trace content and intervened on verifier objective: absolute process-only vs order-balanced sibling comparison. / E42 固定 trace 内容，只干预 verifier 目标：absolute process-only 与顺序平衡 sibling comparison。
- The current official P0 result is conservative but strong: absolute over-accept remains; sibling comparison recovers the errors. / 当前官方 P0 结果保守但强：absolute 过度接受仍存在；sibling comparison 能恢复错误。

Stage 5: style and cross-family controls / 阶段 5：风格与跨家族控制

- E43 checked paraphrase transfer in hidden states; E59c asked P0 models to rewrite traces into their own style and then used source-blind self/cross verification. / E43 检查 hidden state 的跨改写迁移；E59c 让 P0 模型把 trace 改写成自身风格，再做来源盲化自审/互审。
- E59c showed that the absolute over-acceptance pattern is not only a fixed human-writing style or one-model self-preference artifact. / E59c 显示 absolute 过度接受不只是固定人工文风或单模型自偏好 artifact。

## 4. Next experiments / 后续实验规划

### E53 answer-anchor ablation / 答案锚定消融

Question / 问题：absolute over-accept 到底有多少来自 final answer being correct? / absolute 过度接受有多少来自最终答案正确？

Design / 设计：for the same trace, score four variants: final answer shown, final answer removed, final answer masked, final answer wrong. Keep the process text fixed. / 对同一 trace 评分四种版本：显示最终答案、移除最终答案、遮盖最终答案、改错最终答案；过程文本保持不变。

Expected information / 预期信息：if invalid acceptance collapses when the answer is removed or wrong, final-answer anchoring is a main driver. If it remains high, process underchecking is deeper than answer anchoring. / 如果移除或改错答案后 invalid 接受率大幅下降，最终答案锚定是主因；如果仍高，说明过程检查问题比答案锚定更深。

### E60 process-inspection objective ladder / 过程检查 objective 梯度

Question / 问题："更仔细检查"到底能修复多少？哪种检查形式最稳？ / “更仔细检查”到底能修复多少？哪种检查形式最稳？

Design / 设计：on the same rows, compare: minimal absolute Yes/No, current strict process-only Yes/No, step-by-step checklist, error-span localization, locate-then-judge, sibling comparison, and calibrated threshold. / 在同一批样本上比较：最小 absolute Yes/No、当前严格 process-only Yes/No、逐步 checklist、错误 span 定位、先定位再判断、sibling comparison 和校准阈值。

Audit / 审计：malformed outputs must count as failures; generated rationales must not be used as labels unless manually audited. / 格式坏必须计为失败；生成解释不能未经人审直接当标签。

### E54 parameterized no-leak generalization / 参数化无泄露泛化

Question / 问题：现象是否跨错误族存在，而不是 discount 或少数短题特例？ / 现象是否跨错误族存在，而不是 discount 或少数短题特例？

Design / 设计：build parameterized families covering aggregation, percentage base, unit/scale, quantifier/inequality, order/comparison, rate/ratio, algebraic transformation, counting/combinatorics, geometry notation, table interpretation, code execution traces, and proof validity. / 构造参数化样本族，覆盖聚合、百分比基准、单位/数量级、量词/不等式、顺序/比较、速率/比例、代数变形、计数/组合、几何符号、表格解读、代码执行 trace 和证明有效性。

No-leak rule / 无泄露规则：known error spans and gold labels are used only for post-hoc audit, not in model prompts. / 已知错误 span 和 gold 标签只用于事后审计，不进入模型 prompt。

### E61 language-route and error-taxonomy grid / 语言路径与错误类型网格

Question / 问题：language mixing 到底是风险来源、放大器，还是只是表面形式？ / language mixing 到底是风险来源、放大器，还是只是表面形式？

Design / 设计：for selected task families, cross problem language, reasoning language, verifier prompt language, and error-language location: zh->zh, zh->en, en->zh, en->en, and mixed term traces. Keep final answer and process label fixed. / 对选定任务族交叉题目语言、推理语言、verifier prompt 语言和错误所在语言：zh->zh、zh->en、en->zh、en->en 与混合术语 trace；保持最终答案和过程标签固定。

Expected information / 预期信息：separates surface language effects from process semantics and tests whether some errors become easier or harder when the wrong claim is lexicalized in another language. / 区分表层语言效应与过程语义，并测试错误 claim 用另一种语言词汇化后是否更难或更容易被发现。

### E55/E56 mechanism deepening / 机制深化

Question / 问题：hidden residual process evidence 如何影响 Yes/No logits 和 A/B logits？attention/MLP/residual 谁贡献？ / hidden residual 过程证据如何影响 Yes/No logits 和 A/B logits？attention、MLP、residual 谁贡献？

Design / 设计：E55 residual-to-logit mediation first; then E56 component decomposition over layers/positions identified by E55. / 先做 E55 residual-to-logit 中介；再在 E55 找到的层/位置上做 E56 组件分解。

### E57/E58/E59 expansion / 困难题、筛选模拟与跨家族扩展

- E57: harvest P0 final-correct hard-task traces before process audit; do not use P2 Qwen2.5-Math as main evidence. / E57：先在 P0 上采困难题 final-correct trace，再做人审过程；不把 P2 Qwen2.5-Math 当主证据。
- E58: simulate outcome-only, absolute-verifier, and sibling-verifier filters to see which one amplifies ACPI. / E58：模拟只看答案、absolute verifier、sibling verifier 三种筛选器，看哪种会放大 ACPI。
- E59: after external P0 smoke tests, extend source-blind cross-family verifier matrices. / E59：外部 P0 smoke test 通过后，扩展来源盲化跨家族 verifier 矩阵。

## 5. Recommended order / 推荐顺序

1. E53 answer-anchor ablation. / E53 答案锚定消融。
2. E60 process-inspection objective ladder. / E60 过程检查 objective 梯度。
3. E54 parameterized no-leak generalization. / E54 参数化无泄露泛化。
4. E61 language-route grid. / E61 语言路径网格。
5. E55 residual-to-logit mediation. / E55 residual-to-logit 中介。
6. E56 component decomposition. / E56 组件分解。
7. E57 hard-task harvesting in the background. / E57 困难题采样后台运行。
8. E58/E59 after broader trace pools and external model smoke tests. / E58/E59 等更广 trace pool 与外部模型 smoke test 后推进。
