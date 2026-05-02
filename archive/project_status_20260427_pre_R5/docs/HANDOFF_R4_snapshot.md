# Handoff / 交接说明

Date / 日期: 2026-04-27 CST
Project / 项目目录: `/home/Awei/P02_multilingual_process_lens`

## Active Memory / 当前项目记忆

- Current history / 当前 history: `docs/HISTORY_KG_20260427_R4.md`
- Literature and novelty review / 文献与创新性复核: `docs/LITERATURE_AND_NOVELTY_REVIEW_20260427.md`
- Archive index / 旧状态文档归档索引: `archive/README.md`

Old handoff/history/status documents were moved to `archive/project_status_20260427_pre_R4/`.

旧的 handoff、history、status 文档已移动到 `archive/project_status_20260427_pre_R4/`。

## Environment / 环境

```bash
cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/src
```

For Qwen3.5, use hf5 first / Qwen3.5 优先使用 hf5：

```bash
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
```

## Latest Results / 最新结果

- E18 targeted four-GPU generation / E18 四卡定向生成: `reports/E18_S3_TARGETED_SIBLING_EXPANSION_AND_AUDIT_20260427.md`
- E19 module patch / E19 模块级 patch: `reports/E19_real_acpi_module_patch_summary.md`
- E22 clean-sibling span patch / E22 干净 sibling span patch: `reports/E22_e18_clean_sibling_span_patch_summary.md`
- E23 clean-sibling contrastive verifier / E23 干净 sibling 对比 verifier: `reports/E23_e18_clean_sibling_contrastive_summary.md`

## Key Current Claim / 当前关键主张

Multilingual surface lexicalization can create ACPI trace-selection risk; absolute Yes/No verifiers over-accept selected ACPI rows, while sibling comparison and hidden span patch can expose process/error-span signals in robust pairs. This is not universal: Qwen14 E21/E20 is an explicit hard negative boundary.

中文：多语言表层词汇化会产生 ACPI 轨迹选择风险；绝对式是/否 verifier 会过度接受部分 ACPI，而 sibling 对比和 hidden span patch 能在稳健 pair 中暴露过程/错误 span 信号。但该机制不是万能的：Qwen14 的 E21/E20 是明确困难负例边界。

## Next Best Stage / 下一阶段

1. Expand clean same-route pair bank to at least 8 robust pairs. / 扩展干净同 route pair bank 到至少 8 对。
2. Run head-level or circuit-level localization only on robust E19/E22 targets. / 只在稳健 E19/E22 目标上做头级或 circuit 级定位。
3. Build automatic triangulation proxy; do not claim oracle policy as a deployed method. / 构建自动三角测量 proxy，不把人工 oracle 策略宣称为可部署方法。
