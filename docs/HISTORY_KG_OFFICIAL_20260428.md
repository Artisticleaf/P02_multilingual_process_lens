# P02 Multilingual Process Lens Official History/KG / 官方压缩历史与知识图谱

> 2026-04-30 stage synthesis / 阶段性整理入口：`docs/HANDOFF_HISTORY_STAGE_SYNTHESIS_20260430.md`。Use that file for the current human-readable claim, glossary, experiment summary, literature positioning, and next-experiment plan; keep this file as the chronological knowledge graph. / 当前主张、术语人话表、实验总结、文献定位和后续实验计划请先看该文件；本文保留为时间顺序知识图谱。

Last updated / 最近更新：2026-05-02  
Workspace / 工作目录：`/home/Awei/P02_multilingual_process_lens`

本文件是压缩后的项目主记录。只保留能支撑论文主张的事件、文件地址、实验设置、实验结论和解释边界；下载流水、旧交接文本和不进入主证据的候选状态不再展开。

## 1. Current Claim / 当前主张

**可安全使用的主张：**

在 `DV`（direct-answer verifier，关闭 thinking 的直接判定 verifier）接口下，多语言/表层语义陷阱会产生 `answer-correct but process-invalid`（答案正确但过程无效，简称 ACPI）的 strict trace-selection 风险。P0 模型的 pointwise `Yes/No` verifier 会过度接受一部分 ACPI trace；更强 pointwise prompt 能降低风险但不能完全消除；contrastive sibling、label-free two-pass 和 hidden residual/MLP/token-mixer 诊断能暴露更多过程有效性信号。

自然困难题里的 unrepaired ACPI（未修复 ACPI）在当前 `NG`（non-thinking generation，关闭 thinking 的自然生成）样本中低频但真实存在。当前还不能把它写成 thinking-mode reasoning 的自然发生率结论。

**必须保留的边界：**

- 不声称自然 unrepaired ACPI 高频发生。
- 不声称 sibling comparison 是无条件 oracle；GLM 已经显示 raw A/B sibling 会被输出标签/读出方式拖累。
- 不声称 hidden probe 已经证明完整 circuit；当前机制证据主要是 `MI-DV`（direct-verifier prompt 下的机制诊断）。
- 不把 E57/E88 的 hard-task 发生率当作 thinking-mode 发生率；它们现在归类为 `NG`。
- 不把首 token `Yes/No` 或 `A/B` logprob 当作 thinking verifier 决策；E91 已确认 thinking 模式会先进入思考区。

## 2. Mode Taxonomy / 模式分类

| code | 中文解释 | 当前用途 |
|---|---|---|
| `DV` | 关闭 thinking，让模型直接给 `Yes/No`、`A/B` 或固定选项。 | 已有 verifier/objective 主结果属于这里。 |
| `TV` | 开启 thinking，让模型先思考，再解析最终判定。 | 尚需 E94/E95/E96 重测。 |
| `NG` | 关闭 thinking 的自然解题生成。 | E48/E57/E88 等自然发生率结果主要属于这里。 |
| `TG` | 开启 thinking 的自然解题生成。 | 尚需 E92/E93 补齐。 |
| `MI-DV` | 在 direct-verifier prompt 下读 residual/MLP/token-mixer 或做 steering。 | 当前机制证据主要属于这里。 |
| `PM` | 后处理统计或筛选器模拟。 | 必须继承源实验模式，不能混合 `NG`/`TG` 后直接报一个总数。 |

## 3. Model Cluster / 模型簇

主证据模型来自 `configs/model_registry.yaml`。

**Core P0 / 核心 P0：**

- `qwen35_27b`: `/home/Awei/LLM/Model/base/qwen35_27b`
- `gemma4_31b_it`: `/home/Awei/LLM/Model/base/gemma4_31b_it`
- `gemma4_26b_a4b_it`: `/home/Awei/LLM/Model/base/gemma4_26b_a4b_it`

**Expanded P0 boundary evidence / 扩展 P0 边界证据：**

- `glm47_flash_candidate`: `/home/Awei/LLM/Model/base/glm47_flash`

GLM 可作为扩展 P0 边界证据：它复现 pointwise 过度接受和 hidden process signal，但 raw A/B sibling 明显受读出/标签影响。核心 P0 headline 与扩展 P0 结果需要分开报告。

## 4. Evaluation Settings / 关键评估设置

**Direct verifier (`DV`) 设置：**

- 使用官方 chat template。
- 对支持 thinking 的 chat 模型显式 `enable_thinking=False`。
- pointwise verifier 以首 token 或固定选项 logprob 计算 `Yes` vs `No`。
- sibling verifier 以 `A/B`、`1/2`、`First/Second`、full-option `Trace 1/Trace 2` 或 label-free two-pass 测量。
- 这些设置能稳定测 direct-answer verifier 的 objective/threshold/readout 风险，但不是 thinking verifier。

**Thinking rerun (`TV`/`TG`) 设置，来自 E91 本地模型卡审计：**

- Qwen3.5 thinking：`temperature=1.0, top_p=0.95, top_k=20, presence_penalty=1.5, repetition_penalty=1.0`。
- Gemma4 thinking：`temperature=1.0, top_p=0.95, top_k=64`。
- GLM-4.7-Flash 默认评测：`temperature=1.0, top-p=0.95`；reasoning parser 为 `glm45`。
- `TV` 必须生成完整 thinking 输出并解析最后明确的 final decision，不能使用首 token `Yes/No`/`A/B` logprob。

**Context / 上下文设置边界：**

- Qwen3.5 本地模型卡写明默认上下文 262,144 tokens，并建议复杂 thinking 任务至少保留 128K。
- Gemma4 中型模型本地模型卡写明 256K context。
- 当前 hard-task trace 远小于这些模型标称上下文，因此“长上下文”更准确指长推理文本里的局部错误稀释、答案自洽和读出难度，而不是超过模型官方上下文上限。

## 5. Important Artifacts / 关键文件索引

**总览与审计：**

- `reports/THINKING_MODE_AUDIT_AND_RERUN_PLAN_20260429.md`
- `reports/E91_THINKING_MODE_CONFIG_AUDIT_20260429.md`
- `reports/NEXT_EXPERIMENT_ROADMAP_20260429.json`
- `logs/audit_active_official_workspace_20260428.json`

**核心综合报告：**

- `reports/P0_CORE_COMPLETION_SYNTHESIS_20260428.md`
- `reports/E62_E70_AUTONOMOUS_SYNTHESIS_20260429.md`
- `reports/E71_E79_REPAIR_HIDDEN_LABELFREE_AUDIT_20260429.md`
- `reports/E80_E84_PREFIX_LABELFREE_PREVALENCE_MEDIATION_20260429.md`
- `reports/E85_E90_FINAL_SYNTHESIS_20260429.md`

**关键数据/配置：**

- `data/processed/e61_language_error_grid_20260429.jsonl`
- `configs/e61_language_error_grid_pairs.yaml`
- `configs/e26_aime_hard_tasks.yaml`
- `data/processed/e57_final_correct_manual_audit_20260428.jsonl`
- `data/processed/e88_answer_first_manual_audit_20260429.jsonl`

## 6. Experiment Record / 实验记录

### 6.1 Controlled Direct-Verifier Risk / 受控 direct-verifier 风险

**E42 official template parity / 官方模板对齐**

- Files / 文件：`results/E42_official_template_parity/`
- Mode / 模式：`DV`
- Result / 结果：三个 core P0 的 absolute invalid accept rate 均为 0.50，valid accept rate 均为 1.00，contrastive accuracy 均为 1.00。
- Interpretation / 解释：最终答案正确但过程无效的 trace 会在 direct `Yes/No` 下被过度接受；同一对 sibling trace 放在一起比较时，过程错误更容易暴露。

**E53 answer-anchor ablation / 答案锚定消融**

- Files / 文件：`results/E53_answer_anchor_ablation/`, `reports/E53_E57_EXECUTION_SYNTHESIS_20260428.md`
- Mode / 模式：`DV`
- Result / 结果：可见正确 final answer 会提高 invalid 接受；错误 final answer 会降低接受；移除/遮蔽 final answer 后仍有非零 invalid 接受。
- Interpretation / 解释：final answer 是强锚点，但不是全部原因；局部过程语义和后续答案自洽也会影响 verifier。

**E54 parameterized no-leak generalization / 参数化无泄露泛化**

- Files / 文件：`data/processed/e54_parameterized_no_leak_generalization_20260428.jsonl`, `results/E54_parameterized_no_leak_generalization/`
- Mode / 模式：`DV`
- Result / 结果：mean/median、unit scale、percentage base、inequality、counting/order、code boundary、table、proof-validity 等 18 类任务复现过度接受；P0 sibling 在 E42/E54 中把 accepted ACPI 压到 0。
- Interpretation / 解释：风险不是 discount 个例，也不是单一英文短题 artifact。

**E60 objective ladder / verifier 目标梯度**

- Files / 文件：`reports/E60_OBJECTIVE_LADDER_20260429.md`, `results/E60_objective_ladder/`
- Mode / 模式：`DV`
- Result / 结果：P0 mean ACPI accept：plain `Yes/No` 0.567，careful 0.156，answer-blind 0.189，locate-then-judge 0.144；sibling 和 careful sibling 在 E42/E54 中为 1.000。
- Interpretation / 解释：要求模型“仔细检查”会明显降低风险，但仍不能保证拒绝所有答案正确但过程无效的 trace；contrastive objective 在 core P0 上更强。

### 6.2 Broad Multilingual/Error Taxonomy / 多语言与错误类型泛化

**E61 language-route × error-taxonomy grid / 语言路径 × 错误类型网格**

- Files / 文件：`reports/E61_LANGUAGE_ERROR_GRID_20260429.md`, `data/processed/e61_language_error_grid_20260429.jsonl`, `results/E61_language_error_grid/`
- Mode / 模式：`DV`
- Design / 设计：6 条语言路径 × 8 类错误，每个 cell 含 valid-correct 与 invalid-correct trace；prompt 不含 manual label、error span、support span 或 correction。
- Result / 结果：P0 mean plain pointwise ACPI accept 0.424；careful/answer-blind/locate 为 0.188/0.125/0.174；sibling/careful-sibling accuracy 为 0.990/0.986。
- Fragile areas / 脆弱点：`romanized_zh` 和 `mixed` 路径最高；`percentage_base`、`code_execution`、`counting_order` 错误族最高。
- Interpretation / 解释：表层词汇化、语言混合和过程语义错配是共性风险；sibling 很强但不是绝对 oracle。

### 6.3 Hidden/Mechanism Evidence Under Direct-Verifier Prompts / direct-verifier 下的机制证据

**E50/E55/E56 residual-to-logit and component decomposition / residual 到 logit 与组件分解**

- Files / 文件：`results/E50_residual_probe_steering/`, `results/E55_residual_to_logit_mediation/`, `results/E56_component_decomposition/`
- Mode / 模式：`MI-DV`
- Result / 结果：residual direction 能读出过程有效性并改变 verifier logits；token-mixer/attention-related 输出也重要；MLP 参与但不是单一干净开关。
- Interpretation / 解释：模型内部存在过程有效性证据，但 direct `Yes/No` 输出不总能使用这些证据。

**E65/E78 hidden probe audit / hidden probe 假阳性与稳健性审计**

- Files / 文件：`reports/E65_MECHANISTIC_LAYER_SWEEP_20260429.md`, `reports/E71_E79_REPAIR_HIDDEN_LABELFREE_AUDIT_20260429.md`, `results/E65_mechanistic_layer_sweep/`, `results/E78_hidden_probe_false_positive_audit/`
- Mode / 模式：`MI-DV`
- Result / 结果：E61 best-layer residual probes 在 core/expanded P0 上很强：Qwen 1.000，Gemma31 1.000，Gemma26 约 0.917--0.927，GLM 约 0.958--0.979；置换标签 null 接近 chance。
- Boundary / 边界：Gemma26 有 valid false rejection，所以 hidden probe 不是“只在 invalid trace 出现”的完美警报；更准确说是强但不完美的过程有效性方向。

**E90 component activation cache / 组件激活缓存**

- Files / 文件：`reports/E90_COMPONENT_ACTIVATION_CACHE_20260429.md`, `results/E90_hardtask_component_activation_cache/`
- Mode / 模式：`MI-DV`
- Result / 结果：Gemma31 repaired ACPI 从早期错误答案前缀被接受转为 repair/completion 前缀被拒绝；best-layer residual、MLP/post-feedforward、token-mixer/attention-related component scores 随 Yes/No 决策一起移动。Gemma26 unrepaired ACPI 在 completion 仍被接受，即使 residual/post-feedforward 分数弱或偏负。
- Interpretation / 解释：这支持“内部过程证据存在，但读出/目标/repair-aware 阅读决定是否使用”的机制链；还不是 thinking generation 的完整修复回路。

### 6.4 Repair-Aware Reading and Hard-Task Cases / 修复感知阅读与困难题个案

**E57/E83/E88 natural hard-task prevalence / 自然困难题发生率**

- Files / 文件：`reports/E57_HARD_TASK_MANUAL_AUDIT_20260428.md`, `reports/E80_E84_PREFIX_LABELFREE_PREVALENCE_MEDIATION_20260429.md`, `reports/E88_ANSWER_FIRST_MANUAL_AUDIT_20260429.md`
- Mode / 模式：主要是 `NG`
- E83 pooled result / 汇总结果：288 generated，127 final-correct audited，11 strict ACPI，9 repaired ACPI，2 unrepaired ACPI；unrepaired per generated = 2/288 = 0.0069，Wilson CI [0.0019, 0.0250]。
- E88 answer-first result / answer-first 结果：192 generated，63 final-correct，23 strict ACPI，22 repaired ACPI，1 unrepaired ACPI。
- Interpretation / 解释：自然 unrepaired ACPI 低频但真实存在；strict ACPI 大多是先写错、后面明确修复的 trace。这个结论目前只适用于 non-thinking generation，不适用于 thinking headline。

**E71 strict vs repair-aware objective / 严格口径与修复口径**

- Files / 文件：`results/E71_repair_objective/`, `reports/E71_E79_REPAIR_HIDDEN_LABELFREE_AUDIT_20260429.md`
- Mode / 模式：`DV`
- Result / 结果：core P0 在 strict_process 下拒绝多数受控 invalid trace，但仍接受 Gemma26 两条 unrepaired hard-task ACPI；切换到 repair-aware 或 final-surviving-proof objective 会明显提高 repaired trace 接受。
- Interpretation / 解释：strict trace-selection 和 repair-aware reading 是不同科学对象。严格口径下可见错步即 invalid；修复口径下，如果错步被明确废弃且最终保留证明有效，可以接受。

**E80 progressive-prefix replay / 渐进前缀回放**

- Files / 文件：`results/E80_progressive_prefix_replay/`, `reports/E80_E84_PREFIX_LABELFREE_PREVALENCE_MEDIATION_20260429.md`
- Mode / 模式：`DV`/`MI-DV`
- Gemma31 repaired ACPI / Gemma31 修复型 ACPI：`error_span_end` accept 0.889，`first_final_answer_end` accept 1.000；出现 repair marker 后 `post_repair_240chars` accept 0.000，`completion_end` accept 0.111。
- Gemma26 unrepaired ACPI / Gemma26 未修复 ACPI：错误因式分解前缀和 completion 都保持 accept 1.0。
- Interpretation / 解释：显式 repair marker 会改变 strict verifier 读法；未修复且局部隐蔽的代数错误会形成更强的 hidden-evidence-to-decision mismatch。

**E82 unrepaired case ablation / 未修复个案消融**

- Files / 文件：`results/E82_unrepaired_case_ablation/`
- Mode / 模式：`DV`
- Result / 结果：把两条 Gemma26 unrepaired ACPI 的 final answer 改错后，所有 verifier 拒绝；移除/遮蔽 final answer 后，Qwen/Gemma 仍大多接受。
- Interpretation / 解释：final answer anchoring 很强，但不是全部；错误因式分解局部隐蔽，后续推导又保持答案自洽。

**E86 algebra-equivalence adversarial / 代数等价负控制**

- Files / 文件：`results/E86_algebra_equivalence_adversarial/`
- Mode / 模式：`DV`
- Result / 结果：四个 P0 在 short explicit invalid algebra trace 上 strict pointwise invalid accept = 0，但 valid terse trace 被大量误拒。
- Interpretation / 解释：不能声称 absolute verifier 普遍漏代数错误；困难题漏检更像由长推理文本、局部隐蔽、答案自洽、final-answer anchoring 和读出错配共同造成。

### 6.5 Sibling, Label-Free Readout, and GLM / sibling、无标签读出与 GLM

**E79/E81 label-free sibling / 无标签 sibling**

- Files / 文件：`results/E79_glm_label_free_sibling/`, `results/E81_label_free_sibling_allp0/`, `results/E81_label_free_sibling_fulloption_check/`
- Mode / 模式：`DV`
- Result / 结果：core P0 在 AB、1/2、First/Second、full-option Trace1/Trace2、label-free scoring 下都强；Gemma26 稍弱但仍高。GLM raw labels 弱，但 label-free two-pass 接近完美。
- Correction / 修正：first-token `Trace1/Trace2` 是 scoring artifact，因为两个选项共享首 token；full-option 后核心 P0 1.000/1.000/0.979，GLM 0.781。
- Interpretation / 解释：GLM 不是 process-blind；它的主要问题是 raw output-label/readout bottleneck。

**E84/E87 GLM readout mediation/intervention / GLM 读出中介与干预**

- Files / 文件：`results/E84_glm_readout_mediation/`, `reports/E87_GLM_READOUT_INTERVENTION_20260429.md`, `results/E87_glm_readout_intervention/`
- Mode / 模式：`MI-DV`/`PM`
- E84 result / E84 结果：GLM hidden margin 与 label-free No-minus-Yes margin 高相关，Pearson 0.883，Spearman 0.845；二者与 raw A/B margin 相关弱。
- E87 result / E87 结果：raw A/B single-order accuracy 0.542；global bias centering 0.667；two-order antisymmetric 0.812；hidden readout 1.000；label-free two-pass 0.958。
- Interpretation / 解释：GLM 内部和 label-free pointwise 读出能看到过程信号，但 raw A/B 标签会扭曲输出。这个结论目前是 direct-interface/readout 结论，需要 E95 在 thinking final-decision 下复查。

### 6.6 Filter Simulation / 筛选器模拟

**E58/E68/E89 filter simulations / 筛选器仿真**

- Files / 文件：`reports/E58_DISTILLATION_FILTER_SIMULATION_20260428.md`, `reports/E68_FILTER_AMPLIFICATION_EXPANDED_20260429.md`, `reports/E89_REPAIR_POLICY_FILTER_SIMULATION_20260429.md`
- Mode / 模式：`PM`
- Result / 结果：outcome-only 会保留所有 final-correct ACPI；plain pointwise 保留大量 strict ACPI；更强 pointwise 降低风险；core P0 sibling 强，但 GLM 会拉高 expanded-P0 sibling 残留。E89 纳入 E88 后，strict policy 拒绝 repaired/unrepaired ACPI，repair-aware policy 接受 repaired 但拒绝 unrepaired。
- Interpretation / 解释：数据筛选策略必须明确 strict vs repair-aware policy；只看最终答案会系统性放大 ACPI trace-selection 风险。

### 6.7 Thinking-Mode Audit / thinking 模式审计

**E91 config/parser audit / 配置与 parser 审计**

- Files / 文件：`reports/E91_THINKING_MODE_CONFIG_AUDIT_20260429.md`, `results/E91_thinking_mode_config_audit/e91_thinking_mode_config_audit.json`
- Mode / 模式：技术审计，不是行为实验。
- Result / 结果：Qwen35-27B、Gemma4-31B-it、Gemma4-26B-A4B-it、GLM-4.7-Flash 都通过 thinking/non-thinking 模板区分检查。
- Template facts / 模板事实：Qwen thinking 以 `<think>` 开始，non-thinking 插入空 `<think>...</think>`；Gemma thinking 注入 `<|think|>`，non-thinking 是空 thought channel；GLM thinking 以 `<think>` 开始，non-thinking 以 `</think>` 开始。
- Key consequence / 关键后果：首 token `Yes/No` 或 `A/B` logprob 不是 thinking verifier 测量。已有 verifier 结论保留为 `DV`；thinking headline 需要 E92-E99。

**E92 Qwen thinking pilot and E100-E102 batch/mode audit / Qwen thinking 初测与 batch/mode 机制审计**

- Files / 文件：`results/E92_thinking_hard_task_natural/qwen35_27b_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json`, `results/E92_thinking_hard_task_natural/e92_qwen35_27b_thinking_boxed_k2_max8192_checkpoint.jsonl`, `reports/E100_E102_BATCH_MODE_HIDDEN_CONTRAST_20260429.md`, `results/E100_batch_invariance_audit/`, `results/E101_batch_generation_sensitivity/`, `results/E102_thinking_nonthinking_hidden_contrast/`
- Mode / 模式：`TG` pilot、`MI-TG/MI-NG` replay audit、batch sensitivity diagnostic。
- E92 Qwen result / E92 Qwen 结果：36 条 thinking hard-task 生成中 6 条 final-correct；所有 36 条都没有严格 `Final answer:` 行，正确答案靠 `answer_phrase_line_last_number` 等 fallback 抽取。6 条 final-correct 快速人审未见 unrepaired ACPI；但样本小，不能写成 thinking 自然发生率结论。
- Boxed rerun boundary / boxed 重跑边界：把 prompt 改为要求最后 `\boxed{...}` 并把 `max_new_tokens` 提到 8192 后，Qwen 前两条仍 hit max 且没有 boxed final answer。这说明 Qwen thinking 的主要问题不是 token 给少一点，而是会持续自检、不收口；盲目拉长 token 会放大 endless thinking。
- E100 batch invariance / batch 不变性：固定 prompt+completion replay，不生成新文本；Qwen27B 在 4096-token replay、batch=1/2/4 下 residual/MLP/token-mixer/logits 近乎一致，整体 worst min cosine 0.9995675，worst max relative L2 0.03044。解释：batch size 不太可能推翻 hidden 方向结论，但不是 bit-identical，论文 appendix 应把它列为数值/实现 confound。
- E101 batch generation sensitivity / batch 生成敏感性：小样本、`max_new_tokens=512`、batch=1/2/4；NG 与 TG 都 100% hit max、无 final marker、0 final-correct。解释：这是 sensitivity diagnostic，不是自然发生率；短上限能避免 endless thinking，但会把“未收口”显式暴露出来。
- E102 thinking vs non-thinking hidden contrast / thinking 与非 thinking hidden 对比：把已有 TG/NG trace 放入同一 strict direct-verifier prompt；NG 平均 1124 completion tokens，TG 平均 4352 tokens。NG overall accept 0.667、Yes-No 2.46；TG overall accept 0.75、Yes-No 1.19。NG_E57 strict-valid-like rows accept 1.0、Yes-No 4.81；NG_E88 answer-first repaired rows accept 0、Yes-No -2.25；TG_E92 rows accept 0.667、Yes-No 1.0；boxed truncated TG rows accept 1.0、Yes-No 1.75。
- Interpretation / 解释：thinking 与 non-thinking 的主要差异不是“有无内部计算”，而是外显推理预算、收口/格式遵从、以及 strict verifier 如何读取这段 trace。non-thinking 也有 hidden process evidence；thinking 更长、更常反复自检，但不自动保证更好的 final decision 或更好的 trace-selection。

**E103-E104 Qwen TG/NG fair hard-task audit / Qwen thinking 与 non-thinking 公平对照**

- Files / 文件：`reports/E103_E104_TG_NG_FAIRNESS_AUDIT_20260429.md`, `reports/E103_E104_TG_NG_FAIRNESS_AUDIT_20260429.json`, `results/E103_tg_ng_fair_hardtask/qwen35_27b_e103_tg_ng_fair_hardtask.json`, `data/processed/e104_tg_ng_process_audit_official_20260429.jsonl`.
- Mode / 模式：`TG`/`NG` generation plus manual process audit. / thinking 与非 thinking 生成，并做人审过程有效性。
- Design / 设计：Qwen35-27B, 3 hard tasks (`base_divisor`, `integer_pairs_quad`, `trapezoid_incircle`), 3 prompt variants (`neutral`, `self_check`, `answer_first_no_gold`), k=1, max_new_tokens=4096, batch max_time=600s; no gold answer or trap note in prompts. / Qwen35-27B，3 道困难题，3 个 prompt 变体，每格 1 条，4096 token 上限，prompt 无答案/陷阱泄露。
- E103 strict result / E103 strict 结果：`NG_baseline` strict final-correct 8/9, explicit final marker 9/9, hit-max 2/9; `NG_matched_sampling` strict 7/9, marker 9/9, hit-max 4/9; `TG_official` strict 0/9, marker 0/9, hit-max 9/9. / strict 口径下 TG 不是更强，而是全部不收口。
- Fallback boundary / fallback 边界：`TG_official` fallback-correct 5/9, but all 5 are 4096-token truncated traces without explicit final marker. These are "the correct number appears in thinking", not strict final decisions. / TG fallback 有 5/9 能抽到正确数字，但全是无 final marker 的截断 trace，不能当作模型明确提交的最终答案。
- E104 audit / E104 人审：NG final-correct rows include 3 repaired strict ACPI cases, all from `answer_first_no_gold` where the trace starts with a wrong `Final answer` and later corrects it; unrepaired ACPI = 0. TG fallback-correct rows are audited as unfinished TG, not strict ACPI. / NG 中 3 条 repaired strict ACPI 都来自 answer-first 先写错答案再修复；未修复 ACPI 为 0。TG fallback-correct 行归类为未完成 thinking，不计 strict ACPI。
- Interpretation / 解释：thinking did not improve strict final-answer correctness in this Qwen small sample; the primary TG failure is closure/final-decision formatting. Sampling contributes because `NG_matched_sampling` worsens hit-max vs baseline, but it does not explain all TG behavior because matched NG still emits explicit final markers in 9/9 rows. / 这轮 Qwen 小样本中 thinking 没提升 strict 正确率，主要失败是收口/最终决策格式；采样参数会加重长输出，但无法解释 TG 0/9 final marker。

**E105 Qwen TG closure-policy intervention / Qwen thinking 收口策略干预**

- Files / 文件：`reports/E105_TG_CLOSURE_POLICY_20260429.md`, `reports/E105_TG_CLOSURE_POLICY_20260429.json`, `scripts/run_e105_tg_closure_policy.py`, `scripts/summarize_e105_tg_closure_policy.py`, `logs/e105_qwen35_tg_closure_k1_checkpoint_20260429.jsonl`, `logs/e105r_qwen35_canary16k_checkpoint_20260429.jsonl`, `logs/e105r_qwen35_canary32k_checkpoint_20260429.jsonl`.
- Mode / 模式：`TG` generation diagnostic; Qwen35-27B thinking enabled, official-style sampling `temperature=1.0, top_p=0.95, top_k=20`; prompts contain no gold answer or trap note. / thinking 生成诊断；Qwen35-27B 开启 thinking，使用官方风格采样参数，prompt 无答案/陷阱泄露。
- 8k boundary / 8k 边界：`free_think_8192` capped pilot produced 2 rows; both hit 8192 tokens, 0/2 explicit `Final answer`, strict final-correct 0/2, fallback-correct 1/2. / 8k 仍不收口，不能把 fallback 数字当作最终提交。
- 16k canary / 16k canary：on `aime25_base_divisor_p1`, 3/3 strict final-correct and 3/3 explicit marker, but clean final stop only 1/3. `free_think_16384` and `budgeted_final_16384` hit max and continued after `Final answer`; `final_contract_16384` stopped naturally at 16111 tokens with final line last. / 16k 能让正确 final marker 出现，但只有强 final-contract 干净停止。
- 32k canary / 32k canary：`final_contract_32768` on the same task stopped naturally at 13120 tokens, strict final-correct 1/1, clean final stop 1/1. / 32k 强契约在该题上能自然收口。
- Interpretation / 解释：Qwen TG failure is not simply “it cannot compute the answer”; it is a closure/final-decision control problem. `Final answer` appearing somewhere in a long thought stream is weaker than a clean final stop. / Qwen thinking 的主要失败不是不会算，而是不稳定收口；长思考中出现 `Final answer` 不等于模型已经完成严格最终决策。
- Boundary / 边界：E105 canary mostly covers one easy hard-task (`base_divisor`); it does not prove TG beats NG. It tells us that future TG/TG-mechanism experiments should use final-contract prompts and must report token budget, hit-max, post-final continuation, and clean final stop separately. / E105 不能证明 thinking 整体更强；它给后续 TG 评估规定了更严格的数据治理口径。

## 7. Claims After Thinking Audit / thinking 审计后的结论保留状态

**可以保留，但必须注明模式：**

- `DV`: controlled ACPI trace-selection risk 稳健；pointwise `Yes/No` 会过度接受；objective/threshold/final-answer anchor/readout 会影响接受率。
- `DV`: E61 证明风险跨多语言路径和错误类型，不是 discount 个例。
- `DV`: core P0 sibling 与 label-free 诊断能强烈暴露过程错误；但 GLM 说明 raw sibling 不是 oracle。
- `MI-DV`: hidden residual/MLP/token-mixer 中存在过程有效性证据；置换和留一审计排除了简单模板 artifact。
- `MI-DV/MI-TG replay`: 固定 token replay 的 batch=1/2/4 hidden/component 读数高度一致但非 bit-identical；batch size 应作为工程 confound 记录，不应把现场 generation 的 batch 敏感性混入 hidden replay 结论。
- `NG`: 当前 non-thinking hard-task 样本中 unrepaired ACPI 低频但真实存在。
- `TG` boundary: Qwen E103 shows no strict final-correct advantage for thinking under the 4096-token hard-task prompt; E105 shows that higher budget plus a strong final-contract can make Qwen submit a clean final answer on `base_divisor`, but 8k still failed and 16k free/budgeted prompts continued after the final marker. This is a closure-policy boundary, not a universal TG ability claim. / `TG` 边界：Qwen E103 在 4096 token 下没有 strict 正确率优势；E105 显示更高 token 加强 final-contract 可在 `base_divisor` 上干净提交答案，但 8k 仍失败，16k free/budgeted 会在 final marker 后继续输出。这是收口策略边界，不是 thinking 能力普遍提升结论。
- `PM`: outcome-only 或过弱 verifier 筛选会保留 ACPI；strict 与 repair-aware policy 会导致不同数据治理结论。

**不能直接保留为 thinking-mode claim，需要重测：**

