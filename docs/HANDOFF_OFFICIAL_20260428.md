# Official Handoff / 官方交接（2026-04-28）

> 2026-04-30 stage synthesis / 阶段性整理入口：`docs/HANDOFF_HISTORY_STAGE_SYNTHESIS_20260430.md`。Use that file for the current human-readable claim, glossary, experiment summary, literature positioning, and next-experiment plan; keep this file as the original detailed audit handoff. / 当前主张、术语人话表、实验总结、文献定位和后续实验计划请先看该文件；本文保留为原始详细交接流水。

## Working Directory / 工作目录

`/home/Awei/P02_multilingual_process_lens`

## Environment / 环境

```bash
cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
```

中文：所有官方 HF runner 都应使用上述环境；不要原地升级当前 conda 环境。

## Backend Decision / 后端决定

English: Use HuggingFace for Qwen3.5/Gemma4 P0 runs and all mechanism experiments. Use vLLM only for compatible generation-only CausalLM controls.

中文：Qwen3.5/Gemma4 P0 结果与所有机制实验使用 HuggingFace；vLLM 只用于架构兼容、只做生成的 CausalLM 控制实验。

Evidence / 证据：`reports/APPENDIX_BACKEND_COMPATIBILITY_AND_THROUGHPUT_20260428.md`。

## P0 Model Cluster / P0 模型簇

Current core P0 / 当前核心 P0：

- `qwen35_27b`
- `gemma4_31b_it`
- `gemma4_26b_a4b_it`

中文：只有这三个本地最新中等开源模型承载主结论。`qwen35_9b`、`qwen3_14b_base`、DeepSeek distill 与其他小模型现在是 P1 控制；`qwen25_math_7b_instruct` 是 P2 旧数学控制。

Model-tier report / 模型分层报告：`reports/P0_MODEL_CLUSTER_UPDATE_20260428.md`。

External candidates / 外部候选：`exaone45_33b_candidate`、`nemotron_cascade2_30b_a3b_candidate`、`xiaomi_mimo_v2_flash_candidate`、`mistral_small4_candidate`、`glm47_flash_candidate` are registry entries only and must not be used in official runs until downloaded and smoke-tested in an isolated environment. / 这些只是 registry 候选，下载并隔离 smoke test 前不能进入 official run。

## Active Audits / 当前审计脚本

- `scripts/audit_eval_settings_appendix.py` / 检查评估设置。
- `scripts/audit_e43_e47_next_experiments.py` / 检查 E43-E47。
- `scripts/audit_e48_e50_official_results.py` / 检查 E48-E50 与 backend appendix。
- `scripts/audit_active_official_workspace.py` / 检查主目录只保留官方材料。

## Historical Queue / 历史队列

Queue script / 队列脚本：`scripts/launch_official_tmux_queue_20260428.sh`。

Historical jobs / 历史任务：

1. E48 `qwen35_9b` HF natural prevalence. / Qwen35-9B 自然发生率。
2. E48 `gemma4_31b_it` HF natural prevalence. / Gemma4-31B 自然发生率。
3. E49 `qwen35_27b` HF answer-anchor diagnostic. / Qwen35-27B answer-anchor 诊断，不作自然发生率。
4. E49 `gemma4_26b_a4b_it` HF no-gold hard-task pilot. / Gemma4-26B-A4B 无 gold 困难题 pilot。
5. E49 `gemma4_26b_a4b_it` HF answer-anchor diagnostic. / Gemma4-26B-A4B answer-anchor 诊断。
6. E50 `qwen3_14b_base` HF residual probe/steering control. / Qwen3-14B base 残差 probe/steering 控制。
7. E48 `qwen3_14b_base` vLLM generation-only control. / Qwen3-14B base vLLM 生成控制。
8. E49 `qwen25_math_7b_instruct` vLLM hard-task generation-only control, now not adopted for mainline. / Qwen2.5-Math-7B vLLM 困难题生成控制，现在不纳入主线。

## Monitoring / 监控

```bash
tmux ls
tmux attach -t official_queue_20260428
tail -f logs/official_queue_20260428.log
nvidia-smi dmon -s pucm
```

中文：若 GPU util 偏低但日志持续更新，通常不是卡死；若日志长时间不动且无新输出，再检查进程。

## Post-Queue Audit / 队列后审计

A second tmux session waits for the GPU queue to finish and then runs `scripts/recompute_e48_process_audit.py`, `py_compile`, `audit_e48_e50_official_results.py`, and `audit_active_official_workspace.py`.

中文：另一个 tmux 会等待 GPU 队列结束，然后自动运行 E48 过程标签重算、语法检查、E48-E50 审计和主目录官方材料审计。

```bash
tmux attach -t official_post_audit_20260428
tail -f logs/official_post_queue_audit_20260428.log
```

## Queue Completion Notes / 队列完成备注

- Main synthesis report: `reports/E48_E50_OFFICIAL_QUEUE_SYNTHESIS_20260428.md`. / 主要综合报告见该文件。
- If continuing hard-task work, do not rely only on strict `Final answer:` extraction; run a separate benchmark-style parser that accepts `\boxed{}` and then separately require trace-selection final-line formatting where needed. / 继续困难题时，不要只依赖 strict `Final answer:`；应同时做允许 `\boxed{}` 的 benchmark parser，并把 trace-selection final-line 作为另一项格式要求。
- Current GPUs are idle after the queue. / 队列结束后 GPU 当前空闲。
- All active audits passed after post-hoc parser/regex fixes. / parser/regex 修正后所有 active audit 已通过。

## Qwen2.5-Math Hard-Task Not Adopted / Qwen2.5-Math 困难题不采纳

Use `reports/QWEN25_MATH_HARD_TASK_NOT_ADOPTED_20260428.md` before interpreting any old E49/E51/E52 hard-task material.

中文：解释任何旧 E49/E51/E52 困难题材料前，先看 `reports/QWEN25_MATH_HARD_TASK_NOT_ADOPTED_20260428.md`。

- `qwen25_math_7b_instruct` is now P2 legacy and must not enter future mainline synthesis. / `qwen25_math_7b_instruct` 现在是 P2 旧控制，不能进入后续主线综合。
- E49/E51/E52 Qwen2.5-Math hard-task outputs were archived under `archive/qwen25_math_hard_task_not_adopted_20260428/`. / E49/E51/E52 Qwen2.5-Math 困难题输出已归档到该目录。
- Do not use the E52 boxed-correct rows as seed cases for the next mainline causal experiment. / 不再把 E52 boxed-correct 行作为下一步主线因果实验种子。
- Re-run hard-task and causal-chain experiments on current P0 models or newly admitted P0 candidates. / 困难题与因果链实验应在当前 P0 或新进入 P0 的候选模型上重跑。

## P0 Candidate Download / P0 候选下载

Download script / 下载脚本：`scripts/download_p0_candidates_20260428.sh`。

Priority candidates / 优先候选：Nemotron Cascade 2 30B-A3B, GLM-4.7-Flash, and EXAONE 4.5 33B. / 优先候选：Nemotron Cascade 2 30B-A3B、GLM-4.7-Flash、EXAONE 4.5 33B。
EXAONE 4.5 33B is user-approved for the external P0 candidate cluster, but keep it candidate-only until download, license check, and isolated backend smoke test pass. / EXAONE 4.5 33B 已获用户确认进入外部 P0 候选簇；但在下载、许可检查与隔离后端 smoke test 通过前，只能作为候选，不进入官方证据。

The script tries `https://hf-mirror.com` first and falls back to the original Hugging Face endpoint if the mirror fails. The checked-in script now has three resumable attempts per source for future reruns. / 脚本会优先使用 `https://hf-mirror.com`，失败后再回退到 Hugging Face 原始源。当前脚本已为未来重跑加入每个源三次断点续传尝试。

Note / 备注：the first Nemotron download attempt stalled after the mirror failed; it was restarted at 2026-04-28 14:59 CST after verifying no size change and `CLOSE_WAIT` sockets. The resumed download continues in `p0_candidate_download_20260428`. / 第一次 Nemotron 下载在镜像失败后曾停滞；已在 2026-04-28 14:59 CST 核实文件大小不变和 `CLOSE_WAIT` socket 后重启。续传仍在 `p0_candidate_download_20260428` 中运行。

## P0 Core Completion / P0 核心补齐

Synthesis report / 综合报告：`reports/P0_CORE_COMPLETION_SYNTHESIS_20260428.md`。

- `p0_completion_queue_20260428` finished all planned steps with `rc=0`. / `p0_completion_queue_20260428` 的所有计划任务均以 `rc=0` 完成。
- E42 P0 core result: all three P0 models have absolute invalid accept rate 0.50, valid accept rate 1.00, and contrastive accuracy 1.00. / E42 P0 核心结果：三个 P0 模型 absolute 接受 invalid 均为 0.50，接受 valid 均为 1.00，contrastive accuracy 均为 1.00。
- E50 P0 core result: all three P0 models reach best residual leave-one-task-out accuracy 0.9583, with random controls near chance. / E50 P0 核心结果：三个 P0 模型最佳 residual leave-one-task-out accuracy 均为 0.9583，随机控制接近机会水平。
- E44 result: MLP-only steering is weak and nonspecific; use it as a boundary on the mechanism claim. / E44 结果：MLP-only steering 弱且不够特异，应作为机制主张的边界条件。
- Current safe mechanism wording: distributed residual-state process evidence with causal steering effects; not a complete named circuit. / 当前安全机制表述：分布式 residual-state 过程证据，且有因果 steering 效应；不是完整命名 circuit。

## Verifier Objective and Mechanism Audit / Verifier 目标与机制审计

Report / 报告：`reports/VERIFIER_OBJECTIVE_AND_MECHANISM_AUDIT_20260428.md`。

- P0 absolute verifiers are self-verifiers, not official verifier checkpoints. / P0 absolute verifier 是 self-verifier，不是官方指定 verifier checkpoint。
- Core plain-language point: absolute Yes/No can accept because answer-correct/fluent trace pushes above threshold; sibling comparison cancels answer/context and forces the local process difference into the decision. / 核心说人话：absolute Yes/No 会被答案正确/文字流畅推过阈值；sibling comparison 抵消答案和上下文，迫使模型看局部过程差异。
- E50 should be described as residual-state process evidence with causal steering effects, not a complete circuit or single MLP knob. / E50 应描述为 residual-state 过程证据及因果 steering 效应，不是完整 circuit 或单个 MLP 开关。
- Next suggested experiments: E53 answer-anchor ablation, E54 parameterized no-leak generalization, E55 residual-to-logit mediation, E56 component decomposition, E57 P0 hard-task harvesting, E58 distillation-filter simulation, E59 cross-family verifier. / 下一步建议实验如上。

## Self-Verifier Rationale and E59a / Self-verifier 方法与 E59a

Report / 报告：`reports/SELF_VERIFIER_METHOD_RATIONALE_AND_E59_20260428.md`。
Result / 结果：`results/E59_cross_verifier_controlled/e59a_cross_verifier_controlled_matrix.json`。

- Self-verifier should be framed as an audited deployment pattern, not a trusted oracle. / self-verifier 应被表述为被审计的部署模式，不是可信 oracle。
- E59a uses existing E42 P0 outputs and shows all three P0 verifiers share absolute over-acceptance but recover under sibling comparison. / E59a 使用已有 E42 P0 输出，显示三个 P0 verifier 都有 absolute 过度接受且 sibling 恢复。
- E59a is not yet full mutual verification over model-generated traces; continue with E59b source-model × verifier-model matrix and E59c style-controlled rewriting. / E59a 还不是模型生成 trace 的完整互审；后续做 E59b source-model × verifier-model 矩阵和 E59c 风格受控改写。

## E59c Style-Controlled Mutual Verifier / E59c 风格受控互审

