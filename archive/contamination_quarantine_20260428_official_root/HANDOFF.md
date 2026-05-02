# Handoff R6 / 交接说明 R6

Date / 日期: 2026-04-27 CST  
Project / 项目目录: `/home/Awei/P02_multilingual_process_lens`

## Active Memory / 当前项目记忆

- Current history / 当前 history: `docs/HISTORY_KG_20260427_R6.md`
- Current index / 当前索引: `docs/CURRENT_PROJECT_INDEX_20260427.md`
- Main S6 report / S6 主报告: `reports/S6_INTEGRATED_SCIENTIFIC_ANALYSIS_AND_NEXT_PLAN_20260427.md`
- S6 literature review / S6 文献复核: `docs/LITERATURE_S6_POST_GRID_COLLISION_REVIEW_20260427.md`
- S7 task/verifier survey / S7 任务与 verifier 管线调研: `docs/S7_TASK_AND_VERIFIER_PIPELINE_SURVEY_20260427.md`
- E30/E31 non-discount reports / E30/E31 非折扣报告: `reports/E30_non_discount_lexical_grid_audit.md`, `reports/E31_non_discount_counterfactual_summary.md`
- Archive index / 归档索引: `archive/README.md`

Old status snapshots are archived under / 旧状态快照已归档到：

- `archive/project_status_20260427_pre_R4/`
- `archive/project_status_20260427_pre_R5/`
- `archive/project_status_20260427_pre_R6/`

## Environment / 环境

```bash
cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
```

For Qwen3.5-27B multi-GPU loading / Qwen3.5-27B 多卡加载：

```bash
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
# use --device auto / 使用 --device auto
```

## Latest Results / 最新结果

- Lexical grid audit / 词汇网格审计: `reports/S6_lexical_paraphrase_grid_audit.md`
- Integrated metrics / 综合指标: `results/S6_integrated_analysis/s6_integrated_metrics.json`
- Absolute verifier results / 绝对 verifier 结果: `results/S6_lexical_grid_absolute_verifier/`, `results/S6_lexical_grid_absolute_verifier_qwen27/`
- Contrastive verifier results / 对比 verifier 结果: `results/S6_lexical_grid_contrastive_verifier/`, `results/S6_lexical_grid_contrastive_verifier_qwen27/`
- Span patch summary / span patch 汇总: `reports/S6_lexical_grid_span_patch_summary.md`
- Layerwise lens summary / 分层 lens 汇总: `reports/S6_lexical_grid_layerwise_lens_summary.md`
- E28 counterfactual/answer masking / E28 反事实与答案遮蔽: `reports/E28_counterfactual_answer_masking_summary.md`
- E29 error-span extraction verifier / E29 错误 span 抽取 verifier: `reports/E29_error_span_extraction_verifier_summary.md`
- E30 non-discount natural grid audit / E30 自然非折扣网格审计: `reports/E30_non_discount_lexical_grid_audit.md`
- E30 non-discount verifier and span patch / E30 非折扣 verifier 与 span patch: `reports/E30_non_discount_verifier_summary.md`, `reports/E30_non_discount_span_patch_summary.md`
- E31 controlled non-discount counterfactual / E31 受控非折扣反事实: `reports/E31_non_discount_counterfactual_summary.md`
- E31 non-discount error-span extraction / E31 非折扣错误 span 抽取: `reports/E31_non_discount_error_span_summary.md`

## Key Scientific Facts / 关键科学事实

