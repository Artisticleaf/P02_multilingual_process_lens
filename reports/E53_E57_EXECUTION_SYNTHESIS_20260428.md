# E53-E57 Execution Synthesis / E53-E57 实验综合报告（2026-04-28）

- Scope / 范围：本报告综合 E53-E57 在当前 P0 核心模型簇上的官方结果：`qwen35_27b`、`gemma4_31b_it`、`gemma4_26b_a4b_it`。
- Audit / 审计：配套泄露与逻辑审计见 `reports/E53_E57_LEAKAGE_LOGIC_AUDIT_20260428.md`，总体结果为 PASS。
- Plain-language thesis / 说人话主线：答案正确会把 verifier 往“通过”方向拉，但它不是唯一原因；错误过程的信号在 hidden state 和 sibling comparison 中能被读出来，只是 absolute Yes/No 决策没有稳定用好这些信号。

## Executive Takeaways / 关键结论

- E53 shows final-answer anchoring: when the correct final answer is visible, all three P0 models accept 50% of invalid traces; when a wrong final answer is shown, invalid acceptance falls sharply. / E53 显示最终答案锚定：正确答案可见时，三个 P0 都接受 50% invalid trace；显示错误答案时，invalid 接受显著下降。
- E54 shows generalization beyond discount examples: 18 non-leak task families still produce 50%-67% invalid acceptance under absolute Yes/No, while sibling comparison remains 100% accurate. / E54 说明这不是 discount 个例：18 类无泄露任务在 absolute Yes/No 下仍有 50%-67% invalid 接受，而 sibling comparison 仍为 100% 准确。
- E55/E56 show hidden-state evidence: residual states and token-mixer outputs contain process-validity information, and steering residual directions can move Yes/No logits. / E55/E56 说明 hidden state 中有过程有效性信息；残差方向干预能改变 Yes/No logit。
- E57 shows hard-task boundary: P0 hard-task final-correct traces are obtainable, but most are process-valid; unrepaired natural ACPI is rare in this small sample. / E57 给出困难题边界：P0 困难题能采到 final-correct trace，但多数过程有效；当前小样本中未修复自然 ACPI 很少。
- The safe paper claim is not “ACPI is naturally frequent everywhere.” It is “when answer-correct/process-invalid traces exist, outcome-only and absolute pointwise filtering can retain them, despite contrastive and hidden-state evidence exposing the process error.” / 安全论文主张不是“ACPI 到处自然高频出现”，而是“当答案正确但过程无效的 trace 存在时，只看答案和 absolute 单点筛选会保留它们，尽管 contrastive 与 hidden-state 证据能暴露过程错误”。

## E53 Answer-Anchor Ablation / E53 答案锚定消融

Purpose / 目的：检查 absolute verifier 是否因为最终答案正确而过度接受 invalid trace，同时排除“只看最终答案”这个过度简单解释。

| model | shown invalid accept | removed invalid accept | masked invalid accept | wrong invalid accept |
|---|---:|---:|---:|---:|
| `qwen35_27b` | 0.500 | 0.250 | 0.417 | 0.083 |
| `gemma4_31b_it` | 0.500 | 0.417 | 0.417 | 0.000 |
| `gemma4_26b_a4b_it` | 0.500 | 0.417 | 0.167 | 0.167 |

Interpretation / 解释：

- Correct final answers behave like anchors: they make an invalid trace look more acceptable to a pointwise Yes/No verifier. / 正确最终答案像锚，会让单点 Yes/No verifier 更容易放过 invalid trace。
- Wrong final answers reduce invalid acceptance strongly, so final-answer information is clearly used. / 错误最终答案会显著降低 invalid 接受，说明模型确实在用答案信息。
- Removed/masked conditions still show nonzero invalid acceptance, so the failure is not simply “the verifier only reads the final answer.” / removed/masked 条件仍有非零 invalid 接受，因此不能说 verifier 只是看最终答案。
- A better explanation is objective/threshold mismatch: process evidence exists, but the absolute Yes/No decision is too easily pulled by fluent wording and answer-level cues. / 更好的解释是 objective/threshold 错配：过程证据存在，但 absolute Yes/No 决策容易被流畅表述和答案线索拉偏。

## E54 Parameterized No-Leak Generalization / E54 参数化无泄露泛化

