# Handoff + History Stage Synthesis / 交接与历史阶段性整理（2026-04-30，updated 2026-05-03）

Working directory / 工作目录：`/home/Awei/P02_multilingual_process_lens`

This document replaces the old habit of reading the whole handoff/history chain before making scientific decisions. The older files remain the audit trail; this file is the human-readable stage synthesis. / 本文档用于替代“先读完整交接和历史长流水再判断科学主线”的做法。旧文件仍是审计流水；本文档是阶段性主线整理。

## 1. One-Sentence Claim / 一句话主张

**Current safe claim / 当前安全主张：**

In direct or non-thinking verifier settings, current P0 models often contain hidden process-validity evidence, but the final Yes/No or A/B decision may fail to use that evidence because of objective, threshold, answer anchoring, repair-aware reading, output-label readout, language-route difficulty, local semantic competence, and stop/commit control. A new finding (E172 probe, 2026-05-03): hidden states also carry a selective “pre-turnaround signal” — elevated risk that precedes explicit conceptual self-correction in CoT, suggesting metacognitive uncertainty is encoded in component states before it surfaces in visible text. / 在 direct 或 non-thinking verifier 设置中，当前 P0 模型内部常有”过程是否有效”的隐藏证据，但最终 Yes/No 或 A/B 决策可能因为目标、阈值、答案锚定、把 CoT 当可修复草稿读、输出标签读出、语言路径难度、局部语义能力和停止/提交控制而没有用好这些证据。新发现（E172 probe）：hidden state 中还编码了选择性的”预转变信号”——在模型显式写出概念性自纠文本之前，hidden risk 就已经升高，说明元认知不确定性在进入可见文本之前就已经在 component state 中编码。

**Do not overclaim / 不要过度主张：**

- Do not say natural unrepaired ACPI is common. Current NG hard-task rate is low but real: 2/200 strict final decisions, or 2/252 generated rows. / 不能说自然未修复 ACPI 很常见。当前 NG 困难题中它低频但真实。
- Do not say sibling comparison or hidden probes are oracles. GLM and Gemma26 are explicit boundaries. / 不能说 sibling 或 hidden probe 是万能 oracle。GLM 和 Gemma26 已经给出边界。
- Do not call the current mechanism a complete named circuit. It is strong hidden-state/component evidence plus limited causal evidence. / 不能说已经找到完整命名电路。现在是强 hidden-state/component 证据和有限因果证据。
- Do not mix modes. DV, TV, NG, TG, MI-DV, MI-TG, and PM must be reported separately. / 不要混模式。DV、TV、NG、TG、MI-DV、MI-TG、PM 必须分开报。

## 2. Glossary in Plain Language / 术语人话表

