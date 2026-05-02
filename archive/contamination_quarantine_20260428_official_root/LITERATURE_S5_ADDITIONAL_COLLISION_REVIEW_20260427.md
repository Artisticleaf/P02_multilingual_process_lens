# S5 Additional Literature And Novelty Check / S5 追加文献与创新性复核

Date / 日期: 2026-04-27 CST
Scope / 范围: additional 2023-2026 literature search after `docs/LITERATURE_AND_NOVELTY_REVIEW_20260427.md` and `docs/LITERATURE_S4_MECHANISM_HARD_TASKS_20260427.md`. / 本轮是在前两份文献综述之后的追加检索。

Search rule / 检索规则：skip already-central papers where possible, but keep them in the collision map when they directly define the boundary. / 尽量跳过已重点覆盖论文，但在它们直接定义撞车边界时保留。

## 1. What Is Already Covered / 已覆盖内容

Already central in earlier docs / 前文档已重点覆盖：`Let's Verify Step by Step`（逐步验证）, `Math-Shepherd`（数学牧羊人）, `ProcessBench`（过程错误识别基准）, `PRMBench`（过程奖励模型基准）, BIG-Bench Mistake（错误发现基准）, `Large Language Models are not Fair Evaluators`（LLM 裁判不公平）, multilingual CoT（多语言思维链）, `Language-Specific Neurons`（语言特异神经元）, `Separating Tongue from Thought`（语言外壳/思想分离）, `Patchscopes`（隐藏表征检查框架）, and Anthropic attribution graphs（归因图/电路追踪）。

This round therefore focuses on collision pressure from CoT faithfulness, process-outcome alignment, judge bias, hard math, and mechanism-level standards. / 因此本轮关注 CoT 忠实性、过程-结果对齐、裁判偏差、困难数学和机制解释标准带来的撞车压力。

## 2. Added Literature Map / 追加文献图谱

