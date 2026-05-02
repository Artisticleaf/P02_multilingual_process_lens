# S5 Integrated Scientific Analysis And Roadmap / S5 综合科学分析与路线图

Date / 日期: 2026-04-27 CST
Data artifact / 数据产物: `results/S5_integrated_analysis/s5_integrated_metrics.json`

Purpose / 目的：把已有实验讲成具体科学事实，而不是只给 E24/E25 这类代号。每个代号下面都说明“模型看到了什么、错在哪里、验证器怎么反应、隐藏层证据说明什么”。

## 0. One-Sentence Answer / 一句话结论

我们现在已经有一条可写进论文的因果证据链：真实模型会生成“答案正确但推理过程有错”的多语言/表层语义陷阱轨迹；绝对式 Yes/No verifier 经常把这些轨迹判为可接受；对比 sibling 轨迹和隐藏层 span/module patch 在多数稳健 pair 上能暴露过程错误信号；但这个现象不是“所有任务、所有模型、所有 verifier 都成立”，困难 Qwen14 词汇例、Gemma4 的位置偏差、AIME 难题零 final-correct 都是必须正面写出的边界。

English terms / 英文术语：ACPI = answer-correct but process-invalid（答案正确但过程无效）；absolute verifier = 绝对式单条轨迹 verifier；contrastive verifier = 对比式 sibling verifier；span patch = 把某段 token 的隐藏状态从一条轨迹替换到另一条轨迹。

## 1. What We Actually Observed / 我们实际观察到了什么

### 1.1 真实 ACPI 不是假设，而是已经在生成轨迹中出现

Manual audit facts / 人工审计事实：

| dataset / 数据 | rows / 行数 | final-correct / 答案正确 | process-invalid / 过程错误 | ACPI / 答案对但过程错 | What this means / 这说明什么 |
|---|---:|---:|---:|---:|---|
| E05 combined simple-task audit / 简单任务综合审计 | 154 | 138 | 18 | 9 | 在真实生成轨迹中，确实有一小批“答案对但过程有错”的样本。 |
| E18 targeted sibling audit / 定向 sibling 审计 | 32 | 25 | 8 | 1 | 定向搜索找到了新的同 route Qwen14 `打八折` ACPI，并找到了干净 valid siblings。 |
| E26 AIME hard smoke / AIME 难题 smoke | 48 | 0 | 7 visible invalid | 0 | 当前本地模型在难题上连 final-correct 都很少，不能直接测 ACPI 频率。 |
| E27 transfer subset / 迁移 verifier 子集 | 11 | 11 | 4 | 4 | 用于测试 Qwen3.5-27B 和 Gemma4 verifier 的锚点，全部答案正确，其中 4 条过程无效。 |

Concrete examples / 具体例子：

1. Discount lexical trap / 折扣词汇陷阱：题目是“一件 80 美元夹克优惠 25% 后售价是多少？”，正确答案是 60。有一条 Qwen3.5 trace 最终给 60，但中间写“打八折，即原价的 75%”。这里“八折”和“75%”互相冲突；答案对了，但推理文字不对。
2. Derivative rule trap / 求导规则陷阱：题目是求 `x^2 + 3x` 的导数。有一条 Qwen14 trace 最终给 `2x+3`，但过程里说“3 是常数，常数的导数为 0，所以 `(3x)'=3`”。最终答案对，但理由把“系数 3”和“整个 3x”混在一起。
3. Chinese discount translation trap / 中文折扣转写陷阱：题目“先上涨 25%，再打八折”，正确最终价格是 80。有一条 Qwen14 same-route trace 写成 “apply the 80% discount” 但计算 `100 * 0.80 = 80`。英文“80% discount”通常表示优惠 80% 后付 20%，但公式是在付 80%；这就是表层词汇化和过程语义错配。
4. Gemma4 transfer drift / Gemma4 迁移漂移：Gemma4 在 `打七五折` 任务上把中文“支付 75%”解释成英文 `75% off`，最后给 `$20` 而不是 `$60`。这条不是 ACPI，因为答案也错了；但它说明表层折扣词汇漂移在非 Qwen 模型上也会出现。

### 1.2 绝对式 verifier 的主要问题不是“不懂数学”，而是过度接受

