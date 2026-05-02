# E38 Gemma4-31B + E36/E37 Synthesis / E38 Gemma4-31B 与 E36/E37 综合分析

Date / 日期: 2026-04-27 CST

## 1. Operational result / 运行结果

- `gemma4_31b_it` download completed. There are two complete safetensor shards and no `*.incomplete` cache file. / `gemma4_31b_it` 下载已完成；两个 safetensor 分片齐全，没有 `*.incomplete` 缓存文件。
- The four-GPU core verifier suite finished through the HF `device_map=auto` fallback. / 四卡核心 verifier 套件已通过 HF `device_map=auto` fallback 跑完。
- E36 and E37 also finished after the Gemma4-31B suite. / Gemma4-31B suite 结束后，E36 与 E37 也已完成。
- No tmux job is currently running, and all four GPUs are idle after completion. / 当前没有 tmux 任务运行，四张 GPU 完成后空闲。

Completed outputs / 已完成输出：

- `results/S6_lexical_grid_absolute_verifier_hf/gemma4_31b_it_manual_trace_verifier.json`
- `results/E28_counterfactual_answer_masking_absolute_verifier_hf/gemma4_31b_it_manual_trace_verifier.json`
- `results/E30_non_discount_absolute_verifier_hf/gemma4_31b_it_manual_trace_verifier.json`
- `results/E31_non_discount_counterfactual_absolute_verifier_hf/gemma4_31b_it_manual_trace_verifier.json`
- `reports/E36_inequality_boundary_deep_dive_20260427.md`
- `reports/E37_e31_layerwise_lens_summary_20260427.md`

## 2. Gemma4-31B main facts / Gemma4-31B 主要事实

Process-only ACPI false-accept rates / 只审过程时 ACPI 误接受率：

| experiment / 实验 | English prompt / 英文提示 | Chinese prompt / 中文提示 | plain fact / 人话解释 |
|---|---:|---:|---|
| S6 lexical discount grid | 1.000 | 1.000 | 31B accepts all selected discount lexical ACPI traces. / 31B 接受全部已选择的折扣词汇 ACPI。 |
| E28 phrase/final-answer counterfactual | 1.000 | 1.000 | Local phrase edits still do not force rejection when final answer remains helpful. / 局部错误短语仍没有迫使拒绝。 |
| E30 one natural non-discount ACPI | 1.000 | 1.000 | The single natural inequality ACPI is still accepted in both prompt languages. / 唯一自然非折扣 ACPI 仍被中英提示接受。 |
| E31 controlled non-discount traps | 0.400 | 0.600 | 31B is stricter than smaller Gemma on controlled non-discount traps, but risk remains. / 31B 在受控非折扣上更严格，但风险没有消失。 |

Comparison with smaller Gemma on E31 / 与较小 Gemma 在 E31 上比较：

| model / 模型 | English ACPI false accept | Chinese ACPI false accept | interpretation / 解释 |
|---|---:|---:|---|
| Gemma4-E4B-it | 1.000 | 1.000 | small Gemma almost always accepts ACPI. / 小 Gemma 几乎全接受。 |
| Gemma4-26B-A4B-it | 0.800 | 0.800 | 26B-A4B reduces some false accepts but still accepts most ACPI. / 26B-A4B 有改善但仍接受多数。 |
| Gemma4-31B-it | 0.400 | 0.600 | 31B is materially stricter on E31, but still accepts answer-correct process-invalid rows. / 31B 在 E31 明显更严格，但仍接受答案正确、过程错误的行。 |

Trap-level E31 behavior for Gemma4-31B / Gemma4-31B 的 E31 陷阱级行为：

| trap / 陷阱 | English process-only | Chinese process-only | scientific read / 科学解释 |
|---|---|---|---|
| ratio denominator / 比例分母 | reject | accept | Prompt language changes the threshold. / 提示语言改变阈值。 |
| inequality boundary / 不等式边界 | accept | reject at tie | This remains unstable; the bad trace mixes wrong wording and correct list. / 仍不稳定；坏 trace 混合错误表述与正确枚举。 |
| dozen/pairs unit / 打/双单位 | reject | accept | Chinese prompt is more permissive here. / 中文提示在该项更宽松。 |
| diameter/radius geometry / 直径/半径 | reject | reject | This error is robustly visible to 31B. / 这个错误对 31B 较清楚。 |
| unordered combinatorics / 无序组合 | accept | accept | The order/selection wording remains a hard ACPI. / “是否计顺序”仍是困难 ACPI。 |

Training-candidate objective / 训练样本清洗目标：on E31, the stricter training-candidate prompt reduces false acceptance further: process-invalid false accept is 0.133 in English and 0.000 in Chinese. But this stricter objective does not solve every setting: S6 and E30 still show substantial acceptance under training-candidate prompts. / 在 E31 上，更严格的训练样本清洗目标进一步降低误接受：英文过程无效误接受 0.133，中文为 0.000。但它不能解决所有场景；S6 与 E30 在 training-candidate 目标下仍有明显接受。

Bottom line / 结论：model scale changes thresholds but does not erase the ACPI trace-selection risk. / 模型变大改变了阈值，但没有消除 ACPI trace-selection 风险。

## 3. E36: why the inequality boundary is hard / E36：不等式边界为什么难

E36 tested five span variants of the same bad trace. The bad trace first says `between 3 and 7, inclusive`, which would include 3, but then immediately lists the correct values `4, 5, 6, and 7`. / E36 测了同一个坏 trace 的五种 span。坏 trace 先写 `between 3 and 7, inclusive`，这会包含 3，但随后立即列出正确值 `4, 5, 6, and 7`。

Key results / 关键结果：

