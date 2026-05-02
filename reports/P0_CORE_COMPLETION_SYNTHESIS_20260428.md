# P0 Core Completion Synthesis / P0 核心模型补齐综合分析（2026-04-28）

## 1. Plain-language result / 说人话结论

English: On the refreshed P0 core (`qwen35_27b`, `gemma4_31b_it`, `gemma4_26b_a4b_it`), the controlled causal-chain evidence is now much stronger than before: all three models over-accept audited invalid traces under an absolute Yes/No verifier, all three recover the right comparison under a contrastive sibling objective, and all three carry a strong process-validity direction in residual hidden states. The natural no-leak prevalence result remains conservative: simple surface-semantic prompts produced many correct answers but zero audited ACPI events.

中文：在刷新后的 P0 核心模型（`qwen35_27b`、`gemma4_31b_it`、`gemma4_26b_a4b_it`）上，受控因果链证据比之前更强：三个模型在 absolute Yes/No verifier 下都会过度接受人工审定的 invalid trace；换成 contrastive sibling objective 后三个模型都能选对；三个模型的 residual hidden states 中都存在很强的过程有效性方向。自然无泄露发生率仍然保守：简单表层语义 prompt 能产生很多答案正确样本，但没有发现人工审计后的 ACPI。

## 2. What was completed / 本轮补齐了什么

- E42 controlled verifier objective parity was completed for the three P0 core models. / 已补齐三个 P0 核心模型的 E42 受控 verifier objective parity。
- E44 MLP direction steering was completed for the three P0 core models. / 已补齐三个 P0 核心模型的 E44 MLP direction steering。
- E50 residual probe and residual steering was completed for the three P0 core models. / 已补齐三个 P0 核心模型的 E50 residual probe 与 residual steering。
- E48 natural prevalence already existed for the three P0 core models and is summarized here together with E42/E44/E50. / 三个 P0 核心模型的 E48 自然发生率此前已完成，本报告合并总结。
- External candidate downloads are still separate from evidence: Nemotron/GLM/EXAONE must be downloaded, license-checked, and smoke-tested before entering official evidence tables. / 外部候选下载仍与证据分开：Nemotron/GLM/EXAONE 必须先下载、检查许可、通过 smoke test，才能进入官方证据表。

## 3. E48 natural no-leak prevalence / E48 自然无泄露发生率

No gold answer and no known error span were inserted into the prompt. / prompt 中没有插入 gold answer，也没有插入已知错误片段。

| Model / 模型 | Rows / 行数 | Strict final-correct / 严格答案正确 | Audited ACPI / 人审 ACPI | Main meaning / 主要含义 |
|---|---:|---:|---:|---|
| `qwen35_27b` | 96 | 85 | 0 | Simple natural prompts mostly yield valid reasoning when final-correct. / 简单自然题答案对时大多过程也对。 |
| `gemma4_31b_it` | 96 | 88 | 0 | Same pattern, slightly stronger final correctness. / 同样模式，答案正确率稍高。 |
| `gemma4_26b_a4b_it` | 48 | 42 | 0 | Smaller sample, still no natural ACPI. / 样本较小，仍未发现自然 ACPI。 |

Plain-language interpretation / 说人话解释：

- This does not prove ACPI is rare in deployment; it says our current simple no-leak tasks do not naturally elicit it. / 这不能证明部署中 ACPI 很少；只能说明当前简单无泄露任务不容易自然诱发。
- Natural prevalence is bottlenecked by final-correct conditioning: if a model misses the answer, that row is not an ACPI candidate. / 自然发生率受 final-correct 条件限制：答案错的样本不能算 ACPI 候选。
- For a top-tier paper, natural prevalence should be re-estimated on broader, harder, and more realistic trace-selection settings. / 若要达到顶会级，仍需在更广、更难、更真实的 trace-selection 场景中重新估计自然发生率。

## 4. E42 controlled verifier mismatch / E42 受控 verifier 错配

Each model saw matched valid/invalid sibling traces. The invalid trace has the correct final answer but an audited wrong process. / 每个模型看到配对的 valid/invalid sibling trace；invalid trace 的最终答案正确，但过程经审计为错误。

| Model / 模型 | Absolute verifier accepts invalid / absolute 接受 invalid | Absolute accepts valid / absolute 接受 valid | Absolute accuracy / absolute 准确率 | Contrastive accuracy / contrastive 准确率 |
|---|---:|---:|---:|---:|
| `qwen35_27b` | 0.50 | 1.00 | 0.75 | 1.00 |
| `gemma4_31b_it` | 0.50 | 1.00 | 0.75 | 1.00 |
| `gemma4_26b_a4b_it` | 0.50 | 1.00 | 0.75 | 1.00 |