Process-only absolute verifier means: 给 verifier 一条轨迹，让它只判断推理步骤是否数学有效，不要因为格式或截断扣分。/ process-only absolute verifier 的含义是：只看推理步骤是否有效。

Observed behavior / 观察到的行为：

| setting / 设置 | verifier models / verifier 模型 | key fact / 关键事实 | Plain-language interpretation / 人话解释 |
|---|---|---|---|
| E06 simple-task manual audit | Qwen3.5-9B, Qwen14, DeepSeek-Qwen8B, Phi4-mini | English prompt 下，Qwen3.5-9B、DeepSeek、Phi4 对 ACPI 的 false accept rate 是 1.0；Qwen14 是 0.778。 | 单条轨迹判断时，verifier 很容易因为最终答案对、文字顺、格式像样而说“过程有效”。 |
| E24 E18 targeted audit | 4 local verifiers | Qwen3.5-9B/Qwen14 在中文 prompt 下对 process-invalid 的 yes rate 达到 1.0；多数模型对新 ACPI 也给 Yes。 | 换成定向样本后，绝对式 verifier 仍然漏掉表层词汇错误。 |
| E27 transfer absolute verifier | Qwen3.5-27B, Gemma4 | 两个迁移 verifier 在 11 条锚点上 process-only yes rate 都是 1.0，ACPI false accept rate 都是 1.0。 | 更大/新模型也不能靠“单条 Yes/No 判断”自动解决问题。 |

Scientific fact / 科学事实：absolute verifier 的失败更像 objective/threshold mismatch（目标/阈值错配），而不只是“模型完全没有过程信号”。因为同样的证据放进 contrastive sibling prompt 后，一些模型能明显更好地找出坏轨迹。

### 1.3 对比式 sibling verifier 有用，但不是 oracle

Contrastive verifier means: 给 verifier 同一道题的两条轨迹，一条 valid，一条 ACPI，让它选哪条推理无效。/ 对比式 sibling verifier 的含义是：同题两条轨迹二选一。

Observed behavior / 观察到的行为：

| setting / 设置 | model / 模型 | accuracy / 准确率 | What happened / 发生了什么 |
|---|---|---:|---|
| E12 early selected pairs | Qwen3.5-9B | 0.875 | 早期选择 pair 上，对比比绝对式好很多。 |
| E16 expanded pairs | Qwen14 | 0.818 | 扩展到更多 pair 后，Qwen14 仍较强。 |
| E21 hard Qwen14 `打八折` pair | Qwen14 | 0.333 | 自己生成的困难同 route 词汇 ACPI，Qwen14 反而常选错。 |
| E23 clean Qwen3.5 siblings | Qwen3.5-9B and Qwen14 | 1.000 / 1.000 | 对 Qwen3.5 discount ACPI 的干净 sibling，两个 verifier 都能稳定找错。 |
| E27 transfer contrastive | Qwen3.5-27B | 0.875 | 大模型迁移到对比式后能利用相对过程证据。 |
| E27 transfer contrastive | Gemma4 | 0.542 | Gemma4 很多时候倾向选 A，说明有 position/order bias（位置/顺序偏差）。 |

Scientific fact / 科学事实：sibling comparison 是一个有用的 mitigation（缓解方法），因为它降低了“只看最终答案是否对”的诱惑；但它必须 order-balanced（bad_A/bad_B 都测），也不能宣称 universal oracle（万能裁判）。

### 1.4 隐藏层证据支持“过程错误信号存在”，但还不是完整 circuit 证明

What span patch did / span patch 做了什么：

- 在 bad trace 和 valid sibling trace 的同一题上，选定错误相关 span，例如“apply an 80% discount”或“打八折，即原价的75%”。
- 把 bad trace 在某些层、某些 token span 的 hidden states 替换成 valid trace 对应位置的 hidden states，观察 verifier 的 Yes/No 或 A/B margin 是否按“更像 valid”的方向移动。
- 如果替换非最终答案 span 也能移动 verifier margin，说明过程/错误信息不只在最终答案 token 上。

Key facts / 关键事实：

