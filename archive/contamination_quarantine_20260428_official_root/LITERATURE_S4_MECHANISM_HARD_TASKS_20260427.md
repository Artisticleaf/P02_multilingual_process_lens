# S4 Literature Refresh: Mechanism, Hard Math, And Model Transfer / S4 文献刷新：机制、困难数学与跨模型迁移

Date / 日期: 2026-04-27 CST
Scope / 范围: 2024-2026 papers and model/dataset sources that were not the main focus of `docs/LITERATURE_AND_NOVELTY_REVIEW_20260427.md`. This round emphasizes causal-chain evidence, hidden-layer/MLP mechanisms, hard math tasks, and Qwen/Gemma transfer feasibility.

中文说明：本轮跳过前一版已经重点覆盖的过程监督基准、多语言 CoT、语言特异神经元、Patchscopes 等通用主题，补充更贴近 S4 的因果链、hidden layer/MLP、困难数学和跨模型迁移证据。

## 1. Process Verifiers And Hard Math / 过程 verifier 与困难数学

| Work / 工作 | Main point / 主要结论 | Collision risk / 撞车风险 | P02 positioning / P02 应如何区别 |
|---|---|---|---|
| Qwen team, `The Lessons of Developing Process Reward Models in Mathematical Reasoning` / “数学推理 PRM 开发经验”, arXiv 2025, https://arxiv.org/abs/2501.07301 | Large-scale PRM development requires detailed data synthesis and evaluation; process reward quality is sensitive to annotation/verification design. / 大规模 PRM 需要细粒度数据合成与评测，过程奖励质量强依赖标注与验证设计。 | High for generic PRM/step-verifier claims. / 泛泛声称“过程监督重要”会撞车。 | P02 should not present itself as a PRM training paper. Our angle is selection risk under answer-correct/process-invalid multilingual traces, plus objective/threshold mismatch in absolute verifiers. / P02 不是训练 PRM，而是研究 ACPI 轨迹选择风险与 verifier 目标错配。 |
| `PRIME: Process Reinforcement through Implicit Rewards`, arXiv 2025, https://arxiv.org/abs/2502.01456 | Implicit process rewards can improve reasoning via online RL-style updates. / 隐式过程奖励可通过在线强化提升推理。 | Medium-high for “process signal can improve reasoning”. | P02 complements rather than competes: we show hidden/process signals may exist but a simple absolute Yes/No verifier does not reliably use them, especially under surface lexical traps. / P02 关注“有信号但 verifier 未正确使用”的错配。 |
| `ProcessBench`, arXiv 2024, https://arxiv.org/abs/2412.06559 | A benchmark for identifying process errors in reasoning traces. / 推理过程错误识别基准。 | High for benchmark framing. | P02 must avoid claiming a general process-error benchmark; use selected real ACPI pairs as causal/mechanistic probes. / 不写成通用 benchmark，而写成真实 ACPI 因果 probe。 |
| `Outcome-Process Consistency in Mathematical Reasoning`, arXiv 2026, https://arxiv.org/abs/2602.11570 | Directly studies consistency between final answers and reasoning processes. / 直接研究答案-过程一致性。 | Very high for the broad “answer/process inconsistency” phrase. | P02's safer novelty is the multilingual/surface lexical ACPI subset, verifier over-acceptance, sibling comparison, and residual/module span patch evidence. / 我们的新意要落在“多语言表层词汇化 + verifier 过度接受 + hidden/span 因果信号”。 |
| AIME 2024/2025 public HF datasets, https://huggingface.co/datasets/TianHongZXY/AIME2024 and https://huggingface.co/datasets/TianHongZXY/AIME2025 | Harder math tasks with compact final integer answers. / 更困难且答案为整数的数学任务。 | Low as a data source, high if we overclaim benchmark-scale evaluation. | Use as stress-test: ACPI may become rarer because final-correct traces are rare; this tests whether P02 is simple-task-specific. / 作为压力测试，不宣称完整 AIME benchmark。 |

## 2. Hidden Layers, MLP, And Output Reorganization / 隐藏层、MLP 与输出端重整

