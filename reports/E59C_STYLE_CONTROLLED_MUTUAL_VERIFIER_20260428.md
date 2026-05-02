# E59c Style-Controlled Mutual-Verifier Proxy / E59c 风格受控互审代理实验

Date / 日期: 2026-04-28 CST

## 1. Question / 问题

Can the absolute-overaccept vs sibling-recover pattern survive when the same controlled traces are rewritten in the surface style of different P0 models, and when the rewritten traces are judged by both the source model itself and other P0 models? / 当同一批受控 trace 被不同 P0 模型改写成各自表面风格后，再由源模型自己和其他 P0 模型互审，absolute 过度接受、sibling 恢复的模式是否仍然存在？

Plain-language version / 说人话版本：

E59a 只说明三个 P0 verifier 在同一批人工 trace 上都犯类似错误。E59c 往前走一步：让 Qwen/Gemma 把这些 trace 改写成自己的说话风格，但不许修正数学过程。然后我们重新审计这些改写是否保留原来的 valid/invalid 标签，再做 source model × verifier model 矩阵。这样可以初步测试“是不是只因为模型偏好自己风格”以及“互为 verifier 后现象还在不在”。

## 2. Design / 设计

- Source models / 源模型：`qwen35_27b`, `gemma4_31b_it`, `gemma4_26b_a4b_it`.
- Verifier models / verifier 模型：same three P0 models. / 同三个 P0。
- Input traces / 输入 trace：E42 controlled valid/invalid pairs, all final-answer-correct. / E42 受控 valid/invalid 成对 trace，最终答案都正确。
- Rewrite prompt / 改写 prompt：style-transfer only; preserve every mathematical claim and local step; do not correct mistakes. / 只做风格改写；保留每个数学 claim 和局部步骤；不许修正错误。
- Audit / 审计：after rewriting, rows are re-audited for final answer and process-label preservation; repaired/ambiguous rows are dropped. / 改写后重新审计最终答案和过程标签是否保留；被修复或不明确的行剔除。
- Verifier objectives / verifier 目标：absolute Yes/No and order-balanced sibling comparison. / absolute Yes/No 与顺序平衡 sibling comparison。
- Source blinding / 来源盲化：verifier prompt does not reveal source model. / verifier prompt 不告诉 trace 来自哪个模型。

Files / 文件：

- Raw rewrites / 原始改写：`results/E59_style_rewrite_raw/`
- Audited rewritten data / 审计后改写数据：`data/processed/e59c_style_rewrite_audited/`
- Pair configs / 成对配置：`configs/e59c_style_rewrite_pairs/`
- Cross-verifier results / 跨 verifier 结果：`results/E59_cross_verifier_style/`
- Summary / 摘要：`results/E59_cross_verifier_style/summary.json`

## 3. Rewrite audit / 改写审计

Important audit note / 重要审计说明：the first regex audit produced false positives for valid percent-increase and rounding rewrites because the regex was too broad. We manually inspected the dropped rows, corrected the rules, and rebuilt the audited data. / 第一版 regex 审计把有效的涨价与四舍五入改写误判为可疑，因为规则过宽。我们人工检查了被剔除行，修正规则后重建审计数据。

| Source model / 源模型 | Raw rows | Preserved rows | Verifier rows | Pairs | Dropped rows | Main dropped reason / 主要剔除原因 |
|---|---:|---:|---:|---:|---:|---|
| `qwen35_27b` | 24 | 23 | 22 | 11 | 1 | one invalid row repaired/ambiguous / 1 行 invalid 被修复或不明确 |
| `gemma4_31b_it` | 24 | 24 | 24 | 12 | 0 | none / 无 |
| `gemma4_26b_a4b_it` | 24 | 23 | 22 | 11 | 1 | one invalid row repaired/ambiguous / 1 行 invalid 被修复或不明确 |

Plain fact / 事实：most style rewrites preserve the process label, but some models do repair an invalid trace even when instructed not to. Those repaired/ambiguous rows are excluded from verifier matrices. / 大多数风格改写保留了过程标签，但即使明确要求不要修正，模型有时仍会修复 invalid trace；这些行已从 verifier 矩阵剔除。

## 4. Cross-verifier matrix: absolute objective / 跨 verifier 矩阵：absolute objective

Values are invalid-correct accept rates under absolute Yes/No; valid accept rate is 1.00 in every cell. / 数值为 absolute Yes/No 下 invalid-correct 接受率；每个格子的 valid accept rate 都是 1.00。

| Source \ Verifier | `qwen35_27b` | `gemma4_31b_it` | `gemma4_26b_a4b_it` |
|---|---:|---:|---:|
| `qwen35_27b` | 0.545 | 0.545 | 0.636 |
| `gemma4_31b_it` | 0.500 | 0.500 | 0.500 |
| `gemma4_26b_a4b_it` | 0.364 | 0.455 | 0.455 |

