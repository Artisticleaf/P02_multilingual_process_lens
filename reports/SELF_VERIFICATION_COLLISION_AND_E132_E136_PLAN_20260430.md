# Self-Verification Collision Audit and E132-E136 Plan / 自验证撞车审计与 E132-E136 计划

- Date / 日期：2026-04-30
- Scope / 范围：`Reasoning Models Know When They're Right: Probing Hidden States for Self-Verification` 与相邻 adaptive thinking / hidden confidence / PRM 工作；并敲定 E132-E136 的实现边界。

## 1. Collision Risk / 撞车风险结论

Conclusion / 结论：`Reasoning Models Know When They're Right` is a medium collision risk, not a fatal collision. / 这篇是中等撞车风险，不是致命撞车。

It overlaps with us on three points:

- Hidden-state probing / hidden state 探针：they also show that hidden states encode correctness information.
- Internal evidence not fully used / 内部证据未被充分使用：they use a hidden verifier for early exit because the model keeps reasoning after reaching a correct answer.
- Adaptive compute / 自适应计算：they reduce tokens by thresholding hidden-probe confidence.

But it does not directly cover our main object:

- They study intermediate answer correctness in long explicit reasoning models. / 他们研究 long-CoT reasoning model 的中间答案正确性。
- We study answer-correct but process-invalid trace-selection risk, especially strict process validity under direct/non-thinking verifier settings. / 我们研究答案正确但过程无效的 trace-selection 风险，尤其是 direct/non-thinking verifier 下的 strict process validity。
- Their early exit stops when the current answer is likely correct. Our adaptive checking triggers a local/global check when process-risk signal appears, including when the final answer may be correct. / 他们是在“答案看起来对”时早停；我们是在“过程有风险”时触发检查，即使答案可能已经正确。

Safe framing / 安全写法：

> Prior work shows hidden states can predict intermediate answer correctness and support early exit. Our work asks a different question: when a trace has the correct final answer but invalid process, do verifier hidden states contain process-validity evidence, where does it appear, when is it ignored by Yes/No readout, and can it trigger low-cost local checking?

中文：

> 既有工作说明 hidden state 可以预测中间答案是否正确，并支持 early exit。我们的不同问题是：当最终答案正确但过程无效时，verifier hidden state 是否包含过程有效性证据，这个证据出现在什么位置，什么时候被 Yes/No 读出忽略，以及能否作为低成本局部检查的触发器。

## 2. What Zhang et al. Actually Do / Zhang 等人的具体方法

Paper / 论文：`Reasoning Models Know When They're Right: Probing Hidden States for Self-Verification`, COLM 2025 / OpenReview.

Method summary / 方法摘要：

- They collect long CoT responses from reasoning models. / 收集 reasoning model 的长 CoT。
- They split traces into paragraphs and identify new reasoning paths using keywords such as `wait`, `double-check`, and `alternatively`. / 用段落和 `wait`、`double-check`、`alternatively` 等关键词切分 reasoning path。
- They use Gemini 2.0 Flash to extract intermediate answers and label each intermediate answer as correct or incorrect against the true answer. / 用 Gemini 2.0 Flash 抽取中间答案并与真值比对打标签。
- Each chunk representation is the last-layer hidden state at the last token position. / 每个 chunk 的表征是最后一层、最后 token hidden state。
- They train a two-layer MLP probe with weighted binary cross-entropy; many useful probes reduce to near-linear probes. / 用加权 BCE 训练两层 MLP probe，很多情况下近似线性 probe 已有非平凡效果。
- Models include DeepSeek-R1-Distill-Llama/Qwen sizes and QwQ-32B. / 模型包括 DeepSeek-R1-Distill 系列和 QwQ-32B。
- Datasets include GSM8K, MATH, AIME, KnowLogic, and GPQA. / 数据包括 GSM8K、MATH、AIME、KnowLogic、GPQA。
- They show hidden states predict intermediate answer correctness, sometimes before the intermediate answer is fully generated. / hidden state 能预测中间答案是否正确，有时在答案完全生成前就能预测。
- For early exit, they sequentially score intermediate answers and stop when the probe confidence exceeds a threshold; on R1-Distill-Llama-8B / MATH, threshold 0.85 reduces tokens by about 24% with roughly unchanged accuracy. / early-exit 时按中间答案顺序打分，超过阈值就截断；在 R1-Distill-Llama-8B / MATH 上，0.85 阈值约节省 24% token 且准确率基本不降。
- They compare reasoning vs non-reasoning models and suggest correctness encoding is stronger in long-CoT reasoning models, possibly because long-CoT supervision exposes models to correct and incorrect intermediate answers with self-correction/backtracking. / 他们比较 reasoning 与 non-reasoning 模型，认为 long-CoT 监督可能增强了自验证表征。

