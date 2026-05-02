# E42 Gap Analysis And Next Experiments / E42 缺口分析与下一阶段实验规划

Date / 日期: 2026-04-28 CST

## 1. What is still missing for a top-conference paper / 要做成顶会级工作还缺什么

**Gap A: controlled evidence is now broad, but natural prevalence is still not proven. / 缺口 A：受控证据已经变宽，但自然发生率仍未证明。**

E39 expands from discount and E31's five traps to 12 controlled surface-semantic families. This is strong for mechanism and possibility, but it is still manually constructed. A top paper should separate two claims: (i) this failure mode is causally real under controlled lexical semantics; (ii) how often it appears in natural generated traces. / E39 从折扣和 E31 的 5 类陷阱扩展到 12 类受控表层语义族。它强在机制和可诱发性，但仍是人工构造。顶会论文必须区分两个主张：（i）这种失败模式在受控词汇语义下因果真实；（ii）它在自然生成 trace 中多常见。

**Gap B: hidden-state evidence is strong at residual level, but still shallow at circuit level. / 缺口 B：隐藏层证据在 residual 层很强，但 circuit 层仍浅。**

E33/E34/E40 show many clean residual span-patch effects. E35/E41 show MLP participation. But single-module effects are smaller than residual effects, and we have not shown reusable features, path-level causal mediation, or ablation/steering that flips final decisions. / E33/E34/E40 显示很多干净 residual span-patch 效应。E35/E41 显示 MLP 参与。但单模块效应小于 residual，而且我们还没有证明可复用 feature、路径级因果中介，或能翻转最终决策的消融/steering。

**Gap C: objective/threshold mismatch is supported, but the objective matrix should be systematic on E39. / 缺口 C：目标/阈值错配已有证据，但 E39 上还需要系统 objective matrix。**

E29/E31 locate-then-judge showed that stronger localization objectives can recover errors missed by absolute Yes/No. E39 now supplies 12 new families; we should run the same objective matrix on E39: absolute, training-candidate, contrastive sibling, locate-only, locate-then-judge, answer-masked. / E29/E31 的 locate-then-judge 已说明更强定位目标能恢复 absolute Yes/No 漏掉的错误。E39 现在提供 12 个新语义族；应在 E39 上系统比较 absolute、training-candidate、contrastive sibling、locate-only、locate-then-judge、answer-masked。

**Gap D: hard tasks remain under-conditioned. / 缺口 D：难题还没有得到足够 final-correct trace 条件化。**

Previous AIME smoke found few or no strict final-correct traces, so it mostly tested model generation difficulty rather than ACPI. The next hard-task step should first condition on final-correct traces using strong samplers/verifiers, then audit process validity. / 之前 AIME smoke 几乎没有严格 final-correct trace，所以主要测的是生成难度，而不是 ACPI。下一步难题实验应先用强模型/筛选器获得 final-correct trace，再审计过程有效性。

## 2. New experiments completed in this stage / 本阶段已完成的新实验

### E39: broader controlled generalization / E39：更宽的受控泛化

Design / 设计：12 surface-semantic families × 6 variants = 72 rows. Families include mean/median, range/average, coefficient/exponent, reciprocal/additive inverse, percent increase/percent-of, without-replacement, each-vs-total, log base/argument, round/truncate, Chinese perimeter/area, Chinese 亿/万, and Chinese strict interval. / 12 类表层语义族 × 6 个变体 = 72 行，覆盖均值/中位数、极差/平均、系数/指数、倒数/相反数、增长百分比/原价百分比、无放回、每人/总量、log 底数/真数、四舍五入/截断、中文周长/面积、亿/万、中文严格区间。

Key process-only ACPI false accept / 关键只审过程 ACPI 误接受：

| verifier | English prompt | Chinese prompt | plain fact / 人话解释 |
|---|---:|---:|---|
| Qwen3.5-27B | 1.000 | 0.833 | Large Qwen over-accepts almost all E39 ACPI under English prompts. / 大 Qwen 在英文提示下几乎全接受 E39 ACPI。 |
| Qwen3.5-9B | 0.750 | 0.833 | Smaller Qwen3.5 also strongly over-accepts. / 小 Qwen3.5 也明显过度接受。 |
| Qwen3-14B-Base | 0.250 | 0.250 | Qwen14 is stricter under process-only, but not under all objectives. / Qwen14 只审过程更严格，但不是所有目标都严格。 |
| Gemma4-31B-it | 0.500 | 0.417 | Gemma31 is stricter than Qwen3.5 but still accepts many ACPI rows. / Gemma31 比 Qwen3.5 严格，但仍接受不少 ACPI。 |