Report / 报告：`reports/E59C_STYLE_CONTROLLED_MUTUAL_VERIFIER_20260428.md`。
Summary / 摘要：`results/E59_cross_verifier_style/summary.json`。

- E59c rewrites controlled E42 traces with each P0 source model, re-audits process-label preservation, then scores source-blind source × verifier matrices. / E59c 让每个 P0 源模型改写 E42 受控 trace，重新审计过程标签保留，再做来源盲化 source × verifier 矩阵。
- Main result: self and cross absolute invalid accept means are both 0.500; self and cross sibling accuracies are 0.941 and 0.933. / 主结果：自审和互审 absolute invalid 接受均值都是 0.500；自审与互审 sibling 准确率分别为 0.941 和 0.933。
- Interpretation: current evidence favors objective/threshold mismatch over pure self-preference. / 解释：当前证据更支持 objective/threshold 错配，而不是纯自偏好。
- Note: initial queue audit import bug is archived under `archive/e59c_queue_first_attempt_import_bug_20260428/`; outputs were fixed and rerun. / 注意：初始队列 audit 导入错误已归档，输出已修复重跑。

## External Candidate Download Update / 外部候选下载更新

- `nemotron_cascade2_30b_a3b_candidate`, `glm47_flash_candidate`, and `exaone45_33b_candidate` are locally downloaded but still pending license/backend smoke tests. / Nemotron、GLM 与 EXAONE 均已本地下载，但仍待许可和后端 smoke test。
- Do not promote any external candidate into official P0 evidence before isolated loader smoke tests and license checks pass. / 在隔离 loader smoke test 和许可检查通过前，不要把任何外部候选提升为官方 P0 证据。


## E53-E58 Current Status / E53-E58 当前状态

Reports / 报告：

- `reports/E53_E57_EXECUTION_SYNTHESIS_20260428.md` / E53-E57 综合报告。
- `reports/E53_E57_LEAKAGE_LOGIC_AUDIT_20260428.md` / E53-E57 泄露与逻辑审计，PASS。
- `reports/E57_HARD_TASK_MANUAL_AUDIT_20260428.md` / E57 困难题人工过程审计。
- `reports/E58_DISTILLATION_FILTER_SIMULATION_20260428.md` / E58 筛选器模拟，PASS。

Key facts / 关键事实：

- E53: correct final answers anchor absolute verifiers toward Yes, but removed/masked conditions still have invalid acceptance; not purely answer-only. / E53：正确最终答案会把 absolute verifier 往 Yes 拉，但 removed/masked 仍有 invalid 接受；不是纯粹只看答案。
- E54: 18 non-leak task families reproduce absolute over-acceptance; sibling comparison remains 1.000 on P0. / E54：18 类无泄露任务族复现 absolute 过度接受；P0 sibling comparison 仍为 1.000。
- E55/E56: residual/token-mixer states carry process-validity evidence; residual steering moves Yes/No logits; no full named circuit yet. / E55/E56：residual/token-mixer state 携带过程有效性证据；residual steering 会移动 Yes/No logit；尚非完整命名 circuit。
- E57: P0 hard-task final-correct rows are available; strict ACPI is 11/119, but unrepaired ACPI is only 2/119. / E57：已采到 P0 困难题 final-correct 行；strict ACPI 为 11/119，但未修复 ACPI 只有 2/119。
- E58: outcome-only and absolute filters retain ACPI risk; sibling comparison suppresses accepted ACPI to 0 in E42/E54 P0 runs. / E58：只看答案和 absolute 筛选都会保留 ACPI 风险；sibling comparison 在 E42/E54 P0 运行中将 accepted ACPI 压到 0。

Current safe claim / 当前安全主张：

Controlled ACPI and verifier objective mismatch are robust on current P0. Natural simple-task ACPI remains unobserved in small no-leak samples, and hard-task unrepaired ACPI exists but is rare in the current P0 sample. / 当前 P0 上 controlled ACPI 与 verifier objective 错配是稳健的。简单任务自然 ACPI 在小型无泄露样本中仍未观察到；困难题未修复 ACPI 存在但当前 P0 样本中很少。

Useful commands / 常用命令：

```bash
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
python scripts/audit_e53_e57_official_results.py
python scripts/run_e58_distillation_filter_simulation.py
```

## E60 Objective Ladder / E60 过程检查目标梯度

Report / 报告：`reports/E60_OBJECTIVE_LADDER_20260429.md`。
Audit / 审计：`reports/E60_OBJECTIVE_LADDER_AUDIT_20260429.json`，PASS。
Results / 结果：`results/E60_objective_ladder/`。

- E60 completed on all current P0 core models with `rc=0`. / E60 已在所有当前 P0 核心模型上完成，`rc=0`。
- It compares `plain_yes_no`, `careful_yes_no`, `answer_blind_yes_no`, `locate_then_judge_yes_no`, `sibling_comparison`, and `careful_sibling_comparison`. / 它比较普通 Yes/No、仔细检查、answer-blind、先定位再判断、普通 sibling 和 careful sibling。
- Main result: P0 mean ACPI accept falls from 0.567 under plain Yes/No to 0.156 under careful Yes/No and 0.144 under locate-then-judge, but only sibling comparison reaches 0 accepted ACPI in E42/E54. / 主结果：P0 平均 ACPI 接受从普通 Yes/No 的 0.567 降到仔细检查的 0.156、先定位再判断的 0.144；但只有 sibling comparison 在 E42/E54 中达到 0 accepted ACPI。
- Interpretation: stronger process prompts help, but objective structure still matters; pairwise comparison remains the most reliable current text-only diagnostic. / 解释：更强过程 prompt 有帮助，但 objective 结构仍重要；成对比较仍是当前最可靠的 text-only 诊断。

Useful command / 常用命令：

```bash
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
python scripts/audit_e60_objective_ladder.py
```

## Stage Report and Automatic Roadmap / 阶段报告与自动路线图

Report / 报告：`reports/STAGE_REPORT_CLAIM_BOUNDARY_AND_NEXT_ROADMAP_20260429.md`。
Roadmap JSON / 路线图 JSON：`reports/NEXT_EXPERIMENT_ROADMAP_20260429.json`。

- The report clarifies that pointwise Yes/No is not leakage: no labels, spans, or corrections are inserted into the prompt. / 报告澄清 pointwise Yes/No 不是泄露：prompt 不插入标签、span 或修正。
- Sibling comparison is a stronger contrastive diagnostic, not an error-span leak. / sibling comparison 是更强的对比诊断，不是错误 span 泄露。
- Mechanism interventions are oracle-style diagnostics and must not be reported as blind verifier performance. / 机制干预是 oracle-style 诊断，不能报告成 blind verifier performance。
- The user authorized routine continuation without step-by-step approval. Proceed through E61-E70 unless blocked by license, destructive action, or major claim reversal. / 用户已授权常规任务无需逐步批准。除非遇到许可、破坏性操作或主张重大反转阻塞，继续推进 E61-E70。
- Immediate next: E61 language-route × error-taxonomy grid. / 立即下一步：E61 语言路径 × 错误类型网格。

## 2026-04-29 E61 Completed / E61 已完成

Report / 报告：`reports/E61_LANGUAGE_ERROR_GRID_20260429.md`。
Audit / 审计：`reports/E61_LANGUAGE_ERROR_GRID_AUDIT_20260429.json`，PASS。
Results / 结果：`results/E61_language_error_grid/`。
Stage report / 阶段报告：`reports/AUTONOMOUS_CONTINUATION_STAGE_REPORT_20260429.md`。
Roadmap / 路线图：`reports/NEXT_EXPERIMENT_ROADMAP_20260429.json`。

Key facts / 关键事实：

- E61 covers 6 language routes and 8 error families, with valid-correct / invalid-correct paired traces. / E61 覆盖 6 条语言路径和 8 类错误，每个 cell 有 valid-correct / invalid-correct 成对 trace。
- It ran on `qwen35_27b`, `gemma4_31b_it`, and `gemma4_26b_a4b_it` using official chat templates and deterministic option-logprob scoring. / 实验在三个核心 P0 模型上运行，使用官方 chat template 与确定性 option-logprob 打分。
- Leakage checks passed: no labels, spans, or corrections are inserted into prompts. / 泄露检查通过：prompt 不插入标签、span 或修正。
- P0 mean plain pointwise ACPI accept is 0.424; careful/answer-blind/locate reduce it to 0.188/0.125/0.174. / P0 平均普通 pointwise ACPI 接受为 0.424；careful/answer-blind/locate 降到 0.188/0.125/0.174。
- Sibling/careful-sibling accuracy is 0.990/0.986; this remains much stronger than pointwise but is not perfect in E61. / sibling/仔细 sibling 准确率为 0.990/0.986，仍明显强于 pointwise，但在 E61 中不是完美。
- Highest plain pointwise risks are `romanized_zh` and `mixed` routes, and `percentage_base`, `code_execution`, and `counting_order` families. / 普通 pointwise 风险最高的是 `romanized_zh` 与 `mixed` 路径，以及 `percentage_base`、`code_execution`、`counting_order` 错误类型。
- Sibling errors occur only for `gemma4_26b_a4b_it` and concentrate in `romanized_zh`; treat transliteration as a new high-value follow-up direction. / sibling 错误只出现在 `gemma4_26b_a4b_it`，并集中在 `romanized_zh`；应把转写语言作为下一步高价值方向。

Next / 下一步：

- E62 external P0 candidate smoke is next. Check license, tokenizer/chat-template, HF text generation, deterministic Yes/No or A/B option-logprob scoring, hidden-state output, hook compatibility, memory behavior, and vLLM feasibility for `nemotron_cascade2_30b_a3b_candidate`, `glm47_flash_candidate`, and `exaone45_33b_candidate`. / 下一步是 E62 外部 P0 候选 smoke test；检查 Nemotron、GLM、EXAONE 的许可、tokenizer/chat-template、HF 生成、确定性选项打分、hidden-state 输出、hook 兼容性、显存行为与 vLLM 可行性。
- After E62, promote only passing candidates into E63 replication; do not use pending-smoke candidates as official evidence. / E62 后只把通过的候选提升到 E63 复现；pending-smoke 候选不能作为官方证据。

## 2026-04-29 E62 Completed / E62 已完成

Report / 报告：`reports/E62_EXTERNAL_P0_SMOKE_20260429.md`。
Audit / 审计：`reports/E62_EXTERNAL_P0_SMOKE_AUDIT_20260429.json`，准入决策已完成。
Results / 结果：`results/E62_external_p0_smoke/`。

Key facts / 关键事实：

- `glm47_flash_candidate` passed license/backend/tokenizer/HF-hidden-state/option-logprob/layer-discovery checks and is admitted into expanded P0 for E63. / `glm47_flash_candidate` 通过许可、后端、tokenizer、HF hidden-state、选项 logprob 与层发现检查，进入扩展 P0 做 E63。
- `nemotron_cascade2_30b_a3b_candidate` remains backend-blocked because HF dynamic loading requires missing `mamba-ssm`; it must not be used as official evidence until that dependency/backend path passes a new smoke test. / `nemotron_cascade2_30b_a3b_candidate` 因 HF 动态加载需要缺失的 `mamba-ssm` 而后端受阻；新 smoke 通过前不得作为官方证据。
- `exaone45_33b_candidate` remains backend/license-limited because current Transformers cannot load `exaone4_5`, local docs request a forked backend, and license is non-commercial research/education only; it must not be used as official evidence. / `exaone45_33b_candidate` 因当前 Transformers 无法加载 `exaone4_5`、本地文档要求 fork 后端且许可为非商业研究/教育用途而受限；不得作为官方证据。
- Active workspace audit passed after E62. / E62 后活动工作区审计通过。
- Next: run E63 GLM replication over E42, E60, and E61 first; add GLM mechanism runs only if hooks/components work cleanly. / 下一步：先在 GLM 上复现 E42、E60 与 E61；只有 hook/组件路径干净可用时再加入 GLM 机制实验。