Why this matters to us / 对我们的影响：

- We must cite this paper in any hidden-gated adaptive checking section. / hidden-gated 自适应检查必须引用它。
- We cannot claim novelty for “hidden states know correctness” or “hidden probe can reduce tokens.” / 不能声称 hidden state 预测正确性或 hidden probe 省 token 是我们的首创。
- We can claim novelty for process-validity vs answer-correctness, ACPI trace-selection, repair-aware vs strict policy, residual/MLP/token-mixer localization near error spans, and confidence-matched false-positive audits. / 我们的新意应落在过程有效性而不是答案正确性、ACPI trace-selection、修复口径、错误 span 附近组件定位和置信度匹配假阳性审计。

## 3. Nearby Work / 相邻工作

- Snell et al. 2024, test-time compute scaling: allocates inference compute adaptively by prompt difficulty and verifier/search strategies. This supports adaptive compute but is not process-error-span focused. / 按题目难度和 verifier/search 分配 test-time compute，支持自适应计算方向，但不是过程错误 span。
- Zeng et al. EMNLP 2025, `Thinking Out Loud`: studies verbalized confidence, SFT/RL calibration, and knowledge-boundary erosion in reasoning models. It supports our confidence-entanglement caution. / 研究 verbalized confidence、SFT/RL calibration 和知识边界退化，支持我们对置信度混杂的谨慎。
- Gema et al. 2025, inverse scaling in test-time compute: shows more thinking can hurt on some tasks. This supports our low-cost non-thinking plus selective checking framing. / 说明更多 thinking 有时会伤害性能，支持我们“低成本 non-thinking + 选择性检查”的动机。
- PRM/OmegaPRM/process-supervision papers: focus on step-level supervision/reward and first-error localization for training or reranking. They support the importance of process labels, but generally train external verifiers instead of probing self-verifier hidden states under ACPI trace-selection. / PRM 工作支持过程监督的重要性，但多是外部 verifier/训练奖励，不是 ACPI 下的自身 hidden signal 和读出错配。
- LoRA/QLoRA: supports later small-model organism experiments, especially low-cost SFT/adapter training before RL. / 支持后续先 LoRA/QLoRA 再 RL 的小模型机制来源实验。

## 4. E132 Suspicious-but-Valid Controls / 可疑但正确控制组

Purpose / 目的：test whether the hidden process-risk signal fires on valid traces that merely look suspicious. / 检查 hidden process-risk 是否会在“看起来可疑但实际正确”的 trace 上误触发。

Minimum probe version / 第一版探针：

- Use existing E61 controlled tasks and E119/E146 hard-task rows as seeds. / 用 E61 和 E119/E146 作为种子。
- Add synthetic/curated valid variants:
  - `clean_valid`: direct correct solution.
  - `suspicious_valid_marker`: valid solution with `Wait`, `double-check`, `let me verify`, `this step is easy to confuse`.
  - `suspicious_valid_alternative`: valid solution explores an alternative route and discards it without an error.
  - `low_conf_valid`: valid solution with uncertainty language but correct proof.
  - `unusual_valid`: valid but nonstandard algebraic transformation.
