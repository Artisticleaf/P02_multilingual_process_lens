# P02 History KG R6 / P02 项目历史知识图谱 R6

Date / 日期: 2026-04-27 CST  
Working directory / 工作目录: `/home/Awei/P02_multilingual_process_lens`  
R6 stage / R6 阶段: `S6 lexical causality, verifier objective, and hidden-span mechanism consolidation` / `S6 词汇因果、verifier 目标与 hidden-span 机制整合`。

## 0. Current Claim / 当前主张

English: Multilingual surface lexicalization can create answer-correct but process-invalid trace-selection risk. This risk is not just wrong answer or bad format; it can come from mismatch among surface lexicalization, process semantics, and verifier objective/threshold. In selected real traces, process/error-span signals can be exposed by sibling comparison or residual/module span patching, while absolute Yes/No verifiers often over-accept. / 中文：多语言表层词汇化会产生“答案正确但过程无效”（ACPI）的轨迹选择风险。这个风险不只是答案错或格式坏，而可能来自表层词汇化、过程语义、verifier 目标/阈值之间的错配。在选择后的真实 trace 中，过程/错误 span 信号可被 sibling comparison（兄弟对比）或 residual/module span patch（残差/模块 span patch）暴露，但 absolute Yes/No verifier（绝对式是/否验证器）常常过度接受。

R6 refinement / R6 细化：S6 now gives controlled lexical evidence: `pay 75%`, `75% off`, `打八折/pay80`, and `80% discount/pay20` can flip local process semantics while preserving the final number. / S6 给出了受控词汇证据：`pay 75%`、`75% off`、`打八折/pay80`、`80% discount/pay20` 会翻转局部过程语义，同时最终数字可能保持正确。

## 1. Active Mainlines / 当前五条主线

| Mainline / 主线 | R6 status / R6 状态 | Plain meaning / 人话解释 |
|---|---|---|
| A. Real ACPI existence / 真实 ACPI 存在 | Strong selected evidence. E05/E18 found ACPI; S6 added 3 paper-grade lexical ACPI rows. / 选择集证据强；S6 新增 3 条论文级词汇 ACPI。 | Real generated traces can look answer-correct and format-valid while containing a wrong process sentence. / 真实生成 trace 可以答案对、格式也对，但过程句错。 |
| B. Verifier over-acceptance / verifier 过度接受 | Strong. E24 had 8/8 selected ACPI over-accepted; S6 selected ACPI false-accept is 1.0 for Gemma4, Qwen14, and Qwen3.5-27B absolute process prompts. / 证据强；S6 中 Gemma4、Qwen14、Qwen3.5-27B 绝对式过程提示对选择 ACPI 全接受。 | A pointwise Yes/No judge is too permissive for this failure family. / 单点 Yes/No 判断对这类错误过于宽松。 |
| C. Lexical causality / 词汇因果性 | Stronger after S6. Errors concentrate in pay/off discount wording; ratio and derivative controls stay clean in S6. / S6 后更强；错误集中在折扣 pay/off 表述，比例和导数控制题干净。 | The problem is surface meaning, not just arithmetic difficulty. / 问题来自表层语义，不只是算术难度。 |
| D. Hidden process/error signal / 隐藏过程/错误信号 | Positive but bounded. S6 Qwen14 support/error span L14 patch is strong (`+2.750`, `-1.000`); Gemma patch effects are clean but weak. / 正向但有边界；S6 Qwen14 L14 patch 强，Gemma 干净但弱。 | The model/verifier state contains some local error information even when final Yes/No accepts. / 即使最终 Yes/No 接受，模型/verifier 状态中仍有局部错误信息。 |
| E. Sibling mitigation / sibling 缓解 | Useful but not universal. Qwen-family contrastive helps on some pairs; Gemma4 and Qwen3.5-27B show A-position bias on Gemma pairs. / 有用但不万能；Qwen 系在部分 pair 有帮助，Gemma4 与 Qwen3.5-27B 在 Gemma pair 上有 A 位置偏差。 | Pairwise comparison must be order-balanced and conservative. / 对比式必须平衡顺序并保守处理。 |

## 2. Evidence Ledger / 证据台账

| ID / 编号 | Artifact / 产物 | Finding / 发现 | Interpretation / 解释 |
|---|---|---|---|
| Archive / 归档 | `archive/project_status_20260427_pre_R4/`, `archive/project_status_20260427_pre_R5/`, `archive/project_status_20260427_pre_R6/` | Old project status snapshots were archived. / 旧项目状态快照已归档。 | Active memory now points to R6. / 当前记忆指向 R6。 |
| E24 causal ledger / E24 因果台账 | `reports/E24_s4_causal_chain_ledger.md` | 9 pairs; 8 manual ACPI; 8/8 absolute-overaccepted; 7/8 contrastive signal; 6/8 hidden-span signal; 2/8 MLP signal. / 9 对；8 对人工 ACPI；8/8 绝对式过度接受；7/8 有对比信号；6/8 有 hidden span 信号；2/8 有 MLP 信号。 | Best pre-S6 causal-chain table, selected-pair only. / S6 前最佳因果链表，但仅代表选择集。 |
| E25 layerwise lens / E25 分层 lens | `reports/E25_layerwise_verifier_lens_summary.md` | Middle-layer signal can drop or flip at output. / 中层信号可能在输出端下降或翻转。 | Supports output-head/objective re-entanglement hypothesis. / 支持输出头/目标再纠缠假设。 |
| E26 AIME boundary / E26 AIME 边界 | `reports/E26_aime_hard_smoke_audit_summary.md` | 48 AIME-style rows; strict final-correct = 0; ACPI = 0. / 48 行 AIME 风格；严格答案正确为 0；ACPI 为 0。 | Hard-task ACPI cannot be estimated until final-correct hard traces exist. / 在有 final-correct 难题 trace 前，不能估计难题 ACPI。 |
| E27 transfer / E27 迁移 | `reports/E27_transfer_absolute_verifier_summary.md`, `reports/E27_transfer_contrastive_verifier_summary.md` | Qwen3.5-27B and Gemma4 over-accept selected ACPI absolutely; Qwen3.5-27B contrastive acc 0.875; Gemma4 has A-position bias. / Qwen3.5-27B 与 Gemma4 绝对式过度接受；Qwen3.5-27B 对比准确率 0.875；Gemma4 有 A 位置偏差。 | Transfer supports objective mismatch but also reveals model-specific contrastive bias. / 迁移支持目标错配，也显示模型特异对比偏差。 |
| S6 lexical audit / S6 词汇审计 | `reports/S6_lexical_paraphrase_grid_audit.md` | 192 rows; Gemma4 has 2 paper-grade ACPI; Qwen14 has 1 paper-grade ACPI; controls are mostly clean. / 192 行；Gemma4 有 2 条论文级 ACPI；Qwen14 有 1 条论文级 ACPI；控制题基本干净。 | Controlled lexical grid strengthens lexical-causality story. / 受控词汇网格强化词汇因果故事。 |
| S6 verifier objective / S6 verifier 目标 | `results/S6_lexical_grid_absolute_verifier/`, `results/S6_lexical_grid_absolute_verifier_qwen27/`, `results/S6_lexical_grid_contrastive_verifier/`, `results/S6_lexical_grid_contrastive_verifier_qwen27/` | Absolute ACPI false accept: Gemma4/Qwen14/Qwen3.5-27B = 1.0 in English and Chinese prompts; contrastive helps Qwen-family partially but shows position bias. / 绝对式 ACPI 误接受：Gemma4/Qwen14/Qwen3.5-27B 中英提示均为 1.0；对比式对 Qwen 系部分有效但有位置偏差。 | Same trace evidence behaves differently under different verifier objectives. / 同一 trace 证据在不同 verifier 目标下行为不同。 |
| S6 span patch / S6 span patch | `reports/S6_lexical_grid_span_patch_summary.md` | Qwen14 pay75 pair support/error span L14: `valid->bad +2.750`, `bad->valid -1.000`; Gemma effects weak but clean. / Qwen14 pay75 pair 的 support/error span L14：`valid->bad +2.750`，`bad->valid -1.000`；Gemma 弱但方向干净。 | Strong new hidden-span causal evidence for one lexical ACPI pair. / 一个词汇 ACPI pair 上有强 hidden-span 因果证据。 |
| S6 layerwise lens / S6 分层 lens | `reports/S6_lexical_grid_layerwise_lens_summary.md` | Diagnostic lens shows middle target-positive signals that can be lost before final A/B or Yes/No decision. / 诊断 lens 显示中层 target-positive 信号可能在最终 A/B 或 Yes/No 决策前丢失。 | Supports middle-layer confounding and output objective re-entanglement, not full circuit proof. / 支持中层混杂和输出目标再纠缠，但不是完整 circuit 证明。 |
| S6 literature / S6 文献 | `docs/LITERATURE_S6_POST_GRID_COLLISION_REVIEW_20260427.md` | New papers increase collision risk for broad CoT faithfulness, process/outcome mismatch, and PRM claims. / 新文献提高了泛化 CoT 忠实性、过程-结果错配和 PRM 主张的撞车风险。 | Keep novelty narrow: multilingual lexical ACPI + objective mismatch + hidden-span causality + boundaries. / 创新点要收窄为多语言词汇 ACPI + 目标错配 + hidden-span 因果性 + 边界。 |
| S6 integrated report / S6 综合报告 | `reports/S6_INTEGRATED_SCIENTIFIC_ANALYSIS_AND_NEXT_PLAN_20260427.md` | Human-readable synthesis of results, novelty, boundaries, and next experiments. / 人话综合结果、创新点、边界和后续实验。 | Use this as current communication report. / 当前沟通优先使用此报告。 |