Aggregate / 聚合：

- Self-verifier mean invalid accept: 0.500. / 自审均值：0.500。
- Cross-verifier mean invalid accept: 0.500. / 互审均值：0.500。
- Interpretation / 解释：in this style-controlled proxy, over-acceptance is not higher for self-verification than cross-verification. The risk looks more like a shared absolute-objective/threshold issue than a pure self-preference artifact. / 在这个风格受控代理实验中，自审并不比互审更容易接受 invalid trace。风险更像共同的 absolute objective/threshold 问题，而不是纯自偏好 artifact。

## 5. Cross-verifier matrix: sibling comparison / 跨 verifier 矩阵：sibling comparison

Values are contrastive sibling accuracies. / 数值为 sibling comparison 准确率。

| Source \ Verifier | `qwen35_27b` | `gemma4_31b_it` | `gemma4_26b_a4b_it` |
|---|---:|---:|---:|
| `qwen35_27b` | 0.909 | 0.864 | 0.818 |
| `gemma4_31b_it` | 0.958 | 0.958 | 0.958 |
| `gemma4_26b_a4b_it` | 1.000 | 1.000 | 0.955 |

Aggregate / 聚合：

- Self-verifier mean sibling accuracy: 0.941. / 自审 sibling 均值：0.941。
- Cross-verifier mean sibling accuracy: 0.933. / 互审 sibling 均值：0.933。
- Interpretation / 解释：sibling comparison remains much stronger than absolute Yes/No after model-style rewriting, but not perfectly robust for Qwen-source rewrites. / 模型风格改写后，sibling comparison 仍明显强于 absolute Yes/No，但 Qwen 源改写上的稳健性不是完美的。

## 6. Main scientific interpretation / 科学解释

E59c strengthens the method story. / E59c 加强了方法叙事。

- The absolute over-acceptance pattern is not just one model grading one fixed human-written style. / absolute 过度接受不只是某个模型在审某种固定人工文风。
- Self-verifier is a valid object of audit, but E59c shows the same average risk under cross-verification; therefore our main claim should emphasize objective/threshold mismatch more than self-preference. / self-verifier 是合理审计对象，但 E59c 显示互审平均风险相同；因此主张应更强调 objective/threshold 错配，而不是自偏好。
- Model-specific style matters somewhat: Qwen-source rewrites are harder for sibling comparison than Gemma-source rewrites. / 模型风格仍有影响：Qwen 源改写在 sibling comparison 下比 Gemma 源改写更难。
- The rewrite stage itself is informative: models sometimes repair invalid traces despite explicit “do not correct” instructions, suggesting a useful future repair-vs-preserve analysis. / 改写阶段本身也有信息：即使明确要求不要修正，模型有时仍会修复 invalid trace，这提示后续可做 repair-vs-preserve 分析。

## 7. Boundary / 边界

- E59c is still a proxy, not a natural-prevalence experiment. / E59c 仍是代理实验，不是自然发生率实验。
- The rewritten traces derive from controlled E42 traces, so they do not prove spontaneous ACPI generation. / 改写 trace 来自 E42 受控 trace，不证明自然自发生成 ACPI。
- The rewrite audit is conservative and includes manual rule correction, but it is not a full independent two-annotator human labeling study. / 改写审计是保守的并经过人工规则修正，但还不是完整双人标注研究。
- The initial tmux queue had an import bug in the audit step; the bug is archived and fixed, and zero-row verifier outputs were overwritten by successful reruns. / 初始 tmux 队列 audit 步骤有导入错误；该错误已归档并修复，zero-row verifier 输出已被成功重跑覆盖。

## 8. Paper-facing update / 面向论文的更新

Recommended wording / 推荐表述：

Self-verification is treated as an audited deployment pattern rather than a trusted oracle. In a style-controlled mutual-verifier proxy, P0 models rewrite the same controlled traces in their own surface style, and all rewritten rows are re-audited before verifier scoring. The absolute Yes/No over-acceptance rate remains comparable under self- and cross-verification, while sibling comparison continues to expose most process errors. This suggests that the dominant failure is not merely self-preference, but a broader mismatch between pointwise verifier objective/threshold and available process-validity evidence.

中文翻译：我们把 self-verification 视为被审计的部署模式，而不是可信 oracle。在风格受控互审代理实验中，P0 模型把同一批受控 trace 改写成自己的表面风格，所有改写行在 verifier 打分前重新审计。absolute Yes/No 的过度接受率在自审与互审下相近，而 sibling comparison 仍能暴露大多数过程错误。这说明主导失败不只是自偏好，而是单点 verifier objective/threshold 与可用过程有效性证据之间更普遍的错配。