Important objective fact / 重要目标事实：Gemma31's training-candidate objective reduces E39 ACPI acceptance to `0.083/0.083`, and Qwen35-27B Chinese training-candidate drops to `0.083`, but Qwen35-27B English training-candidate remains `0.833`. This shows objective and prompt language jointly set the threshold. / Gemma31 的 training-candidate 目标把 E39 ACPI 接受率降到 `0.083/0.083`，Qwen35-27B 中文 training-candidate 降到 `0.083`，但 Qwen35-27B 英文 training-candidate 仍为 `0.833`。这说明目标与提示语言共同决定阈值。

Files / 文件：`data/processed/e39_surface_semantic_generalization_20260428.jsonl`, `reports/E39_surface_semantic_generalization_summary_20260428.md`.

### E40: residual hidden evidence generalizes / E40：residual 隐藏证据泛化

E40 patches support/error spans on all 12 E39 pairs. / E40 在 E39 全部 12 对 support/error span 上做 residual patch。

| model | clean residual pairs | strongest example / 最强例子 | meaning / 含义 |
|---|---:|---|---|
| Qwen3.5-9B | 11/12 | Chinese strict interval L8 `+3.062/-4.187` | Hidden process evidence is widespread even when the absolute verifier accepts. / 即使 absolute verifier 接受，隐藏过程证据仍广泛存在。 |
| Qwen3-14B-Base | 10/12 | each-vs-total L12 `+2.500/-3.750` | The S6/E31 mechanism generalizes to new semantic families. / S6/E31 的机制泛化到新语义族。 |

Boundary facts / 边界事实：round-vs-truncate is weak for Qwen14 and near-zero for Qwen35 despite high acceptance; zh 亿/万 is weak for Qwen14 but clean for Qwen35. These should be treated as boundary/heterogeneity, not hidden in averages. / round-vs-truncate 对 Qwen14 弱、对 Qwen35 近零但高接受；中文亿/万对 Qwen14 弱、对 Qwen35 干净。它们应作为边界异质性处理，不能被平均值掩盖。

Files / 文件：`reports/E40_surface_semantic_span_patch_summary_20260428.md`.

### E41: MLP participates, but not a full circuit yet / E41：MLP 参与，但还不是完整 circuit

E41 decomposes selected E40 residual effects into attention/linear-attention vs MLP outputs. / E41 把部分 E40 residual 效应拆到 attention/linear-attention 与 MLP 输出。

Key facts / 关键事实：

- Qwen3.5-9B: best module is MLP on all four selected pairs; effects are small but clean, e.g. each-vs-total L4 `+0.375/-0.062`. / Qwen3.5-9B 四个 pair 的最强模块都是 MLP，效应小但干净，例如 each-vs-total L4 `+0.375/-0.062`。
- Qwen14: Chinese strict interval has the strongest module result, MLP L20 `+0.500/-0.250`; other pairs are weaker. / Qwen14 最强模块结果是中文严格区间 MLP L20 `+0.500/-0.250`；其他 pair 较弱。
- The module effects are much smaller than residual effects, so the safest mechanism claim remains distributed middle residual-state evidence with MLP participation. / 模块效应显著小于 residual 效应，所以最安全机制主张仍是：分布式中层 residual-state 证据，并有 MLP 参与。

Files / 文件：`reports/E41_surface_semantic_module_patch_summary_20260428.md`.

## 3. How this changes the paper claim / 这如何改变论文主张

Before E39-E41, the main weakness was that non-discount generalization rested on E31's five controlled traps. After E39-E41, the claim is stronger: the same ACPI/verifier mismatch pattern appears across 12 additional surface-semantic families, four verifier models, and two model families; hidden support/error-span evidence generalizes across 10/12 or 11/12 pairs in two probe models. / E39-E41 之前，非折扣泛化主要依赖 E31 的 5 类受控陷阱。E39-E41 之后，主张更强：同样的 ACPI/verifier 错配模式出现在额外 12 类表层语义族、4 个 verifier 模型、2 个模型家族上；hidden support/error-span 证据在两个 probe 模型中分别泛化到 10/12 与 11/12 对。