| result / 结果 | fact / 事实 | Interpretation / 解释 |
|---|---|---|
| E24 causal ledger | 8 个 manual ACPI pair 中，6 个有 robust hidden-span signal。 | 多数稳健 pair 中，隐藏层确实有可干预的过程/错误 span 信号。 |
| E24 causal ledger | 8 个 manual ACPI pair 中，2 个有 MLP clean-direction signal。 | MLP 输出能解释一部分残差流效果，但还不是普遍机制。 |
| E25 layerwise lens | Qwen3.5-9B ACPI final positive rate 0.8，middle positive rate 0.5；Qwen14 ACPI final positive rate 0.5，middle positive rate 1.0。 | 中层和输出层对“是否接受”的倾向不一致，支持 middle-layer process confounding 与 output-head re-entanglement。 |
| E20 hard Qwen14 pair | 新 same-route `打八折` pair 的 span patch 弱。 | 并非每个 ACPI 都有简单可定位的 patch 信号；困难例要作为边界。 |

Scientific fact / 科学事实：我们能说“隐藏状态中存在可因果干预的过程/错误信号”；暂时不能说“我们已经找到了完整 reasoning circuit”。如果要顶会/顶刊级机制主张，下一步需要 head-level、MLP-block、SAE/transcoder 或 attribution-graph 级验证。

## 2. Causal Chain / 因果链总结

当前最强链条不是“某一个指标高”，而是下面这条链：

1. Natural generation / 自然生成：模型真实生成了 final-correct but process-invalid trace，不是我们手写的假样本。
2. Manual process audit / 人工过程审计：逐句标出错误 span，并确认 final answer correct、process invalid、route valid。
3. Absolute over-acceptance / 绝对式过度接受：同一条坏轨迹被 Yes/No verifier 接受。
4. Sibling contrast / sibling 对比：同题 valid sibling 放在旁边后，部分 verifier 能找到哪条错。
5. Hidden intervention / 隐藏层干预：把错误相关 span 的 hidden states patch 到 sibling 方向，会改变 verifier margin。
6. Boundary / 边界：hard Qwen14 lexical pair、Gemma4 位置偏差、AIME 零 final-correct 都提醒我们不能过度外推。

E24 causal ledger numbers / E24 因果链数字：

- 9 个 pair 总数。
- 8 个是 manual ACPI pair。
- 8/8 manual ACPI pair 被 absolute verifier 过度接受。
- 7/8 manual ACPI pair 有 contrastive signal。
- 6/8 manual ACPI pair 有 robust hidden-span signal。
- 2/8 manual ACPI pair 有 MLP clean-direction signal。

## 3. Comparison To Published Work / 与已发表工作的差异

### 3.1 What published work already covers / 已有工作已经覆盖什么

- CoT faithfulness / CoT 忠实性：Turpin et al. 2023 和 Lanham et al. 2023 已经说明 chain-of-thought 解释可能不忠实，且可通过干预推理文本来测忠实性。P02 不能声称“首次发现 CoT 不忠实”。
- Process supervision / 过程监督：`Let's Verify Step by Step`, Math-Shepherd, PRMBench, ProcessBench, PRIME 等已经覆盖“过程监督/过程奖励/过程错误识别很重要”。P02 不能写成“又一个 PRM benchmark”。
- Correct answer but flawed process / 答案对但过程错：Qwen PRM lessons 和 2026 process-outcome alignment 方向已经明确指出 PRM/BoN 评估会被“正确答案但错误过程”干扰。P02 不能泛泛声称这是全新现象。
- LLM-as-judge bias / LLM 裁判偏差：ACL 2024 `Large Language Models are not Fair Evaluators` 已经证明位置偏差等问题。P02 不能把“judge 有位置偏差”当主创新。
- Mechanistic interpretability / 机制解释：Patchscopes、language-specific neurons、attribution graphs 等已有方法和标准很强。P02 不能声称发明了 patching 或已经完成完整 circuit tracing。

### 3.2 What seems novel enough in P02 / P02 仍然足够新的地方

P02 的创新点不是单点，而是一个交叉组合：

