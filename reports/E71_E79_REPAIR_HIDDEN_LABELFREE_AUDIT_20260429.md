# E71/E76/E77/E78/E79 阶段报告：修复口径、hidden probe 假阳性、GLM 标签瓶颈

日期：2026-04-29  
范围：`E71`、`E76`、`E77`、`E78`、`E79`。机器可读汇总见 `reports/E71_E79_REPAIR_HIDDEN_LABELFREE_AUDIT_20260429.json`。

## 0. 一句话结论 / One-sentence conclusion

- 中文：这一批实验把主张从“模型会不会看过程”推进到更细的因果边界：P0 模型的 hidden residual 里确实有很强的过程有效性信号；但单条 Yes/No verifier 是否使用这个信号，强烈依赖评价口径和输出形式。GLM 的新结果尤其重要：它不是看不见错误，而是 raw A/B/First/Trace 标签读出很差；改成 label-free two-pass 后几乎恢复。
- English: This batch moves the claim from “can the model see process errors” to a sharper boundary: P0 models contain strong residual evidence of process validity, but pointwise Yes/No use of that evidence depends heavily on the objective and output format. GLM is especially informative: it is not blind to the error; raw A/B/First/Trace labels fail, while label-free two-pass almost recovers.

## 1. 实验设计与防泄露 / Design and leakage controls

- `E71_repair_objective`：同一批 hard-task 人审 trace 和 E61 controlled trace，分别用三种 verifier 口径打分：`strict_process`、`repair_aware`、`final_surviving_proof`。prompt 只给 problem 与 visible trace，不给人工标签、错误 span、修复标签或 gold 答案。
- `E78_hidden_probe_false_positive_audit`：在 E61 的最佳层 residual 上做留一任务、留一错误族、留一路径和标签置换检验，问 hidden probe 是否只是记住题目/语言/模板。
- `E79_glm_label_free_sibling`：专门检查 GLM 的 sibling 失败是否来自 A/B 或位置标签。比较 `AB`、`1/2`、`First/Second`、`Trace 1/Trace 2` 和不输出标签的 `label_free_two_pass`。
- `E76/E77_hardtask_hidden_replay`：teacher-forced 回放 hard-task 中已保存的 Gemma31 repaired ACPI 和 Gemma26 unrepaired ACPI trace，用 E61 学到的 residual validity direction 投影关键位置。
- 所有结果 JSON 内部 leakage audit 均显示：标签、错误 span、人工修复说明均未进入模型 prompt，只用于离线分组和评分。

## 2. E71：严格口径 vs 修复口径 / Strict vs repair-aware objective

### 2.1 主要数值 / Main numbers

| verifier model | objective | acc to objective | yes rate | strict-invalid accept | repaired accept | unrepaired accept |
|---|---:|---:|---:|---:|---:|---:|
| qwen35_27b | strict_process | 0.902 | 0.647 | 0.034 | 0.000 | 1.000 |
| qwen35_27b | repair_aware | 0.879 | 0.930 | 0.814 | 0.933 | 1.000 |
| qwen35_27b | final_surviving_proof | 0.851 | 0.921 | 0.780 | 0.800 | 1.000 |
| gemma4_31b_it | strict_process | 0.981 | 0.744 | 0.068 | 0.033 | 1.000 |
| gemma4_31b_it | repair_aware | 0.870 | 0.977 | 0.915 | 0.933 | 1.000 |
| gemma4_31b_it | final_surviving_proof | 0.833 | 0.967 | 0.881 | 0.767 | 1.000 |
| gemma4_26b_a4b_it | strict_process | 0.902 | 0.665 | 0.068 | 0.000 | 1.000 |
| gemma4_26b_a4b_it | repair_aware | 0.837 | 0.953 | 0.915 | 0.900 | 1.000 |
| gemma4_26b_a4b_it | final_surviving_proof | 0.819 | 0.860 | 0.610 | 0.567 | 1.000 |
| glm47_flash_candidate | strict_process | 0.777 | 0.521 | 0.034 | 0.033 | 0.000 |
| glm47_flash_candidate | repair_aware | 0.888 | 0.958 | 0.847 | 0.933 | 1.000 |
| glm47_flash_candidate | final_surviving_proof | 0.842 | 0.893 | 0.610 | 0.533 | 1.000 |

### 2.2 说人话解释 / Plain-language interpretation