## 3. Mechanistic Hypotheses After S6 / S6 后的机制假设

1. Middle-layer process confounding / 中层过程混杂：middle layers can represent both surface lexical cues and local process semantics; lexical traps can make these cues conflict. / 中层可能同时表示表层词汇线索与局部过程语义；词汇陷阱会使二者冲突。
2. Output-head/objective re-entanglement / 输出头/目标再纠缠：even if middle layers contain error evidence, the final Yes/No or A/B objective can reweight it with final-answer correctness, fluency, language prior, or position bias. / 即使中层含错误证据，最终 Yes/No 或 A/B 目标也可能把它与答案正确性、流畅度、语言先验或位置偏差重新加权。
3. Support/error-span causality / 支持/错误 span 因果性：on robust sibling pairs, replacing hidden representations of local support/error spans causally moves verifier margins. / 在稳健 sibling pair 上，替换局部 support/error span 的隐藏表征会因果移动 verifier margin。

## 4. Research Boundaries / 科研边界

- Selected-set rates are not population prevalence. / 选择集比例不是总体发生率。
- S6 proves controlled lexical vulnerability for Gemma4/Qwen14 under tested prompts, not universal model behavior. / S6 证明的是测试提示下 Gemma4/Qwen14 的受控词汇脆弱性，不是所有模型的普遍行为。
- Qwen3.5-9B and DeepSeek generator failures are prompt/template boundaries, not negative scientific evidence. / Qwen3.5-9B 与 DeepSeek 生成失败是提示/模板边界，不是科学阴性结论。
- Layerwise lens is diagnostic, not a trained tuned lens or circuit proof. / 分层 lens 是诊断工具，不是训练过的 tuned lens 或 circuit 证明。
- AIME hard-task branch remains a boundary until final-correct hard traces are obtained. / AIME 难题分支在获得 final-correct hard trace 前仍是边界。

## 5. Next Experiments / 下一步实验

1. Larger lexical pair bank / 更大词汇 pair bank：expand to at least 20 paper-grade clean ACPI/valid sibling pairs across discount, ratio, derivative, and translation families. / 扩展到至少 20 对论文级干净 ACPI/valid sibling，覆盖折扣、比例、导数和翻译族。
2. Error-span extraction verifier / 错误 span 抽取 verifier：ask models to mark the first invalid phrase before Yes/No; compare against absolute and contrastive prompts. / 要求模型先标出第一处无效短语，再判断；与绝对式和对比式比较。
3. Head/MLP/SAE mechanism / 头、MLP、SAE 机制：decompose robust S6 Qwen14 L14 and prior E22 robust spans into attention head, MLP block, and optional SAE/transcoder features. / 将稳健 S6 Qwen14 L14 与 E22 span 分解到 attention head、MLP block 与可选 SAE/transcoder 特征。
4. Hard-task final-correct conditioning / 难题 final-correct 条件化：use Qwen3.5-27B/Gemma4 plus verifier-guided sampling on AIME24/25 until final-correct traces exist; then audit process validity. / 用 Qwen3.5-27B/Gemma4 与 verifier-guided sampling 在 AIME24/25 上先得到 final-correct trace，再审计过程有效性。
5. Prompt-template repair / 提示模板修复：repair Qwen3.5-9B and DeepSeek generator prompts and rerun only S6 lexical grid first. / 修复 Qwen3.5-9B 与 DeepSeek 生成提示，先只复跑 S6 词汇网格。

## 6. Validation Status / 验证状态

R6 validation will be run after doc updates. / R6 文档更新后会运行验证。

## 7. R6 Validation Result / R6 验证结果

Validation run on 2026-04-27 after S6/R6 updates passed. / S6/R6 更新后已在 2026-04-27 运行验证并通过。

- `python -m py_compile` passed for S6 audit, generation, verifier, contrastive verifier, span patch, and layerwise lens scripts. / S6 审计、生成、verifier、对比 verifier、span patch 与分层 lens 脚本通过 `py_compile`。
- `bash -n` passed for new S6 launch scripts. / 新 S6 启动脚本通过 `bash -n`。
- `python scripts/check_project.py` passed in `passage_prep_py312`. / `passage_prep_py312` 环境下 `python scripts/check_project.py` 通过。
- GPUs were idle after cleanup: GPU0 17 MiB, GPU1 2 MiB, GPU2 2 MiB, GPU3 2 MiB. / 清理后 GPU 空闲：GPU0 17 MiB，GPU1 2 MiB，GPU2 2 MiB，GPU3 2 MiB。
- Completed S6 tmux sessions were closed. / 已关闭完成的 S6 tmux 会话。

## 8. S7 Pre-Experiment Claim Audit / S7 实验前主张审计

Stage material / 阶段性材料: `reports/S7_CLAIM_AUDIT_AND_HIGH_INFORMATION_EXPERIMENT_PLAN_20260427.md`.

Key judgement / 关键判断：the current claim is strongest when written as a causal chain rather than as a generic CoT/verifier failure. / 当前主张最强的写法是因果链，而不是泛泛的 CoT/verifier 失败。

- Strong side / 优势：the lexical ACPI family is concrete, controlled, and supported by S6 real traces, absolute verifier over-acceptance, and one strong Qwen14 hidden-span causal patch. / 优势是词汇 ACPI 族具体、可控，并有 S6 真实 trace、绝对式过度接受和一个强 Qwen14 hidden-span patch 支持。
- Weak side / 薄弱点：paper-grade ACPI count remains small, discount examples may look narrow, hidden-layer evidence is not yet head/MLP/feature-level, and verifier failure is not fully decomposed into answer bias, Yes bias, language prior, and position bias. / 薄弱点是论文级 ACPI 数量仍少，折扣例子可能显得窄，隐藏层证据还不是 head/MLP/feature 级，verifier 失败还未拆成答案偏置、Yes 偏置、语言先验和位置偏差。
- Next high-information sequence / 下一高信息收益顺序：counterfactual trace editing, answer masking, error-span extraction verifier, larger lexical minimal-pair bank, then head/MLP/SAE mechanism decomposition and hard-task final-correct conditioning. / 下一步优先做反事实 trace 编辑、答案遮蔽、错误 span 抽取、更大词汇最小对，再做 head/MLP/SAE 机制分解与难题 final-correct 条件化。

