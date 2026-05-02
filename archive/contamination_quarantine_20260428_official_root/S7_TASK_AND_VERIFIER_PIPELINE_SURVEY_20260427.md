# S7 Task/Verifier Pipeline Survey / S7 任务与 verifier 管线调研

Date / 日期: 2026-04-27 CST  
Purpose / 目的: answer two user questions before expanding experiments: (1) are our current discount examples already a published-task collision, and how should we broaden tasks; (2) is `L -> P -> A -> H -> V` a necessary/common LLM workflow or an artificial verifier scenario? / 在扩展实验前回答两个问题：折扣例子是否撞车、如何扩展任务；以及 `L -> P -> A -> H -> V` 是否是大模型必经/常见工作链，还是我们人为构造了 verifier 场景。

## 1. Bottom Line / 结论先说

- Discount/percentage word problems are common in math reasoning benchmarks, so we should not sell “discount errors” as the novelty. / 折扣/百分比应用题在数学推理基准中很常见，因此不能把“折扣题会错”包装成创新。
- I did not find evidence that major 2023-2026 verifier/process benchmarks focus on the exact multilingual lexical ACPI pattern `打八折 = pay 80%` vs `80% discount = pay 20%` vs `sold for 75% = pay 75%`. / 我没有发现 2023-2026 主流 verifier/过程基准把 `打八折=付80%`、`80% discount=付20%`、`sold for 75%=付75%` 这种多语言词汇 ACPI 当作核心现象。
- The verifier part is not mandatory for every LLM use. A plain chatbot can generate `L -> P -> A` without any external verifier. / verifier 不是所有大模型使用的必经环节；普通聊天可以只有 `L -> P -> A`。
- But verifier/selector stages are very common in modern reasoning systems: best-of-N sampling, process reward models (PRM, 过程奖励模型), outcome reward models (ORM, 结果奖励模型), RLVR/RLAIF data filtering, LLM-as-a-judge, reranking, and training-data selection. / 但 verifier/selector 在现代推理系统里非常常见：best-of-N、PRM、ORM、RLVR/RLAIF 数据过滤、LLM-as-a-judge、重排序和训练数据筛选都需要类似判断器。
- Therefore our safest claim is conditional: **when a system uses a verifier/selector to choose or keep traces, multilingual lexical ACPI creates a trace-selection risk; even without an external verifier, the same conflict can reappear as an internal output-head/decoding decision.** / 因此最安全主张是条件式：**当系统用 verifier/selector 选择或保留 trace 时，多语言词汇 ACPI 会带来 trace-selection 风险；即使没有外部 verifier，同一冲突也可能在内部输出头/解码决策中出现。**

## 2. What Existing Work Already Covers / 已发表工作已经覆盖什么

### 2.1 Process-error benchmarks and PRMs / 过程错误基准与 PRM

- `Let's Verify Step by Step` introduced the now-standard point that supervising intermediate reasoning steps can outperform outcome-only supervision on math. / `Let's Verify Step by Step` 已经提出逐步过程监督比只看答案更可靠这一大方向。Source: https://arxiv.org/abs/2305.20050
- `Math-Shepherd` studies step-level verification/reinforcement without human annotations. / `Math-Shepherd` 研究无需人工标注的逐步验证与强化。Source: https://arxiv.org/abs/2312.08935
- `ProcessBench` evaluates identifying process errors in mathematical reasoning traces. / `ProcessBench` 直接评测数学推理 trace 中的过程错误识别。Source: https://arxiv.org/abs/2412.06559
- `PRMBench` is a fine-grained benchmark for process-level reward models. / `PRMBench` 是面向过程奖励模型的细粒度基准。Source: https://arxiv.org/abs/2501.03124
- `Right Is Not Enough` already makes the broad ACPI-like point: correct final answers can hide flawed reasoning, and judge-style methods can miss it. / `Right Is Not Enough` 已经撞车广义 ACPI：最终答案正确可能掩盖错误过程，judge 方法也会漏检。Source: https://arxiv.org/abs/2506.06877

Implication for us / 对我们的含义：

We should not claim novelty for “process supervision matters,” “correct answers can hide wrong reasoning,” or “LLM judges miss process errors.” Our novelty must be the **specific conjunction**: multilingual lexical surface traps, answer-correct/process-invalid trace selection, verifier objective/threshold mismatch, sibling comparison, and hidden support/error-span causal evidence. / 不要声称“过程监督重要”“正确答案会掩盖错误推理”“LLM judge 会漏检过程错误”是新发现。创新必须收窄为：多语言词汇表层陷阱 + ACPI trace selection + verifier 目标/阈值错配 + sibling 对比 + hidden support/error-span 因果证据的组合。

### 2.2 Surface-form robustness and multilingual math / 表层形式鲁棒性与多语言数学