| Area / 领域 | Work / 工作 | Relevant point / 相关点 | Collision risk / 撞车风险 | P02 positioning / P02 定位 |
|---|---|---|---|---|
| CoT faithfulness / CoT 忠实性 | Turpin et al., `Language Models Don't Always Say What They Think`, NeurIPS 2023, https://arxiv.org/abs/2305.04388 | CoT explanations can be plausible but unfaithful to the model's actual decision process. / CoT 解释可能可信但不忠实于真实决策过程。 | High for any generic “reasoning traces can be unfaithful” claim. / 泛化“CoT 不忠实”会撞车。 | P02 should not claim first discovery of unfaithful CoT; our unit is selected multilingual ACPI traces with final-correct but process-invalid content, plus verifier and hidden-span probes. / P02 不声称首次发现 CoT 不忠实，而研究多语言 ACPI、verifier 与 hidden-span 因果链。 |
| CoT intervention / CoT 干预 | Lanham et al., `Measuring Faithfulness in Chain-of-Thought Reasoning`, arXiv 2023, https://arxiv.org/abs/2307.13702 | Intervening on CoT can reveal whether answers depend on the stated reasoning. / 干预 CoT 可揭示答案是否依赖显式推理。 | Medium-high for intervention-on-trace framing. / trace 干预表述有撞车风险。 | P02's interventions target verifier decisions and process/error spans, not generator answer dependence alone. / P02 干预的是 verifier 决策与过程/错误 span，而非只看生成器答案依赖。 |
| Mechanistic CoT / 机制化 CoT | Dutta et al., `How to think step-by-step`, 2024, https://arxiv.org/abs/2402.18312 | Mechanistic analyses of CoT search for internal substructures supporting reasoning. / 机制分析可寻找支持 CoT 的内部子结构。 | Medium for “reasoning has hidden mechanisms”. / “推理有内部机制”会撞车。 | P02 should frame E25 as a verifier-decision lens (验证器决策 lens) for ACPI traces, not as a general CoT mechanism theory. / E25 应定位为 ACPI verifier 决策 lens，不是通用 CoT 机制理论。 |
| Process reward models / 过程奖励模型 | Zhang et al., `The Lessons of Developing Process Reward Models in Mathematical Reasoning`, 2025, https://arxiv.org/abs/2501.07301 | PRM evaluation can be biased by correct answers with flawed processes; PRM objectives can drift toward final-answer assessment. / PRM 评测会受“答案对但过程错”影响，目标可能漂向最终答案。 | Very high because it names correct-answer/flawed-process PRM issues. / 高撞车。 | P02 must emphasize multilingual surface lexicalization, absolute-vs-contrastive verifier mismatch, and causal hidden-span evidence rather than PRM development. / P02 必须强调多语言表层词汇化、绝对/对比 verifier 错配与 hidden-span 因果证据。 |
| Process RL / 过程强化 | PRIME, `Process Reinforcement through Implicit Rewards`, 2025, https://arxiv.org/abs/2502.01456 | Dense process rewards and online implicit rewards improve math/coding reasoning but raise reward-model design issues. / 稠密过程奖励和隐式过程奖励可提升推理，但带来 reward 设计问题。 | Medium-high for “process signal helps reasoning”. / “过程信号有用”会撞车。 | P02 is diagnostic/mechanistic rather than an RL training method. / P02 是诊断/机制研究，不是 RL 训练方法。 |
| Process-outcome alignment / 过程-结果对齐 | `PRIME: A Process-Outcome Alignment Benchmark for Verifiable Reasoning in Mathematics and Engineering`, 2026, https://arxiv.org/abs/2602.11570 | Verifiers can reward correct answers from incorrect derivations; benchmark evaluates process-outcome alignment and reports AIME gains for process-aware RLVR. / verifier 可能奖励错误推导得到的正确答案；该基准评估过程-结果对齐，并报告过程感知 RLVR 在 AIME 上增益。 | Very high for broad answer-correct/process-wrong verifier risk. / 对广义答案对/过程错 verifier 风险高度撞车。 | P02's safest novelty is narrower: multilingual lexical ACPI, selected real traces, sibling/order controls, residual/module patch and layerwise lens. / P02 的安全创新点更窄：多语言词汇 ACPI、真实选择轨迹、sibling/order 控制、残差/模块 patch 与分层 lens。 |
| LLM-as-judge bias / LLM 裁判偏差 | Wang et al., `Large Language Models are not Fair Evaluators`, ACL 2024, https://aclanthology.org/2024.acl-long.511 | LLM judges exhibit positional bias and require calibration/order controls. / LLM 裁判有位置偏差，需要校准和顺序控制。 | High for judge-bias claims. / 裁判偏差本身会撞车。 | P02 contributes a task-specific bias instance: Gemma4 contrastive verifier often predicts A, so sibling mitigation must be order-balanced. / P02 提供任务特异偏差例：Gemma4 对比 verifier 常选 A。 |
| LLM-as-judge robustness / LLM 裁判鲁棒性 | `Judging the Judges: Evaluating Alignment and Vulnerabilities in LLMs-as-Judges`, 2024/2025, https://arxiv.org/abs/2406.12624 | LLM judge agreement can hide vulnerability and alignment differences. / LLM 裁判表面一致性可能掩盖脆弱性与对齐差异。 | Medium for evaluating judges as systems. / 将 judge 当系统评估有撞车风险。 | P02 should report both absolute and contrastive modes, plus error rows, not only aggregate accuracy. / P02 应报告绝对式、对比式和错误行，而非只报总体准确率。 |
| Mechanistic standard / 机制标准 | Anthropic, `Circuit Tracing: Revealing Computational Graphs in Language Models`, 2025, https://transformer-circuits.pub/2025/attribution-graphs/methods.html | Cross-layer transcoders and attribution graphs set a high bar for circuit claims; MLP features can be decomposed but require validation. / 跨层 transcoder 与归因图提高了 circuit 声称门槛；MLP 特征可分解但需验证。 | Low for P02 if we avoid full-circuit claims; high if we overclaim. / 若不声称完整 circuit，撞车低；若过度声称则高。 | P02 should call E19/E25 “module-level causal evidence” and “diagnostic lens”, reserving circuit claims for future SAE/transcoder work. / P02 应称 E19/E25 为模块级因果证据与诊断 lens，将 circuit 留作未来。 |
| Model transfer / 模型迁移 | Qwen3.5-27B model card, 2026 current, https://huggingface.co/Qwen/Qwen3.5-27B | 27B model, 64 layers, 201-language coverage, default thinking mode, long context; needs careful loading. / 27B、64 层、支持 201 种语言、默认 thinking mode、长上下文；加载需谨慎。 | Low as a model source. / 作为模型来源撞车低。 | Supports transfer test; Qwen3.5-27B absolute over-accepts but contrastive works better. / 支持迁移测试；Qwen3.5-27B 绝对式过度接受，对比式更好。 |
| Model transfer / 模型迁移 | Google Gemma4 E4B-it model card, 2026 current, https://huggingface.co/google/gemma-4-E4B-it | Multimodal open model with E4B dense size, 42 layers, 128K context, multilingual support. / 多模态开放模型，E4B dense、42 层、128K 上下文、多语言支持。 | Low as a model source. / 作为模型来源撞车低。 | Supports non-Qwen transfer; Gemma4 over-accepts absolutely and shows contrastive position bias. / 支持非 Qwen 迁移；Gemma4 绝对式过度接受且对比式有位置偏差。 |
| Hard math / 困难数学 | AIME2024/2025 public HF datasets, https://huggingface.co/datasets/TianHongZXY/AIME2024 and https://huggingface.co/datasets/TianHongZXY/AIME2025 | Compact answer benchmarks with 30 rows per year in the cited public HF versions. / 公开 HF 版本每年 30 行，答案紧凑。 | Low as stress-test data, high if overclaimed as full benchmark. / 作为压力测试撞车低，若宣称完整 benchmark 则高。 | E26 should be written as a boundary/control: zero final-correct traces means no ACPI estimate yet. / E26 应写成边界/控制：没有 final-correct 就没有 ACPI 估计。 |

## 3. Innovation Check / 创新性检查