- S6 generated 192 lexical-grid rows. Gemma4 produced 2 paper-grade ACPI rows; Qwen14 produced 1 paper-grade ACPI row. / S6 生成 192 行词汇网格；Gemma4 产生 2 条论文级 ACPI；Qwen14 产生 1 条论文级 ACPI。
- The ACPI rows are concrete surface-semantic flips: `打八折=pay80` confused with `pay75`, `打八折/pay80` translated as `80% discount/pay20`, and `sold for 75%` translated as `75% discount`. / ACPI 行是具体表层语义翻转。
- Absolute process verifiers over-accept selected S6 ACPI: Gemma4, Qwen14, and Qwen3.5-27B have ACPI false-accept rate 1.0 in both English and Chinese prompts. / 绝对式过程 verifier 对选择后的 S6 ACPI 过度接受：Gemma4、Qwen14、Qwen3.5-27B 中英提示误接受率均为 1.0。
- Contrastive sibling verification helps Qwen-family models on some pairs but is not universal; Gemma4 predicts A on 12/12 S6 contrastive rows, and Qwen3.5-27B predicts A on 10/12. / 对比式 sibling 对 Qwen 系部分有效但不万能；Gemma4 在 12/12 行选 A，Qwen3.5-27B 在 10/12 行选 A。
- S6 hidden-span patch gives a strong Qwen14 causal signal: support/error span L14 has `valid->bad +2.750` and `bad->valid -1.000`. / S6 hidden-span patch 给出强 Qwen14 因果信号：support/error span L14 为 `valid->bad +2.750` 与 `bad->valid -1.000`。
- E28 showed text-level causal evidence: swapping only the invalid lexical phrase almost always lowers the Yes-minus-No verifier margin, but the final binary decision often still accepts. / E28 给出文本层因果证据：只替换无效词汇短语几乎总会降低 Yes-minus-No verifier 边际，但最终二值决策仍常接受。
- E29 showed that span-extraction prompts are diagnostic but noisy: `75% discount` is easier to expose, while `打八折=支付75%` remains hard. / E29 显示错误 span 抽取提示有诊断价值但噪声大：`75% discount` 更容易暴露，`打八折=支付75%` 仍难。
- E30 broadened beyond discount. Clean natural non-discount ACPI was rare in the first pass: only one paper-grade Qwen14 inequality-boundary row was promoted. / E30 扩展到折扣之外；第一轮干净自然非折扣 ACPI 很少，只提升 1 条论文级 Qwen14 边界量词样例。
- E30's one non-discount ACPI row was still accepted by all four absolute verifiers in English and Chinese prompts. / E30 的这一条非折扣 ACPI 仍被四个绝对式 verifier 在中英提示下全部接受。
- E31 controlled five non-discount traps and showed the phenomenon is not discount-only: Gemma4 and Qwen3.5-27B heavily over-accept answer-correct process-invalid rows, while Qwen14 is stricter. / E31 控制了 5 类非折扣陷阱，说明现象不只属于折扣：Gemma4 与 Qwen3.5-27B 对答案正确但过程错误的行明显过度接受，而 Qwen14 更严格。
- E31 error-span extraction shows objective dependence: Qwen3.5-27B locate-then-judge rejects most invalid non-discount rows, even though its absolute process-only prompt over-accepts many ACPI rows. / E31 错误 span 抽取显示目标依赖：Qwen3.5-27B 的“先定位再判断”会拒绝多数非折扣无效行，但它的绝对式只审过程提示会过度接受许多 ACPI 行。

## Current Claim / 当前主张

The safest novelty claim is not generic “CoT is wrong” or “correct answers can hide wrong processes.” The safest claim is the conjunction: multilingual lexical surface forms create selected real ACPI traces; absolute verifier objectives over-accept them; controlled non-discount traps show the same risk can be induced outside discount wording; sibling comparison and hidden support/error-span interventions expose process signals in some robust pairs; hard tasks, natural prevalence, position bias, and prompt-template failures define boundaries. / 最安全创新点不是泛泛说“CoT 会错”或“正确答案会掩盖错误过程”，而是这个组合：多语言词汇表层形式产生选择后的真实 ACPI；绝对式 verifier 目标会过度接受；受控非折扣陷阱说明这种风险能在折扣表述之外被诱发；sibling 对比和 hidden support/error-span 干预在部分稳健 pair 上暴露过程信号；难题、自然发生率、位置偏差和提示模板失败构成边界。

## Next Best Stage / 下一最佳阶段

