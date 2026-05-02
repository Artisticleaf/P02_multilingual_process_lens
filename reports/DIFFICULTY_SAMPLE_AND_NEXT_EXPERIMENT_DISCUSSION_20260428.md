# Difficulty Samples and Next-Experiment Discussion / 困难样本与下一阶段实验讨论

Date / 日期: 2026-04-28 CST

Status / 状态: discussion-only planning; no new experiment launched. / 仅做讨论与规划；未启动新实验。

## 1. What style-controlled E42 rewriting means / E42 风格受控改写是什么意思

English: E42 controlled traces are manually paired traces for the same problem and same final answer: one trace has a valid process, while the sibling trace has a deliberately invalid local process. Style-controlled rewriting asks a P0 model to rewrite the trace in its own natural wording while preserving every mathematical claim, local step, error, and final answer. It is a style-transfer control, not a new solving task.

中文：E42 受控 trace 是同一道题、同一个最终答案下的成对 trace：一个过程有效，另一个有意包含局部过程错误。风格受控改写是让 P0 模型把这段 trace 改成自己更自然的说法，但必须保留每个数学主张、局部步骤、错误点和最终答案。它是“换文风”的控制实验，不是让模型重新解题。

Plain-language example / 说人话例子：

- Original invalid trace / 原始错误过程："The mean is the middle value of the ordered list, so it is 4. To compute the requested average, still add the numbers and divide by the count: (2+4+9)/3 = 5. Final answer: 5."
- Qwen-style rewrite / Qwen 风格改写："The mean is described here as the middle value of the ordered list, which would be 4. However, to compute the requested average, we add the numbers and divide by the count: (2+4+9)/3 = 5. Final answer: 5."

The rewrite changes wording and discourse markers, but it preserves the error "mean is the middle value." / 改写改变了措辞和连接方式，但保留了“mean 是 middle value”这个错误点。

## 2. What “the model repairs an invalid trace despite instructions” means / 什么叫模型“不听话地修复 invalid trace”

English: During E59c rewriting, some models were explicitly told not to correct mistakes, yet they still removed or softened the original invalid step. These rows were dropped before verifier scoring.

中文：在 E59c 改写阶段，我们明确要求模型不要修正错误，但有些模型仍然把原来的错误步骤删掉、改正确，或说得不再明确。这些行已经在 verifier 打分前剔除。

Concrete observed cases / 已观察到的具体案例：

- `qwen35_27b`, `zh_yi_wan_unit`: the original invalid trace said `1亿等于1000万`; the rewrite replaced this with the correct `1 yi equals 10,000 wan`, so the original invalid process was repaired. / 原始错误为 `1亿等于1000万`，改写后变成正确的 `1 yi equals 10,000 wan`，因此错误过程被修复。
- `gemma4_26b_a4b_it`, `percent_increase_vs_percent_of`: the rewrite retained a wrong sentence about the new price being 20% of the original, but immediately used the correct increase operation; this was conservatively dropped as repaired/ambiguous. / 改写仍保留“新价格是原价 20%”这类错误句，但马上用了正确的涨价操作；我们保守标为被修复/不明确并剔除。

Information value / 信息收益：

- Repair tendency suggests that models may contain a semantic-repair prior: when rewriting, they often normalize a trace toward mathematical coherence. / 修复倾向说明模型可能有一种“语义修复先验”：在改写时会把内容往数学一致方向拉。
- This can separate latent process understanding from absolute verifier behavior. A model can implicitly repair an error in a rewrite task while still over-accepting similar invalid traces under a Yes/No verifier objective. / 这可以区分“潜在过程理解”和“absolute verifier 决策”：模型在改写任务里能隐式修错，但在 Yes/No verifier 目标下仍可能接受类似错误 trace。
- Therefore repair-vs-preserve can become a probe: which errors are automatically repaired, which are preserved, and whether repaired errors align with stronger hidden-state validity directions. / 因此 repair-vs-preserve 本身可以成为探针：哪些错误会被自动修复，哪些会被保留，被修复错误是否对应更强 hidden-state 有效性方向。

