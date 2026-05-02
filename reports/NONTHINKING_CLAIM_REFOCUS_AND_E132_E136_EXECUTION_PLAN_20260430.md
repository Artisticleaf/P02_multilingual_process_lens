# Non-Thinking Claim Refocus and E132-E136 Execution Plan / non-thinking 主张重聚焦与 E132-E136 执行计划

- Date / 日期：2026-04-30
- Status / 状态：claim refocus plus executable experiment plan. / 主张重聚焦与可执行实验计划。

## 1. Refocused Claim / 重聚焦主张

Main claim / 主 claim：

> Even without explicit long-CoT thinking, current non-thinking verifier/generator modes contain hidden-state evidence about process invalidity. The key scientific question is not whether long thinking can self-verify, but whether short/non-thinking computation already carries process-risk signals, where those signals appear, when they are confused with confidence or hesitation, and whether they can trigger low-cost checking.

中文：

> 即使没有显式 long-CoT thinking，当前模型的 non-thinking verifier/generator 模式中也存在关于“过程是否无效”的 hidden-state 证据。我们的核心科学问题不是 long thinking 能否自验证，而是短输出/non-thinking 计算内部是否已经有 process-risk 信号、这些信号出现在哪里、什么时候会与低置信度或犹豫混杂，以及能否用它触发低成本检查。

What is now secondary / 降级为工程边界：

- `strict trace-as-proof vs repair-aware trace-as-draft` is not the headline scientific claim. / strict 与 repair-aware 不再作为 headline 科研 claim。
- It remains an evaluation/policy boundary: process supervision, trace selection, and training filters must specify whether visible CoT is treated as proof or draft. / 它仍是评价和工程策略边界：过程监督、trace 选择、训练筛选必须说明把 CoT 当证明还是草稿。

Paper-level novelty / 论文级新意：

- Non-thinking hidden process-risk evidence rather than long-CoT intermediate answer correctness. / non-thinking hidden 过程风险证据，而不是 long-CoT 中间答案正确性。
- ACPI: answer-correct but process-invalid traces. / ACPI：答案正确但过程无效。
- Error-near localization across residual, MLP, token-mixer/attention-related components. / 错误附近 residual、MLP、token-mixer/attention 相关组件定位。
- Confidence/hesitation false-positive controls. / 置信度/犹豫假阳性控制。
- Hidden-triggered adaptive checking that preserves non-thinking for easy/no-risk cases. / hidden 触发自适应检查，对无风险题保持 non-thinking。

## 2. E132 Suspicious-but-Valid Controls / 可疑但正确控制组

Question / 问题：

> Does the hidden process-risk signal fire only for true process errors, or also for valid traces that merely look suspicious?

中文：hidden process-risk 信号只在真实过程错误出现，还是也会在“看起来可疑但其实正确”的 trace 上响？

Implementation / 实现：

- Build a small controlled dataset from E61 seeds plus curated variants. / 从 E61 种子构造小型受控数据。
- Classes:
  - `clean_valid`: clean correct proof. / 干净正确。
  - `suspicious_valid_marker`: correct proof with `Wait`, `double-check`, `verify`. / 含检查词但正确。
  - `suspicious_valid_alternative`: correct proof with a valid alternate route. / 有替代正确路线。
  - `low_conf_valid`: correct proof with uncertainty language. / 低置信但正确。
  - `unusual_valid`: correct but nonstandard expression. / 非标准但正确。
  - `subtle_invalid`: local wrong step, final answer correct. / 隐蔽错步。
  - `repaired_invalid_strict`: wrong step later repaired. / strict 口径错后修复。
  - `unrepaired_invalid`: retained wrong key step. / 未修复错步。

Metrics / 指标：

- false trigger rate on each valid suspicious class. / 各 valid 可疑类误触发率。
- true trigger recall on invalid classes. / invalid 召回率。
- marker ablation sensitivity. / 去掉检查词后的变化。
- model split: Qwen3.5-27B, Gemma4-31B-it, Gemma4-26B-A4B-it. / 三模型横向。

## 3. E133 Confidence-Matched Process Probe / 置信度匹配过程探针

Question / 问题：