Useful commands / 常用命令：

```bash
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3
python scripts/audit_e62_external_p0_smoke.py
python scripts/audit_active_official_workspace.py
```

## 2026-04-29 E62-E70 Completed / E62-E70 已完成

Synthesis / 综合：`reports/E62_E70_AUTONOMOUS_SYNTHESIS_20260429.md`。
Roadmap / 路线图：`reports/NEXT_EXPERIMENT_ROADMAP_20260429.json` 已标记 E62-E70 完成。

Key facts / 关键事实：

- E62 admitted only `glm47_flash_candidate` into expanded P0; Nemotron and EXAONE remain blocked and must not be used as official evidence without a new passing smoke test. / E62 只准入 GLM；Nemotron 与 EXAONE 未通过，不得作为官方证据。
- E63: GLM replicates pointwise strict ACPI over-acceptance but breaks the “sibling is always perfect” simplification. Treat GLM as boundary evidence. / E63：GLM 复现单点 strict ACPI 过度接受，但打破“sibling 永远完美”的简化说法；GLM 是边界证据。
- E64: GLM hard-task natural generation found 8 final-correct rows out of 72; all 8 were manually audited strict-valid, so no new natural ACPI. / E64：GLM 困难题自然生成 72 条中 8 条 final-correct，全部 strict-valid，未发现新自然 ACPI。
- E65: E61 full-layer residual probes are very strong across all four core/expanded P0 models; GLM best layer 27 reaches 0.979 despite weak sibling behavior. / E65：E61 全层 residual probe 在四个核心/扩展 P0 上很强；GLM 第 27 层 0.979，尽管 sibling 行为弱。
- E66: GLM sibling weakness is partly label/position-related but not fully fixed by simple calibration; contrastive objective design needs more work. / E66：GLM sibling 弱部分来自标签/位置，但简单校准不能完全修复；对比目标设计仍需深挖。
- E67: literal error-span matching is unreliable across multilingual routes; hidden probes still recover process validity, supporting a surface-lexicalization vs process-semantics mismatch. / E67：多语言路线中字面 error-span 匹配不可靠；hidden probe 仍能恢复过程有效性，支持表层词汇化与过程语义错配。
- E68: filter simulation shows outcome-only and plain pointwise retain substantial strict ACPI; sibling suppresses core P0 but GLM weakens expanded-P0 aggregate. / E68：筛选模拟显示只看答案和普通单点会保留大量 strict ACPI；sibling 压制核心 P0 风险，但 GLM 拉低扩展 P0 聚合。
- E69: many controlled strict-invalid traces include later repair/override; use the term `strict trace-selection risk`, and keep unrepaired ACPI prevalence separate. / E69：许多受控 strict-invalid trace 含后续修复/覆盖；必须使用 `strict trace-selection risk`，并把 unrepaired ACPI 发生率单独报告。
- E70: statistics appendix adds Wilson CIs and leave-one-family sensitivity. / E70：统计附录已加入 Wilson 区间与留一错误类型敏感性。

Current safe claim / 当前安全主张：

Controlled strict trace-selection risk is robust and mechanistically visible in residual states. Pointwise absolute Yes/No verifiers over-accept strict ACPI; stronger pointwise prompts reduce risk; sibling is strong for core P0 but not a universal oracle; natural unrepaired ACPI remains uncommon in current hard-task samples. / 受控 strict trace-selection 风险稳健且在 residual state 中可见；单点 absolute Yes/No 会过度接受 strict ACPI；更强单点 prompt 降低风险；sibling 对核心 P0 很强但不是通用 oracle；当前困难题自然未修复 ACPI 仍不常见。

Recommended next / 建议下一步：

1. E71 strict vs repair-aware verifier objective. / 严格 vs 修复口径 verifier 目标。
2. E72 best-layer causal mediation using E65 layers. / 用 E65 最佳层做因果中介。
3. E73 translated-span token patching. / 翻译对齐 span 的 token patch。
4. E74 larger natural harvesting with strict/repaired/unrepaired labels. / 更大自然采样并区分 strict/repaired/unrepaired。
5. E75 label-free contrastive objective for GLM-style A/B bias. / 面向 GLM 式 A/B 偏置的无标签对比目标。

## 2026-04-29 E71/E76/E77/E78/E79 Completed / E71/E76/E77/E78/E79 已完成

Report / 报告：`reports/E71_E79_REPAIR_HIDDEN_LABELFREE_AUDIT_20260429.md`。  
Machine-readable summary / 机器可读汇总：`reports/E71_E79_REPAIR_HIDDEN_LABELFREE_AUDIT_20260429.json`。  
Queue status / 队列状态：`logs/e71_e79_e76_e77_e78_status_20260429.jsonl`，`all_done`。

Key facts / 关键事实：

- E71 separates strict trace-selection from repair-aware reading. Strict means any visible wrong step is invalid; repair-aware means explicitly corrected scratch mistakes can be accepted if the final surviving proof is valid. / E71 区分严格 trace-selection 与修复感知阅读。严格口径下任何可见错步都 invalid；修复口径下，明确修复的草稿错误可以在最终证明有效时被接受。
- Under strict scoring, Qwen35-27B/Gemma4-31B/Gemma4-26B-A4B reject most controlled invalid traces but accept both Gemma26 unrepaired hard-task ACPI cases. GLM rejects those two but has many valid false rejections. / 严格口径下，Qwen35-27B/Gemma4-31B/Gemma4-26B-A4B 拒绝大多数受控 invalid trace，但接受 Gemma26 两条未修复困难题 ACPI；GLM 拒绝这两条但误拒绝很多 valid trace。
- E78 hidden-probe audit passes negative controls: leave-one-task/family/route accuracies remain high and permutation nulls stay near 0.50. / E78 hidden-probe 负控制通过：留一任务/错误族/路径准确率仍高，标签置换约为 0.50。
- E79 shows GLM raw sibling weakness is mostly a label/output-format readout bottleneck: label-free two-pass reaches 0.990 accuracy. / E79 显示 GLM raw sibling 弱主要是标签/输出格式读出瓶颈；无标签 two-pass 达到 0.990。
- E76/E77 hard-task hidden replay is a boundary result: only projected scores were saved, not full hidden tensors, and no simple repair trajectory was proven. / E76/E77 困难题 hidden 回放是边界结果：只保存投影分数，没有保存完整 hidden tensor，也没有证明简单修复轨迹。

Current safe claim / 当前安全主张：

Process-validity evidence is present in residual hidden states, but verifier decisions can fail to use it because of objective, threshold, repair-aware reading, and output-label/readout bottlenecks. Controlled strict ACPI risk is robust; natural unrepaired ACPI remains low-frequency in current samples and needs larger harvesting. / residual hidden state 中存在过程有效性证据，但 verifier 决策可能因为目标、阈值、修复感知阅读和输出标签/读出瓶颈而没有用好。受控 strict ACPI 风险稳健；当前自然未修复 ACPI 仍是低频样本，需要扩大采样。

Recommended next / 建议下一步：

1. E80 progressive-prefix verifier replay for Gemma31 repaired and Gemma26 unrepaired hard-task cases. / 对 Gemma31 repaired 与 Gemma26 unrepaired 困难题做 progressive-prefix verifier replay。
2. E81 label-free sibling across Qwen/Gemma/GLM. / 在 Qwen/Gemma/GLM 上扩展无标签 sibling。
3. E82 deep audit and ablation of the two Gemma26 unrepaired ACPI cases. / 对 Gemma26 两条未修复 ACPI 做深度审计与消融。
4. E83 larger natural hard-task harvesting. / 更大规模自然困难题采样。
5. E84 GLM readout mediation from hidden validity direction to raw labels and label-free scores. / 做 GLM 从 hidden validity direction 到 raw 标签与无标签分数的读出中介分析。

## 2026-04-29 E80-E84 Completed / E80-E84 已完成

Report / 报告：`reports/E80_E84_PREFIX_LABELFREE_PREVALENCE_MEDIATION_20260429.md`。  
Machine-readable summary / 机器可读汇总：`reports/E80_E84_PREFIX_LABELFREE_PREVALENCE_MEDIATION_20260429.json`。  
Queue status / 队列状态：`logs/e80_e84_status_20260429.jsonl` 与 `logs/e81_trace1_fulloption_status_20260429.jsonl` 均为 `all_done`。

Key facts / 关键事实：

- E80 shows Gemma31 repaired ACPI turns from accepted early wrong-answer prefixes to rejected after repair markers under the same strict verifier prompt. / E80 显示 Gemma31 repaired ACPI 在同一 strict verifier prompt 下，早期错误答案前缀会被接受，修复标记出现后转为拒绝。
- E80 shows Gemma26 unrepaired ACPI is accepted already at the erroneous factorization prefix and remains accepted at the end, despite non-clean hidden validity projection. / E80 显示 Gemma26 未修复 ACPI 在错误因式分解前缀处就被接受，到结尾仍被接受，尽管 hidden validity 投影并不干净。
- E81 full-option check fixes the `Trace1/Trace2` first-token artifact. Core P0 remains robust; GLM improves but still has raw-label bias, while label-free two-pass remains near-perfect. / E81 full-option 校验修正 `Trace1/Trace2` first-token 工件。核心 P0 仍稳；GLM 有改善但仍有 raw-label 偏置，而无标签 two-pass 近乎完美。
- E82 finds final-answer anchoring is strong but not the whole story: wrong final answers make all verifiers reject, while removed/masked final answers still leave Qwen/Gemma mostly accepting the unrepaired traces. / E82 发现最终答案锚定很强但不是全部：错最终答案让所有 verifier 拒绝；删除/遮蔽最终答案后 Qwen/Gemma 仍大多接受未修复 trace。
- E83 pooled no-gold hard-task audit: 288 generated rows, 127 final-correct audited rows, 11 strict ACPI, 9 repaired ACPI, 2 unrepaired ACPI. / E83 pooled no-gold 困难题审计：288 条生成、127 条 final-correct 人审、11 条 strict ACPI、9 条 repaired ACPI、2 条 unrepaired ACPI。
- E84 GLM readout mediation: hidden margin correlates strongly with label-free margin but weakly with raw A/B margin, supporting a readout/output-label bottleneck. / E84 GLM 读出中介：hidden margin 与无标签 margin 强相关，但与 raw A/B margin 弱相关，支持读出/输出标签瓶颈。

Current safe claim / 当前安全主张：

Controlled strict ACPI risk is robust; natural unrepaired ACPI is low-frequency but real in current hard-task samples; hidden process evidence is available, but objective, final-answer anchor, repair-aware reading, and output-label readout determine whether the verifier decision uses it. / 受控 strict ACPI 风险稳健；当前困难题自然未修复 ACPI 低频但真实存在；hidden 过程证据可用，但目标、最终答案锚定、修复感知阅读和输出标签读出决定 verifier 决策是否使用它。

Recommended next / 建议下一步：

1. E85 full hidden cache for hard-task repair/unrepaired case trajectories. / 对困难题 repaired/unrepaired case 做完整 hidden cache。
2. E86 algebra-equivalence adversarial set around factorization/sign/root-set traps. / 围绕因式分解、符号、根集合构造代数等价陷阱。
3. E87 GLM readout intervention from hidden validity direction to raw A/B logits. / 对 GLM 做 hidden validity direction 到 raw A/B logits 的读出干预。
4. E88 larger answer-first/no-gold natural sample with manual audit. / 扩大 answer-first/no-gold 自然采样并人审。
5. E89 repair-policy-aware filter simulation. / 做修复策略感知的筛选器仿真。

