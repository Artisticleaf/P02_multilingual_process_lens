# Stage Report: Current Claim, Boundary, and Next Roadmap / 阶段报告：当前主张、边界与后续路线图（2026-04-29）

## 0. Purpose / 目的

This report records the current state of the project after E60 and turns the latest discussion into an actionable research roadmap. It is meant to guide future work without requiring additional user approval for routine experiment execution, result landing, and analysis.

本报告记录 E60 之后项目的当前状态，并把最近一次讨论沉淀为可执行科研路线图。后续常规实验执行、结果落盘和数据分析可按本路线图持续推进，无需每一步再次等待用户确认。

## 1. Pointwise Is Not Leakage / Pointwise 不是信息泄露

### What pointwise means / pointwise 的含义

In our official E42/E54/E60 setting, `pointwise` means the verifier sees one trace at a time and must judge whether its visible reasoning process is valid.

在当前正式 E42/E54/E60 设置中，`pointwise` 指 verifier 一次只看到一条 trace，并判断这条 trace 的可见推理过程是否有效。

The pointwise prompt contains only:

- the problem / 题目；
- the reasoning trace / 推理过程；
- generic rules such as “if any mathematical step is wrong, answer No” / 通用规则，例如“任一步数学推理错就回答 No”。

It does not contain:

- manual process labels / 人工过程标签；
- `error_span` / 错误片段标注；
- `support_span` / 正确依据片段；
- `manual_correction` / 人工修正；
- the sentence “this line is wrong” / “这一句错了”之类提示；
- error type metadata / 错误类型元数据。

Therefore, pointwise is not information leakage. The model must still find the error by itself.

因此，pointwise 不是信息泄露；模型仍必须自己发现错误。

### What sibling comparison means / sibling comparison 的含义

`sibling comparison` gives the verifier two traces for the same problem and asks which one has an invalid process. It does not reveal which trace is wrong, but it does provide a contrastive structure: one valid and one invalid sibling are placed side by side.

`sibling comparison` 给 verifier 同一道题的两条 trace，并要求判断哪条过程无效。它没有告诉模型哪条错，但提供了更强的对比结构：一好一坏的 sibling 并排出现。

This is not leakage; it is a stronger diagnostic objective. Its role is to show that the process-error signal is available to the model when the objective makes the local difference salient.

这不是泄露，而是更强的诊断目标。它的作用是证明：当 objective 让局部差异变得显著时，模型可以利用过程错误信号。

### What is oracle-style mechanism evidence / 什么是 oracle-style 机制证据

Span patching and residual/MLP/token-mixer interventions are different. They may use human labels, valid-invalid directions, or known spans to test whether hidden states contain process-validity evidence.

span patch 和 residual/MLP/token-mixer 干预是另一类实验。它们可能使用人工标签、valid-invalid 方向或已知 span 来测试 hidden state 是否含有过程有效性证据。

These are mechanism diagnostics, not blind verifier-performance measurements.

这些是机制诊断，不是 blind verifier 行为指标。

## 2. Experiments Completed / 已完成实验总览

### 2.1 Workspace, audit, and backend / 工作区、审计与后端

- Legacy raw prompts, stale handoffs, and contaminated materials were archived. / 旧 raw prompt、旧交接和可能污染材料已归档。
- Active workspace audit was added and passes. / active workspace 审计已加入并通过。
- Evaluation setting appendix was written. / evaluation setting appendix 已完成。
- Backend appendix was written: HF is official for Qwen3.5/Gemma4 P0 mechanism experiments; vLLM is limited to compatible generation-only controls. / 后端 appendix 已完成：Qwen3.5/Gemma4 P0 机制实验以 HF 为官方后端；vLLM 仅用于兼容的 generation-only 控制。
- Qwen2.5-Math hard-task outputs were downgraded to P2 legacy and not adopted for the mainline. / Qwen2.5-Math 困难题输出已降级为 P2 legacy，不进入主线。

Key reports:

- `reports/APPENDIX_EVAL_SETTING_AUDIT_20260428.md`
- `reports/APPENDIX_BACKEND_COMPATIBILITY_AND_THROUGHPUT_20260428.md`
- `reports/QWEN25_MATH_HARD_TASK_NOT_ADOPTED_20260428.md`