| Term / 术语 | Plain Chinese / 中文人话 | Plain English |
|---|---|---|
| ACPI | 答案对，但推理过程里有错。 | Answer-Correct but Process-Invalid. |
| strict ACPI | 只要可见 trace 里出现关键错步，即使后面修了，也按“这段 trace 不是严格证明”处理。 | A trace is invalid as a proof if any visible key wrong step appears, even if later repaired. |
| repaired ACPI | 前面错了，后面明确推翻或修正；严格口径算 invalid，草稿口径可能接受。 | A wrong step is later explicitly corrected or discarded. Strict proof rejects; draft-aware reading may accept. |
| unrepaired ACPI | 最终答案碰巧对，但保留下来的证明仍依赖错步。 | The final answer is correct, but the surviving reasoning still relies on a wrong step. |
| trace-selection risk | 如果只按答案或弱 verifier 筛 trace，会把“答案对但过程坏”的 trace 留进数据。 | A filter may select correct-answer traces whose reasoning process is invalid. |
| trace-as-proof | 把 CoT 当正式证明；任何关键错步都不能出现。 | Treat the chain as a proof; key wrong steps invalidate it. |
| trace-as-draft / repair-aware | 把 CoT 当草稿；前面错了但后面明确修好，可以接受最终保留证明。 | Treat the chain as scratch work; explicit repair can make the final surviving proof acceptable. |
| DV | 关闭 thinking，直接让 verifier 给 Yes/No、A/B 或固定选项。 | Direct-answer verifier with thinking disabled. |
| TV | 开启 thinking，让模型完整思考后输出最终判定。 | Thinking verifier with full generated reasoning and parsed final decision. |
| NG | 关闭 thinking 的自然生成。 | Non-thinking natural generation. |
| TG | 开启 thinking 的自然生成。 | Thinking natural generation. |
| MI-DV | 在 direct verifier prompt 下读 hidden state、MLP、token-mixer 或做 steering。 | Mechanistic diagnostics under direct-verifier prompts. |
| MI-TG | 在 thinking trace 上读 hidden state、stop signal 或 component。 | Mechanistic diagnostics on thinking traces. |
| PM | 后处理、统计、筛选器仿真。 | Post-processing/statistical/filter simulation. |
| pointwise / absolute verifier | 单独看一条 trace，问“这条对吗”。 | Judge one trace in isolation. |
| sibling comparison | 把一对只有局部过程不同的 trace 放一起比较。 | Compare sibling traces that differ mainly in the local process step. |
| label-free two-pass | 不用 A/B 标签，分别问每条 trace，再比较分数。 | Score each trace separately without relying on A/B labels. |
| answer anchor | 正确最终答案会把 verifier 往“接受”方向拉。 | A correct final answer biases a verifier toward acceptance. |
| readout bottleneck | 内部有证据，但输出格式/标签/logit 读法把证据压坏了。 | Internal evidence exists, but the output/readout channel fails to express it. |
| objective mismatch | 模型默认优化的判断目标和我们要的严格过程目标不一致。 | The model's implicit judging objective differs from the intended strict process objective. |
| threshold mismatch | 模型有负面证据，但没低到触发拒绝阈值。 | Evidence exists but does not cross the rejection threshold. |
| process-validity evidence | hidden state 中可读出的“过程是否有效”的信息。 | Information in hidden states about whether the process is valid. |
| hidden process-risk signal | 某些 hidden 分数变差，提示附近可能有过程风险。 | A hidden-state score indicating possible process risk. |
| residual | transformer 每层累积的主状态向量。 | The main accumulated state vector at a layer. |
| MLP | transformer 中的前馈子层，常承载非线性特征变换。 | The feed-forward sublayer. |
| token-mixer / attention-related | 负责跨 token 汇合信息的 attention 相关输出。 | Components that mix information across tokens, especially attention-related outputs. |
| logit / margin | 输出词的分数；Yes-No margin 是 Yes 分数减 No 分数。 | Output scores; Yes-No margin is Yes score minus No score. |
| activation steering | 人为沿某个 hidden 方向推激活，看输出是否改变。 | Push activations along a direction and test whether decisions move. |
| span patch | 只替换或干预某个错误 span 附近的激活。 | Patch/intervene on activations near a specific error span. |
| hidden gate | hidden 风险分数过阈值才触发二次检查。 | A gate that triggers a second check only when hidden risk is high. |
| final marker | 模型明确写出 `Final answer:` 这类最终提交标志。 | An explicit final-answer marker. |
| fallback answer | 没有 final marker 时，从文本里抽到的数字；不能等同最终提交。 | A number extracted without an explicit final decision; not a strict final answer. |
| clean final stop | 写出最终答案后自然停止，不再继续自检或输出。 | The model stops cleanly after the final answer. |
| stop/commit signal | hidden state 中可读出的”是否该提交并停止”的信号。 | Hidden evidence about whether to commit and stop. |
| pre-turnaround signal | 模型在显式写出自纠文本（如”Wait...”）之前，hidden risk 就已经升高的现象。选择性出现：概念性纠错前有信号，执行检查前没有。 | Hidden risk elevation that precedes explicit self-correction markers. Selective: appears before conceptual error recognition, not before execution checks. |
| prompt leakage | 答案、人工标签、错误 span 或 trap note 进入 prompt。 | Gold answers, labels, error spans, or trap notes leaking into prompts. |
| Wilson CI | 小样本比例的置信区间，比普通正态近似更稳。 | A robust confidence interval for proportions. |
| romanized_zh | 中文内容用拼音/罗马字母写，语义在中文，表面像英文。 | Chinese content written in romanized form. |
| mixed route | 中英或多语言混合表达。 | Mixed-language reasoning route. |
| local semantic competence | 模型是否真的懂某个局部公式/语言/语义错误。 | Whether the model can understand a local semantic or algebraic error. |

## 3. Model and Mode Boundary / 模型与模式边界

**Core P0 / 核心 P0：**

- `qwen35_27b`
- `gemma4_31b_it`
- `gemma4_26b_a4b_it`

**Expanded boundary model / 扩展边界模型：**

- `glm47_flash_candidate`

GLM is admitted as expanded P0 boundary evidence, not merged into the core headline. It reproduces pointwise over-acceptance and hidden process signals, but raw A/B sibling readout is weak. / GLM 是扩展边界证据，不并入核心 headline。它复现 pointwise 过度接受和 hidden 过程信号，但 raw A/B sibling 读出弱。

## 4. Experiment Results by Stage / 分阶段实验结论

### Stage A: Controlled Direct-Verifier Risk / 受控 direct-verifier 风险

**E42 / template parity.** Core P0 absolute invalid accept = 0.50, valid accept = 1.00, contrastive accuracy = 1.00. / 核心 P0 在单点 Yes/No 下会接受一半 invalid trace；把 sibling 放一起比时可恢复。

**E53 / answer anchor.** Correct final answers push acceptance up; wrong final answers push it down; removing/masking the final answer still leaves nonzero invalid acceptance. / 最终答案是强锚点，但不是全部原因。

**E54 / no-leak generalization.** 18 task families reproduce over-acceptance; sibling suppresses accepted ACPI to 0 in core P0 E42/E54. / 风险不是单个 discount 题 artifact。

**E60 / objective ladder.** P0 mean ACPI accept: plain Yes/No 0.567, careful 0.156, answer-blind 0.189, locate-then-judge 0.144; sibling/careful sibling remains strongest. / “仔细检查”有用，但结构化对比更强。