Plain-language interpretation / 说人话解释：

- The same model can fail as an absolute Yes/No verifier but succeed when asked to compare siblings. / 同一个模型做绝对 Yes/No 判断会失败，但做 sibling 对比会成功。
- Therefore the issue is not simply “the model has no process signal”; the objective and threshold decide whether the signal is used. / 因此问题不只是“模型没有过程信号”；objective 和阈值决定了信号是否被用起来。
- This is direct evidence for the chain: surface lexicalization/process semantics create a trap, hidden evidence exists, but the verifier decision can over-accept. / 这直接支持链条：表层词汇/过程语义制造陷阱，隐藏证据存在，但 verifier 决策仍会过度接受。

## 5. E50 residual hidden-state mechanism / E50 residual hidden-state 机制

E50 tests whether process validity is linearly recoverable from verifier residual states and whether adding the learned direction causally changes Yes/No margins. / E50 测试 verifier residual states 中是否可线性恢复过程有效性，以及加上学习到的方向是否会因果改变 Yes/No margin。

| Model / 模型 | Best residual layer / 最佳 residual 层 | Leave-one-task-out accuracy / 留一任务准确率 | Random control mean / 随机控制均值 | Absolute accepts invalid / absolute 接受 invalid | Strongest invalid→valid steering / 最强 invalid→valid steering |
|---|---:|---:|---:|---:|---|
| `qwen35_27b` | 32 | 0.9583 | 0.5417 | 0.50 | layer 56, mean effect +3.51, 6/12 flips / 第56层，均值效应 +3.51，6/12 翻转 |
| `gemma4_31b_it` | 32 | 0.9583 | 0.5365 | 0.50 | layer 48, mean effect +17.49, 5/12 flips / 第48层，均值效应 +17.49，5/12 翻转 |
| `gemma4_26b_a4b_it` | 16 | 0.9583 | 0.4531 | 0.50 | layer 24, mean effect +19.85, 6/12 flips / 第24层，均值效应 +19.85，6/12 翻转 |

Plain-language interpretation / 说人话解释：

- All three P0 models contain a reusable process-validity signal in residual states. / 三个 P0 模型的 residual states 中都有可复用的过程有效性信号。
- The signal is not just correlational: steering it changes verifier margins and flips multiple invalid rows. / 这个信号不只是相关：沿方向干预会改变 verifier margin，并让多个 invalid 样本翻转。
- The signal is model-family transferable at the phenomenon level but not identical in layer location: Gemma4-26B-A4B peaks earlier than Qwen/Gemma4-31B. / 现象层面跨模型可复现，但层位置不同：Gemma4-26B-A4B 的峰值层更早。
- This supports a careful mechanism claim: distributed residual-state process evidence with causal effects, not a fully solved circuit. / 这支持一个谨慎机制主张：存在分布式 residual-state 过程证据并有因果效应，但还不是完整 circuit。

## 6. E44 MLP direction result / E44 MLP 方向结果

| Model / 模型 | Best process-direction effect / 最佳过程方向效应 | Best random control / 最佳随机控制 | Best opposite control / 最佳反向控制 | Flips / 翻转 |
|---|---:|---:|---:|---:|
| `qwen35_27b` | +0.107 | +0.096 | +0.099 | 0 |
| `gemma4_31b_it` | +0.191 | +0.142 | +0.158 | 0 |
| `gemma4_26b_a4b_it` | +0.298 | +0.258 | +0.278 | 0 |

Plain-language interpretation / 说人话解释：

- MLP-only direction steering is weak and not very specific: random/opposite controls are close, and no row flips. / 只看 MLP 方向的 steering 很弱且不够特异：random/opposite control 很接近，也没有样本翻转。
- This is an important negative result: the process signal is not a single clean MLP knob. / 这是重要负结果：过程信号不是一个单一干净的 MLP 开关。
- The stronger causal evidence is currently residual-level, so the mechanism story should not overclaim MLP localization. / 当前更强的因果证据在 residual 层面，因此机制叙事不能过度声称 MLP 定位。

## 7. Current claim status / 当前主张状态

Supported strongly / 强支持：

- Controlled ACPI exists on recent P0 medium models. / 受控 ACPI 在最新 P0 中等模型上存在。
- Absolute Yes/No verifiers over-accept invalid traces even when contrastive sibling comparison succeeds. / 即使 contrastive sibling comparison 能成功，absolute Yes/No verifier 仍会过度接受 invalid trace。
- Residual hidden states contain process-validity evidence and steering this evidence changes decisions. / residual hidden states 中有过程有效性证据，沿该证据方向干预会改变决策。