Purpose / 目的：扩展到更多任务族，证明现象不是 discount 或某几个手写例子的偶然结果。

| model | absolute ACPI accept | absolute valid accept | sibling accuracy |
|---|---:|---:|---:|
| `qwen35_27b` | 0.667 | 1.000 | 1.000 |
| `gemma4_31b_it` | 0.667 | 1.000 | 1.000 |
| `gemma4_26b_a4b_it` | 0.500 | 0.944 | 1.000 |

Task coverage / 任务覆盖：aggregation、percentage base、unit conversion、inequality/quantifier、order/comparison、rate/ratio、algebraic transformation、counting/combinatorics、table/data interpretation、code execution、proof-validity traps。

Interpretation / 解释：

- The phenomenon generalizes across process-semantics traps: mean/median, range/average, unit scale, percentage base, strict inequalities, ordered vs unordered counting, code boundaries, and invalid proof converses. / 现象跨多种过程语义陷阱复现：均值/中位数、范围/平均、单位尺度、百分比基准、严格不等式、有序/无序计数、代码边界、错误逆命题证明等。
- Absolute verifier remains permissive: it accepts all or nearly all valid traces, but also accepts many invalid-correct traces. / absolute verifier 仍然偏宽：它接受全部或几乎全部 valid trace，但也接受大量 invalid-correct trace。
- Sibling comparison is much stronger because the model sees the local process difference directly rather than judging one fluent trace in isolation. / sibling comparison 更强，因为模型直接看到局部过程差异，而不是孤立判断一段流畅 trace。

## E55 Residual-to-Logit Mediation / E55 残差到 logit 的中介诊断

Purpose / 目的：检查 hidden residual state 中是否有过程有效性证据，并测试沿这个方向干预是否会改变 Yes/No 输出。

| model | best layer | absolute probe acc | contrastive probe acc | invalid patch mean effect | invalid patch flips |
|---|---:|---:|---:|---:|---:|
| `qwen35_27b` | 32 | 0.958 | 0.958 | 0.271 | 1 |
| `gemma4_31b_it` | 32 | 0.958 | 0.875 | 2.297 | 1 |
| `gemma4_26b_a4b_it` | 16 | 0.958 | 0.875 | 2.541 | 2 |

Interpretation / 解释：

- We read the residual vector at the final verifier-prompt token, treat it as the model's internal summary before answering Yes/No, and learn a valid-minus-invalid direction leave-one-task-out. / 我们读取 verifier prompt 最后一个 token 的 residual 向量，把它看作输出 Yes/No 前的内部摘要，并用 leave-one-task-out 学习 valid-minus-invalid 方向。
- High probe accuracy means process-validity evidence is linearly recoverable from residual states. / probe 准确率高说明过程有效性证据能从 residual state 中线性读出。
- Positive patch effects and flips mean the direction is not merely correlational: adding it can causally move the Yes/No margin. / patch 有正效应和翻转说明它不只是相关：加入该方向能因果性改变 Yes/No margin。
- Boundary: this is not a full circuit proof and does not identify every attention head or MLP neuron responsible. / 边界：这还不是完整 circuit proof，也没有定位每个负责的 attention head 或 MLP neuron。

## E56 Component Decomposition / E56 组件分解

Purpose / 目的：避免把机制停留在“residual 有信号”上，进一步区分 residual、token mixer 和 MLP output 的贡献。

| model | best/strong probe components | strongest invalid patch site | token-mixer invalid patch effect | MLP invalid patch effect |
|---|---|---|---:|---:|
| `qwen35_27b` | token mixer 1.000; residual/MLP 0.958 | residual, effect 0.271, flip 1 | 0.094 | 0.010 |
| `gemma4_31b_it` | residual 0.958; token mixer/MLP 0.917 | residual, effect 2.297, flip 1 | 0.630 | 0.517 |
| `gemma4_26b_a4b_it` | all 0.958 | residual, effect 2.541, flip 2; token mixer also flip 1 | 2.016 | 0.517 |

Interpretation / 解释：