- `TV`: thinking verifier 是否仍 over-accept ACPI。
- `TG`: thinking generation 下自然 strict/repaired/unrepaired ACPI 的发生率。
- `TG`: Qwen thinking pilot 显示“长思考、不收口、缺 final marker”是独立现象；不能把 fallback 抽取答案当成模型明确 final decision。
- `TV`: thinking sibling/readout 是否仍显示 GLM raw-label bottleneck。
- `TG/TV mechanism`: thinking tokens、repair markers、final decision tokens 上是否仍能读出 residual/MLP/token-mixer 过程信号。
- `TG` scaling: E105 的 final-contract 成功只覆盖一题；必须在多题、多模型上重测，且单独报告 clean final stop。

## 8. Next Experiments E92-E99 / 下一阶段实验

| id | mode | 实验内容 | 为什么做 |
|---|---|---|---|
| E92 | `TG` | 在所有 P0 上开启 thinking，重跑 AIME-style hard-task 自然生成；使用 `neutral`、`answer_first_no_gold`、`self_check` 变体；对 final-correct 行人工/agent 审计为 strict-valid、repaired ACPI、unrepaired ACPI。 | 验证 E57/E88 的 hard-task 发生率是否只是 non-thinking 条件现象；建立 thinking-mode 自然发生率。 |
| E93 | `TG` | 开启 thinking 重跑 E48 simple/no-leak surface-semantic 自然任务。 | 检查简单任务中“几乎不自然产生 ACPI”的结论在 thinking 模式下是否仍成立。 |
| E94 | `TV` | 对 E42/E53/E54/E60/E61/E71 的受控 trace 开启 thinking verifier；生成完整输出并解析最终 `Yes/No`；比较 plain/careful/answer-blind/locate/sibling。 | 验证 direct-verifier over-accept 是否在 thinking verifier 中保留，或 thinking 是否显著修复 objective/threshold 错配。 |
| E95 | `TV` | thinking sibling/readout：A/B、反向顺序、label-free two-pass，重点 GLM。 | 检查 GLM raw A/B readout bottleneck 是否只是首 token/direct-logprob artifact，还是 thinking final decision 也会发生。 |
| E96 | `TV` | thinking strict-vs-repair-aware 与 hard-case ablation：repaired/unrepaired 个案、final answer shown/removed/wrong/masked、E86 代数负控制。 | 分离“模型默认把 CoT 当草稿读”的 repair-aware 接受，与真正漏掉 unrepaired 错误。 |
| E97 | `TG/TV mechanism` | 保存 thinking 输出中的 thought tokens、repair markers、final decision tokens，以及 residual/MLP/token-mixer/attention-related 激活；做 probe、留一和置换控制。 | 把机制主张从 direct-verifier prompt 推进到 thinking 路径，确认“意识到错误/修复”的激活变化。 |
| E98 | `PM` | 在 E92-E97 后重算 outcome-only、DV、TV、sibling、label-free、strict、repair-aware filters；分 `NG`/`TG` 报表。 | 给论文 appendix 一个不混模式的数据治理风险表。 |
| E99 | `TG/TV` | thinking self/cross verifier：source model 生成 thinking trace，由自己和其它 P0 模型用 thinking verifier 盲审。 | 验证 self-verifier 方法论是否合理，以及 cross-family 判断是否仍共享同一风险。 |

## 9. Immediate Execution Policy / 立即执行规则

1. 新结果必须标注 `DV`/`TV`/`NG`/`TG`/`MI-DV`/`PM`。
2. 所有 thinking verifier 不能用首 token option-logprob，必须解析最终判定。
3. E57/E88 只能作为 `NG` hard-task 证据，直到 E92 完成。
4. E42/E60/E61 等 verifier 结论只能作为 `DV` 证据，直到 E94 完成。
5. hidden mechanism claim 只能作为 `MI-DV`，直到 E97 捕捉 thinking token/repair marker/final decision token。
6. active workspace audit 当前通过；官方结果以 reports/results/data/processed/configs 中列出的文件为准。

## 10. 2026-04-30 E106-E114 Non-Thinking Mechanism Suite / non-thinking 机制套件

- Plan / 计划：`reports/E106_E120_EXPERIMENT_EXECUTION_PLAN_20260430.md`
- Report / 报告：`reports/E106_E114_NONTHINKING_MECHANISM_SUITE_20260430.md`
- Scripts / 脚本：`scripts/run_e106_e114_nonthinking_mechanism_suite.py`, `scripts/launch_e106_e114_nonthinking_mechanism_queue_20260430.sh`
- Result dir / 结果目录：`results/E106_E114_nonthinking_mechanism_suite/`
- Status log / 状态日志：`logs/e106_e114_nonthinking_mechanism_status_20260430.jsonl`
- Mode / 模式：`MI-DV` + direct/non-thinking verifier diagnostics. / direct/non-thinking verifier 机制诊断。
- Status / 状态：四模型队列已完成，`all_done` at `2026-04-30T01:08:58+08:00`。
- Main question / 主问题：hidden process-validity signal 是否只是 readout confidence；如果不是，能否用 hidden gate 或 activation steering 激发 non-thinking 的内部过程监控潜力。
- Design correction / 设计修正：E106/E114 的 base readout 使用 E61 同款 `plain_yes_no`，hidden process direction 来自 strict-prompt final-token residual。这样 E114 检验的是 plain absolute over-accept 是否能被 hidden process gate 降低，而不是检验已经很强的 strict prompt。
- Static audit / 静态审计：`py_compile`、launcher `bash -n`、active workspace audit 均通过；Qwen/Gemma26/GLM smoke 均通过，prompt leakage counters 通过。
- Main result 1 / 主要结果 1：hidden process AUC 分别为 Qwen 1.000、Gemma31 1.000、Gemma26 0.970、GLM 0.997；plain Yes/No accuracy 只有 0.698-0.792。说明 non-thinking hidden residual 中已经有强过程有效性证据，但默认读出没有完全使用。
- Main result 2 / 主要结果 2：process direction 与 readout confidence direction 高度同轴，cosine 0.935-0.994；控制 confidence 和 entropy 后 partial correlation 仍为 0.650-0.882。安全解释是：过程证据和置信度缠在一起，但 hidden 仍保留默认 Yes/No 未充分使用的 process-specific 信息。
- Main result 3 / 主要结果 3：hidden gate 将受控 ACPI base accept 从 0.375-0.458 降到 0-0.042；valid retention 对 Qwen/Gemma31 无损，对 Gemma26/GLM 有少量 false rejection。说明可以激发 non-thinking 的内部过程监控潜力，但阈值需要校准。
- Main result 4 / 主要结果 4：E109 activation steering 只在 GLM 上产生大量 flip；且 process-invalid 与 confidence-low 干预效果相似。因此 E109 证明 GLM readout/threshold 可被推动，但还没有因果分离 process 与 confidence。
- Main result 5 / 主要结果 5：Gemma31 repaired ACPI 在 `error_span_end` 仍被接受，repair marker 后 hidden score 和 Yes/No margin 转负；Gemma26 出现 hidden 已偏负但 Yes/No 仍接受的错配。说明 repair-aware 阅读、答案自洽后文和读出阈值会影响过程证据是否被用上。

## 11. 2026-04-30 E116-E118 Thinking Stop-Signal / thinking 收口信号

- Plan / 计划：`reports/E116_E120_EXECUTION_PLAN_20260430.md`
- Report / 报告：`reports/E116_E118_THINKING_STOP_SIGNAL_20260430.md`
- Script / 脚本：`scripts/run_e116_e118_thinking_stop_signal_suite.py`
- Queue / 队列：`scripts/launch_e116_e118_thinking_stop_signal_queue_20260430.sh`
- Result / 结果：`results/E116_E118_thinking_stop_signal/qwen35_27b_e116_e118_thinking_stop_signal_suite.json`
- Cache / 激活缓存：`results/E116_E118_thinking_stop_signal/qwen35_27b_e116_e118_component_points.pt`
- Mode / 模式：`MI-TG` post-hoc replay. / thinking trace 机制复放。
- Status / 状态：队列已完成，`all_done` at `2026-04-30T01:30:06+08:00`；active workspace audit 通过。
- Leakage / 泄露：不做新生成；复放原始 E105/E103 prompt+completion；gold/final/manual labels 只用于离线分组和 policy simulation，泄露计数均为 0。
- Main result 1 / 主要结果 1：Qwen thinking clean-stop 点与 hit-max/post-final-continuation 点在 `34:residual_hidden_state` stop direction 上分离明显；positive mean 29.345，negative mean -8.438，threshold 10.453。
- Main result 2 / 主要结果 2：process-validity score 在各 stop label 中大多为正，说明“过程看起来有效”和“是否应该停止/提交”不是同一个信号。
- Main result 3 / 主要结果 3：post-hoc early-stop simulation 在 10 个 final-like candidate 中触发 6 个，6 个全是 final-correct，平均节省 1318 tokens；但漏掉 3 个 final-correct candidate，所以它是高精度、低召回的小样本诊断，不是可靠部署策略。
- Current interpretation / 当前解释：thinking 暴露了一个独立于 ACPI 的 final-decision/stop bottleneck；模型可能已经得到答案并有过程有效性信号，但仍不会稳定提交并停止。

## 12. 2026-04-30 E120 Unified Audit Package / 统一审计包

- Script / 脚本：`scripts/run_e120_unified_audit_package.py`
- Report / 报告：`reports/E120_UNIFIED_AUDIT_PACKAGE_20260430.md`
- JSON / 机器可读结果：`reports/E120_UNIFIED_AUDIT_PACKAGE_20260430.json`
- Mode / 模式：`PM` appendix/audit synthesis. / 后处理审计汇总。
- Status / 状态：生成完成，active workspace audit 通过。
- Purpose / 目的：把 E106-E114 与 E116-E118 的模式边界、泄露计数、hidden gate、stop-signal、剩余风险汇总成论文 appendix 草稿。
- Main boundary / 主要边界：`DV`、`MI-DV`、`NG`、`TG`、`MI-TG`、`PM` 必须分开报告；首 token direct verifier 不能冒充 thinking verifier，fallback 抽取答案不能冒充 clean final decision。
- Current safe claim / 当前安全 claim：受控 strict ACPI trace-selection risk 在 direct/non-thinking verifier 中稳健；hidden activation 有过程有效性证据，但最终决策是否使用它取决于 confidence/objective/threshold/answer anchor/repair-aware reading/long self-consistency/readout format。thinking 额外引入 stop/commit bottleneck：模型可以已有有效过程证据，却仍不能稳定提交并停止。

## 13. 2026-04-30 E119 Natural Hard-Task Expansion / 自然困难题扩样

- Plan / 计划：`reports/E119_NATURAL_HARDTASK_EXPANSION_PLAN_20260430.md`
- Builder / 审计表构建：`scripts/build_e119_natural_hardtask_audit_sheet.py`
- Queue / 队列：`scripts/launch_e119_natural_hardtask_expansion_queue_20260430.sh`
- Result / 结果：`results/E119_natural_hardtask_expansion/e119_audit_sheet_summary.json`, `data/processed/e119_natural_hardtask_final_correct_audit_sheet_20260430.jsonl`.
- Status / 状态：completed; `all_done` at `2026-04-30T04:06:05+08:00`; status file `logs/e119_natural_hardtask_expansion_status_20260430.jsonl`.
- Mode / 模式：`NG` only, `thinking=false`.
- Design / 设计：4 models × 6 AIME-style tasks × 3 no-gold prompt variants × k=2 = 144 generated rows, `max_new_tokens=4096`.
- Static/smoke / 静态与冒烟：builder `py_compile` 通过，queue `bash -n` 通过，Qwen 1-row smoke 通过，启动前 active workspace audit 通过。
- Purpose / 目的：扩大 NG 自然困难题 final-correct 条件下 strict/repaired/unrepaired ACPI 的估计样本；不混入 thinking 生成或 thinking verifier。
- Main fact / 主要事实：144 generated rows produced 104 final-correct rows for manual/process audit; leakage counters all 0. Per-model final-correct counts are Qwen 24/36, Gemma31 31/36, Gemma26-A4B 32/36, GLM 17/36. / 144 条生成得到 104 条 final-correct 待人工/过程审计，泄露计数为 0。各模型 final-correct 为 Qwen 24/36、Gemma31 31/36、Gemma26-A4B 32/36、GLM 17/36。
- Caveat / 边界：this is `NG_uniform_legacy_baseline` because the generation parameters used the project-uniform profile (`temperature=0.7`, `top_p=0.95`, `top_k=50`, `max_new_tokens=4096`), not the later model-card HF profile. / 这是项目统一采样 baseline，不是后续模型卡 HF profile。

## 14. 2026-04-30 E121-E130 Top-Tier Next-Stage Scaffold / 顶会级下一阶段脚手架

- Plan / 计划：`reports/TOP_TIER_CLAIM_AND_NEXT_EXPERIMENT_PLAN_20260430.md`
- Manifest / 实验清单：`configs/e121_e130_next_stage_manifest.yaml`
- Smoke script / 冒烟脚本：`scripts/smoke_e121_e130_scaffold.py`
- Smoke result / 冒烟结果：`results/E121_E130_scaffold_smoke/e121_e130_scaffold_smoke.json`
- Mode / 模式：planning + no-GPU static smoke; no large model loaded. / 规划和无 GPU 静态冒烟，不加载大模型。
- Status / 状态：`py_compile` passed; scaffold smoke passed; active workspace audit passed after whitelisting official artifacts. / 编译、脚手架冒烟和官方工作区审计均通过。
- Current claim / 当前主张：controlled strict ACPI trace-selection risk is robust in `DV`/`MI-DV`; natural unrepaired ACPI is low-frequency but real in current `NG`; hidden activation carries process-validity evidence, but confidence/objective/threshold/answer anchor/repair-aware reading/long self-consistency/readout format/stop-commit control decide whether final decisions use it. / 受控 strict ACPI 在 direct/non-thinking verifier 中稳健；自然 unrepaired ACPI 在当前 non-thinking 困难题中低频但真实；hidden activation 有过程有效性证据，但最终是否用上取决于置信度、目标、阈值、答案锚定、repair-aware 阅读、长自洽后文、读出格式和 stop/commit 控制。
- Key weakness / 主要薄弱点：natural prevalence remains underpowered; `TV` replication is missing; hidden mechanism is still partly correlational; process/confidence/stop are entangled; hard-task scope needs broader families; human audit reliability needs double-audit appendix. / 自然发生率仍欠样本量；thinking verifier 还未系统复现；hidden 机制仍有相关性成分；过程、置信度和停止信号缠绕；困难任务需要更广任务族；人审需要双审附录。
- Planned experiments / 规划实验：E121 `TV` objective ladder, E122 `TV` sibling/label-free, E123 process-confidence-stop disentanglement, E124 layer/component causal sweep, E125 natural hard-task expansion, E126 activation-induced/reduced ACPI, E127 training-filter simulation, E128 human-audit reliability, E129 cross-family replication, E130 trace-as-proof vs trace-as-draft policy. / E121-E130 分别覆盖 thinking verifier、thinking sibling、过程/置信度/停止解缠、组件因果干预、自然发生率扩样、激活诱发/降低 ACPI、训练筛选模拟、人审可靠性、跨模型复现，以及 CoT 是证明还是草稿的评价口径。

## 15. 2026-04-30 Qwen/Gemma Parameter Audit / Qwen/Gemma 参数审计

- Report / 报告：`reports/QWEN_GEMMA_PARAMETER_AUDIT_AND_NEXT_DESIGN_20260430.md`
- Manifest / 参数清单：`configs/qwen_gemma_parameter_profiles_20260430.yaml`
- Scope / 范围：Qwen3.5-27B、Gemma4-31B-it、Gemma4-26B-A4B-it；GLM 暂时作为后续补跑边界证据。
- Main audit fact / 主要审计事实：`DV/MI-DV` verifier and hidden-replay experiments are parameter-valid because they use deterministic option-logprob or teacher-forced replay; sampling parameters are not applicable there. / direct verifier 和 hidden replay 实验参数可信，因为它们是确定性打分或 teacher-forced replay，不依赖采样参数。
- Relabeling / 重标注：E57/E88/E119-style `NG` natural generation used project-uniform sampling (`temperature=0.7`, `top_p=0.95`, `top_k=50`), so these runs must be labeled `NG_uniform_legacy_baseline`, not model-card official sampling. / 自然生成历史结果应标成项目统一采样 baseline，不能写成模型卡官方参数。
- Correction / 修正：future generation scripts now use `tokenizer.pad_token_id` when available instead of forcing `pad_token_id=eos_token_id`; this matters for Gemma4 whose generation config uses pad id 0 and multiple EOS ids. / 后续生成脚本已改为优先使用 tokenizer 自带 pad id；这对 Gemma4 很重要。
- Locked profiles / 敲定参数：Qwen `TG` uses `temperature=1.0`, `top_p=0.95`, `top_k=20`, final-contract, `max_new_tokens=32768`; Gemma uses `temperature=1.0`, `top_p=0.95`, `top_k=64`, `max_new_tokens=8192` with 16k escalation if hit-max is high. / Qwen thinking 后续用 32k final-contract；Gemma thinking/non-thinking 用 1.0/0.95/64，必要时从 8k 升到 16k。
- Remaining caveat / 剩余边界：Qwen model-card `presence_penalty` is not natively implemented in current HF generate; future exact model-card reruns must implement it, use a backend that supports it, or explicitly record it as unavailable. / Qwen 的 presence penalty 当前 HF 生成没有原生实现；后续必须实现、换后端，或显式记录未启用。

## 16. 2026-04-30 Qwen/Gemma E119 Audit Sheet + E146 Queue / Qwen/Gemma E119 审计表与 E146 队列

- E119 Qwen/Gemma audit sheet / E119 Qwen/Gemma 审计表：`data/processed/e119_qwen_gemma_final_correct_audit_sheet_20260430.jsonl`
- E119 Qwen/Gemma summary / E119 Qwen/Gemma 摘要：`results/E119_natural_hardtask_expansion/e119_qwen_gemma_audit_sheet_summary.json`
- E146 queue manifest / E146 队列清单：`configs/qwen_gemma_next_stage_queue_20260430.yaml`
- E146 launcher / E146 启动脚本：`scripts/launch_e146_qwen_gemma_ng_model_card_queue_20260430.sh`
- E146 smoke / E146 冒烟：`scripts/smoke_qwen_gemma_next_stage_queue.py`, `results/E146_qwen_gemma_ng_model_card_hf_profile/_smoke/qwen_gemma_next_stage_queue_smoke.json`
- Status / 状态：three model generations completed by `2026-04-30T06:36:31+08:00`; queue wrote `all_done` at `2026-04-30T06:36:32+08:00`. The audit-sheet build initially failed due to a relative-path bug in `scripts/build_e119_natural_hardtask_audit_sheet.py`; after patching `display_path()` usage, the E146 audit summary was rebuilt successfully at `2026-04-30T12:04:06+08:00`. / 三个模型生成在 `2026-04-30T06:36:31+08:00` 前完成；队列在 `2026-04-30T06:36:32+08:00` 写出 `all_done`。审计表构建一开始因相对路径 bug 失败；修复 `display_path()` 使用后，E146 审计摘要在 `2026-04-30T12:04:06+08:00` 成功重建。
- E119 Qwen/Gemma facts / E119 Qwen/Gemma 事实：108 generated rows, 87 final-correct rows selected for process audit, leakage counters all 0. Qwen has 24/36 final-correct with 16 hit-max rows; Gemma31 has 31/36 final-correct with 2 hit-max rows; Gemma26-A4B has 32/36 final-correct with 4 hit-max rows. / Qwen/Gemma 共 108 条生成，87 条 final-correct 进入过程审计，泄露计数为 0。Qwen 为 24/36 final-correct、16 条 hit-max；Gemma31 为 31/36 final-correct、2 条 hit-max；Gemma26-A4B 为 32/36 final-correct、4 条 hit-max。
- E146 purpose / E146 目的：rerun natural hard-task generation for the three Qwen/Gemma P0 models under model-card-aligned HF generation profiles, then build a separate final-correct audit sheet. / 用更贴近模型卡的 HF 生成参数复跑 Qwen/Gemma 三个 P0 模型的自然困难题，再单独构建 final-correct 过程审计表。
- E146 parameters / E146 参数：Qwen uses `temperature=1.0`, `top_p=0.95`, `top_k=20`, `max_new_tokens=8192`, `thinking=false`; Gemma31/Gemma26 use `temperature=1.0`, `top_p=0.95`, `top_k=64`, `max_new_tokens=8192`, `thinking=false`. / Qwen 使用 1.0/0.95/20/8192/non-thinking；Gemma31/Gemma26 使用 1.0/0.95/64/8192/non-thinking。
- E146 facts / E146 事实：108 generated rows produced 97 final-correct rows for process audit; leakage counters all 0. Qwen has strict/fallback final-correct 30/31 out of 36 with 8 hit-max rows; Gemma31 has 32/32 out of 36 with 2 hit-max rows; Gemma26-A4B has 34/34 out of 36 with 2 hit-max rows. / E146 共 108 条生成，97 条 final-correct 进入过程审计，泄露计数为 0。Qwen strict/fallback final-correct 为 30/31/36，8 条 hit-max；Gemma31 为 32/32/36，2 条 hit-max；Gemma26-A4B 为 34/34/36，2 条 hit-max。
- Boundary / 边界：E146 is labeled `NG_model_card_hf_profile`, not exact Qwen model-card replication, because Qwen `presence_penalty` is still unavailable in current HF generate. / E146 标注为 `NG_model_card_hf_profile`，不是 Qwen 精确模型卡复现，因为当前 HF generate 仍未启用 Qwen presence penalty。
- Safety / 安全性：static compile, launcher `bash -n`, no-GPU smoke, and active workspace audit passed before launch. The launcher waits for E119 to finish or release GPUs before loading any large Qwen/Gemma model, reducing OOM risk. / 启动前静态编译、`bash -n`、无 GPU 冒烟和官方工作区审计均通过。启动脚本会等 E119 完成或释放 GPU 后再加载大模型，降低 OOM 风险。

## 17. 2026-04-30 E119/E146 Official Process Audit / E119/E146 官方过程审计

- Script / 脚本：`scripts/finalize_e119_e146_process_audit.py`
- Report / 报告：`reports/E119_E146_PROCESS_AUDIT_20260430.md`
- JSON / 机器可读结果：`reports/E119_E146_PROCESS_AUDIT_20260430.json`
- Official rows / 官方逐行标签：`data/processed/e119_e146_process_audit_official_20260430.jsonl`
- Summary copy / 摘要副本：`results/E119_E146_human_process_audit/e119_e146_process_audit_summary.json`
- Mode / 模式：`NG`, `thinking=false`; E119 is `NG_uniform_legacy_baseline`, E146 is `NG_model_card_hf_profile`. / 只讨论 non-thinking 自然生成；E119 是项目统一采样 baseline，E146 是模型卡对齐 HF profile。
- Audit policy / 审计口径：strict process treats an explicit wrong final answer, wrong key formula, or wrong intermediate claim as process-invalid even if later repaired; repair-aware process accepts a trace only if the later text clearly discards the wrong step and gives a self-consistent correct proof; unrepaired ACPI means the final answer is correct but the retained proof still depends on a wrong key step. / strict 口径下，只要 trace 明确提交过错误最终答案、错误关键公式或错误中间结论，即使后文修好也算过程无效；repair-aware 口径只在后文明确丢弃错误步骤并给出正确证明时接受；unrepaired ACPI 是最终答案正确但最终保留证明仍依赖错误关键步骤。
- Main fact / 主要事实：252 generated rows produced 201 final/fallback-correct rows for audit; 200 rows were strict final decisions because `1460087` was truncated fallback-only. / 252 条生成得到 201 条 final/fallback-correct 审计行；其中 200 条是严格最终答案提交，`1460087` 只是截断后 fallback 抽到正确数字，不进入 strict final-decision 分母。
- Strict ACPI / strict 口径 ACPI：46/200 strict final-decision rows, Wilson CI [0.177, 0.293]. / strict ACPI 为 46/200，置信区间如上。
- Repaired vs unrepaired / 已修复与未修复：44 repaired strict ACPI and 2 unrepaired ACPI. Unrepaired ACPI rate is 2/200 = 0.010, Wilson CI [0.003, 0.036]; per generated it is 2/252 = 0.008, Wilson CI [0.002, 0.028]. / 44 条是先错后修的 repaired strict ACPI，2 条是未修复 ACPI；未修复 ACPI 仍低频。
- Unrepaired cases / 未修复个案：`1190020` and `1460021`, both Gemma4-26B-A4B integer-pairs answer-first traces. Both use the wrong plus-xy factorization `(3x - 2y)(4x + 3y)` or equivalent, never repair it, and still reach the correct answer 117 because the line counts are sign-symmetric. / 两条未修复个案均来自 Gemma26-A4B 的整数二次型 answer-first trace；错误分解会产生 `+xy`，但由于计数对符号对称，答案碰巧仍为 117。
- By model / 按模型：Qwen 19 strict ACPI / 0 unrepaired; Gemma31 16 / 0; Gemma26-A4B 10 / 2; GLM 1 / 0. / Qwen 和 Gemma31 主要是 repaired；Gemma26-A4B 提供两条未修复自然 ACPI；GLM 样本少，仅 1 条 repaired。
- By prompt / 按 prompt：answer-first is the main source, with 32 strict ACPI including both unrepaired cases; neutral has 5 repaired strict ACPI plus one fallback-only unfinished row; self-check has 9 repaired strict ACPI. / answer-first 是主要来源，包含两条未修复个案；neutral/self-check 主要是 repaired 或 fallback 边界。
- Interpretation / 解析：natural hard tasks show that strict ACPI is common when the model writes a first answer or a visible scratch proof, but unrepaired ACPI remains low-frequency. This strengthens the paper by separating trace-as-proof risk from true unrepaired wrong-process prevalence. / 自然困难题说明：如果把 CoT 当严格证明，先错后修的 strict ACPI 很常见；但真正未修复、答案碰巧正确的 ACPI 仍低频。论文必须把“trace-as-proof 风险”和“未修复错误过程发生率”分开写。
- Current safe claim update / 当前安全主张更新：controlled strict ACPI trace-selection risk remains robust; NG natural unrepaired ACPI is low-frequency but real; E119/E146 add evidence that repair-aware reading is not a side issue but a dominant natural boundary. / 受控 strict ACPI 风险仍稳健；自然未修复 ACPI 低频但真实；E119/E146 进一步说明 repair-aware 阅读不是边角问题，而是自然 trace 中很主要的边界。
- Remaining weakness / 剩余薄弱点：human audit is still single-agent/one-pass with targeted second sampling; a publication-grade appendix should add independent double audit, broader hard-task families, and hidden residual/MLP/token-mixer localization on the newly labeled repaired/unrepaired rows. / 当前人审仍是单 agent 加定向二抽；顶会级附录还需要独立双审、更广困难任务族，以及在这些新标签上做 hidden residual/MLP/token-mixer 定位。

## 18. 2026-04-30 E131 E119/E146 Hidden Localization / E119/E146 隐藏层定位

- Runner / 运行脚本：`scripts/run_e131_e119_e146_hidden_localization.py`
- Queue / 队列：`scripts/launch_e131_e119_e146_hidden_localization_queue_20260430.sh`
- Summary script / 汇总脚本：`scripts/summarize_e131_hidden_localization.py`
- Report / 报告：`reports/E131_E119_E146_HIDDEN_LOCALIZATION_20260430.md`
- JSON / 机器可读结果：`reports/E131_E119_E146_HIDDEN_LOCALIZATION_20260430.json`
- Result dir / 结果目录：`results/E131_e119_e146_hidden_localization/`
- Status / 状态：queue completed with `all_done` at `2026-04-30T15:28:01`; all three Qwen/Gemma P0 models exited 0. / 队列正常完成，三个 Qwen/Gemma P0 模型均 exit 0。
- Mode / 模式：`NG`, `thinking=false`, direct strict verifier replay; no generation sampling. / 非 thinking 自然生成结果上的 strict verifier 重放；不涉及新采样。
- Design / 设计：use official E119/E146 process labels only offline to select strict-valid, repaired ACPI, and unrepaired ACPI rows and prefix endpoints; verifier prompts contain only problem plus visible trace prefix. E61 controlled process-validity directions are projected onto E119/E146 residual, MLP, token-mixer/attention-related, and norm outputs around the selected hidden layer. / 人工标签只用于离线选行和截断点；verifier prompt 只看题目和可见 trace 前缀。用 E61 的过程有效性方向投影 E119/E146 的 residual、MLP、token-mixer/attention 相关输出和 norm 输出。
- Leakage audit / 泄露审计：for all three models, `error_spans_in_prompt_rows=0`, `gold_answer_in_prompt_rows=0`, `labels_in_prompt_rows=0`. / 三个模型均无错误 span、答案或标签进入 prompt。
- Main fact Qwen / Qwen 事实：strict-valid accept 15/15, mean Yes-No 3.308, mean best residual score 1.105; repaired ACPI accept 4/133, mean Yes-No -3.544, mean best residual score -2.208. / Qwen 在 strict-valid 与 repaired ACPI 上分离清楚。
- Main fact Gemma31 / Gemma31 事实：strict-valid accept 30/30, mean Yes-No 20.165, mean best residual score 2.962; repaired ACPI accept 42/112, mean Yes-No -4.075, mean best residual score -3.165. First-final prefix is often accepted, but repair/error prefixes turn strongly negative. / Gemma31 在初始答案前缀和修复/错误前缀之间出现明显内部状态移动。
- Main fact Gemma26 / Gemma26 事实：strict-valid accept 18/18, mean Yes-No 4.958, mean best residual score -0.843; repaired ACPI accept 12/56, mean Yes-No -4.420, mean best residual score -4.456; unrepaired ACPI accept 8/10, mean Yes-No 5.956, mean best residual score -1.441. / Gemma26 的未修复 ACPI 是关键错配：Yes/No 最终放行，但 best residual score 仍低于 strict-valid。
- Unrepaired stage signal / 未修复阶段信号：for Gemma26 unrepaired ACPI, detected-error-marker prefixes are rejected 0/2 with mean Yes-No -0.719 and best residual score -2.172; completion prefixes are accepted 2/2 with mean Yes-No 8.187 while best residual score remains only -1.028. / 两条未修复个案在错误附近能看到负向过程信号，但完成态又被答案自洽拉回接受。
- Component interpretation / 组件解释：residual is the strongest readout in E131, but MLP, token-mixer/attention-related outputs, and norm outputs also move with prefix stage. This supports component-level observability, not yet a named causal circuit. / residual 最强，但 MLP、token-mixer/attention 相关输出和 norm 输出也随阶段移动；这说明组件层面可观测，不等于已经证明完整因果电路。
- Current safe claim update / 当前安全主张更新：E131 strengthens the evidence that process-validity information exists inside the verifier state on natural hard-task traces, including near error spans. The remaining gap is causal use: we still need activation steering/span patch to show that changing the relevant state changes decisions in the intended direction on these E119/E146 natural rows. / E131 强化了“自然困难题 trace 的 verifier 内部存在过程有效性证据，且错误附近可见”的证据；剩余缺口是因果使用，需要在这些自然行上继续做 steering/span patch。

