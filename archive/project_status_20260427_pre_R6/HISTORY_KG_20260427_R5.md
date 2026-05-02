# P02 History Knowledge Graph R5 / P02 历史知识图谱 R5

Date / 日期: 2026-04-27 CST
Project / 项目: `/home/Awei/P02_multilingual_process_lens`

This is the active project memory after the S4 causal-chain, mechanism, hard-task, and transfer-model round. / 本文件是 S4 因果链、机制、困难任务和跨模型迁移轮次后的当前项目记忆。

## 0. Active Claim / 当前主张

Paper-level claim candidate / 论文级候选主张：

> Multilingual and surface-semantic traps can create answer-correct but process-invalid traces (ACPI; 答案正确但过程无效), producing a trace-selection risk (轨迹选择风险). The risk is not merely wrong answers or broken formatting; it can arise from a mismatch among surface lexicalization (表层词汇化), process semantics (过程语义), and the verifier objective/threshold (验证器目标与阈值). Real traces contain process/error-span signals (过程/错误 span 信号) that sibling comparison (兄弟轨迹对比) or residual/module span patching (残差流/模块 span patch) can expose in robust pairs, while absolute Yes/No verifiers (绝对式是/否验证器) often over-accept. The mitigation is useful but not universal, especially for hard same-route lexical cases and for evaluators with position bias.
>
> 中文：多语言与表层语义陷阱会产生 ACPI（答案正确但过程无效）轨迹选择风险。这一风险不只是答案错或格式坏，而可能来自表层词汇化、过程语义、验证器目标/阈值之间的错配。真实轨迹中存在过程/错误 span 信号，在稳健 pair 中可被 sibling comparison 或 residual/module span patch 暴露，但 absolute Yes/No verifier 往往过度接受。该缓解并非万能，特别是在困难同 route 词汇例和有位置偏差的评估器上。

Current stage / 当前阶段：`S4 causal-chain and mechanism stress test`（S4：因果链与机制压力测试）。

## 1. Mainlines / 五条主线

| Mainline / 主线 | Question / 问题 | R5 status / R5 当前状态 |
|---|---|---|
| A. Natural ACPI existence / 真实 ACPI 存在性 | Do real generated traces contain final-correct but process-invalid reasoning? / 真实生成轨迹是否有答案正确但过程错误？ | Strong selected-pair evidence. E05 found strict/paper-grade ACPI; E18 added same-route Qwen14 `180092`; E27 Gemma4 generation added surface semantic drift but not ACPI. / 已有强选择集证据；E27 Gemma4 生成新增表层语义漂移但不是 ACPI。 |
| B. Verifier reliability / verifier 可靠性 | Do absolute verifiers filter these risks? / 绝对 verifier 能否筛掉这些风险？ | Strong failure evidence. E24 ledger shows 8/8 manual ACPI pairs were over-accepted by absolute verifiers; E27 Qwen3.5-27B and Gemma4 also over-accept selected ACPI rows. / 失败证据强：E24 为 8/8，E27 跨模型复现过度接受。 |
| C. Multilingual surface-semantic mechanism / 多语言表层语义机制 | Are errors tied to surface lexicalization rather than random math mistakes? / 错误是否来自表层语义词汇化而非随机数学错误？ | Stronger. `打八折` being lexicalized as `80% discount` while computing pay80 now appears in same-route Qwen14 ACPI `180092`; Gemma4 treats `打七五折` as `75% off` and outputs `$20` final-wrong. / 更强：同 route ACPI 与 Gemma4 final-wrong 语义漂移共同支持表层词汇化风险。 |
| D. Hidden process/error signal / 隐藏过程与错误信号 | Is process-validity information represented outside the final answer token? / 非最终答案位置是否含过程有效性信息？ | Positive but bounded. E24: 6/8 ACPI pairs have robust hidden span signal and 2/8 have MLP clean-direction signal; E25 logit lens suggests middle-layer process signal can be lost or re-entangled at output. / 正向但有边界：hidden span 较稳，MLP/输出头证据仍是诊断级。 |
| E. Sibling/triangulation mitigation / 兄弟对比与三角测量缓解 | Can pairwise comparison or conservative consistency reduce risk? / 对比与保守一致性能否降低风险？ | Useful but not universal. E24: 7/8 ACPI pairs show contrastive signal; E27 Qwen3.5-27B contrastive accuracy is 0.875, while Gemma4 is 0.542 with A-position bias. / 有用但不万能，需顺序平衡与保守拒绝。 |

