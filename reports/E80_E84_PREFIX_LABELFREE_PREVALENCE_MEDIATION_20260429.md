# E80-E84 阶段报告：prefix repair 轨迹、label-free sibling、自然困难题发生率与 GLM readout mediation

日期：2026-04-29  
机器可读汇总：`reports/E80_E84_PREFIX_LABELFREE_PREVALENCE_MEDIATION_20260429.json`

## 0. 一句话结论

这一批实验把主线进一步收紧：模型内部确实能表征过程有效性，但“证据如何进入最终 verifier 决策”高度依赖读出方式。GLM 的失败主要不是看不见错误，而是 raw A/B/Trace 标签读出瓶颈；Gemma26 的两条 unrepaired hard-task ACPI 则显示，最终答案锚定和局部代数错误的隐蔽性仍会让 core P0 strict verifier 漏判。自然困难题池中 unrepaired ACPI 目前低频，但置信区间仍不够窄。

## 1. 实验与审计边界

- `E80 progressive-prefix verifier replay`：同一 strict verifier prompt 下，逐步揭示 hard-task trace 前缀，观察 Yes/No logit margin 与 hidden validity projection 如何变化。
- `E81 label-free sibling across P0`：把 E79 的 label-free two-pass 扩展到 Qwen/Gemma/GLM，并加入 full-option 校验，避免 first-token 对 `Trace 1`/`Trace 2` 只比较同一个首 token `Trace` 的假问题。
- `E82 unrepaired ACPI case ablation`：对 Gemma26 两条 unrepaired quadratic-pairs ACPI 做 final removed/masked/wrong/error-prefix 等消融。
- `E83 natural hard-task prevalence audit`：不跑新推理，汇总已有 no-gold hard-task generation 和人工审计，得到当前 P0/expanded-P0 的自然困难题发生率估计。
- `E84 GLM readout mediation`：比较 hidden validity margin、label-free No-minus-Yes margin、raw A/B margin 三者相关性，定位 GLM 的读出瓶颈。
- 所有实验的 prompt 均不包含人工标签、错误 span 标注或 trap note；人工 span 只用于离线截断、构造 ablation 或评分。

## 2. E80：progressive-prefix repair replay

### 2.1 Gemma31 repaired ACPI

| stage | n | accept rate | mean Yes-No | mean hidden validity |
|---|---:|---:|---:|---:|
| error_span_end | 9 | 0.889 | 7.993 | 0.720 |
| first_final_answer_end | 9 | 1.000 | 10.979 | 1.248 |
| repair_trigger_end | 9 | 0.111 | -11.340 | -2.681 |
| post_repair_240chars | 9 | 0.000 | -13.198 | -2.941 |
| completion_end | 9 | 0.111 | -8.792 | -0.329 |

说人话：Gemma31 的 repaired ACPI 很像“先写了一个看起来完整/自洽的错误答案，直到出现 Wait/However 等修复信号后，strict verifier 才把它当作包含错误步骤的 trace 拒绝”。这支持 strict trace-selection 的必要性：如果你只看前半段或第一个 final answer，模型会非常愿意接受；看到修复动作后，它反而意识到前面是错的。

### 2.2 Gemma26 unrepaired ACPI

| stage | n | accept rate | mean Yes-No | mean hidden validity |
|---|---:|---:|---:|---:|
| error_span_end | 2 | 1.000 | 5.594 | -0.583 |
| first_final_answer_end | 2 | 1.000 | 8.969 | -0.797 |
| completion_end | 2 | 1.000 | 8.969 | -0.797 |

说人话：Gemma26 两条真正未修复 ACPI 在错误因式分解刚出现时就已经被 strict verifier 接受，后续最终答案只让接受更强。hidden projection 是负的，说明内部方向并非完全看不到异常；但 Yes/No 输出头没有把这个异常用成拒绝。这是“hidden evidence -> decision readout mismatch”的强 case study。

### 2.3 E80 边界

- E80 比 E76/E77 更可信，因为它保持同一个 verifier prompt，只改变 visible trace 前缀。
- 但它仍是 teacher-forced 已保存 trace，不等于复现采样时的完整内在生成路径。
- 当前保存的是关键前缀的 logits/projection，不是全层全 token hidden tensor；如果要做头/MLP 级轨迹，还要新增缓存型实验。