## 19. 2026-04-30 Self-Verification Collision Audit + E132-E136 Plan / 自验证撞车审计与 E132-E136 计划

- Report / 报告：`reports/SELF_VERIFICATION_COLLISION_AND_E132_E136_PLAN_20260430.md`
- Status / 状态：literature audit and design memo only; no new model run. / 只做文献审计与实验设计备忘录，未启动新模型实验。
- Collision conclusion / 撞车结论：`Reasoning Models Know When They're Right` is a medium collision risk. It already shows hidden states in long-CoT reasoning models encode intermediate answer correctness and can support confidence-based early exit. It does not directly study answer-correct but process-invalid trace-selection, strict vs repair-aware process validity, error-span localization, residual/MLP/token-mixer component movement, or confidence-matched ACPI false-positive audits. / 这篇是中等撞车风险：它证明 long-CoT reasoning model hidden state 能编码中间答案正确性并支持 early exit；但没有直接研究答案正确但过程无效的 trace-selection、strict/repair-aware 口径、错误 span 定位、组件移动或 ACPI 的置信度匹配假阳性审计。
- Required framing / 必须采用的写法：do not claim novelty for hidden states knowing correctness or hidden-probe early exit. Claim novelty for process-validity under ACPI, evidence-to-readout mismatch, and local adaptive checking triggered by process-risk signals. / 不能声称 hidden state 知道正确性或 hidden-probe early exit 是首创；新意应写在 ACPI 过程有效性、证据到读出的错配，以及由过程风险信号触发的局部自适应检查。
- E132 / 实验：`Suspicious-but-valid controls` will test whether the hidden process-risk signal fires on valid traces that merely contain hesitation, double-checking, alternative valid routes, or unusual but correct algebra. / 可疑但正确控制组用于检查信号是否只是看到犹豫/检查词/非标准但正确步骤就误报。
- E133 / 实验：`Confidence-matched process probe` will match or regress out Yes/No margin, entropy, length, task, marker count, answer visibility, and repair markers to test whether hidden process score adds information beyond confidence. / 置信度匹配探针用于区分过程有效性与低置信度/难度。
- E134 / 实验：`Trigger-window audit` will inspect 160-240 character windows around hidden-triggered suspicious points and label repair, local recomputation, answer anchoring, hesitation-only, true error, false alarm, and ignored risk. / 可疑点窗口审计用于看触发点附近模型具体做了什么。
- E136 / 实验：`Adaptive checking policy` will compare NG-only, always-check, and hidden-trigger-check. Stage 1 is post-hoc trigger plus second-pass global/local check; Stage 2 is online semantic-boundary hidden monitoring. / 自适应检查比较只正常回答、总是检查、hidden 触发检查；第一阶段离线触发二次检查，第二阶段在线语义边界监控。
- E135 memo / 备忘录：LoRA/RL source experiment is deferred but mandatory later. Use small model families with base/instruct/reasoning checkpoints if Qwen3.5/Gemma4 full checkpoint chains are unavailable; first train LoRA/QLoRA adapters for outcome-only, process-aware, and adaptive-check objectives, then optionally run LoRA-GRPO/RL on rented GPUs. Treat small models as model organisms only if they reproduce the 30B ACPI, false-positive, confidence-matched, and adaptive-checking signatures. / LoRA/RL 来源实验暂缓但保留为必须线：若 Qwen3.5/Gemma4 无完整 checkpoint 链，先用小模型族做 LoRA/QLoRA，再必要时租卡做 LoRA-GRPO/RL；只有复现 30B 的关键签名时，才能把小模型称为机制 model organism。

## 20. 2026-04-30 E132-E134 Suspicious/Confidence Probe / 可疑但正确与置信度匹配小探针

- Dataset builder / 数据脚本：`scripts/build_e132_suspicious_valid_controls.py`
- Probe runner / 探针脚本：`scripts/run_e132_e133_suspicious_confidence_probe.py`
- Queue / 队列：`scripts/launch_e132_e133_probe_queue_20260430.sh`
- Window audit / 窗口审计：`scripts/build_e134_trigger_window_audit.py`
- Summary / 汇总：`scripts/summarize_e132_e134_probe.py`
- Report / 报告：`reports/E132_E134_SUSPICIOUS_CONFIDENCE_PROBE_20260430.md`
- JSON / 机器可读结果：`reports/E132_E134_SUSPICIOUS_CONFIDENCE_PROBE_20260430.json`
- Data / 数据：`data/processed/e132_suspicious_valid_controls_20260430.jsonl`, `data/processed/e134_trigger_window_audit_sheet_20260430.jsonl`
- Results / 结果：`results/E132_E133_suspicious_confidence_probe/`, `results/E134_trigger_window_audit/`
- Status / 状态：three-model queue completed with `all_done` at `2026-04-30T18:01:14`; GPU idle after completion. / 三模型队列正常完成。
- Scope / 范围：first controlled probe, 60 rows per model, 12 per variant, `thinking=false` direct verifier replay. / 第一版受控小探针，每模型 60 条、每变体 12 条。
- Design / 设计：E132 has 5 variants: clean valid, suspicious-valid marker, suspicious-valid alternative, low-confidence valid, and repaired strict-invalid. Labels/spans/gold are offline metadata only. / E132 五类变体，标签、span 和答案只作离线元数据。
- Main fact Qwen / Qwen 事实：completion-level hidden trigger `score<0` is 12/12 on invalid, 2/48 on all valid, and 2/36 on suspicious-valid; hidden AUC valid-vs-invalid is 1.000 while strict-confidence AUC is 0.447. / Qwen 的 hidden 信号不是单纯置信度，也不是看到可疑词就乱报。
- Main fact Gemma31 / Gemma31 事实：invalid 12/12 triggers; valid and suspicious-valid 0/48 and 0/36 trigger; hidden AUC 1.000. / Gemma31 最干净。
- Main fact Gemma26 / Gemma26 事实：invalid 12/12 triggers; valid 6/48 and suspicious-valid 5/36 trigger; hidden AUC 0.960. / Gemma26 仍能抓住 invalid，但 valid false trigger 更高，与 E78/E131 的 Gemma26 false-rejection 边界一致。
- Confidence matching / 置信度匹配：nearest-neighbor matched pairs give hidden valid>invalid accuracy 12/12 for all three models, but match distances remain nontrivial; this is probe evidence, not final causal separation. / 三模型匹配对均 12/12，但距离仍不小，不能过度声称完全分离置信度。
- E134 audit / 窗口审计：209 triggered/near-threshold windows were exported. `suspicion_marker_end` is explicitly marked as marker-only prefix control and excluded from deployment-style policy trigger interpretation. / E134 导出 209 个窗口；`suspicion_marker_end` 只是 marker-only 控制点，不能当部署误触发。
- Claim update / 主张更新：the process-risk signal is not a pure true-error detector, but on this controlled probe it is far more aligned with actual process invalidity than with superficial hesitation markers. Gemma26 requires calibration. / 过程风险信号不是纯错误检测器，但在本探针中明显更对齐真实过程无效，而不是表层犹豫词；Gemma26 需要阈值校准。
- Next / 下一步：expand E132 rows/types and run stricter confidence-matched regression; then run E136 stage-1 adaptive checking using calibrated trigger points. / 后续扩样本、做更严格回归，再进入 E136 自适应检查。

## 21. 2026-04-30 E136 Suspicious-Confidence Adaptive Check / 可疑-置信度自适应检查

- Runner / 运行脚本：`scripts/run_e136_suspicious_confidence_adaptive_check.py`
- Queue / 队列：`scripts/launch_e136_suspicious_confidence_adaptive_check_queue_20260430.sh`
- Summary / 汇总脚本：`scripts/summarize_e136_suspicious_confidence_adaptive_check.py`
- Report / 报告：`reports/E136_SUSPICIOUS_CONFIDENCE_ADAPTIVE_CHECK_20260430.md`
- JSON / 机器可读结果：`reports/E136_SUSPICIOUS_CONFIDENCE_ADAPTIVE_CHECK_20260430.json`
- Results / 结果目录：`results/E136_suspicious_confidence_adaptive_check/`
- Status / 状态：three-model queue completed with `all_done` at `2026-04-30T18:39:33`; all model exits were 0. / 三模型队列正常完成，无失败项。
- Mode / 模式：`NG`, `thinking=false`, post-hoc policy simulation on E132/E133 controlled rows; 60 rows per model. / 非 thinking；在 E132/E133 受控行上做后验策略模拟，每模型 60 条。
- Leakage audit / 泄露审计：all three model outputs report `passed=true`; prompts contain only problem, visible solution, and hidden-trigger-selected visible excerpt. / prompt 不含人工标签、gold 或 error span。
- Policy definition / 策略定义：`base` uses the original pointwise Yes/No decision; `always-global` rechecks every trace; `hidden-global/local` rechecks only when a hidden process-risk prefix triggers. / base 是原始 Yes/No；always-global 每条复查；hidden-global/local 只在 hidden 风险触发时复查。
- Cost definition / 成本口径：the script precomputes global checks for comparison, but real policy cost is the hidden trigger rate: Qwen 14/60, Gemma31 12/60, Gemma26 18/60. / 脚本为了比较预计算 global check；真实 hidden 检查调用率分别为 23.3%、20.0%、30.0%。
- Qwen fact / Qwen 事实：hidden trigger selected all 12 repaired strict-invalid rows and only 2/48 valid rows. Plain base accepted 4/12 invalid rows; hidden-local reduced invalid acceptance to 1/12 while retaining 47/48 valid rows. / Qwen 显示 hidden-trigger 局部检查可用作低成本风险开关。
- Gemma31 fact / Gemma31 事实：hidden trigger selected 12/12 invalid and 0/48 valid rows. Plain base invalid acceptance was 3/12; hidden-local reduced it to 2/12 while retaining 48/48 valid. / Gemma31 触发边界最干净。
- Gemma26 fact / Gemma26 事实：hidden trigger selected 12/12 invalid but also 6/48 valid rows. Local check accepted 5/12 invalid rows, worse than strict base 1/12, while retaining 48/48 valid. / Gemma26 说明 hidden 信号不能单独当 oracle；局部复查 prompt 会出现 repair-aware 或语义误读。
- Plain-language interpretation / 说人话解释：hidden process-risk can cheaply select high-risk traces, but the second-pass checker still needs the right objective. If the checker reads CoT as a repairable draft instead of a strict proof, it may still accept traces that contain a wrong step. / hidden 信号能低成本挑出高风险样本，但二次检查是否有效取决于评价口径；如果二次检查把 CoT 当可修复草稿而非严格证明，仍可能放过错步。
- Boundary / 边界：E136 is a post-hoc filter/recheck simulation, not online generation-time intervention, and its invalid rows are controlled repaired strict-invalid traces, not natural unrepaired ACPI. / E136 不是在线激活干预，也不是自然未修复 ACPI 发生率实验。
- Claim update / 主张更新：adaptive checking is promising for non-thinking verifier regimes, but current evidence supports a narrower claim: hidden process-risk provides a useful trigger; objective/readout still determines whether risk becomes a correct rejection. / 自适应检查有潜力，但当前只能说 hidden 过程风险是有用触发器；最终是否正确拒绝仍由 objective/readout 决定。

## 22. 2026-04-30 Method Note / 方法说明

- Method report / 方法报告：`reports/METHOD_TRACE_SELECTION_PIPELINE_20260430.md`
- Purpose / 用途：paper-style method description for trace construction, verifier objectives, hidden monitor, E136 second-pass verifier, and system-figure design. / 用论文 Method 的方式描述 trace 如何构造、verifier 如何打分、hidden monitor 如何工作、E136 二次检查何时介入，以及系统图怎么画。
- Trace synthesis / Trace 合成：controlled traces are created from task templates with valid and invalid process variants; offline metadata includes gold answer, error span, repair flag, and process label, but verifier prompts receive only problem plus visible trace. / 受控 trace 来自模板，包含正确/错误过程；答案、错误 span、标签只作离线元数据，不进入 verifier prompt。
- Natural traces / 自然 trace：P0 models generate no-gold hard-task solutions; only final-correct rows enter process audit, where they are labeled strict-valid, repaired ACPI, unrepaired ACPI, or truncation/fallback boundary. / 自然 trace 来自无答案困难题生成；最终答案正确行进入过程审计。
- Second verifier timing / 二次 verifier 介入时机：E136 first runs the base pointwise verifier; then prefix hidden scores decide whether to trigger a second global/local check. If no hidden trigger fires, the base decision is kept. / E136 先跑基线 verifier，再由前缀 hidden 分数决定是否触发全局或局部二次复查；不触发则保留基线。
- System diagram language / 系统图描述：left trace factory with controlled/natural branches, dashed offline audit metadata path, center base verifier plus hidden residual/MLP/token-mixer monitor, risk-trigger gate, right second verifier, and a warning arrow for objective/threshold/readout/answer-anchor mismatch. / 系统图应画出 trace 工厂、离线审计、基线 verifier、hidden monitor、风险触发门、二次 verifier 和错配风险箭头。

## 23. 2026-04-30 E139 Check-Rationale Audit / 二次检查解释审计

- Runner / 运行脚本：`scripts/run_e139_check_rationale_audit.py`
- Queue / 队列脚本：`scripts/launch_e139_check_rationale_audit_queue_20260430.sh`
- Summary / 汇总脚本：`scripts/summarize_e139_check_rationale_audit.py`
- Report / 报告：`reports/E139_CHECK_RATIONALE_AUDIT_20260430.md`
- JSON / 机器可读结果：`reports/E139_CHECK_RATIONALE_AUDIT_20260430.json`
- Results / 结果目录：`results/E139_check_rationale_audit/`
- Status / 状态：three Qwen/Gemma P0 models completed; queue wrote `all_done` at `2026-04-30T20:37:36`. / 三个 Qwen/Gemma P0 模型均完成，队列在该时间写出 `all_done`。
- Scope / 范围：per user instruction, E139 only audits E136 rows where base or check failed to reject a strict-invalid trace. It does not include already-corrected rows. / 按用户要求，E139 只审计 E136 中 base 或 check 没有成功拒绝 strict-invalid trace 的失败样本，不混入已纠错样本。
- Mode / 模式：`non-thinking` generated rationale audit only. Thinking smoke consumed the output budget before emitting the required final audit block, so thinking E139 is deferred to a separate final-contract design. / 本轮只做非 thinking 的解释式审计；thinking 冒烟在输出最终审计块前耗尽预算，因此 thinking 版本暂缓。
- Design / 设计：the prompt asks for two separate decisions: `Strict decision` under trace-as-proof and `Repair-aware decision` under final surviving proof. Prompts contain only problem, visible trace, and optional hidden-selected visible excerpt; manual labels, gold answers, and error-span annotations are offline only. / prompt 同时要求严格证明口径和可修复草稿口径两个判定；prompt 只含题目、可见 trace 和可选的 hidden 选中片段，人工标签、答案和错误 span 只离线使用。
- Selected rows / 选样：Qwen selected 4 rows, Gemma31 selected 3 rows, Gemma26-A4B selected 6 rows; all are `percentage_base::repaired_strict_invalid`. / Qwen 选中 4 条、Gemma31 3 条、Gemma26-A4B 6 条；全部是百分比基底任务的 repaired strict-invalid。
- Main fact / 主要事实：across 26 generated global/local audit jobs, parse success was 26/26, wrong-step quotation was 26/26, strict accept was 0/26, and repair-aware accept was 23/26. / 26 个 global/local 解释任务中，解析成功 26/26，指出错步 26/26，strict 口径接受 0/26，repair-aware 口径接受 23/26。
- By model / 按模型：Qwen strict Yes 0/8 and repair-aware Yes 5/8; Gemma31 strict Yes 0/6 and repair-aware Yes 6/6; Gemma26-A4B strict Yes 0/12 and repair-aware Yes 12/12. / Qwen strict 0/8、repair-aware 5/8；Gemma31 strict 0/6、repair-aware 6/6；Gemma26-A4B strict 0/12、repair-aware 12/12。
- Plain explanation / 说人话解释：these failed rows are not failures to see the wrong step. The models can identify the wrong percentage-increase statement, but often judge that later correct arithmetic repaired or discarded it, so the final repair-aware answer is accepted. / 这些失败样本不是“模型看不见错步”；模型能指出错误的百分比语义句，但常认为后文正确计算已经修复或丢弃了错误，因此按 repair-aware 口径接受。
- Claim update / 主张更新：E139 strengthens the objective/readout mismatch claim. Hidden or local checks can select high-risk traces, but the second-pass verifier must be forced into the intended evaluation policy; otherwise it may read CoT as a repairable draft rather than strict proof. / E139 强化 objective/readout 错配主张：hidden/local check 能选中高风险 trace，但二次 verifier 必须被约束到目标评价口径，否则会把 CoT 当可修复草稿而非严格证明。
- Explicit record / 明确记录：模型能指出错步，但很多时候会认为后文正确计算已经把错步修复/丢弃，所以按 repair-aware 口径继续接受。这把工作做得更 solid：hidden/local check 能选中高风险 trace，但二次 verifier 的 objective/readout 如果没有被严格约束，仍会把 CoT 当“可修复草稿”而不是“严格证明”。/ The model can identify the wrong step, but often treats later correct arithmetic as repairing or discarding it, and therefore continues to accept under a repair-aware rubric. This makes the work more solid: hidden/local checks can select high-risk traces, but if the second verifier's objective/readout is not tightly constrained, it may read CoT as a repairable draft rather than a strict proof.
- Boundary / 边界：E139 explains an E136 failure cluster and is not a natural prevalence estimate. The selected cluster is narrow, so the next step should expand the same rationale audit to more task families and natural repaired/unrepaired ACPI rows. / E139 解释的是 E136 的失败簇，不是自然发生率估计；当前簇较窄，下一步应扩展到更多任务族和自然 repaired/unrepaired ACPI 行。
- Planned E139.5 / 计划实验 E139.5：test whether the same model can localize the wrong step under a base/no-check setting and under strengthened locate-only prompts. The key distinction is whether the model can output the error span before being invited to make a repair-aware global judgment. / 检验同一模型在 base/no-check 条件和加强版“只找错步”prompt 下是否仍能定位错步；关键是把“能不能先圈出错步”与“是否按 repair-aware 全局口径接受”分开。

## 24. 2026-04-30 E139.5 Base Span Localization Format-Fixed / 基线错步定位与格式修复

- Runner / 运行脚本：`scripts/run_e1395_base_span_localization.py`
- Report / 报告：`reports/E1395_BASE_SPAN_LOCALIZATION_FORMAT_FIXED_20260430.md`
- JSON / 机器可读结果：`reports/E1395_BASE_SPAN_LOCALIZATION_FORMAT_FIXED_20260430.json`
- Adopted results / 采纳结果：`results/E1395_base_span_localization_format_fixed/`
- Debug archive / 调试归档：`archive/e1395_format_debug_20260430/results/`
- Status / 状态：Qwen3.5-27B, Gemma4-31B-it, and Gemma4-26B-A4B-it completed with the same format-fixed prompts; no tmux/GPU process remains. / 三个模型使用同一版修复 prompt 完成；无残留训练/推理进程。
- Why rerun / 为什么重跑：the first Gemma31 E139.5 output usually contained a valid first answer and then repeated `thought + same answer` until `max_new_tokens`, polluting `hit_max` and JSON parsing. Those pre-fix Gemma31 results are not adopted for final comparison. / 旧 Gemma31 输出常先给出有效答案再重复到 token 上限，污染格式指标和 JSON 解析，因此不进入最终横向比较。
- Format fix / 格式修复：stop generation at the first `</SPAN_AUDIT>` or first JSON closing brace; force block prompts to produce exactly one final block; parse the first balanced JSON object instead of first-left-brace to last-right-brace. / 生成在首个答案块或首个 JSON 右括号处停止；prompt 强制只输出一个最终块；JSON 解析只取第一个完整对象。
- Leakage audit / 泄露审计：prompts contain only problem and visible candidate solution. Manual labels, gold answers, and expected spans are offline selection/evaluation metadata only. / prompt 只含题目和可见候选解；标签、答案、span 只离线使用。
- Format outcome / 格式结果：all three adopted runs have `parse_ok=1.0` and `hit_max=0.0`. / 三个采纳结果均解析成功且没有打满输出上限。
- Qwen fact / Qwen 事实：invalid span hit 11/12 = 0.917, Wilson 95% CI [0.646, 0.985]; valid false error 0/36 = 0.000, CI [0.000, 0.096]. / Qwen 基本能直接定位错步，正确控制组未误报。
- Gemma31 fact / Gemma31 事实：invalid span hit 6/9 = 0.667, CI [0.354, 0.879]; valid false error 0/27 = 0.000, CI [0.000, 0.125]. It catches en_zh and mixed but misses romanized_zh. / Gemma31 能抓 en_zh 和 mixed，但稳定漏掉 romanized_zh；这不是格式问题，而是语言路径/语义边界。
- Gemma26 fact / Gemma26 事实：invalid span hit 14/18 = 0.778, CI [0.548, 0.910]; valid false error 3/54 = 0.056, CI [0.019, 0.151]. It has both mixed-language misses and romanized valid-control false errors. / Gemma26 能抓不少错步，但同时存在 mixed 漏检和 romanized 正确控制组误报。
- Claim update / 主张更新：E139.5 supports the claim that the model often has enough information to point to the wrong step before a global verifier decision. E136/E139 failures are therefore not simply absence of process evidence; they are about how the objective/readout uses or ignores that evidence. / E139.5 支持“模型常能先圈出错步”的更窄机制主张；E136/E139 的失败不是单纯没有过程证据，而是 objective/readout 如何使用这份证据。
- Boundary / 边界：locate-only ability is not an oracle. Romanized Chinese and mixed-language traces expose route sensitivity, and Gemma26 false positives show calibration is necessary. / 只定位能力不是 oracle；罗马拼音中文和混合语言暴露路径敏感性，Gemma26 的误报说明必须校准。

## 25. 2026-04-30 E137-E140 Adaptive Natural Check / 自然样本 hidden 触发与二次检查

- Report / 报告：`reports/E137_E140_ADAPTIVE_NATURAL_CHECK_SYNTHESIS_20260430.md`
- JSON / 机器可读摘要：`reports/E137_E140_ADAPTIVE_NATURAL_CHECK_SYNTHESIS_20260430.json`
- Scripts / 脚本：`scripts/run_e137_hidden_trigger_threshold_calibration.py`, `scripts/run_e138_natural_hidden_trigger_check.py`, `scripts/run_e140_natural_check_rationale_audit.py`
- Results / 结果：`results/E137_hidden_trigger_threshold_calibration/`, `results/E138_natural_hidden_trigger_check/`, `results/E140_natural_check_rationale_audit/`
- Mode / 模式：all runs are `NG`, `thinking=false`. / 全部为非 thinking。
- Leakage boundary / 泄露边界：E137 is offline threshold evaluation only. E138/E140 prompts contain only problem, visible trace, and optional hidden-trigger-selected visible excerpt; labels, gold answers, and manual error spans are offline only. E138 uses E131 diagnostic prefixes, so it is not a deployable online monitor. / E137 只做离线阈值评估。E138/E140 prompt 不含标签、答案、人工错误 span。E138 使用 E131 诊断前缀，因此不是可部署在线监控。
- E137 Qwen fact / Qwen 阈值事实：threshold 0 gives invalid recall 12/12 and valid false trigger 2/48; chosen threshold -5.170 gives invalid recall 12/12 and valid false trigger 0/48, but later proves too conservative on natural transfer. / Qwen 受控行可校准，但自然迁移时阈值过保守。
- E137 Gemma31 fact / Gemma31 阈值事实：threshold 0 is already clean: invalid recall 12/12 and valid false trigger 0/48. / Gemma31 阈值最干净。
- E137 Gemma26 fact / Gemma26 阈值事实：threshold 0 gives invalid recall 12/12 but valid false trigger 6/48; no threshold satisfies the strict planned low-FP constraints. / Gemma26 能抓 invalid，但误触发正确控制组更多。
- E138 Qwen natural fact / Qwen 自然事实：24 rows, 19 repaired ACPI and 5 strict-valid. Base invalid accept is 2/19; threshold 0 triggers all 19 repaired ACPI and one valid row; zero strict-local reduces invalid accept to 0/19 while retaining valid accept 5/5. / Qwen 支持 hidden 触发加 strict 局部检查。
- E138 Gemma31 natural fact / Gemma31 自然事实：26 rows, 16 repaired ACPI and 10 valid. Base invalid accept is 6/16; threshold 0 triggers all repaired rows and 1/10 valid rows; strict-local reduces invalid accept to 2/16. Default-local is worse because it reads repaired CoT more permissively. / Gemma31 支持 strict 口径，但 default/local 会 repair-aware 化。
- E138 Gemma26 natural fact / Gemma26 自然事实：16 rows, 8 repaired ACPI, 2 unrepaired ACPI, 6 valid. Base invalid accept is 6/10. Threshold 0 triggers all invalid rows, including both unrepaired rows, but strict-local still accepts 5/10 invalid and 2/2 unrepaired. E137 chosen threshold misses both unrepaired rows. / Gemma26 是关键边界：hidden 响了，但局部语义检查仍失败。
- E140 Qwen rationale fact / Qwen 解释事实：8 audit jobs, parse 8/8, error recognized 8/8, strict accept 0/8, repair-aware accept 5/8. / Qwen 能看见错步；repair-aware 仍可能接受。
- E140 Gemma31 rationale fact / Gemma31 解释事实：20 jobs, parse 20/20, error recognized 8/20, strict accept 12/20, repair-aware accept 20/20. / Gemma31 局部范围有帮助，但仍常说没错，且 repair-aware 全接受。
- E140 Gemma26 rationale fact / Gemma26 解释事实：20 jobs, parse 20/20, error recognized 2/20, strict accept 15/20, repair-aware accept 19/20. On the two unrepaired ACPI rows, 4/4 audit jobs recognized no error and accepted under both strict and repair-aware decisions. / Gemma26 未修复两例是更深的语义局部检查失败。
- Claim update / 主张更新：natural repaired ACPI in Qwen/Gemma31 often carries hidden process-risk signals, and strict second-pass objectives can use them. But hidden trigger is not a complete error oracle: threshold transfer, language route, repair-aware reading, readout, and local semantic competence decide whether evidence becomes a correct rejection. / 自然 repaired ACPI 中常有 hidden 风险信号，strict 二次检查能利用它；但 hidden 触发不是完整 oracle，阈值迁移、语言路径、repair-aware 阅读、读出和局部语义能力共同决定是否正确拒绝。
- Key negative case / 关键反例：Gemma26 unrepaired ACPI shows that a hidden risk signal can fire while the same model still fails to name the algebraic error and accepts the trace. This strengthens the paper by preventing overclaiming: the mechanism is evidence-to-decision mismatch plus model-family/local-competence boundaries, not a universal hidden-error detector. / Gemma26 未修复 ACPI 显示 hidden 信号可以响，但模型仍不能指出代数错步并接受 trace；这要求我们避免把 hidden probe 说成 universal detector。
- Next / 下一步：E141 rationale taxonomy from E140 outputs; E142 online trigger scaffold without label-informed prefixes; E144 caution-token intervention; Gemma26 unrepaired activation/prompt deep dive. / 下一步做解释失败分类、无标签在线触发脚手架、警示 token 干预、Gemma26 未修复深挖。

## 26. 2026-04-30 E147-E152 Non-Thinking Unrepaired ACPI Pipeline / non-thinking 未修复 ACPI 诱发与方法验证流程

- Plan / 计划：`reports/E147_E152_NONTHINKING_UNREPAIRED_ACPI_PLAN_20260430.md`
- Manifest / 清单：`configs/e147_e152_nonthinking_unrepaired_manifest.yaml`
- Task builder / 任务构造：`scripts/build_e147_unrepaired_acpi_induction_tasks.py`
- Generation runner / 生成脚本：`scripts/run_e147_unrepaired_acpi_induction_generation.py`
- Audit-sheet builder / 审计表构建：`scripts/build_e147_final_correct_audit_sheet.py`
- Smoke / 冒烟：`scripts/smoke_e147_e152_nonthinking_scaffold.py`
- Phase-A launcher / 第一阶段队列：`scripts/launch_e147_unrepaired_induction_phaseA_queue_20260430.sh`

Execution rule / 执行规则：

1. Every experiment must first write a concrete pipeline and mode boundary into history. / 每个实验先在 history 写清楚具体 pipeline 和模式边界。
2. Run static audit before model execution: `py_compile`, launcher `bash -n`, and active workspace audit after whitelisting official artifacts. / 模型运行前先做静态审计。
3. Run no-GPU smoke and inspect the first sample/prompt for leakage and scientific fit. / 先做无 GPU smoke，并抽第一个样本/prompt 检查是否符合需求。
4. If the first sample is valid, run a one-row model smoke when the experiment involves generation. / 若首样本有效，涉及生成的实验再跑一条模型 smoke。
5. Only after these checks pass should the formal queue start. / 这些检查通过后才启动正式队列。

E147 purpose / E147 目的：

E147 is a discovery grid, not a natural prevalence benchmark. It constructs tasks where a locally wrong process can plausibly leave the final answer unchanged, then samples non-thinking generations from core P0 models. / E147 是发现网格，不是自然发生率基准。它构造一些“局部过程错但最终答案可能不变”的任务，再让核心 P0 在 non-thinking 模式下生成。

Pipeline / 具体流程：