## 2. Evidence Ledger / 证据台账

| ID / 编号 | Artifact / 产物 | Finding / 发现 | Interpretation / 解释 |
|---|---|---|---|
| Archive / 归档 | `archive/project_status_20260427_pre_R4/`, `archive/project_status_20260427_pre_R5/` | Old handoff/history/status snapshots were archived. / 旧交接、历史和状态快照已归档。 | Active docs now point to R5. / 当前文档指向 R5。 |
| E18 | `reports/E18_S3_TARGETED_SIBLING_EXPANSION_AND_AUDIT_20260427.md` | 360 targeted rows; new same-route Qwen14 ACPI `180092`; clean Qwen3.5 siblings `181000/181001`. / 360 行定向生成；新增同 route ACPI 和干净 sibling。 | Strengthens natural ACPI and sibling controls. / 强化真实 ACPI 与 sibling 控制。 |
| E19 | `reports/E19_real_acpi_module_patch_summary.md` | MLP-output patch reproduces several robust residual effects. / MLP 输出 patch 复现部分稳健残差信号。 | Mechanism upgrade, not full circuit proof. / 机制升级，但不是完整 circuit 证明。 |
| E20/E21 | `reports/E20_e18_same_route_span_patch_summary.md`, `reports/E21_e18_contrastive_verifier_summary.md` | Qwen14 `打八折` same-route ACPI is hard: span patch weak, contrastive can fail. / Qwen14 同 route 词汇 ACPI 很难。 | Required boundary condition. / 必须作为边界写入论文。 |
| E22/E23 | `reports/E22_e18_clean_sibling_span_patch_summary.md`, `reports/E23_e18_clean_sibling_contrastive_summary.md` | Qwen3.5 `234` remains robust after clean sibling replacement. / Qwen3.5 `234` 在干净 sibling 后仍稳健。 | Strong positive chain. / 强正向链条。 |
| E24 | `reports/E24_s4_causal_chain_ledger.md`, `results/E24_s4_causal_chain_ledger/s4_causal_chain_ledger.json` | 9 pairs, 8 manual ACPI; 8/8 absolute-overaccepted, 7/8 contrastive signal, 6/8 hidden-span signal, 2/8 MLP signal. / 9 对中 8 对 ACPI；绝对过度接受 8/8，对比 7/8，hidden span 6/8，MLP 2/8。 | Best current causal-chain table, but selected-pair only. / 当前最佳因果链表，但仅代表选择集。 |
| E25 | `reports/E25_layerwise_verifier_lens_summary.md` | Diagnostic layerwise lens shows middle-to-final drops and `output/head re-entanglement candidate` tags. / 分层诊断 lens 显示中层到输出层信号下降与输出头再纠缠候选。 | Supports H1/H2 hypotheses, but not a tuned lens or circuit proof. / 支持 H1/H2，但不是 tuned lens 或 circuit 证明。 |
| E26 | `reports/E26_aime_hard_smoke_audit_summary.md` | 48 AIME-style rows, strict final-correct = 0, ACPI candidates = 0. / 48 行 AIME 难题，严格 final-correct 为 0，ACPI 候选为 0。 | Boundary: do not extrapolate simple-task ACPI rates to hard math. / 边界：不能把简单任务 ACPI 频率外推到难题。 |
| E27 absolute / E27 绝对式 | `reports/E27_transfer_absolute_verifier_summary.md` | Qwen3.5-27B and Gemma4 over-accept selected ACPI rows; Gemma4 yes-rate is 1.0. / Qwen3.5-27B 与 Gemma4 对选择 ACPI 过度接受；Gemma4 yes-rate 为 1.0。 | Transfer evidence for absolute objective/threshold risk. / 绝对式目标/阈值风险有跨模型证据。 |
| E27 contrastive / E27 对比式 | `reports/E27_transfer_contrastive_verifier_summary.md` | Qwen3.5-27B contrastive acc 0.875; Gemma4 acc 0.542 with position/order bias. / Qwen3.5-27B 对比准确率 0.875；Gemma4 0.542 且有位置/顺序偏差。 | Contrastive helps capable models but requires order-bias controls. / 对比对强模型有帮助，但必须控制顺序偏差。 |
| E27 generation / E27 生成 | `reports/E27_transfer_trace_generation_audit.md` | Qwen3.5-27B loader works but generated meta-planning, not usable traces; Gemma4 generated clean traces plus one `打七五折 -> 75% off` final-wrong semantic drift. / Qwen3.5-27B 可加载但生成元规划；Gemma4 有一条语义漂移 final-wrong。 | Transfer generation needs stricter prompts; semantic drift still supports surface-trap family. / 跨模型生成需更强提示约束；语义漂移支持表层陷阱族。 |
| S5 integrated / S5 综合 | `reports/S5_INTEGRATED_SCIENTIFIC_ANALYSIS_AND_ROADMAP_20260427.md`, `docs/SCIENTIFIC_COMMUNICATION_MEMO_20260427.md` | All current results were rewritten as human-readable scientific facts, with novelty, boundaries, and next-experiment goals. / 已把当前结果改写成人话科学事实，并列出创新点、边界和后续实验目的。 | Use this as the main communication artifact. / 后续沟通优先使用该文件。 |
| Literature R5 / 文献 R5 | `docs/LITERATURE_S5_ADDITIONAL_COLLISION_REVIEW_20260427.md` | New search round confirms high collision for generic CoT faithfulness, PRM/verifier, multilingual representation, and circuits claims. / 新检索确认泛化 CoT faithfulness、PRM/verifier、多语言表征和 circuit 说法撞车风险高。 | Keep P02 novelty narrow: multilingual lexical ACPI + verifier mismatch + causal hidden-span evidence + boundaries. / 创新点要收窄到 P02 特有链条。 |