### 2.2 Controlled ACPI and verifier objective / 受控 ACPI 与 verifier objective

- E42: controlled same-problem/same-final-answer valid/invalid pairs. Current P0 models all show absolute invalid accept rate 0.50, valid accept rate 1.00, and sibling accuracy 1.00. / E42：同题同最终答案 valid/invalid 受控 pair。当前 P0 三模型 absolute invalid accept 均为 0.50，valid accept 均为 1.00，sibling accuracy 均为 1.00。
- E53: final-answer anchor ablation. Correct final answers pull absolute verifiers toward Yes, but removed/masked final answers still leave nonzero invalid acceptance. / E53：最终答案锚定消融。正确最终答案把 absolute verifier 往 Yes 拉，但 removed/masked 后仍有非零 invalid 接受。
- E54: 18-family parameterized no-leak generalization. Absolute invalid accept remains 0.50-0.667; sibling remains 1.00. / E54：18 类参数化无泄露泛化。absolute invalid accept 仍为 0.50-0.667；sibling 仍为 1.00。
- E58: filter simulation. Outcome-only retains 50% ACPI in balanced controlled pools; absolute reduces but keeps ACPI; sibling suppresses accepted ACPI to 0 in E42/E54. / E58：筛选器模拟。只看答案在均衡受控池中保留 50% ACPI；absolute 会降低但仍保留 ACPI；sibling 在 E42/E54 中将 accepted ACPI 压到 0。
- E60: objective ladder. Careful process prompts reduce ACPI but do not clear it; sibling remains strongest. / E60：objective 梯度。仔细过程检查 prompt 显著降低 ACPI 但不能清零；sibling 仍最强。

Key reports:

- `reports/E53_E57_EXECUTION_SYNTHESIS_20260428.md`
- `reports/E58_DISTILLATION_FILTER_SIMULATION_20260428.md`
- `reports/E60_OBJECTIVE_LADDER_20260429.md`

### 2.3 Hidden-state mechanism / hidden-state 机制

- E40: residual/span patch exposes process/error-span signal. / E40：residual/span patch 暴露过程/错误 span 信号。
- E44: MLP-only steering is weak and nonspecific; no single clean MLP knob. / E44：MLP-only steering 弱且不够特异；没有单一干净 MLP 开关。
- E50: residual probe/steering reaches high leave-one-task-out accuracy in P0; steering changes decisions on some invalid rows. / E50：P0 residual probe/steering 的 leave-one-task-out 准确率高；steering 能改变部分 invalid 行决策。
- E55: residual-to-logit mediation shows residual process-validity directions can move Yes/No logits. / E55：residual-to-logit 中介显示 residual 过程有效性方向能移动 Yes/No logits。
- E56: component decomposition shows distributed evidence in residual stream, token mixer, and MLP; residual is most stable, token mixer is important, MLP participates partially. / E56：组件分解显示 residual stream、token mixer 与 MLP 中都有分布式证据；residual 最稳定，token mixer 重要，MLP 部分参与。

Key reports/results:

- `reports/E40_official_template_span_patch_summary_20260428.md`
- `results/E50_residual_probe_steering/`
- `results/E55_residual_to_logit_mediation/`
- `results/E56_component_decomposition/`

### 2.4 Self-verifier, cross-verifier, and style controls / 自审、互审与风格控制

- E59a: cross-verifier controlled analysis over E42 outputs shows all three P0 verifiers share absolute over-acceptance and recover under sibling comparison. / E59a：在 E42 输出上做跨 verifier 受控分析，显示三个 P0 verifier 都有 absolute 过度接受，且 sibling 恢复。
- E59c: style-controlled rewriting and source-blind mutual verification show self-verifier over-acceptance is not larger than cross-verifier over-acceptance. / E59c：风格受控改写与来源盲互审显示自审 over-accept 不高于互审 over-accept。

Key reports:

- `reports/SELF_VERIFIER_METHOD_RATIONALE_AND_E59_20260428.md`
- `reports/E59C_STYLE_CONTROLLED_MUTUAL_VERIFIER_20260428.md`

### 2.5 Natural and hard-task boundaries / 自然发生率与困难题边界