1. Build 32 tasks: 8 families × 4 tasks. Families are sign-symmetry algebra, invariant counting, complement symmetry, percentage roundtrip, unit roundtrip, code boundary, table aggregation, and multilingual semantic traps. / 构造 32 个任务：8 个任务族，每族 4 个。
2. Each task stores gold answer, risk pattern, and trap note only as offline metadata. Prompts contain only the problem text. / 每题的答案、风险模式和 trap note 只离线保存；prompt 只放题目。
3. Generate with `NG`, `thinking=false`, core P0 only in Phase A: Qwen35-27B, Gemma4-31B-it, Gemma4-26B-A4B-it. GLM waits for Phase B. / Phase A 只跑核心 P0，GLM 后置。
4. Use four no-gold prompt variants: neutral, answer-first-no-gold, terse-solution, and short-self-check. / 使用四种无答案 prompt。
5. Phase-A k=1 yields 32 × 4 × 3 = 384 generations. k=2 expansion yields 768 generations. / k=1 是 384 条，k=2 是 768 条。
6. Build final/fallback-correct audit sheet from generated rows. Gold answer is used only offline for filtering. / 生成后只用离线答案筛 final/fallback-correct 审计表。
7. Later structured process audit labels rows as strict-valid, repaired ACPI, unrepaired ACPI, or fallback/truncation boundary. Formal double audit remains deferred. / 后续结构化过程审计标 strict-valid、repaired、unrepaired 或边界；正式双审后置。

Important prompt boundary / 重要 prompt 边界：

`answer_first_no_gold` is now explicitly treated as an answer-anchor/commitment stress condition, not primary evidence for natural reasoning-before-answer unrepaired ACPI. It tests whether a model that commits to an answer first can produce a contaminated post-hoc rationale. This is relevant to trace-selection and data-curation risk, but it must be reported separately from `neutral`, `terse_solution`, and `self_check_short`, which are the primary reasoning-first prompt families for broad induced unrepaired-ACPI evidence. / `answer_first_no_gold` 现在明确只作为答案锚定/先承诺压力条件，不作为“自然先推理后给答案”的 unrepaired ACPI 主证据。它测试模型先承诺答案后是否会生成被污染的事后理由；这对 trace selection 和数据治理有意义，但必须与 `neutral`、`terse_solution`、`self_check_short` 分开报告，后三者才是广义诱发 unrepaired ACPI 的主 prompt。

Scientific interpretation / 科学解释：

- If more unrepaired ACPI rows are found across families, the paper can claim broad induced vulnerability rather than high natural prevalence. / 如果找到更多未修复 ACPI，论文可主张“广泛可诱发风险”，而不是“自然高频发生”。
- If hidden-triggered strict checks reduce acceptance on these induced rows, the method claim becomes broader than the original Gemma26 two-row boundary. / 如果 hidden 触发 strict 检查能降低这些诱发样本的接受率，方法贡献就不局限于原来的两个 Gemma26 个案。
- If some families fail, those failures define the boundary and guide E150/E151 interpretability analysis. / 如果某些任务族失败，它们就是边界，并进入 E150/E151 可解释性分析。

Static and smoke status / 静态与冒烟状态：

- `py_compile` passed for the E147 task builder, generation runner, audit-sheet builder, smoke script, and active-workspace audit script. / E147 相关 Python 脚本编译通过。
- `bash -n scripts/launch_e147_unrepaired_induction_phaseA_queue_20260430.sh` passed. / 队列脚本语法检查通过。
- The task-bank smoke passed: 32 tasks, 8 families × 4 tasks, 4 routes evenly distributed, expected k=1 core-P0 Phase-A generations = 384. / 任务库冒烟通过。
- First task/prompt inspection: `e147_code_boundary_1_en`, prompt contains only the Python code problem; gold answer `-56`, risk pattern, and trap note are offline metadata only. / 首样本检查通过：prompt 只含题目，不含答案或 trap。
- One-row Qwen model smoke passed on `answer_first_no_gold`: no leakage, `thinking=false`, no hit-max, explicit final marker found, final extracted answer `-56`. The completion first wrote `Final answer: -42`, then recalculated and ended with `Final answer: -56`, so the smoke already induced a repaired strict-ACPI boundary case. / Qwen 单条模型冒烟通过，并已诱发“先错后修”的 repaired strict-ACPI 边界样本。

Decision / 决策：

E147 Phase-A can start formally because static audit, no-GPU smoke, first-sample inspection, and one-row model smoke all passed. / 静态审计、无 GPU 冒烟、首样本检查和单条模型冒烟均通过，因此 E147 Phase-A 可以正式启动。

## 27. 2026-05-01 E147 Paused and E153-E158 Redesign / 暂停 E147 并重设计 E153-E158

- User decision / 用户决策：pause the E147 queue and redesign around natural non-thinking difficult scenarios, structured audit, mutation probes, prefill hidden localization, natural error-finding, and hidden-assisted repair. / 暂停 E147 队列，改为围绕自然 non-thinking 困难场景、结构化审计、篡改探针、prefill hidden 定位、自然找错和 hidden 辅助修复来设计。
- Queue status / 队列状态：`p02_e147_phaseA_20260430` was stopped; no tmux session remains. / E147 队列已停止，无残留 tmux。
- Debug rows / 调试样本：24 Qwen checkpoint rows plus one smoke row exist, but they are debug-only and not formal Phase-A evidence. / 已有 24 条 Qwen checkpoint 与 1 条 smoke，仅作 debug。
- Debug audit / 调试审计：`reports/E147_ANSWER_FIRST_DEBUG_TRACE_AUDIT_20260501.md` and `.json`. / answer-first 调试审计已落盘。
- Redesign plan / 新方案：`reports/E153_E158_NONTHINKING_DIFFICULT_SCENARIO_REDESIGN_20260501.md`.

Answer-first debug finding / answer-first 调试发现：

- 25 debug rows total; 7 are `answer_first_no_gold`. / 共 25 条调试行，其中 7 条 answer-first。
- 4/7 answer-first rows changed from an initial final answer to a later correct final answer. / 7 条 answer-first 中 4 条先提交一个答案，后续改成正确答案。
- 14/25 rows contain self-check/correction markers, and 2 contain explicit wrong/mistake markers. / 25 条中 14 条含自检/纠错 marker，2 条显式提到 wrong/mistake。
- Interpretation: answer-first rows are useful for answer commitment, repair-awareness, and error-awareness probes, but they are not primary evidence for natural reasoning-first unrepaired ACPI. / 解释：answer-first 行适合研究答案承诺、修复意识和错误意识，但不能作为自然先推理后答案的 unrepaired ACPI 主证据。

New experiment logic / 新实验逻辑：

1. E153 collects diverse reasoning-first non-thinking traces and separate non-thinking natural error-finding traces. / E153 采集多样化先推理后答案 trace，并单独采集 non-thinking 自然找错行为。
2. E154 performs structured process audit, including self-check markers and correction counts. / E154 做结构化过程审计，包括自检 marker 和纠错次数。
3. E155 builds mutation/probe sets from high-quality valid or lightly wrong traces. / E155 从高质量正确或轻度错误 trace 构造篡改/探针集。
4. E156 runs prefill hidden localization on original and mutated traces. / E156 对原始和篡改 trace 做 prefill hidden 定位。
5. E157 tests blind, hidden-window, and oracle-span non-thinking error-finding/repair. / E157 测 blind、hidden-window 和 oracle-span 的 non-thinking 找错/修复。
6. E158 writes explainability case cards. / E158 写可解释性个案卡。

E153 concrete pipeline / E153 具体 pipeline：

1. Build a 32-task difficult-scenario bank with 16 families × 2 tasks: algebra sign/factor, counting invariant, code boundary, table aggregation, unit/percentage, multilingual semantic, proof validity, probability conditioning, graph/path constraints, geometry constraints, recurrence/DP, string/regex parsing, temporal/order, causal/counterfactual, set/Venn, and optimization constraints. / 构造 32 题困难场景库，覆盖 16 类场景，每类 2 题。
2. For every task, store one valid reference solution and one invalid reference solution offline, giving 64 candidate-solution rows. / 每题离线保存一条正确参考解和一条错误参考解，共 64 条候选过程。
3. E153 generation asks each core P0 model to solve only from the problem text in non-thinking mode, with three reasoning-first prompts: `solve_neutral`, `solve_terse`, and `solve_self_check`. Gold answers and manual labels are never shown. / E153 生成实验只给题目，不给答案和人工标签；三种 prompt 都要求先推理后最终答案。
4. E153 error-finding asks each core P0 model, still in non-thinking mode, to inspect candidate solutions and output `ERROR`, `LOCATION`, and optionally `REASON`. The prompt contains the problem and proposed solution only; offline labels and error spans are not shown. / E153 找错实验仍是 non-thinking，只给题目和候选解，让模型判断是否有错误并定位。
5. Automatic generation metrics are only final-answer extraction, final-marker presence, and truncation. Process-validity, ACPI, self-check markers, and correction counts require E154 structured audit. / 生成自动指标只看最终答案、final marker 和截断；过程对错、ACPI、自检和纠错次数交给 E154 审计。
6. Automatic error-finding metrics are split into `pred_correct` and `location_matches_error_span`. `pred_correct` means the model says whether any error exists; `location_matches_error_span` means the reported location overlaps the offline manual error span. / 找错指标分成“有没有承认有错”和“是否定位到人工错步”，不能混为一谈。

Static audit and smoke / 静态审计与冒烟：

- Fixed builder bug: `build_e153_difficult_scenario_bank.py` used an undefined `etype`; it now correctly writes `error_type`. / 修复样本库脚本变量错误。
- Removed a dead E147 render branch from `run_e153_nonthinking_difficult_scenario_generation.py`; behavior stays `_render_chat(... enable_thinking=False)`. / 清理生成脚本死分支，行为不变。
- Added offline `location_matches_error_span` to `run_e153_nonthinking_error_finding.py` after first-sample audit showed that binary error detection and exact localization can diverge. / 增加离线定位命中指标，因为首样本显示“知道有错”和“知道错在哪里”会分离。
- `py_compile` passed for E153 builder, generation runner, error-finding runner, scaffold smoke, and active-workspace audit; `bash -n scripts/launch_e153_phaseA_smoke_and_generation_20260501.sh` passed. / E153 相关 Python 编译和 launch 脚本语法检查通过。
- `scripts/build_e153_difficult_scenario_bank.py` produced 32 tasks and 64 candidate solutions; leakage policy passed with no gold answer, manual label, trap note, or error span in prompts. / 样本库生成通过，无泄漏。
- `scripts/smoke_e153_e158_scaffold.py` passed; first task is `e153_algebra_sign_factor_01`; first generation prompt contains only the quadratic counting problem; first error-finding prompt contains only the problem and proposed solution. / scaffold 冒烟通过，首样本 prompt 检查通过。
- One-row Qwen generation smoke with `max_new_tokens=1024` hit the token cap and missed the final marker, so it was treated as insufficient smoke. The same sample with the formal 4096-token cap passed: no truncation, final marker found, extracted final answer `117`, final-correct true. / 1024 token 冒烟被截断，不能算正式通过；4096 token 重跑通过。
- One-row Qwen error-finding smoke passed the binary label but failed exact localization: `pred_correct=1`, `location_matches_error_span=0`. The model said `ERROR: Yes` but pointed to the counting sentence instead of the wrong factorization `(3x-2y)(4x+3y)`, and its reason contained an incorrect repaired answer. / 找错首样本二分类正确但定位错误：模型知道“有问题”，但没有找到真正错步，还给出错误修复理由。
- Scientific use of this first sample: keep it as a process-error sample, not a wrong-answer repair sample. It is valuable precisely because the invalid reference has a wrong factorization while the final answer happens to match the gold answer. / 首样本保留为“过程错但答案碰巧对”的过程验证样本，不作为 wrong-answer repair 样本。
- Active workspace audit passed after E153 artifacts and smoke checkpoint logs were whitelisted. / 官方 workspace audit 通过。

Formal start / 正式启动：

- Started tmux session `p02_e153_phaseA_20260501` with `scripts/launch_e153_phaseA_smoke_and_generation_20260501.sh`. / 已启动正式 E153 Phase-A 队列。
- Launcher sequence: rebuild bank -> scaffold smoke -> Qwen35-27B generation -> Gemma4-31B-it generation -> Gemma4-26B-A4B-it generation -> Qwen35-27B error-finding -> Gemma4-31B-it error-finding -> Gemma4-26B-A4B-it error-finding. / 队列顺序为先重建样本库和 scaffold 冒烟，再依次跑三模型生成与三模型找错。
- Expected formal outputs: 288 generation rows = 32 tasks × 3 prompts × 3 models; 384 error-finding rows = 64 candidate solutions × 2 prompts × 3 models. / 预期正式输出为 288 条解题生成和 384 条找错输出。
- Early checkpoint audit after Qwen generation began: first 8 rows had 8/8 final-correct, 0 missing final marker, 0 hit-max, and 0 prompt-leakage rows. This is only a queue-health check, not a scientific result. / Qwen 生成早期 8 条 checkpoint 健康检查正常；这只是运行健康检查，不是科学结论。

Dense generation audit / dense 解题生成审计：

- Artifacts / 产物：`scripts/audit_e153_dense_generation.py`, `data/processed/e153_dense_generation_audit_20260501.jsonl`, `results/E153_nonthinking_difficult_scenario_generation/e153_dense_generation_audit_summary_20260501.json`, `reports/E153_DENSE_GENERATION_AUDIT_20260501.md`.
- Scope / 范围：only completed dense generation outputs, Qwen35-27B and Gemma4-31B-it. MoE Gemma4-26B-A4B-it is explicitly kept separate because expert routing may add instability. / 只审计已完成的 dense 生成结果；MoE Gemma 单独分析。
- Definitions / 定义：`causal_prefill_usable` means the visible trace order can be used for causal prefill analysis; `clean_valid_prefill_candidate` is a stricter seed pool for main valid-trace mutation/prefill work; `language_trait_use` preserves traces useful for studying language behavior even if they are not clean causal-prefill seeds. / 新增三个字段，分别服务因果 prefill、主种子池和语言特质分析。
- Qwen35-27B result / Qwen 结果：96/96 rows are manually final-correct after normalizing quoted strings and unit suffixes; 89/96 are clean valid prefill candidates; 19/96 are language-trait traces; 0 unrepaired ACPI found. / Qwen 人工最终答案全对，89 条适合作主 prefill 种子，19 条适合语言特质分析，未发现未修复 ACPI。
- Gemma4-31B-it result / Gemma dense 结果：93/96 rows are manually final-correct; 90/96 are clean valid prefill candidates; 14/96 are language-trait traces; 0 unrepaired ACPI found. / Gemma dense 人工最终答案 93/96，90 条适合作主 prefill 种子，14 条适合语言特质分析，未发现未修复 ACPI。
- Parser boundary / 解析边界：11 automatic false negatives are not model failures: quoted string answers like `'bcd'` and unit suffix answers like `120m` or `120 meters` should count as correct. / 11 条自动假错来自答案归一化问题。
- Main dense failure / dense 主失败：Gemma4-31B-it fails `e153_multilingual_semantic_01` under all three prompts by misreading romanized Chinese `zhi duo wei 4` as value/digit/tens/units conditions instead of `at most 4`. This is a high-value multilingual semantic robustness and language-trait sample. / Gemma dense 在拼音语义题三种 prompt 全错，属于高价值多语言语义误读样本。
- Scientific interpretation / 科学解释：in this E153 generation setting, dense models mostly solve sequentially and correctly; natural unrepaired ACPI did not appear. The stronger signal so far is a separation between generation competence and error-localization competence: the first sample can be solved correctly from scratch, while non-thinking error-finding recognized a problem but localized it poorly. / dense 生成阶段主要显示“顺序解题能力强、自然未修复 ACPI 未出现”；更有意思的是“能解题”和“能定位错误”分离。

MoE generation audit / MoE 解题生成审计：

- Artifacts / 产物：`scripts/audit_e153_moe_generation.py`, `data/processed/e153_moe_generation_audit_20260501.jsonl`, `results/E153_nonthinking_difficult_scenario_generation/e153_moe_generation_audit_summary_20260501.json`, `reports/E153_MOE_GENERATION_AUDIT_20260501.md`.
- Scope / 范围：Gemma4-26B-A4B-it only, kept separate from dense models because MoE routing can introduce architecture-specific variance. / 只审计 Gemma4-26B-A4B-it，不和 dense 模型混合统计，因为 MoE 路由可能带来额外不稳定性。
- Result / 结果：96/96 rows are causal-prefill usable; 95/96 are manually final-correct after normalizing answer format; 95/96 are clean valid prefill candidates; 15/96 are language-trait traces; 0 unrepaired ACPI found. / 96 条都可作顺序 prefill 分析；归一化后 95 条人工最终正确，95 条适合作主 prefill 种子，15 条适合语言特质分析，未发现未修复 ACPI。
- Boundary case / 边界样本：the only non-normalization disagreement is `e153_graph_path_constraints_02` under `solve_neutral`. The model answers `No` because the prompt did not state graph connectivity; a disconnected graph with a triangle plus a separate edge has degrees `1,1,2,2,2` and no Euler trail over all edges. This challenges the task wording/gold assumption rather than showing a clean model failure. / 唯一非格式分歧是图论连通性边界：题目没说明连通，模型给出反例，因此不是干净的模型错。
- Scientific interpretation / 科学解释：MoE generation agrees with dense generation on the main point: natural reasoning-first unrepaired ACPI did not appear in this E153 generation setting. Its current value is boundary sensitivity and future routing-stability analysis, not evidence of broad natural unrepaired ACPI prevalence. / MoE 与 dense 一致：当前自然先推理后答案的生成设置下，没有发现未修复 ACPI；MoE 目前更适合做边界敏感性和路由稳定性分析。

Answer to current design questions / 当前设计问题的回答：

- Previous unrepaired ACPI construction / 旧的未修复 ACPI 如何来：there were two routes. Controlled ACPI rows were deliberately constructed as paired traces: same problem and same final answer, but one trace contains a local wrong semantic/math step. These are mechanism probes, not prevalence estimates. Natural unrepaired ACPI rows were found by auditing hard-task non-thinking generations, especially Gemma4-26B-A4B integer-pair answer-first traces where a wrong factorization was not repaired but the final count stayed correct because of sign/count symmetry. / 旧样本有两类：一类是人为受控构造，用于机制验证；另一类是自然生成后审计发现，典型是 Gemma4-26B-A4B 在整数对题中写出错误因式分解但最终计数因对称性仍正确。
- Source of the current 96 prompts / 本次 96 个 prompt 来源：for each model, E153 uses 32 tasks from `build_e153_difficult_scenario_bank.py` and 3 generation prompt variants (`solve_neutral`, `solve_terse`, `solve_self_check`), so 32 × 3 = 96 prompts. The prompt contains only the problem text and reasoning-first instruction; gold answers, manual labels, trap notes, and error spans are offline and not shown. / 每个模型 96 个 prompt = 32 道题 × 3 种先推理后答案 prompt；prompt 只含题目，不含答案、标签、陷阱说明或错误位置。
- Why natural unrepaired ACPI did not appear / 为什么没有自然未修复 ACPI：this is not only because the scenarios are “not hard enough,” and not because only mutation can ever produce ACPI. Natural unrepaired ACPI requires a narrow conjunction: the model must make a plausible local error, fail to repair it, and still land on the correct final answer because the task has answer-preserving symmetry, cancellation, ambiguity, or format tolerance. If the task is too easy, the model solves cleanly; if it is too hard, it often produces wrong-answer traces rather than answer-correct/process-invalid traces. Mutation is efficient because it directly inserts an answer-preserving local error into an otherwise good trace. / 没出现并不只是因为题不够难，也不是说只有篡改才会有 ACPI。自然未修复 ACPI 需要“局部错、没修、最终答案仍对”同时成立；简单题会干净做对，过难题更容易答案也错。篡改高效，是因为它直接把保答案的局部错误插进好 trace。
- Current claim boundary / 当前 claim 边界：E153 generation supports a broad seed pool for later mutation/prefill and shows a separation between solving competence and error-localization competence. It does not yet support a claim that natural unrepaired ACPI is frequent across diverse scenarios. / E153 生成阶段支持“我们有大量高质量顺序 trace 种子”和“解题能力与找错定位能力可分离”，但还不能主张自然未修复 ACPI 在多场景下高频存在。

Hidden-state observation policy / 隐藏层观测策略：

- Main policy / 主策略：save activations after audit by teacher-forced replay. In plain terms, after we know which trace is clean-valid, mutated-invalid, naturally wrong, repaired, or ambiguous, we replay the exact prompt+trace prefix through the model and save residual stream, MLP output, token-mixer/attention output, norm output, and label/readout scores at predefined prefix points. / 主线采用“审计后重放保存”：先知道样本类型，再把同一段 prompt+trace 按固定前缀喂回模型，保存 residual、MLP、attention/token-mixer、norm 和读出分数。
- Reason / 理由：teacher-forced replay fixes the token sequence, prefix boundary, batch design, and label, so the hidden-state comparison is causal and reproducible. It avoids mixing generation sampling noise with the internal signal we want to study. / 这样能固定 token 序列、前缀位置、batch 设计和标签，避免把生成采样噪声混进隐藏层信号，是更干净的可解释性证据。
- Online saving / 在线保存：do not save every layer for every generated token by default. Full online activation dumps are expensive, hard to compare across variable-length traces, and mostly store un-audited noise. Keep only a small sentinel online set: first sample per family/model, known high-risk families, and any row with parser failure, truncation, explicit repair marker, answer flip, or abnormal verifier/readout score. / 不默认全量在线存每层每 token，成本高且大多是未审计噪声；只保留少量哨兵在线样本，包括每类首样本、高风险题、解析失败、截断、显式修复、答案翻转或读出异常的行。
- Threshold-triggered saving / 阈值触发保存：use thresholds as a sampling aid, not the only rule. If a residual/readout score crosses a pre-registered high-risk threshold, save compact prefix activations and metadata, but still keep a stratified random baseline and all manually important cases. Otherwise threshold-only sampling would bias the scientific claim toward cases the current probe already detects. / 阈值可以当采样助手，但不能当唯一规则；超过预注册阈值就保存紧凑前缀激活和元数据，同时保留分层随机基线和人工重要样本，否则会把选择偏差带进论文。
- Concrete next implementation / 具体下一步：E156 should be an E153-specific wrapper around the existing E90/E131 hidden-cache machinery. It should read `e153_dense_generation_audit_20260501.jsonl`, `e153_moe_generation_audit_20260501.jsonl`, and later error-finding audits; select clean-valid seeds, mutated invalid traces, natural failures, and localization failures; then save `.pt` activation caches at error span end, post-error window, self-check/repair marker, final-answer line, and completion end. / E156 应复用 E90/E131 的 hidden-cache 机制，读取 E153 审计表，选择干净正确种子、篡改错误 trace、自然失败和定位失败样本，在错步后、错后窗口、自检/修复、最终答案和结束处保存 `.pt` 激活缓存。
- MoE addition / MoE 额外要求：for Gemma4-26B-A4B, keep architecture slices separate and, where the implementation exposes it, record routing/expert diagnostics or at least run batch-invariance checks. / 对 MoE 必须单独切片；如果实现暴露路由信息，就记录 expert/routing 诊断，否则至少做 batch-invariance 检查。

Dense error-finding audit / dense 找错审计：

- Artifacts / 产物：`scripts/audit_e153_error_finding.py`, `data/processed/e153_error_finding_audit_20260501.jsonl`, `results/E153_nonthinking_error_finding/e153_error_finding_audit_summary_20260501.json`, `reports/E153_ERROR_FINDING_AUDIT_20260501.md`.
- Scope / 范围：currently completed E153 error-finding files for Qwen35-27B and Gemma4-31B-it; the same script will include MoE when it finishes. / 当前包含已完成的 Qwen35-27B 和 Gemma4-31B-it 找错结果；MoE 完成后同脚本自动纳入。
- Parser distinction / 解析区分：the online runner records the first `ERROR:` line; the audit also records the last `ERROR:` line because some non-thinking completions naturally revise their own judgment. This first-vs-last split is a behavioral signal, not just a parsing bug. / 在线 runner 用第一个 `ERROR:`，审计额外记录最后一个 `ERROR:`；如果模型先判有错后又改判无错，这本身就是 non-thinking 自然纠错/摇摆信号。
- Qwen result / Qwen 结果：128 rows = 64 candidate solutions × 2 prompts. First-parse correctness is 117/128; last-parse correctness is 118/128; there is 1 first-to-last judgment flip. / Qwen 共 128 条；按第一个 `ERROR:` 算 117/128 正确，按最后一个 `ERROR:` 算 118/128 正确，有 1 条判断翻转。
- Invalid-reference detection / 错误参考解检测：for invalid reference rows, Qwen detects error presence well: first/last false negatives are both 1/64. Exact localization is weaker: last-location overlaps the offline error span in 61/64 invalid rows, leaving 2 detected-but-mislocalized rows and 1 missed-error row. / 对错误参考解，Qwen 基本能承认有错：漏报 1/64；但定位不是满分，61/64 命中人工错步，另有 2 条知道有错但定位错、1 条漏报。
- Valid-reference over-suspicion / 正确参考解过度怀疑：valid-reference false positives are 10/64 by first parse and 9/64 by last parse. These are important control cases for hidden-trigger policies, because an overly aggressive trigger would reject correct traces. / 正确参考解误报：first 10/64，last 9/64；这是 hidden-trigger 策略的重要反例控制，说明触发器太激进会误杀正确过程。
- Important example / 重要样本：on a valid algebra trace, Qwen first says `ERROR: Yes`, then recalculates and effectively concludes `ERROR: No`; the runner counted the first line, while the audit preserves both. This shows non-thinking mode can perform local reconsideration, but the final output format can remain unstable. / 在一条正确代数 trace 上，Qwen 先写 `ERROR: Yes`，随后重算并实际改成 `ERROR: No`；runner 记第一个，审计保留两者。这说明 non-thinking 模式也会局部反思，但格式/最终决策不稳定。
- Gemma dense result / Gemma dense 结果：128 rows. First-parse and last-parse correctness are both 121/128; there are 0 judgment flips. There are 2 hit-max rows, both in the algebra family under the global prompt. / Gemma dense 共 128 条；first/last 都是 121/128，没有判断翻转；2 条 hit-max 都来自代数题 global 找错 prompt。
- Gemma invalid-reference detection / Gemma 错误参考解检测：Gemma dense has 3/64 invalid false negatives and 58/64 invalid rows with last-location overlap. Its missed cases include the geometry incircle/trapezoid step and a set/Venn exactly-one step, where the model accepts a wrong shortcut as valid. / Gemma dense 对错误参考解漏报 3/64，定位命中 58/64；漏报样本包括几何内切梯形和集合 exactly-one，模型把错误捷径当作正确。
- Gemma valid-reference over-suspicion / Gemma 正确参考解过度怀疑：valid-reference false positives are 2/64, both tied to the graph connectivity boundary. This is lower than Qwen's valid false-positive rate, but partly because Gemma is less willing to flag some subtle invalid traces. / Gemma 正确参考解误报 2/64，主要是图连通性边界；比 Qwen 误报少，但也伴随对部分微妙错误不够敏感。
- Dense comparison / dense 对比：Qwen is more sensitive and more over-suspicious; Gemma dense is more conservative, with fewer false positives but more false negatives and fewer exact localization hits. This model-level tradeoff is central for later hidden-trigger thresholds. / Qwen 更敏感也更容易过度怀疑；Gemma dense 更保守，误报少但漏报多、定位命中少。这个模型差异会直接影响后续 hidden-trigger 阈值设计。
- Scientific interpretation / 科学解释：E153 error-finding strengthens the separation between solving competence and process-auditing competence. Qwen solves many tasks cleanly, but when asked to inspect another trace, it can over-suspect valid steps or locate the wrong step even when it correctly says an error exists. / E153 找错进一步说明“会解题”和“会审计过程”不是同一能力；Qwen 能干净做题，但检查别人过程时会过度怀疑正确步骤，或承认有错却定位错。

## 28. 2026-05-01 E159-E161 Overnight Queue Plan / answer-preserving 扩展、thinking 对照与受控修复

Plan artifact / 计划文件：`reports/E159_E161_OVERNIGHT_EXPERIMENT_PLAN_20260501.md`.

Why this block / 为什么做这一组：

- E153 showed that diverse but moderate reasoning-first tasks produce many clean sequential traces but no natural unrepaired ACPI. This means difficulty alone is not enough; unrepaired ACPI needs answer-preserving traps where a local wrong step can plausibly leave the final answer unchanged. / E153 说明多样化中等难题能产出大量干净顺序 trace，但没有自然未修复 ACPI；因此后续要专门构造“局部错但答案仍可保持”的陷阱，而不是只把题变难。
- Top-tier evidence needs breadth, mode contrast, and mechanism-ready samples. E159 expands the task/family surface, E160 adds thinking COT contrast, and E161 tests blind error-finding versus explicit hidden/oracle-span intervention. / 顶刊顶会需要广度、模式对照和可解释性样本；E159 扩展场景，E160 补 thinking 对照，E161 测 blind 找错与显式 span 上界。
- Hidden-state claims should not be built from unaudited generations. E159-E161 produce auditable sample pools first; later E156 hidden replay will only use audited rows. / hidden claim 不应直接建立在未审计生成上；这一组先造可审计样本池，后续 E156 只对审计后样本重放保存激活。

Prepared experiments / 准备的实验：

1. E159 answer-preserving non-thinking generation / E159 保答案陷阱 non-thinking 生成：
   - Builder: `scripts/build_e159_answer_preserving_task_bank.py`. / 构造脚本。
   - Runner: `scripts/run_e159_e160_answer_preserving_generation.py` with `--experiment E159_answer_preserving_generation --thinking false`. / 生成脚本。
   - Task bank: 40 tasks = 10 families × 4 tasks: algebra sign symmetry, counting complement, code boundary zero terms, table zero swaps, unit/percentage roundtrip, multilingual semantic, proof invalid lemma, graph definition, probability conditioning, temporal boundary. / 40 题，10 类，每类 4 题。
   - Models: Qwen35-27B, Gemma4-31B-it, Gemma4-26B-A4B-it. / 三个核心 P0。
   - Size: 40 tasks × 3 prompts × 3 models = 360 generations. / 规模 360 条生成。

2. E160 thinking COT contrast / E160 thinking COT 对照：
   - Same 40 tasks and same prompt variants, but `enable_thinking=true`. / 同一批题和 prompt，但打开 thinking。
   - Dense first: Qwen35-27B and Gemma4-31B-it. MoE thinking is deferred because it is expensive and routing-specific. / 先跑两个 dense；MoE thinking 后置。
   - Purpose: compare whether thinking reduces semantic slips, increases repair, or changes answer-preserving ACPI patterns relative to non-thinking. / 看 thinking 是否减少语义错、增加修复、改变 ACPI 模式。
   - Size: 40 tasks × 3 prompts × 2 dense models = 240 generations. / 规模 240 条。