Still weak or bounded / 仍薄弱或需要边界化：

- Natural ACPI prevalence on simple no-leak tasks remains zero in the current audited samples. / 当前人审样本中，简单无泄露任务的自然 ACPI 发生率仍为 0。
- Hard-task ACPI remains blocked by obtaining strict final-correct traces on P0 models. / 困难题 ACPI 仍受阻于在 P0 模型上获取严格 final-correct trace。
- MLP localization is not convincing enough; residual-level causal evidence is stronger than MLP-level evidence. / MLP 定位还不够有说服力；residual 层因果证据强于 MLP 层证据。
- External P0 candidates are not yet evidence until local deployment passes. / 外部 P0 候选在本地部署通过前不能作为证据。

Best paper framing now / 当前最稳妥论文表述：

> Multilingual and surface-semantic traps can produce answer-correct but process-invalid traces under controlled trace construction. Recent medium open-weight P0 models often over-accept these traces under absolute verifier objectives, while contrastive sibling objectives and residual-state probes expose recoverable process evidence. The causal mechanism is best described as distributed residual-state process evidence with intervention effects; MLP-only localization remains weak. Natural occurrence is not yet established on simple no-leak tasks and must be studied under broader final-correct and hard-task settings.

中文：

> 多语言和表层语义陷阱可以在受控 trace 构造下产生“答案正确但过程无效”的 trace。最新中等开源 P0 模型在 absolute verifier objective 下常过度接受这些 trace，而 contrastive sibling objective 与 residual-state probe 能暴露可恢复的过程证据。当前最稳妥的因果机制表述是：存在分布式 residual-state 过程证据，并且干预该证据会改变决策；MLP-only 定位仍较弱。简单无泄露任务中的自然发生率尚未建立，需要在更广泛的 final-correct 与困难题设置下继续研究。

## 8. Reliability audit notes / 可靠性审计说明

- E48 no-leak prompts report `gold_answer_in_prompt_rows=0` and `known_error_span_in_prompt_rows=0`. / E48 无泄露 prompt 报告 `gold_answer_in_prompt_rows=0` 与 `known_error_span_in_prompt_rows=0`。
- E42/E50 are controlled verifier/mechanism experiments, not natural prevalence estimates. / E42/E50 是受控 verifier/机制实验，不是自然发生率估计。
- Qwen2.5-Math hard-task results are not used as mainline evidence. / Qwen2.5-Math 困难题结果不作为主线证据。
- All P0 E44/E50 jobs completed with `rc=0` in `logs/p0_completion_queue_status_20260428.jsonl`. / 所有 P0 E44/E50 任务在状态日志中均以 `rc=0` 完成。
- The remaining technical risk is external candidate deployment, not the completed core P0 evidence. / 剩余技术风险主要是外部候选部署，不是已完成的核心 P0 证据。

## 9. Next high-value experiments / 下一步高信息收益实验

1. Broader natural task bank: add more non-discount traps such as symbolic notation collision, bilingual unit conversion, probability wording, set inclusion, geometry-language mismatch, and table/chart reasoning. / 更广自然任务库：加入非 discount 陷阱，例如符号碰撞、双语单位换算、概率措辞、集合包含、几何语言错配、表格/图表推理。
2. P0 hard-task final-correct harvesting: separate benchmark-style boxed correctness from strict trace-selection final-line correctness, then audit only final-correct traces. / P0 困难题 final-correct 采样池：分开 benchmark-style boxed correctness 与 strict final-line correctness，再只审计答案正确 trace。
3. Residual localization: split residual effect into attention output, MLP output, and residual stream at the strongest P0 layers. / residual 定位：在最强 P0 层把效应拆成 attention output、MLP output 与 residual stream。
4. Objective intervention: compare absolute Yes/No, contrastive sibling, span-localized error question, and calibrated threshold on the same rows. / objective 干预：在同一批样本上比较 absolute Yes/No、contrastive sibling、span-localized error question 与校准阈值。
5. External P0 replication: after Nemotron/GLM/EXAONE pass smoke tests, rerun E42/E48/E50 first; only then decide whether they join the headline model table. / 外部 P0 复现：Nemotron/GLM/EXAONE 通过 smoke test 后，先跑 E42/E48/E50，再决定是否进入主表。

## 10. Files / 文件

- E42 results: `results/E42_official_template_parity/`
- E44 results: `results/E44_mlp_direction_steering/`
- E48 results: `results/E48_natural_prevalence_official/`
- E50 results: `results/E50_residual_probe_steering/`
- Queue status: `logs/p0_completion_queue_status_20260428.jsonl`
- Download status: `logs/p0_candidate_download_status_20260428.jsonl`