- E48: simple no-leak natural prompts show many final-correct rows but audited ACPI remains 0 in small samples. / E48：简单无泄露自然 prompt 中 final-correct 很多，但小样本 audited ACPI 为 0。
- E57: P0 hard-task final-correct traces exist; most are process-valid. Strict ACPI is 11/119, but unrepaired ACPI is only 2/119. / E57：P0 困难题能采到 final-correct trace；多数过程有效。strict ACPI 为 11/119，但未修复 ACPI 只有 2/119。

Key reports:

- `reports/E48_E50_OFFICIAL_QUEUE_SYNTHESIS_20260428.md`
- `reports/E57_HARD_TASK_MANUAL_AUDIT_20260428.md`

## 3. Current Claim / 当前主张

### Paper-style claim / 论文式主张

In final-answer-controlled trace-selection settings, multilingual and surface/process-semantic traps can create answer-correct but process-invalid traces. Current medium-scale open P0 models often over-accept these traces under pointwise absolute Yes/No verification, even though contrastive sibling comparison and residual/token-mixer hidden-state diagnostics reveal process-validity signals. The failure is not simply wrong answers, bad formatting, or missing process-check instructions; it reflects a mismatch among surface lexicalization, process semantics, final-answer anchoring, verifier objective, and decision threshold.

在控制最终答案正确的 trace-selection 场景中，多语言/表层词汇化和过程语义陷阱可以产生“答案正确但过程无效”的 trace。当前中等规模开源 P0 模型在 pointwise absolute Yes/No verifier 目标下会系统性过度接受这些 trace；但 sibling comparison 和 residual/token-mixer hidden-state 诊断能暴露过程有效性信号。这不是简单的答案错、格式坏，或 prompt 没要求检查过程，而是表层词汇化、过程语义、最终答案锚定、verifier objective 与决策阈值之间的错配。

### Plain-language claim / 说人话主张

The model is not completely blind to the error. It often has internal evidence that the process is wrong, and it can often pick the bad trace when a valid sibling is shown next to it. But if we show only one fluent trace with a correct final answer and ask for a Yes/No judgment, the model can over-accept it. The final answer acts like an anchor; stronger process-check prompts help but do not fully solve the pointwise objective problem.

模型不是完全看不出错误。它内部经常有“过程不对”的证据；把一条 valid sibling 放在旁边时，它也经常能选出坏 trace。但如果只给它一条文字流畅、最终答案正确的 trace，让它回答 Yes/No，它就可能过度接受。最终答案像锚一样拉高 Yes；更强的过程检查 prompt 有帮助，但不能完全解决 pointwise objective 问题。

### What we should not claim / 不应声称的内容

- Do not claim natural ACPI is frequent across all reasoning tasks. / 不要声称自然 ACPI 在所有推理任务中高频发生。
- Do not claim hard-task unrepaired ACPI is common; current P0 sample has only 2/119 unrepaired ACPI. / 不要声称困难题未修复 ACPI 常见；当前 P0 样本只有 2/119。
- Do not claim a full named mechanistic circuit has been found. / 不要声称已经找到完整命名机制电路。
- Do not claim MLP is a single decisive switch. / 不要声称 MLP 是单一决定性开关。
- Do not claim vendor distillation causes the phenomenon without new evidence. / 没有新证据前不要声称厂商相互蒸馏导致该现象。
- Do not claim pointwise verifier failure means the model only reads the final answer. / 不要声称 pointwise verifier 失败等价于模型只看最终答案。

## 4. P0 Model Status / P0 模型状态

### Core P0 evidence models / 核心 P0 证据模型

These are local, tested, and official evidence models:

- `qwen35_27b`: `/home/Awei/LLM/Model/base/qwen35_27b`
- `gemma4_31b_it`: `/home/Awei/LLM/Model/base/gemma4_31b_it`
- `gemma4_26b_a4b_it`: `/home/Awei/LLM/Model/base/gemma4_26b_a4b_it`

这些模型已本地下载、已跑主线实验，可承载官方证据。

### External P0 candidates / 外部 P0 候选

These are downloaded but not yet official evidence models:

- `nemotron_cascade2_30b_a3b_candidate`: `/home/Awei/LLM/Model/base/nemotron_cascade2_30b_a3b`, status `local_downloaded_pending_smoke`.
- `glm47_flash_candidate`: `/home/Awei/LLM/Model/base/glm47_flash`, status `local_downloaded_pending_smoke`.
- `exaone45_33b_candidate`: `/home/Awei/LLM/Model/base/exaone45_33b`, status `local_downloaded_pending_smoke`.

They must pass license checks and isolated HF/vLLM smoke tests before being promoted into expanded P0 evidence.

它们已下载，但仍需许可检查与隔离 HF/vLLM smoke test；通过前不能进入官方证据。

## 5. Remaining Gaps for Top-Tier Submission / 顶刊顶会仍需补强的缺口

### Gap A: Generalization beyond short math word problems / 超出短数学文字题的泛化性

E54 broadens the task space, but the current strongest evidence is still concentrated in short controlled word-problem traces. We need a systematic language-route × error-taxonomy grid.

E54 已扩展任务空间，但当前最强证据仍集中在短受控文字题 trace。需要系统的语言路径 × 错误类型网格。

### Gap B: Natural prevalence / 自然发生率

Controlled ACPI is strong. Natural ACPI prevalence is still weakly estimated: E48 found 0 in small simple samples; E57 found rare unrepaired hard-task ACPI.

controlled ACPI 很强；自然 ACPI 发生率仍估计不足：E48 小型简单样本为 0，E57 困难题未修复 ACPI 很少。

### Gap C: Mechanistic depth / 机制深度

E55/E56 show hidden-state evidence but not a full circuit. We need layer sweeps, path patching, logit attribution, and span-local activation patching.

E55/E56 显示 hidden-state 证据，但还不是完整 circuit。需要 layer sweep、path patching、logit attribution 和 span-local activation patch。

### Gap D: External family replication / 外部模型家族复现

The current official evidence is Qwen/Gemma. External P0 candidates are downloaded but not admitted. We need smoke tests and then E42/E54/E60/E55/E56 replication.

当前官方证据主要是 Qwen/Gemma。外部 P0 候选已下载但未准入。需要 smoke test，然后复现 E42/E54/E60/E55/E56。

### Gap E: Hard-task scale and clean labeling / 困难题规模与干净标签

E57 is valuable but too small for prevalence claims. We need larger hard-task harvesting with strict/repaired/unrepaired labels and confidence intervals.

E57 有价值，但样本太小，不能支撑发生率 headline。需要更大困难题采样，并报告 strict/repaired/unrepaired 标签与置信区间。

### Gap F: Statistical robustness / 统计稳健性

Current reports are mostly point estimates. We need bootstrap confidence intervals, family-level leave-one-out, and human-audit resampling.

当前报告多为点估计。需要 bootstrap 置信区间、family-level leave-one-out 和人审复抽样。

## 6. Full Experiment Roadmap / 后续完整实验路线图

### E61: Language-Route × Error-Taxonomy Grid / 语言路径 × 错误类型网格

Purpose: prove the phenomenon is not a discount/example artifact and not limited to English short math.

目的：证明现象不是 discount/个例 artifact，也不限于英文短数学题。

Design:

- Cross language routes: en->en, zh->zh, zh->en, en->zh, mixed-script, transliteration.
- Cross error families: unit/scale, percentage-base, quantifier/inequality, ordering/counting, table/data, code trace, proof validity, geometry notation, lexical false friends.
- For each cell: paired valid-correct and invalid-correct traces; optional invalid-wrong control.
- Run objectives: plain pointwise, careful pointwise, answer-blind, locate-then-judge, sibling.

Expected result:

- Absolute pointwise over-accepts across several route/error cells.
- Sibling remains stronger.
- Some cells may show language-specific fragility, which becomes a new finding.

Outputs:

- `configs/e61_language_error_grid.yaml`
- `data/processed/e61_language_error_grid_20260429.jsonl`
- `results/E61_language_error_grid/`
- `reports/E61_LANGUAGE_ERROR_GRID_20260429.md`

### E62: External P0 Candidate Smoke and Promotion / 外部 P0 候选 smoke 与准入