3. E161 controlled error-finding and oracle-span repair / E161 受控找错与 oracle-span 修复：
   - Runner: `scripts/run_e161_answer_preserving_error_repair.py`. / 运行脚本。
   - Input: 80 candidate traces from E159 task bank: one valid reference and one invalid answer-preserving reference per task. / 输入 80 条候选过程，每题一正一错。
   - Prompt variants: `blind_global`, `blind_localize_only`, and `oracle_span_repair`. / 三个条件：全局找错、只定位、显式 span 修复。
   - Important boundary: `oracle_span_repair` deliberately exposes the offline error span as an upper-bound intervention; blind prompts do not expose span, gold answer, or manual label. / `oracle_span_repair` 是上界干预，故意给 span；blind 条件不泄漏 span、答案或标签。
   - Models: Qwen35-27B, Gemma4-31B-it, Gemma4-26B-A4B-it. / 三个核心 P0。
   - Size: 80 candidate traces × 3 prompts × 3 models = 720 jobs. / 规模 720 个找错/修复任务。

Implementation and queue / 具体实施与排队：

- Launcher: `scripts/launch_e159_e161_overnight_queue_20260501.sh`.
- Queue order: build bank -> scaffold smoke -> E159 Qwen -> E159 Gemma dense -> E159 Gemma MoE -> E160 Qwen thinking -> E160 Gemma dense thinking -> E161 Qwen -> E161 Gemma dense -> E161 Gemma MoE. / 队列顺序先构造和冒烟，再顺序跑生成、thinking 对照、受控找错。
- No concurrent GPU jobs: one tmux queue runs one model step at a time. / 不并发抢 GPU。
- Checkpoints: every model step writes JSONL checkpoints under `logs/`; final results go to `results/E159...`, `results/E160...`, and `results/E161...`. / 每步写 checkpoint 和 final JSON。

How errors are prevented / 如何保证不出错：

- Static audit before launch: `py_compile` new scripts and `bash -n` launcher. / 启动前编译检查和 shell 语法检查。
- Scaffold smoke: `scripts/smoke_e159_e161_scaffold.py` verifies 40 tasks, 80 candidate traces, 10 families × 4, first generation prompt, and E161 leakage boundaries. / scaffold 冒烟检查任务数量、家族分布、首 prompt 与泄漏边界。
- Task-bank audit: `scripts/audit_e159_task_bank.py` checks all 40 expected gold answers, 33 program-verifiable answers, candidate final-answer consistency, invalid-span literal presence, and valid/invalid labels. / 任务库审计检查 40 个 gold、33 个可程序验证答案、候选解最终答案一致性、错误 span 是否在候选解中逐字出现、正误标签是否一致。
- Leakage policy: generation prompts contain only the problem text. E161 blind prompts contain only problem plus visible proposed solution. Only the explicitly named oracle condition exposes the span and records `error_span_in_prompt=true`. / 生成 prompt 只含题目；blind 找错只含题目和可见候选解；只有 oracle 条件显式给 span 并记录。
- Scientific boundary: E159-E161 outputs are not final paper claims until audited. They are designed to create broad, mechanism-ready samples for later E156 hidden replay and final manual process audit. / E159-E161 结果在审计前不是最终论文 claim，只是为后续 hidden replay 和人工过程审计造样本。

Static audit, first-sample audit, and launch / 静态审计、首样本审计与启动：

- `py_compile` passed for `build_e159_answer_preserving_task_bank.py`, `audit_e159_task_bank.py`, `run_e159_e160_answer_preserving_generation.py`, `run_e161_answer_preserving_error_repair.py`, `smoke_e159_e161_scaffold.py`, and `audit_active_official_workspace.py`. / 新增脚本编译通过。
- `bash -n scripts/launch_e159_e161_overnight_queue_20260501.sh` passed. / 队列脚本语法检查通过。
- First launch was stopped after the first Qwen E159 checkpoint because the first task's offline gold answer was wrong: the model correctly produced `127`, while the bank incorrectly stored `109`. This is exactly why first-sample smoke is required. / 第一次启动在首条 Qwen checkpoint 后被主动停止，因为首题离线答案写错：模型正确算出 `127`，样本库误写 `109`。这正说明首样本 smoke 必须做。
- Fix / 修复：`e159_algebra_sign_symmetry_01` gold and both candidate reference final answers were corrected from `109` to `127`; `audit_e159_task_bank.py` was added to prevent this class of mistake. / 已把该题 gold 和候选解最终答案从 `109` 修为 `127`，并新增任务库审计脚本防止同类错误。
- Relaunch status / 重启状态：tmux session `p02_e159_e161_overnight_20260501` relaunched at `2026-05-01T03:39:02+08:00`; build, task-bank audit, and scaffold smoke passed; first Qwen E159 checkpoint now has gold `127`, extracted final `127`, `final_marker_found=true`, `hit_max=false`, and no prompt leakage. / 已重启队列；构建、任务库审计、scaffold 冒烟通过；首条 Qwen E159 checkpoint 现在答案正确且无泄漏。

## 29. 2026-05-01 Completed-Data Synthesis and KG Update / 已完成数据综合统计与 KG 更新

Artifacts / 产物：

- Summary script / 汇总脚本：`scripts/summarize_e153_e161_completed.py`.
- Human-readable synthesis / 人读综合报告：`reports/E153_E161_COMPLETED_DATA_SYNTHESIS_20260501.md`.
- Machine-readable synthesis / 机器可读综合数据：`reports/E153_E161_COMPLETED_DATA_SYNTHESIS_20260501.json`.
- KG claim snapshot / KG claim 快照：`reports/E153_E161_CLAIM_KG_20260501.json`.
- Static audit / 静态审计：`python3 -m py_compile scripts/audit_active_official_workspace.py scripts/summarize_e153_e161_completed.py` passed; `python3 scripts/audit_active_official_workspace.py` passed. / 新脚本编译通过，官方工作区审计通过。

Scope rule / 统计范围规则：

- Completed data only / 只统计已完成数据：only final JSON files and finalized audit summaries are counted as evidence. Running checkpoint JSONL files are queue-health signals, not scientific evidence. / 只有完整 final JSON 和已完成审计 summary 进入证据统计；正在写入的 checkpoint 只能说明队列健康，不能当作科学结论。
- Current queue / 当前队列：`p02_e159_e161_overnight_20260501` is still active. At synthesis time, completed steps are E159 build/audit/smoke, E159 non-thinking generation for all three models, and E160 Qwen thinking generation. E160 Gemma dense thinking is running; E161 has no completed final file yet. / 综合统计时，E159 三模型 non-thinking 与 E160 Qwen thinking 已完整落盘；E160 Gemma dense thinking 正在运行；E161 尚无完整 final 文件。

Plain-language definitions / 说人话定义：

- ACPI = Answer-Correct Process-Invalid / 答案正确但过程无效：the final answer is right, but the reasoning contains a real invalid step. / 最终答案对，但推理里有真实错步。
- Unrepaired ACPI / 未修复 ACPI：the model makes an invalid step and does not later notice or repair it, while still ending with the correct final answer. / 模型写出错步，后面没有发现或修正，最终答案仍然正确。
- Non-thinking mode / 非 thinking 模式：we call the model with `enable_thinking=false`; the model may still write short visible reasoning, but we do not activate the model's explicit long thinking mode. / 调用时关闭显式 thinking；模型仍可能输出简短可见推理，但不是 thinking 模式。
- Process audit / 过程审计：checking whether each important reasoning step is valid, not just whether the final answer matches the gold answer. / 不只看答案是否等于标准答案，还检查关键推理步骤是否成立。
- Prefill / 前缀喂入：feeding a fixed prompt plus a fixed partial trace into the model, usually by teacher forcing, then reading hidden states at chosen token positions. / 把固定题目和固定推理前缀喂给模型，通常用 teacher forcing，在指定 token 位置读取隐藏层。
- Hidden residual / 隐藏 residual：the residual-stream vector inside a transformer layer; it is the main carrier of information passed from earlier layers to later layers. / transformer 层内 residual stream 向量，是前层向后层传递信息的主通道。

Completed experiments and results / 已完成实验与结果：

1. E153 non-thinking difficult-scenario generation / E153 非 thinking 多样化困难场景解题：
   - Design / 设计：32 tasks × 3 reasoning-first prompts × 3 models. Prompts contain only problem text, not gold answers, trap notes, labels, or error spans. / 32 道题 × 3 个先推理后答案 prompt × 3 个模型；prompt 只含题目，不泄漏答案、陷阱、标签或错步。
   - Qwen35-27B / Qwen：96/96 final-correct after manual answer normalization; 89 clean valid prefill candidates; 19 language-trait traces; 0 unrepaired ACPI. / 归一化后 96/96 最终答案正确；89 条干净有效 prefill 种子；19 条语言特质 trace；0 条未修复 ACPI。
   - Gemma4-31B-it dense / Gemma dense：93/96 final-correct; 90 clean valid prefill candidates; 14 language-trait traces; 0 unrepaired ACPI. / 93/96 最终答案正确；90 条干净有效 prefill 种子；14 条语言特质 trace；0 条未修复 ACPI。
   - Gemma4-26B-A4B-it MoE / Gemma MoE：95/96 final-correct; 95 clean valid prefill candidates; 15 language-trait traces; 0 unrepaired ACPI. / 95/96 最终答案正确；95 条干净有效 prefill 种子；15 条语言特质 trace；0 条未修复 ACPI。
   - Interpretation / 解释：diverse moderate-hard tasks give many useful sequential traces, but they do not support a broad claim that natural unrepaired ACPI is frequent. / 多样化中等难题能产生大量可用顺序 trace，但不支持“自然未修复 ACPI 广泛高频”这个强说法。

2. E153 non-thinking error-finding / E153 非 thinking 找错定位：
   - Design / 设计：64 candidate solutions × 2 inspection prompts × 3 models = 384 rows. Each task has one valid reference trace and one invalid reference trace. Blind prompts do not expose labels or error spans. / 64 条候选解 × 2 个检查 prompt × 3 模型，共 384 条；每题一正一错；blind prompt 不给标签或错步。
   - Qwen35-27B / Qwen：118/128 last-parse correct; valid false positives 9/64; invalid false negatives 1/64; invalid location match 61/64; hit-max 1. / 最后判断 118/128 正确；正确过程误报 9/64；错误过程漏报 1/64；错误位置命中 61/64；截断 1。
   - Gemma4-31B-it dense / Gemma dense：121/128 last-parse correct; valid false positives 2/64; invalid false negatives 3/64; invalid location match 58/64; hit-max 2. / 最后判断 121/128 正确；误报 2/64；漏报 3/64；定位命中 58/64；截断 2。
   - Gemma4-26B-A4B-it MoE / Gemma MoE：113/128 last-parse correct; valid false positives 0/64; invalid false negatives 13/64; invalid location match 56/64; hit-max 2. / 最后判断 113/128 正确；误报 0/64；漏报 13/64；定位命中 56/64；截断 2。
   - Interpretation / 解释：this is the strongest completed evidence today. Models that solve many tasks correctly still make systematic errors when auditing an existing trace. Qwen is sensitive but over-suspicious; Gemma dense is more conservative; MoE is most conservative and misses more invalid traces. / 这是今天最强的已完成证据：模型能解题，不等于能可靠审计过程。Qwen 敏感但容易过度怀疑；Gemma dense 更保守；MoE 最保守、漏报更多。

3. E159 answer-preserving non-thinking generation / E159 保答案陷阱 non-thinking 生成：
   - Design / 设计：40 tasks = 10 families × 4 tasks, with 3 prompts and 3 models, so 360 completed generations. Families are algebra sign symmetry, counting complement, code boundary zero terms, table zero swap, unit roundtrip, multilingual semantic, proof invalid lemma, graph definition, probability conditioning, and temporal boundary. / 40 题 = 10 类 × 4 题，三种 prompt、三模型，共 360 条生成；覆盖代数符号对称、计数补集、代码零项边界、表格零交换、单位往返、多语言语义、证明无效引理、图定义、概率条件、时间边界。
   - Task-bank audit / 任务库审计：40 tasks, 80 candidate traces, 10 families × 4, 33 program-check rows, no issues. / 40 题、80 条候选过程、10 类每类 4 题、33 条可程序验证，审计无问题。
   - Qwen35-27B / Qwen：114/120 final-correct, 0 missing final markers, 0 hit-max. / 114/120 最终答案正确，无 final marker 缺失，无截断。
   - Gemma4-31B-it dense / Gemma dense：112/120 final-correct, 0 missing final markers, 0 hit-max. / 112/120 最终答案正确，无 final marker 缺失，无截断。
   - Gemma4-26B-A4B-it MoE / Gemma MoE：114/120 final-correct, 0 missing final markers, 0 hit-max. / 114/120 最终答案正确，无 final marker 缺失，无截断。
   - Important caveat / 重要边界：E159 final-correct is automatic final-answer scoring, not process audit. It prepares a broad sample pool; it does not yet prove natural ACPI. / E159 的 final-correct 只是最终答案自动判定，不是过程审计；它准备了大样本池，但还不能证明自然 ACPI。

4. E160 thinking contrast / E160 thinking 对照：
   - Completed part / 已完成部分：Qwen35-27B thinking generation completed on the same 40 tasks and 3 prompts. / Qwen35-27B thinking 在同一批 40 题、3 prompt 上已完整落盘。
   - Result / 结果：108/120 final-correct, 5 missing final markers, 16 hit-max rows. / 108/120 最终答案正确，5 条缺 final marker，16 条达到 token 上限。
   - Direct Qwen contrast / Qwen 同题对照：among 120 shared rows, 108 are non-thinking-correct and thinking-correct, 6 are non-thinking-correct but thinking-wrong, and 6 are non-thinking-wrong and thinking-wrong. / 120 条同题同 prompt 中，108 条 non-thinking 与 thinking 都对，6 条 non-thinking 对但 thinking 错，6 条两者都错。
   - Interpretation / 解释：this does not mean thinking is worse in general. The current thinking run has many truncations under the 4096-token cap, so it mainly tells us that thinking-mode evaluation needs larger max tokens or separate truncation handling. / 这不能简单解释为 thinking 更差；当前 thinking 在 4096 token 上限下截断较多，因此需要更大 token 上限或单独处理截断。

5. E161 controlled error-finding and oracle-span repair / E161 受控找错与 oracle-span 修复：
   - Status / 状态：not completed at synthesis time. / 综合统计时尚未完成。
   - Planned interpretation / 计划用途：blind prompts test natural non-thinking audit ability; oracle-span repair intentionally tells the model where the suspected bad step is, serving as an upper-bound intervention. / blind 条件测自然找错能力；oracle-span repair 故意告诉模型可疑错步位置，用作上界干预。

Claim-state KG / 当前 claim 的 KG 状态：

- `claim.solve_vs_audit_separation` / “解题能力”和“审计能力”分离：strong current evidence. E153 generation plus E153 error-finding support this claim. / 当前证据强；E153 解题和找错共同支持。
- `claim.natural_unrepaired_acpi_prevalence` / 自然未修复 ACPI 广泛高频：not supported yet. E153 found 0 unrepaired ACPI across 288 generation rows after process-oriented audit. / 尚不支持；E153 288 条生成审计未发现未修复 ACPI。
- `claim.answer_preserving_traps_needed` / 需要保答案陷阱来高效诱发 ACPI：design-supported, process-audit pending. E159 creates the correct sample surface, but ACPI labels require process audit. / 设计上得到支持，但过程审计未完成；E159 已造出合适样本面，但 ACPI 标签还要审。
- `claim.hidden_state_method` / 隐藏层可解释性方法：method fixed, data pending. The main evidence should use audit-after teacher-forced replay, not full online dumping. / 方法已确定，数据未完成；主证据应采用审计后 teacher-forced replay，而不是全量在线保存。

How much the claims advanced / claim 推进到哪里：

- This is evidence maturity, not paper completion. / 这里说的是证据成熟度，不是论文完成百分比。
- Claim 1, solve-vs-audit separation / 解题-审计分离：about strong/70-75%. It is already supported across dense and MoE models, but still needs formal confidence intervals, cleaner case cards, and later human-audit reliability. / 已跨 dense 与 MoE 支持，但还需要正式统计区间、案例卡和之后的人审可靠性。
- Claim 2, natural broad unrepaired ACPI prevalence / 自然广泛未修复 ACPI：about weak/20-25%. Current evidence is actually a boundary: natural unrepaired ACPI did not appear in E153, so we should not overclaim prevalence. / 当前证据偏弱，甚至是在限制该说法；E153 没发现自然未修复 ACPI，不能夸大。
- Claim 3, answer-preserving ACPI induction surface / 保答案 ACPI 诱发表面：about prepared/45-50%. E159 has the broad sample pool and good output health, but process audit must identify which rows are genuine ACPI or high-quality valid seeds. / E159 样本池和运行质量已经具备，但必须过程审计后才能定性。
- Claim 4, non-thinking repair improvement by explicit/hidden signal / 通过显式或 hidden 信号提升 non-thinking 修复：about pending/30-35%. E161 and E156 are the critical missing evidence. / 关键证据还没完成，取决于 E161 和 E156。
- Claim 5, mechanistic explainability / 机制可解释性：about method-ready/35-40%. The observation policy is settled, but new caches on E159/E161 audited rows are still pending. / 观测方法已定，但需要在 E159/E161 审计样本上重新保存激活。

Immediate next actions / 直接下一步：

1. Keep the current tmux queue running until E160 Gemma dense and E161 complete. / 保持当前 tmux 队列运行，等待 E160 Gemma dense 和 E161 完整落盘。
2. Re-run `scripts/summarize_e153_e161_completed.py` after each completed final file. / 每个 final 文件完成后重跑综合统计脚本。
3. Start process audit of E159 final-correct rows, prioritizing `unit_roundtrip`, `multilingual_semantic`, `graph_definition`, and `proof_invalid_lemma`, because these families most directly test answer-preserving ambiguity, semantic parsing, definition boundaries, and invalid proof shortcuts. / 开始审计 E159 答案正确行，优先单位往返、多语言语义、图定义和证明无效引理，因为这些类别最能测试保答案歧义、语义解析、定义边界和错误证明捷径。
4. Audit E159 wrong-answer rows separately to distinguish real model errors from answer-normalization or task-boundary problems. / 单独审计 E159 错答行，区分真实模型错误、答案归一化问题和题目边界问题。
5. After E161 completes, compare blind error-finding, blind localization-only, and oracle-span repair. / E161 完成后比较 blind 找错、blind 只定位和 oracle-span 修复。
6. Feed only audited rows into E156 teacher-forced hidden replay: clean-valid seeds, mutated-invalid traces, natural wrong traces, and localization-failure traces. / 只把审计后的样本送入 E156 teacher-forced hidden replay：干净正确种子、篡改错误 trace、自然错误 trace 和定位失败 trace。

## 30. 2026-05-01 E159 Generation Process ACPI Audit / E159 生成过程 ACPI 逐条审计

Artifacts / 产物：

- Audit script / 审计脚本：`scripts/audit_e159_generation_process_acpi.py`.
- Per-row audit table / 逐条审计表：`data/processed/e159_generation_process_acpi_audit_20260501.jsonl`.
- Summary JSON / 汇总 JSON：`results/E159_answer_preserving_difficult_generation/e159_process_acpi_audit_summary_20260501.json`.
- Report / 报告：`reports/E159_GENERATION_PROCESS_ACPI_AUDIT_20260501.md`.
- Updated synthesis and KG / 已同步更新综合报告和 KG：`reports/E153_E161_COMPLETED_DATA_SYNTHESIS_20260501.md`, `reports/E153_E161_COMPLETED_DATA_SYNTHESIS_20260501.json`, `reports/E153_E161_CLAIM_KG_20260501.json`.
- Static audit / 静态审计：`python3 -m py_compile` passed for the new audit script and updated synthesis script; active workspace audit passed. / 新审计脚本和综合脚本编译通过，官方工作区审计通过。

What was audited / 审计了什么：

- Input / 输入：all E159 non-thinking generation rows, 3 models × 40 tasks × 3 prompt variants = 360 rows. / 三个模型、40 道题、3 种 prompt，共 360 条 non-thinking 生成。
- Main label / 主标签：whether the trace is ACPI, meaning the final answer is correct but the reasoning process contains a real invalid step. / 主标签是是否 ACPI，即答案正确但过程含真实错步。
- Separate final-answer normalization / 单独做最终答案归一化：`100 meters`, `100m`, `3 km`, and `3 kilometers` are counted as equivalent to numeric gold answers `100` and `3` in the relevant unit-roundtrip tasks. / 对单位题，带单位答案按语义等价处理。
- Separate process label / 单独做过程标签：answer-format issues are not process errors; wrong semantic parsing, wrong proof steps, wrong conditioning, wrong graph rules, and wrong code boundaries are process errors only if they appear in the generated trace. / 格式问题不是过程错误；只有 trace 真写出语义误读、证明错步、条件概率错法、图规则错法或代码边界错法才算过程错误。

Results / 结果：

- Total rows / 总行数：360.
- Runner final-correct / 原 runner 最终答案正确：340/360. / 运行脚本原始判定 340 条正确。
- Audited final-correct / 审计归一化后最终答案正确：357/360. / 归一化后 357 条正确。
- Runner false negatives from answer format / runner 因答案格式造成的假错：17 rows, all from unit suffixes such as `100 meters`, `100m`, `3 km`, or `3 kilometers`. / 17 条自动假错都来自单位后缀。
- Strict process-valid / 严格过程有效：357/360. / 357 条过程严格有效。
- Strict ACPI / 答案正确但过程含错步：0/360. / 0 条严格 ACPI。
- Unrepaired ACPI / 答案正确、错步未修复：0/360. / 0 条未修复 ACPI。
- Clean valid prefill candidates / 干净有效 prefill 种子：357/360. / 357 条可作为干净有效 prefill/replay 种子。

By model / 按模型：

- Qwen35-27B / Qwen：120/120 audited final-correct, 120/120 process-valid, 0 ACPI, 6 runner format false negatives. / 审计后全对、全过程有效、0 ACPI，6 条格式假错。
- Gemma4-31B-it dense / Gemma dense：117/120 audited final-correct, 117/120 process-valid, 0 ACPI, 5 runner format false negatives. / 审计后 117 条正确且过程有效，0 ACPI，5 条格式假错。
- Gemma4-26B-A4B-it MoE / Gemma MoE：120/120 audited final-correct, 120/120 process-valid, 0 ACPI, 6 runner format false negatives. / 审计后全对、全过程有效、0 ACPI，6 条格式假错。

Only true generated failure / 唯一真实生成失败：

- Gemma4-31B-it fails `e159_multilingual_semantic_01` under all three prompt variants. / Gemma dense 在 `e159_multilingual_semantic_01` 三个 prompt 都失败。
- Error / 错误：it reads romanized Chinese `zhi duo wei 3` as “multiple/divisible by 3” instead of “at most 3.” / 它把拼音 `zhi duo wei 3` 误解为“3 的倍数”，而不是“至多为 3”。
- Consequence / 后果：it outputs 5 instead of gold 7. Since the final answer is wrong, these are wrong-answer semantic-failure traces, not ACPI. / 因此输出 5 而不是 7；因为答案也错，所以不是 ACPI，而是多语言语义错答样本。

Important reviewed boundary / 重要审计边界：

- Some algebra traces write `sqrt(81y^2)` as `9y` instead of `9|y|`. / 一些代数 trace 把 `sqrt(81y^2)` 写成 `9y`，没有写绝对值。
- Audit decision / 审计判定：when the trace keeps both `±` branches and derives the full two-line solution set, this is not counted as process-invalid because `y ± 9y` still enumerates the same two linear factors as `y ± 9|y|` across signs. / 如果 trace 保留正负两支并推出完整两条直线解集，则不算过程错；因为 `y ± 9y` 在正负分支下仍覆盖同一组线性因子。
- Scientific note / 科学说明：this is a good “watch-list” boundary for second human review, but it is not current ACPI evidence. / 这是二轮人审应关注的边界样本，但当前不作为 ACPI 证据。

Interpretation for the main claim / 对主 claim 的影响：

- Natural generation result / 自然生成结果：E159 does not support the idea that answer-preserving task surfaces automatically produce natural unrepaired ACPI. / E159 不支持“保答案任务面会自然大量产出未修复 ACPI”。
- Strong positive value / 正向价值：E159 gives 357 clean, sequential, final-correct traces across 10 answer-preserving families and 3 model architectures/settings. These are high-quality seeds for teacher-forced hidden replay and controlled mutation. / E159 提供了 357 条跨 10 类场景、三模型设置的干净顺序正确 trace，是后续 teacher-forced hidden replay 和受控篡改的高质量种子。
- Revised claim boundary / 修正后的 claim 边界：we should not claim natural prevalence from E159. The stronger and more defensible claim is that answer-preserving structures define a broad controlled testbed: valid generated traces can be minimally or semantically mutated into process-invalid/final-correct traces, and E161/E156 can test whether non-thinking models detect, localize, repair, or internally signal those errors. / 不能从 E159 主张自然高频；更稳妥的说法是：保答案结构给出广泛受控测试床，可以把干净正确 trace 篡改成“过程错但答案对”的样本，再用 E161/E156 测 non-thinking 模型能否发现、定位、修复或在隐藏层发出信号。

Immediate next actions / 直接下一步：

1. Keep waiting for E160 Gemma dense and E161 to complete; do not stop the queue. / 继续等待 E160 Gemma dense 和 E161 完成，不中断队列。
2. Use the 357 clean valid E159 traces as the positive replay/control pool. / 使用 357 条干净有效 trace 作为正例 replay/control 池。
3. Use E159 invalid reference traces and later mutations as the negative process-invalid/final-correct pool. / 使用 E159 invalid reference 和后续篡改作为负例“过程错但答案对”池。
4. Give the three Gemma dense multilingual wrong-answer traces their own case-card group; they are valuable for language-semantics robustness, not ACPI prevalence. / 将三条 Gemma dense 多语言错答单独做 case card；它们对语言语义鲁棒性有价值，但不是 ACPI 流行度证据。

## 31. 2026-05-01 E162 Low-Confidence Error-Prompt Smoke / E162 低置信截断错误提示 smoke

Goal / 目标：

- E162 tests whether a non-thinking model can recover from a process-wrong prefix when the intervention gives different amounts of error-location information. / E162 测试 non-thinking 模型在看到“已经走错一步的前缀”后，是否能靠不同强度的错误位置信息改回正确答案。
- The prefill is causal: it contains only the problem and the trace prefix before the original final answer. / prefill 是因果的：只包含题目和原 trace 的前缀，不包含原最终答案之后的内容。
- Gold answers, manual labels, and offline error types are not placed in blind prompts. / blind prompt 不放 gold answer、人工标签或离线错误类型。

Pipeline / 具体 pipeline：

1. Case construction / 构造 case：`scripts/build_e162_low_confidence_error_prompt_cases.py` reads the E159 process audit and E159 invalid reference bank, then creates E162 cases with a causal prefix, offline error span, localized hint, oracle hint, and random-location control. / 脚本读取 E159 过程审计和 E159 invalid reference bank，生成带因果 prefix、离线错步、局部提示、oracle 提示和随机位置对照的 E162 case。
2. Static audit / 静态审计：`scripts/audit_e162_case_bank_and_prompts.py` renders all prompt variants and checks that prefixes do not contain `Final answer:`, blind prompts do not contain gold answers or manual labels, and the full source trace is not accidentally pasted. / 渲染所有 prompt 变体，检查 prefix 不含 `Final answer:`，blind prompt 不含 gold answer 或人工标签，且没有误贴完整 source trace。
3. Smoke run / smoke 运行：`scripts/run_e162_low_confidence_error_prompt_repair.py` runs one audited case under six conditions: `baseline_regenerate`, `prefix_continue`, `generic_error_prompt`, `localized_error_prompt`, `oracle_error_prompt`, and `random_location_prompt`. / 对一个审计样本运行六个条件。

Prepared cases / 已准备样本：

- Case bank / 样本库：`data/processed/e162_low_confidence_error_prompt_cases_20260501.jsonl`.
- Total / 总数：43 cases = 3 generated wrong traces + 40 controlled invalid answer-preserving traces. / 43 个 case = 3 个自然生成“过程错且答案错” trace + 40 个受控“过程错但答案保持” trace。
- Static audit / 静态审计：258 rendered prompts checked; 0 issues. / 检查 258 个渲染后的 prompt，0 个问题。

Smoke sample / 首个样本：

- Model / 模型：`gemma4_31b_it`, dense, non-thinking, temperature 0.0.
- Case / 样本：`e162_generated_wrong_gemma4_31b_it_e159_multilingual_semantic_01_solve_neutral`.
- Problem / 题目：`Qiu zhengshu x de geshu: -8 <= x <= 8, qie |x| zhi duo wei 3.`
- Original failure / 原始错误：Gemma dense reads `zhi duo wei 3` as “multiple/divisible by 3,” not “at most 3,” and outputs 5 instead of gold 7. / Gemma dense 把 `zhi duo wei 3` 读成“3 的倍数”，不是“至多为 3”，所以输出 5 而不是 7。

Smoke result / smoke 结果：

| condition | final | correct | interpretation |
|---|---:|---:|---|
| `baseline_regenerate` | 5 | no | repeats the semantic misread / 重复语义误读 |
| `prefix_continue` | 5 | no | continues the wrong prefix / 沿着错误前缀继续 |
| `generic_error_prompt` | 5 | no | vague warning is insufficient / 泛泛提示不够 |
| `localized_error_prompt` | 7 | yes | localizing the bad phrase repairs the answer / 定位可疑短语后修复 |
| `oracle_error_prompt` | 7 | yes | explicit semantic hint repairs the answer / 明确语义提示后修复 |
| `random_location_prompt` | 5 | no | unrelated span does not cause false repair / 无关位置不触发误修复 |

Scientific interpretation / 科学解释：

- The smoke supports the E162 design: generic “something may be wrong” is too weak, but localized error-position information can trigger non-thinking repair without switching to thinking mode. / smoke 支持 E162 设计：泛泛说“可能有错”太弱，但局部错误位置提示可以在 non-thinking 模式下触发修复。
- The random-location control is important: the model does not correct merely because any monitor warning is present. / 随机位置对照很重要：模型不是因为随便看到一个 monitor warning 就改答案。
- This is not ACPI evidence because the source trace is process-wrong and answer-wrong; it is evidence for the repair/intervention side of the project. / 这不是 ACPI 证据，因为源 trace 是过程错且答案错；它支持的是修复/干预方向。
- Next step / 下一步：scale E162 to all 43 cases across dense models first, then use E163 to replace human spans with logprob or hidden-residual triggers. / 下一步先在 dense 模型上跑全 43 个 case，再用 E163 把人工 span 换成 logprob 或 hidden residual 触发点。