## 9. S7 Task/Verifier Survey And E28/E29 Results / S7 任务/verifier 调研与 E28/E29 结果

Survey / 调研: `docs/S7_TASK_AND_VERIFIER_PIPELINE_SURVEY_20260427.md`.

Key survey judgement / 关键调研判断：

- Discount/percentage tasks are common in math reasoning benchmarks, but the exact multilingual lexical ACPI family (`打八折=pay80`, `80% discount=pay20`, `sold for 75%=pay75`) was not found as the central claim of major 2023-2026 process/verifier benchmarks. / 折扣/百分比题在数学推理基准里常见，但没有发现主流 2023-2026 过程/verifier 基准把上述多语言词汇 ACPI 作为核心主张。
- The chain `L -> P -> A -> H -> V` is not a universal law for all LLM use; it is a risk model for verifier/selector-mediated reasoning pipelines. / `L -> P -> A -> H -> V` 不是所有 LLM 使用的普适定律，而是 verifier/selector 介入推理管线的风险模型。
- Verifier/selector stages are common in best-of-N, PRM/ORM, LLM-as-judge, test-time search, and training-data filtering, so the scenario is not artificial even though it is conditional. / verifier/selector 阶段在 best-of-N、PRM/ORM、LLM-as-judge、测试时搜索和训练数据过滤中常见，因此这个场景不是人为臆造，但它是条件式主张。

E28 / E28：counterfactual lexical editing and answer masking / 反事实词汇编辑与答案遮蔽。

- Data / 数据: `data/processed/e28_counterfactual_answer_masking_20260427.jsonl` with 18 rows: 3 lexical trap families × valid/invalid process × correct/masked/wrong final answer. / 18 行：3 个词汇陷阱族 × 有效/无效过程 × 正确/遮蔽/错误最终答案。
- Report / 报告: `reports/E28_counterfactual_answer_masking_summary.md`.
- Main result / 主要结果：for all four verifiers, changing only the invalid lexical phrase almost always lowered the Yes-minus-No margin, but often did not cross the rejection threshold. / 四个 verifier 中，仅替换无效词汇短语几乎总会降低 Yes-minus-No 边际，但通常没有跨过拒绝阈值。
- Concrete numbers / 具体数字：ACPI false accept under process-only prompts remained high: Gemma4 1.000/1.000 (en/zh), Qwen3.5-27B 1.000/0.667, Qwen3.5-9B 0.667/0.667, Qwen14 0.667/1.000. / 只审过程提示下 ACPI 误接受仍高。
- Interpretation / 解释：E28 strengthens the threshold/objective mismatch claim: the verifier has graded evidence against invalid lexical phrases, but the final binary decision over-accepts, especially when the final answer is correct. / E28 强化了阈值/目标错配：verifier 对无效词汇短语有连续信号，但最终二值决策仍过度接受，尤其答案正确时。

E29 / E29：error-span extraction verifier / 错误 span 抽取 verifier。

- Data / 数据: `data/processed/e29_error_span_evalset_s6_plus_e28_20260427.jsonl` with 24 rows: 6 S6 real rows plus 18 E28 counterfactual rows. / 24 行：6 条 S6 真实行 + 18 条 E28 反事实行。
- Report / 报告: `reports/E29_error_span_extraction_verifier_summary.md`.
- Main result / 主要结果：locate-then-judge prompts were more informative than absolute Yes/No: Qwen3.5-9B and Qwen3.5-27B reached span accuracy around 0.667/0.667 and 0.583/0.500 (en/zh), respectively, but still missed many invalid spans. / locate-then-judge 比绝对 Yes/No 更有信息量：Qwen3.5-9B 与 Qwen3.5-27B 的 span accuracy 分别约为 0.667/0.667 与 0.583/0.500（英/中），但仍漏掉不少错误 span。
- Task-level fact / 任务层事实：`75% discount` was easiest to expose; `打八折=支付75%` remained hardest and caused many false positives or `NONE` acceptances. / `75% discount` 最容易暴露；`打八折=支付75%` 最难，常出现误报或 `NONE` 接受。
- Boundary / 边界：generation-format instability is significant for Gemma4 and Qwen3.5 locate-only prompts; E29 should be treated as a diagnostic, not a clean benchmark. / Gemma4 与 Qwen3.5 的 locate-only 生成格式不稳；E29 应作为诊断实验，不应当成干净 benchmark。

Scientific update / 科学更新：S7 now has causal-chain evidence at the text/verifier-output level: local lexical invalidity reduces hidden/output margins (E28), while explicit span prompts sometimes expose the error and sometimes reveal that the model names suspicious text but still accepts (E29). / S7 现在在文本/verifier 输出层面补上因果链证据：局部词汇无效性会降低 hidden/output 边际（E28），显式 span 提示有时暴露错误，也有时暴露“指出可疑文本但仍接受”（E29）。

## 10. S7/E28/E29 Validation Result / S7/E28/E29 验证结果

Validation run / 验证运行: `logs/check_project_s7_e28_e29_20260427.json`.

- `python -m py_compile` passed for E28/E29 build, run, and summarization scripts. / E28/E29 构造、运行与汇总脚本通过 Python 编译检查。
- `python scripts/check_project.py` passed in `passage_prep_py312`. / `passage_prep_py312` 环境下 `python scripts/check_project.py` 通过。
- GPUs were idle after cleanup: GPU0 17 MiB, GPU1 2 MiB, GPU2 2 MiB, GPU3 2 MiB. / 清理后 GPU 空闲：GPU0 17 MiB，GPU1 2 MiB，GPU2 2 MiB，GPU3 2 MiB。
- No new training/evaluation leakage was introduced: E28 is a manually constructed diagnostic counterfactual set derived from S6 selected examples, not a training set; E29 uses only S6/E28 audited rows. / 未引入新的训练/评估泄露：E28 是由 S6 选择样例派生的人工诊断反事实集，不是训练集；E29 只使用 S6/E28 审计行。

## 11. E30/E31 Non-Discount Expansion / E30/E31 非折扣扩展

E30 natural non-discount grid / E30 自然非折扣网格：

- Config and data / 配置与数据: `configs/e30_non_discount_lexical_grid.yaml`, `data/raw/e30_non_discount_lexical_grid_trace_pool/`, `data/processed/e30_non_discount_grid_manual_audit_20260427.jsonl`.
- Audit report / 审计报告: `reports/E30_non_discount_lexical_grid_audit.md`.
- Scope / 范围: 24 non-discount task families × 2 routes × 2 samples × 4 generator models = 384 rows. / 24 个非折扣任务族 × 2 条 route × 每格 2 条样本 × 4 个生成模型 = 384 行。
- Main finding / 主要发现: clean natural non-discount ACPI was rare in this first pass; only one paper-grade row was promoted, Qwen14 `inequality_no_more_than` row `300311`. / 第一轮干净自然非折扣 ACPI 很少；只提升 1 条论文级样例，即 Qwen14 的 `inequality_no_more_than` 行 `300311`。
- Concrete error / 具体错误: the problem says “greater than 3 and no more than 7”; the trace says “between 3 and 7, inclusive”, which would include 3, but then lists 4,5,6,7 and gives final answer 4. / 题目说“大于 3 且不超过 7”；trace 说 “between 3 and 7, inclusive”，这会包含 3，但后面又列出 4,5,6,7 并给出正确答案 4。
- Boundary fact / 边界事实: unit semantics produced strong drift, especially “3 dozen socks” treated as 36 pairs instead of 36 individual socks, but those rows were final-wrong rather than ACPI. / 单位语义产生强漂移，尤其是把“3 打袜子”当作 36 双而不是 36 只，但这些行答案错，不是 ACPI。