## 2026-04-29 E85-E89 Current Handoff / 当前断点

- Status / 状态：E85-E90 are completed; `logs/e85_e89_status_20260429.jsonl` and `logs/e90_component_cache_status_20260429.jsonl` both end with `all_done`. / E85-E90 已完成，两个状态日志均为 `all_done`。
- Final synthesis / 最终综合：`reports/E85_E90_FINAL_SYNTHESIS_20260429.md` and `.json`. / 最终综合已落盘。
- E88 manual audit / E88 人审：`data/processed/e88_answer_first_manual_audit_20260429.jsonl`, `reports/E88_ANSWER_FIRST_MANUAL_AUDIT_20260429.md`, and `.json`. / E88 人审数据与报告已落盘。
- E90 component report / E90 组件报告：`reports/E90_COMPONENT_ACTIVATION_CACHE_20260429.md` and `.json`. / E90 组件激活报告已落盘。
- E89 rerun / E89 重跑：`reports/E89_REPAIR_POLICY_FILTER_SIMULATION_20260429.md` now includes E88 manual policy records. / E89 已纳入 E88 人审策略记录。
- Important boundary / 重要边界：E86 is a negative-control/boundary result. Short explicit algebra ACPI is caught by strict pointwise in all P0 models, so do not overclaim that absolute verifiers miss algebra errors in general. / E86 是负控制/边界结果，不能过宽声称 absolute verifier 普遍漏代数错。
- Current safe claim / 当前安全主张：controlled strict ACPI trace-selection risk is robust; natural unrepaired ACPI is low-frequency but real; hidden residual/MLP/token-mixer activations contain process-validity evidence, but objective, threshold, final-answer anchoring, repair-aware reading, local subtlety, and output-label/readout format determine whether verifier decisions use it. / 受控 strict ACPI trace-selection 风险稳健；自然未修复 ACPI 低频但真实存在；hidden residual/MLP/token-mixer 激活含过程有效性证据，但 verifier 决策是否用上它取决于目标、阈值、最终答案锚定、修复感知阅读、局部隐蔽性和输出标签/读出格式。
- Next practical step / 下一步：run `python scripts/audit_active_official_workspace.py` after whitelist update; then plan larger no-gold natural harvesting and component-level causal patching. / 白名单更新后跑 active workspace audit；随后规划更大无 gold 自然采样与组件级因果 patching。

## 2026-04-29 Thinking-Mode Audit / thinking 模式审计

Reports / 报告：

- `reports/THINKING_MODE_AUDIT_AND_RERUN_PLAN_20260429.md`. / thinking/non-thinking 重分类与重测表。
- `reports/E91_THINKING_MODE_CONFIG_AUDIT_20260429.md`. / E91 tokenizer、chat-template、参数与 parser 审计。
- `results/E91_thinking_mode_config_audit/e91_thinking_mode_config_audit.json`. / E91 机器可读结果。

Current mode boundary / 当前模式边界：

- `DV`: direct-answer verifier. Existing first-token `Yes/No` or `A/B` logprob verifier runs belong here because scripts used `enable_thinking=False`. / 直接回答 verifier；已有首 token `Yes/No`/`A/B` logprob verifier 属于这里。
- `TV`: thinking verifier. Must enable thinking, generate full output, and parse a final decision. First-token option-logprob is invalid for this mode. / thinking verifier；必须开启 thinking，生成完整输出并解析最终判定，不能用首 token option-logprob。
- `NG`: non-thinking generation. Existing E57/E88 hard-task prevalence belongs here. / 非 thinking 生成；已有 E57/E88 困难题发生率属于这里。
- `TG`: thinking generation. Existing evidence is sparse; E92/E93 must replenish it. / thinking 生成；当前证据稀疏，需要 E92/E93 补齐。
- `MI-DV`: hidden/residual/MLP/token-mixer mechanism under direct-verifier prompts. / direct-verifier prompt 下的机制诊断。

E91 facts / E91 事实：

- Qwen35-27B, Gemma4-31B-it, Gemma4-26B-A4B-it, and GLM-4.7-Flash all passed template differentiation checks for thinking vs non-thinking. / 四个模型均通过 thinking 与非 thinking 模板区分检查。
- Qwen thinking starts with `<think>`; non-thinking inserts an empty thought block. Gemma thinking inserts `<|think|>`; non-thinking starts an empty thought channel. GLM thinking starts with `<think>`; non-thinking starts with `</think>`. / Qwen/Gemma/GLM 的模板差异已记录。
- Use local model-card thinking parameters for TG/TV reruns: Qwen `temperature=1.0, top_p=0.95, top_k=20, presence_penalty=1.5`; Gemma `temperature=1.0, top_p=0.95, top_k=64`; GLM default evaluation `temperature=1.0, top-p=0.95`. / 后续 TG/TV 重跑使用本地模型卡建议参数。

Immediate next experiments / 立即下一实验：

1. E92: thinking hard-task natural harvesting over all P0 models, variants `neutral`, `answer_first_no_gold`, and `self_check`, with final-correct manual/agentic audit into strict-valid, repaired ACPI, and unrepaired ACPI. / E92：全 P0 thinking 困难题自然采样并人审。
2. E93: thinking simple-task natural prevalence rerun of E48-style no-leak tasks. / E93：简单任务 thinking 自然发生率。
3. E94: thinking verifier objective ladder over controlled E42/E54/E61 subsets, parsing final decisions instead of first-token logprob. / E94：受控样本 thinking verifier objective 梯度。
4. E95: thinking sibling/readout, especially GLM, with both orders and label-free two-pass final decisions. / E95：thinking sibling/readout，重点 GLM。
5. E97: thinking mechanism capture, saving thought-token, repair-marker, residual/MLP/token-mixer, and final-decision-token states separately. / E97：thinking 机制捕捉。

## 2026-04-29 E92 Phase-A Running / E92 第一阶段运行中

- Session / 会话：`tmux p02_e92_phaseA_20260429`。
- Status log / 状态日志：`logs/e92_thinking_hard_task_status_20260429.jsonl`。
- Current active log / 当前模型日志：`logs/e92_qwen35_27b_thinking_k2_20260429.log`。
- Scope / 范围：all core/expanded P0 models, 6 AIME-style tasks, 3 prompt variants (`neutral`, `answer_first_no_gold`, `self_check`), `k=2`, `max_new_tokens=3072`, `thinking=true`. / 全 P0/扩展 P0，6 道困难题，3 个 prompt 变体，每格 2 条，thinking 开启。
- Parameter note / 参数说明：Qwen uses `temperature=1.0, top_p=0.95, top_k=20`; Gemma uses `temperature=1.0, top_p=0.95, top_k=64`; GLM uses `temperature=1.0, top_p=0.95, top_k=0`. / 参数按 E91 本地模型卡设置。
- Parser note / 解析说明：thinking models often compute the answer without obeying the exact `Final answer:` line. `run_e49_hard_task_conditioning_official.py` now records `extraction_method`; final-marker absence is preserved, but answer phrases such as `Sum = 70` can be parsed for final-correct filtering. / thinking 模型常不写精确 `Final answer:` 行；脚本现在记录 `extraction_method`，保留 final marker 缺失信息，同时允许从 `Sum = 70` 等答案短语中抽取最终答案。
- Smoke result / smoke 结果：Qwen one-task smoke showed no gold/trap leakage and all rows `thinking=true`; 1024 tokens truncated, 3072 tokens allowed answer extraction from answer phrases. / Qwen 小样本确认无泄露且 thinking 标记正确；1024 token 不够，3072 token 可抽取答案。
- Next after all_done / 完成后下一步：run `python scripts/build_e92_thinking_hard_task_audit_sheet.py`, manually/agentically audit final-correct rows, summarize strict-valid/repaired/unrepaired ACPI, then update History/KG and decide E93/E94 ordering. / 队列结束后构建 audit sheet，人审 final-correct 行，再更新 history/KG。

## 2026-04-29 E100-E102 Completed / E100-E102 已完成

Reports / 报告：

- `reports/E100_E102_BATCH_MODE_HIDDEN_CONTRAST_20260429.md` and `.json`. / batch 与 thinking 模式机制审计报告。
- `results/E100_batch_invariance_audit/qwen35_27b_e100_batch_invariance.json`. / E100 固定序列 batch 不变性。
- `results/E101_batch_generation_sensitivity/qwen35_27b_e101_batch_generation_sensitivity.json`. / E101 小样本 batch 生成敏感性。
- `results/E102_thinking_nonthinking_hidden_contrast/qwen35_27b_e102_thinking_nonthinking_hidden_contrast.json`. / E102 thinking/non-thinking hidden 对比。

Key facts / 关键事实：

- E92 Qwen thinking pilot completed before pause: 36 generated, 6 final-correct, no strict `Final answer:` line in any row. / E92 Qwen thinking 初测已完成：36 条生成、6 条 final-correct，所有行都没有严格 `Final answer:` 行。
- Boxed thinking rerun was intentionally paused after two checkpoint rows: both hit `max_new_tokens=8192` and still did not emit `\boxed{}`. / boxed thinking 重跑在两条 checkpoint 后暂停：两条都撞 8192 token，仍没有输出 `\boxed{}`。
- E100 fixed-token replay: with `max_model_len=4096`, batch=1/2/4 residual/MLP/token-mixer/logits are extremely close but not bit-identical; worst min cosine 0.9995675 and worst max relative L2 0.03044. / E100 固定 token 复放：4096 token 下 batch=1/2/4 的 residual/MLP/token-mixer/logits 极接近但非 bit-identical；最差 min cosine 0.9995675，最大相对 L2 0.03044。
- E101 generation sensitivity: capped 512-token generation for NG/TG across batch=1/2/4 always hit max and produced no final marker; this is a diagnostic, not prevalence. / E101 生成敏感性：512 token 硬上限下 NG/TG 在 batch=1/2/4 都撞上限且无 final marker；这是诊断，不是发生率。
- E102 strict-verifier replay: NG traces average 1124 completion tokens, TG traces average 4352; NG accept 0.667, TG accept 0.75. NG_E57 rows are accepted strongly; NG_E88 answer-first repaired rows are rejected; TG_E92 is mixed. / E102 strict verifier 复放：NG 平均 1124 token，TG 平均 4352；NG accept 0.667，TG accept 0.75。NG_E57 强接受，NG_E88 answer-first repaired 被拒，TG_E92 混合。

Interpretation / 解释：

- Batch size is a valid engineering confound to audit. For fixed-token hidden replay it does not erase the signal, but generation-time batch sensitivity must be kept separate. / batch size 是必须审计的工程 confound；固定 token hidden replay 中它不会抹掉信号，但现场生成的 batch 敏感性必须分开。
- Qwen thinking shows a closure problem: more token budget can produce more self-checking rather than a final answer. / Qwen thinking 显示“收口问题”：更多 token 预算可能带来更多自检，而不是最终答案。
- Non-thinking does not mean no internal computation. Current safe wording: non-thinking hides or compresses the reasoning channel, while residual/MLP/token-mixer states can still carry process-validity evidence. / non-thinking 不等于没有内部计算；安全表述是：non-thinking 隐藏或压缩外显推理通道，但 residual/MLP/token-mixer 仍可携带过程有效性证据。

## 2026-04-29 E103-E104 Completed / E103-E104 已完成

Reports and data / 报告与数据：

- `reports/E103_E104_TG_NG_FAIRNESS_AUDIT_20260429.md` and `.json`. / TG/NG 公平对照报告。
- `results/E103_tg_ng_fair_hardtask/qwen35_27b_e103_tg_ng_fair_hardtask.json`. / E103 生成结果。
- `data/processed/e104_tg_ng_process_audit_sheet_20260429.jsonl`. / E104 待审表。
- `data/processed/e104_tg_ng_process_audit_official_20260429.jsonl`. / E104 人审后 official 表。
- `results/E104_tg_ng_process_audit/e104_tg_ng_process_audit_official_summary.json`. / E104 人审汇总。

