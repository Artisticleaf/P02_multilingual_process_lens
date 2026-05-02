# Verifier Objective and Mechanism Audit / Verifier 目标与机制审计

Date / 日期: 2026-04-28 CST

Purpose / 目的：本文件回答当前 P0 证据链中的七个关键问题：absolute verifier 是谁、它是否来自官方推荐、absolute 与 sibling objective 的差异、E50 residual hidden-state mechanism 的含义、与既有工作的重叠边界、controlled trace construction 的解释、以及 ACPI trace 到底可能来自记忆/过拟合还是潜在推理被干扰。

## 1. P0 absolute verifier identity / P0 absolute verifier 身份

Short answer / 简短结论：三个 P0 模型的 absolute verifier 都是“同一个模型自己做自己的 verifier”（self-verifier）。这不是任何官方文档指定的 verifier checkpoint，而是我们的研究设计。官方文档主要告诉我们如何加载模型、如何套用 chat template、如何避免 special token 重复、如何使用多卡/低精度；官方文档并没有说“请用 Qwen3.5-27B 或 Gemma4-31B-it 当过程 verifier”。

| P0 model / P0 模型 | Absolute verifier actually used / 实际 absolute verifier | Setting / 设置 | Official vs methodological / 官方推荐还是我们选择 |
|---|---|---|---|
| `qwen35_27b` | `qwen35_27b` self-verifier, local path `/home/Awei/LLM/Model/base/qwen35_27b` | E42 `official_if_chat`, `used_chat_template=True`, `enable_thinking=False`, bf16, `device=auto`, deterministic Yes/No option log-prob scoring | Methodological choice. 官方只约束 chat/inference 格式；self-verification 是我们的实验设计。 |
| `gemma4_31b_it` | `gemma4_31b_it` self-verifier, local path `/home/Awei/LLM/Model/base/gemma4_31b_it` | E42 `official_if_chat`, `used_chat_template=True`, bf16, `device=auto`, deterministic Yes/No option log-prob scoring | Methodological choice. 官方没有指定它是 verifier；我们使用官方模板做 self-verifier 测试。 |
| `gemma4_26b_a4b_it` | `gemma4_26b_a4b_it` self-verifier, local path `/home/Awei/LLM/Model/base/gemma4_26b_a4b_it` | E42 `official_if_chat`, `used_chat_template=True`, bf16, `device=auto`, deterministic Yes/No option log-prob scoring; max length 4096 for memory safety | Methodological choice. 官方没有指定它是 verifier；我们使用官方模板做 self-verifier 测试。 |

What is official / 哪些设置是官方相关：

- Chat/instruction models should use the model-specific chat template. / chat/instruction 模型应使用模型自己的 chat template。
- If a rendered chat template is tokenized later, duplicate special tokens should be avoided. / 先渲染 chat template 再 tokenize 时，应避免重复 special tokens。
- Big-model inference commonly uses `device_map="auto"` and reduced precision to fit memory. / 大模型推理通常用 `device_map="auto"` 与低精度降低显存压力。
- Deterministic Yes/No log-prob scoring is not a generation task, so model-card sampling temperature/top-p recommendations are not the decisive parameter. / 确定性的 Yes/No logprob 打分不是开放生成，因此模型卡的 temperature/top-p 建议不是关键参数。

Why this is a useful design / 为什么这个设计有科学意义：如果一个强模型在“只看一个 trace、回答 Yes/No”的自验证场景里过度接受 invalid process，而同一个模型在“把两个 sibling trace 放在一起比较”时能稳定找出错误，那么问题就不只是模型没有能力识别错误，而是 objective/threshold 没把它已经有的过程证据信号转化成正确决策。

## 2. Plain-language explanation: absolute vs sibling / 说人话解释：absolute 与 sibling

Plain-language version / 说人话版本：

absolute Yes/No verifier 就像老师只看一份作业，然后问：“这份解答过程对吗？”如果最后答案是对的、文字很顺、步骤看起来像数学推理，模型容易给一个“算了，通过”的 Yes。它不是完全看不见错误，而是这个任务形式让“答案对”“语气像推理”“熟悉表述”这些捷径把局部过程错误压过去了。

sibling comparison 是把两份同题、同答案、只有某个局部步骤不同的 trace 放在一起问：“哪一份过程错？”这样最终答案和题目难度被抵消掉，模型不得不注意两份 trace 的局部差异。我们现在看到的是：同一个模型在 absolute Yes/No 下会接受一半 invalid-correct trace，但在 sibling comparison 下 24/24 都选对 invalid trace。也就是说，错误信号不是不存在；它在模型内部/上下文里存在，只是 absolute Yes/No objective 的阈值和决策方式没有把这个信号用好。