1. Mechanism first / 机制优先：decompose the robust S6 Qwen14 `pay75` L14 span into attention-head, MLP, and optional SAE/transcoder features; E30 inequality is a boundary control, not the main mechanism anchor. / 优先分解稳健的 S6 Qwen14 `pay75` L14 span 到 head、MLP 与可选 SAE/transcoder；E30 不等式是边界控，不是主机制锚点。
2. Natural pair expansion / 自然 pair 扩展：do targeted natural generation around lexical families with two common operational meanings and numerically survivable final answers; do not claim broad non-discount prevalence yet. / 围绕“两个常见操作含义且最终数字能幸存”的词汇族做定向自然生成；暂不声称非折扣广泛发生。
3. Verifier objective matrix / verifier 目标矩阵：compare absolute Yes/No, contrastive, locate-only, locate-then-judge, answer-masked, and calibrated-margin objectives on the same sibling rows. / 在同一批 sibling 上比较绝对 Yes/No、对比式、仅定位、定位后判断、答案遮蔽和边际校准目标。
4. Hard-task final-correct conditioning / 难题 final-correct 条件化：for AIME24/25, first obtain final-correct traces with Qwen3.5-27B/Gemma4 plus verifier-guided sampling, then audit process validity. / 对 AIME24/25，先用 Qwen3.5-27B/Gemma4 与 verifier-guided sampling 获得 final-correct trace，再审计过程。
5. Paper framing / 论文表述：separate natural prevalence from controlled possibility, and present E30 as a boundary that makes the claim more credible rather than weaker. / 区分自然发生率与受控可行性，把 E30 作为让主张更可信的边界而非削弱。

## Validation / 验证

Run after R6 updates / R6 更新后运行：

```bash
python -m py_compile scripts/audit_s6_lexical_grid.py scripts/run_trace_pool_generate.py scripts/run_manual_trace_verifier.py scripts/run_contrastive_acpi_verifier_smoke.py scripts/run_real_acpi_span_patch_smoke.py scripts/run_layerwise_verifier_lens.py
python -m py_compile scripts/build_e28_counterfactual_answer_masking.py scripts/run_error_span_extraction_verifier.py scripts/summarize_e28_counterfactual_answer_masking.py scripts/summarize_e29_error_span_extraction_verifier.py
python -m py_compile scripts/audit_e30_non_discount_grid.py scripts/summarize_e30_non_discount_verifier.py scripts/build_e31_non_discount_counterfactual.py scripts/summarize_e31_non_discount_counterfactual.py
python scripts/check_project.py
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
tmux ls 2>/dev/null || true
```

## R6 Validation Result / R6 验证结果

R6 validation passed on 2026-04-27. / R6 验证已在 2026-04-27 通过。

- Python compile passed for the S6 scripts. / S6 脚本通过 Python 编译检查。
- Shell syntax passed for the S6 launch scripts. / S6 启动脚本通过 shell 语法检查。
- `scripts/check_project.py` passed in `passage_prep_py312`. / `passage_prep_py312` 环境下 `scripts/check_project.py` 通过。
- GPUs are idle and completed tmux sessions were closed. / GPU 空闲，已关闭完成的 tmux 会话。

## S7/E28/E29 Validation Result / S7/E28/E29 验证结果

Validation passed on 2026-04-27 after E28/E29. / E28/E29 后已在 2026-04-27 通过验证。

- `python -m py_compile` passed for new E28/E29 scripts. / 新 E28/E29 脚本通过 Python 编译检查。
- `python scripts/check_project.py` passed; log is `logs/check_project_s7_e28_e29_20260427.json`. / `python scripts/check_project.py` 通过；日志为 `logs/check_project_s7_e28_e29_20260427.json`。
- GPUs are idle: GPU0 17 MiB, GPU1 2 MiB, GPU2 2 MiB, GPU3 2 MiB. / GPU 空闲：GPU0 17 MiB，GPU1 2 MiB，GPU2 2 MiB，GPU3 2 MiB。

## E30/E31 Validation Result / E30/E31 验证结果

Validation passed on 2026-04-27 after E30/E31. / E30/E31 后已在 2026-04-27 通过验证。