**E61 / multilingual × error taxonomy.** P0 plain pointwise ACPI accept = 0.424; careful/answer-blind/locate = 0.188/0.125/0.174; sibling/careful-sibling = 0.990/0.986. Highest risk: `romanized_zh`, `mixed`, `percentage_base`, `code_execution`, `counting_order`. / 多语言表层和局部过程语义错配是主风险。

**Stage A fact / 人话结论：** If a verifier judges one trace alone, the correct answer and fluent suffix can overpower a local wrong step. If it compares a matched sibling or is forced to locate the process difference, the error is much easier to expose. / 单条判断容易被正确答案和流畅后文带偏；成对比较或定位错步能让局部过程差异浮出来。

### Stage B: Cross-Model Boundary and Hidden Signals / 跨模型边界与 hidden 信号

**E62-E70 / GLM expansion.** GLM passes smoke and enters expanded P0. It reproduces pointwise strict ACPI over-acceptance but weakens the claim that sibling is always perfect. / GLM 说明“sibling 永远有效”不能写死。

**E65/E78 / hidden probe audit.** Best-layer residual probes are strong: Qwen 1.000, Gemma31 1.000, Gemma26 about 0.917-0.970 depending on set, GLM about 0.958-0.979; permutation controls stay near chance. / hidden state 中确实有过程有效性信号，但 Gemma26 有假阳性边界。

**E79/E84/E87 / GLM readout.** GLM hidden margin and label-free margin correlate strongly, but raw A/B margin is weak; readout intervention improves raw A/B. / GLM 不是看不见过程，而是 A/B 输出标签读出会扭曲证据。

**Stage B fact / 人话结论：** The hidden signal generalizes better than some text output formats. Output labels can be the bottleneck. / hidden 证据比某些输出格式更稳，瓶颈可能在读出。

### Stage C: Strict vs Repair-Aware and Natural NG Prevalence / 严格口径、修复口径与自然 NG 发生率

**E71 / strict vs repair-aware.** Strict means any visible key wrong step invalidates the trace as proof. Repair-aware accepts only if later text clearly discards the wrong step and leaves a valid proof. / 这不是文字游戏，而是两种不同科学对象。

**E57/E83/E88 / early hard-task samples.** Natural unrepaired ACPI exists but is rare; many strict ACPI are repaired scratch mistakes. / 自然困难题里真未修复错步低频，但“先错后修”的 strict ACPI 常见。

**E119/E146 / official NG process audit.** 252 generated rows, 201 final/fallback-correct audit rows, 200 strict final-decision rows. Strict ACPI = 46/200, Wilson CI [0.177, 0.293]. Repaired strict ACPI = 44. Unrepaired ACPI = 2/200 = 0.010, Wilson CI [0.003, 0.036]; per generated = 2/252 = 0.008, Wilson CI [0.002, 0.028]. Both unrepaired rows are Gemma26 integer-pairs answer-first traces with a wrong plus-xy factorization whose final count is preserved by sign symmetry. / 自然 NG 中，严格证明口径下 ACPI 不少，但真正未修复 ACPI 低频；两条关键反例都来自 Gemma26。

**Stage C fact / 人话结论：** If CoT is treated as a proof, many natural traces are invalid because they contain visible wrong scratch steps. If CoT is treated as a draft, many of those are acceptable repairs. The rare but important cases are unrepaired traces where the wrong step survives and the answer is still right. / 把 CoT 当证明和当草稿会得到完全不同的结论；未修复 ACPI 才是最硬的风险样本。

### Stage D: Natural Hidden Localization and Adaptive Checking / 自然样本 hidden 定位与自适应检查

**E106-E114 / non-thinking mechanism suite.** Hidden process AUC: Qwen 1.000, Gemma31 1.000, Gemma26 0.970, GLM 0.997. Process and confidence directions are highly aligned (cosine 0.935-0.994), but partial correlations remain positive (0.650-0.882). Hidden gate reduces controlled ACPI retention from 0.375-0.458 to 0-0.042 while mostly preserving valid traces. / hidden 信号很强，但和置信度缠在一起；仍有超出普通 Yes/No 置信度的信息。

**E131 / E119/E146 hidden localization.** Qwen separates strict-valid and repaired ACPI cleanly (valid accept 15/15; repaired accept 4/133). Gemma31 separates many repaired rows but accepts 42/112. Gemma26 accepts unrepaired ACPI 8/10 overall; detected-error-marker prefixes are rejected 0/2, but completion prefixes are accepted 2/2 while residual score remains weaker than valid. / Gemma26 给出最强错配：错误附近信号响，结尾又被答案自洽后文拉回接受。

**E132-E134 / suspicious-valid controls.** Qwen: invalid trigger 12/12, valid trigger 2/48, hidden AUC 1.000 while strict-confidence AUC 0.447. Gemma31: invalid 12/12, valid 0/48, AUC 1.000. Gemma26: invalid 12/12, valid 6/48, AUC 0.960. / hidden 风险不是单纯看到“我再检查一下”这类犹豫词，但 Gemma26 误触发更多。