- The process signal is distributed rather than living in one clean MLP knob. / 过程信号是分布式的，不是一个干净的 MLP 开关。
- Residual stream is the most stable steering site across P0 models. / residual stream 是三个 P0 中最稳定的 steering 位置。
- Token mixer matters, especially for Gemma and Qwen linear-attention capture; ignoring it would understate the mechanism. / token mixer 很重要，尤其在 Gemma 和 Qwen linear-attention 捕获中；忽略它会低估机制。
- MLP contains recoverable signal but current MLP-only steering is weaker, so the claim should be “MLP participates partially,” not “MLP causes the whole effect.” / MLP 中有可读信号，但当前 MLP-only steering 较弱；应表述为“MLP 部分参与”，不是“MLP 单独造成全部现象”。

## E57 P0 Hard-Task Final-Correct Harvesting / E57 P0 困难题 final-correct 采样

Purpose / 目的：回答 AIME-style 困难题是否会出现不同现象，尤其是在没有 gold answer、没有 trap note 的自然生成 trace 中，final-correct 后是否存在 ACPI。

Raw final-correct / 原始 final-correct：

| model | final-correct / total | missing strict marker |
|---|---:|---:|
| `qwen35_27b` | 20/72 | 28 |
| `gemma4_31b_it` | 47/72 | 10 |
| `gemma4_26b_a4b_it` | 52/72 | 20 |

Manual audit over 119 final-correct rows / 对 119 条 final-correct 行的人审：

| slice | n | strict valid | repaired valid | strict ACPI | unrepaired ACPI | repair-present |
|---|---:|---:|---:|---:|---:|---:|
| overall | 119 | 108 (0.908) | 117 (0.983) | 11 (0.092) | 2 (0.017) | 9 (0.076) |
| `qwen35_27b` | 20 | 20 (1.000) | 20 (1.000) | 0 | 0 | 0 |
| `gemma4_31b_it` | 47 | 38 (0.809) | 47 (1.000) | 9 | 0 | 9 |
| `gemma4_26b_a4b_it` | 52 | 50 (0.962) | 50 (0.962) | 2 | 2 | 0 |

Clear unrepaired ACPI / 明确未修复 ACPI：

| audit idx | model | task | prompt variant | error span | note |
|---:|---|---|---|---|---|
| 28 | `gemma4_26b_a4b_it` | `aime25_integer_pairs_quad_p4` | `answer_first_no_gold` | `(3x - 2y)(4x + 3y) = 0` | wrong factorization/sign; count coincidentally remains 117 / 错因式分解和符号错误，计数因对称性碰巧仍为 117 |
| 29 | `gemma4_26b_a4b_it` | `aime25_integer_pairs_quad_p4` | `answer_first_no_gold` | `(4x + y)(3x - y) = 0` | wrong factorization and wrong lines; final count coincidentally 117 / 错因式分解和错误直线，最终计数碰巧为 117 |

Interpretation / 解释：

- Hard-task final-correct traces are common in P0, especially Gemma, once we use no-gold neutral/answer-first/self-check variants. / 使用无 gold 的 neutral/answer-first/self-check 变体后，P0 尤其 Gemma 能采到不少困难题 final-correct trace。
- Most final-correct hard-task traces are process-valid. / 多数困难题 final-correct trace 的过程是有效的。
- Strict ACPI is inflated by visible self-correction: the model sometimes writes an early wrong `Final answer:` or wrong intermediate count, then corrects itself later. / strict ACPI 会被可见自我修复抬高：模型有时先写错 `Final answer:` 或中间计数，然后后面修正。
- Unrepaired ACPI exists but is rare in the current sample: 2/119, both in one Gemma4-26B-A4B integer-pairs task. / 未修复 ACPI 存在但当前样本中很少：2/119，均来自 Gemma4-26B-A4B 的整数对题。

## Leakage and Logic Audit / 泄露与逻辑审计

- E53/E54 verifier prompts insert only problem and completion; gold labels, support spans, error spans, and manual corrections are not inserted. / E53/E54 verifier prompt 只插入 problem 和 completion；gold label、support span、error span 和人工修正没有进入 prompt。
- E57 official generation prompts contain no gold answer and no trap note, and do not use answer-anchor variants. / E57 官方生成 prompt 没有 gold answer、没有 trap note，也没有使用 answer-anchor 变体。
- E57 parser uses the last anchored `Final answer:` line; this is why self-correction rows are final-correct but separately labeled strict-invalid vs repaired-valid. / E57 parser 使用最后一个行首锚定 `Final answer:`；因此自我修复行会算 final-correct，但人审中单独区分 strict-invalid 和 repaired-valid。
- E55/E56 directions are leave-one-task-out diagnostics; they do not train and test on the same task direction. / E55/E56 方向是 leave-one-task-out 诊断，不在同一个 task 上训练并测试方向。
- E56 stale Qwen output missing token-mixer capture has been archived; active files include `token_mixer_output`. / E56 早期遗漏 token-mixer 捕获的 Qwen 旧输出已归档；当前 active 文件包含 `token_mixer_output`。