- `python -m py_compile` passed for new E30/E31 scripts and span-extraction summarization. / 新 E30/E31 脚本与 span 抽取汇总通过 Python 编译检查。
- `python scripts/check_project.py` passed; log is `logs/check_project_e30_e31_20260427.json`. / `python scripts/check_project.py` 通过；日志为 `logs/check_project_e30_e31_20260427.json`。
- E31 integrity audit passed; log is `logs/e31_integrity_audit_20260427.txt`. / E31 完整性审计通过；日志为 `logs/e31_integrity_audit_20260427.txt`。
- GPUs are idle: GPU0 17 MiB, GPU1 2 MiB, GPU2 2 MiB, GPU3 2 MiB. / GPU 空闲：GPU0 17 MiB，GPU1 2 MiB，GPU2 2 MiB，GPU3 2 MiB。

## E32 Gemma4 Medium Four-GPU Update / E32 Gemma4 中型模型四卡更新

- Stage report / 阶段报告: `reports/E32_gemma4_medium_4gpu_status_20260427.md`.
- No stuck training was observed / 没有观察到训练卡死：at 2026-04-27 22:07-22:16 CST GPUs were idle and the active process was the `gemma4_31b_it` download, not training. / 2026-04-27 22:07-22:16 CST GPU 空闲，运行的是 `gemma4_31b_it` 下载，不是训练。
- `gemma4_31b_it` download is progressing / `gemma4_31b_it` 下载在推进：directory grew from about 11 GB to 17 GB during monitoring. / 监控期间目录从约 11 GB 增至 17 GB。
- Unified runner / 统一运行器: `scripts/launch_blackbox_4gpu_suite.sh` uses `MPLENS_BACKEND=auto|vllm|hf`; default auto uses vLLM where supported and HF four-GPU `device_map=auto` for Gemma4. / `scripts/launch_blackbox_4gpu_suite.sh` 支持 `MPLENS_BACKEND=auto|vllm|hf`；默认自动选择，Gemma4 走 HF 四卡。
- Important boundary / 重要边界：do not force all models through vLLM. `gemma4_26b_a4b_it` fails in vLLM 0.12.0 because the fallback loader cannot match `layer_scalar`, but HF four-GPU loading works. / 不要强制所有模型走 vLLM；Gemma4-26B-A4B 当前 vLLM 加载失败，但 HF 四卡可跑。
- Completed / 已完成：`gemma4_26b_a4b_it` S6/E28/E30/E31 absolute verifier core suite. Outputs are under `results/S6_lexical_grid_absolute_verifier_hf/`, `results/E28_counterfactual_answer_masking_absolute_verifier_hf/`, `results/E30_non_discount_absolute_verifier_hf/`, and `results/E31_non_discount_counterfactual_absolute_verifier_hf/`. / 已完成 26B-A4B 的 S6/E28/E30/E31 绝对式 verifier 核心套件。
- Key 26B fact / 26B 关键事实：S6 process-only ACPI false accept is 1.000/1.000 en/zh; E30 process-only ACPI false accept is 1.000/1.000; E31 process-only ACPI false accept is 0.800/0.800. / 26B-A4B 对 S6、E30、E31 的 ACPI 仍明显过度接受。
- Current tmux / 当前 tmux：`gemma31_postdownload` waits for download PID `756393` and then runs `scripts/launch_blackbox_4gpu_suite.sh gemma4_31b_it core`. Log: `logs/gemma4_31b_it_postdownload_hf4gpu_suite_driver.log`. / `gemma31_postdownload` 会等待下载完成后自动跑 31B 核心套件。

## E33 S6 Qwen14 Mechanism Deep Dive / E33 S6 Qwen14 机制深挖

