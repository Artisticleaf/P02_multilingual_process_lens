# Autonomous Continuation Stage Report / 自动推进阶段报告（2026-04-29）

## 1. Why this report exists / 为什么写这份报告

This report records the current research state after the latest user discussion and turns it into a concrete execution plan. It is meant to guide future agents or future sessions to continue without re-asking for routine approval.

本报告把本轮沟通后的科研判断、主张边界和后续实验路线落盘。后续 agent 或新会话可直接按本报告继续推进，不需要在常规脚本实现、实验运行、结果落盘、审计和分析上反复等待确认。

## 2. Current scientific fact pattern / 当前已经被实验支持的科学事实

### 2.1 Pointwise is not leakage / pointwise 不是信息泄露

Pointwise Yes/No verification means the verifier sees one trace at a time and receives only the problem, the visible trace, and a generic instruction such as “if any mathematical step is wrong, answer No.” It does not receive process labels, `error_span`, `support_span`, manual corrections, or a hint saying which line is wrong.

pointwise Yes/No 的意思是 verifier 一次只看一条 trace，prompt 里只有题目、可见推理过程和通用规则（例如“任一步数学推理错就回答 No”）。它不包含过程标签、`error_span`、`support_span`、人工修正，也不会告诉模型“哪一句错了”。所以 pointwise 不是信息泄露；模型仍必须自己发现错误。

Sibling comparison is also not leakage, but it is a stronger diagnostic objective: the verifier sees two same-problem/same-final-answer traces and must choose which process is invalid. It is easier because the contrast makes the local process difference salient.

sibling comparison 也不是泄露，但它是更强的对比诊断：verifier 看到同题、同最终答案的一好一坏两条 trace，并判断哪条过程无效。它更容易，是因为对比结构把局部过程差异凸显出来。

Span patching, residual steering, MLP/token-mixer decomposition, and similar interventions are different: they are oracle-style mechanistic diagnostics. They can use known labels or spans to test whether hidden states contain process-validity evidence, but they should not be reported as blind verifier accuracy.

span patch、residual steering、MLP/token-mixer 分解等机制实验是另一类 oracle-style 机制诊断。它们可以使用已知标签或 span 来测试 hidden state 中是否存在过程有效性证据，但不能被写成 blind verifier 准确率。

### 2.2 Main empirical pattern / 主要实验模式

Across E42/E54/E60, current core P0 models (`qwen35_27b`, `gemma4_31b_it`, `gemma4_26b_a4b_it`) often over-accept answer-correct/process-invalid traces under pointwise absolute Yes/No verification. Stronger process-check prompts reduce the risk but do not eliminate it. Sibling comparison is much more reliable in the controlled pools.

在 E42/E54/E60 中，当前核心 P0 模型（`qwen35_27b`、`gemma4_31b_it`、`gemma4_26b_a4b_it`）在 pointwise absolute Yes/No verifier 目标下经常过度接受“答案正确但过程无效”的 trace。更强的过程检查 prompt 能显著降低风险，但不能清零。sibling comparison 在受控池中稳定得多。

E60 gives the clearest text-only objective result so far:

- plain Yes/No P0 mean ACPI accept: 0.567;
- careful Yes/No: 0.156;
- answer-blind Yes/No: 0.189;
- locate-then-judge Yes/No: 0.144;
- sibling and careful sibling: 0 accepted ACPI in E42/E54 controlled pools.

E60 目前给出最清楚的文本 verifier objective 证据：普通 Yes/No 的 P0 平均 ACPI 接受为 0.567；仔细检查为 0.156；answer-blind 为 0.189；先定位再判断为 0.144；普通 sibling 与 careful sibling 在 E42/E54 受控池中都达到 0 accepted ACPI。

### 2.3 Mechanistic fact pattern / 机制事实模式

E50/E55/E56 support the statement that hidden states carry process-validity evidence, but the model's absolute Yes/No decision does not always use it well.

E50/E55/E56 支持这样一个事实：hidden state 中确实有“过程是否有效”的证据，但模型的 absolute Yes/No 决策没有稳定、充分地利用这些证据。

Safe wording:

- residual stream contains a stable process-validity direction in controlled P0 settings;
- residual steering can move Yes/No logits and flip some invalid decisions;
- token mixer is important in the path from process evidence to decision;
- MLP participates partially but is not a single clean switch;
- no complete named circuit has been established yet.

安全表述是：residual stream 在 P0 受控设置中包含稳定的过程有效性方向；residual steering 能移动 Yes/No logits 并翻转部分 invalid 决策；token mixer 在过程证据到决策的路径中很重要；MLP 有部分参与，但不是单一干净开关；目前还没有完整命名 circuit。

## 3. Current claim / 当前论文主张

Paper-style English claim:

In final-answer-controlled trace-selection settings, multilingual and surface/process-semantic traps can create answer-correct but process-invalid traces. Current medium-scale open P0 models often over-accept these traces under pointwise absolute Yes/No verification, even though contrastive sibling comparison and residual/token-mixer hidden-state diagnostics expose process-validity signals. The failure is not merely wrong answers, malformed outputs, or a missing instruction to check steps; it reflects a mismatch among surface lexicalization, process semantics, final-answer anchoring, verifier objective, and decision threshold.

中文论文式主张：

在控制最终答案正确的 trace-selection 场景中，多语言与表层/过程语义陷阱可以产生“答案正确但过程无效”的 trace。当前中等规模开源 P0 模型在 pointwise absolute Yes/No verification 下会过度接受这些 trace；但 contrastive sibling comparison 与 residual/token-mixer hidden-state 诊断能够暴露过程有效性信号。这种失败不是简单的答案错、格式坏，或 prompt 忘了要求检查步骤，而是表层词汇化、过程语义、最终答案锚定、verifier objective 与决策阈值之间的错配。

说人话：模型不是完全看不出错。很多时候它内部有证据，也能在一好一坏并排时找出坏过程。但如果只给它一条文字流畅且最终答案正确的 trace，让它回答 Yes/No，它就容易被最终答案和流畅表述“推过阈值”。

## 4. What remains weak for a top-tier paper / 顶刊顶会还薄弱在哪里

1. Generalization is still not broad enough. E54 has 18 families, but the strongest results still look like short controlled word-problem traces. We need language-route × error-taxonomy evidence, including mixed language, transliteration, table, code, proof, geometry, unit, and quantifier errors.

2. Natural prevalence is under-estimated. Controlled ACPI is strong, but small natural simple-task samples found no ACPI, and hard-task unrepaired ACPI is rare in E57. We need larger natural/hard-task harvesting with clear strict/repaired/unrepaired labels.

3. Mechanism is not yet deep enough. Residual evidence is strong, but a top-tier interpretability claim needs layer sweeps, path-specific mediation, token-position/span-local patching, and component-level decomposition that separates residual, attention/token-mixer, and MLP contributions.

4. External model-family replication is pending. Nemotron, GLM, and EXAONE are downloaded but still pending license/backend smoke tests; they cannot yet carry official evidence.

5. Statistical presentation needs strengthening. Most reports use point estimates; the paper appendix should include bootstrap confidence intervals, family leave-one-out, prompt leakage checks, and human-audit resampling.

## 5. Official model cluster and evidence status / 模型簇状态

Core P0 official evidence models:

- `qwen35_27b`: local, tested, official core P0.
- `gemma4_31b_it`: local, tested, official core P0.
- `gemma4_26b_a4b_it`: local, tested, official core P0.

External P0 candidates, not official yet:

- `nemotron_cascade2_30b_a3b_candidate`: locally downloaded, pending license/backend smoke.
- `glm47_flash_candidate`: locally downloaded, pending license/backend smoke.
- `exaone45_33b_candidate`: locally downloaded, pending license/backend smoke.

These candidates must pass isolated tokenizer/chat-template, HF generation, deterministic option-logprob, hidden-state/hook, and license checks before promotion.

## 6. Full experimental roadmap / 后续完整实验路线

### E61 Language-route × error-taxonomy grid / 语言路径 × 错误类型网格

Purpose: show the phenomenon is not a discount/example artifact and not limited to English short math.

目的：证明现象不是 discount 或少数例子的 artifact，也不限于英文短数学题。

Design: 6 language routes × 8 error families, paired valid-correct and invalid-correct traces, scored with plain/careful/answer-blind/locate/sibling objectives. This is the immediate next experiment.

### E62 External P0 candidate smoke / 外部 P0 候选准入测试

Purpose: decide whether Nemotron, GLM, and EXAONE can become official evidence models.

Checks: license, tokenizer/chat template, HF text generation, option-logprob scoring, hidden-state output, hook compatibility, four-GPU memory behavior, and vLLM feasibility if applicable.

### E63 External P0 replication / 外部模型家族复现实验

Purpose: rerun E42/E54/E60 and selected E55/E56 mechanism diagnostics on any candidate promoted by E62.

Goal: show the claim is not only Qwen/Gemma-specific.

### E64 Larger natural and hard-task harvesting / 更大自然与困难题采样

Purpose: estimate spontaneous/natural ACPI and hard-task unrepaired ACPI prevalence.

Design: sample larger P0-generated final-correct traces on AIME-style, olympiad-style, code/table/proof tasks; manually label process as valid, repaired-invalid, or unrepaired-invalid.

### E65 Mechanistic layer sweep / 机制层扫描

Purpose: locate where process-validity evidence becomes linearly available and where it affects decisions.