Key facts / 关键事实：

- E103 Qwen setup: 3 tasks, 3 prompt variants, k=1, `max_new_tokens=4096`, no gold/trap leakage, modes `NG_baseline`, `NG_matched_sampling`, and `TG_official`. / E103 Qwen 设置：3 道题、3 个 prompt、每格 1 条、4096 token 上限、无答案/陷阱泄露。
- Strict final-correct: `NG_baseline` 8/9, `NG_matched_sampling` 7/9, `TG_official` 0/9. / strict 最终答案正确率：NG baseline 8/9，NG matched 7/9，TG 0/9。
- Final marker: both NG modes 9/9 explicit final markers; TG 0/9. / 两种 NG 都 9/9 有明确 final marker，TG 是 0/9。
- Hit-max: `NG_baseline` 2/9, `NG_matched_sampling` 4/9, `TG_official` 9/9. / 撞上限：NG baseline 2/9，NG matched 4/9，TG 9/9。
- TG fallback-correct is 5/9, but all are unfinished 4096-token traces without explicit final marker; do not count these as strict final decisions. / TG fallback 正确为 5/9，但全是无明确 final marker 的截断 trace，不能算 strict final decision。
- E104 manual audit: 3 repaired strict ACPI cases in NG answer-first rows, all caused by an initial wrong `Final answer` later corrected; unrepaired ACPI = 0. / E104 人审：NG answer-first 中 3 条 repaired strict ACPI，均为开头写错 final answer 后面修复；未修复 ACPI 为 0。

Current implication / 当前含义：

- Qwen thinking does not currently support a "TG is better than NG" claim under strict final-decision evaluation. The stronger claim is that thinking exposes a closure/final-decision problem and makes fallback extraction scientifically dangerous. / 当前不能声称 Qwen thinking 在 strict final-decision 下优于 NG；更稳的结论是 thinking 暴露了收口/最终决策问题，fallback 抽取会造成科学误读。
- E105 has now completed; use its final-contract findings before scaling TG to more P0 models. / E105 已完成；后续扩展 TG 到更多 P0 模型前，应采用其 final-contract 和 clean-stop 口径。

## 2026-04-29 E105 Completed / E105 已完成

Reports and data / 报告与数据：

- `reports/E105_TG_CLOSURE_POLICY_20260429.md` and `.json`. / Qwen thinking 收口策略报告。
- `logs/e105_qwen35_tg_closure_k1_checkpoint_20260429.jsonl`. / 8k capped pilot checkpoint。
- `logs/e105r_qwen35_canary16k_checkpoint_20260429.jsonl`. / 16k no-timecap canary checkpoint。
- `logs/e105r_qwen35_canary32k_checkpoint_20260429.jsonl`. / 32k no-timecap canary checkpoint。
- `scripts/run_e105_tg_closure_policy.py`, `scripts/summarize_e105_tg_closure_policy.py`, `scripts/launch_e105_reviewer_stress_20260429.sh`. / 运行和汇总脚本。

Key facts / 关键事实：

- 8k capped pilot: 2 rows, both hit 8192 tokens, 0/2 explicit `Final answer`, strict final-correct 0/2, fallback-correct 1/2. / 8k 仍不收口。
- 16k no-timecap canary on `aime25_base_divisor_p1`: 3/3 strict final-correct and 3/3 explicit marker, but only `final_contract_16384` cleanly stopped; `free_think_16384` and `budgeted_final_16384` continued after the final marker and hit max. / 16k 能出现答案，但 free/budgeted 没有干净停住。
- 32k no-timecap canary: `final_contract_32768` stopped naturally at 13120 tokens with `Final answer: 70` as the final line. / 32k 强 final-contract 在该题上自然收口。
- Leakage audit: 0 rows with gold answer in prompt and 0 rows with trap note in prompt. / 无答案或陷阱泄露。

Current implication / 当前含义：

- Qwen TG should be evaluated with three separate fields: fallback number, explicit final marker, and clean final stop. / Qwen TG 评估必须分开记录 fallback 数字、final marker、干净停止。
- E105 does not prove TG is better than NG; it proves the earlier Qwen TG failure has a strong closure-policy component. / E105 不证明 thinking 更强，只证明 Qwen 之前的 TG 失败有很强的收口策略因素。
- Next mechanism step should capture residual/MLP/token-mixer/attention-related activations around thought tokens, repair markers, and final-decision tokens under `final_contract` conditions. / 下一步机制实验应在 final-contract 条件下捕捉 thought token、repair marker、final decision token 附近的 residual/MLP/token-mixer/attention 相关激活。

## 2026-04-30 E106-E114 Completed / E106-E114 已完成

Plan and scripts / 计划与脚本：

- `reports/E106_E120_EXPERIMENT_EXECUTION_PLAN_20260430.md`. / E106-E120 总体规划。
- `reports/E106_E114_NONTHINKING_MECHANISM_SUITE_20260430.md`. / E106-E114 阶段报告。
- `scripts/run_e106_e114_nonthinking_mechanism_suite.py`. / non-thinking 机制套件。
- `scripts/launch_e106_e114_nonthinking_mechanism_queue_20260430.sh`. / 四模型顺序队列。

Execution / 执行：

- Session / 会话：`tmux p02_e106_e114_20260430`。
- Status / 状态：`logs/e106_e114_nonthinking_mechanism_status_20260430.jsonl`。
- Queue log / 队列日志：`logs/e106_e114_nonthinking_mechanism_queue_20260430.log`。
- Models / 模型顺序：`qwen35_27b` -> `gemma4_31b_it` -> `gemma4_26b_a4b_it` -> `glm47_flash_candidate`。
- Final state / 最终状态：`all_done` at `2026-04-30T01:08:58+08:00`。

Audit facts / 审计事实：

- `py_compile`、launcher `bash -n`、active workspace audit passed. / 静态检查通过。
- Smoke passed on Qwen, Gemma4-26B-A4B, and GLM. / 三个模型家族 smoke 通过。
- Important correction: E106/E114 now use plain absolute Yes/No as `base_accept`; strict-prompt residual supplies the hidden process score. / 重要修正：E106/E114 的 base accept 使用 plain absolute Yes/No，hidden process score 来自 strict prompt residual；这样才能测试 hidden gate 是否修复 plain over-accept。
- Prompt leakage counters are zero in all four official result files. / 四个官方结果文件的 prompt 泄露计数均为 0。

Scientific purpose / 科学目的：

- Separate process-validity evidence from readout confidence. / 区分过程有效性证据与读出置信度。
- Test whether long self-consistent suffixes and answer anchors suppress process evidence. / 测试长自洽后文与答案锚定是否压制过程证据。
- Simulate a hidden-gated verifier and small activation steering to see whether non-thinking latent process monitoring can be released. / 模拟 hidden-gated verifier 与小规模 activation steering，检验 non-thinking 潜在过程监控能否被释放。

Key results / 关键结果：

- Hidden process AUC is high across models: Qwen 1.000, Gemma31 1.000, Gemma26 0.970, GLM 0.997. / hidden process AUC 在四模型上都很高。
- Process direction and confidence direction are highly aligned (`cosine=0.935-0.994`), so process evidence is not independent of confidence; however partial correlations remain positive (`0.650-0.882`) and hidden accuracy exceeds plain Yes/No accuracy. / 过程证据与置信度高度缠绕，但不能完全化约为置信度。
- Hidden gate reduces controlled ACPI retention from 0.375-0.458 to 0-0.042 while mostly preserving valid traces. / hidden gate 显著降低 ACPI 保留率，并大体保留 valid trace。
- E109 steering flips only GLM strongly; process-invalid and confidence-low steering are similar there. / E109 只在 GLM 上强翻转，且 process 与 confidence 干预相似。
- Safe claim: in `MI-DV`, non-thinking hidden activations contain process-validity evidence, but objective/threshold/readout/anchor/repair-aware context determine whether final Yes/No uses it. / 安全 claim：non-thinking hidden activation 里有过程有效性证据，但最终 Yes/No 是否使用它取决于目标、阈值、读出、答案锚定和 repair-aware 上下文。

## 2026-04-30 E116-E118 Completed / E116-E118 已完成

Artifacts / 文件：

- `reports/E116_E120_EXECUTION_PLAN_20260430.md`.
- `reports/E116_E118_THINKING_STOP_SIGNAL_20260430.md`.
- `scripts/run_e116_e118_thinking_stop_signal_suite.py`.
- `scripts/launch_e116_e118_thinking_stop_signal_queue_20260430.sh`.
- `results/E116_E118_thinking_stop_signal/qwen35_27b_e116_e118_thinking_stop_signal_suite.json`.
- `results/E116_E118_thinking_stop_signal/qwen35_27b_e116_e118_component_points.pt`.

Execution / 执行：

- Queue status / 队列状态：`all_done` at `2026-04-30T01:30:06+08:00`.
- Source / 来源：12 saved Qwen thinking traces from E105/E103; no new generation. / 复放 E105/E103 的 12 条 Qwen thinking trace，不做新生成。
- Captured points / 捕捉点：61 points over final-answer, answer-phrase, post-final, and completion-end positions. / 61 个 token/position 点。
- Component cache shape / 激活缓存形状：`[61, 15, 5120]`.

Key facts / 关键事实：

- Selected stop key / stop 方向：`34:residual_hidden_state`.
- Clean-stop positive mean vs continuation negative mean: `29.345` vs `-8.438`; threshold `10.453`. / clean-stop 与继续生成点明显分离。
- Stop policy simulation: 10 final-like candidates, either-stop rate 0.600, stopped correct candidates 6/6, missed final-correct candidates 3/9, mean savings among stopped candidates 1318 tokens. / 早停模拟高精度但低召回。
- Safe claim / 安全说法：thinking 中存在可测的 stop/commit hidden signal；它不同于 process-validity signal，但目前只是 Qwen 小样本 post-hoc 证据。

## 2026-04-30 E120 Completed / E120 已完成

Artifacts / 文件：

- `scripts/run_e120_unified_audit_package.py`.
- `reports/E120_UNIFIED_AUDIT_PACKAGE_20260430.md`.
- `reports/E120_UNIFIED_AUDIT_PACKAGE_20260430.json`.

Purpose / 目的：

- E120 is an appendix/audit synthesis, not a new model run. / E120 是附录审计汇总，不是新模型实验。
- It records mode boundaries (`DV`, `MI-DV`, `NG`, `TG`, `MI-TG`, `PM`) and prevents mixing direct first-token verifier, thinking verifier, natural generation, and mechanism replay claims. / 它用于固定模式边界，防止不同口径混用。

Key facts / 关键事实：

- E106-E114 leakage status: PASS for all four P0/expanded-P0 result files. / E106-E114 四模型泄露审计通过。
- E116-E118 leakage status: PASS. / E116-E118 泄露审计通过。
- E120 restates that natural unrepaired ACPI prevalence still needs E119 expansion. / E120 明确自然 unrepaired ACPI 仍需 E119 扩样。

## 2026-04-30 E119 Completed / E119 已完成

Artifacts / 文件：

- `reports/E119_NATURAL_HARDTASK_EXPANSION_PLAN_20260430.md`.
- `scripts/build_e119_natural_hardtask_audit_sheet.py`.
- `scripts/launch_e119_natural_hardtask_expansion_queue_20260430.sh`.
- Status / 状态：`logs/e119_natural_hardtask_expansion_status_20260430.jsonl`.
- Queue log / 队列日志：`logs/e119_natural_hardtask_expansion_queue_20260430.log`.
- Result dir / 结果目录：`results/E119_natural_hardtask_expansion/`.
- Summary / 摘要：`results/E119_natural_hardtask_expansion/e119_audit_sheet_summary.json`.
- Audit sheet / 审计表：`data/processed/e119_natural_hardtask_final_correct_audit_sheet_20260430.jsonl`.

