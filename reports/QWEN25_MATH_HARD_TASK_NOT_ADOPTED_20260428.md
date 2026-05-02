# Qwen2.5-Math Hard-Task Results Not Adopted / Qwen2.5-Math 困难题结果不采纳（2026-04-28）

## Decision / 决定

- `qwen25_math_7b_instruct` is now `P2_legacy_math_control`. / `qwen25_math_7b_instruct` 现在是 `P2_legacy_math_control`。
- Its hard-task E49/E51/E52 outputs are **not adopted for the mainline**. / 它的 E49/E51/E52 困难题输出**不纳入主线**。
- These outputs must not be used as headline evidence for the paper's P0 model claims. / 这些输出不能作为论文 P0 模型主张的主证据。
- Future hard-task and mechanism experiments should not depend on Qwen2.5-Math unless explicitly labeled as legacy debugging. / 后续困难题与机制实验不应依赖 Qwen2.5-Math，除非明确标注为旧管线调试。

## Why / 原因

- The project's P0 cluster now focuses on recent, stronger, medium open-weight models: `qwen35_27b`, `gemma4_31b_it`, `gemma4_26b_a4b_it`, plus downloaded and smoke-tested new candidates. / 当前 P0 聚焦较新、较强、中等开源模型：`qwen35_27b`、`gemma4_31b_it`、`gemma4_26b_a4b_it`，以及后续下载并 smoke test 通过的新候选。
- Qwen2.5-Math-7B is older and much smaller; using it in the mainline would let reviewers dismiss findings as legacy-model or small-model artifacts. / Qwen2.5-Math-7B 较旧且更小，把它放进主线会让 reviewer 质疑结果只是旧模型/小模型 artifact。
- E49-E52 were still useful diagnostically: they showed a hard-task format/objective bottleneck, but that bottleneck is not a P0 frontier-model conclusion. / E49-E52 仍有诊断价值：它们暴露困难题格式/目标瓶颈，但这不是 P0 前沿模型结论。

## Archive / 归档

Archived files are under:

归档文件位于：

`archive/qwen25_math_hard_task_not_adopted_20260428/`

The archive manifest states that these materials are legacy diagnostics only and must not enter future mainline synthesis. / 归档 manifest 已说明这些材料仅为旧诊断，不得进入后续主线综合。

## Consequence for KG / 对 KG 的影响

- Do not cite Qwen2.5-Math hard-task boxed-correct rows as evidence for the main claim. / 不引用 Qwen2.5-Math 困难题 boxed-correct 行作为主张证据。
- Do not use E52 as a planned seed source for the next mainline causal experiment. / 不再把 E52 作为下一步主线因果实验的种子来源。
- Re-run hard-task and causal-chain experiments on current P0 models or newly admitted P0 candidates. / 困难题与因果链实验应在当前 P0 或新进入 P0 的候选模型上重跑。