E30 verifier and mechanism probes / E30 verifier 与机制 probe：

- Verifier report / verifier 报告: `reports/E30_non_discount_verifier_summary.md`.
- Span patch report / span patch 报告: `reports/E30_non_discount_span_patch_summary.md`.
- Main verifier result / 主要 verifier 结果: all four absolute verifiers accepted the one non-discount ACPI row under both English and Chinese prompts; contrastive verification exposed some signal but also strong position bias. / 四个绝对式 verifier 在中英提示下都接受了这条非折扣 ACPI；对比式验证暴露了一些信号，但也有强位置偏置。
- Mechanism boundary / 机制边界: Qwen14 span patch on the E30 inequality pair showed large but unclean directionality, so it should be treated as a negative-control/boundary result rather than the main mechanism anchor. / E30 不等式 pair 的 Qwen14 span patch 效应大但方向不干净，应作为负控/边界，而不是主机制锚点。

E31 controlled non-discount counterfactuals / E31 受控非折扣反事实：

- Builder and data / 构造脚本与数据: `scripts/build_e31_non_discount_counterfactual.py`, `data/processed/e31_non_discount_counterfactual_20260427.jsonl`.
- Absolute verifier report / 绝对式 verifier 报告: `reports/E31_non_discount_counterfactual_summary.md`.
- Error-span report / 错误 span 报告: `reports/E31_non_discount_error_span_summary.md`.
- Design / 设计: 5 traps × valid/invalid process × correct/masked/wrong final answer = 30 rows. / 5 类陷阱 × 有效/无效过程 × 正确/遮蔽/错误最终答案 = 30 行。
- Trap families / 陷阱族: ratio denominator, inequality boundary, dozen/pairs unit, diameter/radius geometry, and unordered committee combinatorics. / 陷阱族包括比例分母、边界量词、打/双单位、直径/半径几何、不区分顺序的组合。
- Absolute process-only ACPI false accept / 绝对式只审过程 ACPI 误接受: Gemma4 1.000/1.000, Qwen3.5-27B 1.000/0.800, Qwen3.5-9B 0.600/0.800, Qwen14 0.200/0.600 for English/Chinese prompts. / 中英提示下分别为 Gemma4 1.000/1.000、Qwen3.5-27B 1.000/0.800、Qwen3.5-9B 0.600/0.800、Qwen14 0.200/0.600。
- Margin fact / 边际事实: invalid local phrases almost always lowered the Yes-minus-No margin relative to valid siblings; for example Qwen3.5-27B English correct rows had a -1.950 invalid-valid delta, but still accepted all ACPI rows. / 无效局部短语几乎总会相对有效 sibling 压低 Yes-minus-No 边际；例如 Qwen3.5-27B 英文正确答案行的 invalid-valid delta 为 -1.950，但仍接受全部 ACPI。
- Trap-level fact / 陷阱层事实: inequality boundary was accepted by all four verifiers in both prompt languages; unit dozen/pairs was hardest to over-accept in Chinese but hardest to localize automatically. / 边界量词陷阱在两种提示语言下被四个 verifier 全部接受；打/双单位在中文下最不容易被过度接受，但也最难自动定位。

E31 span-extraction update / E31 span 抽取更新：

- Strong diagnostic result / 强诊断结果: Qwen3.5-27B locate-then-judge reached invalid span hit 0.733/0.800 and invalid reject rate 0.933/1.000 in English/Chinese prompts. / Qwen3.5-27B 的 locate-then-judge 中英提示无效 span 命中率为 0.733/0.800，无效拒绝率为 0.933/1.000。
- Contrast with absolute verification / 与绝对式对照: the same Qwen3.5-27B absolute process-only prompt accepted all English ACPI rows and 0.800 Chinese ACPI rows. / 同一个 Qwen3.5-27B 的绝对式只审过程提示接受全部英文 ACPI 行和 0.800 中文 ACPI 行。
- Interpretation / 解释: the evidence supports an objective/threshold story, not a pure blindness story: stronger localization objectives can recover errors that pointwise Yes/No over-accepts. / 这支持目标/阈值错配，而不是“完全看不见错误”：更强的定位目标可以恢复绝对 Yes/No 过度接受的错误。

Scientific update / 科学更新：E30 and E31 sharpen the claim. Natural non-discount ACPI does not appear everywhere, so the paper should not claim broad prevalence. But controlled non-discount traps show the same causal pattern: local process semantics can be wrong while the answer remains correct; absolute verifiers often accept; span/objective changes can expose hidden evidence. / E30 与 E31 细化了主张。自然非折扣 ACPI 不是到处都有，所以论文不应声称广泛发生率。但受控非折扣陷阱显示同样因果模式：局部过程语义可以错而答案仍正确；绝对式 verifier 常接受；span/目标变化可以暴露隐藏证据。

## 12. E30/E31 Validation Result / E30/E31 验证结果

Validation run / 验证运行: `logs/check_project_e30_e31_20260427.json`.

- `python -m py_compile` passed for E30 audit/summarization, E31 construction/summarization, and span-extraction scripts. / E30 审计/汇总、E31 构造/汇总与 span 抽取脚本通过 Python 编译检查。
- `python scripts/check_project.py` passed in `passage_prep_py312`. / `passage_prep_py312` 环境下 `python scripts/check_project.py` 通过。
- E31 integrity audit passed: 30 rows, 30 unique `audit_idx`, 5 tasks, balanced 5-per-variant design, and four complete absolute/error-span result files. Log: `logs/e31_integrity_audit_20260427.txt`. / E31 完整性审计通过：30 行、30 个唯一 `audit_idx`、5 个任务、每个变体 5 行均衡设计，且四个绝对式/错误 span 结果文件完整。日志：`logs/e31_integrity_audit_20260427.txt`。
- GPUs were idle after cleanup: GPU0 17 MiB, GPU1 2 MiB, GPU2 2 MiB, GPU3 2 MiB. / 清理后 GPU 空闲：GPU0 17 MiB，GPU1 2 MiB，GPU2 2 MiB，GPU3 2 MiB。
- No new leakage risk was introduced: E31 is a manually constructed diagnostic set for verifier behavior, not a training set or a benchmark-test submission; E30 raw generations and audits are stored separately. / 未引入新的数据泄露风险：E31 是人工构造的 verifier 行为诊断集，不是训练集或基准提交；E30 原始生成与审计分开保存。

## 13. E32 Gemma4 Medium Four-GPU Status / E32 Gemma4 中型模型四卡状态

Stage report / 阶段报告: `reports/E32_gemma4_medium_4gpu_status_20260427.md`.

Operational status / 运行状态：2026-04-27 22:07-22:16 CST 没有发现训练或实验卡死。GPU 基本空闲，真正运行的是 `gemma4_31b_it` 下载进程 PID `756393`。下载文件持续增长，说明不是卡死。 / 2026-04-27 22:07-22:16 CST 没有发现训练或实验卡死。GPU 基本空闲，真正运行的是 `gemma4_31b_it` 下载进程 PID `756393`。下载文件持续增长，说明不是卡死。

Four-GPU runner / 四卡运行器：新增 `scripts/launch_blackbox_4gpu_suite.sh`。它默认使用 `MPLENS_BACKEND=auto`：vLLM 支持的模型走四卡 vLLM；Gemma4 等当前 vLLM 不兼容模型自动走 HuggingFace `device_map=auto`。 / 新增统一四卡黑箱 verifier 运行器，自动在 vLLM 与 HuggingFace 四卡之间选择。