## 3. Mechanistic Hypotheses / 机制假设

1. Middle-layer process confounding / 中层过程混杂：middle layers may jointly encode surface lexical cues and process semantics; patching selected support/error spans moves verifier margins, but signals can be ambiguous in hard lexical cases. / 中层可能混合表层词汇线索与过程语义；patch 某些 support/error span 会移动 verifier margin，但困难词汇例中信号可能混杂。
2. Output-head re-entanglement / 输出头再纠缠：diagnostic lens suggests some middle-layer process signals are lost or reweighted by the final output head, plausibly by final-answer correctness, fluency, language prior, or Yes-bias. / 诊断 lens 显示部分中层过程信号在最终输出头被丢失或重权，可能与答案正确性、流畅度、语言先验或 Yes-bias 再纠缠。
3. Objective-threshold bottleneck / 目标-阈值瓶颈：absolute Yes/No prompts can map weak or ambiguous process evidence to acceptance; contrastive sibling prompts expose relative error evidence in many but not all pairs. / 绝对式提示会把弱或模糊过程证据映射为接受；对比 sibling 提示能在多数但非全部 pair 中暴露相对错误证据。

Current novelty-safe wording / 当前低撞车表述：P02 is not claiming a new general process reward model (PRM; 过程奖励模型), a new process-error benchmark (过程错误基准), a general multilingual concept discovery, or a complete circuit proof. It claims a selected, realistic multilingual surface-lexical ACPI failure family and tests the causal chain from manual process labels to verifier behavior and hidden-span interventions. / P02 不声称新的通用 PRM、过程错误基准、多语言概念发现或完整 circuit；它声称一个选择后的真实多语言表层词汇 ACPI 失败族，并检验从人工过程标签到 verifier 行为与 hidden-span 干预的因果链。

## 4. Hard-Task Boundary / 困难任务边界

E26 shows that current local 8B/9B/14B-class models rarely produce final-correct AIME-style traces under the tested prompts; therefore ACPI cannot be measured there without first obtaining final-correct hard traces. / E26 显示当前本地 8B/9B/14B 级模型在测试提示下几乎不产生 final-correct AIME 风格轨迹；因此必须先获得 final-correct 难题轨迹，才能测 ACPI。

Recommended hard-task path / 推荐难题路径：

