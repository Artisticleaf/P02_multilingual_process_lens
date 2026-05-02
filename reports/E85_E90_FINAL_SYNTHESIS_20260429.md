# E85-E90 Final Synthesis / E85-E90 最终综合（2026-04-29）

- Queue / 队列：`logs/e85_e89_status_20260429.jsonl` 与 `logs/e90_component_cache_status_20260429.jsonl` 均已 `all_done`。
- Scope / 范围：E85 全层 hidden cache、E86 代数边界负控制、E87 GLM 读出干预、E88 answer-first/no-gold 自然困难题人审、E89 修复策略筛选器模拟、E90 residual/MLP/token-mixer 组件激活缓存。
- Plain language / 说人话：这一批结果没有推翻主 claim，但把 claim 变得更精确。自然未修复 ACPI 仍低频；高 strict ACPI 主要来自 answer-first 先错后修；隐藏层/组件里确实有过程信号，但输出决策是否用它，取决于目标、读出格式、答案锚定和 trace 是否被当草稿阅读。

## Key Facts / 关键事实

### E85 Hidden Cache / E85 hidden 缓存

- Gemma31 repaired ACPI：`error_span_end` accept 0.889，`first_final_answer_end` accept 1.000；出现 repair marker 后，`repair_trigger_end` accept 0.111，`post_repair_240chars` accept 0.000，`completion_end` accept 0.111。
- 解释：Gemma31 在“错误答案刚出现”时会被 strict verifier 接受；一旦 trace 明确开始纠错，同一个 strict prompt 反而识别到“这条 trace 曾经错过”，转为拒绝。
- Gemma26 unrepaired ACPI：错误因式分解前缀和完整 trace 都被接受，accept rate 1.000；best-layer hidden projection 不干净地支持 valid，说明输出 Yes 与内部证据不完全一致。

### E86 Algebra Boundary / E86 代数边界

- 12 组短代数等价/符号陷阱中，四个 P0 模型 strict pointwise 对 invalid trace 的接受率都是 0.000。
- 但 valid trace 接受率只有 0.500-0.583，说明 strict prompt 能抓短显式代数错步，但也会误拒简短正确证明。
- 结论边界：不能声称“absolute verifier 普遍漏掉代数错误”；更准确说法是，长上下文、答案自洽、局部错误隐蔽和最终答案锚定共同放大风险。

### E87 GLM Readout / E87 GLM 读出

- GLM raw A/B single-order accuracy 0.542；global bias centering 0.667；two-order antisymmetric 0.812；hidden readout replacement 1.000；label-free two-pass 0.958。
- 解释：GLM 不是过程盲。它的问题更像是 raw A/B 输出标签读出把内部过程证据压坏。

### E88 Natural Answer-First Audit / E88 自然 answer-first 人审

- 192 条 answer-first/no-gold 生成中，63 条 final-correct。
- 63 条 final-correct 中，strict ACPI 23 条，其中 repaired ACPI 22 条，unrepaired ACPI 1 条。
- Wilson rates：final-correct per generated 63/192 = 0.328 [0.266, 0.397]；strict ACPI per generated 23/192 = 0.120 [0.081, 0.173]；unrepaired ACPI per generated 1/192 = 0.005 [0.001, 0.029]。
- 关键未修复个案：GLM 在二次型题中写出 `(3x - 2y)(4x + 3y)=0`，但这个展开是 `12x^2+xy-6y^2`，不是题目的 `12x^2-xy-6y^2`。由于错误直线的可数点数与正确直线对称相同，最终答案仍是 117；这个证明没有修复，是真正 unrepaired ACPI。
- 解释：E88 的高 strict ACPI 很大部分是 answer-first 格式效应，也就是模型第一行先给错 final answer，后文又改正。若论文讨论 strict trace-selection，这些确实是风险；若讨论最终保留证明是否有效，应单独报告 repaired 与 unrepaired。

### E89 Filter Simulation / E89 筛选器模拟