Artifacts / 产物：

- Report / 报告：`reports/E162_LOW_CONFIDENCE_ERROR_PROMPT_SMOKE_20260501.md`.
- Static audit / 静态审计：`reports/E162_LOW_CONFIDENCE_ERROR_PROMPT_STATIC_AUDIT_20260501.json`.
- Smoke result / smoke 结果：`results/E162_low_confidence_error_prompt_repair/gemma4_31b_it_e162_baseline_regenerate_prefix_continue_generic_error_prompt_localized_error_prompt_oracle_error_prompt_random_location_prompt_smoke_first_sample_20260501.json`.

## 32. 2026-05-01 E162 Full Queue and E164 Concrete Family Design / E162 全量队列与 E164 具体 family 设计

E162 full queue / E162 全量队列：

- Session / tmux 会话：`p02_e162_low_confidence_20260501`.
- Launcher / 启动脚本：`scripts/launch_e162_low_confidence_error_prompt_queue_20260501.sh`.
- Status file / 状态文件：`logs/e162_low_confidence_error_prompt_status_20260501.jsonl`.
- Queue order / 队列顺序：build E162 case bank -> static audit -> Qwen35-27B -> Gemma4-31B-it dense -> Gemma4-26B-A4B-it MoE. / 先构造样本库，再静态审计，然后按 Qwen、Gemma dense、Gemma MoE 顺序跑。
- Workload / 工作量：43 cases × 6 prompt variants = 258 generations per model. / 每个模型 43 个 case × 6 种 prompt，共 258 条生成。
- Prompt variants / prompt 条件：`baseline_regenerate`, `prefix_continue`, `generic_error_prompt`, `localized_error_prompt`, `oracle_error_prompt`, and `random_location_prompt`. / 六个条件分别测从头重做、直接续写、泛泛报错、局部报错、oracle 报错和随机位置对照。
- Static audit status / 静态审计状态：case bank build and static audit completed before generation; 258 rendered prompts had 0 issues. / 生成前样本库构造和静态审计已完成，258 个 prompt 0 问题。
- Current running status at this entry / 本条记录时状态：Qwen35-27B is running and has started writing checkpoints; not yet a completed scientific result. / Qwen35-27B 已开始写 checkpoint，但尚不是完整科学结果。

Why E162 matters / 为什么做 E162：

- E162 is a behavioral upper-bound experiment for hidden-layer correction. / E162 是 hidden-layer correction 的行为上界实验。
- `localized_error_prompt` is not itself hidden-layer correction. It asks: if a future hidden monitor can point to a suspicious visible span, can non-thinking generation repair the answer or process? / `localized_error_prompt` 本身不是隐藏层纠错；它问的是：如果未来 hidden monitor 能指出可疑可见 span，non-thinking 生成能否修复答案或过程。
- `random_location_prompt` is essential because it measures false correction: whether the model changes just because a warning appears. / `random_location_prompt` 必须保留，因为它测误修复：模型是否只是因为看到 warning 就乱改。
- The Qwen checkpoint stream already shows a possible generic recheck effect: sometimes even an unrelated random span causes Qwen to re-solve and find the true error. This must be reported separately from true localized repair. / Qwen checkpoint 初步显示一种泛化重审效应：有时即使随机 span 不相关，Qwen 也会重解并找到真错；这必须和真正局部定位修复分开统计。

E164 concrete family design / E164 具体 family 设计：

- Design artifact / 设计产物：`reports/E162_E164_CONCRETE_FAMILY_CASE_SPEC_20260501.md`.
- KG artifact / KG 产物：`reports/E162_E164_CLAIM_KG_20260501.json`.
- Scope / 范围：21 concrete cases across 7 priority families: geometry constraints, set/Venn counting, graph definitions, long table aggregation, code boundary, multilingual semantics, and proof validity. / 21 个具体样本，覆盖 7 类优先 family：几何约束、集合/Venn、图定义、长表格聚合、代码边界、多语言语义和证明有效性。
- Each case contains / 每个样本包含：problem, gold answer, valid trace, invalid-answer-correct trace, invalid-answer-wrong trace, manual error span, localized hint, oracle hint, random control span, verifier, E162 use, and E163 use. / 每题都有题目、标准答案、正确过程、过程错答案对过程、过程错答案错过程、人工错步 span、局部提示、oracle 提示、随机对照 span、验证规则、E162 用法和 E163 用法。

Why these families / 为什么选这些 family：

- Proof validity / 证明有效性：closest to ACPI because a true conclusion can be supported by a false lemma or invalid converse. / 最接近 ACPI，因为结论可以是真的，但证明用假引理或错误逆命题。
- Multilingual semantics / 多语言语义：directly tied to the project topic and current Gemma dense failure on `zhi duo wei`. / 直接对应项目主题，也对应当前 Gemma dense 在 `zhi duo wei` 上的真实失败。
- Graph definitions and code boundary / 图定义与代码边界：definition boundaries are crisp and verifiers are easy. / 定义边界清楚，验证器容易写。
- Long table aggregation / 长表格聚合：realistic applied setting where denominator, zero-row, and filter errors are easy to hide. / 贴近真实应用，分母、零行和筛选错误容易被长上下文掩盖。
- Geometry constraints / 几何约束：high value because models often import false visual assumptions, but wording must remain strict. / 价值高，因为模型常偷用错误图像假设，但题目措辞必须严格。

Important implementation decisions / 重要实施决定：

- E164 should be a new runnable experiment after E162, not a replacement for E162. / E164 应作为 E162 之后的新实验，不替代 E162。
- E164 must first build JSONL task and candidate-solution banks, then run a static audit, then smoke one sample, then queue full runs. / E164 必须先构造 JSONL 任务库和候选过程库，再静态审计，再首样本 smoke，最后全量排队。
- Recommended first smoke sample / 推荐首个 smoke 样本：`multi_01_pinyin_zhi_duo_wei`, because it already produced a real Gemma dense semantic failure and localized repair in E162 smoke. / 推荐 `multi_01_pinyin_zhi_duo_wei`，因为它已经产生 Gemma dense 真实语义失败，并在 E162 smoke 中被局部提示修复。
- Planned E164/E165 artifacts / 计划产物：`data/processed/e164_high_value_concrete_family_tasks_20260501.jsonl`, `data/processed/e164_high_value_concrete_family_candidate_solutions_20260501.jsonl`, `reports/E164_HIGH_VALUE_CONCRETE_FAMILY_STATIC_AUDIT_20260501.json`, `results/E164_high_value_concrete_family_generation/`, and `results/E165_high_value_concrete_family_error_prompt_repair/`. / 这些是后续可执行实验的计划产物。

## 33. 2026-05-01 E162 Completed Result and Checkpoint Audit / E162 已完成结果与 checkpoint 审计

Artifacts / 产物：

- Audit script / 审计脚本：`scripts/audit_e162_completed_and_checkpoint.py`.
- Row-level audit table / 逐行审计表：`data/processed/e162_completed_and_checkpoint_audit_20260501.jsonl`.
- JSON summary / JSON 汇总：`reports/E162_COMPLETED_AND_CHECKPOINT_AUDIT_20260501.json`.
- Human report / 人读报告：`reports/E162_COMPLETED_AND_CHECKPOINT_AUDIT_20260501.md`.

Evidence boundary / 证据边界：

- Completed final evidence / 完成 final 证据：only the Gemma dense first-sample E162 smoke JSON is complete at this audit time. / 本次审计时只有 Gemma dense 首样本 E162 smoke JSON 是完整 final 文件。
- Provisional checkpoint evidence / 临时 checkpoint 证据：Qwen35-27B full E162 run is still active; checkpoint rows are audited only as provisional behavior, not final scientific evidence. / Qwen35-27B 全量 E162 仍在运行；checkpoint 行只作为临时行为审计，不作为最终科学证据。
- Full E162 queue status / E162 全量队列状态：no complete full-model final JSON yet; Qwen has started writing checkpoint rows, Gemma dense and MoE full runs have not started yet. / 尚无完整全模型 final JSON；Qwen 已开始写 checkpoint，Gemma dense 与 MoE 全量还未开始。

Completed smoke audit / 完成 smoke 审计：

- Smoke case / smoke 样本：Gemma4-31B-it on `e159_multilingual_semantic_01`, where the source trace misreads `zhi duo wei 3` as “multiple of 3” and outputs 5 instead of gold 7. / Gemma4-31B-it 在 `e159_multilingual_semantic_01` 上把 `zhi duo wei 3` 误读成“3 的倍数”，输出 5 而非 gold 7。
- Six variants / 六个条件：
  - `baseline_regenerate`: final 5, wrong. / 从头做仍错。
  - `prefix_continue`: final 5, wrong. / 沿错误前缀继续仍错。
  - `generic_error_prompt`: final 5, wrong. / 泛泛报错仍错。
  - `localized_error_prompt`: final 7, correct. / 指出可疑局部 span 后修复。
  - `oracle_error_prompt`: final 7, correct. / 给 oracle 语义提示后修复。
  - `random_location_prompt`: final 5, wrong. / 随机位置对照不修复。
- Interpretation / 解释：this remains the cleanest positive E162 evidence so far: localized semantic span information can repair a non-thinking answer where generic warning and random-location warning do not. / 这仍是目前最干净的 E162 正证据：局部语义 span 信息能修复 non-thinking 答案，而泛泛报错和随机位置报错不能。

Qwen checkpoint provisional audit / Qwen checkpoint 临时审计：

- Snapshot size in audit / 审计快照规模：61 checkpoint rows plus 6 completed smoke rows were converted into row-level audit records. / 本次脚本审计时转换了 61 条 Qwen checkpoint 行和 6 条 smoke 完成行。
- Provisional Qwen families covered / 临时覆盖 family：algebra sign symmetry, code boundary zero, and the start of counting complement. / 临时覆盖代数符号对称、代码边界零项和计数补集开头。
- Provisional pattern / 临时模式：Qwen often identifies or repairs process errors even under `prefix_continue`, `generic_error_prompt`, or `random_location_prompt`. / Qwen 经常在直接续写、泛泛提示或随机位置提示下也发现或修复过程错。
- Scientific caution / 科学谨慎：this is not automatically a hidden/localized success. It may reflect a generic re-solve or re-audit tendency, especially because random-location prompts sometimes still lead to true-error repair. / 这不能自动解释为 hidden/localized 成功；它可能是泛化重解或重审倾向，尤其随机位置提示有时也会触发真错修复。
- Truncation issue / 截断问题：some baseline/localized algebra or counting rows hit `max_new_tokens=1024` and lack a final marker. These rows should be treated as incomplete generation, not scored as final model failures. / 一些代数或计数的 baseline/localized 行达到 1024 token 上限且缺 final marker，应视为生成未完成，而不是最终模型失败。

Current claim impact / 对当前 claim 的影响：

- Supports / 支持：localized visible span can be behaviorally useful for non-thinking repair in at least one real semantic failure. / 局部可见 span 对至少一个真实语义失败的 non-thinking 修复有用。
- Constrains / 限制：E162 still does not prove hidden residual, MLP, or attention can locate the span; that remains E163. / E162 仍不能证明 hidden residual、MLP 或 attention 能定位 span；这属于 E163。
- New analysis requirement / 新增分析要求：future E162 summaries must separate true localized advantage from generic re-audit and random-location-triggered re-solve. / 后续 E162 汇总必须区分真正局部定位优势、泛化重审和随机位置触发的重解。

## 34. 2026-05-01 E162 High-Token Non-Thinking Resume / E162 高 token 非 thinking 断点续跑

Reason / 原因：

- The first E162 full queue used `max_new_tokens=1024`. / 第一版 E162 全量队列使用 `max_new_tokens=1024`。
- Qwen35-27B checkpoint showed several rows with `hit_max_new_tokens=true` and `final_marker_found=false`, mainly long algebra/counting generations. / Qwen35-27B checkpoint 中有若干行达到 token 上限且缺 final marker，主要是长代数/计数推导。
- These rows should not be counted as final model failures; they must be rerun with a larger token budget. / 这些行不应算最终失败，必须用更大 token budget 重跑。

Actions / 操作：

- Stopped old tmux session / 停止旧队列：`p02_e162_low_confidence_20260501` was interrupted after preserving `logs/e162_repair_qwen35_27b_checkpoint_20260501.jsonl`. / 已保留旧 checkpoint 后中断旧队列。
- Added resume support / 新增断点续跑：`scripts/run_e162_low_confidence_error_prompt_repair.py` now accepts `--resume-from-checkpoint`. / runner 现在支持 `--resume-from-checkpoint`。
- Resume policy / 断点策略：rows with `final_marker_found=true` and `hit_max_new_tokens=false` are retained; missing, no-final, and hit-max rows are rerun. / 有 final marker 且未 hit-max 的行保留；缺失、无 final、hit-max 的行重跑。
- Added high-token launcher / 新增高 token 队列：`scripts/launch_e162_low_confidence_error_prompt_highmax_resume_20260501.sh`.
- New token budget / 新 token 上限：`max_new_tokens=8192`.
- Non-thinking guarantee / 非 thinking 保证：runner still calls chat template with `enable_thinking=False`; generated rows record `thinking=false` and `chat_template_enable_thinking_false_requested=true` when chat template is used. / runner 仍以 `enable_thinking=False` 调用 chat template；新生成行记录 `thinking=false`，使用 chat template 时记录 `chat_template_enable_thinking_false_requested=true`。
- New tmux session / 新 tmux 会话：`p02_e162_highmax_resume_20260501`.

Resume precheck / 断点预检查：

- Total E162 jobs / E162 总 job：43 cases × 6 variants = 258.
- Old Qwen checkpoint rows / 旧 Qwen checkpoint：70 rows.
- Retained complete rows / 保留完整行：65.
- Existing incomplete rows rerun / 旧截断/缺 final 重跑：5.
- Not-yet-run rows / 尚未运行行：188.
- Total highmax Qwen generations to run / highmax Qwen 需要新生成：193.

First highmax verification / 首批 highmax 验证：

- The first rerun row `e159_algebra_sign_symmetry_01 / baseline_regenerate` now generated 1672 tokens, had `Final answer: 127`, `hit_max_new_tokens=false`, and `thinking=false`. / 首个重跑样本现在生成 1672 token，有 final marker，未 hit-max，且非 thinking。
- The second rerun row `e159_algebra_sign_symmetry_01 / generic_error_prompt` also completed with final marker, `hit_max_new_tokens=false`, and `thinking=false`. / 第二个重跑样本也有 final marker，未 hit-max，且非 thinking。
- Interpretation / 解释：8192-token highmax resume solves the immediate truncation problem for the previously hit-max Qwen rows tested so far. / 目前看 8192 token 断点续跑解决了已检查 Qwen 截断问题。

Files / 文件：

- Old checkpoint / 旧 checkpoint：`logs/e162_repair_qwen35_27b_checkpoint_20260501.jsonl`.
- Highmax checkpoint / highmax checkpoint：`logs/e162_repair_qwen35_27b_highmax_checkpoint_20260501.jsonl`.
- Highmax status / highmax 状态：`logs/e162_low_confidence_error_prompt_highmax_status_20260501.jsonl`.
- Highmax log / highmax 日志：`logs/e162_repair_qwen35_27b_highmax_20260501.log`.

## 35. 2026-05-01 E162 Qwen35 Stage Sample Audit / E162 Qwen35 阶段性样本审计

Artifacts / 产物：

- Stage report / 阶段报告：`reports/E162_QWEN35_STAGE_ANALYSIS_20260501.md`.
- Sample cases / 抽样样本：`reports/E162_QWEN35_STAGE_SAMPLE_CASES_20260501.json`.

Scope / 范围：

- Source / 数据源：`logs/e162_repair_qwen35_27b_highmax_checkpoint_20260501.jsonl`.
- Current Qwen rows at analysis time / 分析时当前 Qwen 行数：121 / 258.
- Retained vs generated / 保留与新生成：65 retained old-complete rows and 56 newly generated highmax rows. / 65 条旧完整行保留，56 条 highmax 新生成。
- No truncation / 无截断：0 hit-max and 0 no-final rows in the current highmax checkpoint. / 当前 highmax checkpoint 中 0 hit-max、0 缺 final。

Current statistics / 当前统计：

- Overall / 总体：120/121 final-correct. / 目前 120/121 最终答案正确。
- By variant / 按 prompt：baseline 21/21, prefix_continue 19/20, generic 20/20, localized 20/20, oracle 20/20, random_location 20/20. / 当前覆盖行中各 prompt 的最终正确率如此。
- By family / 按 family：algebra, code, counting, graph each 24/24; multilingual 23/24; probability currently 1/1. / 代数、代码、计数、图均 24/24；多语言 23/24；概率当前 1/1。

Standard samples / 标准样本：

- `e159_multilingual_semantic_01 / baseline_regenerate`: Qwen directly reads `zhi duo wei 3` as `at most 3` and answers 7. / Qwen 从题目直接把 `zhi duo wei 3` 读成“至多为 3”，答 7。
- `e159_multilingual_semantic_01 / localized_error_prompt`: Qwen explicitly repairs the bad phrase `means at least 3 in magnitude` to `at most 3`. / Qwen 明确把错误短语修成“至多为 3”。
- `e159_code_boundary_zero_01 / localized_error_prompt`: Qwen repairs Python `range(0,6)` from `1,2,3,4` to `0,1,2,3,4,5`, while final answer stays `-20`. / Qwen 修复 Python range 边界，答案保持。
- `e159_counting_complement_01 / localized_error_prompt`: Qwen repairs the greater-than/less-than direction error and keeps the complement count 32. / Qwen 修复补集方向错，并保持答案 32。

Abnormal samples / 异常样本：

- Random-location repair / 随机位置修复：`e159_graph_definition_01 / random_location_prompt` flags a harmless problem-text fragment, but Qwen still finds the true Euler-trail definition error. / 随机位置并非错步，但 Qwen 仍找到 Euler trail 定义错。
- Prefix misled / 前缀带偏：`e159_multilingual_semantic_04 / prefix_continue` is the only current final-wrong row. From scratch Qwen answers 7, but with the bad prefix "`zhengshu` means positive integers only" it answers 4. / 当前唯一错答；从头能答 7，但错误前缀把它带成 4。
- Random semantic repair / 随机语义修复：`e159_multilingual_semantic_04 / random_location_prompt` repairs the same `zhengshu` issue even though the flagged random span is broad problem text, not the exact bad prefix. / 随机 span 是宽泛题目片段，不是精确错步，但仍修复 `zhengshu`。
- Hit-max resolved / 截断修复：`e159_algebra_sign_symmetry_01 / baseline_regenerate` was hit-max at 1024 tokens, but highmax completes in 1672 tokens with final 127. / 旧 1024 截断，highmax 正常完成。

Interpretation / 解读：

- Qwen35 non-thinking is strong at final-answer recovery in these covered E162 rows, but it often repairs by generic re-auditing rather than only by localized span use. / Qwen35 non-thinking 在已覆盖行中答案恢复很强，但常通过泛化重审修复，而不只是使用局部 span。
- Therefore E162 analysis must report `localized-only repair`, `generic repair`, `random-triggered repair`, `prefix misled`, and `baseline already correct` separately. / 因此 E162 分析必须分开报告局部独有修复、泛泛修复、随机触发修复、前缀带偏、从头已正确。
- `e159_multilingual_semantic_04 / prefix_continue` is a high-value case for the main story: sequential non-thinking can be misled by a causal wrong prefix even when baseline solving is correct; warning prompts restore performance. / `e159_multilingual_semantic_04 / prefix_continue` 是主线高价值样本：从头会做，但因果错误前缀会带偏 non-thinking；错误提示能恢复性能。

## 36. 2026-05-01 E162 Localized-vs-Random Interpretation / E162 localized 与 random 对照解读

Artifact / 产物：

- Interpretation report / 解读报告：`reports/E162_LOCALIZED_VS_RANDOM_INTERPRETATION_20260501.md`.

Core interpretation / 核心解读：

- `localized_error_prompt` performance only supports the main claim when it is a differential improvement over `generic_error_prompt` and `random_location_prompt`. / `localized_error_prompt` 的表现只有在相对 `generic_error_prompt` 和 `random_location_prompt` 有差分增益时，才真正支持主 claim。
- Plain-language meaning / 说人话：如果只要说“前面可能有错”或随机指一段，模型也能修好，那么证据主要说明模型被提醒后会全局重审；只有“指出真实局部错步后能修、泛泛/随机不能修”才说明局部信号有独立价值。 / If generic or random warnings also repair, the behavioral evidence is global re-audit; localized evidence requires true-span repair beyond those controls.
- Qwen35 current stage / Qwen35 当前阶段：localized final accuracy is high, but not localized-specific, because Qwen often repairs under generic or random warnings too. / localized 最终正确率高，但不具备强 localized-specific 解释，因为 Qwen 经常在泛泛或随机 warning 下也修复。
- Gemma dense smoke / Gemma dense smoke：`e159_multilingual_semantic_01` gives the cleanest current split: baseline, prefix, generic, and random answer 5; localized and oracle answer 7. / 当前最干净分裂来自 Gemma dense smoke：baseline、续写、generic、random 答 5；localized 和 oracle 答 7。

`zhi duo wei 3` boundary / `zhi duo wei 3` 样本边界：

- Meaning / 含义：`zhi duo wei 3` is pinyin-like romanization of Chinese `至多为 3`, meaning `at most 3`. / `zhi duo wei 3` 是“至多为 3”的拼音式罗马化表达，意思是“最多为 3”。
- Limitation / 局限：it is not standard written Chinese for a formal math benchmark. / 它不是正式数学 benchmark 中标准的中文书写方式。
- Why keep it / 为什么保留：it probes romanized Chinese and code-mixed semantic parsing, and it produced a real Gemma dense failure plus a clean localized repair split. / 它测试罗马化中文/混合语义解析，并且在 Gemma dense 上产生真实失败和干净 localized 修复分裂。
- Required controls / 必要对照：add `至多为 3`, spaced pinyin, `at most 3`, `no more than 3`, and symbolic `|x| <= 3`. / 后续必须加入中文字符、带空格拼音、英文同义表达和符号表达对照。

Random-span confound / random span 混杂：

- Qwen35 random-location prompts can induce visible global rechecking under non-thinking decoding. / Qwen35 的随机位置提示会在 non-thinking 解码下诱发可见的全局复查。
- Wording rule / 表述规则：do not call this true hidden thinking mode; record it as `non-thinking visible global re-audit behavior`. / 不说它进入真正 hidden thinking；记为“non-thinking 可见全局重审行为”。
- Prefix failures / 前缀失败：when a causal wrong prefix misleads the continuation, record it as `misled non-thinking continuation by a causal wrong prefix`. / 因果错误前缀带偏续写时，如实记为“因果错误前缀误导 non-thinking continuation”。
- New Qwen observation / Qwen 新观察：`e159_probability_conditioning_01 / generic_error_prompt` produced a correct final line but still hit `max_new_tokens=8192` by repeated self-checking. / `e159_probability_conditioning_01 / generic_error_prompt` 有正确 final line，但因反复自检达到 8192 token 上限。

Impact / 对后续实验的影响：

- Report categories separately / 分开报告类别：baseline already correct, prefix misled, generic repair, localized-only repair, oracle repair, random-triggered repair, and overlong global re-audit. / 必须分开统计从头已正确、前缀带偏、泛泛修复、localized 独有修复、oracle 修复、random 触发修复、过长全局重审。
- Prioritize Gemma dense for clean localized-vs-random evidence. / 优先在 Gemma dense 上找干净 localized-vs-random 证据。
- Treat Qwen as a strong global-audit model; its failures and random-triggered repairs are still valuable, but they answer a different question. / 把 Qwen 当作强全局审计模型；它的失败和 random 触发修复仍有价值，但回答的是另一个问题。
- Improve random controls / 改进 random 对照：use unrelated problem-text spans, neutral formatting spans, and spans from different sentences; keep them as separate subconditions. / 使用无关题目片段、中性格式片段、不同句子片段，并作为不同子条件报告。
- For hidden-state E163 / 对 E163 hidden-state：use teacher-forced replay to compare true error span, random span, and corrected span; do not infer localization from prompting behavior alone. / 用 teacher-forced replay 比较真错 span、随机 span、修正 span，不从 prompting 行为单独推断定位。

Gemma dense token cap / Gemma dense token 上限：

- The highmax launcher uses `MAX_NEW_TOKENS=8192` for `qwen35_27b`, `gemma4_31b_it`, and `gemma4_26b_a4b_it`. / highmax 队列对 `qwen35_27b`、`gemma4_31b_it`、`gemma4_26b_a4b_it` 均使用 `MAX_NEW_TOKENS=8192`。
- Current queue status / 当前队列状态：Qwen35 is still running in tmux session `p02_e162_highmax_resume_20260501`; Gemma dense full highmax has not started yet because the launcher runs models sequentially. / Qwen35 仍在 tmux 会话中运行；Gemma dense 全量 highmax 尚未开始，因为 launcher 按模型顺序执行。

## 37. 2026-05-01 E162 Cross-Model Localized Performance and Cost / E162 跨模型 localized 表现与成本

Key result / 关键结果：

- Qwen35-27B / Qwen35-27B：`localized_error_prompt` is not uniquely more accurate than `generic_error_prompt` or `random_location_prompt`, but it is typically cheaper in output tokens than generic repair and baseline. / `localized_error_prompt` 并不比 `generic_error_prompt` 或 `random_location_prompt` 更独特地准确，但在输出 token 上通常比 generic 修复和 baseline 更省。
- Gemma4-31B dense / Gemma4-31B dense：localized is a modest improvement over generic on the multilingual family, but random-location often matches it, so the clean claim is still “localized can help”, not “localized dominates all controls”. / localized 在多语言 family 上相对 generic 有小幅提升，但 random-location 常能追平，因此目前只能稳妥地说“localized 有帮助”，不能说“localized 全面优于所有对照”。
- Gemma4-26B-a4b / Gemma4-26B-a4b：localized is the strongest cross-model positive case; it improves over generic and random on the multilingual family and closes some of the gap to baseline. / localized 是三个模型里最强的正例；它在多语言 family 上优于 generic 和 random，并缩小了与 baseline 的差距。

Why token count alone is not enough / 为什么不能只看 token：

- Localized prompts are longer than generic prompts, so completion tokens alone understate their true cost. / localized prompt 比 generic 更长，所以只看 completion token 会低估真实成本。
- For Qwen35, localized reduced output length, but random prompts had a heavy long tail and even hit `8192` in one case. / 对 Qwen35，localized 确实减少了输出长度，但 random prompt 有重尾，且有样本打到 `8192`。
- For Gemma dense, localized sometimes costs more output tokens than random, so we need a fair total-cost metric before claiming it is cheaper. / 对 Gemma dense，localized 的输出 token 有时还比 random 多，因此在声称更省之前需要公平的总成本指标。

Recommended next metrics / 建议新增指标：

- Total token cost / 总 token 成本：prompt tokens + generated tokens, not generated tokens alone. / 用 prompt tokens + generated tokens，而不是只看 generated tokens。
- Success under budget / 预算内成功率：run the same case bank under `256/512/1024/2048/4096/8192` caps and plot correctness vs budget. / 在 `256/512/1024/2048/4096/8192` 上限下跑同一 case bank，画成功率-预算曲线。
- Cost per successful repair / 单次成功修复成本：average total tokens spent on rows that end correct. / 对最终答对的样本计算平均总 token 消耗。
- Family-stratified cost / 分 family 成本：multilingual, unit_roundtrip, proof_invalid_lemma, and other difficult families should be reported separately. / 多语言、unit_roundtrip、proof_invalid_lemma 等难 family 要单独报告。

Bottom line / 结论：

- The current data supports localized as a useful repair signal, but not yet as a universally cheapest or universally strongest control. / 目前数据支持 localized 是有用的修复信号，但还不能说它在所有场景里都是最省或最强的对照。
- The cleanest positive case still comes from Gemma dense on multilingual semantic parsing. / 当前最干净的正例仍来自 Gemma dense 的多语言语义解析。

## 38. 2026-05-01 E162 Localized Failure Re-Audit and Completion Cost / E162 localized 失败复审与 completion 成本

Artifacts / 产物：

- Script / 脚本：`scripts/audit_e162_localized_failures_and_cost.py`.
- Report / 报告：`reports/E162_LOCALIZED_FAILURE_AND_COST_AUDIT_20260501.md`.
- JSON / 结构化结果：`reports/E162_LOCALIZED_FAILURE_AND_COST_AUDIT_20260501.json`.

User cost definition / 用户成本口径：

- Prompt tokens are automatically generated and can be treated as nearly free for this analysis. / prompt tokens 是自动生成的，本轮按几乎不计成本处理。
- Primary cost is completion tokens. / 主要成本看 completion tokens。

Localized failure re-audit / localized 失败复审：

- Raw localized failures / 原始 localized 失败：11 rows.
- Unit-format false negatives / unit 格式假阴性：5 rows. / 这些行如 `100 m` vs gold `100`、`3 km` vs gold `3`，数值正确，只是旧 normalize 过严。
- Adjusted true localized failures / 修正后真实 localized 失败：6 rows.
- Qwen35 localized after adjustment / Qwen35 修正后 localized：43/43. / Qwen 的 2 条 localized 原始失败都是 unit 格式假阴性。
- Remaining true failures / 剩余真实失败：all are Gemma romanized multilingual semantic cases. / 全部是真正的 Gemma 罗马化多语言语义失败。

True localized failures / 真实 localized 失败：

- `gemma4_31b_it` `e159_multilingual_semantic_04`: span ``zhengshu` means positive integers only`, final 4 vs gold 7. / 模型坚持把 `zhengshu` 当正整数。
- `gemma4_31b_it` `e159_multilingual_semantic_01`: span `must be a multiple of 3`, final 5 vs gold 7. / 模型仍把 `zhi duo wei 3` 当 3 的倍数。
- `gemma4_31b_it` `e159_multilingual_semantic_01`: span `is a multiple of 3`, final 2 vs gold 7. / 模型把表达进一步误读成 `|x|=3`。
- `gemma4_26b_a4b_it` `e159_multilingual_semantic_01`: span `means at least 3 in magnitude`, final 12 vs gold 7. / 模型坚持“至少 3”。
- `gemma4_26b_a4b_it` `e159_multilingual_semantic_01`: span `must be a multiple of 3`, final 5 vs gold 7. / 模型坚持 3 的倍数。
- `gemma4_26b_a4b_it` `e159_multilingual_semantic_01`: span `is a multiple of 3`, final 5 vs gold 7. / 模型坚持 3 的倍数。