**E136 / controlled adaptive check.** Qwen hidden-local reduces invalid accept 4/12 -> 1/12 with valid 47/48. Gemma31 reduces 3/12 -> 2/12 with valid 48/48. Gemma26 hidden-local accepts 5/12 invalid, worse than its strict base 1/12. / hidden 触发有用，但二次检查 prompt 和模型局部语义能力决定成败。

**E137-E140 / natural adaptive check.** Qwen natural repaired rows: base invalid accept 2/19, zero-threshold triggers all 19, strict-local reduces to 0/19 and keeps valid 5/5. Gemma31: base 6/16, strict-local 2/16. Gemma26: base 6/10, zero trigger covers repaired + unrepaired, but strict-local still accepts 5/10 and both unrepaired rows. / 自然样本上 Qwen/Gemma31 支持 hidden-trigger + strict local check；Gemma26 是关键反例。

**E139/E139.5 / rationale and span localization.** E139 failed-row audits: 26/26 parse, 26/26 wrong-step quotation, strict accept 0/26, repair-aware accept 23/26. E139.5 locate-only span hit: Qwen 11/12 with 0/36 valid false error; Gemma31 6/9 with 0/27 false error; Gemma26 14/18 with 3/54 false error. / 许多失败不是“模型看不见错步”，而是看见后按 repair-aware 口径放过，或在 Gemma26 的局部代数语义上真的没看懂。

**Stage D fact / 人话结论：** Hidden risk can cheaply select many bad traces, but it is not an error detector by itself. The second verifier must use the right strict objective, and some model-family/local-language cases still fail. / hidden 风险能低成本挑出风险样本，但不能替代正确评价目标和局部语义能力。

### Stage E: Thinking Mode Boundary / thinking 模式边界

**E91 / mode audit.** Qwen, Gemma, and GLM templates distinguish thinking vs non-thinking. First-token Yes/No or A/B logprob is not a TV measurement. / 以前的 verifier 结果是 DV，不是 thinking verifier。

**E103-E105 / Qwen TG closure.** Qwen TG at 4096 tokens gives 0/9 strict final-correct and 0/9 final marker; all hit max. 16k/32k final-contract can make one task cleanly stop, but this does not prove TG is generally better. / Qwen thinking 的首要问题是收口/最终提交，不是单纯算不出来。

**E116-E118 / thinking stop signal.** A Qwen stop direction separates clean-stop vs continuation points (29.345 vs -8.438; threshold 10.453). Stop/commit is not the same as process validity. / thinking 额外引入“该不该提交并停止”的独立瓶颈。

**Stage E fact / 人话结论：** Thinking mode is not automatically safer. A model may have computed a useful answer but fail to submit cleanly; or it may keep thinking after a final marker. TV/TG claims still need systematic reruns. / thinking 不是自动更可靠；必须单独测最终提交、干净停止和过程有效性。

### Stage F: Pre-Turnaround Signal in Hidden States / hidden state 中的预转变信号

**E172 probe / 预转变信号探测（2026-05-03）：**

在 4 道高分自纠正确题（p14/p17/p27/p28，最终答案正确但过程中分别有 15/16/23/12 个 self-correction anchor）的 baseline completion 上，每 300 chars 做 teacher-force prefill，读取 E166 校准的 hidden component（`35:residual_hidden_state`）risk 分数。每个采样点按距离最近 "Wait..." / self-correction anchor 的位置分为 confident（远离任何 anchor 的正常推理）、pre_correction（anchor 前 50-400 chars）、at_correction（anchor ±50 chars）、post_correction（anchor 后 50-400 chars）。

核心假设：hidden state 不仅反映当前 token 的 risk，还编码了模型对推理过程的**元认知不确定性**。如果模型即将在显式文本中识别出一个概念性推理错误，这种不确定性会在 hidden state 中提前升高——早于显式的 "Wait..." 文本。

聚合结果（4 题合并，n=374 采样点）：
| segment | n | mean_risk | 解释 |
|---------|---|-----------|------|
| confident | 227 | 2.546 | 正常推理基线 |
| pre_correction | 61 | 2.692 | **比 confident 高 0.146** |
| at_correction | 16 | 3.034 | 纠错时刻最高（sanity check 通过）|
| post_correction | 70 | 2.657 | 纠错后略回落 |

聚合层面存在预转变信号（delta +0.146）。

但逐题拆开后发现**信号是选择性的**：
| task | confident | pre_corr | delta | 类型 |
|------|-----------|----------|-------|------|
| **p28** | 2.775 | **3.553** | **+0.778** | **极强信号，std=0.19** |
| p14 | 2.590 | 2.783 | +0.193 | 中等信号 |
| p17 | 2.498 | 2.437 | -0.061 | 无信号 |
| p27 | 2.341 | 2.247 | -0.094 | 无信号 |

定性分析（逐 anchor 读上下文）揭示了为什么有些任务有信号、有些没有：