### 3.1 High-collision statements to avoid / 应避免的高撞车表述

1. “CoT is unfaithful.” / “CoT 不忠实。”
2. “Process supervision is important.” / “过程监督重要。”
3. “Verifiers miss flawed derivations.” / “verifier 会漏掉错误推导。”
4. “LLM judges have position bias.” / “LLM 裁判有位置偏差。”
5. “Hidden layers contain reasoning signals.” / “隐藏层含推理信号。”
6. “Activation patching reveals mechanisms.” / “activation patching 能揭示机制。”

### 3.2 Lower-collision P02 contribution / P02 较低撞车贡献

P02 is still novel enough if phrased as the following combined claim. / 如果写成以下组合主张，P02 仍具有足够创新性：

> A realistic multilingual surface-lexical family of answer-correct/process-invalid traces creates trace-selection risk because surface lexicalization, process semantics, and verifier objective/threshold disagree. In selected real traces, this mismatch is visible across a causal chain: manual ACPI labels -> absolute Yes/No over-acceptance -> contrastive sibling visibility in many pairs -> residual/module span patch and layerwise verifier-lens signals, with explicit hard boundaries.
>
> 中文：一类真实多语言表层词汇 ACPI 轨迹会造成轨迹选择风险，因为表层词汇化、过程语义和 verifier 目标/阈值错配。在选择后的真实轨迹中，该错配可沿因果链观察：人工 ACPI 标签 -> 绝对式 Yes/No 过度接受 -> 多数 pair 中的对比 sibling 可见性 -> 残差/模块 span patch 与分层 verifier-lens 信号，同时保留明确困难边界。

## 4. Mechanism Opportunities Beyond Published Work / 区别于既有工作的机制切口

1. Verifier-decision lens / 验证器决策 lens：study hidden states of the verifier's decision token under absolute and contrastive objectives, not hidden states of the original generator alone. / 研究 verifier 决策 token 在绝对式与对比式目标下的 hidden state，而非只研究生成器。
2. Middle-layer process confounding / 中层过程混杂：test whether lexical cue states and arithmetic/process states co-occupy middle layers in trap traces. / 测试词汇线索和算术/过程状态是否在陷阱 trace 的中层混杂。
3. Output-head re-entanglement / 输出头再纠缠：compare middle-layer target/error margins with final-layer Yes/No or A/B margins to quantify signal loss/reweighting. / 比较中层 target/error margin 与最终层 Yes/No 或 A/B margin，量化信号丢失/重权。
4. Objective-threshold bottleneck / 目标-阈值瓶颈：contrast absolute pointwise judging against pairwise sibling judging on identical trace evidence. / 在同一 trace 证据上比较绝对式 pointwise 与 pairwise sibling 判断。
5. Error-span causality / 错误 span 因果性：patch support/error spans and module outputs only after manual/sibling controls identify a real ACPI pair. / 只有在人工/sibling 控制确认真实 ACPI 后才 patch support/error span 与模块输出。

## 5. What Makes The Work More Solid / 如何更扎实

- Expand pair bank / 扩展 pair bank：increase clean same-route ACPI/valid sibling pairs to at least 8 robust pairs before claiming broadness. / 至少 8 对稳健干净同 route pair 后再谈广泛性。
- Pre-register downgrade rules / 预注册降级规则：if contrastive margin, patch strength, or manual route validity fails, mark as boundary rather than hide it. / 对比 margin、patch 强度或 route 有效性失败时标记为边界。
- Add paraphrase controls / 加入改写控制：`打八折`, `pay 80%`, `20% off`, `80% discount`, and `75% off` should be separated. / 分离打八折、支付 80%、优惠 20%、80% off、75% off 等表层形式。
- Separate task difficulty / 分离任务难度：simple-task ACPI evidence and AIME hard-task boundary should be separate claims. / 简单任务 ACPI 与 AIME 难题边界应分开。
- Use calibrated mechanism language / 使用校准机制语言：current evidence is residual/module patch plus diagnostic lens; full circuit claims require head-level, SAE/transcoder, or attribution-graph validation. / 当前证据是残差/模块 patch 与诊断 lens；完整 circuit 需要头级、SAE/transcoder 或归因图验证。

## 6. Bottom Line / 结论

The main claim remains innovative if it is kept narrow and causal-chain based. / 若保持窄化并围绕因果链，本项目主张仍有创新性。

The largest collision risk is the 2025-2026 process-outcome/verifier literature, especially work noting that correct answers can have flawed derivations. / 最大撞车风险来自 2025-2026 的过程-结果/verifier 文献，特别是已指出“正确答案可能来自错误推导”的工作。

The most defensible novelty is the intersection of multilingual surface lexicalization, selected real ACPI traces, absolute-vs-contrastive objective mismatch, and hidden-span/module/layerwise causal evidence with explicit failure boundaries. / 最稳创新点是：多语言表层词汇化 + 真实选择 ACPI 轨迹 + 绝对式/对比式目标错配 + hidden-span/module/layerwise 因果证据 + 明确失败边界。