## 3. Are current difficult samples multi-aspect enough? / 当前困难样本是否足够多角度

Short answer / 简短答案：not yet. The current official evidence is strong for controlled surface-semantic ACPI and residual-state process evidence, but the sample space is still too concentrated around short mathematical word-problem traps. It is enough to establish a phenomenon, not enough to claim broad top-tier generality. / 还不够。当前官方证据足以支持“受控表层语义 ACPI + residual-state 过程证据”这个现象，但样本空间仍过于集中在短数学文字题陷阱。它足以证明现象存在，还不足以支撑顶会/顶刊级的广泛共性主张。

Current coverage / 当前已覆盖的主要方面：

- Surface lexicalization: multilingual words, unit words, percent wording, mean/median-like lexical traps. / 表层词汇化：多语言词、单位词、百分比措辞、mean/median 类词汇陷阱。
- Process semantics: local operation mismatch while final answer remains correct. / 过程语义：局部操作错配但最终答案保持正确。
- Verifier objective: absolute Yes/No over-accepts while sibling comparison exposes many errors. / verifier 目标：absolute Yes/No 过度接受，而 sibling comparison 暴露很多错误。
- Hidden-state evidence: residual-stream validity signals and causal steering effects in P0 models. / 隐藏层证据：P0 模型中有 residual-stream 有效性信号与 steering 因果效应。

Main weakness / 主要薄弱点：

- Too much of the evidence still looks like controlled short-task diagnostics rather than broad natural reasoning behavior. / 证据仍太像受控短任务诊断，而不是广泛自然推理行为。
- Natural no-leak ACPI has not been observed in current simple samples. / 当前简单无泄露自然样本还没有观察到 ACPI。
- Hard-task ACPI is blocked by final-correct harvesting and final-line format compliance. / 困难题 ACPI 受限于先采到最终答案正确样本以及 final-line 格式合规。
- Mechanism is still residual-state level; component-level attention/MLP decomposition is not complete. / 机制仍停留在 residual-state 层面，attention/MLP 组件分解还没完成。

## 4. Needle-in-a-haystack vs diagnostic challenge set / “大海捞针”与诊断挑战集

English: Natural ACPI harvesting is a needle-in-a-haystack problem because the model must both get the final answer right and produce a locally invalid process without being prompted toward that error. This is important for prevalence, but it is not the only way to test the scientific claim. We should use two complementary tracks.

中文：自然 ACPI 采样像“大海捞针”，因为模型必须同时满足：最终答案正确、过程局部无效、而且 prompt 不能泄露目标错误。这对估计自然发生率重要，但不是检验科学主张的唯一方式。我们应该走两条互补路线。

Track A: prevalence harvesting / 路线 A：自然发生率采样

- Goal: estimate how often ACPI appears naturally. / 目标：估计 ACPI 自然出现频率。
- Risk: low yield, heavy manual audit, strong dependence on prompt style and final-answer format. / 风险：阳性率低、人审重、强依赖 prompt 风格和最终答案格式。

Track B: diagnostic challenge set / 路线 B：诊断挑战集

- Goal: isolate whether a verifier uses process evidence when final answer, style, language, and trace length are controlled. / 目标：在最终答案、文风、语言、长度受控时，隔离 verifier 是否使用过程证据。
- Value: high information per sample, suitable for causal ablation, hidden-state intervention, and objective comparison. / 价值：单样本信息收益高，适合做因果消融、hidden-state 干预和 objective 对比。

Paper-facing framing / 论文表述：prevalence asks "how often does this happen naturally?"; diagnostics ask "when the risk exists, why does the verifier fail and which objective can expose it?" Both are necessary but answer different questions. / 自然发生率回答“这种事自然有多常见”；诊断集回答“当风险存在时，verifier 为什么失败，什么目标能暴露它”。两者都必要，但问题不同。