- **p28（极强信号）**：组合数学/匹配问题。纠错是**概念性/结构性**的——模型在构建理论框架，发现"这个情况不能推广"、"block 必须是隔离的"。hidden state 在模型"意识到框架有问题"之前就升高了。所有 13 个 pre-correction 采样点一致高 risk（std=0.19），不是偶然波动。
- **p14（中等信号）**：同样是系统性 casework 中的概念纠错。
- **p17（无信号）**：网格路径计数。纠错是**执行性**的——"这条路径数了两次"、"n=1 的 base case 对不对"。模型在做机械验证，不是在识别框架错误。
- **p27（无信号）**：立体几何。纠错是**定义性**的——"什么叫 disphenoid？"、"insphere 的条件是什么？"。模型在搜索知识，不是在发现推理错误。

脚本：`scripts/probe_e172_pre_turnaround_signal.py`。
结果：`results/E172_aime2026_pre_turnaround_signal/qwen35_27b_e172_pre_turnaround_signal_20260503.json`。

**Stage F fact / 人话结论：** Hidden states carry a selective "pre-turnaround signal" — risk elevates BEFORE the model explicitly writes "Wait..." / self-correction markers, but only for conceptual/structural error recognition, not for routine execution checks or definitional uncertainty. The strongest case (p28) shows +28% risk elevation with std=0.19 across all 13 pre-correction samples. This suggests hidden states encode metacognitive uncertainty about the reasoning framework, not just local token risk. The causal direction is not yet proven (correlation, not intervention). / hidden state 中存在选择性的预转变信号——模型在写出"Wait..."之前，hidden risk 就已经升高了。但这个信号只对概念性/结构性的错误识别有效，对执行细节检查和定义不确定不敏感。p28 是最强证据：pre-correction risk 比 confident 高 28%，且所有 13 个采样点一致地高（std=0.19）。这说明 hidden state 编码了对推理框架的元认知不确定性，而不仅仅是局部 token 风险。因果方向尚未通过干预实验证明。

**E147 / p28 细粒度时间曲线（2026-05-03）：**

对 p28 以 100 chars 步长、±500 chars 窗口做逐 anchor 细粒度探测。12 个 anchor 全部显示 uniformly high risk（~3.5），std 仅 0.21-0.30。pre=3.52, at=3.56, post=3.55 —— risk 在整个窗口内平坦高企，不是在 "Wait..." 前一刻尖峰。说明模型在概念性框架构建时进入了**持续的"高元认知不确定性格局"**，而非仅在意识到错误前短暂升高。

**E148 / 错题 hidden risk 探针（2026-05-03）：**

对 4 道错题（p13/p15/p29/p30）做同样 probe，与正确自纠题对比：
| 类型 | confident | pre | at | post | pre-conf delta |
|------|-----------|-----|-----|------|----------------|
| 正确自纠题 (4) | 2.546 | 2.692 | 3.034 | 2.657 | **+0.146** |
| 错题 (4) | 2.753 | 2.635 | 2.688 | 2.682 | **-0.118** |

错题没有预转变信号。三种错题模式：
1. **p15 "自信地错了"**：risk 全程低（2.23-2.58），at_correction 最低——模型不知道自己错了。
2. **p13 "纠错后恐慌"**：post=3.19 > at=2.96 > pre=2.86——纠错后 risk 飙升，"修错了"。
3. **p29/p30 "看起来对但实际错"**：模式类似正确题但 risk 更低，无 pre-turnaround signal。

**核心洞察：** 正确自纠和错误自纠在 hidden state 层面有系统性差异——hidden risk 不仅反映"附近有风险"，还编码了模型对纠错质量的元认知。

**Boundaries / 边界：**
- 当前证据仅在 Qwen3.5-27B 的 4 道 AIME2026 正确题上，不能声称跨模型或跨任务分布。
- 聚合 delta +0.146 主要由 p28 驱动；p17/p27 无信号。
- "预转变"的因果方向尚未证明——这是相关性，不是干预结果。
- 所有 segment（包括 confident）都有 85% 采样点跨过 HP 阈值，再次确认 E166 阈值对 AIME2026 分布过于敏感。

## 5. Current Paper Position / 当前论文位置

**Best headline / 最稳 headline：**

> Evidence-to-decision mismatch in multilingual/process verification: LLM verifiers often contain hidden evidence of process invalidity, but pointwise decisions can still accept answer-correct/process-invalid traces unless the objective, readout, and checking policy force the evidence into the decision. / 多语言/过程验证中的“证据到决策错配”：LLM verifier 内部常有过程无效证据，但如果目标、读出和检查策略不合适，单点决策仍会接受答案正确但过程无效的 trace。

**What is novel / 新意：**

