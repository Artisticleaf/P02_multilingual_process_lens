# Scientific Communication Memo / 科研沟通备忘录

Date / 日期: 2026-04-27 CST
Based on / 基于: `reports/S5_INTEGRATED_SCIENTIFIC_ANALYSIS_AND_ROADMAP_20260427.md`

## 1. Current Research Result / 目前实验得到的科研结果

我们现在看到的核心科学事实是：有些多语言推理轨迹的最终答案是对的，但中间过程在语义上是错的；这些错误常常发生在表层词汇转换处，例如中文“打八折/七五折”和英文“80% discount/75% off/pay 80%”之间。

具体事实：

- 在 154 条简单任务人工审计轨迹中，有 9 条 ACPI，也就是 final answer correct 但 process invalid。
- 在 32 条定向 sibling 审计中，新增 1 条同 route Qwen14 `打八折` ACPI，并找到多个 valid sibling。
- 在 8 个 manual ACPI pair 中，8 个都被 absolute Yes/No verifier 过度接受。
- 在同一批 ACPI pair 中，7 个有 contrastive sibling signal，6 个有 hidden-span signal，2 个有 MLP-level signal。
- Qwen3.5-27B 和 Gemma4 在作为 absolute verifier 时也会过度接受这些 ACPI；Qwen3.5-27B 在 contrastive mode 下明显更好，Gemma4 则暴露 position bias。
- AIME 难题 smoke 里没有 ACPI，因为 48 条都没有 strict final-correct；这说明困难任务上必须先获得 final-correct trace，不能直接外推简单任务结果。

## 2. Compared With Published Work / 相比已发表工作的创新点

已有工作已经讲过：CoT 可能不忠实、过程监督很重要、PRM/verifier 会受答案正确性影响、LLM judge 有位置偏差、隐藏层 patching 可以做机制分析。

我们不能把这些泛化表述当创新。我们的创新点应该写成组合式：

1. 多语言 surface lexicalization：我们研究的是中文折扣词和英文折扣词之间的语义错配，不是一般数学算错。
2. ACPI trace-selection risk：我们关心的是这些“答案对但过程错”的轨迹会被数据筛选/verifier 选择误保留下来。
3. Absolute vs contrastive objective mismatch：同一条坏轨迹在单条 Yes/No 下被接受，但放到 sibling 对比中，部分模型能找出错误。
4. Real generated traces：样本来自模型真实生成，然后人工逐句审计，不是纯手写 toy examples。
5. Hidden-span causal signal：在多数稳健 pair 中，错误 span 的隐藏状态 patch 会移动 verifier margin，说明过程错误信号在内部表征中可被暴露。
6. 明确边界：我们保留失败例和负控，不把 sibling comparison 或 hidden patch 说成万能。

## 3. Proposed Next Experiments / 后续实验设计

### A. Pair Bank Expansion / 扩展干净 sibling pair 库

目的：让论文不只依赖少数明星样本。

做法：继续定向生成和人工审计，至少找 8 对同题、同输入语言、同推理语言的 ACPI/valid sibling。覆盖折扣、比例、导数和百分比复合操作。

希望结果：多数 pair 被 absolute verifier 过度接受；至少一半 pair 有 contrastive 或 hidden-span 信号。

### B. Lexical Paraphrase Grid / 表层词汇改写网格

目的：证明错误真的是词汇表层导致，而不是随机算错。

做法：同一道题只替换表达方式，例如 `打八折`、`付原价80%`、`20% off`、`80% discount`、`75% off`。

希望结果：模型在 pay-form 和 discount-form 之间出现系统差异，特别是 `打八折 -> 80% discount`、`七五折 -> 75% off` 更容易触发语义漂移。

### C. Verifier Objective Intervention / verifier 目标干预

目的：证明 absolute verifier 失败是目标/阈值错配。

做法：同一批轨迹分别跑 absolute process-only、absolute training-candidate、contrastive A/B、order-balanced contrastive。