- `GSM-Symbolic` shows that small symbolic/name/number perturbations can sharply change math reasoning accuracy. / `GSM-Symbolic` 已经说明表层扰动会显著影响数学推理准确率。Source: https://arxiv.org/abs/2410.05229
- `MMLU-ProX`, `PolyMath`, `MultiNRC`, and `MathMist` all support the broader fact that multilingual reasoning is not just English reasoning with translated words. / `MMLU-ProX`、`PolyMath`、`MultiNRC`、`MathMist` 都支持一个大事实：多语言推理不是简单把英文题翻译一下。Sources: https://arxiv.org/abs/2503.10497, https://arxiv.org/abs/2504.18428, https://arxiv.org/abs/2507.17476, https://arxiv.org/abs/2510.14305

Implication for us / 对我们的含义：

Published work already knows that surface form and language matter. What is less directly covered is **a local lexical item changes process semantics while the final number remains correct, and the verifier has some hidden/process signal but the final Yes/No decision underuses it.** / 已有工作已经知道表层形式和语言重要。较少被直接覆盖的是：**一个局部词汇项改变过程语义，但最终数字仍然正确；verifier 内部有某些过程信号，但最终 Yes/No 决策没有充分使用。**

## 3. Are Discount Examples Already Studied? / 折扣例子是否已被研究过

What I checked / 我本轮补查的方向：

- GSM8K/word-problem-style benchmarks with `discount`, `sale price`, `percentage off`, `sold for`, and related surface phrases. / GSM8K 与应用题基准中的折扣、售价、百分比折扣等短语。
- Process/verifier benchmarks such as ProcessBench and PRMBench for whether their central unit is the exact multilingual `折`/`discount` lexical flip. / ProcessBench、PRMBench 是否把 `折`/`discount` 词汇翻转作为核心单元。
- Chinese-specific searches for `打八折` + LLM/math reasoning/benchmark. / 中文 `打八折` + 大模型数学推理/基准。

Finding / 发现：

- Discount/percentage is a normal word-problem theme and therefore not unique. / 折扣/百分比题型本身很普通，不独特。
- I did not find a top-paper benchmark whose main claim is exactly: Chinese `打八折` means pay 80%, English `80% discount` means pay 20%, and a trace can write the wrong phrase while preserving the correct final answer. / 我没有找到顶会/主流基准把“中文打八折=付80%，英文80% discount=付20%，trace 写错短语但答案仍正确”作为核心 claim。
- Therefore the current discount examples are acceptable as **seed mechanisms**, but too narrow as the whole paper. / 所以当前折扣例子可以作为**种子机制**，但不能作为整篇论文的全部。

Action / 行动建议：

We should expand from “discount” to a **surface-semantic minimal-pair bank**. Each family should have: valid sibling, invalid sibling, final-correct ACPI variant, final-masked variant, final-wrong variant, and negative controls. / 我们应该从“折扣”扩成一个**表层语义最小对样本库**。每个族都要有：有效 sibling、无效 sibling、final-correct ACPI 变体、final-masked 变体、final-wrong 变体和负控。

## 4. Is `L -> P -> A -> H -> V` Necessary or Common? / `L -> P -> A -> H -> V` 是必需还是常见？

### 4.1 Not necessary for every LLM use / 不是所有 LLM 使用的必经链

If a user asks a model one question and directly reads the answer, there may be no external verifier. In that case, the observable chain is closer to: / 如果用户直接问模型并直接读答案，可能没有外部 verifier。此时可观测链更接近：

`surface lexicalization L -> generated process semantics P -> final answer A`

Here `H` and `V` are internal or implicit: the hidden state and output head decide the next tokens, but there is no separate verifier model. / 这里的 `H` 和 `V` 是内部/隐式的：隐藏状态和输出头决定下一个 token，但没有单独 verifier 模型。

### 4.2 Very common in reasoning systems / 但在推理系统中很常见

Verifier/selector stages appear in many important pipelines: / verifier/selector 出现在很多重要管线中：

- Best-of-N and reranking: sample many reasoning traces, then choose a final trace/answer. / best-of-N 和重排序：采样多条推理 trace，再选最终 trace/答案。
- Process reward model (PRM): score intermediate steps or trace prefixes. / PRM：给中间步骤或 trace 前缀打分。
- Outcome reward model (ORM): score final answer or final trace. / ORM：给最终答案或最终 trace 打分。
- Test-time compute scaling: use search/verifier-like selection to spend more compute on harder problems. / 测试时计算扩展：用搜索/verifier 类选择在难题上多花计算。
- Training data filtering: keep “high-quality” traces for SFT/RL or distillation. / 训练数据过滤：保留“高质量” trace 用于 SFT/RL/蒸馏。
- LLM-as-a-judge: evaluate model outputs or select responses. / LLM-as-a-judge：评测或选择模型回答。

Examples / 例子：

