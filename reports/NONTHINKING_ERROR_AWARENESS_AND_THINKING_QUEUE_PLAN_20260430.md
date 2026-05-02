# Non-Thinking Error-Awareness and Thinking Queue Plan / non-thinking 错误感知与 thinking 队列方案（2026-04-30）

## 1. 核心判断

当前最有潜力的主线不是“thinking 一定更强”，而是：

> non-thinking/direct verifier 并不是没有内部检查。它以更低 token 成本直接执行判断，hidden residual/MLP/token-mixer 中已经有过程有效性证据；但默认 Yes/No 或 A/B 输出侧经常没有稳定使用这些证据。thinking 会显式展开更多自检，但引入更高上下文成本和 stop/commit bottleneck。

这使我们的工作区别于普通 CoT 论文：我们不是只问“写长 CoT 是否更准”，而是在问“模型还没外显长 CoT 时，hidden activation 是否已经有过程错误感知；这个信号为什么没有进入最终 verifier 决策；能否用更低成本的 hidden-gated verifier 重构 process supervision/trace-selection”。

## 2. 已有证据能支持什么

### 2.1 non-thinking hidden 中有过程有效性证据

E106-E114 显示，四个 P0/expanded-P0 模型的 hidden process AUC 很高：

- Qwen3.5-27B: 1.000
- Gemma4-31B-it: 1.000
- Gemma4-26B-A4B-it: 0.970
- GLM-4.7-Flash: 0.997

plain Yes/No accuracy 只有 0.698-0.792。说人话：模型内部比它最终直接说出的 Yes/No 更清楚 trace 过程是否靠谱。

### 2.2 这不是纯粹置信度，但和置信度缠绕

E106-E108 显示 process direction 与 confidence direction 高度同轴，cosine 0.935-0.994；但控制 confidence/entropy 后 partial correlation 仍为 0.650-0.882，且 hidden AUC 通常高于 plain readout。

安全说法：

> 错误感知信号包含置信度成分，但不能完全化约为低置信度。它是 confidence-entangled process-validity evidence。

### 2.3 hidden gate 能显著减少受控 ACPI 保留

E114 的模拟规则：

```text
accept = plain_absolute_yes_no_accept AND hidden_process_score > 0
```

把 controlled ACPI retention 从 0.375-0.458 降到 0-0.042；valid retention 在 Qwen/Gemma31 无损，在 Gemma26/GLM 有少量 false rejection。说人话：如果把 hidden 里的过程信号接到筛选器上，能显著减少“答案对但过程错”的 trace 被当成好样本留下。

### 2.4 错误信号会随 repair marker 和组件状态移动

E80/E90 的 Gemma31 repaired ACPI 是当前最清楚的轨迹证据：

- 错误前缀/第一行错误 final answer：strict verifier 仍强接受。
- 出现 Wait/Correction/However 风格 repair marker 后：Yes-No 从强 Yes 转为强 No。
- residual、MLP/post-feedforward、token-mixer/attention-related 输出都随阶段变化向 invalid 侧移动。

这说明信号不是只存在于一个 final residual probe；多个组件都在关键前缀处发生阶段性变化。

### 2.5 自然 ACPI 低频但真实

E83 目前估计：

- strict ACPI per generated: 11/288 = 0.038, Wilson CI [0.021, 0.067]
- unrepaired ACPI per generated: 2/288 = 0.0069, CI [0.0019, 0.0250]
- unrepaired ACPI conditional final-correct: 2/127 = 0.0157, CI [0.0043, 0.0556]

所有 strict ACPI 都来自 answer-first/no-gold；这支持“先给答案再补过程”的自然低频风险，而不是 discount 个例。

## 3. 还不能支持什么

1. 不能说 natural unrepaired ACPI 高频。当前只能说低频但真实。
2. 不能说 hidden probe 已经定位了完整 circuit。当前是可读出、组件轨迹和少量干预，不是 head/neuron 级因果机制。
3. 不能说错误感知完全独立于置信度。它明显与 confidence/entropy/stop 缠绕。
4. 不能说 sibling 或 hidden gate 是 oracle。GLM raw A/B 和 Gemma26 valid false rejection 都提醒我们读出/阈值会坏。
5. 不能把 thinking fallback 抽取到正确数字当作 strict final decision。E103-E105 已经证明 Qwen thinking 有明显 stop/commit 问题。

## 4. 错误感知信号能否对应具体错误位置

目前答案是：有初步对应，但还不够 solid。

已有证据：