Design / 设计：

- Mode / 模式：`NG` only; `thinking=false`. / 只做 non-thinking generation。
- Models / 模型：`qwen35_27b`, `gemma4_31b_it`, `gemma4_26b_a4b_it`, `glm47_flash_candidate`.
- Tasks / 任务：6 AIME-style tasks.
- Variants / prompt 变体：`neutral`, `self_check`, `answer_first_no_gold`.
- k / 每格采样：2.
- max_new_tokens / 上限：4096.

Audit facts / 审计事实：

- `py_compile` for builder passed. / builder 编译通过。
- Queue `bash -n` passed. / 队列静态检查通过。
- Qwen 1-row smoke passed; prompt leakage counters were 0. / Qwen smoke 通过，gold/trap 泄露为 0。
- Active workspace audit passed before launch. / 启动前 active workspace audit 通过。

Final status / 最终状态：

- Completed with `all_done` at `2026-04-30T04:06:05+08:00`. / 已在该时间写出 `all_done`。
- Generated 144 rows and selected 104 final-correct rows for process/manual audit; leakage counters were all 0. / 生成 144 条，筛出 104 条 final-correct 进入过程/人工审计，泄露计数为 0。
- Per-model final-correct counts: Qwen 24/36, Gemma31 31/36, Gemma26-A4B 32/36, GLM 17/36. / 各模型 final-correct：Qwen 24/36，Gemma31 31/36，Gemma26-A4B 32/36，GLM 17/36。
- Boundary: this run is `NG_uniform_legacy_baseline`, not model-card HF profile; E146 is the Qwen/Gemma model-card-profile rerun. / 边界：本轮是项目统一采样 baseline，不是模型卡 HF profile；E146 才是 Qwen/Gemma 的模型卡 profile 复跑。

## 2026-04-30 E121-E130 Scaffold Initialized / E121-E130 脚手架已初始化

Artifacts / 文件：

- `reports/TOP_TIER_CLAIM_AND_NEXT_EXPERIMENT_PLAN_20260430.md`. / 顶会级主张与后续实验规划。
- `configs/e121_e130_next_stage_manifest.yaml`. / 下一阶段实验清单。
- `scripts/smoke_e121_e130_scaffold.py`. / 无 GPU 脚手架冒烟。
- `results/E121_E130_scaffold_smoke/e121_e130_scaffold_smoke.json`. / 冒烟结果。

Execution / 执行：

- No large model was loaded; this was safe while E119 occupies GPUs. / 没有加载大模型，不影响 E119 显存。
- `python -m py_compile scripts/smoke_e121_e130_scaffold.py scripts/audit_active_official_workspace.py` passed. / 编译通过。
- `python scripts/smoke_e121_e130_scaffold.py` passed with no prompt leakage hits. / 冒烟通过，模板无答案、人工标签或陷阱词泄露。
- `python scripts/audit_active_official_workspace.py` passed after whitelisting the official E121-E130 artifacts. / 新文件加入白名单后官方工作区审计通过。

Scientific framing / 科学框架：

- Keep claims separated by mode: `DV`, `TV`, `NG`, `TG`, `MI-DV`, `MI-TG`, `PM`. / 结论必须按模式分开。
- Current safe claim: controlled strict ACPI trace-selection risk is robust in `DV`; natural unrepaired ACPI is low-frequency but real in current `NG`; hidden process evidence exists, but final decisions can fail to use it because of confidence/objective/threshold/anchor/repair-aware reading/readout/stop-control mismatch. / 当前安全主张：direct verifier 中受控 strict ACPI 风险稳健；non-thinking 自然困难题中 unrepaired ACPI 低频但真实；hidden 里有过程证据，但最终决策可能因为置信度、目标、阈值、答案锚定、repair-aware 阅读、读出和停止控制错配而没用好。
- Next scientific bottlenecks: `TV` replication, larger natural prevalence CIs, process-vs-confidence-vs-stop disentanglement, causal component intervention, human audit reliability, and broader task/model families. / 下一步瓶颈：thinking verifier 复现、自然发生率置信区间、过程/置信度/停止解缠、组件因果干预、人审可靠性，以及更广任务/模型族。

Immediate next action / 直接下一步：

- Keep monitoring E119 until all four model generations finish. Then build and audit the final-correct process sheet before launching any GPU-heavy E121-E130 run. / 继续监控 E119，四模型完成后先构建并审计 final-correct 过程表，再启动任何重 GPU 的 E121-E130 实验。

## 2026-04-30 Qwen/Gemma Parameter Audit / Qwen/Gemma 参数审计

Artifacts / 文件：

- `reports/QWEN_GEMMA_PARAMETER_AUDIT_AND_NEXT_DESIGN_20260430.md`.
- `configs/qwen_gemma_parameter_profiles_20260430.yaml`.

Key facts / 关键事实：

- `DV`/`MI-DV` results are still valid as deterministic direct-verifier or teacher-forced hidden-replay evidence; generation sampling parameters do not apply to those scores. / `DV/MI-DV` 结果仍有效，因为它们是确定性打分或 teacher-forced hidden replay，不依赖采样参数。
- Historical `NG` hard-task generation used a project-uniform baseline (`temperature=0.7`, `top_p=0.95`, `top_k=50`, `max_new_tokens=4096`), not exact Qwen/Gemma model-card sampling. / 历史自然生成是项目统一采样 baseline，不是精确模型卡参数。
- Future Qwen/Gemma generation scripts should use `tokenizer.pad_token_id` when available; `run_e49`, `run_e103`, `run_e105`, and `run_e101` were patched accordingly. / 后续生成脚本应优先使用 tokenizer 自带 pad id；相关脚本已修正。
- Qwen exact model-card reruns need `presence_penalty`; current HF generate does not provide OpenAI-style presence penalty directly, so future runs must implement it, use a backend that supports it, or record it as unavailable. / Qwen 精确模型卡复跑需要处理 presence penalty。
- Qwen/Gemma-only next design: audit E119 Qwen/Gemma rows first, then run model-card NG rerun, token-level localization, residual/component span patch, process-confidence-stop disentanglement, thinking verifier objective, and final-contract TG natural generation. / Qwen/Gemma-only 下一步先审 E119 Qwen/Gemma 行，再做模型卡 NG 复跑、token 定位、span patch、过程/置信度/停止解缠、thinking verifier 和 final-contract TG。

## 2026-04-30 E119 Qwen/Gemma Audit Sheet + E146 Queue / E119 Qwen/Gemma 审计表与 E146 队列

Artifacts / 文件：

- `data/processed/e119_qwen_gemma_final_correct_audit_sheet_20260430.jsonl`.
- `results/E119_natural_hardtask_expansion/e119_qwen_gemma_audit_sheet_summary.json`.
- `configs/qwen_gemma_next_stage_queue_20260430.yaml`.
- `scripts/smoke_qwen_gemma_next_stage_queue.py`.
- `scripts/launch_e146_qwen_gemma_ng_model_card_queue_20260430.sh`.
- `results/E146_qwen_gemma_ng_model_card_hf_profile/_smoke/qwen_gemma_next_stage_queue_smoke.json`.

Facts / 事实：

- E119 Qwen/Gemma subset is already summarized: 108 generated rows, 87 final-correct rows for process audit, gold/trap leakage counters all 0. / E119 的 Qwen/Gemma 子集已经汇总：108 条生成，87 条 final-correct 进入过程审计，gold/trap 泄露计数全为 0。
- Per-model final-correct counts: Qwen 24/36, Gemma31 31/36, Gemma26-A4B 32/36. / 各模型 final-correct：Qwen 24/36，Gemma31 31/36，Gemma26-A4B 32/36。
- E146 three model generations completed by `2026-04-30T06:36:31+08:00`; queue wrote `all_done` at `2026-04-30T06:36:32+08:00`. / E146 三个模型生成在该时间前完成，队列随后写出 `all_done`。
- E146 audit-sheet build initially failed from a relative-path bug in `scripts/build_e119_natural_hardtask_audit_sheet.py`; after patching `display_path()` usage, the audit summary was rebuilt successfully at `2026-04-30T12:04:06+08:00`. / E146 审计表最初因相对路径 bug 失败；修复后已在该时间成功重建。
- E146 final summary: 108 generated rows, 97 final-correct rows for process audit, leakage counters all 0. Qwen strict/fallback final-correct 30/31 out of 36 with 8 hit-max rows; Gemma31 32/32 out of 36 with 2 hit-max rows; Gemma26-A4B 34/34 out of 36 with 2 hit-max rows. / E146 最终摘要：108 条生成，97 条 final-correct 进入过程审计，泄露计数为 0。Qwen strict/fallback final-correct 为 30/31/36，8 条 hit-max；Gemma31 为 32/32/36，2 条 hit-max；Gemma26-A4B 为 34/34/36，2 条 hit-max。
- E146 status log: `logs/e146_qwen_gemma_ng_model_card_status_20260430.jsonl`; queue log: `logs/e146_qwen_gemma_ng_model_card_queue_20260430.log`. / E146 状态日志和队列日志如上。
- E146 label: `NG_model_card_hf_profile`. For Qwen this is not exact model-card sampling because current HF generate still does not apply `presence_penalty`. / E146 标签为 `NG_model_card_hf_profile`。对 Qwen 来说这不是精确模型卡采样，因为当前 HF generate 仍未应用 `presence_penalty`。

Immediate next action / 直接下一步：

- Manually/process-audit E119/E146 final-correct sheets before using them as natural ACPI prevalence evidence. / 在把 E119/E146 写成自然 ACPI 发生率证据前，先做人审/过程审计。

## 2026-04-30 E119/E146 Official Process Audit Completed / E119/E146 官方过程审计已完成

Artifacts / 文件：

- `scripts/finalize_e119_e146_process_audit.py`.
- `reports/E119_E146_PROCESS_AUDIT_20260430.md`.
- `reports/E119_E146_PROCESS_AUDIT_20260430.json`.
- `data/processed/e119_e146_process_audit_official_20260430.jsonl`.
- `results/E119_E146_human_process_audit/e119_e146_process_audit_summary.json`.

Audit scope / 审计范围：

- Mode: `NG`, `thinking=false`. / 模式：非 thinking 自然生成。
- E119 is `NG_uniform_legacy_baseline`; E146 is `NG_model_card_hf_profile`. / E119 是项目统一采样 baseline；E146 是模型卡对齐 HF profile。
- Gold answers were used only offline for filtering; prompt leakage counters are 0. / 答案只用于离线筛选，prompt 泄露计数为 0。

Main results / 主要结果：

- 252 generated rows, 201 final/fallback-correct audit rows. / 252 条生成，201 条 final/fallback-correct 审计行。
- 200 strict final-decision rows; `1460087` is fallback-only unfinished and excluded from the strict final-decision denominator. / 200 条严格最终答案提交；`1460087` 是截断 fallback-only，不进 strict 分母。
- 46 strict ACPI rows, Wilson CI [0.177, 0.293] per strict final decision. / 46 条 strict ACPI。
- 44 repaired strict ACPI rows and 2 unrepaired ACPI rows. / 44 条已修复 strict ACPI，2 条未修复 ACPI。
- Unrepaired ACPI rate: 2/200 = 0.010, Wilson CI [0.003, 0.036]; per generated: 2/252 = 0.008, Wilson CI [0.002, 0.028]. / 未修复 ACPI 仍低频。
- The two unrepaired rows are `1190020` and `1460021`, both Gemma4-26B-A4B integer-pairs answer-first traces with the same wrong plus-xy factorization that happens to preserve the final count by sign symmetry. / 两条未修复个案均来自 Gemma26-A4B 整数二次型 answer-first trace，错误因式分解没有修复，但答案因符号对称碰巧正确。