1. ACPI as the object: focus on answer-correct but process-invalid traces, not generic wrong-answer reasoning. / 研究对象是答案正确但过程无效，不是泛泛错题。
2. Strict vs repair-aware split: separates trace-as-proof risk from repair-aware draft reading. / 把“证明”和“草稿”两种口径拆开。
3. Hidden evidence to readout mismatch: residual/MLP/token-mixer signals can see risk while Yes/No or A/B accepts. / hidden 证据与输出决策错配。
4. Multilingual route taxonomy: romanized Chinese and mixed-language routes expose surface lexicalization vs process semantics. / 多语言路径揭示表层词汇化与过程语义错配。
5. Natural NG prevalence with repaired/unrepaired labels: strict ACPI is common under answer-first, but unrepaired ACPI remains low-frequency. / 自然样本中分清 repaired 和 unrepaired。
6. Adaptive checking boundary: hidden triggers can reduce risk for Qwen/Gemma31, but Gemma26 shows why this is not an oracle. / hidden 触发可用但有模型边界。
7. Pre-turnaround signal: hidden states carry a selective metacognitive signal that elevates before conceptual self-correction in CoT, with p28 showing +28% risk elevation (std=0.19) across all pre-correction samples. / hidden state 中存在选择性的预转变信号，在概念性自纠前可检测到。

## 6. 2024-2026 Literature Positioning / 2024-2026 文献定位

This is a targeted scan of recent top-conference, top-journal, and frontier-lab work most relevant to process verification, hidden-state monitoring, reasoning-model faithfulness, and multilingual reasoning. / 这是针对过程验证、hidden-state 监控、reasoning model faithfulness、多语言推理的近期顶会/顶刊/前沿实验室文献扫描。

