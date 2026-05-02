# S6 Post-Grid Literature And Collision Review / S6 网格实验后的文献与撞车复核

Date / 日期: 2026-04-27 CST  
Scope / 范围: extra 2025-2026 literature checked after the S5 review, focused on CoT faithfulness, process/outcome mismatch, multilingual hard reasoning, and hidden-layer/mechanistic standards. I skipped already-central papers where possible; a few prior items reappear only because they define the collision boundary. / 本轮是在 S5 文献综述之后追加检索，重点看 CoT 忠实性、过程-结果错配、多语言困难推理、隐藏层与机制解释标准。尽量跳过已重点查询论文；少数前文献只因定义撞车边界而再次出现。

## 1. New Papers That Increase Collision Risk / 会提高撞车风险的新文献

| Area / 领域 | Work / 工作 | What it says / 主要事实 | Collision risk / 撞车风险 | P02-safe distinction / P02 安全区别 |
|---|---|---|---|---|
| CoT faithfulness / CoT 忠实性 | Anthropic, `Reasoning models don't always say what they think`, 2025, https://www.anthropic.com/research/reasoning-models-dont-say-think | Reasoning models often omit the true cue that affected their answer; outcome RL improved faithfulness only partly and plateaued; reward-hack cues were often not verbalized. / 推理模型常不说出真正影响答案的线索；只靠 outcome RL 提升有限；reward-hack 线索常不被说出。 | High for any broad “CoT is not faithful” statement. / 泛泛说“CoT 不忠实”会撞车。 | P02 should not claim general CoT faithfulness novelty. Our unit is trace-selection risk from multilingual lexical ACPI plus verifier-objective mismatch and hidden span patching. / P02 的单位是多语言词汇 ACPI 的轨迹选择风险、verifier 目标错配与 hidden span patch，而不是通用 CoT 忠实性。 |
| CoT in realistic prompts / 真实提示中的 CoT | Arcuschin et al., `Chain-of-Thought Reasoning In The Wild Is Not Always Faithful`, 2025, https://arxiv.org/abs/2503.08679 | Unfaithful CoT can happen without artificial bias; hard math can show illogical shortcuts. / 无人工偏置也会有不忠实 CoT；困难数学会出现不合逻辑捷径。 | High for “real traces can rationalize wrong process.” / “真实 trace 会事后合理化”会撞车。 | P02 adds a concrete multilingual surface-lexical mechanism (`打八折`, `75% off`, `pay 75%`) and evaluates verifier acceptance, not only generator faithfulness. / P02 增加具体表层词汇机制，并评估 verifier 是否接受。 |
| Instance-level faithfulness benchmark / 实例级忠实性基准 | `FaithCoT-Bench`, 2025/2026, https://arxiv.org/abs/2510.04040 | Frames unfaithfulness detection as discriminative instance-level evaluation with expert labels and step evidence. / 将不忠实检测做成实例级判别任务，含专家标签和步骤证据。 | Medium-high for benchmark/instance-detection framing. / 若写成通用检测基准会撞车。 | P02 should present selected causal probes, not a comprehensive faithfulness benchmark. / P02 应写成选择后的因果 probe，不写成综合基准。 |
| Outcome supervision pitfall / outcome 监督陷阱 | Guo et al., `Right Is Not Enough`, 2025, https://arxiv.org/abs/2506.06877 | Correct final answers can mask unsound math processes; LLM-as-judge methods struggle; stepwise verification helps. / 最终答案正确会掩盖错误过程；LLM-as-judge 难可靠发现；逐步验证有帮助。 | Very high for ACPI in math. / 对数学 ACPI 现象本身高度撞车。 | P02 must emphasize multilingual lexicalization and the absolute-vs-contrastive verifier threshold failure, plus hidden-span causal evidence. / P02 必须强调多语言词汇化、绝对式/对比式 verifier 阈值错配，以及 hidden-span 因果证据。 |
| Process/outcome benchmark / 过程-结果基准 | PRIME process-outcome alignment, 2026, https://arxiv.org/abs/2602.11570 | Outcome-centric verifiers may assign positive rewards to correct answers from incorrect derivations; PRIME evaluates derivation flaws and links verifier accuracy to RLVR gains. / outcome-centric verifier 会奖励错误推导得到的正确答案；PRIME 评估推导缺陷并关联到 RLVR 收益。 | Very high for broad process-outcome alignment. / 对广义过程-结果一致性高度撞车。 | P02 should be positioned as a multilingual lexical micro-mechanism and verifier-decision study, not as another STEM verifier benchmark. / P02 是多语言词汇微机制与 verifier 决策研究，不是另一个 STEM verifier benchmark。 |
| Process reward design / 过程奖励设计 | `Beyond Correctness: Harmonizing Process and Outcome Rewards`, 2025, https://arxiv.org/abs/2509.03403 | ORMs are too coarse to distinguish flawed reasoning in correct answers; PRMs can be inaccurate or reward-hackable. / ORM 太粗，无法区分正确答案里的错误过程；PRM 也可能不准或被 reward hacking。 | High for reward-objective language. / reward/objective 相关表述撞车高。 | P02 is diagnostic and causal-audit oriented; it does not propose a training algorithm. / P02 是诊断和因果审计，不是训练算法。 |
| Rule-verifiable process rewards / 规则可验证过程奖励 | VPRM, 2026, https://arxiv.org/abs/2601.17223 | Deterministic rule checks can avoid opaque neural judges in domains with explicit rules. / 在规则明确的领域，确定性步骤检查可避免黑箱 judge。 | Medium for “use process checks rather than neural judge.” / “用过程检查替代 judge”会撞车。 | P02 can cite this as motivation for external/rule checks but our observed failure is multilingual lexical semantics where rules must encode surface meanings. / P02 可把它作为外部规则检查动机，但我们的失败点是多语言词汇语义。 |