- Qwen3.5-9B: all 5 span variants have directionally clean patch signals; strongest is the longer span containing both wrong wording and correction (`valid->bad +0.188`, `bad->valid -2.563`). / Qwen3.5-9B 五个 span 变体都有方向干净信号；最强的是同时包含错误表述与修正的长 span。
- Qwen14: 3/5 variants are clean; strongest clear semantic endpoint signal is `inclusive` vs `no more than 7` (`valid->bad +0.125`, `bad->valid -1.500`). / Qwen14 五个变体中三个方向干净；最强端点语义信号来自 `inclusive` 与 `no more than 7`。
- The correct-list variant is not a simple local-error patch for Qwen14: patching the shared list has negative effects in both directions (`-2.000/-2.500`). / 对 Qwen14 来说，后续正确列表不是简单错误定位 patch；共享列表在两个方向都产生负效应。

Interpretation / 解释：the inequality example is not weak because there is no hidden evidence. It is weak because the trace contains conflicting evidence: local wording is invalid, but the next sentence and final answer are consistent with the correct process. The absolute verifier can be pulled toward acceptance by this downstream correction. / 不等式样例不是“完全没有隐藏证据”，而是证据冲突：局部表述错，但下一句和最终答案又符合正确过程。绝对式 verifier 会被下游修正拉向接受。

## 4. E37: middle hidden evidence vs final Yes/No decision / E37：中层隐藏证据与最终 Yes/No 决策

E37 is a diagnostic logit lens, not the same scoring rule as the full option-logprob verifier. It projects each layer's decision-token hidden state through the final LM head, so it is useful for locating hidden evidence but should not be read as the deployed verifier accuracy. / E37 是诊断性 logit lens，不等同于完整 option-logprob verifier。它把每层决策位置 hidden state 投到最终 LM head，因此适合看隐藏证据位置，不应当直接当成部署 verifier 准确率。

Main facts / 主要事实：

- Qwen3.5-9B absolute lens: ACPI final-positive rate is 0.600, middle-positive rate is 0.500, and mean middle-to-final drop is 5.311. / Qwen3.5-9B 绝对 lens：ACPI 最终正向率 0.600，中层正向率 0.500，中层到最终平均下降 5.311。
- Qwen14 absolute lens: ACPI middle-positive rate is 1.000, but final-positive rate is only 0.500; mean middle-to-final drop is 8.037. / Qwen14 绝对 lens：ACPI 中层正向率 1.000，但最终正向率只有 0.500，中层到最终平均下降 8.037。
- Contrastive lens is often stronger than absolute lens: Qwen3.5-9B reaches final target-positive 1.000 on ratio, geometry, and combinatorics pairs; Qwen14 keeps middle target-positive 1.000 on all five E31 pairs but final target-positive can collapse, especially on inequality. / 对比式 lens 常强于绝对式：Qwen3.5-9B 在比例、几何、组合 pair 上最终目标正向率为 1.000；Qwen14 在五个 E31 pair 上中层目标正向率均为 1.000，但最终层可能坍缩，尤其是不等式。

Interpretation / 解释：this supports the `hidden evidence exists but final objective/threshold underuses it` story. The model is not purely blind to process differences; rather, the final decision head/objective can re-entangle process evidence with answer correctness, fluency, prompt language, and order bias. / 这支持“隐藏证据存在，但最终目标/阈值没有充分使用”的故事。模型不是纯粹看不见过程差异；最终决策头/目标会把过程证据与答案正确、流畅性、提示语言和位置偏差重新纠缠。

## 5. Scientific update / 科学更新

The current strongest claim should be: / 目前最强主张应表述为：

> Multilingual and surface-semantic lexical traps can create answer-correct but process-invalid traces. This risk is not only an answer error or formatting error. It comes from a mismatch among local lexicalization, process semantics, and verifier objective/threshold. Hidden process/error-span evidence is often present in middle residual states or contrastive objectives, but an absolute Yes/No verifier may still accept because final decision layers re-entangle that evidence with answer correctness and downstream correction.
>
> 多语言与表层语义词汇陷阱会产生“答案正确但过程无效”的 trace。这不是简单答案错或格式坏，而是局部词汇化、过程语义、verifier 目标/阈值之间的错配。中层残差状态或对比式目标中常能看到过程/错误 span 证据，但绝对 Yes/No verifier 仍可能因为最终决策层把这些证据与答案正确和下游修正重新纠缠而接受。

Boundary / 边界：we still should not claim natural prevalence across all tasks. E30 found only one clean natural non-discount ACPI in the first pass. The stronger publishable angle is a controlled and mechanistic risk model, not a frequency claim. / 边界：仍不应声称所有任务中自然高发。E30 第一轮只找到一条干净自然非折扣 ACPI。更稳的发表角度是受控且机制化的风险模型，而不是发生率主张。

## 6. Reliability audit / 可靠性审计

- Data leakage risk is low for these experiments: E31 is a manually constructed diagnostic set, and E36 only reuses the same audited pair with different span boundaries. / 本轮数据泄露风险低：E31 是人工构造诊断集，E36 只是在同一条已审计 pair 上改变 span 边界。
- E37 is explicitly diagnostic; it should not be mixed with full verifier accuracy tables without a warning. / E37 是诊断 lens，不能不加说明地与完整 verifier 准确率表混用。
- The E36/E37 scripts compiled and `scripts/check_project.py` passed after completion. / E36/E37 脚本编译通过，完成后 `scripts/check_project.py` 通过。
- The Gemma4-31B run used HF four-GPU fallback because current vLLM does not support this Gemma4 family reliably in our environment. / Gemma4-31B 使用 HF 四卡 fallback，因为当前环境的 vLLM 对该 Gemma4 家族不稳定。