- `strict_process` 的意思是：只要可见 trace 里出现任何一步错，即使后来修了、最终答案也对，也要判 No。这个口径适合“训练数据筛 trace”或“过程监督”场景，因为你不想把错误步骤也当成好过程写进训练集。
- `repair_aware` 的意思是：允许 CoT 像草稿一样先错后改；如果错误被明确放弃，最后留下来的推理链是对的，就可以判 Yes。这个口径适合“看解题过程有没有最终自我修复”的场景。
- `final_surviving_proof` 更进一步，只看最后保留下来的证明链，不惩罚已经废弃的草稿。
- 关键科学事实：同一条 trace，换一个评价口径，接受率会发生巨大变化。这说明 verifier 失败不是一个简单的“模型笨/模型聪明”问题，而是 objective 与 threshold 的问题。
- 更关键的是：Gemma26 的两条 hard-task unrepaired ACPI 在 core P0 的 strict verifier 下仍被 Qwen/Gemma 全部接受；GLM strict 拒绝了这两条，但 GLM 在 strict 口径下也误拒绝了不少 valid trace。因此我们不能把 GLM 解释成“更好”，而应解释成“更保守但不稳”。

### 2.3 对 claim 的影响 / Impact on claim

- 加强：`strict_process` 下，P0 可以拒绝绝大多数受控 strict-invalid trace，但仍会漏掉 hard-task 中更隐蔽的 unrepaired ACPI。这说明 controlled short traps 与 hard-task algebra traps 的难度不同。
- 加强：`repair_aware` 与 `final_surviving_proof` 显著提高 repaired trace 接受率，支持“模型可能把 CoT 当草稿阅读”的解释。
- 收紧：不能再把所有 strict-invalid trace 都说成同一种坏样本。论文必须显式区分 repaired ACPI 与 unrepaired ACPI。

## 3. E78：hidden probe 假阳性审计 / False-positive audit of hidden probes

### 3.1 主要数值 / Main numbers

| model | best layer | leave-one-task acc | leave-one-family acc | leave-one-route acc | permutation mean/max | p-value |
|---|---:|---:|---:|---:|---:|---:|
| qwen35_27b | 34 | 1.000 | 0.990 | 1.000 | 0.497 / 0.646 | 0.0099 |
| gemma4_31b_it | 34 | 1.000 | 1.000 | 0.990 | 0.504 / 0.667 | 0.0099 |
| gemma4_26b_a4b_it | 17 | 0.927 | 0.917 | 0.927 | 0.499 / 0.656 | 0.0099 |
| glm47_flash_candidate | 27 | 0.979 | 0.958 | 0.979 | 0.499 / 0.677 | 0.0099 |

补充解释：表中 `valid->invalid` 是把 valid trace 误判成 invalid 的 false rejection；`invalid->valid` 是把 invalid trace 误判成 valid 的 false acceptance。Gemma26 的错误主要是 false rejection：它会把一部分 valid trace 也投到 invalid 侧，而不是只在 invalid trace 上才激活一个干净信号。

### 3.2 说人话解释 / Plain-language interpretation

- 如果 hidden probe 只是记住题号、语言路线或模板，它在留一任务/留一错误族/留一路径上应该掉很多；实际没有。
- 如果 hidden probe 只是随机线性方向碰巧分开，标签置换后的准确率应该接近真实准确率；实际置换最高只有 0.65--0.68 左右，远低于真实 0.92--1.00。
- 因此，“hidden residual 里有过程有效性证据”比之前更可靠。但这仍不是完整 circuit：它说明可读出，不说明每个 attention head/MLP neuron 如何因果生成这个信号。

### 3.3 对假阳性的回答 / Answer to the false-positive concern

- Qwen/Gemma31：目前 E61 grid 上几乎没有 false-positive 风险，CI 下界也高。
- Gemma26：存在明显 valid false rejection，因此 Gemma26 的 hidden signal 不能说成“只在 invalid trace 出现”；更准确说法是“它有强过程有效性方向，但 valid 侧边界较脆”。
- GLM：hidden probe 很强，而 raw sibling 弱，形成关键错配证据：内部有信号，输出形式没有稳定读出来。

## 4. E79：GLM label-free sibling / GLM 的标签与输出形式瓶颈

### 4.1 主要数值 / Main numbers

| format | n | accuracy | predict-first rate | mean target margin |
|---|---:|---:|---:|---:|
| AB | 96 | 0.552 | 0.948 | 0.432 |
| one_two | 96 | 0.646 | 0.625 | 0.193 |
| first_second | 96 | 0.500 | 1.000 | 0.224 |
| trace1_trace2 | 96 | 0.500 | 1.000 | 0.000 |
| label_free_two_pass | 96 | 0.990 | 0.510 | 4.948 |

