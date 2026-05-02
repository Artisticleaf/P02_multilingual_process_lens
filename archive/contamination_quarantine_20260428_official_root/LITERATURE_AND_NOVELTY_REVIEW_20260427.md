# Literature And Novelty Review / 文献与创新性复核

Date / 日期: 2026-04-27 CST

## Scope / 范围

This review targets 2023-2026 work related to process supervision, verifier reliability, multilingual reasoning, hidden-state interpretability, and LLM-as-judge bias. It is meant to check collision risk and sharpen the current claim.

中文说明：本综述检索 2023-2026 年与过程监督、verifier 可靠性、多语言推理、隐藏层可解释性、LLM-as-judge 偏差相关的顶会/顶刊或高影响论文，用于确认本项目主张是否撞车，以及如何把证据链做得更扎实。

## 1. Process Supervision And Verifier Benchmarks / 过程监督与 verifier 基准

| Work / 工作 | Main point / 主要结论 | Collision risk / 撞车风险 | Difference from P02 / 与本项目差异 |
|---|---|---|---|
| Lightman et al., `Let's Verify Step by Step` / “让我们逐步验证”, ICLR 2024, https://openreview.net/forum?id=v8L0pN6EOi | Process reward models can outperform outcome supervision for mathematical reasoning. / 过程奖励模型可优于只看最终答案的监督。 | High for generic “process supervision matters”. / 若只说过程监督重要，会撞车。 | P02 is not proposing a new PRM; it studies answer-correct/process-invalid traces under multilingual surface traps and shows absolute Yes/No verifiers over-accept while sibling/hidden-span signals can expose errors. |
| Wang et al., `Math-Shepherd` / “数学牧羊人：无人工标注逐步验证”, ACL 2024, https://aclanthology.org/2024.acl-long.510/ | Automatically constructs process-level supervision for math steps. / 自动构造数学步骤级监督。 | Medium for step-level verification. / 与步骤级 verifier 相关。 | P02's novelty is not cheaper PRM annotation; it is the mismatch among surface lexicalization, process semantics, verifier objective/threshold, and hidden span evidence. |
| `ProcessBench: Identifying Process Errors in Mathematical Reasoning` / “ProcessBench：识别数学推理过程错误”, 2024/2025, https://arxiv.org/abs/2412.06559 | Benchmarks process-error identification in reasoning traces. / 为过程错误识别建立基准。 | High for “find reasoning errors” framing. | P02 should avoid presenting itself as just another process-error benchmark; it contributes a controlled multilingual ACPI failure family plus causal hidden-state probes and sibling comparison. |
| `PRMBench: A Fine-grained and Challenging Benchmark for Process-Level Reward Models` / “PRMBench：细粒度且具有挑战性的过程奖励模型基准”, 2025, https://arxiv.org/abs/2501.03124 | Fine-grained PRM evaluation. / 细粒度评测过程奖励模型。 | High if P02 claims benchmark novelty. | P02 can use PRMBench-style framing as related work, but its claim is mechanistic and selection-risk oriented. |
| BIG-Bench Mistake / “大基准错误：LLM 能否发现并纠正推理错误”, ACL Findings 2024, https://aclanthology.org/2024.findings-acl.826/ | LLMs often struggle to locate reasoning mistakes even when correction may be possible. / LLM 常常难以定位错误。 | Medium for verifier failure. | P02 adds answer-correct/process-invalid risk, multilingual lexical traps, and contrast between absolute and sibling objectives. |

## 2. LLM-As-Judge Bias And Selection Risk / LLM 裁判偏差与选择风险

| Work / 工作 | Relevant point / 相关点 | Implication for P02 / 对 P02 的启示 |
|---|---|---|
| `Large Language Models are not Fair Evaluators` / “大语言模型不是公平评估器”, ACL 2024, https://aclanthology.org/2024.acl-long.511/ | LLM evaluators can show position, verbosity, and self-enhancement biases. / LLM 裁判有位置、冗长、自我偏好等偏差。 | All contrastive experiments must balance `bad_A`/`bad_B`; P02 has done this in E16/E21/E23. |
| RewardBench and multilingual reward-model follow-ups / RewardBench 与多语言奖励模型评测 | Reward/verifier behavior depends on objective, prompt, language, and benchmark. / reward/verifier 受目标、提示、语言与基准影响。 | P02 should phrase verifier failure as objective/threshold and prompt-conditioned mismatch, not as “models cannot verify”. |

## 3. Multilingual Reasoning And Surface Lexicalization / 多语言推理与表层词汇化

| Work / 工作 | Main point / 主要结论 | Difference from P02 / 与本项目差异 |
|---|---|---|
| Shi et al., `Language Models are Multilingual Chain-of-Thought Reasoners` / “语言模型是多语言思维链推理器”, ICLR 2023, https://openreview.net/forum?id=fR3wGCk-IXp | Multilingual chain-of-thought can work across languages. / 多语言 CoT 可跨语言工作。 | P02 is not a broad multilingual CoT performance paper; it focuses on surface semantic traps such as 七五折/pay75 vs 75% off/pay25. |
| mCoT / “多语言指令调优提升推理一致性”, ACL 2024 | Multilingual instruction tuning can improve reasoning consistency. / 多语言指令调优可提升一致性。 | P02 studies failure modes and trace-selection risk rather than tuning for higher accuracy. |
| Language confusion and latent-language work / “语言混淆与潜在语言”系列 | Multilingual models can internally route through dominant languages or confuse output language. / 多语言模型可能存在语言路由与输出语言混淆。 | P02 should not claim generic language routing novelty; its sharper novelty is lexicalized process semantics that stays hidden from absolute verifiers. |