Plain-language interpretation / 说人话解释：

- Many natural hard-task traces are not clean proofs. They often write a wrong first answer or wrong scratch step, then repair it. If a dataset/filter treats the whole trace as a proof, those are strict process-invalid traces even though a repair-aware reader may accept the final proof. / 许多自然困难题 trace 不是干净证明：模型会先写错答案或错公式，再修好。如果筛选器把整段 CoT 当严格证明，这些就是过程无效；如果把 CoT 当草稿并检查最终保留证明，它们可以是修复后有效。
- The current data do not support saying unrepaired natural ACPI is common. They support saying it is low-frequency but real, and that repaired strict ACPI is a dominant boundary condition. / 当前数据不能说自然未修复 ACPI 很常见；更准确是“低频但真实”，而“已修复 strict ACPI”是主要边界。

Next recommended work / 下一步建议：

- Use the official E119/E146 labels for E121-E130, especially hidden residual/MLP/token-mixer localization on repaired vs unrepaired rows. / 后续 E121-E130 应使用这些官方标签，尤其是在 repaired/unrepaired 行上做 hidden residual/MLP/token-mixer 定位。
- Add double-audit reliability before paper submission. / 投稿前补独立双审可靠性。
- Broaden natural hard-task families beyond the current 6 AIME-style templates. / 扩展到当前 6 个 AIME-style 模板之外的任务族。

## 2026-04-30 E131 E119/E146 Hidden Localization Completed / E119/E146 隐藏层定位已完成

Artifacts / 文件：

- `scripts/run_e131_e119_e146_hidden_localization.py`.
- `scripts/launch_e131_e119_e146_hidden_localization_queue_20260430.sh`.
- `scripts/summarize_e131_hidden_localization.py`.
- `reports/E131_E119_E146_HIDDEN_LOCALIZATION_20260430.md`.
- `reports/E131_E119_E146_HIDDEN_LOCALIZATION_20260430.json`.
- `results/E131_e119_e146_hidden_localization/`.
- Status log: `logs/e131_e119_e146_hidden_localization_status_20260430.jsonl`; queue log: `logs/e131_e119_e146_hidden_localization_queue_20260430.log`.

Scope / 范围：

- Mode: `NG`, `thinking=false`, direct strict verifier replay. / 非 thinking 自然生成上的 strict verifier 重放。
- Inputs: official E119/E146 process labels; labels/error spans/gold answers are offline only. / 使用 E119/E146 官方过程标签；标签、错误 span 和答案只用于离线分析。
- Prompt leakage counters are 0 for Qwen, Gemma31, and Gemma26-A4B. / 三个模型 prompt 泄露计数均为 0。

Main facts / 主要事实：

- Qwen3.5-27B: strict-valid accept 15/15; repaired ACPI accept 4/133; best residual score separates strict-valid 1.105 from repaired -2.208. / Qwen 的 strict-valid 与 repaired ACPI 分离清楚。
- Gemma4-31B-it: strict-valid accept 30/30; repaired ACPI accept 42/112; repaired first-final prefixes are often accepted, but error/repair prefixes turn negative in Yes/No and residual/component projections. / Gemma31 的初始答案前缀常被接受，但错误/修复附近转负。
- Gemma4-26B-A4B-it: unrepaired ACPI accept 8/10 overall; the two unrepaired cases are rejected at detected-error-marker prefixes 0/2 but accepted at completion 2/2. This is the strongest current evidence for hidden process signal being overridden or diluted by later answer-coherent context. / Gemma26 两条未修复个案在错误附近被拒绝，但完成态又被接受，是“内部过程信号被后文答案自洽覆盖/稀释”的最强当前证据。
- Residual is the strongest readout, while MLP, token-mixer/attention-related, and norm outputs also move with prefix stage. / residual 最强，MLP、token-mixer/attention 相关输出和 norm 输出也随阶段移动。

Boundary / 边界：

- E131 is diagnostic/observational, not a full causal circuit proof. / E131 是诊断性证据，不是完整因果电路证明。
- Next causal step should use these same E119/E146 natural rows for activation steering/span patch, with separate controls for process validity vs confidence. / 下一步应在这些自然行上做 activation steering/span patch，并把过程有效性和置信度分开控制。

## 2026-04-30 Self-Verification Collision Audit + E132-E136 Plan / 自验证撞车审计与 E132-E136 计划

Artifact / 文件：

- `reports/SELF_VERIFICATION_COLLISION_AND_E132_E136_PLAN_20260430.md`.

Key literature conclusion / 关键文献结论：

- `Reasoning Models Know When They're Right` is a medium collision risk. It trains hidden-state probes on long-CoT reasoning chunks to predict intermediate answer correctness and uses thresholded probe confidence for early exit. / 这篇是中等撞车风险：它在 long-CoT reasoning chunk 上训练 hidden-state probe 预测中间答案正确性，并用阈值 early exit。
- Our novelty must not be “hidden states know correctness.” It should be ACPI process-validity risk, strict vs repair-aware policy, residual/MLP/token-mixer localization near error spans, confidence-matched false-positive controls, and hidden-triggered local checking in non-thinking. / 我们的新意不能写成 hidden state 知道正确性；应写成 ACPI 过程有效性风险、strict/repair-aware 口径、错误 span 附近组件定位、置信度匹配假阳性控制，以及 non-thinking 下 hidden 触发局部检查。

Approved next experiment design / 已同意的后续设计：

- E132 `Suspicious-but-valid controls`: add valid-but-suspicious traces with hesitation/checking/alternative valid route/unusual valid algebra. / 可疑但正确控制组。
- E133 `Confidence-matched process probe`: match/regress out confidence, entropy, length, task, marker count, answer visibility, and repair markers. / 置信度匹配过程探针。
- E134 `Trigger-window audit`: inspect model text around hidden-triggered suspicious points. / 可疑点窗口审计。
- E136 `Adaptive checking policy`: stage 1 post-hoc hidden trigger plus second-pass global/local check; stage 2 online semantic-boundary trigger. / 自适应检查策略。
- E135 `LoRA/RL source memo`: deferred but mandatory later; use small model organisms with LoRA/QLoRA then optional LoRA-GRPO/RL if 30B full checkpoint chains are unavailable. / LoRA/RL 来源实验暂缓但保留。

## 2026-04-30 E132-E134 Suspicious/Confidence Probe Completed / 可疑但正确与置信度匹配小探针已完成

Artifacts / 文件：

- `scripts/build_e132_suspicious_valid_controls.py`.
- `scripts/run_e132_e133_suspicious_confidence_probe.py`.
- `scripts/launch_e132_e133_probe_queue_20260430.sh`.
- `scripts/build_e134_trigger_window_audit.py`.
- `scripts/summarize_e132_e134_probe.py`.
- `data/processed/e132_suspicious_valid_controls_20260430.jsonl`.
- `data/processed/e134_trigger_window_audit_sheet_20260430.jsonl`.
- `reports/E132_E134_SUSPICIOUS_CONFIDENCE_PROBE_20260430.md`.
- `reports/E132_E134_SUSPICIOUS_CONFIDENCE_PROBE_20260430.json`.
- `results/E132_E133_suspicious_confidence_probe/`.
- Status log: `logs/e132_e133_probe_status_20260430.jsonl`; queue wrote `all_done` at `2026-04-30T18:01:14`.

Main facts / 主要事实：

- Dataset: E132 has 240 controlled rows; first probe used 60 rows per model, 12 per variant. / E132 共 240 条，本次每模型 60 条。
- Qwen3.5-27B: invalid trigger 12/12, valid trigger 2/48, suspicious-valid trigger 2/36; hidden AUC 1.000 while strict-confidence AUC 0.447. / Qwen hidden 信号明显不是纯置信度。
- Gemma4-31B-it: invalid trigger 12/12, valid trigger 0/48, suspicious-valid trigger 0/36; hidden AUC 1.000. / Gemma31 最干净。
- Gemma4-26B-A4B-it: invalid trigger 12/12, valid trigger 6/48, suspicious-valid trigger 5/36; hidden AUC 0.960. / Gemma26 仍能抓错，但误触发更多。
- Confidence matching: nearest-neighbor matched pairs give 12/12 hidden valid>invalid for all three models; distances are still nontrivial, so treat as probe evidence. / 置信度匹配对均 12/12，但仍是小探针证据。
- E134 exported 209 windows for audit. `suspicion_marker_end` is marker-only prefix control, not a deployment trigger. / E134 导出 209 个窗口；marker-only prefix 不当作部署触发。

Interpretation / 解释：

- The hidden process-risk signal is not a pure true-error detector, but on E132 it is much more aligned with actual process invalidity than superficial hesitation markers. / hidden 过程风险信号不是纯错误检测器，但比表层犹豫词更对齐真实过程无效。
- Gemma26 remains the main calibration boundary and should be highlighted rather than hidden. / Gemma26 是主要校准边界，应如实报告。

Next / 下一步：

- Expand E132 to more task types and natural suspicious-valid rows. / 扩大任务和自然可疑正确样本。
- Run stricter confidence-matched regression. / 做更严格置信度匹配回归。
- Use calibrated trigger points for E136 stage-1 adaptive checking. / 用校准触发点做 E136 第一阶段。

## 2026-04-30 E136 Suspicious-Confidence Adaptive Check Completed / 可疑-置信度自适应检查已完成

Artifacts / 文件：

- `scripts/run_e136_suspicious_confidence_adaptive_check.py`.
- `scripts/launch_e136_suspicious_confidence_adaptive_check_queue_20260430.sh`.
- `scripts/summarize_e136_suspicious_confidence_adaptive_check.py`.
- `reports/E136_SUSPICIOUS_CONFIDENCE_ADAPTIVE_CHECK_20260430.md`.
- `reports/E136_SUSPICIOUS_CONFIDENCE_ADAPTIVE_CHECK_20260430.json`.
- `results/E136_suspicious_confidence_adaptive_check/`.
- Status log: `logs/e136_suspicious_confidence_adaptive_check_status_20260430.jsonl`; queue wrote `all_done` at `2026-04-30T18:39:33`.

Scope / 范围：

- Mode: `NG`, `thinking=false`, stage-1 post-hoc policy simulation on E132/E133 controlled rows. / 非 thinking；第一阶段后验策略模拟。
- Each model uses 60 rows, 12 per variant. / 每模型 60 条，每变体 12 条。
- Prompts contain only problem, visible solution, and hidden-trigger-selected visible excerpt. Manual labels/gold/error spans are offline only. / prompt 不含人工标签、答案或错误 span。

Main facts / 主要事实：

- Qwen3.5-27B: hidden trigger selected 12/12 invalid and 2/48 valid. Plain base accepted 4/12 invalid; hidden-local accepted only 1/12 invalid while retaining 47/48 valid. / Qwen 支持 hidden-trigger 低成本局部检查。
- Gemma4-31B-it: hidden trigger selected 12/12 invalid and 0/48 valid. Plain base accepted 3/12 invalid; hidden-local accepted 2/12 invalid while retaining 48/48 valid. / Gemma31 触发最干净。
- Gemma4-26B-A4B-it: hidden trigger selected 12/12 invalid and 6/48 valid. Hidden-local accepted 5/12 invalid, worse than strict base 1/12, while retaining 48/48 valid. / Gemma26 暴露局部检查 prompt 的 repair-aware/语义误读边界。

Interpretation / 解释：