`label_free_two_pass` 只有 1 条错误，且该条两个 trace 的 invalid score 完全打平：`score_first=0.0`、`score_second=0.0`，所以更像 tie/读数边界，不是系统性看错。

### 4.2 说人话解释 / Plain-language interpretation

- GLM raw sibling 失败不是因为它完全不会看过程。否则 label-free two-pass 不可能到 0.990。
- GLM 的主要问题是：让它在同一个 prompt 里输出 A/B、First/Second、Trace1/Trace2 时，它很容易固定选第一个，或者把标签读出搞坏。
- 换成“分别给两条 trace 各自打一个 No-minus-Yes invalid 分数，再比较分数”后，GLM 几乎恢复。这说明 GLM 内部/pointwise 层面能区分过程错误，但直接 contrastive 输出头或 prompt 格式把这个信号压坏了。

### 4.3 对 claim 的影响 / Impact on claim

- 加强：GLM 不是反例，而是机制证据。它证明“hidden/process evidence -> output decision”之间有读出瓶颈。
- 收紧：不能说 sibling comparison 是无条件 oracle。更准确说：core P0 raw sibling 很强；GLM 这种模型需要 label-free 或 calibrated sibling 才能把内部过程信号释放出来。

## 5. E76/E77：hard-task hidden replay / 困难题 hidden 回放

### 5.1 主要数值 / Main numbers

| model/source rows | target rows | layer | error-span mean | repair-trigger mean | completion-end mean |
|---|---:|---:|---:|---:|---:|
| gemma4_31b_it repaired ACPI | 9 | 34 | -13.736 | -27.979 | -21.938 |
| gemma4_26b_a4b_it unrepaired ACPI | 2 | 17 | -10.654 | -15.054 | -5.787 |

### 5.2 重要边界 / Important boundary

- 这不是最终机制证据。原因是：direction 是在 E61 verifier prompt 上学到的，但回放是在 hard-task generation prompt 上做的；prompt 语境不同，投影分数不能直接解释成“越高越好/越低越坏”的同一标尺。
- 本次没有保存完整 hidden tensor，只保存了关键位置在 residual validity direction 上的投影分数、token 位置和 span 文本。完整 hidden tensor 体积较大，下一步如果需要做细粒度时间轨迹，应单独跑 raw hidden dump 或分层缓存。
- Gemma31 repaired trace 没有出现一个简单的“修复后分数变正”的模式；反而 repair trigger 和 completion end 仍明显在 invalid 侧。这是负结果，说明跨 prompt 迁移的 validity direction 不足以解释 hard-task self-repair。
- Gemma26 unrepaired 两条在错误 span 附近分数明显为负，但 final answer 处分数变得不那么负；这可能表示模型内部曾经有“这里不对”的信号，但最终输出时被答案锚定或证明收束稀释。这个解释目前只是可检验假设，不是结论。

### 5.3 信息收益 / Information gain

- E76/E77 告诉我们：如果要证明“纠错过程中 hidden state 如何变化”，不能只把 E61 verifier direction 迁移到 hard-task generation trace。下一步要在同一个 verifier prompt 内做 progressive-prefix replay：把同一条 trace 截断在错误步、修复触发、修复后、最终答案，逐段问 verifier，并记录 residual/logit。
- 这批结果防止我们过度宣称“hidden probe 已经解释了 hard-task repair”。目前只能说：controlled verifier prompt 下 hidden probe 很强；hard-task generation replay 初步显示错误附近有负向信号，但 repair 轨迹还没有被干净解释。

## 6. 当前科学事实更新 / Updated scientific facts

1. strict trace-selection 与 repair-aware reading 是两个不同评价口径；把它们混在一起会导致论文主张不清。
2. Core P0 在 strict prompt 下能拒绝大多数 controlled invalid trace，但会漏掉 Gemma26 的两条 unrepaired hard-task algebra ACPI。
3. GLM 在 strict prompt 下拒绝了这两条 unrepaired ACPI，但代价是 valid false rejection 高；它不是简单更强，而是更保守/阈值不同。
4. E78 证明 hidden residual validity signal 不是简单的题号、语言路线或随机标签假阳性；但 Gemma26 的 valid false rejection 要如实报告。
5. E79 证明 GLM 的 sibling 残留主要是 label/output-form bottleneck：raw A/B 弱，label-free two-pass 强。
6. E76/E77 不支持一个简单的“修复后 residual direction 变正”故事；hard-task repair 机制需要新实验。