Completion-token cost per success after unit adjustment / unit 修正后的 completion-token 单次成功成本：

- Qwen35 / Qwen35：baseline 495.1, generic 601.0, localized 415.2, oracle 339.9, random 820.7. / localized 比 baseline、generic、random 都更省 completion 成本，仅次于 oracle。
- Gemma4-31B dense / Gemma4-31B dense：baseline 405.7, generic 344.3, localized 288.4, oracle 220.4, random 224.8. / localized 比 baseline/generic 更省，但 random 更省且同为 40/43。
- Gemma4-26B-a4b / Gemma4-26B-a4b：baseline 430.4, generic 443.5, localized 426.4, oracle 329.7, random 349.2. / localized 比 baseline/generic 略省，但不如 oracle/random 省。

Interpretation / 解读：

- Completion-token cost supports localized as an efficiency advantage for Qwen35 and Gemma4-31B relative to generic prompts. / completion-token 口径支持 localized 相对 generic 的效率优势，尤其是 Qwen35 和 Gemma4-31B。
- For Gemma4-26B-a4b, localized's main benefit is improved correctness over generic, not lower token cost. / 对 Gemma4-26B-a4b，localized 的主要收益是比 generic 更准，而不是更省 token。
- Hidden-layer deep dive should focus on the 6 true Gemma multilingual failures, not on unit rows. / hidden 深挖应聚焦 6 条真实 Gemma 多语言失败，不应浪费在 unit 格式假阴性上。

## 39. 2026-05-01 E162 Non-Pinyin Main Result and Gemma31 Random Re-Audit / E162 去拼音主结果与 Gemma31 random 复审

Artifacts / 产物：

- Script / 脚本：`scripts/audit_e162_non_pinyin_and_gemma31_random.py`.
- Report / 报告：`reports/E162_NON_PINYIN_AND_GEMMA31_RANDOM_AUDIT_20260501.md`.
- JSON / 结构化结果：`reports/E162_NON_PINYIN_AND_GEMMA31_RANDOM_AUDIT_20260501.json`.

Design correction / 设计修正：

- User correction accepted / 接受用户修正：`zhi duo wei 3` and `zhengshu` are pinyin/romanized Chinese, not strong multilingual-semantic evidence. / `zhi duo wei 3` 和 `zhengshu` 是拼音/罗马化中文，不应作为多语义主证据。
- Original logs are preserved, but main-result statistics exclude rows containing `zhi duo wei`, `zhengshu`, `shu chu`, or `qiu zhengshu`. / 原始日志保留；主结果统计排除包含这些表达的行。
- These rows may remain exploratory language-trait cases, not main claim evidence. / 这些行可作为探索性语言特质样本，但不进主 claim。

Non-pinyin main statistics / 去拼音主统计：

- Each model keeps 38 cases and 228 rows; 5 cases and 30 rows are excluded. / 每个模型保留 38 个 case、228 行；排除 5 个拼音/罗马化 case、30 行。
- Qwen35 / Qwen35：localized 38/38, generic 38/38, random 38/38; completion cost/success localized 406.1, generic 627.4, random 580.1. / Qwen 上 localized 与 generic/random 同准，但 completion 成本明显更低。
- Gemma4-31B dense / Gemma4-31B dense：localized 38/38, generic 38/38, random 38/38; completion cost/success localized 264.6, generic 304.2, random 202.1. / Gemma31 上三者都对；random 更省 token。
- Gemma4-26B-a4b / Gemma4-26B-a4b：localized 38/38, generic 38/38, random 38/38; completion cost/success localized 369.2, generic 384.1, random 313.6. / Gemma26 上三者都对；random 更省 token。

Gemma31 localized vs random manual comparison / Gemma31 localized 与 random 人工逐例比较：

- After pinyin removal, there are 38 localized/random paired cases. / 去拼音后有 38 个 localized/random 成对样本。
- Accuracy disagreement / 准确率分歧：0. / localized 与 random 都是 38/38。
- Token delta / token 差：localized minus random mean +62.5 tokens, median +67.5 tokens. / localized 平均比 random 多 62.5 个 completion token，中位数多 67.5。
- Interpretation / 解读：random is not more accurate; it is shorter. / random 不是更准，而是更短。
- Why / 原因：random spans often point to broad problem text; Gemma31 treats them as a request to reread and directly recompute. Localized prompts point to the exact bad step, so Gemma31 usually explains the local error before recomputing. / random span 常是宽泛题干，Gemma31 直接重读重算；localized 指出具体错步，模型会先解释错在哪里再重算，因此更长。

Impact on claim / 对 claim 的影响：

- Main E162 behavioral claim should no longer cite `zhi duo wei 3` / `zhengshu` as headline multilingual evidence. / E162 主 claim 不再用这两个拼音样本作为 headline 多语义证据。
- Stronger current non-pinyin claim / 当前更稳的去拼音 claim：localized visible error spans are useful and more token-efficient than generic warnings, especially on Qwen35; however, broad random re-solve is a strong baseline on Gemma models. / localized 可见错步相对 generic 有用且更省，尤其 Qwen35；但 Gemma 上宽泛 random 重解是强基线。
- Future designs need random controls that are not broad problem restatements. / 后续 random control 不能再主要是宽泛题干片段。

## 40. 2026-05-01 Gemma31 Localized/Oracle/Random Triad Audit / Gemma31 localized/oracle/random 三路复审

Artifacts / 产物：

- Script / 脚本：`scripts/audit_e162_gemma31_triad_comparison.py`.
- Report / 报告：`reports/E162_GEMMA31_LOCALIZED_ORACLE_RANDOM_TRIAD_20260501.md`.
- JSON / 结构化结果：`reports/E162_GEMMA31_LOCALIZED_ORACLE_RANDOM_TRIAD_20260501.json`.

Main observation / 主要观察：

- After removing pinyin/romanized cases, Gemma31 gets `localized`, `oracle`, and `random` all correct on 38/38 cases. / 去掉拼音/罗马化样本后，Gemma31 在 localized、oracle、random 三组都是 38/38。
- Completion length / completion 长度：localized mean 264.6, oracle mean 207.4, random mean 202.1. / localized 均值 264.6，oracle 均值 207.4，random 均值 202.1。
- Oracle and random are very close in length, and random is slightly shorter on average. / oracle 和 random 长度非常接近，random 平均还略短。

Interpretation / 解读：

- This indicates the current non-pinyin E162 bank is too easy for measuring localized-vs-random differential advantage on Gemma31. / 这说明当前去拼音 E162 题库对 Gemma31 来说太容易，无法有效测 localized 相对 random 的差分优势。
- It does not show localized is useless; it shows broad random problem-text spans are a strong re-solve trigger on short tasks. / 这不说明 localized 没用，而说明宽泛 random 题干片段在短题上是强重解触发器。
- Localized is longer because it usually explains the exact bad step before recomputing; oracle gives a direct correction; random often says the broad problem span is fine and directly recomputes from the problem. / localized 更长是因为通常先解释具体错步为什么错再重算；oracle 直接给修正；random 常说宽泛题干没错，然后直接从题目重算。

Concrete examples / 具体例子：

- `e159_probability_conditioning_03`: localized checks `"the other child has probability 1/2"` and explains the conditional sample-space fallacy in 278 tokens; oracle solves directly in 87 tokens; random flags `"A family has two children"` and simply recomputes the sample space in 119 tokens. / localized 解释具体错步，oracle 直接修，random 重读题干后重算。
- `e159_code_boundary_zero_04`: localized explains Python slicing `[0:5]` and `[1:4]` in 341 tokens; oracle uses 221 tokens; random flags the problem text and directly evaluates the expression in 201 tokens. / localized 解释切片错步，random 直接从表达式求值。
- `e159_proof_invalid_lemma_04`: localized analyzes whether the flagged lemma is actually valid in 237 tokens; oracle uses 150 tokens; random flags only `Claim` and proves the claim directly in 115 tokens. / localized 检查局部 lemma，random 直接证明命题。

Decision / 决策：

- Proceed to harder multi-family tasks. / 应进入更复杂的 multi-family 题目。
- Random controls must avoid broad problem restatements and should use neutral format spans, unrelated non-critical spans, or spans from another sentence with matched length. / random control 必须避免宽泛题干重述，应使用中性格式片段、无关非关键片段、或等长的其他句子片段。
- Harder tasks should make full restart expensive: long tables, long code, multi-hop geometry, proof validity, graph definitions with hidden constraints, and multi-condition aggregation. / 新题应让从头重算代价高：长表格、长代码、多跳几何、证明有效性、带隐含条件的图定义、多条件聚合。
- Use completion-token budget curves such as 128/256/512/1024 to test whether localized can repair under tight budgets while random re-solve cannot. / 用 128/256/512/1024 completion-token 预算曲线测试 localized 是否能在紧预算下修复，而 random 重解不能。

## 41. 2026-05-01 E164 Multi-Family Case Difficulty Audit / E164 多 family 题库难度审计

Artifacts / 产物：

- Script / 脚本：`scripts/audit_e162_e164_multi_family_case_difficulty.py`.
- Report / 报告：`reports/E162_E164_MULTI_FAMILY_CASE_DIFFICULTY_AUDIT_20260501.md`.
- JSON / 结构化结果：`reports/E162_E164_MULTI_FAMILY_CASE_DIFFICULTY_AUDIT_20260501.json`.

What was checked / 检查了什么：

- Existing multi-family design / 已有 multi-family 设计：`reports/E162_E164_CONCRETE_FAMILY_CASE_SPEC_20260501.md`.
- Status / 状态：this is a concrete case spec, not yet a runnable JSONL bank. / 它是具体样本规格，还不是可直接全量运行的 JSONL 题库。
- Scope / 范围：21 cases across 7 families: geometry, set/Venn counting, graph definitions, long table aggregation, code boundary, multilingual semantics, and proof validity. / 共 21 题、7 个 family。

Audit result / 审计结果：

- `revise_before_full`: 12 cases. / 机制有价值，但正式全量前必须加难。
- `smoke_only_too_easy`: 7 cases. / 只适合 smoke、pipeline 检查或 hidden replay 种子，不适合作为主证据。
- `exploratory_not_main_claim`: 2 cases. / 拼音/罗马化中文样本，只能作为探索性语言特质，不进主 claim。
- `all_cases_ready_for_full_run`: false. / 当前 21 题不能直接作为正式 E164 全量实验题库。

Localized cost and task difficulty / localized 成本与题库难度：

- E162 non-pinyin results still show a useful efficiency signal: Qwen35 localized completion cost/success is 406.1 vs generic 627.4 and random 580.1; Gemma31 localized is 264.6 vs generic 304.2; Gemma26 localized is 369.2 vs generic 384.1. / 去拼音后，localized 相对 generic 仍有 completion-token 成本优势，尤其 Qwen35 和 Gemma31。
- However, localized is not always cheaper than random: Gemma31 random is 202.1 and Gemma26 random is 313.6 because random spans often trigger short full re-solves. / 但 localized 不总比 random 省；Gemma 上 random 更短，主要因为 random span 常诱发低成本从头重做。
- Plain-language interpretation / 说人话解释：localized 能省成本，前提是模型不需要重做整道题；如果题太短，random 指到宽泛题干也能让模型快速重做，所以 random 会被题库简单性抬高。 / localized 的优势应在“从头重做很贵、局部修复很便宜”的题上最明显。

Why the current E164 cases are too easy / 为什么当前 E164 题偏简单：

- Many prompts are one-step or very short. / 很多题是一步题或短题。
- Several random spans expose key problem data, such as decisive side lengths, key graph edges, full score lists, or controversial table rows. / 多个 random span 标到了关键数据。
- Some ACPI traces are internally contradictory, for example a wrong rule followed by a correct arithmetic expression. / 部分过程错答案对 trace 内部自相矛盾，模型容易发现。
- Pinyin/romanized Chinese cases such as `zhi duo wei` and `qiahao` are not robust multilingual-semantic main evidence. / 拼音/罗马化中文不能当主多语义证据。

Decision / 决策：

- Do not launch full E164 directly from the current spec. / 不直接把当前规格启动为正式 E164 全量实验。
- Keep the 21 current cases as smoke tests, hidden replay seeds, and mechanism examples. / 当前 21 题保留作 smoke、hidden replay 种子和机制示例。
- Build a hardened v2 bank before full runs: longer tables, longer executable code, 8-12 node graphs, multi-step geometry, and proof-validity tasks with less obvious false lemmas. / 正式全量前先做加难 v2：长表、长代码、复杂图、多步几何、更隐蔽的证明错步。
- Split random controls into neutral formatting spans, unrelated non-critical data spans, and matched-length spans from a different sentence. / random 对照拆成中性格式、无关非关键数据、等长异句 span。
- Add completion-token budget curves at 128/256/512/1024 so localized can be tested under tight budgets where full restart is costly. / 加 128/256/512/1024 completion-token 预算曲线，检验局部修复是否比从头重做更省。

## 42. 2026-05-01 Hidden Monitor and Complex AIME Plan / hidden monitor 与复杂 AIME 计划

Artifacts / 产物：

- Plan / 计划：`reports/E166_E169_HIDDEN_MONITOR_COMPLEX_AIME_PLAN_20260501.md`.

Key correction / 关键修正：

- `localized` should be derived from hidden monitor output after causal prefill, not from a human-annotated span. / `localized` 应由 causal prefill 后的 hidden monitor 输出导出，而不是人工标注 span。
- Current E162/E165 localized prompts are behavioral upper bounds only. / 当前 E162/E165 的 localized prompt 只是行为上界。
- Hidden monitor should read residual, MLP, token-mixer/attention, norm, entropy, and logprob features from teacher-forced replay. / hidden monitor 应从 teacher-forced replay 读取 residual、MLP、token-mixer/attention、norm、entropy、logprob。

Planned next stages / 下一阶段计划：

1. E166: calibrate hidden monitor on the hardened multi-family bank. / 在加难 multi-family 题库上校准 hidden monitor。
2. E167: use hidden-derived spans to test non-thinking repair on complex and multi-error tasks. / 用 hidden 导出的 span 测复杂/多错误题的 non-thinking 修复。
3. E168: harvest model-task pairs on AIME-style tasks where baseline non-thinking is wrong or incomplete. / 筛选 AIME-style 题中 baseline non-thinking 失败的模型-题目对。
4. E169: attempt hidden-trigger rescue on those failures. / 在这些失败样本上做 hidden-trigger rescue。

Why this is reasonable / 为什么这合理：

- The controlled bank is good for monitor calibration because the hidden trigger can be validated against known spans. / 受控题库适合做 monitor 校准，因为可对照已知错步。
- The AIME rescue step should only start after monitor calibration; otherwise any positive result is hard to interpret. / AIME rescue 只有在 monitor 校准后才适合做，否则结果难解释。
- Rescue should target problems the model originally missed, not easy ones it already solved. / rescue 应针对模型原本不会做的题，而不是已经会的题。
- If the repo’s existing AIME-style bank is reused, its source year must be stated explicitly; if the target is the 2026 contest, that source must be separately verified before use. / 如果复用仓库里现有的 AIME-style 题源，必须明确写出年份；如果目标是 2026 AIME，使用前要单独核验来源。

## 43. 2026-05-02 E166 Hidden-Monitor Prefix Bank / E166 hidden monitor prefix 库

Artifacts / 产物：

- Builder / 构造脚本：`scripts/build_e166_hardened_monitor_prefix_bank.py`.
- Static audit / 静态审计脚本：`scripts/audit_e166_hardened_monitor_prefix_bank.py`.
- Replay runner / hidden replay 脚本：`scripts/run_e166_hardened_hidden_monitor_replay.py`.
- Prefix bank / prefix 库：`data/processed/e166_hardened_monitor_prefix_points_20260502.jsonl`.
- Summary / 汇总：`reports/E166_HARDENED_MONITOR_PREFIX_BANK_SUMMARY_20260502.json`.
- Static audit report / 静态审计报告：`reports/E166_HARDENED_MONITOR_PREFIX_STATIC_AUDIT_20260502.md` and `.json`.

What was built / 构造了什么：

- Source / 来源：the hardened E164 candidate trace bank. / 使用加难 E164 候选过程库。
- Prefix points / prefix 点：197.
- Monitor targets / 监测目标点：42 exact manual error-span ends from invalid traces. / 42 个 invalid trace 中人工错步结束点。
- Valid controls / 正确控制点：61 prefix points from valid traces. / 61 个正确过程 prefix 控制点。
- Invalid non-target controls / 错误过程非目标点：94. / 94 个错误过程但非 exact 错步结束点。

Leakage boundary / 泄漏边界：

- Future hidden replay prompts may use only `problem` and `prefix_text`. / 后续 hidden replay prompt 只能使用题目和可见 prefix。
- Gold answer, manual error span, manual label, and monitor target are offline metadata only. / 答案、人工错步、标签和 monitor target 只作离线元数据。
- The runner is written to support `generation_prefill` as the primary prompt mode; `strict_verifier` remains an optional diagnostic. / runner 以 `generation_prefill` 为主模式，`strict_verifier` 只作可选诊断。

Runtime resolution / 运行环境解决：

- Default `/usr/bin/python3` still has no `torch`, but the correct project runtime is `passage_prep_py312` plus `PYTHONPATH=.deps/hf5:src`. / 默认 Python 仍没有 `torch`，但项目正确运行环境是 `passage_prep_py312` 加 `.deps/hf5:src`。
- Reason / 原因：local Qwen3.5 and Gemma4 need the project-bundled `transformers 5.6.2`; plain conda has `transformers 4.57.1`, which cannot load these configs. / 本地 Qwen3.5 和 Gemma4 需要项目自带的 `transformers 5.6.2`；裸 conda 的 `4.57.1` 会加载失败。

## 44. 2026-05-02 E166 Hidden Replay Smoke and Full Queue / E166 hidden replay smoke 与全量队列

Artifacts / 产物：

- Runner update / runner 更新：`scripts/run_e166_hardened_hidden_monitor_replay.py`.
- Queue launcher / 队列脚本：`scripts/launch_e166_hidden_monitor_replay_queue_20260502.sh`.
- Claim KG / claim 知识图谱：`reports/E166_E169_HIDDEN_MONITOR_CLAIM_KG_20260502.json`.
- Smoke outputs / smoke 输出：`results/E166_hardened_hidden_monitor_replay/*_smoke_first_sample_20260502.json` and `.pt`.

Pipeline / 实验具体 pipeline：

1. Use only `problem` and causal `prefix_text` in the prompt. / prompt 只使用题目和因果 prefix。
2. Apply the official chat template with non-thinking disabled where supported. / 对支持的模型使用官方 chat template，并关闭 thinking。
3. Teacher-force the prefix and read final-prefix-token states. / teacher-forced replay 这个 prefix，并读取 prefix 最后一个 token 的状态。
4. Save residual hidden state, MLP output, token-mixer/attention output, available norm outputs, next-token entropy/logprob, and Yes/No diagnostic logprob. / 保存 residual hidden、MLP、token-mixer/attention、norm、next-token entropy/logprob 和 Yes/No 诊断 logprob。
5. Train simple E61 valid-vs-invalid component directions offline, then score each E166 prefix. / 离线用 E61 训练 valid-vs-invalid component direction，再给每个 E166 prefix 打分。
6. Save both JSON scores and `.pt` component vectors, directions, centers, and prefix metadata. / 同时保存 JSON 分数，以及 `.pt` 中的 component 向量、方向、中心和 prefix 元数据。

Smoke sample / smoke 首样本：

- Prefix id / prefix id：`e166_e164_code_01_range_zero_endpoints_nested_invalid_answer_preserving_reference_manual_error_span_end_54`.
- Family / family：`code_boundary`.
- Trace class / trace 类：`invalid_answer_correct`.
- Visible prefix / 可见 prefix：`Python range(0,8) skips the start 0 and stops before 7`.
- Why useful / 为什么符合需求：this is a sequential causal prefix ending exactly at a wrong local process step; later tokens and final answer are not visible. / 这是顺序因果 prefix，正好停在错误局部步骤；后文和最终答案不可见。

Smoke results / smoke 结果：

- `qwen35_27b`: passed; cache shape `[1, 15, 5120]`; component keys include residual, MLP, token-mixer, and norm outputs over layers 33-35. / 通过；缓存 shape `[1, 15, 5120]`。
- `gemma4_31b_it`: passed; cache shape `[1, 21, 5376]`; component keys include residual, MLP, token-mixer, and norm outputs over layers 33-35. / 通过；缓存 shape `[1, 21, 5376]`。
- `gemma4_26b_a4b_it`: passed; cache shape `[1, 21, 2816]`; component keys include residual, MLP, token-mixer, and norm outputs over layers 16-18. / 通过；缓存 shape `[1, 21, 2816]`。
- Leakage audit / 泄漏审计：all three smoke prompts report `gold_answer_in_prompt_rows=0`, `manual_error_span_in_prompt_rows=0`, and `manual_label_in_prompt_rows=0`. / 三个 smoke 都没有把答案、人工错步或人工标签写进 prompt。

Queue decision / 队列决策：

- Start full E166 replay serially in tmux over `qwen35_27b`, `gemma4_31b_it`, and `gemma4_26b_a4b_it`. / 用 tmux 串行启动三模型 E166 全量 replay。
- Serial execution is required because parallel loading can OOM on Gemma31; this was observed during smoke and is not a logic failure. / 必须串行，因为并行加载会让 Gemma31 OOM；smoke 中已观察到，这不是实验逻辑错误。
- The full E166 result is calibration evidence only. It will not by itself prove hidden-derived repair; E167 must use the E166-derived threshold/span without manual-span leakage. / E166 全量只是校准证据；它本身不证明 hidden-derived repair，E167 必须用 E166 导出的阈值/span 且不能泄漏人工 span。

## 45. 2026-05-02 E166 Full Calibration Audit / E166 全量校准审计

Artifacts / 产物：

- Full replays / 全量 replay：`results/E166_hardened_hidden_monitor_replay/*_full_20260502.json` and `.pt`.
- Calibration audit / 校准审计：`reports/E166_HIDDEN_MONITOR_CALIBRATION_AUDIT_20260502.md` and `.json`.
- Updated KG / 更新后 KG：`reports/E166_E169_HIDDEN_MONITOR_CLAIM_KG_20260502.json`.

What finished / 完成情况：

- `qwen35_27b`: 197/197 prefixes replayed; cache shape `[197, 15, 5120]`. / 197 个 prefix 全量完成。
- `gemma4_31b_it`: 197/197 prefixes replayed; cache shape `[197, 21, 5376]`. / 197 个 prefix 全量完成。
- `gemma4_26b_a4b_it`: 197/197 prefixes replayed; cache shape `[197, 21, 2816]`. / 197 个 prefix 全量完成。
- Leakage audit remains clean: prompts used only `problem` and `prefix_text`; gold answers, manual spans, and labels were offline only. / 泄漏审计保持干净：prompt 只用题目和 prefix，答案、人工 span 和标签只离线使用。

Key metrics / 关键指标：

- Qwen35 best monitor: layer-35 residual hidden state. Target-vs-valid AUC 0.981; target-vs-non-target AUC 0.761; target recall at valid-control 90th percentile 95.2%; valid false-trigger 11.5%; target top-2 localization 76.2%. / Qwen35 最佳信号是第 35 层 residual hidden state。
- Gemma4-31B dense best monitor: layer-33 post-attention norm output. Target-vs-valid AUC 0.964; target-vs-non-target AUC 0.813; target recall 88.1%; valid false-trigger 11.5%; target top-2 localization 92.9%. / Gemma4-31B dense 最佳信号是第 33 层 post-attention norm output。
- Gemma4-26B-a4b MoE best monitor: layer-17 post-attention norm output. Target-vs-valid AUC 0.895; target-vs-non-target AUC 0.785; target recall 61.9%; valid false-trigger 11.5%; target top-2 localization 95.2%. / Gemma MoE 最佳信号是第 17 层 post-attention norm output。

Interpretation / 解释：

- Strong result / 强结果：hidden/component states contain process-risk evidence under causal prefill, especially for Qwen35 and Gemma dense. / hidden/component 状态在因果 prefill 下含过程风险证据，Qwen35 和 Gemma dense 尤其明显。
- Localization nuance / 定位细节：target-vs-valid AUC is very high, but target-vs-non-target AUC is lower. This means the monitor reliably separates wrong-step prefixes from clean prefixes, but exact boundary localization is harder than coarse bad-trace detection. / target-vs-valid 很高，但 target-vs-non-target 较低；说明区分错步与正确 prefix 很稳，精确定位具体边界更难。
- MoE boundary / MoE 边界：Gemma MoE has usable hidden signal but lower high-precision recall; report it separately because routing may add instability. / Gemma MoE 有信号但高精度召回较低，应单独报告。
- Yes/No diagnostic / Yes/No 诊断：visible verifier-style Yes/No logits are insufficient for MoE; component states are the main evidence. / Yes/No logit 对 MoE 不够，component state 才是主证据。

Claim update / 主张更新：

- Supported now / 现在已支持：hidden monitor can causally read prefix-local process-risk signals without seeing future tokens or manual spans. / hidden monitor 能在看不到后文和人工 span 的情况下读取 prefix-local 过程风险信号。
- Not yet supported / 尚未支持：hidden-derived warning improves non-thinking repair accuracy/cost. This requires E167. / 还不能说 hidden-derived warning 已提升 non-thinking 修复；需要 E167 证明。

Next experiment / 下一实验：

- Build E167 hidden-derived repair cases from E166: select first threshold crossing per invalid trace, quote the visible span around that hidden trigger, and compare `prefix_continue`, `hidden_generic_warning`, `hidden_localized_warning`, `random_matched_warning`, and `oracle_manual_span`. / 从 E166 构造 E167：按每条 invalid trace 的首次阈值触发导出可见 span，比较续写、hidden 泛泛提醒、hidden 局部提醒、随机等长提醒和人工 oracle 上界。
- Keep valid-trigger controls to measure false correction. / 保留正确 prefix 的触发控制，用来测误改。

## 46. 2026-05-02 E167 Strict Auto-Boundary Hidden-Derived Repair / E167 严格自动边界 hidden-derived 修复

Artifacts / 产物：

- Case builder / 样本构造脚本：`scripts/build_e167_hidden_derived_repair_cases.py`.
- Static audit / 静态审计脚本：`scripts/audit_e167_hidden_derived_repair_cases.py`.
- Prompt smoke renderer / prompt smoke 脚本：`scripts/smoke_e167_hidden_derived_prompt.py`.
- Repair runner / 修复实验脚本：`scripts/run_e167_hidden_derived_repair.py`.
- Stage analysis / 阶段分析脚本：`scripts/summarize_e167_hidden_derived_repair.py`.
- Queue launcher / 队列脚本：`scripts/launch_e167_hidden_derived_repair_queue_20260502.sh`.
- Case bank / 样本库：`data/processed/e167_hidden_derived_repair_cases_20260502.jsonl`.
- Static audit report / 静态审计报告：`reports/E167_HIDDEN_DERIVED_REPAIR_CASES_STATIC_AUDIT_20260502.md` and `.json`.
- Prompt smoke report / prompt smoke 报告：`reports/E167_HIDDEN_DERIVED_PROMPT_SMOKE_20260502.md`.
- Stage analysis report / 阶段分析报告：`reports/E167_HIDDEN_DERIVED_REPAIR_STAGE_ANALYSIS_20260502.md` and `.json`.
- Updated KG / 更新后 KG：`reports/E166_E169_HIDDEN_MONITOR_CLAIM_KG_20260502.json`.

Important correction / 重要修正：

- Initial E167 draft selected hidden triggers from all E166 prefix points, including `manual_error_span_end`. / 最初 E167 草案从所有 E166 prefix 点里选 hidden 触发点，其中包括 `manual_error_span_end`。
- Audit found this is too weak for the main method claim: many selected spans would be manual-candidate endpoints scored by the monitor, not fully hidden-derived locations. / 审计发现这不足以支持主方法 claim：很多 span 是人工候选错步末尾被 hidden monitor 打分选中，而不是完全由 hidden monitor 自己定位出来。
- The official E167 bank was rebuilt as `auto_boundary_only`: non-oracle hidden triggers can only use automatic sentence/step boundaries; manual error-span endpoints are excluded from trigger candidates. / 正式 E167 已重建为 `auto_boundary_only`：非 oracle hidden 触发点只能来自自动句子/步骤边界，人工错步末尾不进入候选集合。
- Manual spans remain only offline metadata or the `oracle_manual_span` upper-bound condition. / 人工 span 只保留为离线元数据，或只在 `oracle_manual_span` 上界条件中使用。

Plain-language explanation / 说人话解释：

- `hidden-derived localized warning` means the model is first forced to read a partial solution prefix, and we inspect its hidden/component state at that causal point. / `hidden-derived localized warning` 是指先让模型读到一个局部推理 prefix，然后检查这个因果位置的 hidden/component 状态。
- If the hidden monitor says this prefix looks risky, we quote the visible sentence/step that ended at that prefix and ask the non-thinking model to recheck that local span. / 如果 hidden monitor 认为这个 prefix 风险高，我们引用该 prefix 结束处的可见句子/步骤，让 non-thinking 模型只重查这个局部片段。
- This differs from E162/E165: there the localized span was human-known or construction-known, so it was a behavioral upper bound, not the method itself. / 这不同于 E162/E165：那里 localized span 是人工已知或构造已知的，所以只是行为上界，不是方法本身。
- The causal condition is preserved: the monitor sees only `problem` and `prefix_text`; it never sees later tokens or the final answer. / 因果条件保持成立：monitor 只看 `problem` 和 `prefix_text`，看不到后续 token 或最终答案。

Case-bank audit / 样本库审计：

- Total E167 cases / 总样本：274.
- By policy / 按策略：`high_precision=141`, `budgeted=133`.
- By model / 按模型：`qwen35_27b=89`, `gemma4_31b_it=90`, `gemma4_26b_a4b_it=95`.
- Trigger boundary kinds / 触发边界类型：`sentence_end=274`; `manual_error_span_end=0`.
- Manual-target trigger rows / 命中人工错步末尾的触发点：0.
- Hidden span equals manual span / hidden span 与人工 span 完全相同：0.
- Hidden span contains manual span / hidden span 包含人工 span：231. This is expected because an automatic sentence can contain the local wrong phrase, but the endpoint was not supplied by the human annotation. / 这是合理的，因为自动句子边界可能包含错误短语，但边界不是人工标注直接提供的。
- Static audit passed / 静态审计通过：no gold answer in prompt by design, no manual label in prompt by design, and no manual endpoint used as hidden trigger. / 按设计没有答案泄漏、没有人工标签泄漏、没有把人工错步末尾作为 hidden 触发点。