- E136 does not prove adaptive checking solves ACPI. It shows hidden process-risk can select high-risk traces at low call rate, but the second-pass objective/readout decides whether the selected risk becomes a correct rejection. / E136 不是“自适应检查已经解决 ACPI”；它说明 hidden 风险信号能低成本选中高风险样本，但二次检查能否拒绝还取决于 objective/readout。
- The next causal/mechanistic step is online generation-time hidden monitoring plus calibrated local-check prompts on natural E119/E146 repaired/unrepaired ACPI rows. / 下一步应做在线生成时 hidden 监控，并在自然 E119/E146 repaired/unrepaired 行上校准局部检查 prompt。

## 2026-04-30 E139 Check-Rationale Audit Completed / 二次检查解释审计已完成

Artifacts / 文件：

- `scripts/run_e139_check_rationale_audit.py`.
- `scripts/launch_e139_check_rationale_audit_queue_20260430.sh`.
- `scripts/summarize_e139_check_rationale_audit.py`.
- `reports/E139_CHECK_RATIONALE_AUDIT_20260430.md`.
- `reports/E139_CHECK_RATIONALE_AUDIT_20260430.json`.
- `results/E139_check_rationale_audit/`.
- Status log: `logs/e139_check_rationale_audit_status_20260430.jsonl`; queue wrote `all_done` at `2026-04-30T20:37:36`.

Scope / 范围：

- Per latest user instruction, E139 only audits rows where E136 base/check failed to reject strict-invalid traces. / 按最新指令，E139 只审计 E136 中 base/check 未成功拒绝 strict-invalid trace 的失败样本。
- Mode is `non-thinking` generated rationale audit. Thinking smoke hit max-token before final audit block, so thinking E139 is deferred. / 本轮是非 thinking 解释式审计；thinking 冒烟未能稳定输出最终审计块，暂缓。
- Prompt contains problem, visible trace, and optional hidden-selected visible excerpt; no manual label, gold answer, or error-span annotation is inserted. / prompt 只含题目、可见 trace 和可选 hidden 选中片段，不插入人工标签、答案或错误 span。

Main facts / 主要事实：

- Selected rows: Qwen 4, Gemma31 3, Gemma26-A4B 6; all are `percentage_base::repaired_strict_invalid`. / 被选样本分别为 4、3、6 条，全部是百分比基底 repaired strict-invalid。
- Across 26 global/local audit jobs, parse success was 26/26, wrong-step quotation was 26/26, strict accept was 0/26, repair-aware accept was 23/26. / 26 个审计任务中，解析成功 26/26，指出错步 26/26，strict 接受 0/26，repair-aware 接受 23/26。
- By model: Qwen strict 0/8 and repair-aware 5/8; Gemma31 strict 0/6 and repair-aware 6/6; Gemma26-A4B strict 0/12 and repair-aware 12/12. / 分模型数字如上。

Interpretation / 解释：

- E136 check failures are not simply “the verifier cannot see the wrong step.” E139 shows the models can quote or describe the wrong step, but then often decide that later correct arithmetic repaired/discarded it. / E136 的 check 失败不是简单的“verifier 看不见错步”；E139 显示模型能指出错步，但常认为后文正确计算已修复或丢弃错误。
- This strengthens the objective/readout mismatch claim: hidden risk triggers can select bad traces, but the second-pass verifier still needs the intended strict evaluation policy. / 这强化 objective/readout 错配主张：hidden 风险触发能选中坏 trace，但二次 verifier 仍必须使用目标 strict 评价口径。
- Explicit record / 明确记录：模型能指出错步，但很多时候会认为后文正确计算已经把错步修复/丢弃，所以按 repair-aware 口径继续接受。这把工作做得更 solid：hidden/local check 能选中高风险 trace，但二次 verifier 的 objective/readout 如果没有被严格约束，仍会把 CoT 当“可修复草稿”而不是“严格证明”。/ The model can identify the wrong step, but often treats later correct arithmetic as repairing or discarding it, then accepts under a repair-aware rubric. This strengthens the mechanism claim that the failure is in evidence-to-objective/readout use, not simply absence of process evidence.
- Boundary: E139 explains a narrow E136 failure cluster; it is not a natural prevalence estimate. Expand to more task families and natural repaired/unrepaired ACPI before broad claims. / 边界：E139 解释一个窄失败簇，不是自然发生率估计；广义 claim 前需要扩展任务族和自然样本。
- Proposed E139.5 / 建议 E139.5：run base/no-check and strengthened locate-only prompts on the same failure rows to ask whether the model can localize the wrong step before any repair-aware global decision is requested. / 在相同失败行上补 base/no-check 与加强版“只找错步”prompt，检验模型是否能在 repair-aware 全局判定前先定位错步。

## 2026-04-30 E139.5 Base Span Localization Format-Fixed Completed / 基线错步定位格式修复已完成

Artifacts / 文件：

- `scripts/run_e1395_base_span_localization.py`.
- `reports/E1395_BASE_SPAN_LOCALIZATION_FORMAT_FIXED_20260430.md`.
- `reports/E1395_BASE_SPAN_LOCALIZATION_FORMAT_FIXED_20260430.json`.
- Adopted results: `results/E1395_base_span_localization_format_fixed/`.
- Superseded/debug archive: `archive/e1395_format_debug_20260430/results/`.

Scope / 范围：

- Mode is non-thinking locate-only verification on the same E136 failure-selected rows plus matched valid controls. / 非 thinking；只定位错步；样本来自 E136 失败行和匹配正确控制组。
- Prompts contain only problem and visible candidate solution. Manual label, gold answer, and expected span are offline only. / prompt 不含人工标签、答案或错误 span。

Format fix / 格式修复：

- The first Gemma31 E139.5 output had a format artifact: it often gave a valid first block/JSON, then repeated `thought + same answer` until `max_new_tokens`. / 旧 Gemma31 输出有格式伪差：先给有效答案，然后重复到 token 上限。
- The script now stops at the first `</SPAN_AUDIT>` or first JSON closing brace and parses the first balanced JSON object. / 脚本已改为首个答案即停，并解析第一个完整 JSON。
- Adopted format-fixed runs have `parse_ok=1.0` and `hit_max=0.0` for all three models. / 三个采纳运行均解析成功且没有打满输出上限。

Main facts / 主要事实：

- Qwen3.5-27B: invalid span hit 11/12 = 0.917, valid false error 0/36. / Qwen 基本能直接圈出错步，正确控制组未误报。
- Gemma4-31B-it: invalid span hit 6/9 = 0.667, valid false error 0/27; catches en_zh and mixed but misses romanized_zh. / Gemma31 格式已解决，漏检集中在 romanized_zh。
- Gemma4-26B-A4B-it: invalid span hit 14/18 = 0.778, valid false error 3/54; misses mixed rows and falsely flags some romanized valid controls. / Gemma26 同时有漏检和少量误报。

Interpretation / 解释：

- E139.5 strengthens the evidence-to-objective/readout mismatch claim: models often can localize a wrong step before making a global judgment, so the failure is not simply “no process evidence.” / E139.5 强化证据到 objective/readout 错配主张：模型常能先定位错步，因此失败不是简单“没有过程证据”。
- Boundary: span localization is not an oracle and remains language-route sensitive. / 边界：错步定位不是 oracle，且受语言路径影响。

## 2026-04-30 E137-E140 Adaptive Natural Check Completed / 自然样本 hidden 触发与二次检查已完成

Artifacts / 文件：

- `reports/E137_E140_ADAPTIVE_NATURAL_CHECK_SYNTHESIS_20260430.md`
- `reports/E137_E140_ADAPTIVE_NATURAL_CHECK_SYNTHESIS_20260430.json`
- `scripts/run_e137_hidden_trigger_threshold_calibration.py`
- `scripts/run_e138_natural_hidden_trigger_check.py`
- `scripts/launch_e138_natural_hidden_trigger_check_queue_20260430.sh`
- `scripts/run_e140_natural_check_rationale_audit.py`
- `results/E137_hidden_trigger_threshold_calibration/`
- `results/E138_natural_hidden_trigger_check/`
- `results/E140_natural_check_rationale_audit/`
- E138 status log: `logs/e138_natural_hidden_trigger_check_status_20260430.jsonl`, with `all_done` at `2026-04-30T22:08:32`.

Scope / 范围：

- All runs are non-thinking (`thinking=false`). / 全部为非 thinking。
- E137 is offline threshold evaluation on E132/E133 controlled rows. / E137 是离线阈值评估。
- E138 uses natural E119/E146 final-correct rows and E131 diagnostic prefix availability. This is diagnostic, not deployable online monitoring. / E138 使用自然 final-correct 行和 E131 诊断前缀；这是诊断实验，不是可部署在线监控。
- E140 generates rationale audits for selected E138 rows, separating strict trace-as-proof and repair-aware final-surviving-proof decisions. / E140 对 E138 选中样本生成解释式审计，并区分 strict 与 repair-aware。

Main facts / 主要事实：

- E137 Qwen: threshold 0 catches 12/12 invalid with 2/48 valid false triggers; chosen threshold -5.170 has 0/48 valid false triggers but is too conservative on natural transfer. / Qwen 受控阈值干净但自然迁移过保守。
- E137 Gemma31: threshold 0 catches 12/12 invalid with 0/48 valid false triggers. / Gemma31 最干净。
- E137 Gemma26: threshold 0 catches 12/12 invalid but has 6/48 valid false triggers; no threshold satisfies strict FP constraints. / Gemma26 误触发较高。
- E138 Qwen: 19 repaired ACPI; base invalid accept 2/19; zero hidden trigger covers all 19; zero strict-local reduces invalid accept to 0/19 while keeping valid accept 5/5. / Qwen 的自然 repaired ACPI 支持 hidden 触发和 strict 局部检查。
- E138 Gemma31: 16 repaired ACPI; base invalid accept 6/16; zero trigger covers all 16; strict-local reduces invalid accept to 2/16. Default-local is more repair-aware and worse. / Gemma31 也支持，但 default/local 会变宽。
- E138 Gemma26: 8 repaired + 2 unrepaired ACPI; base invalid accept 6/10; zero trigger covers all invalid rows, but strict-local still accepts 5/10 invalid and both unrepaired rows. / Gemma26 是边界：hidden 触发不等于正确拒绝。
- E140 Qwen: error recognized 8/8, strict accept 0/8, repair-aware accept 5/8. / Qwen 能看见错，但 repair-aware 仍接受。
- E140 Gemma31: error recognized 8/20, strict accept 12/20, repair-aware accept 20/20. / Gemma31 常没指出错，且 repair-aware 全接受。
- E140 Gemma26: error recognized 2/20, strict accept 15/20, repair-aware accept 19/20; unrepaired ACPI rows have error recognized 0/4 and strict accept 4/4. / Gemma26 未修复两例完全漏检并接受。

Interpretation / 解释：

- For Qwen/Gemma31, natural repaired ACPI often has a hidden process-risk signal, and strict second-pass checking can use it. / 对 Qwen/Gemma31，自然 repaired ACPI 常有 hidden 风险信号，strict 二次检查能利用。
- The same hidden trigger can fail to become a correct decision when the second checker reads CoT as a repairable draft or lacks local semantic competence. / 如果二次检查把 CoT 当可修复草稿，或局部语义能力不足，hidden 触发也不一定变成正确拒绝。
- Gemma26 unrepaired ACPI is the most important negative case for the next stage. It prevents overclaiming and motivates activation/prompt deep dives. / Gemma26 未修复 ACPI 是下一阶段最重要反例，提醒不能过度声称。

Immediate next / 直接下一步：

- E141: taxonomy of E140 rationales; no GPU needed. / 对 E140 解释文本做失败分类。
- E142: online trigger scaffold without label-informed prefixes. / 去掉离线错误 span 的在线触发脚手架。
- E144: caution-token intervention for low-cost non-thinking adaptive checking. / 警示 token 干预。
- Gemma26 unrepaired deep dive: distinguish threshold/readout/semantic-local-competence failure. / 深挖 Gemma26 未修复失败来源。