## 2. New Papers That Shape Mechanism Standards / 影响机制主张标准的新文献

| Area / 领域 | Work / 工作 | What it says / 主要事实 | P02 implication / 对 P02 的影响 |
|---|---|---|---|
| SAE + CoT / 稀疏自编码器与 CoT | `How does Chain of Thought Think?`, 2025, https://arxiv.org/abs/2507.22928 | Uses sparse autoencoders and activation patching to causally study CoT/noCoT features on GSM8K. / 用 SAE 与 activation patching 研究 GSM8K 上 CoT/noCoT 特征。 | We should not claim first feature-level CoT mechanism. Our mechanism target is verifier decision states for ACPI traces, especially support/error span and objective threshold. / 不能声称首个 CoT 特征机制；我们的机制对象是 ACPI verifier 决策状态。 |
| Circuit modularity / circuit 模块性 | `Circuit Compositions`, ACL 2025, https://aclanthology.org/2025.acl-long.727/ | Shows circuits for compositional string-edit subtasks can overlap and compose. / 组合子任务的 circuit 可重叠和组合。 | If we claim reusable circuits, we need head-level/circuit validation. Current S6 is residual/module patch plus diagnostic lens only. / 若声称可复用 circuit，需要头级/circuit 验证；S6 只能说 residual/module patch 与诊断 lens。 |
| Global MI / 全局机制解释 | `Towards Global-level Mechanistic Interpretability`, ICML 2025, https://proceedings.mlr.press/v267/he25x.html | Proposes modular circuit vocabulary to improve generalization beyond task-specific circuits. / 提出模块 circuit 词表，缓解任务特异 circuit 的泛化问题。 | P02 can frame future work as “from ACPI-specific spans to reusable lexical/process modules,” but not yet claim a vocabulary. / 未来可从 ACPI span 走向可复用词汇/过程模块，但现在还不能声称词表。 |
| MI benchmark / 机制解释基准 | BlackboxNLP 2025 shared task, https://arxiv.org/abs/2511.18409 | Standardizes circuit localization and causal-variable localization evaluation. / 标准化 circuit 定位和 causal variable 定位评估。 | P02 should call current layerwise lens diagnostic; full MI claims need benchmark-style localization or SAE/transcoder validation. / 当前 lens 只能称诊断；完整 MI 主张需要基准式定位或 SAE/transcoder 验证。 |
| Attribution graphs / 归因图 | Anthropic attribution-graph work, 2025, https://transformer-circuits.pub/2025/attribution-graphs/biology.html | Sets a high bar for circuit tracing with interpretable replacement components and graph-level claims. / 以可解释替代组件和图级证据提高 circuit tracing 门槛。 | Use as aspirational standard; P02 should say “module-level causal evidence,” not “complete circuit proof.” / 作为未来标准；P02 说“模块级因果证据”，不说“完整 circuit 证明”。 |

## 3. New Multilingual/Hard-Reasoning Context / 新的多语言与难题背景