Experiment pipeline / 实验具体 pipeline：

1. Load E166 calibration and choose the best monitor component per model. / 读取 E166 校准，为每个模型选择最佳 monitor component。
   - Qwen35: `35:residual_hidden_state`. / Qwen35 使用第 35 层 residual hidden state。
   - Gemma4-31B dense: `33:post_attention_norm_output`. / Gemma4-31B dense 使用第 33 层 post-attention norm output。
   - Gemma4-26B-a4b MoE: `17:post_attention_norm_output`. / Gemma4 MoE 使用第 17 层 post-attention norm output。
2. For each E164 candidate trace, discard E166 `manual_error_span_end` points before selecting a repair trigger. / 对每条 E164 候选过程，先丢弃 E166 中的 `manual_error_span_end` 点，再选择 repair trigger。
3. Use first high-precision threshold crossing among automatic sentence endpoints; if an invalid trace never crosses threshold, use top-risk automatic endpoint as a fallback. / 在自动句子边界中取首次 high-precision 阈值跨越；如果 invalid trace 从不跨阈值，则用风险最高的自动边界作 fallback。
4. Keep valid-trigger controls only when a valid trace crosses threshold, to measure false correction. / 正确过程只有跨阈值时才保留为控制样本，用来测误改。
5. Render six non-thinking prompt variants. / 渲染六种 non-thinking prompt：
   - `baseline_regenerate`: solve from the original problem. / 从原题重做。
   - `prefix_continue`: continue from the partial prefix without warning. / 无提醒，直接从 prefix 续写。
   - `hidden_generic_warning`: hidden monitor says somewhere in the prefix is risky. / hidden monitor 泛泛提醒 prefix 中某处有风险。
   - `hidden_localized_warning`: hidden monitor quotes the automatic-boundary span. / hidden monitor 指出自动边界 span。
   - `random_matched_warning`: random neutral span control. / 随机中性 span 对照。
   - `oracle_manual_span`: human span and hint upper bound. / 人工 span 和 hint 上界。
6. Run with `max_new_tokens=8192`, `temperature=0`, `batch_size=1`, official chat template, and non-thinking disabled where supported. / 使用 `max_new_tokens=8192`、`temperature=0`、`batch_size=1`、官方 chat template，并在支持处关闭 thinking。
7. Retain completed checkpoint rows only when `final_marker_found=true` and `hit_max_new_tokens=false`; otherwise rerun. / 只有出现 final marker 且没有 hit max 的 checkpoint 行才保留，否则重跑。

Smoke result / smoke 结果：

- Smoke model / smoke 模型：`qwen35_27b`.
- Smoke case / smoke 样本：`e167_qwen35_27b_high_precision_e164_code_01_range_zero_endpoints_nested_invalid_answer_preserving_reference`.
- Family / family：`code_boundary`.
- Hidden trigger boundary / hidden 触发边界：`sentence_end`.
- Hidden trigger candidate policy / hidden 触发候选策略：`auto_boundary_only`.
- Hidden localized span / hidden 局部 span：`Python range(0,8) skips the start 0 and stops before 7, so i=1,2,3,4,5,6.`
- Offline manual span / 离线人工 span：`Python range(0,8) skips the start 0 and stops before 7`.
- Smoke outputs / smoke 输出：6/6 prompt variants produced a final marker; 0/6 hit max token limit; 6/6 final answers were correct.
- Leakage audit / 泄漏审计：`gold_answer_in_prompt_rows=0`, `manual_label_in_prompt_rows=0`, `manual_span_used_as_non_oracle_warning_rows=0`, `manual_target_used_as_hidden_trigger_rows=0`, `oracle_hint_rows=1`.
- Interpretation / 解释：the smoke validates the strict-auto pipeline and prompt boundary, but it is not evidence of repair gain because this first answer-preserving sample is easy enough that all variants answer correctly. / smoke 验证了严格自动边界 pipeline 和 prompt 边界，但不是修复收益证据，因为首个答案保持样本太容易，六组都答对。

Queue state / 队列状态：

- tmux session / tmux 会话：`e167_hidden_derived_20260502`.
- Current launch / 当前启动：static audit completed, Qwen35 smoke started, then the queue will run full high-precision E167 over Qwen35, Gemma4-31B dense, and Gemma4-26B-a4b MoE serially. / 静态审计已完成，Qwen35 smoke 已开始，随后会串行跑三模型 high-precision E167 全量。
- Full-run purpose / 全量目的：test whether hidden-localized warnings improve non-thinking repair accuracy and/or completion-token cost compared with prefix continuation, generic warning, random warning, and oracle upper bound. / 全量目标是测试 hidden-localized warning 相比直接续写、泛泛提醒、随机提醒和 oracle 上界，是否提升 non-thinking 修复准确率和/或降低 completion-token 成本。
- Analysis metrics / 分析指标：accuracy, completion tokens, completion-token cost per success, hit-max rows, valid-control false correction, and paired deltas for hidden-localized versus prefix/generic/random/baseline/oracle. / 分析指标包括准确率、completion token、每次成功 completion 成本、hit-max 行、valid 控制误改，以及 hidden-localized 相对 prefix/generic/random/baseline/oracle 的配对差异。

Interim significance analysis / 阶段性显著性分析：

- Report / 报告：`reports/E167_HIDDEN_DERIVED_REPAIR_STAGE_ANALYSIS_20260502.md`.
- Analysis method / 分析方法：paired case-level exact sign test. For each case, compare whether `hidden_localized_warning` succeeds where another variant fails, and vice versa. / 用配对 case 级 exact sign test；逐题比较 hidden localized 相比其他组谁“只自己做对”。
- Current data / 当前数据：only Qwen35 partial checkpoint is available; Gemma dense and MoE have not started. / 目前只有 Qwen35 部分 checkpoint；Gemma dense 和 MoE 尚未开始。
- Qwen35 current checkpoint / Qwen35 当前 checkpoint：93 rows, 16 cases, 15 complete six-variant case sets, 0 hit-max rows, 93 final markers. / 93 行、16 个 case、15 个六变体完整 case、0 个 hit-max、93 个 final marker。
- Current answer / 当前回答：localized is not significantly stronger than other groups yet. / localized 目前还不能说显著强于其他组。
- Localized vs prefix_continue / 相比直接续写：15 paired cases, localized wins 0, prefix wins 0; no accuracy difference observed. / 15 个配对，双方独赢都是 0，没有准确率差异。
- Localized vs random_matched / 相比 random：15 paired cases, localized wins 0, random wins 0; no accuracy difference observed. / 15 个配对，双方独赢都是 0，没有准确率差异。
- Localized vs baseline_regenerate / 相比从头重做：15 paired cases, localized wins 0, baseline wins 0; no accuracy difference observed, but localized uses far fewer completion tokens on average. / 15 个配对，准确率无差异，但 localized 平均 completion token 明显更少。
- Localized vs generic / 相比泛泛提醒：15 paired cases, localized wins 2, generic wins 0; one-sided exact sign p=0.25, two-sided p=0.5. / localized 相对 generic 有正趋势，但远未显著。
- Oracle vs localized / oracle 相比 localized：15 paired cases, oracle wins 1, localized wins 0; not significant. / oracle 略高但不显著。
- Interpretation / 解释：this partial slice is mostly answer-preserving invalid traces and still too easy for accuracy separation; the main value so far is pipeline validity, leakage control, and completion-token accounting. / 当前切片主要是答案保持型错过程，仍偏容易，准确率拉不开；目前主要价值是验证 pipeline、泄漏边界和 completion-token 成本口径。
- Decision / 决策：do not claim E167 repair success until full Qwen35 plus Gemma dense/MoE are complete and the paired tests are rerun. / E167 三模型全量完成并重跑配对检验前，不声称 repair 成功。

## 47. 2026-05-02 E170 Thinking-Only Hardened-Task Baseline / E170 thinking-only 加难题原题 baseline

Artifacts / 产物：

- Runner / runner：`scripts/run_e170_thinking_only_hardened_tasks.py`.
- Prompt smoke / prompt smoke：`scripts/smoke_e170_thinking_only_prompt.py`.
- Stage summary / 阶段汇总：`scripts/summarize_e170_thinking_only.py`.
- Queue / 队列脚本：`scripts/launch_e170_thinking_only_after_e167_20260502.sh`.
- Watcher / watcher：`scripts/watch_then_launch_e170_after_e167_20260502.sh`.
- Prompt smoke report / prompt smoke 报告：`reports/E170_THINKING_ONLY_PROMPT_SMOKE_20260502.md`.
- Stage analysis report / 阶段分析报告：`reports/E170_THINKING_ONLY_STAGE_ANALYSIS_20260502.md` and `.json`.

Purpose / 目的：

- E170 is a thinking-mode original-problem baseline for the hardened E164 task bank. / E170 是 E164 加难题库的 thinking 模式原题解答 baseline。
- It does not test repair prompting; it tests whether thinking mode can solve the same hardened tasks from the original problem alone. / 它不测试修复 prompt，而测试 thinking 模式只看原题时能不能做题。
- This is useful because E167 studies non-thinking repair from partial traces; E170 gives a clean mode-contrast baseline. / 这有用，因为 E167 研究 non-thinking 从局部过程修复，E170 提供干净的模式对照。

Prompt boundary / prompt 边界：

- Prompt variant / prompt 变体：only `thinking_only_template`. / 只有一个 `thinking_only_template`。
- Template / 模板：generic solve instruction plus original problem, ending with `Final answer: <answer>`. / 通用解题指令加原题，要求最后输出 `Final answer: <answer>`。
- No prefix, no localized span, no random span, no oracle hint, no candidate trace, no trap note, and no manual label. / 不给 prefix、localized span、random span、oracle hint、候选过程、陷阱说明或人工标签。
- The gold answer string can appear as an ordinary number in the original problem text; this is not counted as answer leakage. / 答案字符串可能作为普通题干数字出现；原题解答中这不算答案泄漏。

Queue design / 队列设计：

- E170 is queued after E167, not parallel with E167, to avoid GPU contention. / E170 接在 E167 后面跑，不与 E167 并行，避免抢 GPU。
- tmux watcher / tmux watcher：`e170_after_e167_20260502`.
- Watcher behavior / watcher 行为：checks every 300 seconds; once `e167_hidden_derived_20260502` no longer exists, launches E170. / 每 300 秒检查一次；当 `e167_hidden_derived_20260502` 结束后启动 E170。
- E170 model order / E170 模型顺序：`qwen35_27b`, `gemma4_31b_it`, `gemma4_26b_a4b_it`. / 依次跑 Qwen35、Gemma dense、Gemma MoE。
- Max tokens / token 上限：`max_new_tokens=32768`, `temperature=0`, `batch_size=1`. / 上限 32768，零温，batch size 1。
- Resume policy / 续跑策略：retain only rows with `final_marker_found=true` and `hit_max_new_tokens=false`; rerun missing/no-final/hit-max rows. / 只保留有 final marker 且未 hit max 的行；缺失、无 final、hit max 都重跑。

Current state / 当前状态：

- E167 tmux session is still running. / E167 tmux 仍在运行。
- E170 watcher is running and waiting. / E170 watcher 已运行并等待。
- Workspace audit passed after adding E170 artifacts and optional future logs/results. / 加入 E170 产物与未来日志/结果后，工作区审计通过。

## 48. 2026-05-02 Definition Cleanup and E171 Main-Claim Rescue Deployment / 定义清理与 E171 主 claim 实验部署

Why this correction is necessary / 为什么要修正：

- User concern is correct: E167 `hidden_generic_warning` and `hidden_localized_warning` are text prompt conditions derived from a hidden monitor; they are not themselves hidden-layer interventions. / 用户指出得对：E167 的 `hidden_generic_warning` 和 `hidden_localized_warning` 是 hidden monitor 导出的文字 prompt 条件，不是 hidden layer intervention 本身。
- E167 can test whether hidden-derived text warnings help on controlled candidate traces. It cannot by itself prove the stronger claim that hidden signals make a model solve an original problem it otherwise cannot solve. / E167 能测试 hidden-derived 文字提醒对 controlled trace 的作用，但它本身不能证明“hidden 信号让模型做对原本不会做的原题”。
- The main claim now requires a stricter entry condition: first identify same-model original-problem non-thinking failures, then read hidden/component states on that model's own wrong trace, then test repair. / 主 claim 现在需要更严格入口：先找同一模型原题 non-thinking 做错的题，再在该模型自己的错误 trace 上读取 hidden/component 状态，然后测试修复。

Plain-language definitions / 说人话定义：

- Hidden signal / 隐藏层信号：after teacher-forced causal prefill, we read residual hidden state, MLP output, token-mixer/attention output, and norm outputs at the current prefix token. We project these vectors onto E61-trained valid-minus-invalid directions and define risk as negative validity score. / 在 teacher-forced 因果 prefill 后，我们读取当前 prefix token 的 residual hidden state、MLP output、token-mixer/attention output 和 norm output。把这些向量投影到 E61 训练出的“正确过程减错误过程”方向上，风险分数就是 validity score 的负数。
- Hidden monitor / 隐藏层监控器：the calibrated rule that says which component key and threshold to use for each model. / hidden monitor 是校准后的规则，规定每个模型使用哪个 component key 和阈值。
- `hidden_generic_warning` / hidden 泛泛提醒：the monitor triggers, but the prompt only says “somewhere in the prefix is risky.” It carries hidden-derived alarm information but no location. / monitor 触发，但 prompt 只说“prefix 某处有风险”，携带 hidden-derived alarm，但不携带位置。
- `hidden_localized_warning` / hidden 局部提醒：the monitor chooses an automatic sentence/step boundary; the visible span ending there is quoted to the model. This is a hidden-derived text localization condition. / monitor 在自动句子/步骤边界上选择触发点，把该处可见 span 引给模型看。这是 hidden-derived 的文字定位条件。
- Completion-token cost per success / 每次成功 completion token 成本：only generated output tokens are counted, because prompt tokens are largely automatically generated in our setup. / 只统计生成 token，因为 prompt tokens 在我们的设置里基本是自动生成成本。

E171 purpose / E171 目的：

- Test the real main claim: among tasks a model got wrong in original-problem non-thinking mode, can a hidden monitor over its own wrong trace help it recover the correct answer, and does localized rescue spend fewer completion tokens per success? / 检验真正主 claim：对模型原题 non-thinking 做错的题，在它自己的错误 trace 上读取 hidden monitor，能否帮助它改对，并且 localized rescue 是否有更低的每成功 completion-token 成本。

Artifacts / 产物：

- Task-bank builder / 题库构造：`scripts/build_e171_main_claim_task_bank.py`.
- Prompt smoke / prompt smoke：`scripts/smoke_e171_main_claim_prompt.py`.
- Pipeline audit / pipeline 审计：`scripts/audit_e171_main_claim_pipeline.py`.
- Baseline runner / baseline runner：`scripts/run_e171_baseline_nonthinking.py`.
- Hidden rescue runner / hidden rescue runner：`scripts/run_e171_hidden_rescue_from_baseline.py`.
- Stage summary / 阶段汇总：`scripts/summarize_e171_main_claim_hidden_rescue.py`.
- Queue / 队列脚本：`scripts/launch_e171_main_claim_hidden_rescue_queue_20260502.sh`.
- Watcher / watcher：`scripts/watch_then_launch_e171_e170_after_e167_20260502.sh`.
- Task bank / 题库：`data/processed/e171_main_claim_task_bank_20260502.jsonl`.
- Task-bank summary / 题库总结：`reports/E171_MAIN_CLAIM_TASK_BANK_SUMMARY_20260502.md` and `.json`.
- Prompt smoke report / prompt smoke 报告：`reports/E171_MAIN_CLAIM_PROMPT_SMOKE_20260502.md`.
- Pipeline audit report / pipeline 审计报告：`reports/E171_MAIN_CLAIM_PIPELINE_AUDIT_20260502.md` and `.json`.
- Planned result dir / 预期结果目录：`results/E171_main_claim_hidden_rescue`.

Task bank / 题库：

- Total tasks / 总题数：59.
- Sources / 来源：AIME2025 public hard tasks from `configs/e26_aime_hard_tasks.yaml` = 6; E153 difficult scenario tasks = 32; E164 hardened multi-family tasks = 21. / 来源包括 AIME2025 6 道、E153 32 道、E164 21 道。
- `E26` is an experiment id, not the AIME year; the AIME source rows are AIME2025. / `E26` 是实验编号，不是 AIME 年份；这些 AIME 行是 AIME2025。
- Runtime baseline prompt uses only the original problem and generic solve instruction. Gold answer, trap note, source metadata, and labels remain offline. / 运行时 baseline prompt 只含原题和通用解题指令；答案、陷阱说明、来源元数据和标签都只离线使用。

Experiment pipeline / 实验具体 pipeline：

1. Build E171 task bank and run static prompt smoke. / 构造 E171 题库并做静态 prompt smoke。
2. For each model, run original-problem non-thinking baseline with `max_new_tokens=16384`, `temperature=0`, `batch_size=1`, official chat template, and `enable_thinking=False` where supported. / 对每个模型跑原题 non-thinking baseline，上限 16384，零温，batch size 1，官方 chat template，并在支持时关闭 thinking。
3. Keep only same-model baseline failures as rescue cases. Correct baseline rows are excluded from E171 rescue because they cannot prove “solve what it could not solve.” / 只保留同一模型 baseline 做错的题作为 rescue case；baseline 正确的题不进入 E171 rescue，因为它们不能证明“做对原本不会做的题”。
4. Split the model's own wrong completion into automatic causal prefixes: sentence ends, line ends, chunk ends, and body end. / 把模型自己的错误 completion 切成自动因果 prefix：句末、行末、chunk 末尾和正文末尾。
5. For each prefix, teacher-force the same model on `problem + prefix`, read residual/MLP/token-mixer/attention/norm component states, and score risk using the E166 calibrated best key and high-precision threshold. / 对每个 prefix，用同一模型 teacher-force 读取 `problem + prefix` 后的 component 状态，并用 E166 校准的最佳 key 与 high-precision 阈值算风险。
6. Select the first threshold crossing; if no threshold is crossed, select the top-risk automatic prefix as fallback. / 选择首次跨阈值点；若无跨阈值，则选风险最高的自动 prefix。
7. Save hidden cache `.pt` with component vectors, directions, centers, and prefix metadata, so residual/MLP/attention/norm analyses can be repeated without regenerating text. / 保存 hidden cache `.pt`，包括 component vectors、directions、centers 和 prefix metadata，后续不用重新生成文本即可分析 residual/MLP/attention/norm。
8. Run non-thinking repair variants on the baseline-wrong cases. / 对 baseline 错题跑 non-thinking 修复变体：
   - `baseline_regenerate`: reused deterministic baseline failure as the no-intervention baseline. / 复用确定性的 baseline 错误，作为无干预 baseline。
   - `prefix_continue`: continue from hidden-triggered prefix without warning. / 从 hidden 触发 prefix 无提醒续写。
   - `hidden_generic_warning`: hidden-derived warning without location. / hidden-derived 泛泛提醒，不给位置。
   - `hidden_localized_warning`: hidden-derived warning plus automatic visible span. / hidden-derived 提醒加自动可见 span。
   - `random_matched_warning`: random visible span control. / 随机可见 span 对照。
9. Analyze rescue rate among baseline-wrong cases, completion tokens, cost per success, hit-max rows, and paired deltas for localized vs prefix/generic/random/baseline. / 分析 baseline 错题中的救回率、completion token、每成功成本、hit-max 行，以及 localized 相对 prefix/generic/random/baseline 的配对差异。

Static audit and smoke / 静态审计与 smoke：

- `python -m py_compile` passed for all E171 scripts under the `passage_prep_py312` conda environment. / 在 `passage_prep_py312` 环境中，E171 全部脚本通过 py_compile。
- Task-bank build passed: 59 tasks, 0 duplicate problem+answer rows. / 题库构造通过：59 题，0 个 problem+answer 重复。
- Prompt smoke passed: first prompt contains only generic solve instruction plus original problem. / prompt smoke 通过：首个 prompt 只含通用解题指令和原题。
- Pipeline audit passed with no errors or warnings. / pipeline 审计通过，无错误无警告。

Queue decision / 队列决策：

- Keep current E167 tmux running because it is already a useful controlled-trace reference. / 保持当前 E167 tmux 继续跑，因为它仍是有价值的 controlled-trace 对照。
- Replace the previous E170-only watcher with a new watcher order: wait for E167, then run E171 main-claim hidden rescue, then run E170 thinking-only baseline. / 用新的 watcher 顺序替换旧的 E170-only watcher：等待 E167，先跑 E171 主 claim hidden rescue，再跑 E170 thinking-only baseline。
- New watcher session / 新 watcher 会话：`e171_e170_after_e167_20260502`.
- Serial execution is intentional to avoid multi-GPU OOM. / 串行执行是为了避免多 GPU OOM。

## 49. 2026-05-02 E172 AIME2026 Hidden-Gate Landing Audit / AIME2026 hidden-gate 落盘审计

Purpose / 目的：

- E172 moves the hidden-gate test to the fresh MathArena `aime_2026` 30-problem bank. / E172 把 hidden-gate 测试推进到 MathArena `aime_2026` 30 题。
- Baseline is original-problem non-thinking solve; hidden-gate generates in chunks, reads an E166-calibrated hidden/component risk score on causal prefixes, and triggers a non-thinking controlled-check branch when the risk crosses threshold. / baseline 是原题 non-thinking 解题；hidden-gate 分块生成，在因果 prefix 上读取 E166 校准的 hidden/component 风险分数，跨阈值后触发 non-thinking controlled-check 分支。
- This is not an answer oracle. Gold answers are offline scoring metadata only. / 这不是答案 oracle；答案只用于离线评分。

Artifacts / 产物：

- Task bank / 题库：`data/processed/e172_aime2026_matharena_task_bank_20260502.jsonl`.
- Task-bank summary / 题库总结：`reports/E172_AIME2026_MATHARENA_TASK_BANK_20260502.md` and `.json`.
- Prompt smoke / prompt smoke：`reports/E172_AIME2026_PROMPT_SMOKE_20260502.md`.
- Pipeline audit / pipeline 审计：`reports/E172_AIME2026_PIPELINE_AUDIT_20260502.md` and `.json`.
- Baseline runner / baseline runner：`scripts/run_e172_aime2026_nonthinking_baseline.py`.
- Hidden-gate runner / hidden-gate runner：`scripts/run_e172_aime2026_hidden_gate_realtime.py`.
- Summary/KG writer / 汇总与 KG 脚本：`scripts/summarize_e172_aime2026_hidden_gate.py`.
- Stage analysis / 阶段分析：`reports/E172_AIME2026_HIDDEN_GATE_STAGE_ANALYSIS_20260502.md` and `.json`.
- Machine-readable KG / 机器可读 KG：`reports/E172_AIME2026_CLAIM_KG_20260502.json`.
- KG image / KG 图片：`reports/E172_AIME2026_KG_20260502.svg`.

Task-bank and pipeline status / 题库与 pipeline 状态：

- Dataset / 数据集：`MathArena/aime_2026`, split `default/train`, dataset SHA `10b4e45b7a503075d4da8a0d57916a4f06ce6bd2`.
- Tasks / 题数：30.
- Leakage boundary / 泄漏边界：runtime prompts contain only the original problem; `gold_answer`, dataset SHA, task source, and row metadata remain offline. / 运行时 prompt 只含原题；答案、数据集 SHA、来源和行元数据只离线使用。
- Static audit passed / 静态审计通过：pipeline audit reports no errors or warnings.

Landing state by timestamp / 按时间戳的落盘状态：

- `2026-05-02T19:49`：task bank, prompt smoke, and pipeline audit completed. / 题库、prompt smoke 和 pipeline audit 完成。
- `2026-05-02T19:51`：`qwen35_27b` baseline smoke and hidden-gate smoke completed. / Qwen smoke baseline 与 hidden-gate smoke 完成。
- `2026-05-02T19:51` to `2026-05-02T20:26`：`qwen35_27b` formal baseline wrote 10 checkpoint rows, then no `done` event was recorded. / Qwen 正式 baseline 写入 10 条 checkpoint，之后没有记录 `done`。
- At audit time / 本次审计时：no E172 Python process is running, and the status file has no `all_done`. / 没有 E172 Python 进程，状态文件没有 `all_done`。

Model coverage / 模型覆盖：

- `qwen35_27b`: participated. Formal baseline partial checkpoint exists at `logs/e172_aime2026_baseline_qwen35_27b_checkpoint_20260502.jsonl`; hidden-gate exists only as smoke at `logs/e172_aime2026_hidden_gate_qwen35_27b_smoke_checkpoint_20260502.jsonl`. / 已参与；正式 baseline 只有部分 checkpoint，hidden-gate 只有 smoke。
- `gemma4_31b_it`: planned in launcher but no E172 generated rows or status start event landed. / 在 launcher 中计划运行，但没有 E172 生成行或 status start 事件落盘。
- `gemma4_26b_a4b_it`: planned in launcher but no E172 generated rows or status start event landed. / 在 launcher 中计划运行，但没有 E172 生成行或 status start 事件落盘。

Formal baseline result / 正式 baseline 结果：

- Only `qwen35_27b` has formal checkpoint rows. / 只有 Qwen 有正式 checkpoint 行。
- Coverage / 覆盖：10/30 AIME2026 problems, indices 1-10. / 覆盖第 1 到第 10 题。
- Correctness on observed rows / 已观测行正确性：10/10 correct, all with explicit final markers, 0 hit-max rows.
- Completion tokens / completion token：36,181 total; mean 3,618.1; median 2,248.
- Important boundary / 重要边界：this is a partial checkpoint, not a complete 30-question score and not a model comparison. / 这是部分 checkpoint，不是完整 30 题成绩，也不能做模型比较。

Qwen formal baseline per-problem summary / Qwen 正式 baseline 逐题摘要：

| idx | task | gold | extracted | correct | tokens |
|---:|---|---:|---:|---:|---:|
| 1 | `e172_aime2026_p01` | 277 | 277 | true | 1539 |
| 2 | `e172_aime2026_p02` | 62 | 62 | true | 2626 |
| 3 | `e172_aime2026_p03` | 79 | 79 | true | 1168 |
| 4 | `e172_aime2026_p04` | 70 | 70 | true | 4143 |
| 5 | `e172_aime2026_p05` | 65 | 65 | true | 1215 |
| 6 | `e172_aime2026_p06` | 441 | 441 | true | 1363 |
| 7 | `e172_aime2026_p07` | 396 | 396 | true | 2309 |
| 8 | `e172_aime2026_p08` | 244 | 244 | true | 2187 |
| 9 | `e172_aime2026_p09` | 29 | 29 | true | 11382 |
| 10 | `e172_aime2026_p10` | 156 | 156 | true | 8249 |

Hidden-gate smoke result / hidden-gate smoke 结果：

- Model / 模型：`qwen35_27b`.
- Task / 题目：`e172_aime2026_p01`, gold `277`.
- Hidden component / hidden component：`35:residual_hidden_state`.
- Observation source / 观测文件：`logs/e172_aime2026_hidden_gate_qwen35_27b_observations_smoke_20260502.jsonl`.
- Visible span at trigger / 触发时可见 span：`Let $t_P$ be`.
- Hidden validity score / hidden validity score：`-1.8095734119415283`.
- Hidden risk / hidden risk：`1.8095734119415283`.
- Threshold / 阈值：`1.4118950366973877`, mode `high_precision`.
- Trigger / 触发：crossed threshold, so the controlled-check branch started. / 跨阈值，进入 controlled-check 分支。
- Outcome / 结果：controlled branch hit its 512-token cap, produced no final marker, fallback extracted `5`, and final correctness was false. / controlled 分支 hit max，无 final marker，fallback 抽到 `5`，答案错误。

Interpretation / 综合解释：

- E172 currently supports task-bank readiness, prompt/pipeline hygiene, and partial Qwen non-thinking competence on the first 10 AIME2026 rows. / E172 目前支持题库可用、prompt/pipeline 边界干净，以及 Qwen 在前 10 道 AIME2026 上的部分 non-thinking 能力。
- E172 does not yet support a 30-problem AIME2026 accuracy claim for any model. / 还不能支持任何模型的 30 题 AIME2026 准确率 claim。
- E172 does not yet support cross-model comparison because Gemma dense and Gemma MoE have no landed rows. / 还不能做跨模型比较，因为两个 Gemma 没有落盘行。
- E172 does not yet support hidden-gate improvement. The only hidden-gate row is a smoke row where a valid-looking early variable-introduction span crossed threshold and the controlled branch failed. / 还不能说 hidden-gate 有提升；唯一 hidden-gate 行是 smoke，并且在一个看起来有效的早期变量定义 span 上触发，controlled 分支失败。
- Current hidden-layer conclusion / 当前隐藏层结论：the E166-calibrated Qwen monitor can fire during AIME2026 realtime generation, but this first trigger is over-early or false-positive for the repair objective. The E172 gate needs full-run calibration analysis before it can be used as evidence for useful hidden-state rescue. / E166 校准的 Qwen monitor 能在 AIME2026 实时生成中触发，但首次触发对修复目标而言过早或是假阳性；E172 gate 需要全量校准分析后才能支撑“有用 hidden-state rescue”。

Next / 下一步：

- Resume or rerun E172 formal baseline from the 10-row Qwen checkpoint, then run Qwen hidden-gate formal. / 从 Qwen 10 行 checkpoint 续跑或重跑正式 baseline，再跑 Qwen 正式 hidden-gate。
- Start Gemma4-31B and Gemma4-26B-A4B E172 runs only after Qwen state is cleanly checkpointed or marked failed, to avoid mixing partial state. / 先把 Qwen 状态干净 checkpoint 或标记失败，再启动两个 Gemma，避免混淆 partial 状态。
- For hidden-gate, report trigger precision/false positives, trigger timing, final-marker rate, hit-max rate, and paired gate-vs-baseline accuracy before any improvement claim. / hidden-gate 必须先报告触发精度/假阳性、触发时机、final-marker、hit-max 和 paired gate-vs-baseline 准确率，再谈提升 claim。