- 加入 E88 后，outcome-only 仍会保留所有 final-correct repaired/unrepaired ACPI。
- E88 manual strict filter 会拒绝 repaired 与 unrepaired ACPI；manual repair-aware filter 会接受 repaired ACPI、拒绝 unrepaired ACPI。
- 解释：同一条 trace 是否“坏”，取决于筛选目标。训练数据筛选如果要求整条 trace 全程无错，就不能保留先错后修；如果把 CoT 当草稿，只要求最终保留证明有效，就应允许 repaired 但拒绝 unrepaired。

### E90 Component Activations / E90 组件激活

- E90 捕捉了 selected layers 的 `residual_hidden_state`、`token_mixer_output`、`mlp_output`、attention/norm/feedforward outputs。prompt 未注入 gold、标签或人工 error span。
- Gemma31 repaired ACPI 的 best layer 34：从 `first_final_answer_end` 到 `repair_trigger_end`，Yes-No 从 +10.972 转到 -11.181；residual 从 +0.813 转到 -2.877；MLP 从 -0.073 转到 -2.438；post-FF norm 从 +0.482 转到 -3.761。
- 解释：修复触发后，不只是 residual，MLP/post-feedforward 与 token-mixer/attention 相关组件也同步移动。这支持“过程有效性信号是分布式组件信号”，不是单一 residual 标量。
- Gemma26 unrepaired ACPI 的 best layer 17：completion 仍 accept 1.000，Yes-No +7.125；但 residual -0.902、post-FF norm -3.983，MLP 约 +0.039。解释：组件证据混杂，输出头仍给 Yes，是更强的 evidence-to-decision mismatch 个案。

## Updated Claim / 更新后的安全主张

Controlled strict ACPI trace-selection risk is robust. Natural unrepaired ACPI is low-frequency but real in current hard-task samples. Hidden residual/MLP/token-mixer activations contain process-validity evidence, but whether the verifier decision uses that evidence depends on objective, threshold, final-answer anchoring, repair-aware reading, context/local subtlety, and output-label/readout format.

中文：受控 strict ACPI trace-selection 风险稳健；当前困难题自然未修复 ACPI 低频但真实存在。hidden residual、MLP、token-mixer 等激活里存在过程有效性证据，但 verifier 最终是否用上这些证据，取决于评价目标、阈值、最终答案锚定、是否把 CoT 当草稿读、上下文/局部错误隐蔽性，以及输出标签/读出格式。

## Remaining Top-Tier Gaps / 顶会级剩余短板

- Natural prevalence still needs larger and more diverse no-gold harvesting beyond answer-first, because answer-first itself creates many repaired strict ACPI artifacts. / 自然发生率还需要更大更多样的无 gold 采样，不能只依赖 answer-first。
- E90 shows component signals, but does not yet prove component-level causal mediation. Next step should patch or steer residual/MLP/token-mixer components and measure Yes/No or A/B logit changes. / E90 展示组件信号，但还不是组件级因果中介证明。
- GLM readout mismatch is scientifically valuable but needs a cleaner output-interface study: label-free, two-order, calibrated logits, and hidden readout should be compared under the same trace pool. / GLM 读出错配很重要，但需要更干净地比较无标签、双顺序、校准 logits 与 hidden readout。
- The paper must separate three claims: controlled strict trace-selection risk, natural unrepaired prevalence, and mechanistic hidden evidence. Mixing them will overclaim. / 论文必须分开三件事：受控 strict 风险、自然未修复发生率、机制 hidden 证据；混在一起会过度声称。

## Bottlenecks / 当前瓶颈

- Human/agent audit scale is the main statistical bottleneck for natural ACPI. / 自然 ACPI 的统计瓶颈是人审规模。
- Exact hidden/MLP capture requires HF hooks, so throughput is lower than vLLM; this is a measurement requirement, not training卡死。 / 精确 hidden/MLP 捕捉依赖 HF hook，吞吐低于 vLLM，这是测量需求不是训练卡死。
- Nemotron/EXAONE remain backend/license blocked and must not enter official evidence until smoke tests pass. / Nemotron/EXAONE 仍受后端或许可阻塞，通过新 smoke 前不能进入官方证据。