## 7. 对顶会/顶刊主线的建议 / Recommendation for top-tier framing

当前最稳的论文主线应写成：

> 多语言/表层语义与过程语义的错配可以构造出 final-answer-correct 但 strict-process-invalid 的 trace-selection 风险。最新中等开源 P0 模型在 pointwise absolute Yes/No verifier objective 下会过度接受一部分这类 trace，尤其当最终答案正确或错误很隐蔽时。模型 hidden residual 中存在强过程有效性证据；contrastive 或 label-free scoring 可以释放这些证据，但 raw output labels、threshold 和 repair-aware reading 可能把证据压坏。因此，风险不是“答案错/格式坏”，而是 L -> P -> A -> H -> V 链条中 process evidence 与 verifier objective/readout 的错配。

英文对应：

> Multilingual/surface-semantic traps can create final-answer-correct but strict-process-invalid trace-selection risks. Recent medium-scale open P0 models over-accept some of these traces under pointwise absolute Yes/No verification, especially when the final answer is correct or the local error is subtle. Strong process-validity evidence exists in residual hidden states; contrastive or label-free scoring can expose it, but raw output labels, thresholds, and repair-aware reading can suppress it. The failure is therefore not merely wrong answers or malformed formats, but a mismatch along the L -> P -> A -> H -> V chain between process evidence and verifier objective/readout.

## 8. 仍然欠缺什么 / Remaining gaps

- 自然发生率：当前 hard-task unrepaired ACPI 样本只有 2 条，足够做案例机制，不足够估计广泛发生率。
- hard-task repair 机制：需要同 prompt progressive-prefix hidden/logit replay，不应继续直接把 E61 direction 跨语境迁移后过度解释。
- 因果链：E78 是可读出与负控制，E55/E56 是已有 steering 证据；但 E79 提出的 label-free readout bottleneck 还需要 residual-to-logit mediation 版本。
- 更广任务：E61 已覆盖 8 类错误和 6 条语言路线，但还缺真实开放题、长解题、代码执行/表格的自然生成版本。
- 人审规模：Gemma26 两条 unrepaired ACPI 需要作为 case study 深审，包括模型是否意识到错误、错误是否被答案对称性掩盖、其他 verifier 为什么漏掉。

## 9. 下一步实验建议 / Next experiments

1. `E80 progressive-prefix verifier replay`：同一 verifier prompt，把 Gemma31 repaired 与 Gemma26 unrepaired trace 截到错误步、修复触发、修复后、最终答案，记录 Yes/No logits 与 hidden projection。目的：证明 repair-aware reading 是否真的改变 hidden/logit。
2. `E81 label-free sibling across all P0`：把 E79 的 label-free two-pass 扩展到 Qwen/Gemma/GLM。目的：区分“contrastive objective 本身强”与“raw A/B 标签读出强”。
3. `E82 unrepaired ACPI case deep audit`：围绕 Gemma26 两条 quadratic-pairs trace 做人工逐句审计、局部扰动、去 final answer、wrong final answer、masked proof。目的：解释为什么所有 core P0 strict verifier 都漏掉。
4. `E83 hard-task natural harvesting expansion`：扩大 AIME24/25 和其他 hard math/code/table tasks 的 no-gold 采样，严格标注 final-correct / repaired / unrepaired。目的：估计自然 unrepaired ACPI 是否只是低频偶发。
5. `E84 readout mediation for GLM`：比较 raw A/B logits、label-free no-minus-yes 分数、hidden validity direction 三者的相关与干预。目的：把 GLM 的 output-label bottleneck 做成机制创新点。

## 10. 审计结论 / Audit conclusion

- 代码语法检查：Python scripts 与 shell launcher 通过 `py_compile` / `bash -n`。
- 队列状态：`logs/e71_e79_e76_e77_e78_status_20260429.jsonl` 记录 `all_done`。
- 数据泄露：E71/E78/E79/E76/E77 结果内置 leakage audit 均为 0 标签/0 span/0 gold 注入。
- 逻辑风险：E76/E77 是跨 prompt 投影，不能作为强机制结论；E78 的 `valid_false_positive_rate` 字段名在脚本里不够直观，报告中已改称 valid false rejection。