Still unsafe / 仍不安全的说法：

- Do not claim natural prevalence yet. / 暂不声称自然高发。
- Do not claim a single MLP/head circuit. / 不声称单个 MLP/head circuit。
- Do not claim all LLM reasoning requires a verifier. / 不声称所有 LLM 推理都必须有 verifier。

Safer publishable wording / 更安全的发表表述：

> In verifier- or selector-mediated reasoning pipelines, surface-semantic lexicalization can create answer-correct but process-invalid traces. Across controlled multilingual and English/Chinese surface-semantic traps, absolute Yes/No verifiers often over-accept these traces. The failure is not pure blindness: sibling/objective changes and residual support/error-span patching reveal hidden process evidence, but final verifier objectives and thresholds underuse or re-entangle it with answer correctness and downstream correction.
>
> 在 verifier/selector 介入的推理管线中，表层语义词汇化会产生“答案正确但过程无效”的 trace。在受控多语言和中英文表层语义陷阱中，绝对式 Yes/No verifier 经常过度接受这些 trace。这不是纯粹看不见错误：sibling/objective 改变和 residual support/error-span patch 能暴露隐藏过程证据，但最终 verifier 目标和阈值没有充分使用这些证据，或者把它与答案正确和下游修正重新纠缠。

## 4. Next experiments with highest information gain / 下一步最高信息收益实验

### P0. E42 objective matrix on E39 / P0：E39 目标矩阵

Run contrastive sibling, locate-only, locate-then-judge, answer-masked, and calibrated-margin variants on the same 12 E39 families. / 在同一批 12 个 E39 家族上跑 contrastive sibling、locate-only、locate-then-judge、answer-masked、calibrated-margin。

Expected result / 希望看到：absolute Yes/No over-accepts; locate-then-judge and contrastive recover more invalid spans; answer-masked reduces answer-driven acceptance. / 预期：absolute Yes/No 过度接受；locate-then-judge 与 contrastive 找回更多错误 span；answer-masked 降低答案驱动接受。

Why it matters / 为什么重要：this directly tests the objective/threshold part of the causal chain. / 这直接检验因果链中的目标/阈值环节。

### P1. E43 paraphrase-transfer hidden patch / P1：跨改写 hidden patch

For each robust E40 family, create 2-3 paraphrased valid/invalid traces with the same process semantics but different wording. Patch a residual/MLP vector learned from one wording into another. / 对每个稳健 E40 家族构造 2-3 个同语义不同表述的 valid/invalid trace，把一个表述中的 residual/MLP 向量 patch 到另一个表述。

Expected result / 希望看到：if the effect transfers, it is more likely a semantic process signal; if it fails, the signal may be lexical-token-specific. / 如果能迁移，更像过程语义信号；如果不能，更可能只是词面 token 信号。

Why it matters / 为什么重要：this is the key difference between a top-paper mechanism claim and a local patch artifact. / 这是顶会机制主张和局部 patch artifact 的关键区别。

### P2. E44 causal ablation/steering of MLP direction / P2：MLP 方向的因果消融/steering

Build a valid-minus-invalid direction at the strongest E41 MLP layers, subtract it from valid traces or add it to invalid traces, and measure whether final Yes/No decisions flip. / 在 E41 最强 MLP 层构造 valid-minus-invalid 方向，对 valid trace 做减法或对 invalid trace 做加法，测最终 Yes/No 是否翻转。

Expected result / 希望看到：directional interventions change margins and sometimes flip final decisions. / 方向干预能改变 margin，并在部分样例上翻转最终决策。

Why it matters / 为什么重要：patching shows local causal association; ablation/steering tests whether a reusable direction controls the decision. / patching 说明局部因果关联；消融/steering 检验是否存在可复用方向控制决策。

### P3. E45 natural harvesting for E39 families / P3：E39 家族自然生成挖掘