vLLM boundary / vLLM 边界：`gemma4_26b_a4b_it` 在 vLLM 0.12.0 下无法稳定加载；补充 `top_k` 后仍因 `model.language_model.layers.0.layer_scalar` 权重名不匹配失败。HF 四卡加载通过。 / Gemma4-26B-A4B 当前不能强制走 vLLM，但 HuggingFace 四卡可以跑通。

Gemma4-26B-A4B results / Gemma4-26B-A4B 结果：S6/E28/E30/E31 核心绝对 verifier 已完成，输出在 `results/*_hf/gemma4_26b_a4b_it_manual_trace_verifier.json`。 / S6/E28/E30/E31 核心绝对 verifier 已完成。

Key scientific fact / 关键科学事实：26B-A4B 在 S6 process-only 下 ACPI 误接受率英/中均为 1.000；E30 唯一自然非折扣 ACPI 也英/中均为 1.000；E31 受控非折扣 process-only ACPI 误接受英/中均为 0.800。 / 26B-A4B 不是简单消除风险，正确答案仍会显著掩盖局部过程错误。

Interpretation / 解释：模型变大可以改变阈值和严格程度，但没有消除 ACPI trace-selection 风险；同一模型在 process-only、training-candidate、英文、中文提示之间的差异继续支持 verifier objective/threshold mismatch。 / 模型规模影响阈值，但不消除目标/阈值错配。

Gemma4-31B status / Gemma4-31B 状态：`gemma4_31b_it` 仍在下载；已启动 tmux 会话 `gemma31_postdownload`，下载完成并检查完整后自动运行 `scripts/launch_blackbox_4gpu_suite.sh gemma4_31b_it core`。 / 31B 下载完成后会自动跑同套四卡核心实验。

## 14. E33 S6 Qwen14 Mechanism Deep Dive / E33 S6 Qwen14 机制深挖

Stage report / 阶段报告: `reports/E33_s6_qwen14_mechanism_deep_dive_20260427.md`.

Goal / 目标：decompose the strongest S6 Qwen14 ACPI pair `qwen14_s6_pay75_bad150_valid151` beyond residual patch, asking whether the process signal lives in middle residual stream, MLP, attention, or a single head. / 将最强 S6 Qwen14 ACPI pair `qwen14_s6_pay75_bad150_valid151` 从 residual patch 进一步分解，判断过程信号是在中层残差、MLP、attention 还是单个 head。

Dense residual result / dense residual 结果：support/error span patch across all 40 layers shows a broad clean middle band. Effects rise from L0 `+0.875/-0.875`, peak around L12-L14 at `+2.750/-1.000`, and decay after L20 to near zero by late layers. / 40 层 dense residual support/error span patch 显示宽中层干净信号带：从 L0 的 `+0.875/-0.875` 上升，在 L12-L14 达到 `+2.750/-1.000`，L20 后衰减，后层接近 0。

Module result / module 结果：attention-vs-MLP patch finds the strongest clean module at L14 MLP on the support/error span, `valid->bad +0.375`, `bad->valid -0.125`; L9 MLP and L9/L14 attention also have weaker clean effects. / attention-vs-MLP patch 中最强干净 module 是 L14 MLP 的 support/error span，`valid->bad +0.375`、`bad->valid -0.125`；L9 MLP 和 L9/L14 attention 有较弱干净效应。

Head result / head 结果：pre-o_proj attention-head scan over L9/L14/L20 finds many directionally clean heads but no dominant single head; best is L9 H14 at `+0.125/-0.125`, far smaller than residual patch. / L9/L14/L20 的 pre-o_proj 单 attention head 扫描发现许多方向干净的 head，但没有主导单头；最强 L9 H14 只有 `+0.125/-0.125`，远小于 residual patch。

Mechanistic interpretation / 机制解释：the process/error-span signal appears as a distributed middle residual-state signal with MLP participation, not as a single-head explanation. This strengthens the claim that absolute Yes/No over-acceptance is not pure blindness: hidden process evidence exists, but final objective/threshold/output re-entanglement underuses it. / 过程/error-span 信号更像分布式中层残差状态并有 MLP 参与，而不是单头解释。这强化了“绝对式 Yes/No 过度接受不是纯看不见”：隐藏过程证据存在，但最终目标/阈值/输出重整没有充分使用它。

Files / 文件：`results/S6_lexical_grid_span_patch_dense/qwen3_14b_base_real_acpi_span_patch.json`, `results/S6_lexical_grid_module_patch/qwen3_14b_base_real_acpi_module_patch.json`, `results/S6_lexical_grid_attention_head_patch/qwen3_14b_base_real_acpi_attention_head_patch.json`, and `scripts/run_real_acpi_attention_head_patch.py`. / 相关文件已落盘。

## 15. E34 E31 Non-Discount Mechanism Generalization / E34 E31 非折扣机制泛化

Stage report / 阶段报告: `reports/E34_e31_non_discount_mechanism_generalization_20260427.md`.

Goal / 目标：test whether the hidden process/error-span causal signal found in S6 discount ACPI also appears in E31 non-discount traps. / 测试 S6 折扣 ACPI 中发现的 hidden process/error-span 因果信号是否也出现在 E31 非折扣陷阱中。

Data / 数据：five E31 controlled traps: ratio denominator, inequality boundary, dozen/pairs unit semantics, diameter/radius geometry, and unordered committee combinatorics. / 五类 E31 受控陷阱：比例分母、边界不等式、打/双单位、直径/半径几何、无序组合。

Qwen14 result / Qwen14 结果：4/5 traps show strong clean residual span-patch signals. Best effects are ratio L4 `+1.500/-1.625`, unit L11 `+1.125/-1.375`, geometry L4 `+3.000/-1.625`, combinatorics L10 `+2.125/-1.750`. Inequality is the boundary: bad margin stays high at `+2.500` and best clean patch is only about `+0.250/-0.375`. / Qwen14 中 4/5 类陷阱有强干净 residual span-patch 信号；不等式是边界，bad margin 高且 patch 弱。

Qwen3.5-9B result / Qwen3.5-9B 结果：the model over-accepts more invalid-correct traces, but hidden patch signals still exist. Geometry bad margin is `+1.938` and best patch `+0.500/-3.000`; combinatorics bad margin is `+1.125` and best patch `+2.250/-3.438`; inequality bad margin is `+2.750` with asymmetric weak `valid->bad` but negative `bad->valid`. / Qwen3.5-9B 过度接受更多 invalid-correct trace，但 hidden patch 信号仍存在；几何和组合尤其明显，不等式仍是弱点。

Interpretation / 解释：the hidden process signal generalizes beyond discount, but not uniformly. Strong residual process signals often align with rejection; weak or re-entangled signals, especially inequality boundary wording, align with over-acceptance. This supports a graded objective/threshold mismatch story rather than all-or-none blindness. / hidden process 信号能泛化到折扣之外，但不均匀；强 residual 过程信号常对应拒绝，弱或被重整的信号，尤其边界量词，常对应过度接受。这支持连续的目标/阈值错配，而不是全有全无的失明。

Files / 文件：`configs/e31_non_discount_span_patch_pairs.yaml`, `configs/e31_non_discount_span_patch_pairs_qwen35_9b.yaml`, `results/E34_e31_non_discount_span_patch_dense/qwen3_14b_base_real_acpi_span_patch.json`, `results/E34_e31_non_discount_span_patch_dense/qwen35_9b_real_acpi_span_patch.json`. / 相关文件已落盘。

## 16. E35 E31 Qwen3.5-9B Module Patch / E35 E31 Qwen3.5-9B 模块分解