- Qwen2.5-Math explicitly reports self-improvement with mathematical reasoning data and process/reward components. / Qwen2.5-Math 技术报告包含数学自改进与奖励/过程组件。Source: https://arxiv.org/abs/2409.12122
- DeepSeek-R1 uses RL with reward signals to induce reasoning behavior, showing how reward/verifier-style objectives enter modern reasoning models. / DeepSeek-R1 通过强化学习奖励信号诱导推理行为，说明奖励/verifier 类目标已经进入现代推理模型训练。Source: https://arxiv.org/abs/2501.12948
- Test-time compute work studies when verifier-guided search can beat simply scaling model size. / 测试时计算扩展工作研究 verifier-guided search 何时优于单纯增大模型。Source: https://arxiv.org/abs/2408.03314
- Generative verifiers frame reward modeling itself as a next-token prediction task, again treating selection as a first-class component. / Generative verifier 把奖励建模本身写成 next-token prediction，说明 selection/verifier 是独立组件。Source: https://arxiv.org/abs/2408.15240

### 4.3 Correct framing for our paper / 我们论文的正确表述

Do not write / 不要写：

> All LLM reasoning must follow `L -> P -> A -> H -> V`.

Write / 应该写：

> In verifier- or selector-mediated reasoning pipelines, surface lexicalization can affect process semantics and final-answer selection differently. We study the chain `L -> P -> A -> H -> V` as a risk model for trace selection, not as a universal law of LLM cognition. / 在 verifier 或 selector 介入的推理管线中，表层词汇化会不同地影响过程语义和最终答案选择。我们把 `L -> P -> A -> H -> V` 当作 trace selection 风险模型，而不是大模型认知的普适定律。

## 5. What to Add Beyond Discount / 折扣之外要加什么

High-value families / 高价值任务族：

1. Ratio semantics / 比例语义：`boys:girls = 2:3` vs `boys are 2/3 of total`; 中文“男:女” vs “男占总数”。
2. Inequality quantifiers / 不等式量词：`at least`, `more than`, `no more than`, `不超过`, `少于`, `至少`.
3. Unit and base notation / 单位与进制/符号：`million` vs `亿`, `dozen` vs `pair`, `log base 2` vs subscript notation.
4. Inclusive/exclusive intervals / 区间端点：`between`, `from A to B inclusive`, `开区间/闭区间`.
5. Average vs total / 平均与总量：`average increase` vs `total increase`, `per person` vs `altogether`.
6. Geometry relation words / 几何关系词：reflection over a line vs through a point; radius vs diameter; height vs slant height.
7. Combinatorics order words / 组合计数顺序词：ordered arrangement vs unordered selection; replacement vs no replacement.
8. Calculus/algebra operator words / 算子词：coefficient vs exponent, derivative at x vs derivative function, inverse vs reciprocal.

For each family, the key is not just “can the model solve it?” The key is whether a trace can be answer-correct while a local phrase makes the process semantically invalid, and whether different verifier objectives treat that trace differently. / 每个族的关键不是“模型能不能做对”，而是 trace 是否会答案正确但局部短语让过程语义无效，以及不同 verifier 目标是否会不同地处理这条 trace。

## 6. Immediate Experimental Consequence / 对下一步实验的直接影响

- E28 should isolate lexical phrase causality and answer bias by editing only local phrases/final-answer lines. / E28 应通过只编辑局部短语和最终答案行，隔离词汇因果与答案偏置。
- E29 should ask verifiers to mark the first bad span, because this separates “cannot see the error” from “sees it but still accepts.” / E29 应让 verifier 标出第一处错误，因为这能区分“看不见错误”和“看见但仍接受”。
- E30 should build a non-discount minimal-pair bank with at least 8 families above. / E30 应建立非折扣最小对库，至少覆盖上面 8 个族。
- E31 should repeat span patching on the strongest new non-discount pairs, not on every noisy example. / E31 应只在最强的新非折扣 pair 上做 span patch，不要在噪声样例上平均。

## 7. Collision Boundary / 撞车边界

Safe novelty / 安全创新：

- Multilingual lexical ACPI as a controlled failure family. / 多语言词汇 ACPI 作为受控失败族。
- Trace-selection risk: correct answer causes bad process traces to survive filters. / trace-selection 风险：答案正确让坏过程 trace 通过过滤。
- Objective/threshold mismatch: absolute Yes/No verifier contains some signal but under-rejects. / 目标/阈值错配：绝对 Yes/No verifier 有部分信号但拒绝不足。
- Hidden support/error-span causality in selected robust pairs. / 选择后稳健 pair 中的 hidden support/error-span 因果性。

Unsafe novelty / 不安全创新：

- “Correct answer can hide wrong reasoning.” / “正确答案会掩盖错误推理。”
- “Process supervision is useful.” / “过程监督有用。”
- “LLM judges are imperfect.” / “LLM judge 不完美。”
- “Multilingual math is hard.” / “多语言数学很难。”