Generate many traces around the 12 E39 families with Qwen35-27B/Gemma31, filter final-correct traces, then audit process validity. / 用 Qwen35-27B/Gemma31 围绕 12 个 E39 家族生成多条 trace，先筛 final-correct，再审计过程有效性。

Expected result / 希望看到：some families naturally produce ACPI; others do not. / 预期有些族自然产生 ACPI，有些不产生。

Why it matters / 为什么重要：this separates controlled possibility from natural prevalence. / 这能区分受控可诱发性与自然发生率。

### P4. E46 hard-task final-correct conditioning / P4：难题 final-correct 条件化

For AIME24/25, use strong samplers and verifier-guided selection to first obtain final-correct traces, then audit process validity and run verifier tests. / 对 AIME24/25，先用强采样与 verifier-guided selection 获得 final-correct trace，再审计过程有效性并跑 verifier。

Expected result / 希望看到：ACPI may be rarer, but if it appears it will be more publishable because it is no longer a simple-task artifact. / ACPI 可能更少，但如果出现，会更有发表价值，因为不再是简单题 artifact。

## 5. Literature boundary / 文献边界

Recent verifier/process work already covers broad process-error identification and process/outcome consistency: ProcessBench evaluates earliest error identification in math traces; PRMBench evaluates fine-grained PRM error detection; Right Is Not Enough directly warns that correct answers can hide unsound reasoning; PRIME studies process-outcome alignment for verifiable reasoning. / 近期 verifier/process 工作已经覆盖宽泛的过程错误识别与答案-过程一致性：ProcessBench 评测数学 trace 的 earliest error；PRMBench 评测 PRM 的细粒度错误检测；Right Is Not Enough 直接指出正确答案会掩盖错误过程；PRIME 研究可验证推理中的过程-结果对齐。

Therefore our novelty must not be “correct answer can hide wrong reasoning.” It must be the conjunction: surface-semantic/multilingual lexical traps, verifier objective/threshold mismatch, sibling/objective recovery, and hidden support/error-span causal evidence. / 因此我们的创新不能写成“正确答案会掩盖错误推理”。必须是组合创新：表层语义/多语言词汇陷阱、verifier 目标/阈值错配、sibling/objective 恢复、hidden support/error-span 因果证据。

Mechanistic interpretability work such as Patchscopes and reasoning-circuit papers sets a higher bar: residual and module patching is useful, but full circuit claims need transfer, sufficiency/necessity, and ablation controls. / Patchscopes 与 reasoning-circuit 类机制工作提高了标准：residual 和 module patch 有用，但完整 circuit 主张需要迁移、充分/必要性和消融控制。

Sources / 参考：

- ProcessBench: https://arxiv.org/abs/2412.06559
- PRMBench: https://arxiv.org/abs/2501.03124
- Right Is Not Enough: https://arxiv.org/abs/2506.06877
- PRIME process-outcome alignment: https://arxiv.org/abs/2602.11570
- Patchscopes: https://arxiv.org/abs/2401.06102
- Reasoning Circuits in LMs: https://aclanthology.org/2025.findings-acl.525/

## 6. Reliability audit / 可靠性审计

- E39 is a hand-built diagnostic set, not a training benchmark submission; leakage risk is low but natural-prevalence claims are not allowed. / E39 是手工诊断集，不是训练基准提交；泄露风险低，但不能据此声称自然发生率。
- All E39 rows passed integrity checks: 72 unique rows, 12 tasks, 6 balanced variants, exact support/error span presence, and correct ACPI labeling. / E39 完整性检查通过：72 个唯一行、12 个任务、6 个均衡变体、support/error span 精确存在、ACPI 标签正确。
- E39 verifier results exist for Qwen35-27B, Qwen35-9B, Qwen14, and Gemma31; E40/E41 mechanism outputs exist for Qwen35-9B and Qwen14. / E39 verifier 结果覆盖 Qwen35-27B、Qwen35-9B、Qwen14、Gemma31；E40/E41 机制输出覆盖 Qwen35-9B 与 Qwen14。
- Code compile checks and `scripts/check_project.py` passed after E39/E40/E41. / E39/E40/E41 后代码编译与 `scripts/check_project.py` 通过。

Audit logs / 审计日志：`logs/audit_e39_e40_e41_20260428.json`, `logs/check_project_e39_e40_e41_20260428.json`.