## 5. Proposed ability dimensions beyond the current tasks / 当前任务之外应考查的能力维度

A top-tier benchmark should not only ask whether final answers are correct. It should separately test the following abilities. / 顶会级 benchmark 不应只看最终答案是否正确，而应分开考查以下能力。

1. Error localization / 错误定位能力

- Ask the verifier to identify the exact wrong span or step, not just Yes/No. / 要求 verifier 找出具体错误片段或步骤，而不只是回答 Yes/No。
- Scientific value: tests whether process evidence can be made explicit. / 科学价值：检验过程证据能否显式化。

2. Process repair / 过程修复能力

- Given an invalid trace, ask the model to minimally repair the wrong step while preserving the final answer if possible. / 给定 invalid trace，要求模型最小化修复错误步骤，并尽量保持最终答案。
- Scientific value: separates "can notice and fix" from "will reject under absolute verifier." / 科学价值：区分“能注意并修复”和“在 absolute verifier 下会拒绝”。

3. Counterfactual answer anchoring / 反事实答案锚定

- Show, remove, mask, or corrupt the final answer while keeping the process fixed. / 在过程不变时，显示、移除、遮盖或改错最终答案。
- Scientific value: tests whether acceptance is driven by the final answer rather than process validity. / 科学价值：检验接受判断是否被最终答案牵引，而不是由过程有效性决定。

4. Sibling discrimination / 成对区分能力

- Present same-problem same-answer valid/invalid siblings and ask which process is more reliable. / 展示同题同答案的 valid/invalid 成对 trace，让模型选择哪个过程更可靠。
- Scientific value: tests whether relative comparison unlocks process evidence. / 科学价值：检验相对比较是否能调出过程证据。

5. Paraphrase and language invariance / 改写与语言不变性

- Translate or paraphrase while preserving mathematical structure. / 在保留数学结构的前提下翻译或改写。
- Scientific value: tests whether evidence tracks process semantics rather than surface wording. / 科学价值：检验证据是否跟随过程语义，而不是只跟随表面词。

6. Long-context distractor resistance / 长上下文干扰抵抗

- Add irrelevant but fluent intermediate text, distractor examples, or competing definitions. / 加入无关但流畅的中间文本、干扰例子或竞争定义。
- Scientific value: tests whether verifier attends to the actual error span. / 科学价值：检验 verifier 是否真的关注错误片段。

7. Formal or executable trace checking / 形式化或可执行 trace 检查

- Include algebra transformations, proof steps, code traces, or table operations where local validity can be externally checked. / 纳入代数变形、证明步骤、代码 trace 或表格操作，使局部有效性可外部校验。
- Scientific value: reduces ambiguity in human labels and broadens beyond arithmetic word traps. / 科学价值：减少人审歧义，并超越算术文字题陷阱。

8. Hidden-state mechanism tests / 隐藏层机制测试

- Measure whether process validity directions mediate Yes/No logits and A/B logits; decompose residual, attention, and MLP contributions. / 测量过程有效性方向是否中介 Yes/No logits 和 A/B logits；分解 residual、attention 与 MLP 贡献。
- Scientific value: moves from behavioral finding to mechanistic explanation. / 科学价值：从行为发现推进到机制解释。

## 6. Suggested difficult-sample families / 建议扩展的困难样本族

The next challenge set should cover multiple error families, not just discount-like examples. / 下一批挑战集应覆盖多个错误族，而不只是 discount 类例子。