Stage report / 阶段报告: `reports/E35_e31_qwen35_module_patch_20260427.md`.

Goal / 目标：decompose E34's Qwen3.5-9B E31 residual span signals into `linear_attn`, full `self_attn`, and `mlp` module outputs. / 将 E34 中 Qwen3.5-9B 的 E31 residual span 信号分解到 `linear_attn`、full `self_attn` 和 `mlp` 模块输出。

Result / 结果：single-module effects are much smaller than residual patch effects. The strongest module result is ratio L0 `linear_attn` at `+1.500/-0.125`; inequality has weak clean module signals around `+0.188/-0.187`; geometry best MLP is L8 `+0.312/-0.062`; combinatorics has weak linear-attn/MLP signals around `+0.500/+0.000` and `+0.375/-0.000`. / 单模块效应显著小于 residual patch；最强是比例 L0 `linear_attn` 的 `+1.500/-0.125`，其他任务多为弱信号。

Interpretation / 解释：Qwen3.5-9B non-discount process evidence is distributed across early/middle residual stream, with linear-attention and MLP participation but no single-module explanation. This aligns with E33's Qwen14 conclusion and argues against overclaiming a single-head circuit. / Qwen3.5-9B 的非折扣过程证据分布在早/中层 residual stream 中，有 linear-attention 和 MLP 参与，但不是单模块解释；这与 E33 的 Qwen14 结论一致，避免过度声称单头 circuit。

Files / 文件：`results/E35_e31_non_discount_module_patch/qwen35_9b_real_acpi_module_patch.json`; script `scripts/run_real_acpi_module_patch_smoke.py` now supports `linear_attn`. / 相关文件已落盘，module patch 脚本已支持 `linear_attn`。

## 17. E36/E37 Queued Mechanism Experiments / E36/E37 已排队机制实验

Stage report / 阶段报告: `reports/E36_E37_queued_next_mechanism_20260427.md`.

Current status / 当前状态：`gemma4_31b_it` 仍在下载，下载完成后 `gemma31_postdownload` 会先运行 `scripts/launch_blackbox_4gpu_suite.sh gemma4_31b_it core`。为避免 GPU 冲突，E36/E37 已排队在 tmux 会话 `e36_e37_after_gemma31` 中，等待 Gemma4-31B suite 结束后自动启动。 / `gemma4_31b_it` 仍在下载；31B 核心四卡 suite 会先跑，E36/E37 将在其结束后自动启动。

E36 design / E36 设计：新增 `configs/e36_inequality_boundary_span_variants.yaml`，把 E31 不等式边界 pair 拆成五个 span 变体：完整条件、下界短语、上界/端点短语、后续正确列表、错误短语+后续修正子句。 / E36 用五个 span 变体解释为什么 `between 3 and 7, inclusive` 是弱信号但高接受的边界样例。

E36 goal / E36 目标：判断 verifier 更依赖局部错误短语、后续正确枚举，还是最终答案一致的整体轨迹。若后续正确列表比错误条件更强，说明 absolute verifier 被下游修正/答案一致性拉向接受。 / E36 直接测试错误 evidence 与 correction evidence 的竞争。

E37 design / E37 设计：在 E31 非折扣 sibling pairs 上为 Qwen14 和 Qwen3.5-9B 运行 layerwise verifier logit lens，输出到 `results/E37_e31_layerwise_lens`。 / E37 检验中层 hidden evidence 是否在最终 Yes/No 输出前消失或被再纠缠。

Validation status / 验证状态：`scripts/summarize_e36_inequality_boundary.py` 已通过 `python3 -m py_compile`；E36/E37 完成后会自动运行 `scripts/check_project.py` 并写入 `logs/check_project_e36_e37_20260427.json`。 / E36 summarizer 已编译通过；完整验证会在队列完成后运行。

## 18. E38 Gemma4-31B And E36/E37 Completion / E38 Gemma4-31B 与 E36/E37 完成

Stage report / 阶段报告: `reports/E38_gemma31_e36_e37_synthesis_20260427.md`.

Operational result / 运行结果：`gemma4_31b_it` download completed after the interruption window; the local directory has two complete safetensor shards and no `*.incomplete` file. The four-GPU HF fallback suite completed S6/E28/E30/E31, and the queued E36/E37 mechanism experiments also completed. / 网络中断窗口后 `gemma4_31b_it` 下载已完成；本地目录有两个完整 safetensor 分片且没有 `*.incomplete` 文件。四卡 HF fallback 已完成 S6/E28/E30/E31，排队的 E36/E37 机制实验也已完成。

Gemma4-31B core result / Gemma4-31B 核心结果：S6 process-only ACPI false accept is `1.000/1.000` for English/Chinese prompts; E28 ACPI false accept is `1.000/1.000`; E30 one natural non-discount ACPI is `1.000/1.000`; E31 controlled non-discount ACPI false accept is `0.400/0.600`. / Gemma4-31B 在折扣词汇 ACPI 与 E30 自然非折扣 ACPI 上仍全接受；在 E31 受控非折扣上比小模型更严格，但仍接受部分 ACPI。

Gemma scale interpretation / Gemma 规模解释：Gemma4-E4B E31 ACPI false accept was `1.000/1.000`, Gemma4-26B-A4B was `0.800/0.800`, and Gemma4-31B is `0.400/0.600`. This shows scale changes the threshold but does not remove trace-selection risk. / Gemma4-E4B、26B-A4B、31B 在 E31 上依次更严格，但风险没有消失，说明规模主要改变阈值而非根除机制问题。

E31 trap-level Gemma4-31B facts / E31 陷阱级事实：English prompt accepts inequality and combinatorics but rejects ratio, unit, and geometry. Chinese prompt accepts ratio, unit, and combinatorics, rejects geometry, and rejects inequality at a zero-margin tie. / 英文提示接受不等式和组合，拒绝比例、单位、几何；中文提示接受比例、单位、组合，拒绝几何，不等式在 0 margin tie 下拒绝。

E36 inequality-boundary result / E36 不等式边界结果：Qwen3.5-9B has clean patch signals on all five span variants; strongest is the longer span containing both wrong wording and correction (`valid->bad +0.188`, `bad->valid -2.563`). Qwen14 has clean signals on 3/5 variants, with the endpoint semantic contrast `inclusive` vs `no more than 7` showing `+0.125/-1.500`. / Qwen3.5-9B 五个 span 变体都有干净 patch 信号；Qwen14 五个中三个干净，端点语义对比最明显。

E36 interpretation / E36 解释：the inequality case is not weak because the hidden process evidence is absent. It is weak because the trace contains conflicting evidence: local wording is invalid, but the following list and final answer are correct. Absolute verifiers can be pulled toward acceptance by downstream correction. / 不等式样例不是没有隐藏证据，而是错误短语与后续正确枚举共存，绝对式 verifier 被下游修正拉向接受。

E37 layerwise lens result / E37 分层 lens 结果：Qwen14 has ACPI middle-positive rate `1.000` but final-positive rate `0.500`, with mean middle-to-final drop `8.037`; Qwen3.5-9B has ACPI final-positive `0.600`, middle-positive `0.500`, drop `5.311`. Contrastive lens often preserves more target evidence than absolute lens. / Qwen14 的中层 ACPI 信号很强但最终层正向率下降；Qwen3.5-9B 也有明显中层到最终层下降。对比式 lens 常比绝对式保留更多目标证据。

Mechanistic update / 机制更新：E36/E37 strengthen the `hidden evidence exists but final objective/threshold/output-head re-entanglement underuses it` claim. This is still a diagnostic lens, not a full circuit or tuned-lens proof. / E36/E37 强化了“隐藏证据存在，但最终目标/阈值/输出头再纠缠没有充分使用”的主张；但这仍是诊断 lens，不是完整 circuit 或 tuned-lens 证明。

