# Handoff / 交接说明

Date / 日期: 2026-04-27 CST
Project / 项目目录: `/home/Awei/P02_multilingual_process_lens`

## Active Memory / 当前项目记忆

- Current history / 当前 history: `docs/HISTORY_KG_20260427_R5.md`
- Main literature review / 主文献复核: `docs/LITERATURE_AND_NOVELTY_REVIEW_20260427.md`
- S4 mechanism/hard-task review / S4 机制与难题复核: `docs/LITERATURE_S4_MECHANISM_HARD_TASKS_20260427.md`
- S5 additional collision review / S5 追加撞车复核: `docs/LITERATURE_S5_ADDITIONAL_COLLISION_REVIEW_20260427.md`
- Scientific communication memo / 科研沟通备忘录: `docs/SCIENTIFIC_COMMUNICATION_MEMO_20260427.md`
- Archive index / 归档索引: `archive/README.md`

Old status snapshots are archived under / 旧状态快照已归档到：

- `archive/project_status_20260427_pre_R4/`
- `archive/project_status_20260427_pre_R5/`

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

- E24 causal-chain ledger / E24 因果链台账: `reports/E24_s4_causal_chain_ledger.md`
- E25 layerwise verifier lens / E25 分层 verifier lens: `reports/E25_layerwise_verifier_lens_summary.md`
- E26 AIME hard-task smoke / E26 AIME 难题 smoke: `reports/E26_aime_hard_smoke_audit_summary.md`
- E27 transfer absolute verifier / E27 跨模型绝对 verifier: `reports/E27_transfer_absolute_verifier_summary.md`
- E27 transfer contrastive verifier / E27 跨模型对比 verifier: `reports/E27_transfer_contrastive_verifier_summary.md`
- E27 transfer generation audit / E27 跨模型生成审计: `reports/E27_transfer_trace_generation_audit.md`
- S5 integrated scientific analysis and roadmap / S5 综合科学分析与路线图: `reports/S5_INTEGRATED_SCIENTIFIC_ANALYSIS_AND_ROADMAP_20260427.md`

## Key Current Claim / 当前关键主张

Multilingual surface lexicalization can create ACPI trace-selection risk; absolute Yes/No verifiers over-accept selected ACPI rows, while sibling comparison and hidden span/module patching expose process/error-span signals in robust pairs. The mechanism branch now has diagnostic support for middle-layer process confounding and output-head re-entanglement, but not full circuit proof. Hard Qwen14 lexical pairs, Gemma4 position bias, and AIME zero-final-correct smoke are explicit boundaries.

中文：多语言表层词汇化会产生 ACPI 轨迹选择风险；绝对式是/否 verifier 会过度接受选择后的 ACPI，而 sibling 对比与 hidden span/module patch 能在稳健 pair 中暴露过程/错误 span 信号。机制分支现在有中层过程混杂与输出头再纠缠的诊断支持，但还不是完整 circuit 证明。Qwen14 困难词汇 pair、Gemma4 位置偏差和 AIME 零 final-correct smoke 是明确边界。

## Evidence Snapshot / 证据快照

- E24: 9 pairs; 8 manual ACPI; 8/8 absolute-overaccepted; 7/8 contrastive signal; 6/8 robust hidden span signal; 2/8 MLP signal. / E24：9 对；8 对人工 ACPI；8/8 绝对过度接受；7/8 对比信号；6/8 hidden span；2/8 MLP。
- E25: diagnostic logit lens shows middle-to-final signal drops and output/head re-entanglement candidates. / E25：诊断 logit lens 显示中层到输出层信号下降与输出头再纠缠候选。
- E26: 48 AIME-style rows, zero strict final-correct, zero ACPI candidate. / E26：48 行 AIME 风格样本，严格答案正确为 0，ACPI 候选为 0。
- E27: Qwen3.5-27B and Gemma4 over-accept absolute ACPI rows; Qwen3.5-27B contrastive acc 0.875; Gemma4 contrastive acc 0.542 with A-position bias. / E27：Qwen3.5-27B 与 Gemma4 绝对式过度接受；Qwen3.5-27B 对比准确率 0.875；Gemma4 对比准确率 0.542 且有 A 位置偏差。

## Validation / 验证

Run on 2026-04-27 / 已在 2026-04-27 运行：

```bash
python -m py_compile src/mplens/modeling.py scripts/build_s4_causal_chain_ledger.py scripts/run_layerwise_verifier_lens.py scripts/summarize_layerwise_verifier_lens.py scripts/audit_e26_aime_hard_smoke.py scripts/run_trace_pool_generate.py
python scripts/check_project.py
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
tmux ls 2>/dev/null || true
```

Result / 结果：compile passed, project check passed, GPUs idle, no active tmux sessions reported. / 编译通过，项目检查通过，GPU 空闲，无活跃 tmux 会话。

## Reproduction Scripts / 复现实验脚本

- `scripts/launch_e27_transfer_qwen27_auto_tmux.sh`: Qwen3.5-27B four-GPU `device_map=auto` transfer evaluation and generation. / Qwen3.5-27B 四卡 `device_map=auto` 迁移评估与生成。
- `scripts/launch_e27_transfer_gemma4_tmux.sh`: Gemma4 single-GPU transfer evaluation and generation. / Gemma4 单卡迁移评估与生成。

## Next Best Stage / 下一最佳阶段

1. Expand clean same-route pair bank to at least 8 robust ACPI/valid sibling pairs. / 扩展干净同 route pair bank 至至少 8 对稳健 ACPI/valid sibling。
2. Run head-level or SAE/transcoder-style mechanism probes only on robust E24/E22 targets. / 只在稳健 E24/E22 目标上运行头级或 SAE/transcoder 风格机制 probe。
3. For AIME24/25, first use stronger/larger generators or verifier-guided sampling to obtain final-correct traces; then audit ACPI. / 对 AIME24/25，先用更强/更大生成器或 verifier-guided sampling 获得 final-correct 轨迹，再审计 ACPI。
4. Rerun Qwen3.5-27B generation with stricter prompts to avoid meta-planning; resample Gemma4 discount paraphrases. / 用更严格提示重跑 Qwen3.5-27B 生成以避免元规划；重采 Gemma4 折扣改写。
5. In the paper, keep selected-set and mechanism-language caveats explicit. / 论文中必须明确选择集与机制语言限制。