- Report / 报告: `reports/E33_s6_qwen14_mechanism_deep_dive_20260427.md`.
- Dense residual patch / dense residual patch: `results/S6_lexical_grid_span_patch_dense/qwen3_14b_base_real_acpi_span_patch.json`. The support/error span signal forms a middle-layer band: L12-L14 reach `valid->bad +2.750` and `bad->valid -1.000`; late layers decay to near zero. / support/error span 信号形成中层带：L12-L14 达到 `valid->bad +2.750`、`bad->valid -1.000`；后层接近 0。
- Module patch / module patch: `results/S6_lexical_grid_module_patch/qwen3_14b_base_real_acpi_module_patch.json`. Best clean module is L14 MLP on support/error span, `+0.375/-0.125`; attention has weaker clean effects. / 最强干净 module 是 L14 MLP 的 support/error span，`+0.375/-0.125`；attention 较弱。
- Head patch / head patch: `results/S6_lexical_grid_attention_head_patch/qwen3_14b_base_real_acpi_attention_head_patch.json`. L9/L14/L20 pre-o_proj scan finds no dominant single head; best head is only `+0.125/-0.125`. / 单头扫描没有主导 head；最强只有 `+0.125/-0.125`。
- Interpretation / 解释: process evidence is a distributed middle residual-state signal with MLP participation, not a single-head circuit. This supports objective/threshold/output re-entanglement rather than pure blindness. / 过程证据是分布式中层残差信号并有 MLP 参与，不是单头 circuit；支持目标/阈值/输出重整错配，而不是纯看不见。
- New script / 新脚本: `scripts/run_real_acpi_attention_head_patch.py`. `scripts/run_real_acpi_module_patch_smoke.py` now supports both `e05_idx` and `audit_idx`. / 新增单头 patch 脚本；module patch 脚本支持 `e05_idx` 与 `audit_idx`。

## E34 E31 Non-Discount Mechanism Generalization / E34 E31 非折扣机制泛化

- Report / 报告: `reports/E34_e31_non_discount_mechanism_generalization_20260427.md`.
- Pair configs / pair 配置: `configs/e31_non_discount_span_patch_pairs.yaml`, `configs/e31_non_discount_span_patch_pairs_qwen35_9b.yaml`.
- Qwen14 result / Qwen14 结果: `results/E34_e31_non_discount_span_patch_dense/qwen3_14b_base_real_acpi_span_patch.json`. 4/5 traps have strong clean residual span-patch signals; inequality is the weak/over-accepted boundary. / 4/5 类陷阱有强干净 residual span-patch 信号；不等式是弱且被过度接受的边界。
- Qwen3.5-9B result / Qwen3.5-9B 结果: `results/E34_e31_non_discount_span_patch_dense/qwen35_9b_real_acpi_span_patch.json`. The model over-accepts geometry and combinatorics bad traces but still has strong patchable hidden signals (`geometry +0.500/-3.000`, `combinatorics +2.250/-3.438`). / 模型会过度接受几何和组合 bad trace，但 hidden 信号仍可被 patch 暴露。
- Scientific update / 科学更新: hidden process/error-span signals generalize beyond discount, but are graded and task-dependent. Inequality boundary remains a key weak point where hidden signal is weaker and verifier acceptance is higher. / hidden process/error-span 信号能泛化到折扣之外，但强度随任务变化；不等式边界仍是关键信号弱点。

## E35 E31 Qwen3.5-9B Module Patch / E35 E31 Qwen3.5-9B 模块分解

- Report / 报告: `reports/E35_e31_qwen35_module_patch_20260427.md`.
- Result / 结果: `results/E35_e31_non_discount_module_patch/qwen35_9b_real_acpi_module_patch.json`.
- Script update / 脚本更新: `scripts/run_real_acpi_module_patch_smoke.py` supports `linear_attn` in addition to `self_attn` and `mlp`. / module patch 脚本现在支持 `linear_attn`。
- Key fact / 关键事实: single-module effects are much smaller than residual patch effects. Strongest module is ratio L0 `linear_attn` at `+1.500/-0.125`; geometry best MLP is only `+0.312/-0.062`; combinatorics has weak linear-attn/MLP effects. / 单模块效应明显小于 residual patch；最强是比例 L0 `linear_attn`，几何和组合模块效应较弱。
- Interpretation / 解释: Qwen3.5-9B E31 process evidence is distributed across early/middle residual stream with linear-attention and MLP participation, not a single module/head circuit. / Qwen3.5-9B 的 E31 过程证据是早/中层 residual stream 的分布式信号，不是单模块/单头 circuit。