希望结果：absolute false accept 高；contrastive 在强模型上改善；Gemma4 这类模型可能继续暴露位置偏差。

### D. Mechanism Deepening / 机制深化

目的：把 hidden-span 证据推到模块/头/MLP feature 层面。

做法：只对已经稳健的 pair 做 head-level patch、MLP block ablation、layerwise/tuned lens、可选 SAE/transcoder。

希望结果：中层某些 MLP 或 attention head 对 process/error signal 有稳定贡献；最终输出头把过程信号和 final-answer correctness 重新混合。

### E. AIME Conditional Sampling / AIME 条件化采样

目的：回答困难数学上有没有同类 ACPI。

做法：先用更强模型或更多采样获得 final-correct AIME traces，再人工审计过程；不要把 final-wrong 或 no-final-marker 当 ACPI。

希望结果：如果困难任务中存在 ACPI，absolute verifier 仍会过度接受；如果没有，也能作为“现象受 final-correct 稀缺性限制”的边界。

## 4. What I Need To Confirm With You / 需要与你确认

1. 论文定位：我们是否接受“selected high-risk family + causal/mechanistic evidence”的定位，而不是追求总体 prevalence benchmark？
2. 机制深度：下一轮是否优先做 head/MLP/SAE 机制，还是先扩充 pair bank？我的建议是先扩 pair bank，再对最稳 pair 做机制。
3. 难题路线：AIME 是否继续投入？我的建议是保留为 boundary/control，同时用 conditional final-correct sampling 小规模推进。
4. 模型路线：Qwen3.5-27B 和 Gemma4 已可作为 transfer verifier；若要作为 generator，需要先修 prompt，让 Qwen3.5-27B 不再输出 meta-planning。

## S6 Addendum / S6 补充

The simplest current explanation / 当前最简单解释：the risky traces are not just “bad answers.” They are cases where the final number is correct but the sentence that explains why the number is correct uses the wrong surface meaning. / 风险 trace 不只是“答案错”。它们是最终数字正确，但解释这个数字的句子用了错误表层含义。

Concrete examples / 具体例子：

- `打八折` means pay 80%, not pay 75%. / `打八折` 是支付 80%，不是支付 75%。
- `80% discount` means pay 20%, not multiply by 0.8. / `80% discount` 是支付 20%，不是乘以 0.8。
- `sold for 75% of the original price` means pay 75%; `75% discount` means pay 25%. / `按原价 75% 出售` 是支付 75%；`75% discount` 是支付 25%。

S6 result / S6 结果：Gemma4 and Qwen14 generated three paper-grade ACPI traces of this exact type, and absolute Yes/No verifiers mostly accepted them as process-valid. / Gemma4 与 Qwen14 生成了三条这种类型的论文级 ACPI，绝对式 Yes/No verifier 基本把它们接受为过程有效。

Best current mechanistic fact / 当前最强机制事实：for the Qwen14 `sold for 75%` versus `75% discount` pair, patching the hidden support/error span at layer 14 moved the verifier margin in the expected causal direction (`valid->bad +2.750`, `bad->valid -1.000`). / 对 Qwen14 的 `sold for 75%` 与 `75% discount` pair，在第 14 层 patch hidden support/error span 会按预期因果方向移动 verifier margin（`valid->bad +2.750`，`bad->valid -1.000`）。

How to say novelty safely / 如何安全表述创新：do not say “we discovered that correct answers can have wrong reasoning.” Say “we isolate a multilingual lexical ACPI family, show absolute verifier objective mismatch, and expose hidden support/error-span signals on selected real sibling pairs.” / 不要说“我们发现正确答案可能有错误推理”。应说“我们隔离出一个多语言词汇 ACPI 族，展示绝对式 verifier 目标错配，并在选择后的真实 sibling pair 上暴露 hidden support/error-span 信号。”