Validation / 验证：`python -m py_compile` passed for the new E36 summarizer, and `scripts/check_project.py` passed after E36/E37. Log: `logs/check_project_e36_e37_20260427.json`. / 新 E36 汇总脚本通过编译，E36/E37 后 `scripts/check_project.py` 通过，日志见 `logs/check_project_e36_e37_20260427.json`。

Final E38 validation / E38 最终验证：after updating the synthesis report and handoff, compile checks passed again and `scripts/check_project.py` passed with log `logs/check_project_e38_final_20260427.json`. No tmux jobs were running; GPUs were idle. / 更新综合报告与交接文档后再次通过编译检查和 `scripts/check_project.py`，日志为 `logs/check_project_e38_final_20260427.json`。无 tmux 任务，GPU 空闲。

## 19. E39 Surface-Semantic Generalization / E39 表层语义泛化

Stage report / 阶段报告: `reports/E39_surface_semantic_generalization_summary_20260428.md`.

Design / 设计：E39 is a controlled diagnostic set with 12 surface-semantic trap families and 6 variants per family, 72 rows total. The central slice is `invalid_correct`: local process semantics is wrong but the final answer is correct. / E39 是受控诊断集，包含 12 类表层语义陷阱、每类 6 个变体，共 72 行。核心切片是 `invalid_correct`：局部过程语义错误，但最终答案正确。

Families / 家族：mean vs median, range vs average, coefficient vs exponent, reciprocal vs additive inverse, percent increase vs percent-of, without replacement vs replacement, each vs total, log base vs argument, round vs truncate, Chinese perimeter vs area, Chinese 亿/万 conversion, and Chinese strict interval endpoints. / 家族包括均值/中位数、极差/平均、系数/指数、倒数/相反数、百分比增长/原价百分比、无放回/有放回、每人/总量、log 底数/真数、四舍五入/截断、中文周长/面积、亿/万换算和中文严格区间端点。

Key process-only ACPI false accept / 关键只审过程 ACPI 误接受：Qwen3.5-27B `1.000/0.833` EN/ZH, Qwen3.5-9B `0.750/0.833`, Qwen3-14B-Base `0.250/0.250`, Gemma4-31B-it `0.500/0.417`. / Qwen3.5 系列过度接受明显，Qwen14 和 Gemma31 更严格但仍接受部分 ACPI。

Objective fact / 目标事实：Gemma31 training-candidate reduces ACPI acceptance to `0.083/0.083`; Qwen35-27B Chinese training-candidate drops to `0.083`, but English training-candidate remains `0.833`. / 更强训练样本清洗目标能降低接受率，但效果依赖模型和提示语言。

Scientific update / 科学更新：E39 makes the claim much less discount-specific. It is still controlled evidence, not natural prevalence. / E39 让主张不再像折扣词专属；但它仍是受控证据，不是自然发生率。

## 20. E40/E41 Hidden-State Generalization / E40/E41 隐藏层泛化

E40 report / E40 报告：`reports/E40_surface_semantic_span_patch_summary_20260428.md`. E41 report / E41 报告：`reports/E41_surface_semantic_module_patch_summary_20260428.md`.

E40 residual patch / E40 residual patch：Qwen3.5-9B has clean support/error residual signals on 11/12 E39 pairs; Qwen3-14B-Base has clean signals on 10/12 pairs. / Qwen3.5-9B 在 12 对中 11 对有干净 support/error residual 信号；Qwen14 在 12 对中 10 对有干净信号。

Strong examples / 强例子：Qwen3.5-9B Chinese strict interval L8 `+3.062/-4.187`; Qwen14 each-vs-total L12 `+2.500/-3.750`. / 强例子包括 Qwen3.5-9B 中文严格区间 L8 和 Qwen14 每人/总量 L12。

Boundary examples / 边界例子：round-vs-truncate is weak or near-zero despite high verifier acceptance; zh 亿/万 is weak for Qwen14 but clean for Qwen3.5-9B. / round-vs-truncate 尽管高接受但 patch 弱；亿/万对 Qwen14 弱但对 Qwen3.5-9B 干净。

E41 module patch / E41 模块 patch：MLP is the best module in selected Qwen3.5-9B pairs, but module effects are much smaller than residual effects; Qwen14's strongest selected module is Chinese strict interval MLP L20 `+0.500/-0.250`. / MLP 参与，但单模块效应远小于 residual 效应；Qwen14 最强选中模块是中文严格区间 MLP L20。

Mechanism boundary / 机制边界：the safe claim is distributed middle residual-state process evidence with MLP participation, not a single-head or single-MLP circuit. / 安全表述是“分布式中层 residual-state 过程证据，并有 MLP 参与”，不能说成单头或单 MLP circuit。

## 21. E42 Objective Matrix / E42 目标矩阵

Stage report / 阶段报告: `reports/E42_e39_objective_matrix_summary_20260428.md`. Gap/plan report / 缺口规划报告: `reports/E42_next_stage_gap_analysis_and_experiment_plan_20260428.md`.

Design / 设计：E42 keeps E39 trace content fixed and changes verifier objective: absolute process-only, training-candidate, answer-masked/wrong-answer variants from E39, order-balanced contrastive sibling verification, locate-only, and locate-then-judge. / E42 固定 E39 trace 内容，只改变 verifier 目标：绝对式只审过程、训练候选、答案遮蔽/错误答案变体、顺序平衡 sibling 对比、仅定位、先定位再判断。

Contrastive result / 对比式结果：Qwen35-27B reaches `1.000` overall contrastive accuracy; Qwen35-9B `0.979`; Qwen14 `0.958`; Gemma31 `0.875`. / 对比式在同一批 row 上显著强于绝对式 Yes/No，Qwen35-27B 达到满分。

Locate-then-judge result / 先定位再判断结果：Qwen-family models often reject invalid rows once asked to locate first; Qwen35-9B invalid reject is `1.000/1.000` EN/ZH and Qwen35-27B is also `1.000/1.000`, but span-hit rates vary. Gemma31 localization is unstable. / Qwen 系先定位再判断后常能拒绝 invalid 行；Qwen35-9B 与 Qwen35-27B 无效行拒绝率中英均为 1.000，但 span 命中率不同。Gemma31 定位输出不稳定。

Calibrated margin fact / 连续边际事实：invalid process phrases lower the Yes-minus-No margin relative to valid siblings for all four models, yet ACPI rows can still be accepted. Qwen35-27B English has mean invalid-valid margin delta `-2.458` but accepts `12/12` negative-delta ACPI rows. / 无效过程短语会压低 Yes-No margin，但最终二值判断仍可接受。Qwen35-27B 英文平均 delta 为 `-2.458`，仍接受 `12/12` 个负 delta ACPI 行。

Scientific update / 科学更新：E42 directly supports the objective/threshold part of the causal chain. The verifier is not blind; pointwise Yes/No underuses or re-entangles evidence that contrastive and locate-then-judge objectives can expose. / E42 直接支持因果链中的目标/阈值环节。verifier 不是看不见，而是点式 Yes/No 没有充分使用、或重新纠缠了 contrastive 与 locate-then-judge 能暴露的证据。

Validation / 验证：E42 integrity audit passed: `logs/audit_e42_objective_matrix_20260428.json`. Project check passed: `logs/check_project_e42_objective_matrix_20260428.json`. / E42 完整性审计和项目检查均通过。

## 22. E43 Next-Stage Plan / E43 下一阶段计划

Plan report / 计划报告: `reports/E43_next_stage_mechanism_and_generalization_plan_20260428.md`.