## E36/E37 Queued Mechanism Experiments / E36/E37 已排队机制实验

- Report / 报告: `reports/E36_E37_queued_next_mechanism_20260427.md`.
- New config / 新配置: `configs/e36_inequality_boundary_span_variants.yaml`.
- New summarizer / 新汇总脚本: `scripts/summarize_e36_inequality_boundary.py`.
- Queue / 队列: tmux session `e36_e37_after_gemma31` waits for `gemma31_postdownload` to end, then runs E36 residual span variants and E37 layerwise lens. / `e36_e37_after_gemma31` 会等待 `gemma31_postdownload` 结束，再运行 E36 residual span 变体与 E37 分层 lens。
- Scientific purpose / 科学目的: explain the E31 inequality boundary: the bad trace has wrong local wording (`between 3 and 7, inclusive`) but immediately lists the correct integers (`4, 5, 6, 7`). / 科学目的：解释 E31 不等式边界为何“局部错但整体容易被接受”。
- Check status / 检查状态: `tmux ls`, `tail -80 logs/gemma4_31b_it_postdownload_hf4gpu_suite_driver.log`, and `tail -80 logs/E36_E37_after_gemma31_driver.log`. / 检查状态可看这三个命令。

## E38 Gemma4-31B And E36/E37 Completion / E38 Gemma4-31B 与 E36/E37 完成

- Report / 报告: `reports/E38_gemma31_e36_e37_synthesis_20260427.md`.
- Download status / 下载状态: `gemma4_31b_it` is complete; two safetensor shards exist and no `*.incomplete` file remains. / `gemma4_31b_it` 已完整下载；两个 safetensor 分片齐全，没有 `*.incomplete`。
- Four-GPU suite / 四卡套件: completed S6/E28/E30/E31 under HF fallback, with outputs under `results/*_absolute_verifier_hf/gemma4_31b_it_manual_trace_verifier.json`. / HF fallback 四卡已完成 S6/E28/E30/E31。
- Gemma31 key fact / Gemma31 关键事实: S6, E28, and E30 ACPI false accept remain `1.000/1.000`; E31 controlled non-discount ACPI false accept drops to `0.400/0.600` en/zh. / S6、E28、E30 仍全接受；E31 降到英文 0.400、中文 0.600。
- E36 key fact / E36 关键事实: inequality boundary has hidden evidence, but it is mixed with downstream correction; Qwen3.5-9B is clean on 5/5 span variants, Qwen14 on 3/5. / 不等式边界有隐藏证据，但和后续修正混在一起；Qwen3.5-9B 五个变体都干净，Qwen14 三个干净。
- E37 key fact / E37 关键事实: Qwen14 ACPI middle-positive rate is `1.000` but final-positive rate is `0.500`, supporting middle evidence loss/output re-entanglement. / Qwen14 的 ACPI 中层正向率为 1.000，但最终正向率为 0.500，支持中层证据在输出端丢失或再纠缠。
- Validation / 验证: `logs/check_project_e36_e37_20260427.json` passed; no tmux jobs remained and GPUs were idle at the final check. / 验证通过；最终检查时没有 tmux 任务，GPU 空闲。

Final E38 validation / E38 最终验证: `logs/check_project_e38_final_20260427.json`; no tmux jobs running and GPUs idle. / 最终验证日志为 `logs/check_project_e38_final_20260427.json`；无 tmux 任务，GPU 空闲。

## E39-E42 Latest Update / E39-E42 最新更新

Latest reports / 最新报告：

- `reports/E39_surface_semantic_generalization_summary_20260428.md` / E39 表层语义泛化。
- `reports/E40_surface_semantic_span_patch_summary_20260428.md` / E40 表层语义 residual span patch。
- `reports/E41_surface_semantic_module_patch_summary_20260428.md` / E41 模块 patch。
- `reports/E42_e39_objective_matrix_summary_20260428.md` / E42 E39 目标矩阵。
- `reports/E43_next_stage_mechanism_and_generalization_plan_20260428.md` / E43 下一阶段机制与泛化计划。