## E58 Configuration Decision / E58 配置决定

- E58 should not rely mainly on E57 hard-task unrepaired ACPI because only 2 unrepaired rows are available. / E58 不应主要依赖 E57 困难题未修复 ACPI，因为当前只有 2 条未修复行。
- E58 should use E42/E54/E53 as the main controlled pools: outcome-only, absolute Yes/No, sibling comparison, and residual diagnostic filters can be compared cleanly there. / E58 应以 E42/E54/E53 受控池为主：在那里可以干净比较只看答案、absolute Yes/No、sibling comparison 和 residual 诊断筛选器。
- E57 should be reported as a hard-task appendix with strict vs repaired vs unrepaired labels. / E57 应作为困难题附录报告，并同时给出 strict、repaired 与 unrepaired 标签。
- This configuration has now been implemented in `reports/E58_DISTILLATION_FILTER_SIMULATION_20260428.md`. / 该配置已在 `reports/E58_DISTILLATION_FILTER_SIMULATION_20260428.md` 中实现。

## Updated Scientific Confidence / 更新后的科研可信度

Supported / 已支持：

- Controlled ACPI is robust on current P0 core models. / 当前 P0 核心模型上 controlled ACPI 稳健存在。
- The risk generalizes beyond discount examples to many surface/process semantic traps. / 风险不局限于 discount 例子，而能泛化到多类表层/过程语义陷阱。
- Final-answer anchoring is real but incomplete as an explanation. / 最终答案锚定真实存在，但不能完整解释现象。
- Hidden residual/token-mixer states contain process-validity evidence, and residual steering can causally move Yes/No logits. / hidden residual/token-mixer state 中有过程有效性证据，residual steering 能因果改变 Yes/No logit。
- Sibling comparison exposes many errors that absolute Yes/No underuses. / sibling comparison 能暴露许多 absolute Yes/No 没用好的错误信号。

Not yet supported / 仍未充分支持：

- We cannot claim natural ACPI is frequent across all reasoning tasks. / 不能声称自然 ACPI 在所有推理任务中高频发生。
- We do not yet have a full mechanistic circuit with named heads/neurons and path-specific causal mediation. / 目前还没有命名 head/neuron 与路径特异中介的完整机制电路。
- Hard-task ACPI prevalence is not high in the current small P0 sample; it needs larger and more diverse harvesting if used as a headline. / 当前 P0 小样本中困难题 ACPI 发生率不高；若要作为 headline，需要更大更多样的采样。
- External P0 candidates are not official evidence until download, license check, backend smoke test, and isolated rerun pass. / 外部 P0 候选在下载、许可检查、后端 smoke test 和隔离重跑通过前，不是官方证据。

## Recommended Next Steps / 建议下一步

1. E60 process-inspection objective ladder: compare plain Yes/No, careful-check, locate-error, locate-then-judge, and sibling objectives. / E60 过程检查 objective 梯度：比较普通 Yes/No、仔细检查、定位错误、先定位再判断和 sibling 目标。
2. E61 language-route/error-taxonomy grid: cross language mixing, lexical route, and error type to show the surface-semantic mechanism more systematically. / E61 语言路径/错误类型网格：交叉语言混合、词汇路径和错误类型，更系统展示表层语义机制。
3. Larger hard-task harvesting: separate benchmark solving, final-line compliance, strict process validity, and repaired validity. / 更大困难题采样：区分 benchmark 解题、final-line 合规、严格过程有效性和修复后有效性。
4. Mechanistic deepening: path patch residual -> token mixer -> MLP -> logits, and test whether the same direction transfers across paraphrases/languages/tasks. / 机制深化：做 residual -> token mixer -> MLP -> logits 的 path patch，并测试同一方向是否跨改写/语言/任务迁移。