Next priority / 下一优先级：E43 paraphrase-transfer hidden patch, E44 MLP direction steering with leave-one-family-out controls, E45 residual/MLP/output-head mediation, E46 natural harvesting over E39 families, and E47 hard-task final-correct conditioning. / 下一优先级是 E43 跨改写 hidden patch、E44 leave-one-family-out MLP 方向 steering、E45 residual/MLP/output-head 中介、E46 E39 家族自然挖掘、E47 难题 final-correct 条件化。

Reason / 原因：after E42, objective causality is much stronger. The remaining top-tier gaps are natural prevalence and deeper mechanism: semantic transfer, necessity/sufficiency, and robust controls against lexical-token artifacts. / E42 后目标因果性更强；剩余顶会缺口是自然发生率和更深机制：语义迁移、必要/充分性，以及排除词面 token artifact 的控制。

## 23. Evaluation Setting Audit And Official-Template Correction / 评估设置审计与官方模板修正

Appendix / 附录：`reports/APPENDIX_EVAL_SETTING_AUDIT_20260428.md`.

Goal / 目标：before running E43-E47, audit whether paper-facing evaluation settings follow official/model-native guidance and whether raw historical settings need caveats. / 在继续 E43-E47 前，审计论文主证据相关评估设置是否符合官方/模型原生用法，以及历史 raw 设置是否需要边界说明。

Main correction 1 / 主要修正 1：for chat/post-trained Qwen35 and Gemma models, historical raw prompts remain valid only as a named raw-prompt stress-test family. Official-template parity now uses `apply_chat_template(..., add_generation_prompt=True, enable_thinking=False)` and tokenizes rendered templates with `add_special_tokens=False`. / 对 Qwen35 和 Gemma 这类 chat/post-trained 模型，历史 raw prompt 只能作为已命名的 raw-prompt 压力测试；官方模板 parity 已使用 `apply_chat_template(..., add_generation_prompt=True, enable_thinking=False)`，且渲染后 `add_special_tokens=False`。

Main correction 2 / 主要修正 2：`scripts/run_real_acpi_span_patch_smoke.py` now also respects the no-duplicate-special-token rule for official chat-template hidden patching. The corrected Qwen35-9B official-template rerun records `used_chat_template=True`, `add_special_tokens=False`, `rows=120`. / `run_real_acpi_span_patch_smoke.py` 现在对官方 chat-template hidden patch 也遵守不重复 special token 规则。修正后 Qwen35-9B 官方模板复跑记录为 `used_chat_template=True`、`add_special_tokens=False`、`rows=120`。

Main correction 3 / 主要修正 3：Qwen35-9B has 32 text layers, so stale layer IDs `32/36/39` were removed from `configs/e39_surface_semantic_pairs_qwen35_9b.yaml` and `configs/e31_non_discount_span_patch_pairs_qwen35_9b.yaml`; the audited sweep uses `[0, 4, 8, 12, 14, 16, 20, 24, 28, 31]`. / Qwen35-9B 有 32 个 text layer，旧配置中的 `32/36/39` 已从两个 Qwen35 配置中移除；审计后的层扫描使用 `[0, 4, 8, 12, 14, 16, 20, 24, 28, 31]`。

Official-template parity result / 官方模板 parity 结果：Qwen35-9B absolute process ACPI accept drops to `0.417` while contrastive reaches `1.000`; Qwen35-27B drops to `0.500` with contrastive `1.000`; Gemma4-31B-it is `0.500` with contrastive `1.000`; Qwen3-14B-Base remains raw/base with ACPI accept `0.250` and contrastive `0.958`. / 官方模板会降低 Qwen35 的绝对式误接受，但不会消除；对比式仍几乎完全暴露错误。

Official-template hidden patch result / 官方模板 hidden patch 结果：Qwen35-9B E39 support/error residual patch is clean on `12/12` pairs after correction; strongest remains Chinese strict interval L8 `valid->bad +5.625`, `bad->valid -6.312`. / 修正后 Qwen35-9B 在 E39 12/12 对都有干净 support/error residual patch 信号；最强仍是中文严格区间 L8。

Audit validation / 审计验证：machine audit passed in `logs/audit_eval_settings_appendix_20260428.json`; project check passed in `logs/check_project_eval_audit_20260428.json`; compile checks passed for the new/modified audit and runner scripts. / 机器审计、项目检查和脚本编译均通过。

Scientific boundary / 科学边界：paper tables should separate raw-audit prompt numbers from official-template robustness numbers. The main claim survives the audit, but quantitative claims about over-acceptance should be conservative and setting-specific. / 论文表格应区分 raw-audit prompt 与官方模板稳健性数字。主张没有被审计推翻，但误接受率的数字表述必须更保守、按设置报告。

## 24. E43-E47 Pilot Experiments After Audit / 审计后的 E43-E47 pilot 实验

Stage report / 阶段报告：`reports/E43_E47_next_experiments_summary_20260428.md`.

E43 paraphrase transfer / E43 跨改写迁移：six families × two paraphrases were built in `data/processed/e43_paraphrase_transfer_20260428.jsonl`. Qwen35-9B official-chat and Qwen3-14B raw both show clean cross-paraphrase residual transfer on all same-family targets (`12/12` each), but mismatched-family donors are also strong (`12/12` for Qwen35-9B and `11/12` for Qwen14). / E43 构造了 6 类 × 2 改写；同家族跨改写迁移很强，但错配家族也强。

E43 scientific update / E43 科学更新：hidden residual states carry a reusable valid-vs-invalid process signal, but the current transfer experiment does not yet prove family-specific semantic features. / hidden residual state 中存在可复用的有效/无效过程信号，但当前迁移还不能证明家族特异语义 feature。

E44 MLP direction steering / E44 MLP 方向 steering：leave-one-family-out MLP steering is weak. Qwen35-9B process direction alpha=1 has mean desired effect `0.130`, slightly above random `0.076` and opposite `0.065`, with one flip. Qwen14 process direction is essentially tied with random and has zero flips. / 留一族 MLP steering 效应弱；Qwen35 略强于控制但很小，Qwen14 与随机基本持平。

E44 scientific update / E44 科学更新：MLP participation remains real but naive single-direction MLP steering is not a convincing causal knob. The safe mechanism claim is still distributed middle residual-state evidence with partial MLP participation. / MLP 参与存在，但朴素单方向 MLP steering 不是有说服力的因果旋钮；安全说法仍是中层 residual 分布式证据和部分 MLP 参与。

E46 natural harvesting pilot / E46 自然挖掘 pilot：neutral prompts over the six E43 families produced no process-invalid final-correct rows under conservative pilot audit. Qwen35-27B had `8/12` final-correct and `0` ACPI; Gemma4-31B-it had `5/6` final-correct and `0` ACPI. / 中性提示小样本未自然产生 ACPI；Qwen35-27B 和 Gemma31 的答案正确样本在 pilot 审计下过程有效。

E47 AIME hard conditioning / E47 AIME 难题条件化：Qwen35-27B official-chat thinking run on three AIME-2025 tasks with two samples each produced `0/6` final-correct traces, so no ACPI estimate is possible yet. / AIME pilot 没有答案正确 trace，因此还不能估计难题 ACPI。

Reliability / 可靠性：`logs/audit_e43_e47_next_experiments_20260428.json` passed. E46/E47 prompts do not include known error spans or gold answers; gold answers are used only after generation for filtering. / E43-E47 审计通过；E46/E47 不把错误 span 或 gold answer 放进 prompt。

Publication boundary / 发表边界：these experiments strengthen the non-token-artifact story but also force a more conservative mechanism claim. Natural prevalence and hard-task final-correct conditioning remain the two largest missing pieces for a top-tier paper. / 这些实验加强了“不是固定 token artifact”的说法，但也要求机制主张更保守。自然发生率和难题答案正确条件化仍是顶会论文最大缺口。