Key facts / 关键事实：

- E39 adds 12 controlled surface-semantic families beyond discount and E31. / E39 在折扣和 E31 之外新增 12 类受控表层语义族。
- E39 process-only ACPI false accept: Qwen35-27B `1.000/0.833`, Qwen35-9B `0.750/0.833`, Qwen14 `0.250/0.250`, Gemma31 `0.500/0.417` EN/ZH. / E39 只审过程 ACPI 误接受如上。
- E40 residual hidden evidence generalizes: Qwen35-9B clean `11/12`; Qwen14 clean `10/12`. / E40 residual 隐藏证据泛化：Qwen35-9B 11/12，Qwen14 10/12。
- E41 shows MLP participation but not a single-module circuit; module effects are much smaller than residual effects. / E41 显示 MLP 参与，但不是单模块 circuit。
- E42 contrastive objective strongly exposes invalid siblings: Qwen35-27B `1.000`, Qwen35-9B `0.979`, Qwen14 `0.958`, Gemma31 `0.875` overall accuracy. / E42 对比式强力暴露 invalid sibling。
- E42 calibrated margin fact: all four models usually lower Yes-No margins for invalid phrases, but absolute Yes/No still accepts many ACPI rows. / E42 连续边际显示模型有证据，但绝对式 Yes/No 仍过度接受。

Newest data/results / 最新数据结果：

- E42 focus set: `data/processed/e42_e39_objective_focus_20260428.jsonl`. / E42 focus 数据。
- E42 pairs: `configs/e42_e39_objective_pairs.yaml`. / E42 sibling 配置。
- E42 contrastive results: `results/E42_e39_objective_matrix_contrastive/`. / E42 对比式结果。
- E42 error-span results: `results/E42_e39_objective_matrix_error_span/`. / E42 错误 span 结果。
- E42 summary JSON: `results/E42_e39_objective_matrix_summary/summary.json`. / E42 汇总 JSON。

Newest scripts / 最新脚本：

- `scripts/build_e42_e39_objective_focus.py` / 构造 E42 focus set。
- `scripts/run_e42_contrastive_objective.py` / 运行 E42 sibling 对比。
- `scripts/summarize_e42_objective_matrix.py` / 汇总 E42 目标矩阵。
- `scripts/audit_e42_objective_matrix.py` / 审计 E42 数据与结果。

Validation / 验证：

- `logs/audit_e42_objective_matrix_20260428.json` passed. / E42 审计通过。
- `logs/check_project_e42_objective_matrix_20260428.json` passed. / 项目检查通过。
- GPUs were idle after E42: GPU0 17 MiB, GPU1 2 MiB, GPU2 2 MiB, GPU3 2 MiB. / E42 后 GPU 空闲。

Next best work / 下一最佳工作：

1. E43 paraphrase-transfer hidden patch: distinguish semantic process evidence from lexical-token artifact. / E43 跨改写 hidden patch，用来区分过程语义信号和词面 artifact。
2. E44 MLP direction steering with leave-one-family-out controls. / E44 用留一族控制做 MLP 方向 steering。
3. E46 natural harvesting over E39 families with Qwen35-27B/Gemma31, then manual process audit. / E46 用 Qwen35-27B/Gemma31 做 E39 家族自然挖掘并人工审计。
4. E47 AIME24/25 final-correct conditioning before ACPI audit. / E47 在 AIME24/25 上先拿到答案正确 trace，再审 ACPI。

## Evaluation Setting Audit 2026-04-28 / 评估设置审计 2026-04-28

Latest appendix / 最新附录：`reports/APPENDIX_EVAL_SETTING_AUDIT_20260428.md`.

What changed / 变更：