| Work / 工作 | Main point / 主要结论 | Collision risk / 撞车风险 | P02-specific opening / P02 可创新切口 |
|---|---|---|---|
| `Reasoning Circuits in Language Models: A Case Study of Modular Arithmetic and Planning`, Findings ACL 2025, https://aclanthology.org/2025.findings-acl.525/ | Circuit-level analyses can reveal algorithmic components behind specific reasoning tasks. / 可在特定推理任务上定位 circuit 组件。 | Medium for “reasoning circuits” as a general claim. | We should not claim full circuits yet. S4 can claim a narrower `verifier-decision lens`: non-verdict spans and MLP outputs causally move verifier margins on real ACPI sibling pairs. / 不声称完整 circuit，只声称真实 ACPI verifier 决策中的 span/MLP 因果信号。 |
| `Transfer Neurons in Large Language Models`, EMNLP 2025, https://aclanthology.org/2025.emnlp-main.1618/ | Cross-lingual behavior can involve identifiable transfer-related neurons. / 跨语言行为可涉及可识别的 transfer neurons。 | Medium for multilingual hidden-unit novelty. | P02 differs because the target variable is process validity/error-span, not language identity or generic transfer. / P02 的变量是过程有效性/错误 span，不是语言身份。 |
| Multilingual concept/representation papers from the previous review, e.g. `Separating Tongue from Thought`, ACL 2025, https://aclanthology.org/2025.acl-long.1536/ | Hidden states may separate language form from conceptual content. / 隐藏状态可能分离语言外壳与概念内容。 | High if we claim “language-agnostic concept representation”. | P02 should instead test `surface lexicalization -> mid-layer process confusion -> final verifier over-accept` as a task-specific chain. / 应测任务特异链条：表层词汇化 -> 中层过程混杂 -> 输出端过度接受。 |
| Anthropic attribution-graph line of work, 2025, https://transformer-circuits.pub/2025/attribution-graphs/biology.html | Attribution graphs can describe computations inside a large LM. / attribution graph 可描述大模型内部计算。 | Low-medium method collision. | P02 can cite it as aspirational mechanistic standard; our current evidence is residual/module patch plus logit lens, not a full attribution graph. / 作为机制标准参考，避免过度声称。 |

## 3. New Mechanistic Hypotheses For P02 / P02 可形成的新机制假设

### H1. Middle-layer process confounding / 中层过程混杂

English: In multilingual/surface-trap traces, middle layers may represent both the surface lexical cue (e.g., “打八折”, “80% discount”) and the local arithmetic/process semantics. When the cue is lexically mistranslated but the arithmetic accidentally keeps the final answer correct, middle-layer states can be causally ambiguous: patching support/error spans or MLP outputs moves verifier margins, but not always in a clean universal direction.

中文：在多语言/表层陷阱 trace 中，中层可能同时表示表层词汇线索（如“打八折”“80% discount”）与局部算术/过程语义。当词汇被错误转写但算术偶然得到正确答案时，中层状态可能混杂；patch support/error span 或 MLP 输出会移动 verifier margin，但不保证每个 pair 都干净成立。

### H2. Output-head re-entanglement / 输出头重整或再纠缠

English: Even when middle layers contain a process/error signal, the final output head can re-entangle that signal with final-answer correctness, fluency, language prior, or Yes-bias, causing absolute Yes/No over-acceptance. A layerwise verifier logit lens can test this by looking for middle positive error/target margins that vanish or reverse at the final layer.

中文：即使中层含有过程/错误信号，最终输出头仍可能把该信号与最终答案正确性、流畅度、语言先验或 Yes-bias 再纠缠，导致绝对式 Yes/No 过度接受。分层 verifier logit lens 可检验“中层有信号、输出层消失或反转”的现象。

### H3. Objective-threshold bottleneck / 目标-阈值瓶颈

English: Absolute verifiers are not just weak detectors; their binary objective and threshold can map ambiguous process evidence to acceptance. Contrastive sibling prompts lower the threshold for using relative error evidence on some pairs, while hard same-route Qwen14 `打八折` remains a boundary case.