## 4. Hidden-State Interpretability / 隐藏状态可解释性

| Work / 工作 | Main point / 主要结论 | Collision risk / 撞车风险 | Difference from P02 / 与本项目差异 |
|---|---|---|---|
| `Language-Specific Neurons` / “语言特异神经元”, ACL 2024, https://aclanthology.org/2024.acl-long.309/ | Identifies language-specific neurons in multilingual LMs. / 识别多语言模型中的语言特异神经元。 | Medium for multilingual hidden representations. | P02 should not claim first discovery of language-specific hidden units; it asks whether process-validity/error-span signals are causally usable under verifier mismatch. |
| `Separating Tongue from Thought` / “把语言外壳与思想表征分离”, ACL 2025, https://aclanthology.org/2025.acl-long.1536/ | Activation patching reveals language-agnostic concept representations. / activation patching 可揭示语言无关概念表征。 | High for language-agnostic hidden concept claims. | P02's hidden-state branch must be framed as process/error-span localization in trace verification, not as a general concept-bridge claim. E08 already downgraded broad contextual-bridge claims. |
| `Patchscopes` / “Patchscopes：检查语言模型隐藏表征的统一框架”, 2024/2025, https://arxiv.org/abs/2401.06102 | Uses patching to inspect hidden representations. / 用 patching 检查隐藏表征。 | Medium for methodology. | P02 uses patching as causal evidence for process-validity signals in real sibling traces, not as a new interpretability method. |
| Anthropic, `On the Biology of a Large Language Model` / “大型语言模型的生物学”, 2025, https://transformer-circuits.pub/2025/attribution-graphs/biology.html | Circuit tracing / attribution graphs can expose model computations. / attribution graph 可追踪模型计算。 | Low-to-medium; not same task domain. | P02 should treat E19 module patching as a smoke step toward circuits; full head/MLP/circuit tracing remains future work. |

## 5. Collision Assessment / 撞车评估

High collision if we claim / 高撞车表述：

1. “Process supervision is better than answer-only supervision.” / “过程监督优于只看答案。”
2. “LLMs make or miss reasoning mistakes.” / “LLM 会犯或漏检推理错误。”
3. “Multilingual hidden states contain language-specific or language-agnostic features.” / “多语言隐藏层有语言特异或语言无关特征。”
4. “Activation patching can reveal hidden representations.” / “activation patching 可揭示隐藏表征。”

Lower collision, stronger P02-specific claim / 更低撞车且更强的 P02 主张：

> 多语言/表层语义陷阱会产生 answer-correct but process-invalid 的 trace-selection 风险；这些风险不是单纯答案错或格式坏，而来自 surface lexicalization（表层词汇化）、过程语义、verifier objective/threshold（验证器目标与阈值）之间的错配。真实 trace 中存在可由 sibling comparison（兄弟对比）或 hidden-span patch（隐藏 span patch）暴露的过程/错误 span 信号，但 absolute Yes/No verifier（绝对式是/否验证器）常常过度接受。

## 6. Are The Five Mainlines Enough? / 五条 mainline 是否足够？

Answer / 结论：five mainlines are enough as the paper spine, but only if they are integrated as one causal chain and not reported as five independent smokes.

中文结论：五条主线足以构成论文主干，但必须被组织为同一条因果证据链，不能写成五个互不相干的 smoke 实验。

Recommended framing / 推荐重构：

1. Mainline A: Natural ACPI existence / 真实 ACPI 存在性。
2. Mainline B: Absolute verifier over-acceptance / 绝对 verifier 过度接受。
3. Mainline C: Multilingual surface-semantic trap mechanism / 多语言表层语义陷阱机制。
4. Mainline D: Hidden non-verdict process signal / 非 verdict 隐藏过程信号；split into residual patch and module/head decomposition. / 拆成 residual patch 与模块/头分解。
5. Mainline E: Sibling/triangulation mitigation / 兄弟对比与一致性三角测量缓解。

Missing cross-cutting layer / 需要增加的横向层：

- Audit and leakage controls / 审计与数据泄露控制。
- Order/position-bias controls / 顺序与位置偏差控制。
- Format/truncation separation / 格式与截断分离。
- Pre-registered downgrade conditions / 预注册降级条件。

## 7. What To Do Next / 下一步

1. Expand same-route pair bank to at least 8 clean pairs across discount, ratio, and derivative families. / 扩展同 route pair bank 至至少 8 对干净 pair，覆盖折扣、比例、导数。
2. Use E22/E23 as positive Qwen3.5 evidence; use E21/E20 as negative Qwen14 boundary evidence. / 用 E22/E23 做 Qwen3.5 正证据，用 E21/E20 做 Qwen14 边界证据。
3. Decompose only robust spans: Qwen3.5 `234/181000` support_error L3; Qwen14 `358/359` support_error L14; Qwen14 `402/403` trace L9/L20. / 只对稳健 span 做进一步 head/MLP 分解。
4. Build an automatic triangulation proxy from contrastive margins and conservative rejection; do not claim oracle triangulation as a deployed method. / 用 contrastive margin 与保守拒绝构建自动 proxy，不把人工 oracle 当成正式方法。
