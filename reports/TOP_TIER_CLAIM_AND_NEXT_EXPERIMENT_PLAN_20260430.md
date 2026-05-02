# Top-Tier Claim and Next Experiment Plan / 顶会级主张与后续实验规划（2026-04-30）

## 1. Current Scientific Claim / 当前科学主张

The safest current claim is:

> Controlled strict ACPI trace-selection risk is robust in direct/non-thinking verifier settings. Natural unrepaired ACPI is low-frequency but real in current NG hard-task samples. Hidden activations contain process-validity evidence, but confidence, objective, threshold, answer anchoring, repair-aware reading, long self-consistency, output/readout format, and stop/commit control determine whether final decisions use it.

中文说法：

> 在 direct/non-thinking verifier 中，受控 strict ACPI trace-selection 风险是稳健的。自然困难题里的 unrepaired ACPI 目前低频但真实存在。hidden activation 中有过程有效性证据，但最终决策是否使用它，取决于置信度、目标函数、阈值、答案锚定、repair-aware 阅读、长自洽后文、输出读出格式，以及 thinking 的 stop/commit 控制。

This claim is intentionally narrower than “models often reason incorrectly”. Our result is about trace selection and verifier/readout mismatch.

这不是泛泛地说“大模型经常推理错”。我们的核心是 trace selection 和 verifier/readout mismatch。

## 2. Evidence Already Landed / 已落盘证据

- E61/E106-E114: controlled ACPI over-accept exists across Qwen/Gemma/GLM direct verifiers; hidden residual process scores are strong.
- E106-E108: process score and confidence are highly aligned, but hidden process score retains incremental information beyond plain readout confidence.
- E114: hidden gate reduces controlled ACPI retention from 0.375-0.458 to 0-0.042 while mostly preserving valid traces.
- E80/E90/E110: repair markers can move residual/MLP/token-mixer/readout state from accept to reject.
- E79/E84: GLM has strong hidden/label-free evidence but weak raw A/B readout, supporting readout bottleneck.
- E83/E57/E88: natural unrepaired ACPI is low-frequency but observed; repaired ACPI is more common under answer-first/no-gold.
- E116-E118: thinking introduces a separate stop/commit bottleneck; process-validity and stop signals are not identical.

## 3. Weak Points for a Top-Tier Paper / 顶会级薄弱点

1. Natural prevalence is still underpowered. / 自然发生率样本仍不够。
2. Thinking verifier (`TV`) has not yet replicated the direct verifier (`DV`) findings. / thinking verifier 还没有系统复现。
3. Hidden mechanism is strong but still partly correlational. / hidden 机制仍偏相关性。
4. Process signal and confidence are entangled. / 过程信号与置信度高度缠绕。
5. Natural tasks are still concentrated in AIME-style math and answer-first prompts. / 自然任务仍偏 AIME 数学和 answer-first。
6. Human audit reliability needs appendix-grade double checking. / 人审可靠性需要更正式。
7. Stop/commit findings are Qwen-only and post-hoc. / stop/commit 目前只是 Qwen 小样本 post-hoc。

## 4. Next Experiments / 后续实验

The initialized manifest is:

- `configs/e121_e130_next_stage_manifest.yaml`

The no-GPU scaffold smoke is:

- `scripts/smoke_e121_e130_scaffold.py`
- `results/E121_E130_scaffold_smoke/e121_e130_scaffold_smoke.json`

### E121 Thinking Verifier Objective Ladder

Purpose: test whether ACPI over-accept survives when the verifier is allowed to think and must produce a final parsed decision.

目的：确认 direct verifier 的风险是不是 thinking verifier 也会发生。

Design: controlled E61/E71/E82 traces; full generated judgment; parse final Yes/No; no first-token logprob.

### E122 Thinking Sibling and Label-Free

Purpose: test whether sibling/label-free still exposes process errors under thinking final decisions, especially GLM.

目的：复查 GLM raw A/B bottleneck 是不是 direct-readout artifact。

Design: A/B, reversed order, First/Second, and label-free two-pass with full final decisions.

### E123 Process vs Confidence vs Stop Disentanglement

Purpose: answer whether “the model noticed an error” is just low confidence.

目的：回答“意识到错误”和“低置信度”是否一回事。

Design: confidence-matched pairs, entropy controls, answer-anchor controls, stop-score controls, permutation null.

### E124 Causal Component Intervention Sweep

Purpose: move from linear probe evidence to stronger causal evidence.

目的：把 hidden probe 从相关性推进到因果证据。

Design: layer/component alpha sweep over residual, MLP, token-mixer/attention output; held-out direction training.

### E125 Natural Hard-Task Prevalence Expansion

Purpose: tighten confidence intervals for natural strict/repaired/unrepaired ACPI.

目的：收窄自然发生率置信区间。

Design: E119 is already running as NG only; future expansion should add AIME24/AMC/code/table/unit tasks.

### E126 Activation-Induced and Activation-Reduced ACPI

Purpose: test whether direct activation changes can increase or reduce ACPI retention.

目的：直接验证 hidden direction 是否能诱发或降低风险。

Design: intervention in verifier replay first; generation-time intervention only after small safe smoke.

### E127 Training-Filter Simulation with Hidden Gate

Purpose: model how outcome-only, absolute, strict, repair-aware, sibling, and hidden-gated filters change retained trace distributions.

目的：把单次 verifier 错误提升到数据筛选机制风险。

### E128 Human Audit Reliability

Purpose: make process-validity labels reviewer-proof.

目的：让人工审计达到 appendix 标准。

Design: double audit, adjudication, strict vs repair-aware guide, second-pass span check.

### E129 Cross-Family Replication

Purpose: show the phenomenon is not limited to Qwen/Gemma/GLM.

目的：证明泛化性或明确边界。

Design: only after smoke confirms backend compatibility; no claims from failed backend runs.

### E130 Trace-as-Proof vs Trace-as-Draft Policy

Purpose: formalize strict ACPI vs repair-aware acceptance.

目的：回答 CoT 应被当证明还是草稿。

Design: strict proof, final surviving proof, and repair-aware draft rubrics.

## 5. Execution Philosophy / 具体设计理念

- Separate modes. Do not mix `DV`, `TV`, `NG`, `TG`, `MI-DV`, `MI-TG`, and `PM`.
- Separate final decision types. Strict final marker, fallback answer, and clean stop must be separate fields.
- Separate prevalence from diagnostics. Natural frequency and controlled mechanism answer different questions.
- Separate process validity from answer correctness. ACPI exists only when final answer is correct and process is invalid.
- Separate process evidence from confidence and stop. E106-E118 show these are related but not identical.
- Never put manual labels, known error spans, gold answers, or trap notes into generation/verifier prompts unless the experiment is explicitly answer-anchor and marked non-prevalence.

## 6. Immediate Status / 当前状态

E119 NG natural hard-task expansion is running in `tmux p02_e119_20260430`. Qwen completed 36/36 rows; Gemma31 is running. No OOM or deadlock signal has been observed.