- Aggregation traps: mean vs median, weighted vs unweighted average, range vs average. / 聚合陷阱：均值/中位数、加权/非加权平均、极差/平均数。
- Percentage-base traps: percent increase vs percent of, discount base, reverse percentage, percentage-point vs percent. / 百分比基准陷阱：涨幅/占比、折扣基准、反向百分比、百分点/百分比。
- Unit and scale traps: 亿/万, million/billion, cm/m, hours/minutes, currency units. / 单位和数量级陷阱：亿/万、million/billion、厘米/米、小时/分钟、货币单位。
- Quantifier and inequality traps: at least vs more than, no more than vs less than, inclusive/exclusive bounds. / 量词与不等式陷阱：至少/大于、不超过/小于、闭区间/开区间边界。
- Order and comparison traps: before/after, older/younger, larger/smaller after transformations. / 顺序与比较陷阱：之前/之后、年长/年幼、变换后的大小关系。
- Rate and ratio traps: speed/time/distance, concentration dilution, ratio reversal. / 速率与比例陷阱：速度/时间/距离、浓度稀释、比例反转。
- Algebraic transformation traps: sign errors, dividing by a potentially negative quantity, square-root extraneous roots. / 代数变形陷阱：符号错误、除以可能为负的量、平方根增根。
- Counting and combinatorics traps: ordered vs unordered, with/without replacement, double counting. / 计数与组合陷阱：有序/无序、放回/不放回、重复计数。
- Geometry notation traps: overloaded symbols, diagram-free assumptions, radius/base name collisions. / 几何符号陷阱：符号复用、无图假设、半径/底边同名混杂。
- Table/data interpretation traps: row vs column, subtotal vs total, units in headers. / 表格/数据解读陷阱：行列混淆、小计/总计、表头单位。
- Code/execution trace traps: off-by-one, integer division, mutation/aliasing, loop boundary. / 代码/执行 trace 陷阱：差一错误、整数除法、可变对象/别名、循环边界。
- Proof-validity traps: true conclusion with invalid lemma, circular reasoning, missing case split. / 证明有效性陷阱：结论真但引理错、循环论证、漏分情况。

## 7. Recommended next-step ordering / 推荐下一步顺序

- First: E53 answer-anchor ablation and E55 residual-to-logit mediation. These directly test the causal chain between final answer, hidden process evidence, and verifier decision. / 第一优先：E53 答案锚定消融与 E55 residual-to-logit 中介分析；它们直接检验最终答案、隐藏过程证据和 verifier 决策之间的因果链。
- Second: E54 parameterized no-leak generalization across the sample families above. This addresses the "discount example" and "needle-in-a-haystack" concerns. / 第二优先：E54 在上述样本族上做参数化无泄露泛化；这解决“discount 个例”和“大海捞针”担忧。
- Third: E56 component decomposition after E55 identifies high-yield layers/positions. / 第三优先：E55 定位高收益层/位置后，再做 E56 组件分解。
- Background: E57 P0 hard-task final-correct harvesting should run as a long-yield process, not as the only main path. / 后台推进：E57 P0 困难题 final-correct 采样应作为长期采样任务，而不应成为唯一主线。
- Later: E58 distillation-filter simulation and expanded E59 cross-family verifier once E54/E57 provide a broader trace pool. / 后续：等 E54/E57 提供更广 trace pool 后，再做 E58 蒸馏筛选模拟和扩展 E59 跨家族 verifier。

## 8. Boundary / 边界

English: The current project should not claim that ACPI naturally occurs frequently in all reasoning tasks. The stronger and safer claim is that when final-answer-correct but process-invalid traces exist, modern P0-scale open models can over-accept them under absolute Yes/No verification even though process-validity evidence is available under contrastive and residual-state probes. Broader natural prevalence and hard-task behavior remain open empirical questions.

中文：当前项目不应声称 ACPI 在所有推理任务中都自然高频出现。更强且更安全的说法是：当“最终答案正确但过程无效”的 trace 存在时，现代 P0 级开源模型在 absolute Yes/No verification 下可能系统性过度接受；但 contrastive 与 residual-state probe 表明过程有效性证据是存在的。更广泛的自然发生率和困难题行为仍是待实证回答的问题。