1. Multilingual surface lexicalization / 多语言表层词汇化：错误来自 `打八折`, `七五折`, `80% discount`, `75% off` 等跨语言表层形式与真实过程语义之间的错配，而不是普通算术算错。
2. ACPI trace-selection risk / ACPI 轨迹选择风险：我们关注的是“答案正确但过程无效”的样本会被训练数据筛选或 verifier 选择流程保留下来。
3. Objective/threshold mismatch / 目标和阈值错配：同一条坏轨迹在 absolute Yes/No 下被接受，但在 contrastive sibling 下可能被识别，说明问题不只是“没有信号”，也包括 verifier 目标形式不对。
4. Real trace + sibling control / 真实生成轨迹 + sibling 控制：不是手工构造 toy example，而是从模型生成中挖出 bad trace，再找同题 valid sibling。
5. Hidden-span causal evidence / hidden-span 因果证据：在部分稳健 pair 中，非最终答案 span 的 hidden patch 可以移动 verifier margin，说明过程错误信号在内部状态里可被暴露。
6. Honest boundaries / 诚实边界：我们主动保留失败例：Qwen14 hard pair、Gemma4 位置偏差、AIME zero-final-correct。这让论文更可信。

Candidate paper claim / 推荐论文主张：

> Multilingual surface lexicalization creates a realistic family of answer-correct/process-invalid traces. These traces expose a mismatch between local process semantics and absolute verifier objectives: pointwise Yes/No verifiers over-accept them, while sibling comparison and hidden-span interventions reveal process/error signals in robust cases. The effect transfers across model families but has clear boundaries under hard lexical cases, judge position bias, and hard math tasks where final-correct traces are rare.
>
> 中文：多语言表层词汇化产生一类真实的 ACPI 轨迹。这些轨迹暴露了局部过程语义与绝对式 verifier 目标之间的错配：单条 Yes/No verifier 会过度接受，而 sibling 对比与 hidden-span 干预能在稳健例中暴露过程/错误信号。该现象可跨模型迁移，但在困难词汇例、judge 位置偏差和 final-correct 稀少的难题上有明确边界。

## 4. Research Boundary / 科研边界

我们现在可以说 / What we can claim now：

- 真实生成轨迹中存在 ACPI，不是纯人工构造。
- 多语言表层词汇陷阱是 ACPI 的一个具体来源。
- 绝对式 verifier 会过度接受部分 ACPI。
- 对比式 sibling verifier 在一些模型和 pair 上显著优于绝对式。
- 非最终答案 span 的 hidden states 在部分 pair 中携带可因果干预的过程/错误信号。
- Qwen3.5-27B 和 Gemma4 的迁移结果支持“absolute verifier 过度接受不是单一旧模型问题”。

我们现在不能说 / What we must not claim yet：

- 不能说 ACPI 的总体发生率很高；当前是 targeted/selected set，不是随机总体估计。
- 不能说所有多语言任务都有这个风险；现在强证据集中在折扣、比例、导数等简单可审计任务。
- 不能说 sibling comparison 一定解决问题；Qwen14 hard pair 和 Gemma4 position bias 已经反例。
- 不能说已经发现完整 hidden circuit；目前是 residual/module patch + diagnostic layerwise lens。
- 不能说 AIME 难题上已经发现 ACPI；目前 AIME smoke 的事实是 zero final-correct，因此还没有 ACPI 候选。

## 5. Mainline Plan / 主线任务总体规划

五条 mainline 仍然够，但需要重新命名为“因果链五段”，不是五个孤立实验。

| Mainline / 主线 | Human question / 人话问题 | Current answer / 当前答案 | What is missing / 缺什么 |
|---|---|---|---|
| A. Existence / 存在性 | 模型真的会生成“答案对但过程错”的轨迹吗？ | 会。E05 有 9 条 ACPI；E18 新增同 route Qwen14 `打八折` ACPI。 | 需要更多 clean same-route pair，最好至少 8 对。 |
| B. Lexical cause / 词汇原因 | 这些错误是不是多语言表层词汇导致的，而不是随机算错？ | 多个折扣例支持：`打八折/七五折/80% discount/75% off` 会错配。 | 需要 controlled paraphrase：同题改写只换表层词，看 ACPI/semantic drift 是否随词汇变化。 |
| C. Verifier mismatch / verifier 错配 | 单条 Yes/No verifier 为什么危险？ | 它过度接受 ACPI；同一证据放到 contrastive prompt 后部分模型能找错。 | 需要阈值校准、prompt 对照、order-bias 控制。 |
| D. Hidden signal / 隐藏信号 | 错误过程信号是否存在于隐藏层？ | 6/8 ACPI pair 有 robust hidden-span signal；2/8 有 MLP signal。 | 需要 head-level/MLP-block/SAE 或 attribution-graph 级机制验证。 |
| E. Boundary and mitigation / 边界与缓解 | 这个方法能否推广到难题和新模型？ | Qwen3.5-27B absolute 仍失败、contrastive 更好；Gemma4 absolute 失败且 contrastive 有位置偏差；AIME 当前无 final-correct。 | 需要困难任务 conditional sampling、更多模型、更多语言和人工复审。 |