- E67：即便 literal error span 在多语言 trace 中无法字符串匹配，hidden probe 仍能高比例拒绝 ACPI。这说明信号不是简单抄错词。
- E80：在 error_span_end、repair_trigger_end、post_repair、completion_end 等前缀上，hidden score 和 Yes/No margin 会阶段性变化。
- E90：在 Gemma31 repaired ACPI 上，repair marker 前后 residual/MLP/token-mixer/post-FF 等组件出现同步位移。

不足：

- E80/E90 是关键 prefix 的 final-token activation，不是全 token 全层轨迹。
- 我们还没有证明哪个 token/span 的 patch 会因果改变 verifier 判定。
- 我们还没有把人工错误 span、翻译后 span、模型注意力/MLP 贡献和 logit decision 做严格对齐。

因此下一步应新增一个专门的 span-local causal 包，而不是继续只做全局 hidden probe。

## 5. 新增 span-local causal 实验方案

### E131 Token-Level Error Localization

目的：证明错误感知信号是否在错误 step 附近局部升高，而不是只在 completion end 才出现。

实现：

- 输入：E61 controlled grid、E80/E90 hard-task repaired/unrepaired cases。
- 对每条 trace 保存 all-token selected-layer residual/MLP/token-mixer score。
- 将人工 error span 扩展为 translated/semantic span：英文、中文、拼音、多语混合都对齐到同一“过程语义错误”。
- 指标：error-span token score、neighbor token score、answer-token score、random-span score。

希望看到：

- invalid trace 的 error span 附近 score 更负或变化更大；
- valid trace 的对应位置不出现同样负峰；
- random span 不能复现。

### E132 Residual Span Patch

目的：验证错误 span 是否因果影响 verifier 决策。

实现：

- valid/invalid sibling pair 在同一 prompt 下 teacher-forced replay。
- 将 invalid trace error-span token 的 residual/MLP/token-mixer 替换为 valid sibling 对应步骤的激活，观察 Yes/No logits 是否从 No/低分向 Yes 移动。
- 反向 patch：把 valid trace 对应位置替换为 invalid error-span 激活，观察是否更容易拒绝。

控制：

- random same-length span patch；
- answer span patch；
- punctuation/function-word patch；
- cross-route translated span patch。

希望看到：

- error-span patch 的 logit effect 显著大于 random/answer/punctuation patch。

### E133 Error-Span Intervention Specificity

目的：区分“错误感知”与“低置信度”。

实现：

- 先按 confidence/entropy 匹配 valid-invalid pair。
- 对 error span 和 non-error hard span 分别注入 process-invalid direction 与 confidence-low direction。
- 比较 ACPI rejection、Yes/No margin、hidden score 和 false rejection。

希望看到：

- process-invalid direction 在错误 span 上更有效；
- confidence-low direction 更像全局降置信度，会误伤更多 valid trace。

### E134 False-Positive Audit for Error Awareness

目的：估计“错误感知信号不是假阳性”的概率边界。

实现：

- leave-one-task、leave-one-error-family、leave-one-language-route、leave-one-model-family。
- permutation null 100-1000 次。
- Wilson CI/bootstrapped CI。
- 单独报告 valid false rejection 与 invalid false acceptance。

当前已有 E78 的方向性结果，但 E134 要升级到 token/span-local。

## 6. thinking 结果的初步分析

E103-E105 已经给出一个清楚的边界：

- Qwen TG 在 4096 token hard-task 设置下 strict final-correct 0/9，explicit final marker 0/9，hit-max 9/9。
- fallback correct 5/9 说明它有时在长思考中出现正确数字，但没有明确提交 final decision。
- 8k capped pilot 仍 0/2 final marker。
- 16k/32k final-contract canary 能让 Qwen 在 base_divisor 一题上自然停止并提交正确答案。

说人话：

> thinking 不是简单“更强推理”。它更像把更多搜索和自检显式展开，但带来收口/提交问题。non-thinking 更像压缩执行，成本低、格式更稳定，但可能出现先给答案再补过程的 ACPI 风险。

E116-E118 进一步说明：

- clean-stop 与 post-final continuation / hit-max 在 hidden residual stop direction 上明显分离；
- stop signal 与 process-validity score 不同；
- 这给 “thinking overthinking/stop-control” 一个独立机制主线。

## 7. 睡前可排队但本轮不执行的 thinking 实验方案

### T1 Thinking Verifier Objective Ladder

输入：E61/E71/E82 controlled valid/ACPI traces。