- Add invalid controls:
  - `subtle_invalid`: local wrong step, final answer correct or answer-coherent.
  - `repaired_invalid_strict`: wrong step later repaired; invalid under strict trace-as-proof.
  - `unrepaired_invalid`: retained wrong key step.

Metrics / 指标：

- false trigger rate on suspicious-valid rows. / 可疑但正确的误触发率。
- true trigger recall on invalid rows. / 真实错误召回率。
- trigger distance to visible marker and to manual error span. / 触发点到可疑词和错误 span 的距离。
- marker ablation: remove `wait/check/maybe` words while preserving proof semantics. / 去掉可疑词，检查信号是否仍在。

Important boundary / 边界：If suspicious-valid false triggers are high, the signal is still useful as a check trigger, but not as a process-invalid classifier. / 如果误触发高，它仍可作为检查触发器，但不能称为过程错误分类器。

## 5. E133 Confidence-Matched Process Probe / 置信度匹配过程探针

Purpose / 目的：separate process validity from confidence/difficulty as much as possible. / 尽量把过程有效性从置信度/难度中拆出来。

Feature collection / 特征：

- hidden process score at residual/MLP/token-mixer/norm components.
- Yes-No margin, entropy, top-2 margin.
- trace length, prefix stage, task id, prompt variant.
- visible uncertainty markers count.
- final answer condition: shown/removed/masked/wrong if available.
- repair marker presence.

Analysis / 分析：

- Matched pairs: for each invalid row, match valid rows with similar confidence, length, task, and marker count. / 匹配对。
- Logistic model: `process_valid ~ hidden_score + confidence + entropy + length + marker_count + task + model`. / 控制变量回归。
- Ablation: confidence-only vs hidden-only vs hidden+confidence. / 只用置信度、只用 hidden、二者合并。
- Report both positive and negative outcomes. / 正负结果都报告。

Interpretation rule / 解释规则：

- If hidden remains significant after matching, claim process-specific residual evidence beyond confidence. / 若匹配后仍显著，说明存在超出置信度的过程特异信息。
- If it disappears, claim mixed process-risk/uncertainty signal and use it only as an adaptive checking trigger. / 若消失，则改写成过程风险/不确定性的混合触发信号。

## 6. E134 Trigger-Window Audit / 可疑点窗口审计

Purpose / 目的：understand what the model is doing around hidden-triggered suspicious points. / 看 hidden 触发点附近模型到底在干什么。

Window / 窗口：extract 160-240 characters or one paragraph before/after each trigger point. / 每个触发点前后 160-240 字符或一个段落。

Labels / 标签：

- explicit repair marker / 显式修复标记。
- local recomputation / 局部重算。
- answer anchoring / 围绕已给答案继续自洽。
- hesitation-only / 只是犹豫。
- true local error / 真实局部错误。
- false alarm but valid / 误报但正确。
- ignored risk / 有可疑信号但文本继续推进、不检查。

Expected case studies / 预期个案：

- Gemma31 repaired ACPI: repair marker followed by hidden/readout invalid movement. / Gemma31 已修复 ACPI。
- Gemma26 unrepaired ACPI: hidden signal appears near error but text does not repair, then completion is accepted. / Gemma26 未修复 ACPI。

## 7. E136 Adaptive Checking Policy / 自适应检查策略

Stage 1: post-hoc trigger plus second-pass check / 第一阶段：离线触发 + 二次检查。

- Run normal non-thinking generation or reuse existing NG rows. / 正常 non-thinking 生成或复用已有 NG。
- Replay hidden signals at semantic boundaries: paragraph end, formula line, `Wait`, `Final answer`, and completion. / 在语义边界重放 hidden。
- Trigger if calibrated process-risk score crosses threshold. / 超阈值触发。
- If triggered, issue one extra check prompt:
  - Global check: inspect the whole solution.
  - Localized check: inspect a short hidden-triggered window.
- Compare three policies:
  - `NG-only`: no check.
  - `always-check`: always ask for a second check.
  - `hidden-trigger-check`: check only when hidden risk fires.

