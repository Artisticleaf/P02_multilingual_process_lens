# E43 Next-Stage Mechanism And Generalization Plan / E43 下一阶段机制与泛化实验规划

Date / 日期: 2026-04-28 CST

## 1. Where the claim is strong and where it is still weak / 当前主张的强弱点

**Strong facts / 强事实**

- E39 shows the phenomenon is not just discount wording: 12 controlled surface-semantic families produce answer-correct but process-invalid rows. / E39 说明现象不是折扣词专属：12 类受控表层语义族都能构造答案正确但过程无效的行。
- E42 shows a direct objective intervention: the same traces are often accepted by absolute Yes/No but exposed by contrastive sibling verification. / E42 说明“换目标”本身就是因果干预：同一批 trace 在绝对式 Yes/No 下常被接受，但在 sibling 对比下会被暴露。
- E40/E41 show hidden process evidence exists at residual level and MLP participates, but the effects are distributed. / E40/E41 说明隐藏过程证据存在于 residual state 中，MLP 参与其中，但不是单个模块就能解释。

**Weak facts / 弱点**

- Natural prevalence remains unknown. Controlled E39 tells us the failure is causally possible and model-relevant, not how often it appears in unconstrained model outputs. / 自然发生率仍未知。E39 证明的是可诱发、真实相关，不是总体频率。
- Mechanism is not yet top-tier strong. Residual patching proves local causal sensitivity, but not that a reusable semantic feature/circuit has been found. / 机制还不够顶会强。Residual patch 证明局部因果敏感性，但还没证明找到了可复用语义特征或 circuit。
- Locate objectives are noisy. E42 shows locate-then-judge helps Qwen models, but locate-only and Gemma31 localization can be malformed, so “just ask for a span” is not a finished mitigation. / 定位目标有噪声。E42 显示先定位再判断对 Qwen 有帮助，但 locate-only 和 Gemma31 定位格式不稳，所以“让模型标 span”不是完整修复。
- Hard tasks are still under-conditioned. AIME-style rows without final-correct traces cannot estimate ACPI; they mostly measure generation difficulty. / 难题还没有 final-correct 条件化；没有答案正确 trace 就无法估计 ACPI，只是在测生成难度。

## 2. Literature boundary / 文献边界

Recent work already covers broad process verification and correct-answer/incorrect-reasoning warnings, so our novelty should not be phrased as “CoT can be wrong.” / 近期工作已经覆盖广义过程验证和“答案对但推理错”的提醒，所以我们的创新不能写成“CoT 会错”。

- ProcessBench studies process-error identification in math reasoning traces. / ProcessBench 研究数学推理 trace 中的过程错误识别。
- PRMBench studies fine-grained process reward model evaluation. / PRMBench 研究细粒度 PRM 评测。
- Right Is Not Enough argues that correct final answers are insufficient evidence of sound reasoning. / Right Is Not Enough 指出最终答案正确并不足以证明推理可靠。
- Patchscopes and recent reasoning-circuit/circuit-tracing work raise the bar for hidden-state claims: patching is useful, but strong mechanism claims need transfer, sufficiency/necessity, and ablation controls. / Patchscopes 与 reasoning-circuit/circuit-tracing 工作提高了隐藏层主张的门槛：patch 有用，但强机制主张需要迁移、充分/必要性和消融控制。

Sources / 参考：ProcessBench https://arxiv.org/abs/2412.06559 ; PRMBench https://arxiv.org/abs/2501.03124 ; Right Is Not Enough https://arxiv.org/abs/2506.06877 ; Patchscopes https://arxiv.org/abs/2401.06102 ; Reasoning Circuits in LMs https://aclanthology.org/2025.findings-acl.525/ ; Anthropic circuit tracing https://transformer-circuits.pub/2025/attribution-graphs/methods.html .

**Novelty boundary / 创新边界**：our strongest publishable claim is the conjunction: multilingual/surface-semantic lexicalization creates ACPI trace-selection risk; absolute verifier objectives over-accept; objective changes expose errors; hidden residual/MLP states contain process evidence; and specific boundary cases show when this evidence is re-entangled with final answers or downstream correction. / 最强可发表创新是组合创新：多语言/表层语义词汇化产生 ACPI trace-selection 风险；绝对式 verifier 过度接受；目标改变暴露错误；隐藏 residual/MLP 状态含过程证据；边界样例说明这些证据何时被最终答案或下游修正重新纠缠。

## 3. Next experiments with highest information gain / 下一步最高信息收益实验

### E43. Paraphrase-transfer hidden patch / 跨改写 hidden patch

**Question / 问题**：E40 的 residual span patch 是真正的过程语义信号，还是只对某个固定词面片段有效？ / E40 的 patch 效应是真过程语义，还是固定词面 artifact？

**Design / 设计**：for robust E39 families, create 2-3 valid/invalid paraphrases with the same process semantics but different wording. Patch donor valid/error span vectors from wording A into target wording B. Add mismatched-task donor controls. / 对稳健 E39 家族构造 2-3 套同语义不同表述的 valid/invalid trace，把表述 A 的 valid/error span 向量 patch 到表述 B；加入跨任务错配 donor 作为负控。

**High-value families / 高价值族**：each-vs-total, percent-increase-vs-percent-of, without-replacement, reciprocal-vs-additive-inverse, Chinese strict interval, Chinese perimeter-vs-area. / 优先这些族，因为 E40/E42 里信号强或边界清楚。