- Added machine audit `scripts/audit_eval_settings_appendix.py`; it passed and wrote `logs/audit_eval_settings_appendix_20260428.json`. / 新增机器审计脚本，已通过并写入日志。
- Fixed `scripts/run_real_acpi_span_patch_smoke.py` so official chat-template prompts are tokenized with `add_special_tokens=False`; raw prompts still use `add_special_tokens=True`. / 修正 hidden patch 脚本，官方 chat 模板渲染后不再重复加 special token；raw prompt 仍加 special token。
- Updated Qwen35-9B layer configs in `configs/e39_surface_semantic_pairs_qwen35_9b.yaml` and `configs/e31_non_discount_span_patch_pairs_qwen35_9b.yaml` to valid 32-layer IDs `[0, 4, 8, 12, 14, 16, 20, 24, 28, 31]`. / 更新 Qwen35-9B 层配置为合法层号。
- Reran Qwen35-9B official-template E40 hidden patch: `results/E40_official_template_span_patch/qwen35_9b_real_acpi_span_patch.json`; summary: `reports/E40_official_template_span_patch_summary_20260428.md`. / 已复跑官方模板 E40 hidden patch。
- Project check passed: `logs/check_project_eval_audit_20260428.json`. / 项目检查通过。

Important interpretation / 重要解释：historical raw prompts are not invalid, but they must be reported as a raw-prompt stress-test family. For chat/post-trained models, future main E43-E47 runs should use `official_if_chat`; base models remain raw. / 历史 raw prompt 并非无效，但必须作为 raw-prompt 压力测试报告。后续 chat/post-trained 模型主实验默认 `official_if_chat`，base 模型仍用 raw。

Next work after audit / 审计后的下一步：start the four planned experiments: E43 paraphrase-transfer hidden patch, E44 leave-one-family-out MLP direction steering, E46 natural harvesting, and E47 AIME/hard-task final-correct conditioning. / 接下来启动四个规划实验：E43 跨改写 hidden patch、E44 留一族 MLP 方向 steering、E46 自然挖掘、E47 AIME/难题答案正确条件化。

## E43-E47 Pilot Results 2026-04-28 / E43-E47 pilot 结果 2026-04-28

Report / 报告：`reports/E43_E47_next_experiments_summary_20260428.md`.

Artifacts / 产物：

- E43 data/config: `data/processed/e43_paraphrase_transfer_20260428.jsonl`, `configs/e43_paraphrase_transfer_pairs.yaml`. / E43 数据与配置。
- E43 results: `results/E43_paraphrase_transfer_patch/qwen35_9b_e43_paraphrase_transfer_chat.json`, `results/E43_paraphrase_transfer_patch/qwen3_14b_base_e43_paraphrase_transfer_raw.json`. / E43 结果。
- E44 results: `results/E44_mlp_direction_steering/qwen35_9b_e44_mlp_direction_steering_chat.json`, `results/E44_mlp_direction_steering/qwen3_14b_base_e44_mlp_direction_steering_raw.json`. / E44 结果。
- E46/E47 generation: `results/E46_E47_conditioned_generation/`. / E46/E47 生成与过滤结果。
- Integrity audit: `logs/audit_e43_e47_next_experiments_20260428.json`, passed. / 完整性审计已通过。

Key facts / 关键事实：

- E43: same-family cross-paraphrase transfer is clean (`12/12`) for both Qwen35-9B and Qwen14, but mismatched-family controls are also strong. / 同家族跨改写迁移强，但错配家族也强。
- E44: naive leave-one-family-out MLP direction steering is weak; Qwen35-9B has a small advantage over controls, Qwen14 does not. / 朴素 MLP 方向 steering 弱。
- E46: neutral natural generation pilot finds no ACPI candidates: Qwen35-27B `8/12` final-correct, 0 ACPI; Gemma31 `5/6` final-correct, 0 ACPI. / 中性自然生成 pilot 无 ACPI 候选。
- E47: Qwen35-27B AIME pilot has `0/6` final-correct traces, so ACPI cannot be estimated. / AIME pilot 无答案正确 trace。

Next recommended work / 建议下一步：larger E46 with varied ambiguity-inviting prompts that do not leak the known error span; E44 replacement with residual/subspace steering and fixed-layer controls; E47 higher sampling budget/longer generation or stronger model to obtain final-correct hard traces. / 下一步应扩大 E46、改进 E44 为 residual/subspace steering，并提高 E47 采样预算或换更强模型。