Primary metrics / 主要指标：

- strict ACPI retention.
- unrepaired ACPI retention.
- final answer accuracy.
- token cost.
- false trigger and harmful revision rates.
- repair success after trigger.

Stage 2: online semantic-boundary trigger / 第二阶段：在线语义边界触发。

- During generation, inspect hidden states only at sentence/paragraph/formula/final-answer boundaries, not every token. / 只在语义边界检查，避免每 token 成本。
- On trigger, pause and ask the same model to locally verify the recent step before continuing. / 触发时暂停并要求局部复核。
- Use HF for hidden-state access; vLLM can be used only for baseline generation, not hidden monitoring. / 需要 HF 访问 hidden states。

Plain-language hypothesis / 说人话假设：

> Non-thinking may already notice risk internally, but it lacks a confident trigger to check. Hidden-trigger-check gives non-thinking a cheap “检查开关” without forcing full long thinking on every problem.

## 8. E135 LoRA/RL Source Memo / LoRA/RL 来源实验备忘录

Status / 状态：defer execution, keep as mandatory later line. / 暂缓执行，但保留为必须完成的后续线。

Reason / 理由：Qwen3.5/Gemma4 may not expose a clean base/instruct/reasoning checkpoint chain. / Qwen3.5/Gemma4 未必提供完整 base/instruct/reasoning 链路。

Feasible model-organism route / 可行路线：

1. Use a smaller family with available base/instruct/reasoning checkpoints, preferably Qwen/Gemma lineage. / 用有 base/instruct/reasoning 的小模型族。
2. Train LoRA/QLoRA adapters before RL:
   - outcome-only SFT/reward / 只看答案。
   - process-aware SFT/reward / 奖励过程有效。
   - adaptive-check SFT/reward / 可疑时检查、无可疑时直接答。
3. If local hardware is insufficient for RL, rent GPUs and run LoRA-GRPO or similar adapter RL. / 本机不够则租卡做 LoRA-GRPO 等 adapter RL。
4. Evaluate with exactly the same E132-E136 metrics and hidden probes as 30B models. / 用和 30B 相同指标评估。

How to avoid overclaiming / 如何避免过度声称：

- If small-model LoRA reproduces 30B patterns on ACPI, suspicious-valid false positives, confidence-matched probes, and adaptive checking, we can call it a model organism with convergent evidence. / 若小模型复现 30B 模式，称为 model organism 和收敛证据。
- If it does not reproduce, do not use it to explain 30B; use it only as a training-control ablation. / 若不能复现，只作为训练控制，不解释 30B。

## 9. Immediate Implementation Order / 近期实施顺序

1. E132 small probe set first: use current samples plus synthetic suspicious-valid variants. / 先用当前样本做 E132 小探针。
2. E133 confidence-matched analysis on current + E132 rows. / 用当前与 E132 数据做 E133。
3. E134 trigger-window audit for E131/E132/E133 triggered rows. / 对触发行做窗口审计。
4. E136 stage-1 post-hoc adaptive checking. / 做第一阶段离线自适应检查。
5. Expand sample quantity/types after the probe confirms no code/prompt leakage. / 探针无泄露后再扩样本和类型。

## 10. References / 参考

- Zhang et al., `Reasoning Models Know When They're Right: Probing Hidden States for Self-Verification`, COLM 2025 / OpenReview: https://openreview.net/forum?id=O6I0Av7683
- Code: https://github.com/AngelaZZZ-611/reasoning_models_probing
- Snell et al., `Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters`, arXiv 2024: https://arxiv.org/abs/2408.03314
- Zeng et al., `Thinking Out Loud: Do Reasoning Models Know When They're Right?`, EMNLP 2025: https://aclanthology.org/2025.emnlp-main.73/
- Gema et al., `Inverse Scaling in Test-Time Compute`, arXiv 2025 / TMLR: https://arxiv.org/abs/2507.14417
- LoRA: https://arxiv.org/abs/2106.09685
- QLoRA: https://arxiv.org/abs/2305.14314