Design: layer-wise probes and steering over residual, token-mixer outputs, and MLP outputs; report layer curves and leave-family-out robustness.

### E66 Path-specific mediation / 路径特异中介

Purpose: explain how hidden process evidence reaches Yes/No logits and A/B sibling logits.

Design: path patch residual/token-mixer/MLP components into final-logit differences; compare pointwise Yes/No and sibling A/B objectives.

### E67 Span-local mechanism / span 局部机制

Purpose: test whether evidence is localized around error spans/support spans/final-answer tokens or only global.

Design: patch hidden states at error span, support span, and final-answer tokens separately; keep this clearly labeled as oracle diagnostics.

### E68 Filter amplification loop / 筛选器放大模拟

Purpose: model realistic selection pipelines.

Design: simulate outcome-only, absolute, careful-absolute, and sibling filters over balanced and imbalanced trace pools; measure ACPI retention and valid retention.

### E69 Formal/executable checking / 形式化或可执行检查

Purpose: separate tool-checkable errors from semantic verifier failures.

Design: use calculators/code execution/table parsers where possible, and compare LLM verifier, tool verifier, and hybrid verifier.

### E70 Statistics and audit appendix / 统计与审计 appendix

Purpose: make the paper robust.

Design: bootstrap confidence intervals, family leave-one-out, order-balance checks, leakage/source-code audits, model-config checks, and manual-audit resampling.

## 7. Execution policy / 执行策略

Proceed automatically with implementation, P0 queue execution, result landing, leakage/logic audits, bilingual/plain-language reports, and history/KG/handoff updates.

自动推进脚本实现、P0 队列运行、结果落盘、泄露/逻辑审计、双语说人话报告、history/KG/handoff 更新。

Stop only if one of the following occurs:

- destructive file/system action is required;
- model license blocks use;
- a result causes a major reversal of the core claim;
- unexpected workspace corruption or unexplained file changes are observed.

## 8. Immediate action / 立即动作

The next local action is to finish E61: implement the runner, audit script, launch script, analysis report, and then run the three core P0 models. E61 directly targets the current largest top-tier weakness: generalization beyond short controlled English-like examples.

## 9. Update after E61 execution / E61 执行后更新

E61 has now been completed on the three core P0 models and passed audit.

E61 已在三个核心 P0 模型上完成并通过审计。

Artifacts / 产物：

- report: `reports/E61_LANGUAGE_ERROR_GRID_20260429.md`;
- audit JSON: `reports/E61_LANGUAGE_ERROR_GRID_AUDIT_20260429.json`;
- results: `results/E61_language_error_grid/`;
- runner/audit: `scripts/run_e61_language_error_grid.py`, `scripts/audit_e61_language_error_grid.py`.

Concrete result / 具体结果：

- P0 mean plain pointwise ACPI accept is 0.424. / P0 平均普通 pointwise ACPI 接受为 0.424。
- Careful, answer-blind, and locate-then-judge objectives reduce ACPI accept to 0.188, 0.125, and 0.174. / careful、answer-blind、先定位再判断分别把 ACPI 接受降到 0.188、0.125、0.174。
- Sibling and careful-sibling accuracy are 0.990 and 0.986. / 普通 sibling 和 careful sibling 准确率为 0.990 和 0.986。
- The highest-risk language routes are `romanized_zh` and `mixed`. / 最高风险语言路径是 `romanized_zh` 与 `mixed`。
- The highest-risk error families are `percentage_base`, `code_execution`, and `counting_order`. / 最高风险错误类型是 `percentage_base`、`code_execution` 与 `counting_order`。
- Sibling errors occur only for `gemma4_26b_a4b_it` and concentrate on `romanized_zh`, which suggests transliterated-language traces should become a dedicated follow-up axis. / sibling 错误只出现在 `gemma4_26b_a4b_it`，并集中于 `romanized_zh`，说明转写语言 trace 应成为后续单独深挖方向。

Scientific consequence / 科学含义：

E61 strengthens the claim that ACPI verifier risk is not a discount-only or short-English-task artifact. It also updates the boundary: sibling comparison is much more reliable than pointwise Yes/No, but it is not an oracle in broader multilingual/transliterated grids.

E61 加强了“ACPI verifier 风险不是 discount 个例或短英文题 artifact”的主张。同时它更新了边界：sibling comparison 明显比 pointwise Yes/No 可靠，但在更广的多语言/转写网格中并不是 oracle。

Next immediate step / 立即下一步：

Proceed to E62 external P0 candidate smoke tests for Nemotron, GLM, and EXAONE. Only candidates that pass license/backend smoke should be promoted into E63 replication.

进入 E62 外部 P0 候选 smoke test，检查 Nemotron、GLM、EXAONE。只有通过许可与后端 smoke 的候选才能进入 E63 复现。