设置：thinking verifier，完整生成判断，不使用 first-token logprob；最后解析 `Final decision: Yes/No`。

目的：确认 DV 的 ACPI over-accept 是否在 TV 中仍存在。

### T2 Thinking Sibling / Label-Free

输入：E61 pairs、Gemma26 unrepaired cases、GLM label bottleneck cases。

设置：A/B、反向 A/B、First/Second、label-free two-pass；thinking full judgment。

目的：确认 GLM raw A/B bottleneck 是否只是 direct-readout artifact。

### T3 Thinking Final-Contract Natural Hard Tasks

输入：AIME24/25、AMC、code/table/unit conversion。

设置：只用 final-contract prompt；记录 fallback answer、explicit final marker、clean final stop、hit-max、post-final continuation。

目的：在不被 endless thinking 淹没的条件下估计 TG 自然 ACPI。

### T4 Thinking Hidden Stop and Error Signal

输入：T3 中 clean-stop、post-final-continue、unrepaired/repaired traces。

设置：保存 thought token、repair marker、final decision token 附近 residual/MLP/token-mixer/attention-related activations。

目的：比较 thinking 的 stop signal 与 process-error signal 是否分离。

### T5 TG/NG Same-Problem Paired Contrast

输入：同一题、同一采样族，NG 与 TG 各 k=2。

目的：比较更低成本 non-thinking 是否已经出现 hidden error awareness；thinking 是否只是把部分 latent search 外显化。

## 8. 与已有工作的关系

相关但不同：

- `Reasoning Models Know When They're Right` 研究 reasoning model hidden states 是否编码 answer correctness，并用于 self-verification/early exit。我们的区别是关注 final-answer-correct 但 process-invalid 的 trace-selection，而不是答案对错本身。
- `Coconut` 说明 latent/continuous thought 可以绕开自然语言 CoT 的 token 成本。我们的区别是：不训练新 latent-reasoning 模型，而是在现有 non-thinking verifier 的 hidden states 中读出 process-validity evidence。
- `Reasoning Models Don't Always Say What They Think` 和 2023 的 CoT unfaithfulness 工作说明外显 CoT 不一定忠实。我们的贡献更细：即使不依赖外显长 CoT，hidden activation 也能暴露过程错误信号，但 output objective/readout 未必使用它。
- `DeltaBench` 等长 CoT error detection 工作关注显式长 CoT 的错误检测。我们的任务更窄也更尖锐：answer correct but process invalid 的 trace 是否会被 verifier/filter 错误保留。
- overthinking/manifold steering 工作关注减少 long reasoning token。我们的 E116-E118 与其相邻，但我们把 stop/commit signal 与 process-validity signal 分开，并将其连接到 trace-selection 风险。

Reference links / 参考链接：

- Reasoning Models Know When They're Right: https://arxiv.org/abs/2504.05419
- Coconut / Chain of Continuous Thought: https://arxiv.org/abs/2412.06769
- Reasoning Models Don't Always Say What They Think: https://arxiv.org/abs/2505.05410
- DeltaBench / Can LLMs Detect Errors in Long CoT Reasoning: https://arxiv.org/abs/2502.19361

## 9. 写作建议

论文主线可以改成：

> We show that direct/non-thinking verification is not merely a cheap heuristic. In current medium open models, non-thinking verifier hidden states already encode process-validity evidence that can expose answer-correct but process-invalid traces. The failure is not absence of internal error awareness, but a mismatch between latent process evidence and the verifier's objective, threshold, answer anchoring, repair-aware reading, and output readout. Thinking exposes more deliberation but adds a stop/commit bottleneck; therefore, explicit long CoT is not the only route to process supervision.

中文版本：

> 我们证明 direct/non-thinking verifier 不是一个廉价但无解释性的启发式。当前中等开源模型在 non-thinking verifier 的 hidden states 中已经编码了过程有效性证据，能够暴露答案正确但过程无效的 trace。失败点不是模型内部完全没有错误感知，而是 latent process evidence 与 verifier 的目标函数、阈值、答案锚定、repair-aware 阅读和输出读出之间错配。thinking 会暴露更多自检，但也带来 stop/commit 瓶颈；因此，显式长 CoT 不是过程监督的唯一道路。

## 10. 本轮执行边界

本轮只做方案，不启动 T1-T5 或 E131-E134。建议等 E119 四模型 NG 扩样完成并生成 audit sheet 后，再决定先排 span-local causal 包还是 thinking final-contract 队列。