| Work / 工作 | What it shows / 它证明了什么 | Relation to us / 与我们的关系 |
|---|---|---|
| [ProcessBench, ACL 2025](https://aclanthology.org/2025.acl-long.50/) | Benchmarks identifying erroneous steps in mathematical reasoning. / 评测模型能否找出数学推理错步。 | High relevance. We need compare to it, but our core is ACPI + hidden/readout mismatch + strict/repair-aware + multilingual routes. |
| [Generative Verifiers, ICLR 2025](https://arxiv.org/abs/2408.15240) | Trains verifiers via next-token prediction and shows generative verification scales. / 把 verifier 训练成生成任务。 | We should not claim generic verifier novelty. Our contribution is diagnosing failures of self/verifier decisions and using hidden process-risk triggers. |
| [Rewarding Progress, 2024](https://arxiv.org/abs/2410.08146) | Designs process rewards as progress/step-level advantage for reasoning improvement. / 把过程奖励定义为“这一步是否提高未来成功概率”。 | It strengthens the PRM baseline expectation. We need show how our hidden process validity differs from progress/confidence and how filters retain ACPI. |
| [Right Is Not Enough, 2025](https://arxiv.org/abs/2506.06877) | Correct final answers can mask unsound math reasoning; proposes step verifier. / 答案对不代表过程对。 | Strong collision on outcome-vs-process. Our novelty must be narrower: self-verifier/readout mismatch, hidden localization, multilingual routes, repaired vs unrepaired, and confidence controls. |
| [Reasoning Models Know When They're Right, 2025](https://arxiv.org/abs/2504.05419) | Hidden states in long-CoT reasoning models encode intermediate answer correctness and can reduce tokens via early exit. / long-CoT hidden state 能预测中间答案对错并早停。 | Medium collision. Do not claim “hidden states know correctness” as novelty. Claim non-thinking process-validity under ACPI, not long-CoT answer correctness. |
| [Reasoning Models Don't Always Say What They Think, 2025](https://arxiv.org/abs/2505.05410) | CoT may not faithfully reveal what influenced the answer. / 模型写出的 CoT 不一定忠实反映内部原因。 | Supports our caution that visible trace and hidden state can diverge; our focus is process-validity evidence and verifier decision, not hint verbalization. |
| [Chain-of-Thought Monitorability, 2025/2026](https://arxiv.org/abs/2507.11473) and [OpenAI monitorability note](https://openai.com/index/evaluating-chain-of-thought-monitorability/) | CoT monitoring can be useful but fragile. / CoT 监控有用但脆弱。 | Our hidden-monitor line is complementary: direct/non-thinking hidden signals can trigger checks even when visible CoT is incomplete or unreliable. |
| [DeepSeek-R1, Nature 2025](https://www.nature.com/articles/s41586-025-09422-z) / [arXiv](https://arxiv.org/abs/2501.12948) | RL can incentivize reasoning capability at scale using verifiable rewards. / RL 可诱导强推理能力。 | Shows why process/reward design matters. We need avoid training-scaling claims unless we add LoRA/RL source experiments. |
| [OpenAI o1 system card, 2024](https://openai.com/index/openai-o1-system-card/) | Reasoning models expose safety/faithfulness/final-output complications. / reasoning model 带来 CoT、最终输出和安全边界。 | Justifies our strict separation of TV/TG from DV/NG and the need for final-marker/clean-stop reporting. |
| [mCoT, ACL 2024](https://aclanthology.org/2024.acl-long.649/) | Builds multilingual math CoT instruction data across 11 languages. / 多语言数学 CoT 数据与一致性训练。 | Our multilingual route taxonomy is smaller but more process-focused; we need broader native multilingual tasks to be top-tier. |
| [MultiNRC, 2025](https://arxiv.org/abs/2507.17476) | Native multilingual reasoning benchmark across French, Spanish, Chinese. / 原生多语言推理基准。 | Our romanized/mixed routes are useful but insufficient; add native multilingual/cultural tasks before broad multilingual claims. |
| [MMATH, EMNLP Findings 2025](https://arxiv.org/abs/2505.19126) | Multilingual mathematical reasoning benchmark. / 多语言数学推理基准。 | Useful external benchmark family for future prevalence/verification expansion. |
| [Hard2Verify, 2025](https://arxiv.org/abs/2510.13744) | Step-level verification for recent open-ended frontier math. / 面向前沿开放数学题的逐步验证。 | Raises the bar: our hard tasks are still narrow AIME-style templates. Need broader open-ended tasks and step annotations. |

## 7. Gaps to a Top-Tier Paper / 距离顶会顶刊的不足

1. **TV/TG replication is missing. / thinking verifier 与 thinking generation 还没系统补齐。** Current verifier evidence is mostly DV/MI-DV; natural prevalence is NG. Top-tier reviewers will ask whether reasoning-mode models fix or change the phenomenon.
2. **Natural prevalence is still underpowered and task-narrow. / 自然发生率样本量和任务族还不够。** E119/E146 is good, but 2 unrepaired cases are too few for strong prevalence claims, and tasks are concentrated in AIME-style math.
3. **Human audit reliability is not yet appendix-grade. / 人审可靠性还不够正式。** Need independent double audit, adjudication, written rubric, inter-annotator agreement, and blinded span checks.
4. **Hidden mechanism is not yet a causal circuit. / hidden 机制还不是因果电路。** Probes/localization are strong; causal span patching, component steering, held-out directions, and negative controls need expansion.
5. **Process vs confidence vs stop remains entangled. / 过程、置信度和停止信号仍缠绕。** E106/E114 and E116/E118 show separability is plausible but not complete.
6. **Adaptive check is diagnostic, not deployable. / 自适应检查仍是诊断，不是部署系统。** E138 uses offline diagnostic prefixes; E142 must remove label-informed prefix choice.
7. **External baselines are missing. / 外部 baseline 缺失。** Need compare against ProcessBench-style step detectors, ParaStepVerifier-like prompting, GenRM/PRM-style verifier if available, LLM-as-judge, and text-only locate prompts.
8. **Multilingual claim is promising but not broad enough. / 多语言 claim 有潜力但覆盖不足。** Need native Chinese/French/Spanish/etc., not only romanized/mixed synthetic routes.
9. **Gemma26 negative case is unresolved. / Gemma26 关键反例还没解释清楚。** Hidden signal can fire while local checker accepts unrepaired algebra errors; this is either threshold/readout failure or missing local semantic competence.
10. **Training-source story is deferred. / 训练来源机制还没做。** Without LoRA/RL model organisms, we cannot claim how outcome-only/process-aware training creates or fixes ACPI risk.

## 8. Recommended Next Experiments / 后续实验规划

### Immediate low-GPU or no-GPU work / 近期低 GPU 或无 GPU

1. **E141 rationale taxonomy.** Classify E140/E139 outputs into: no-error-seen, error-seen-but-repair-aware-accept, answer-anchor, local algebra miss, language-route miss, format/readout failure. / 先把失败类型表做出来。Reason: it tells us whether the next fix should be prompt/objective, local math competence, or readout calibration.
2. **Audit rubric + double audit package.** Freeze strict vs repair-aware annotation guide; double-audit E119/E146/E138 sampled rows. / 固定人审说明书并双审。Reason: publication reviewers will not trust single-pass process labels.
3. **External baseline protocol.** Build a small common evaluation set from E61 + E119/E146 and run text-only baselines: LLM-as-judge, locate-only, ProcessBench-style first-error prompt, ParaStepVerifier-like step prompt. / 做可比 baseline。Reason: novelty must be against current verifier literature, not against weak Yes/No only.

### Mechanism and adaptive checking / 机制与自适应检查

4. **E142 online trigger scaffold.** Trigger only at deployable semantic boundaries: sentence end, formula line end, repair marker, final marker, rolling paragraph end. Do not use offline error-span prefixes. / 去掉离线错误 span。Reason: E138 is diagnostic; E142 tests deployability.
5. **E143 Gemma26 unrepaired deep dive.** Use the two unrepaired rows plus synthetic sign-symmetry algebra controls. Test strict local prompts, hidden threshold sweeps, activation steering, and span patching around factorization. / 深挖 Gemma26 两条未修复。Reason: this is the strongest negative case and will define the paper's boundary.
6. **E144 caution-token intervention.** When hidden risk fires, insert a short local warning/check instruction and compare against always-check and no-check. / hidden 响时插入短警示。Reason: tests whether low-cost non-thinking adaptive checking can improve without full long-CoT.
7. **E145 causal component sweep on natural rows.** Patch/steer residual, MLP, token-mixer/attention-related outputs at error spans and completion prefixes, with confidence-matched valid controls. / 在自然行上做组件因果。Reason: turns hidden localization into stronger causal evidence.
8. **E146b process-confidence-stop disentanglement.** Regress/match hidden process score against Yes/No margin, entropy, length, marker count, answer visibility, repair marker, and stop score. / 解缠过程、置信度、停止。Reason: prevents collision with “hidden states just know confidence/correctness.”

### Pre-turnaround signal follow-up / 预转变信号后续

9. **E147 fine-grained p28 probe.** Re-probe p28 at 100-char intervals around each anchor to map the exact temporal profile of the pre-turnaround signal. / 对 p28 做更细粒度探测（100 chars 间隔），画每个 anchor 前后的 risk 时间曲线。Reason: the +0.778 delta with std=0.19 is our strongest single-case evidence; need to characterize it precisely before making a claim.
10. **E148 wrong-case probe.** Run the same probe on the 2 wrong cases (p13, p15) to see whether wrong-answer traces show different hidden risk patterns (e.g., persistently high risk, absent post-correction drop, or different pre/post dynamics). / 对错题做同样 probe。Reason: if wrong cases show different dynamics (e.g., risk stays high after correction, or never drops), it strengthens the interpretation that pre-turnaround + post-correction-drop = successful self-correction.
11. **E149 cross-model pre-turnaround.** If Gemma baseline becomes available, probe at least one Gemma model on the same 4 tasks. / 跨模型验证。Reason: single-model evidence is not a claim.

### Thinking-mode completion / thinking 模式补齐

9. **TV objective ladder.** Re-run E42/E54/E61/E71 subsets with thinking enabled, full generated judgments, parsed final Yes/No, and no first-token logprob. / 补 thinking verifier。Reason: DV results cannot be sold as thinking-verifier results.
10. **TV sibling/label-free and GLM.** Test A/B, reversed order, full-option, and label-free two-pass under thinking final decisions. / 补 thinking sibling。Reason: GLM may be a direct-readout artifact or a deeper contrastive weakness.
11. **TG final-contract natural generation.** Use model-card-compatible sampling, explicit final-contract prompts, separate final marker, fallback, hit-max, post-final continuation, and clean-stop fields. / 补 thinking 自然生成。Reason: Qwen TG failure is closure-sensitive; fallback numbers cannot be prevalence evidence.

### Breadth and paper readiness / 泛化与投稿准备

12. **Broader natural task suite.** Add native multilingual math, code execution, table/unit conversion, proof-validity, and recent open-ended hard math. / 扩展任务族。Reason: current AIME-style scope is too narrow for a broad top-tier claim.
13. **Cross-family replication.** Add only models that pass license/backend/hook smoke; keep failed candidates out of official evidence. / 扩模型族。Reason: phenomenon needs family-level robustness or explicit boundary.
14. **Training/filter simulation.** Compare outcome-only, pointwise, strict, repair-aware, sibling, label-free, PRM-style, and hidden-gated filters on the same labeled rows. / 做筛选器仿真。Reason: connects verifier failure to data curation/training risk.
15. **LoRA/RL model-organism memo.** Train small base/instruct variants under outcome-only, process-aware, and adaptive-check objectives only after the signatures replicate. / 小模型来源实验。Reason: needed if the paper wants mechanism-of-origin rather than only measurement.

## 9. Suggested Paper Structure / 建议论文结构

1. **Problem.** Correct answers can hide invalid processes, and weak verifier objectives select these traces. / 问题：答案对会掩盖坏过程。
2. **Controlled ACPI benchmark.** E42/E54/E60/E61 show robust direct-verifier risk and multilingual/error-family structure. / 受控基准。
3. **Natural prevalence.** E119/E146 separates repaired strict ACPI from unrepaired ACPI. / 自然发生率。
4. **Mechanism.** E106-E114/E131/E132 show hidden process evidence and confidence/false-positive controls. / 机制证据。
5. **Decision mismatch.** E139/E139.5/E140 show evidence can be present but objective/readout can still accept. / 证据到决策错配。
6. **Adaptive check.** E136/E138 show hidden-triggered checking helps in Qwen/Gemma31 but fails on Gemma26 boundary. / 自适应检查。
7. **Pre-turnaround signal (new).** E172 probe shows hidden risk elevates before explicit conceptual self-correction in CoT, with selective metacognitive pattern. / 预转变信号。
8. **Boundaries.** TV/TG, causal mechanism, multilingual breadth, human audit, and external baseline gaps. / 边界。

## 10. Operating Rules Going Forward / 后续执行规则

- Every new result must label its mode: `DV`, `TV`, `NG`, `TG`, `MI-DV`, `MI-TG`, or `PM`. / 每个新结果标模式。
- Prompt leakage counters must be reported: gold answer, manual label, error span, trap note. / 报泄露计数。
- Report final marker, fallback answer, hit-max, post-final continuation, and clean stop separately. / 最终答案字段分开。
- Keep strict and repair-aware denominators separate. / strict 和 repair-aware 分母分开。
- Keep natural prevalence separate from diagnostic/mechanism experiments. / 自然发生率和诊断机制分开。
- Treat hidden probes as evidence and triggers, not as oracle truth. / hidden probe 是证据/触发器，不是真理 oracle。
- Keep GLM and Gemma26 negative cases visible; they make the claim scientifically honest. / 保留 GLM/Gemma26 反例，它们让主张更可信。