## 6. Next Experiments / 后续实验设计

### Experiment 1: Clean Same-Route Pair Bank / 干净同 route sibling pair bank

Purpose / 目的：证明 ACPI 不是单个偶然样本，而是一类可复现的 trace-selection risk。

Design / 设计：

- 任务族：折扣、比例、导数、单位换算、百分比先后操作。
- 每个任务找同 route 的 bad ACPI 和 valid sibling，要求题目、输入语言、推理语言一致。
- 人工逐句审计：final answer、process validity、format、route、earliest error 都要标。

Hoped result / 希望结果：至少 8 对 paper-grade pair，其中 majority 有 absolute over-acceptance，部分有 contrastive/hidden-span signal。

If negative / 如果失败：说明 ACPI 更稀有，论文应转成“selected high-risk family”而不是“常见现象”。

### Experiment 2: Lexical Causal Paraphrase Grid / 表层词汇因果改写网格

Purpose / 目的：把“表层词汇化导致错误”从观察提升到更接近因果。

Design / 设计：同一道题只改写折扣表达：

- Chinese pay form / 中文支付形式：`打八折`, `付原价80%`, `按八折价支付`。
- English discount form / 英文优惠形式：`20% off`, `80% discount`, `pay 80% of the original price`。
- Trap form / 陷阱形式：中文题 + 英文推理，或英文题 + 中文推理。

Hoped result / 希望结果：`打八折 -> pay 80%` 稳定正确；`打八折 -> 80% discount` 或 `七五折 -> 75% off` 更容易产生 process semantic drift。

If negative / 如果失败：词汇陷阱可能不是主因，需降级为“某些 surface forms 的局部风险”。

### Experiment 3: Absolute vs Contrastive Objective Intervention / 绝对式与对比式目标干预

Purpose / 目的：证明 verifier 失败与 objective/threshold 有关，而不只是模型能力弱。

Design / 设计：同一批 ACPI/valid pair，用四种 prompt：

1. Absolute Yes/No, process-only / 单条是/否，只看过程。
2. Absolute Yes/No, training-candidate / 单条是/否，同时看答案、过程、格式。
3. Contrastive A/B, invalid trace selection / 对比选坏轨迹。
4. Contrastive A/B with shuffled order and calibrated threshold / 对比并顺序平衡、阈值校准。

Hoped result / 希望结果：absolute false accept 高；contrastive 在 Qwen-family 上改善；Gemma4 类模型暴露位置偏差。

If negative / 如果失败：若 contrastive 也普遍失败，说明 hidden signal 不能被普通 verifier objective 利用，需要专门训练 verifier。

### Experiment 4: Mechanism Deepening / 机制深化

Purpose / 目的：把“hidden span 有信号”推进到“哪个模块、哪层、哪类头或 MLP feature 在搬运信号”。

Design / 设计：只选已经稳健的 pair，例如 Qwen3.5 `234/181000`、Qwen14 derivative `402/403`。

- Head-level patch / attention head 级 patch。
- MLP-block ablation / MLP block 消融。
- Layerwise lens + tuned lens check / 分层 lens 与 tuned lens 对照。
- Optional SAE/transcoder / 可选稀疏自编码器或 transcoder，对齐 attribution-graph 标准。

Hoped result / 希望结果：中层 MLP 或特定 attention heads 对 verifier margin 有稳定方向性影响；最终输出层会把部分过程错误信号与 final-answer correctness 重新混合。

If negative / 如果失败：机制主张应保持在“残差流层面有因果信号”，不写成模块/circuit 发现。