## 3. E81：label-free sibling across all P0

### 3.1 首轮 first-token 结果

| model | AB acc | 1/2 acc | First/Second acc | Trace1/Trace2 acc | label-free two-pass acc |
|---|---:|---:|---:|---:|---:|
| qwen35_27b | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 |
| gemma4_31b_it | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 |
| gemma4_26b_a4b_it | 0.979 | 0.969 | 0.969 | 0.500 | 0.917 |
| glm47_flash_candidate | 0.552 | 0.646 | 0.500 | 0.500 | 0.990 |

### 3.2 full-option 校验修正

`Trace 1`/`Trace 2` 的 first-token 打分存在技术假象：两个候选第一个 token 都可能是 `Trace`，所以 first-token 模式无法区分。full-option 后：

| model | Trace1/Trace2 full-option acc | predict-first rate |
|---|---:|---:|
| qwen35_27b | 1.000 | 0.500 |
| gemma4_31b_it | 1.000 | 0.500 |
| gemma4_26b_a4b_it | 0.979 | 0.521 |
| glm47_flash_candidate | 0.781 | 0.719 |

### 3.3 说人话解释

- Core P0 不是依赖 A/B 标签才会 sibling 成功；换成 1/2、First/Second、Trace1/Trace2 full-option 或 label-free two-pass，仍然很强。
- GLM 的 raw A/B/First/Trace 输出明显有位置/标签读出问题，但 label-free two-pass 达到 0.990。这说明 GLM 的 process signal 在 pointwise invalid score 中能释放出来，只是 raw contrastive label 输出头压坏了。
- Gemma26 的 label-free two-pass 低于 raw AB/First/Second，说明 label-free 不是无条件更好；不同模型的最佳 readout 不同。

## 4. E82：Gemma26 两条 unrepaired ACPI 消融

| verifier | original accept | final removed | final masked | final wrong | error-prefix only |
|---|---:|---:|---:|---:|---:|
| qwen35_27b | 2/2 | 2/2 | 2/2 | 0/2 | 1/2 |
| gemma4_31b_it | 2/2 | 2/2 | 2/2 | 0/2 | 2/2 |
| gemma4_26b_a4b_it | 2/2 | 2/2 | 2/2 | 0/2 | 2/2 |
| glm47_flash_candidate | 1/2 | 1/2 | 1/2 | 0/2 | 0/2 |

说人话：

- 把最终答案改错后，所有 verifier 都拒绝，说明 final answer anchor 很强。
- 但把最终答案删掉或 masked 后，Qwen/Gemma 仍多数接受，说明不是“只看 final answer”这么简单；错误因式分解本身也很隐蔽，且后续计数结构看起来自洽。
- GLM 对 error-prefix 更敏感，能拒绝两条错误因式分解前缀；但它原始 full trace 仍接受其中 1 条，说明后续自洽推导/答案锚定会把早期错误稀释。
- 这两条 case 的关键不是表层语言，而是代数等价错误被正确最终计数“巧合掩盖”。它们应成为论文 case study，而不是只放平均数。

## 5. E83：自然困难题发生率审计

E83 汇总已有 no-gold hard-task generation：4 个模型 × 72 条 = 288 条生成；其中 127 条 final-correct 全部已人审。

| model | generated | final-correct | strict ACPI | repaired ACPI | unrepaired ACPI |
|---|---:|---:|---:|---:|---:|
| qwen35_27b | 72 | 20 | 0 | 0 | 0 |
| gemma4_31b_it | 72 | 47 | 9 | 9 | 0 |
| gemma4_26b_a4b_it | 72 | 52 | 2 | 0 | 2 |
| glm47_flash_candidate | 72 | 8 | 0 | 0 | 0 |
| all | 288 | 127 | 11 | 9 | 2 |

总体估计：

- final-correct rate: 127/288 = 0.441, Wilson 95% CI [0.385, 0.499]
- strict ACPI per generated trace: 11/288 = 0.038, CI [0.021, 0.067]
- unrepaired ACPI per generated trace: 2/288 = 0.0069, CI [0.0019, 0.0250]
- strict ACPI conditional on final-correct: 11/127 = 0.087, CI [0.049, 0.148]
- unrepaired ACPI conditional on final-correct: 2/127 = 0.0157, CI [0.0043, 0.0556]