1. Use stronger or larger generators and verifier-guided sampling to condition on final-correct traces. / 使用更强或更大生成器与 verifier-guided sampling，先条件化出 final-correct 轨迹。
2. Treat `final-wrong` and `no-final-marker` as separate route/format failure modes, not ACPI. / 将答案错和无 final marker 作为单独 route/格式失败，而不是 ACPI。
3. Only after final-correct hard traces exist, run manual process audit, contrastive sibling comparison, and hidden-span patching. / 只有在有 final-correct 难题轨迹后，才做人审、对比 sibling 与 hidden-span patch。

## 5. Model Transfer / 跨模型迁移

Downloaded local models / 已下载本地模型：

- `qwen35_27b`: `/home/Awei/LLM/Model/base/qwen35_27b`; use `--device auto` and `MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'`. / Qwen3.5-27B 需多卡自动切分。
- `gemma4_e4b_it`: `/home/Awei/LLM/Model/base/gemma4_e4b_it`; single-GPU bf16 loading works. / Gemma4 E4B-it 可单卡 bf16 加载。

Transfer takeaways / 迁移结论：

1. Absolute over-acceptance transfers to both models on selected ACPI rows. / 绝对式过度接受在两个迁移模型上复现。
2. Qwen3.5-27B can use contrastive evidence better than absolute Yes/No (0.875 accuracy), supporting the objective/threshold mismatch claim. / Qwen3.5-27B 对比式明显强于绝对式，支持目标/阈值错配。
3. Gemma4 shows strong position bias in contrastive mode, so sibling comparison must be order-balanced and cannot be treated as a universal oracle. / Gemma4 对比式有强位置偏差，说明 sibling comparison 必须顺序平衡，不能当万能 oracle。

## 6. Reliability And Leakage Audit / 可靠性与泄露审计

- No training or fine-tuning was performed. / 未进行训练或微调。
- Manual labels were created after generation and used only for auditing/evaluation. / 人工标签在生成后创建，仅用于审计/评估。
- AIME tasks are public benchmark-style prompts and were used as a stress test, not as training data. / AIME 题是公开 benchmark 风格提示，仅作压力测试，不作训练数据。
- Contrastive experiments include both `bad_A` and `bad_B` orders. / 对比实验包含 `bad_A` 与 `bad_B` 两种顺序。
- Selected-pair rates are not prevalence estimates. / 选择集比例不是总体发生率。
- E25 is a diagnostic logit lens, not a calibrated tuned lens or circuit proof. / E25 是诊断 logit lens，不是校准 tuned lens 或 circuit 证明。
- Validation on 2026-04-27: `py_compile` passed for modified scripts; `scripts/check_project.py` passed; GPUs were idle; no tmux sessions remained. / 2026-04-27 验证：修改脚本通过 `py_compile`；`scripts/check_project.py` 通过；GPU 空闲；无遗留 tmux 会话。

## 7. Next Actions / 下一步行动

1. Pair bank expansion / 扩展 pair bank：expand clean same-route ACPI/valid sibling pairs to at least 8 robust pairs across discount, ratio, derivative, and paraphrase families. / 覆盖折扣、比例、导数和改写族，至少 8 对稳健干净 sibling。
2. Mechanism deepening / 深化机制：run head-level, MLP-block, and optional SAE/transcoder probes only on robust E24/E22 targets; do not probe weak pairs first. / 只在稳健目标上做头级、MLP block 与可选 SAE/transcoder probe。
3. Hard-task conditioning / 难题条件化：use larger generators or verifier-guided search to obtain final-correct AIME24/25 traces before ACPI/patch probes. / 用更大模型或 verifier-guided search 先获得 final-correct AIME24/25 轨迹。
4. Transfer generation fix / 修复迁移生成：tighten Qwen3.5-27B prompt or chat template to avoid meta-planning; resample Gemma4 `打七五折/打八折` variants to estimate semantic-drift repeatability. / 收紧 Qwen3.5-27B 提示避免元规划，重采 Gemma4 折扣变体估计语义漂移复现性。
5. Paper framing / 论文框架：write as one causal chain, not five independent smokes; keep negative Qwen14, Gemma4 position bias, and AIME zero-ACPI boundary in the main paper. / 写成同一因果链，不写成五个互不相关 smoke；主文保留负例与边界。