Professional phrasing / 专业表述：

The core failure is not merely a capability failure of detecting process errors. It is an objective-induced decision failure: under a pointwise Yes/No objective, answer correctness and fluent surface form can dominate the decision threshold, causing process-invalid but answer-correct traces to be accepted. Under an order-balanced sibling-comparison objective, final answer and surface task context are controlled, making the local process-invalid span contrastive and decision-relevant.

中文翻译：核心失败不只是“模型没有能力检测过程错误”。它更像是目标函数诱发的决策失败：在单点 Yes/No 目标下，答案正确和表面流畅会压过局部过程错误，使“答案对但过程错”的 trace 被接受；在顺序平衡的 sibling comparison 目标下，最终答案和题目上下文被控制住，局部过程错误变成对比性的、必须用于决策的证据。

## 3. E50 residual hidden-state mechanism / E50 residual hidden-state 机制是什么

Plain-language version / 说人话版本：

E50 不是在说“我们找到了某一个神经元开关”。它做的是：当 verifier 读完 prompt、马上要输出 Yes 或 No 的时候，每一层都有一个 residual stream 向量。可以把这个向量理解成模型到这一刻为止对整段题目和 trace 的内部摘要。E50 把 valid trace 和 invalid trace 的这些向量取出来，问三个问题：

1. 这些向量里能不能线性地区分“过程有效”和“过程无效”？
2. 这个区分方向能不能 leave-one-task-out，也就是在没见过的任务上迁移，而不是只记住某道题？
3. 如果把这个方向加回模型的 residual stream，模型的 Yes/No 分数会不会真的改变，甚至把一些 invalid trace 从 No/Yes 方向翻转？

当前 P0 结果显示：三个核心 P0 模型的最佳 leave-one-task-out residual probe accuracy 都是 0.9583，随机同范数方向接近机会水平；把 residual 向量朝“valid”方向推，会让多个 invalid rows 的 Yes-No margin 增大并产生翻转。这说明 hidden state 里确实有可用的 process-validity evidence，而且这个证据对 verifier 决策有因果影响。但安全表述应是 distributed residual-state process evidence with causal steering effects / 分布式 residual-state 过程证据及因果 steering 效应；不能说我们已经找到了完整 circuit，也不能说单个 MLP 就是机制。

E50 design details / E50 设计细节：

- Input / 输入：`data/processed/e42_e39_objective_focus_20260428.jsonl`，包含 paired `valid_correct` 与 `invalid_correct`，最终答案相同。
- Feature / 特征：official verifier prompt 下，每个候选层 prompt-final token 的 residual hidden state。
- Probe / 探针：用训练任务的 valid mean minus invalid mean 得到方向，对 held-out task 做分类。
- Control / 控制：随机同范数方向作为 control。
- Steering / 干预：把该方向加到 residual stream，测 Yes/No option log-prob margin 是否变化。
- Scope / 边界：机制诊断，不是自然发生率估计；小规模成对任务，不等同于完整机制分解。

## 4. Relation to published work / 与已发表工作的关系

Short answer / 简短结论：相关工作已经证明过若干相邻事实，例如 process supervision 优于只看最终答案、LLM 生成的 CoT 可能不忠实、隐藏表示可被 probe/steering、pairwise/rationale-aware verifier 可优于单点判断。但我们目前的组合点仍有新意：多语言/表层语义陷阱下的 answer-correct but process-invalid trace-selection 风险；同一 P0 模型在 self-verifier absolute Yes/No 与 sibling comparison 之间的系统性差异；以及在最终答案相同的 paired trace 中，把 residual process-validity evidence 与 verifier 过度接受连接起来。

Published overlaps / 可能撞车处：