重要分布：所有 strict ACPI 都来自 `answer_first_no_gold`；`neutral` 和 `self_check` 当前为 0 strict ACPI。未修复 ACPI 只出现在 `aime25_integer_pairs_quad_p4`。

说人话：自然 unrepaired ACPI 不是当前样本里的高频现象，但它确实存在，而且集中在答案先写、过程后补的设置里。论文不能声称“自然广泛高频”，但可以说“低频但高危，且一旦进入 outcome-only/weak verifier filter，就会被当作好 trace 留下”。

## 6. E84：GLM hidden-to-readout mediation

GLM 的 E84 结果：

- hidden pair accuracy: 1.000
- label-free pair accuracy: 0.958
- raw A/B order accuracy: 0.542
- raw A/B predict-A rate: 0.938
- hidden margin vs label-free margin Pearson: 0.883；Spearman: 0.845
- hidden margin vs raw A/B margin Pearson: 0.305；Spearman: 0.241
- label-free margin vs raw A/B margin Pearson: 0.278；Spearman: 0.206

说人话：GLM 的 hidden validity signal 与 label-free No-minus-Yes 分数高度一致，但与 raw A/B 输出 margin 相关很弱。也就是说，GLM 内部和 pointwise scoring 都“知道哪条更错”，但 raw A/B 读出没有把这个知道变成正确选择。这是一个很清楚的 readout bottleneck，不是“GLM 没有过程理解”的简单故事。

## 7. 对当前 claim 的更新

当前最稳 claim：

> 多语言/表层语义与过程语义错配可以构造 final-answer-correct 但 strict-process-invalid 的 trace-selection 风险；在自然困难题中，这类风险低频但真实存在，尤其在 answer-first/no-gold 设置中。P0 模型 hidden residual 中有强过程有效性证据，但 pointwise Yes/No、raw A/B sibling、repair-aware reading 与 final-answer anchor 会以不同方式影响证据是否进入最终 verifier 决策。GLM 显示 raw sibling 不是 oracle；label-free readout 可以释放被标签输出头压坏的过程证据。

需要避免的过度表述：

- 不要说自然 unrepaired ACPI 高频；当前只有 2/288 generated、2/127 final-correct。
- 不要说 sibling 永远完美；GLM raw A/B 明显失败，Gemma26 label-free 也不是最强。
- 不要说 hidden probe 已经等于完整机制 circuit；目前证明的是 readout 和相关中介，还不是 head/MLP 级完整因果链。

## 8. 下一步高信息收益实验

1. `E85 hard-task full hidden cache`：对 Gemma26 两条 unrepaired case 和 Gemma31 repaired case 保存全层关键 token hidden/residual/MLP/attention output，用于真正做轨迹机制。
2. `E86 algebra-equivalence adversarial set`：围绕因式分解、等价变形、符号正负、根集合保持/不保持构造 controlled traces，验证 Gemma26 case 是否代表一类代数等价陷阱。
3. `E87 readout intervention`：在 GLM 上把 hidden validity direction steering 到 raw A/B logits，看能否修复 A/B 输出，而不仅仅是相关分析。
4. `E88 natural answer-first larger sample`：只扩展 answer-first/no-gold，因为 E83 显示所有 strict ACPI 都来自该设置；这样信息收益高于均匀扩大所有 prompt。
5. `E89 process-supervision filter simulation with repair policy`：把 strict、repair-aware、label-free、outcome-only 四种筛选器放入同一仿真，估计不同数据治理策略会保留多少 repaired/unrepaired ACPI。

## 9. 审计结论

- 代码语法：E80/E82/E83/E84 脚本 `py_compile` 通过；E80/E84 队列与 E81 full-option 队列 `bash -n` 通过。
- 队列状态：`logs/e80_e84_status_20260429.jsonl` 与 `logs/e81_trace1_fulloption_status_20260429.jsonl` 均为 `all_done`。
- 数据泄露：各结果 JSON 的 leakage audit 均记录 0 标签/0错误 span/0 trap note 注入；E83 不跑新推理，只读已有人审结果。
- 逻辑修正：E81 的 `Trace1/Trace2` first-token 0.5 是打分工件，已用 full-option 校验修正；报告中不把 first-token `Trace1/Trace2` 当科学结论。