> After controlling for readout confidence, entropy, length, task, and visible hesitation markers, does hidden process score still predict process invalidity?

中文：控制读出置信度、entropy、长度、任务和可见犹豫词后，hidden process score 是否仍能预测过程无效？

Implementation / 实现：

- Use E132 rows plus E131 natural rows. / 使用 E132 与 E131 自然行。
- Collect features:
  - hidden residual/component process score.
  - Yes-No margin and binary entropy.
  - input token length.
  - suspicious marker count.
  - task/family/route/prompt class.
  - label: process valid vs invalid.
- Analyses:
  - nearest-neighbor confidence matching. / 最近邻置信度匹配。
  - confidence-binned AUC. / 按置信度分箱 AUC。
  - simple residualized correlation / logistic-style linear score. / 残差化相关/线性评分。

Interpretation / 解释：

- If hidden remains useful after matching: process-specific evidence beyond confidence. / 若匹配后仍有效，说明有超出置信度的过程证据。
- If not: the signal is a mixed process-risk/uncertainty trigger, still useful for adaptive checking but not a pure error detector. / 若无效，它是过程风险与不确定性的混合触发器。

## 4. E134 Trigger-Window Audit / 可疑点窗口审计

Question / 问题：

> When hidden risk fires, what is the model doing in the nearby text?

中文：hidden risk 触发时，模型在附近文本里具体做了什么？

Implementation / 实现：

- Extract windows around triggered prefix points:
  - 160-240 chars before/after for controlled rows.
  - one paragraph before/after for hard-task natural rows.
- Label:
  - true local error.
  - false alarm but valid.
  - hesitation only.
  - local recomputation.
  - explicit repair.
  - answer anchoring.
  - ignored risk.

This is partly human/agent audit. / 这部分需要人工/agent 审计。

## 5. E136 Adaptive Checking Policy / 自适应检查策略

Stage 1: post-hoc trigger plus second-pass check / 第一阶段：离线触发 + 二次检查。

- Baseline rows: E132 controlled rows first; later E119/E146 natural rows. / 先 E132，后 E119/E146。
- Score hidden risk at semantic boundaries. / 在语义边界打 hidden risk。
- Compare:
  - `NG-only`: no check. / 不检查。
  - `always-check`: always ask for a check. / 总是检查。
  - `hidden-trigger-check`: check only if hidden risk fires. / hidden 触发才检查。
- Second-pass prompts:
  - global check: whole trace. / 全局检查。
  - localized check: triggered window only. / 局部检查。
- Metrics:
  - strict ACPI retention.
  - unrepaired ACPI retention.
  - valid harmful revision rate.
  - final-answer accuracy.
  - token cost.
  - repair success.

Stage 2: online semantic-boundary trigger / 第二阶段：在线语义边界触发。

- Generate non-thinking with HF. / HF non-thinking 生成。
- At paragraph/formula/final-answer boundaries, read hidden state. / 在段落/公式/final answer 边界读取 hidden。
- If trigger fires, pause and ask the model to locally check the recent step. / 触发则暂停并局部复核。
- Avoid every-token monitoring unless needed. / 避免每 token 监控。

## 6. Immediate Run Strategy / 近期执行策略

1. Build E132 dataset and dry-run leakage audit. / 构造 E132 数据并做泄露审计。
2. Run Qwen3.5-27B smoke with small rows and no generation. / 先跑 Qwen 小样本 smoke，不新生成。
3. If smoke passes, queue Qwen/Gemma31/Gemma26 sequentially. / 通过后串行跑三模型。
4. Summarize E132/E133/E134 in one report. / 先把 E132-E134 合并报告。
5. Run E136 stage-1 only after E132/E133 thresholds are clear. / 阈值明确后再跑 E136 第一阶段。

## 7. Safety / 安全边界

- No gold answer, manual label, or error span is inserted into verifier/check prompts. / 不把答案、人工标签或错误 span 放入 prompt。
- Synthetic labels are used only offline for evaluation. / 合成标签只离线评估。
- `strict vs repair-aware` remains in appendix/evaluation policy, not as the headline claim. / strict/repair-aware 保留为附录评价口径，不做 headline claim。