Purpose: determine whether Nemotron, GLM, and EXAONE can enter expanded P0 evidence.

目的：判断 Nemotron、GLM、EXAONE 是否能进入扩展 P0 证据簇。

Design:

- License check.
- Tokenizer/chat-template check.
- HF text-only generation smoke.
- Yes/No logprob scoring smoke.
- hidden-state/hook availability smoke.
- vLLM compatibility smoke if feasible.

Expected result:

- Promote compatible models to expanded P0.
- Keep incompatible models as candidate-only with documented reasons.

Outputs:

- `reports/E62_EXTERNAL_P0_SMOKE_20260429.md`
- updated `configs/model_registry.yaml`

### E63: External P0 Replication / 外部 P0 复现

Purpose: test whether the main phenomenon holds beyond Qwen/Gemma.

目的：测试主现象是否超出 Qwen/Gemma。

Design:

- On promoted external P0 models, rerun E42/E54/E60 first.
- If hidden states are supported, rerun E55/E56.
- If generation is stable, run E57-style hard-task sampling.

Expected result:

- Either cross-family replication strengthens the paper, or family-specific differences become a notable finding.

Outputs:

- `results/E63_external_p0_replication/`
- `reports/E63_EXTERNAL_P0_REPLICATION_20260429.md`

### E64: Larger Natural and Hard-Task Harvesting / 更大自然与困难题采样

Purpose: estimate natural ACPI prevalence under realistic generation, not controlled construction.

目的：估计真实生成中的自然 ACPI，而不是仅靠受控构造。

Design:

- More AIME24/25-style tasks.
- MATH/Olympiad-style tasks if available locally.
- Code/table/proof reasoning tasks.
- No gold answer, no trap note.
- Record benchmark correctness, strict final-line correctness, strict process validity, repaired validity, unrepaired ACPI.
- Human/manual audit plus second-sample audit.

Expected result:

- Either identify natural ACPI pockets, or establish that unrepaired natural ACPI is rare under strong P0 models while controlled verifier risk remains severe.

Outputs:

- `results/E64_natural_hard_task_harvesting/`
- `reports/E64_NATURAL_HARD_TASK_HARVESTING_20260429.md`

### E65: Mechanistic Layer Sweep / 机制 layer sweep

Purpose: move from single best-layer residual directions to layer-wise evidence.

目的：从单个最佳层推进到逐层机制证据。

Design:

- For each P0 model and E42/E54/E61 pools, compute probe accuracy and patch effect across layers.
- Components: residual stream, token mixer output, MLP output.
- Report valid/invalid effects separately.

Expected result:

- Identify middle/late layer bands where process-validity evidence is strongest.
- Compare Qwen vs Gemma vs external P0 patterns.

Outputs:

- `results/E65_mechanistic_layer_sweep/`
- `reports/E65_MECHANISTIC_LAYER_SWEEP_20260429.md`

### E66: Path-Specific Mediation / 路径特异中介

Purpose: explain how residual/token-mixer/MLP evidence reaches Yes/No and A/B logits.

目的：解释 residual/token-mixer/MLP 证据如何影响 Yes/No 与 A/B logits。

Design:

- Path patch residual -> token mixer -> MLP -> output logits.
- Compare absolute Yes/No and sibling A/B prompts.
- Measure causal contribution to logits and flips.

Expected result:

- Show whether sibling uses the same validity signal more effectively, or uses a different route.

Outputs:

- `results/E66_path_specific_mediation/`
- `reports/E66_PATH_SPECIFIC_MEDIATION_20260429.md`

### E67: Span-Local Mechanism / span-local 机制

Purpose: connect surface error spans to hidden process-validity directions.

目的：把表层错误 span 与 hidden process-validity direction 连接起来。

Design:

- Patch activations at error-span tokens, support-span tokens, and final-answer tokens.
- Compare effects on absolute Yes/No and sibling logits.
- Use known spans only as mechanism diagnostics, not blind verifier tests.

Expected result:

- Establish whether error-span positions carry stronger causal evidence than final-answer positions.

Outputs:

- `results/E67_span_local_mechanism/`
- `reports/E67_SPAN_LOCAL_MECHANISM_20260429.md`

### E68: Filter Amplification Loop / 筛选放大实验