中文：绝对 verifier 不只是“检测能力弱”；二元目标与阈值会把模糊的过程证据映射为接受。兄弟对比在部分 pair 中降低了使用相对错误证据的门槛，但 Qwen14 同 route 的 `打八折` 仍是边界负例。

## 4. Hard-Task Implications / 困难任务启示

- AIME-style tasks may reduce observable ACPI because final-correct traces are rarer; this can turn the phenomenon from “many bad traces accepted” into “few correct traces, but accepted traces still require process audit”. / AIME 难题可能让 ACPI 观测率下降，因为 final-correct 更少。
- Hard tasks are still valuable as a negative control: if nearly all failures are final-wrong, P02 should not overgeneralize simple-task ACPI frequency. / 难题可作为负控，避免把简单任务频率外推。
- The strongest hard-task test is not raw AIME accuracy; it is whether final-correct hard traces show hidden process disagreement or absolute over-acceptance. / 最强测试不是 AIME 准确率，而是 final-correct hard trace 是否仍有 hidden process disagreement 或 absolute over-acceptance。

## 5. Model Transfer Feasibility / 跨模型迁移可行性

| Model / 模型 | Source / 来源 | Status / 状态 | Experimental note / 实验注意 |
|---|---|---|---|
| Qwen3.5-27B | https://huggingface.co/Qwen/Qwen3.5-27B | Public model card; HF mirror reports ~55.6 GB files. / 公开模型卡；HF mirror 元数据显示约 55.6GB。 | Needs multi-GPU loading. Updated `load_causal_lm(device="auto")` to pass `device_map="auto"`. / 需要多卡加载，已更新 loader。 |
| Google Gemma/Gamma4 `gemma-4-E4B-it` | https://huggingface.co/google/gemma-4-E4B-it | Public model card; HF mirror reports ~16.0 GB files. / 公开模型卡；约 16GB。 | Text-only loader may need `AutoModelForImageTextToText`; current fallback already tries this path. / 可能需多模态 text loader，当前 fallback 已覆盖。 |

## 6. Collision Assessment / 撞车评估

High collision / 高撞车：

1. “Process verification matters for math.” / “数学推理需要过程验证。”
2. “Answer/process inconsistency exists.” / “答案和过程可能不一致。”
3. “Multilingual hidden states contain transfer or concept signals.” / “多语言隐藏层有 transfer/concept 信号。”
4. “Mechanistic interpretability can find circuits.” / “机制解释可找 circuit。”

Lower-collision P02 claim / 更低撞车的 P02 主张：

> Multilingual surface lexicalization creates a selected but realistic ACPI trace family where final-answer correctness, local process semantics, and verifier objective/threshold disagree. The process/error signal can be exposed by sibling comparison and residual/module span patch on robust pairs, while absolute Yes/No verifiers frequently over-accept; hard Qwen14 cases show this mitigation is not universal.
>
> 中文：多语言表层词汇化产生一类真实 ACPI trace，其中最终答案正确性、局部过程语义和 verifier 目标/阈值彼此错配。稳健 pair 中，兄弟对比与 residual/module span patch 可暴露过程/错误信号，但绝对式 Yes/No verifier 常过度接受；Qwen14 困难例表明 mitigation 并非万能。

## 7. Recommended S4 Experiments / 推荐 S4 实验

1. Build a causal-chain ledger linking manual ACPI -> absolute over-accept -> contrastive visibility -> residual/module patch. / 构建人工 ACPI、绝对过度接受、对比可见性、hidden patch 的链式台账。
2. Run layerwise verifier logit lens to test middle-layer signal vs output-head re-entanglement. / 运行分层 verifier lens 检验中层信号与输出端再纠缠。
3. Run small AIME24/25 multilingual hard-task smoke; treat low final-correct rate as an informative boundary, not a failure. / 跑小规模 AIME24/25 多语言难题 smoke，把低 final-correct 视为边界信息。
4. Pull Qwen3.5-27B and Gemma/Gamma4 E4B through HF mirror; if loading works, rerun E18/E26 small smokes. / 通过 HF mirror 拉取 Qwen3.5-27B 与 Gemma/Gamma4 E4B；若可加载，复跑 E18/E26 小实验。