**Expected useful outcome / 希望结果**：same-task cross-paraphrase transfer changes margins in the correct direction more than mismatched-task transfer. / 同任务跨改写 transfer 比错配任务 transfer 更能按正确方向移动 margin。

**Interpretation / 解释**：positive transfer supports a semantic process representation; failure means our current hidden evidence may be too lexical/local and should be framed more conservatively. / 能迁移说明更像过程语义表征；不能迁移说明当前 hidden evidence 可能偏词面/局部，需要保守表述。

### E44. MLP direction steering and necessity/sufficiency / MLP 方向 steering 与必要/充分性

**Question / 问题**：E41 中的 MLP participation 是否只是伴随现象，还是可复用方向能控制 verifier 决策？ / E41 的 MLP 参与是伴随现象，还是存在可复用方向能控制决策？

**Design / 设计**：at each model's strongest E41/E40 layers, build `valid-support minus invalid-error` directions from a training subset of families. Use leave-one-family-out transfer: add the direction to invalid traces and subtract it from valid traces in held-out families. / 在 E41/E40 最强层构造 `valid-support - invalid-error` 方向；采用 leave-one-family-out：在留出的家族上给 invalid 加方向、给 valid 减方向。

**Controls / 控制**：random span directions, mismatched-layer directions, shuffled labels, and final-answer-span directions. / 控制包括随机 span、错层方向、打乱标签、最终答案 span 方向。

**Expected useful outcome / 希望结果**：a real process direction should move Yes-minus-No margins and sometimes flip near-threshold decisions more than controls. / 真过程方向应比控制更能移动 Yes-No margin，并在近阈值样例上产生翻转。

**Interpretation / 解释**：this would convert “patch association” into a stronger causal representation claim. / 这能把“patch 有关联”升级成更强的因果表征主张。

### E45. Path mediation: residual vs MLP vs output head / 路径中介：residual、MLP 与输出头

**Question / 问题**：隐藏证据在哪里被放大、削弱或重新纠缠？ / hidden evidence 在哪里被放大、削弱或重新纠缠？

**Design / 设计**：for E40 robust and boundary families, compute layerwise residual effects, module effects, and final-token logit-lens changes. Estimate what fraction of residual effect is mediated by MLP/attention modules at the same layer. / 对 E40 稳健和边界族，计算 residual effect、module effect 和 final-token logit-lens 改变，估计 residual effect 中多少可由同层 MLP/attention 中介。

**Expected useful outcome / 希望结果**：robust families should show a middle-layer residual band with partial MLP mediation; boundary families such as round-vs-truncate should show weak transfer or late re-entanglement. / 稳健族应显示中层 residual 带和部分 MLP 中介；round-vs-truncate 等边界族应显示弱迁移或后层再纠缠。

### E46. Natural harvesting across E39 families / E39 家族自然挖掘

**Question / 问题**：这些陷阱在自然生成中是否会出现，而不是只存在于人工构造中？ / 这些陷阱自然生成中会不会出现？

**Design / 设计**：for each E39 family, generate 50-100 traces from Qwen35-27B and Gemma31 with varied prompts. Filter final-correct traces, then manually audit process validity and run E42 verifier objectives. / 每类 E39 族用 Qwen35-27B/Gemma31 生成 50-100 条，先筛答案正确，再人工审计过程有效性并跑 E42 目标矩阵。

**Expected useful outcome / 希望结果**：some families produce natural ACPI and others do not; both are publishable because they define prevalence and boundary. / 有些族自然产生 ACPI，有些不产生；二者都有价值，因为能定义发生率和边界。

### E47. Hard-task final-correct conditioning / 难题 final-correct 条件化

**Question / 问题**：AIME24/25 等难题上，ACPI 是否有不同形态？ / AIME24/25 难题是否出现不同形态的 ACPI？

**Design / 设计**：first obtain final-correct traces using high-temperature multi-sampling plus answer checking. Only after final correctness is established, audit process validity and run verifier objectives. / 先用高温多采样加答案检查获得 final-correct trace；之后才审过程有效性和 verifier 目标。

**Risk control / 风险控制**：do not claim benchmark performance; use public answers only as filters, not training labels; report sampling budget and all failures. / 不声称榜单性能；公开答案只作过滤，不作训练；报告采样预算和失败情况。

## 4. Immediate execution order / 立即执行顺序

1. Run E43 small transfer on 6 families × 2 paraphrases for Qwen14 and Qwen35-9B. / 先跑 E43 小规模迁移。
2. Run E44 leave-one-family-out MLP steering on the same families. / 再跑 E44 MLP steering。
3. Start E46 natural harvesting in parallel on Qwen35-27B and Gemma31. / 同时启动 E46 自然挖掘。
4. Only after E46 gives natural final-correct ACPI examples, promote those to hidden-state probes. / E46 找到自然 ACPI 后，再升级到 hidden-state probe。

## 5. Audit requirements / 审计要求

- Keep generated traces, final-answer filters, and manual process labels in separate files. / 生成 trace、答案过滤、人工过程标签分文件保存。
- Do not use known error spans in prompts; use them only for post-hoc scoring. / 不把已知错误 span 放进提示，只用于事后评分。
- For E44 directions, use leave-one-family-out to avoid evaluating on the same family used to build the direction. / E44 方向必须 leave-one-family-out，避免用同族构造又同族评估。
- Report malformed outputs as failures, not silently dropped rows. / 格式坏的输出算失败，不能静默删除。