Purpose: demonstrate how outcome-only or absolute filters can retain/amplify ACPI in synthetic-data or best-of-N pipelines.

目的：展示只看答案或 absolute filter 如何在合成数据/best-of-N 管线中保留或放大 ACPI。

Design:

- Use controlled and model-generated trace pools.
- Compare outcome-only, plain absolute, careful absolute, sibling, and residual-assisted diagnostic filters.
- Track accepted trace count, valid retention, ACPI retention, and accepted ACPI rate.

Expected result:

- Outcome-only and plain absolute retain more ACPI; sibling suppresses it; careful absolute helps but is not perfect.

Outputs:

- `results/E68_filter_amplification_loop/`
- `reports/E68_FILTER_AMPLIFICATION_LOOP_20260429.md`

### E69: Formal/Executable Trace Checking / 形式化或可执行 trace 检查

Purpose: separate cases where errors can be verified by an external tool from purely semantic cases.

目的：区分可由外部工具验证的错误与纯语义错误。

Design:

- For arithmetic/code/table tasks, create executable checks.
- Compare LLM verifier vs tool verifier vs hybrid verifier.
- Keep semantic traps that cannot be fully formalized as separate category.

Expected result:

- Show which ACPI risks are avoidable by tools and which remain semantic/verifier-objective failures.

Outputs:

- `results/E69_formal_executable_checking/`
- `reports/E69_FORMAL_EXECUTABLE_CHECKING_20260429.md`

### E70: Statistical and Human-Audit Appendix / 统计与人工审计 appendix

Purpose: make the paper robust to reviewer concerns.

目的：增强论文面对审稿质疑时的稳健性。

Design:

- Bootstrap confidence intervals for key rates.
- Family-level leave-one-out statistics.
- Human audit protocol and resampling.
- Leakage and prompt-insertion checks for all official experiments.

Expected result:

- A single appendix that supports all main tables.

Outputs:

- `reports/E70_STATISTICS_AND_AUDIT_APPENDIX_20260429.md`

## 7. Execution Policy / 执行策略

Unless blocked by environment, license, or logic-risk issues, proceed automatically with:

1. implement scripts/configs;
2. run P0 queues;
3. land raw and summarized results;
4. run leakage/logic audits;
5. write bilingual/plain-language reports;
6. update history/KG and handoff.

除非遇到环境、许可或逻辑风险阻塞，后续可自动推进：实现脚本/配置、运行 P0 队列、落盘结果、执行泄露/逻辑审计、撰写双语说人话报告、更新 history/KG 与 handoff。

Stop and ask only if:

- a destructive action is needed;
- a license prohibits local use;
- a result implies a major claim reversal requiring user-level framing;
- an unexpected file change suggests workspace corruption.

只有在需要破坏性操作、许可禁止本地使用、结果导致主 claim 重大反转、或发现意外文件变更暗示工作区异常时，才停止询问。

## 8. Immediate Next Step / 立即下一步

Start E61. It gives the highest information gain because it addresses the largest current top-tier weakness: generalization across language routes and error taxonomies.

立即启动 E61。它的信息收益最高，因为它直接补当前顶刊顶会最明显短板：跨语言路径与错误类型的泛化性。

## 9. E61 Completion Update / E61 完成更新

E61 has been completed and audited after this roadmap was written. See `reports/E61_LANGUAGE_ERROR_GRID_20260429.md` and `reports/E61_LANGUAGE_ERROR_GRID_AUDIT_20260429.json`.

E61 已在本路线图写成后完成并通过审计。详见上述报告和审计 JSON。

Key update / 关键更新：P0 plain pointwise ACPI accept is 0.424; careful/answer-blind/locate reduce it to 0.188/0.125/0.174; sibling/careful-sibling accuracy is 0.990/0.986. This strengthens cross-language/error-family generalization while clarifying that sibling comparison is robust but not an oracle.

关键更新：P0 普通 pointwise ACPI 接受为 0.424；careful/answer-blind/locate 降到 0.188/0.125/0.174；普通 sibling/仔细 sibling 准确率为 0.990/0.986。这加强了跨语言路径/错误类型泛化，同时澄清 sibling comparison 很稳但不是 oracle。