### Experiment 5: AIME Conditional Final-Correct Sampling / AIME 条件化 final-correct 采样

Purpose / 目的：回答“简单任务上的现象到困难数学是否还存在”。

Design / 设计：

- 不再直接随机采样 AIME，因为 E26 已显示 final-correct 为 0。
- 先用更强模型或更多 samples 得到 final-correct trace。
- 对 final-correct trace 做人工过程审计，寻找 ACPI。
- 若有 ACPI，再跑 absolute/contrastive verifier 和 hidden-span patch。

Hoped result / 希望结果：如果困难任务中也有 final-correct/process-invalid trace，absolute verifier 仍会过度接受；但频率可能低于简单任务。

If negative / 如果失败：说明 ACPI 在 hard math 上可能被 final-correct 稀缺性压低，论文要把 AIME 写成 boundary/control。

### Experiment 6: Transfer Generation Fix / 迁移生成修复

Purpose / 目的：确认 Qwen3.5-27B 和 Gemma4 作为 generator 是否也能产生 ACPI，而不仅仅作为 verifier 过度接受已有 ACPI。

Design / 设计：

- Qwen3.5-27B：关闭或约束 thinking/meta-planning，强制直接给最多 8 行推理和单行 final answer。
- Gemma4：重采 `打七五折`, `打八折`, `优惠75%`, `20% off`, `pay 80%` 等折扣改写。
- 每个模型每个任务至少 20 samples，人工抽审 high-risk rows。

Hoped result / 希望结果：Gemma4 的 `七五折 -> 75% off` 漂移可复现；Qwen3.5-27B 若格式修好，可能也会产生 surface drift 或 ACPI。

If negative / 如果失败：迁移结果仍可作为 verifier 风险，而 generator ACPI 的跨模型证据需要更多模型。

## 7. Paper Structure Recommendation / 论文结构建议

1. Introduction / 引言：为什么 answer-correct trace selection 不安全，尤其在 multilingual surface semantics 下。
2. Problem definition / 问题定义：ACPI、surface lexicalization、absolute verifier、contrastive sibling、hidden-span signal。
3. Data and audit / 数据与审计：真实生成、人工逐句标签、format/route/final/process 分离。
4. Existence / 存在性：具体 ACPI examples，别只报数字。
5. Verifier mismatch / verifier 错配：absolute 过度接受 vs contrastive 改善与失败。
6. Mechanism / 机制：residual/module patch + layerwise lens；谨慎写，不说完整 circuit。
7. Transfer and hard-task boundary / 迁移与困难任务边界：Qwen3.5-27B/Gemma4、AIME。
8. Mitigation / 缓解：order-balanced sibling comparison + conservative reject；不是 oracle。
9. Limitations / 限制：selected set、simple-task concentration、manual audit、no training, no full circuit。

## 8. Sources Checked / 已复核文献来源

- Turpin et al., `Language Models Don't Always Say What They Think`, NeurIPS 2023: https://arxiv.org/abs/2305.04388
- Lanham et al., `Measuring Faithfulness in Chain-of-Thought Reasoning`, 2023: https://arxiv.org/abs/2307.13702
- Qwen team, `The Lessons of Developing Process Reward Models in Mathematical Reasoning`, 2025: https://arxiv.org/abs/2501.07301
- `PRIME: Process Reinforcement through Implicit Rewards`, 2025: https://arxiv.org/abs/2502.01456
- `ProcessBench: Identifying Process Errors in Mathematical Reasoning`, 2024: https://arxiv.org/abs/2412.06559
- `PRMBench: A Fine-grained and Challenging Benchmark for Process-Level Reward Models`, 2025: https://arxiv.org/abs/2501.03124
- Wang et al., `Large Language Models are not Fair Evaluators`, ACL 2024: https://aclanthology.org/2024.acl-long.511
- `Judging the Judges`, 2024: https://arxiv.org/abs/2406.12624
- Qwen3.5-27B model card: https://huggingface.co/Qwen/Qwen3.5-27B
- Gemma4 model card: https://huggingface.co/google/gemma-4-E4B-it
- AIME2024 dataset: https://huggingface.co/datasets/TianHongZXY/AIME2024
- AIME2025 dataset: https://huggingface.co/datasets/TianHongZXY/AIME2025