| Work / 工作 | What it says / 主要事实 | P02 implication / 对 P02 的影响 |
|---|---|---|
| MathMist, 2025/2026, https://arxiv.org/abs/2510.14305 | Multilingual math reasoning remains inconsistent across languages and worse in low-resource settings. / 多语言数学推理跨语言不一致，低资源语言更差。 | Supports why multilingual surface form matters, but does not itself isolate ACPI lexical traps or verifier over-acceptance. / 支持多语言表层形式的重要性，但未隔离 ACPI 词汇陷阱与 verifier 过度接受。 |
| MultiNRC, 2025, https://arxiv.org/abs/2507.17476 | Native multilingual reasoning differs from translated English reasoning; models are stronger on English equivalents. / 原生多语言推理不同于英文翻译版，模型在英文等价题上更强。 | Supports our route distinction: `zh->en` is not just output language; translation can change process semantics. / 支持 route 区分：`zh->en` 不只是输出语言，翻译会改变过程语义。 |
| PolyMath, NeurIPS 2025, https://arxiv.org/abs/2504.18428 | Multilingual math benchmark across 18 languages; output-language consistency is low and tied to performance. / 18 语种多语言数学基准；输出语言一致性低且与性能有关。 | Our route violations and lexical drifts should be separated from ACPI, not hidden in aggregate accuracy. / 我们应把 route violation 和词汇漂移从 ACPI 中分离。 |
| MMLU-ProX, 2025, https://arxiv.org/abs/2503.10497 | Parallel multilingual benchmark with expert-reviewed translations; performance gaps persist by language. / 多语言平行基准并有专家翻译复核；语言间性能差距持续存在。 | Supports expert translation/audit controls; P02 still needs human audit for tricky lexical meanings. / 支持专家翻译/审计控制；P02 的词汇含义仍需人工审计。 |

## 4. Updated Novelty Judgment / 更新后的创新性判断

### High-collision claims to avoid / 必须避免的撞车表述

1. “Correct answers can have wrong reasoning.” / “正确答案可能有错误推理。”
2. “LLM judges/verifiers miss process errors.” / “LLM judge/verifier 会漏掉过程错误。”
3. “CoT is unfaithful.” / “CoT 不忠实。”
4. “Activation patching or SAE reveals reasoning features.” / “activation patching 或 SAE 能揭示推理特征。”
5. “Multilingual math reasoning is hard.” / “多语言数学推理困难。”

### Lower-collision P02 claim after S6 / S6 后更安全的 P02 主张

P02 remains novel if the paper claims the following conjunction, not the individual pieces alone. / 只要论文声称下面这个组合，而不是单独声称其中任一老问题，P02 仍有创新性：

> Controlled multilingual lexical paraphrases can produce real answer-correct/process-invalid trace-selection failures: the same arithmetic answer survives while the local process semantics flips between `pay 75%`, `75% off`, `打八折/pay80`, and `80% discount/pay20`. On selected real sibling pairs, absolute Yes/No verifiers over-accept these traces, contrastive sibling prompts expose them only for some verifier/model pairs, and residual support/error-span patching shows that process-validity information is present in hidden states even when the final verifier objective accepts the trace.
>
> 中文：受控多语言词汇改写会产生真实 ACPI 轨迹选择失败：同一个算术答案保留下来，但局部过程语义在 `pay 75%`、`75% off`、`打八折/pay80`、`80% discount/pay20` 之间翻转。在选择后的真实 sibling pair 上，绝对式 Yes/No verifier 会过度接受；对比式 sibling prompt 只在部分 verifier/模型上暴露错误；support/error span 的残差 patch 表明，即使最终 verifier 目标接受了轨迹，隐藏状态里仍有过程有效性信号。

## 5. Mechanism Innovation Boundary / 机制创新边界

- Safe now / 现在安全：`verifier-decision lens`（验证器决策 lens）、`support/error-span causality`（支持/错误 span 因果性）、`middle-layer process confounding`（中层过程混杂）、`output-head/objective re-entanglement`（输出头/目标再纠缠） as hypotheses supported by residual patch and diagnostic lens. / 这些可作为有 residual patch 与诊断 lens 支持的假设。
- Not safe yet / 现在不安全：complete circuit, reusable lexical-process module, SAE feature dictionary, or population prevalence. / 不能声称完整 circuit、可复用词汇-过程模块、SAE 特征字典或总体发生率。
- Best next differentiator / 最好的下一步区分点：run head/MLP/SAE probes only on robust S6/E22 spans, and test whether the same lexical-process direction transfers across `打八折`, `七五折`, `75% off`, `sold for 75%`, and `pay 80%`. / 只在稳健 S6/E22 span 上做头/MLP/SAE，并测试同一词汇-过程方向是否跨表层形式迁移。