- Process supervision / 过程监督：OpenAI 的 “Let’s Verify Step by Step” 证明，监督中间步骤比只监督最终答案更能提高数学推理可靠性。我们的工作与此同方向，但重点不是训练 PRM，而是审计最新中等开源模型在 trace-selection/verifier objective 下的过度接受风险。
- ProcessBench and error localization / 过程错误基准：ProcessBench 等工作构建了定位推理错误的 benchmark，强调 PRM 需要识别过程错误。我们的 E42/E50 更窄但更因果：最终答案被控制为相同，absolute 与 sibling objective 被直接比较，hidden residual steering 被纳入证据链。
- Pairwise/rationale-aware verification / 成对或 rationale-aware 验证：已有工作显示 pairwise self-evaluation 或 rationale-aware verifier 能改善答案验证。我们的区别是把 pairwise sibling comparison 用作“揭露 absolute Yes/No threshold/objective 失配”的诊断工具，并且聚焦 ACPI trace-selection 风险，而不是只追求更高 answer-verification accuracy。
- CoT faithfulness / 思维链忠实性：Turpin 等工作显示 CoT 解释可能受偏置影响、并不总反映真实决策原因。我们的结果与“visible trace 不等于真实推理路径”相容，但我们研究的是 verifier 是否会接受一个 visible process-invalid trace。
- Representation engineering / 表示工程与 activation steering：RepE 等工作说明 residual representations 可以被读出和 steer。我们的 E50 是相关方法的任务化应用；新意在于 target 是 process validity under final-answer-controlled traces，而不是一般 truthfulness/sentiment/style。
- Attention Residuals / 注意力残差：Kimi/Moonshot 的 “Attention Residuals” 关注 attention residual connection 如何影响深层 transformer 信息流、linear attention、长上下文与语言建模性能。它与我们都使用 residual/attention-related language，但科学问题不同：该论文是架构/信息流层面的 attention residual 机制；我们的 E50 是 verifier prompt 中 residual stream 里是否编码 process-validity evidence，以及 steering 该证据是否改变 Yes/No 决策。相关但不等价，不构成直接撞车。

Safe novelty statement / 安全创新点表述：

Our novelty is not “hidden states contain information” in the abstract. Our novelty is the causal-chain diagnosis in a trace-selection setting: surface-semantic traps create answer-correct/process-invalid traces; pointwise Yes/No self-verifiers over-accept them; sibling comparison reveals the local process error; and residual-state interventions show that process-validity evidence is present but underused by the absolute decision objective.

中文翻译：我们的创新点不是抽象地说“hidden state 里有信息”。我们的创新点是 trace-selection 场景中的因果链诊断：表层语义陷阱产生答案正确但过程无效的 trace；单点 Yes/No self-verifier 过度接受；sibling comparison 揭露局部过程错误；residual-state 干预显示过程有效性证据存在，但 absolute 决策目标没有充分使用它。

## 5. Controlled trace construction / 什么是受控 trace 构造

Plain-language version / 说人话版本：

“受控 trace 构造”就是我们有意构造一组 paired traces：同一道题、同一个最终答案、一个过程真的有效，另一个过程里混入一个局部语义/数学错误，但最终答案仍然被修正为正确。这样做不是为了声称这些 trace 一定会在真实使用中高频自然出现，而是为了隔离一个科学问题：当答案已经正确时，verifier 会不会仍然检查过程？如果它不检查，那么 trace selection、best-of-N、self-verification、PRM/RM 过滤、数据蒸馏筛选等流程都有潜在风险。

Does this relate to model distillation? / 这和大模型厂商相互蒸馏有关吗？

可能有关，但目前没有直接证据。原因是：很多模型训练/蒸馏会使用合成 reasoning traces，如果筛选器更看重最终答案或表面流畅，而没有强 process validity 约束，那么“答案对但过程有局部污染”的 rationale 可能被保留并传播。另一方面，我们当前 controlled traces 是人工/模板化构造，不足以证明厂商蒸馏导致了该现象。

How to dig deeper / 如何继续深挖：

- Cross-model trace transfer / 跨模型 trace 转移：让模型 A 生成 trace，模型 B 做 absolute/sibling verifier，检测是否存在同源模型更容易过度接受的问题。
- Style/source ablation / 风格与来源消融：同一错误过程，用不同模型风格重写，观察 verifier 是否因为“像某类训练数据”而更宽松。
- Distillation-like filtering simulation / 蒸馏式筛选模拟：用 outcome-only filter、absolute process filter、sibling process filter 分别筛 trace，比较最终保留下来的 ACPI 比率。
- Fresh parameterized tasks / 新鲜参数化任务：随机生成未公开数字与语义组合，降低 benchmark memorization 解释。

## 6. Professional claim formulation / 面向论文的主张表述

Conservative paper-style claim / 保守论文表述：

We study a trace-selection failure mode in which a reasoning trace reaches the correct final answer while containing a locally invalid process step. In controlled multilingual and surface-semantic trap settings, current medium-scale open P0 models can over-accept such answer-correct/process-invalid traces under a pointwise Yes/No self-verification objective. The same models reliably expose the invalid process when evaluated with order-balanced sibling comparison, indicating that the relevant process signal is available but not sufficiently used by the pointwise objective/threshold. Residual-state probes and steering further show that verifier hidden states encode transferable process-validity evidence and that intervening on this evidence can causally change Yes/No margins. We therefore frame the risk as an interaction among surface lexicalization, process semantics, final-answer anchoring, and verifier objective design, rather than as a simple answer-correctness or formatting failure.

中文翻译：我们研究一种 trace-selection 失败模式：推理 trace 得到正确最终答案，但包含局部无效过程步骤。在受控的多语言与表层语义陷阱设置中，当前中等规模开源 P0 模型在单点 Yes/No 自验证目标下会过度接受这些“答案正确但过程无效”的 trace。同一批模型在顺序平衡的 sibling comparison 评估中能可靠暴露无效过程，说明相关过程信号是可获得的，但没有被单点 objective/threshold 充分使用。Residual-state probe 与 steering 进一步显示 verifier hidden states 编码了可迁移的过程有效性证据，并且干预这些证据会因果性改变 Yes/No margin。因此，我们将该风险表述为表层词汇化、过程语义、最终答案锚定和 verifier objective 设计之间的交互，而不是简单的答案正确性或格式错误问题。

Do not claim yet / 暂时不要声称：

- 不要说自然场景高频发生；E48 简单无泄露样本当前 ACPI 为 0。
- 不要说 hard-task ACPI 已在 P0 上成立；E49 当前被 final-correct/format gate 卡住。
- 不要说已找到完整神经 circuit；E50 是 residual-state evidence 与 steering，不是完整 circuit decomposition。
- 不要把 Qwen2.5-Math hard-task archived results 放入主线证据。

## 7. Overfit, memorization, latent reasoning, or polluted autoregression? / 是过拟合、记忆、潜在推理，还是自回归污染？

Current best interpretation / 当前最稳妥解释：这不是单一原因。当前证据最支持的是“模型/上下文中存在过程有效性信号，但 absolute Yes/No 决策没有充分使用它”。这和以下机制都可能同时存在：

1. Answer-first or memorized answer / 答案优先或答案记忆：模型可能先知道/猜到答案，再生成或接受一个看起来合理但局部错误的解释。简单模板题和公开 benchmark 都可能有这种风险。
2. Latent reasoning with unfaithful visible trace / 潜在推理存在但可见 trace 不忠实：模型内部可能通过别的路径得到正确答案，可见文字只是事后 rationalization，因此会出现答案对、文字过程错。
3. Autoregressive contamination / 自回归污染：一旦早期 token 走上错误定义或错误语义，后续 token 可能又被最终答案锚定拉回正确答案，形成“局部错但最后对”的不一致 trace。
4. Output-head/threshold mismatch / 输出头或阈值失配：hidden state 里有 process-invalid evidence，但 Yes/No 输出头更偏向答案正确、表面流畅或默认肯定，导致 absolute accept。
5. Surface lexicalization trap / 表层词汇陷阱：多语言术语、近义词、日常词与数学词、严格/非严格不等式等，会让“看起来像对”的局部词汇选择变成过程错误。

What current evidence rules in/out / 当前证据能说明什么：

- E42 sibling comparison 1.00 accuracy rules out a pure inability story: the models can detect these local errors when objective makes them contrastive. / E42 的 sibling comparison 1.00 准确率排除了“完全不会看错误”的解释。
- E50 residual probe/steering rules in latent process evidence: hidden states contain transferable validity information and steering it changes decisions. / E50 支持 hidden state 中存在潜在过程证据。
- E48 simple natural prevalence 0 ACPI means we cannot yet claim this happens frequently without controlled construction. / E48 表明不能声称简单自然 prompt 高频发生。
- Current results do not yet distinguish memorized answer, implicit reasoning, and autoregressive repair as the source of final correctness. / 当前结果还不能区分最终答案正确来自记忆、隐式推理还是自回归修补。

Are the correct answers “flash of insight” or logical reasoning? / 正确答案是“灵光一闪”还是逻辑推理？

Visible trace alone cannot prove logical reasoning. A correct final answer with an invalid visible process could be a memorized answer, an implicit calculation not faithfully verbalized, a shortcut, or a later repair after a bad intermediate token. Our current contribution is to show that the verifier can have access to process-validity evidence while failing to use it in the absolute Yes/No decision. To decide whether the generator itself reasoned, we need new experiments that separate answer acquisition from trace production.

中文翻译：只看可见 trace 不能证明模型真的按这条文字链做了逻辑推理。答案对但可见过程错，可能是记住答案、内部做了但没忠实说出来、用了捷径，或早期走错后又被答案锚定修回来。我们目前证明的是 verifier 可能有过程有效性证据但 absolute Yes/No 决策没有用好。若要判断 generator 是否真的推理，需要把“得到答案”和“生成 trace”拆开做实验。

## 8. Next experiments with highest information gain / 下一步最高信息收益实验

E53 answer-anchor ablation / E53 答案锚定消融：对同一 trace 构造 four conditions: final answer shown/correct, final answer removed, final answer wrong, final answer masked. Compare absolute Yes/No and sibling comparison. Purpose: isolate whether correct final answer is the main driver of over-acceptance. / 目的：隔离“答案正确”是否是过度接受主因。

E54 parameterized no-leak generalization / E54 参数化无泄露泛化：扩展到更多非 discount 任务，如 mean/median, range/average, strict/non-strict inequality, unit conversion, percentage base, multilingual quantifiers, geometry notation collision。随机数字、随机语言、随机表面词，人工审计 10-20% sample。Purpose: show commonality beyond a few examples. / 目的：证明共性，不被 discount 样例限制。

E55 residual-to-logit mediation / E55 residual 到 logit 的中介分析：记录每层 residual validity direction 对 Yes/No logits 和 A/B logits 的贡献，做 token-position sweep、layer sweep、patch only error-span vs final-token、ablate final-answer tokens。Purpose: explain why sibling uses the signal but absolute underuses it. / 目的：解释为什么 sibling 能用信号而 absolute 没用好。

E56 component decomposition / E56 组件分解：在 E50 strong layers 上分离 residual, attention output, MLP output; compare patching attention-only, MLP-only, residual-only; add causal controls and random/opposite directions。Purpose: move from residual evidence toward circuit evidence without overclaiming. / 目的：从 residual 证据推进到更细的机制证据。

E57 P0 hard-task final-correct harvesting / E57 P0 困难题 final-correct 采样：先用官方推荐生成设置和 benchmark parser 获取 P0 final-correct rows，再单独要求 trace-selection final-line formatting，然后在人审 process validity。Purpose: determine whether hard tasks show different ACPI profile. / 目的：回答 AIME/hard-task 是否不同。

E58 distillation-filter simulation / E58 蒸馏筛选模拟：让多个模型生成 traces，再用 outcome-only, absolute process, sibling process 三种 filter 选择数据，比较留下的 ACPI。Purpose: test whether distillation-like filtering can amplify this risk. / 目的：测试蒸馏式数据筛选是否会放大风险。

E59 cross-family verifier / E59 跨家族 verifier：Qwen trace by Gemma verifier, Gemma trace by Qwen verifier, plus external P0 candidates after smoke test. Purpose: decide whether over-acceptance is self-verifier-specific or a broader verifier objective issue. / 目的：判断风险是否仅限 self-verifier。

## 9. Sources / 参考来源

Verified on 2026-04-28. / 2026-04-28 已核对。

- Hugging Face chat templates / Hugging Face chat 模板：https://huggingface.co/docs/transformers/main/chat_templating
- Hugging Face Accelerate big-model inference / Hugging Face Accelerate 大模型推理：https://huggingface.co/docs/accelerate/main/en/usage_guides/big_modeling
- Qwen3.5-27B model card / Qwen3.5-27B 模型卡：https://huggingface.co/Qwen/Qwen3.5-27B
- Gemma4-31B-it model card / Gemma4-31B-it 模型卡：https://huggingface.co/google/gemma-4-31B-it
- Let’s Verify Step by Step / 逐步验证：https://arxiv.org/abs/2305.20050
- ProcessBench / 过程错误基准：https://aclanthology.org/2025.acl-long.50/
- Rationale-Aware Answer Verification by Pairwise Self-Evaluation / 基于成对自评估的 rationale-aware answer verification：https://aclanthology.org/2024.emnlp-main.905/
- Language Models Don’t Always Say What They Think / 语言模型并不总说出它们真正的决策原因：https://proceedings.neurips.cc/paper_files/paper/2023/hash/ed3fea9033a80fea1376299fa7863f4a-Abstract-Conference.html
- Representation Engineering / 表示工程：https://arxiv.org/abs/2310.01405
- Attention Residuals / 注意力残差：https://arxiv.org/abs/2603.15031
