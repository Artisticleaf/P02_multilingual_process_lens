# E62-E70 Autonomous Synthesis / E62-E70 自动推进综合报告（2026-04-29）

- Scope / 范围：本报告综合 E62 到 E70 的准入、复现、自然采样、机制层扫描、标签校准、span 可观测性、筛选模拟、严格/修复边界和统计附录。
- Plain language / 说人话：这轮实验没有推翻核心现象，但把主张变得更准确：单条 trace 的 Yes/No 审查确实会保留很多“答案对但有错误局部步骤”的 strict trace；模型 hidden state 里通常有过程有效性证据；但 sibling comparison 不是所有模型上天然完美，controlled invalid 也常常包含后续修复，所以论文必须区分 strict trace-selection risk 与 unrepaired ACPI prevalence。

## What We Now Know / 目前已经得到的科学事实

1. **External P0 admission / 外部 P0 准入**：E62 只把 `glm47_flash_candidate` 纳入扩展 P0；Nemotron 因当前 HF 动态路径缺 `mamba-ssm`，EXAONE 因 `exaone4_5` 后端和非商业许可边界未进入官方证据。
2. **Pointwise over-acceptance generalizes / 单点过度接受可跨家族复现**：GLM 在 E42/E60/E61 上复现 plain Yes/No strict ACPI accept：E42=0.417，E60=0.600，E61=0.479；valid accept 仍约等于 1.0。
3. **Stronger pointwise prompts help but are not the whole story / 更强过程 prompt 有帮助但不是完整修复**：在 GLM E61 上 answer-blind/careful strict ACPI accept 降到 0.021/0.083；核心 P0 上也类似下降。这说明风险不是“prompt 完全没要求检查过程”，而是 objective、阈值、答案锚定和输出决策如何使用过程信号的问题。
4. **Sibling comparison boundary / sibling 边界**：核心 P0 的 sibling 仍非常强；但 GLM raw sibling 在 E60/E61 只有 0.533/0.531，careful sibling 为 0.700/0.698。E66 显示这不只是简单 A/B 字母偏置，GLM 的 contrastive process discrimination 本身也更弱。
5. **Hidden-state evidence is stronger than behavior / hidden 证据强于外显行为**：E65 在 E61 的 96 条 trace 上做全层扫描，最佳 residual LOTO 准确率为 Qwen35-27B 1.000、Gemma4-31B 1.000、Gemma4-26B-A4B 0.927、GLM 0.979。GLM 的 hidden evidence 很强，但 A/B sibling 行为弱，这正是“内部有证据，输出目标/阈值/标签使用不稳定”的关键证据。
6. **Natural hard-task ACPI remains rare / 自然困难题 ACPI 仍罕见**：E64 GLM hard-task k=4 生成 72 条，只有 8 条 final-correct；这 8 条人审均过程有效，strict/unrepaired ACPI 都为 0。结合 E57，困难题自然未修复 ACPI 不能作为 headline 高频现象。
7. **Strict vs repair-aware boundary is essential / 必须区分严格与修复口径**：E69 显示 E42/E54/E61 的 78 条 controlled strict ACPI 中有 55 条含显式 repair/override marker。主文必须写成 strict trace-selection risk；不能把所有受控样本说成“未修复乱推碰巧对”。
8. **Span-local surface matching is brittle / span 字面匹配很脆**：E67 显示 E61 48 条 invalid trace 中，人工英文 error_span 只有 9 条能字面出现在 trace 中；多语言路线导致简单字符串定位失效。但 E65 hidden probe 在 span 不可字面匹配时仍几乎能拒绝 strict ACPI。
9. **Filter amplification / 筛选器放大**：E68 中 outcome-only 在 balanced controlled pool 中按定义保留全部 strict ACPI；plain pointwise 的 E61 扩展 P0 平均 strict ACPI retention 为 0.438；answer-blind/careful 降到 0.099/0.161；sibling 扩展均值 0.125，主要被 GLM 边界拉高。
10. **Statistics / 统计附录**：E70 给出 Wilson 区间和 E61 leave-one-family 敏感性。E61 plain ACPI accept 不是由单一 family 单独撑起，但诊断集样本量仍决定了区间较宽。

## Updated Claim / 更新后的主张

**Recommended paper claim / 推荐论文主张：**

> In strict trace-selection settings, multilingual and surface/process-semantic traps can create final-answer-correct traces containing invalid local reasoning steps. Current medium open models often over-accept such traces under pointwise absolute Yes/No verification, even when prompts ask for process checking. Stronger pointwise objectives reduce but do not eliminate the risk. Contrastive sibling comparison is a strong diagnostic for core P0 models, but not an unconditional oracle: GLM shows label/position and contrastive-discrimination boundaries. Across P0/expanded-P0 models, hidden residual states encode strict process-validity evidence much more reliably than the final verifier decision uses it. Therefore the central failure is a mismatch among surface lexicalization, process semantics, final-answer anchoring, verifier objective/threshold, and output-head/label use.

**中文说人话版本：**

> 在严格筛选过程 trace 的场景里，多语言/表层语义陷阱会让 trace 出现“答案是对的，但中间有错误局部步骤”。现在这些中等开源模型经常在单条 Yes/No 审查里把这种 trace 放过去；让它更仔细会改善，但不能保证消除。核心 P0 上 sibling comparison 很强，但 GLM 告诉我们 sibling 也不是天然 oracle，因为 A/B 标签、位置和对比目标本身会出问题。最重要的是，hidden residual 里其实能很强地读出过程有效性，说明模型不是完全看不见错误，而是输出决策没有稳定用好这些证据。

## What Is New / 创新点现在更清楚在哪里

- **Not just answer correctness / 不只是答案对错**：E53/E60/E68 把 outcome-only、plain Yes/No、careful、answer-blind、locate、sibling 放在同一链条里，显示失败来自 verifier objective/threshold，而不是简单“答案错/格式坏”。
- **Hidden evidence vs decision mismatch / hidden 证据与输出决策错配**：E65 的强 residual probe 与 GLM sibling 弱行为并存，提供了更具体的机制创新点：模型内部有过程信号，但 final decision/output-head label use 没有稳定调用。
- **Output-head/label-bias boundary / 输出头标签偏置边界**：E66 把 sibling 失败拆成 A/B 先验与真正对比判别不足；这比简单说“pairwise 更好”更细。
- **Strict vs repair-aware framing / 严格与修复口径分离**：E69 防止过度声称，把 controlled ACPI 定义为 strict trace-selection risk，同时把 natural unrepaired ACPI 单独报告。
- **Multilingual span observability / 多语言 span 可观测性**：E67 显示字面 span 对齐在多语言/拼音/混合语中很不可靠，但 hidden probe 仍能读出过程信号，支持“surface lexicalization 与过程语义错配”的主线。

## Remaining Weaknesses / 距离顶会顶刊仍要补的短板

1. **Natural prevalence / 自然发生率**：E48/E57/E64 都提示自然未修复 ACPI 不高；不能把“自然高频”作为主 headline。若要强化，需要更大、更多任务族、更多模型生成的 final-correct trace，并持续人审。
2. **Full circuit / 完整电路**：E65 是 residual representation 证据，不是 head/neuron 级电路。后续需要 best-layer path patch：token mixer、MLP、attention heads 到 Yes/No 与 A/B logits 的中介。
3. **Span-local causality / span 局部因果**：E67 只是 observability audit；下一步要做 translated-span alignment 与 token-level patch，证明错误 span 的 token 状态对 verifier decision 有因果作用。
4. **Repair-aware objective / 修复口径 verifier**：E69 暴露 controlled traces 常有 repair marker。后续应显式比较 strict verifier、repair-aware verifier、final-surviving-proof verifier 三种目标，而不是把它们混在一起。
5. **External models / 外部模型**：GLM 已纳入扩展 P0；Nemotron/EXAONE 仍是后端/许可阻塞，不应进入主证据，除非后续环境升级并重跑 E62。

## Recommended Next Experiments / 下一步建议

1. **E71 strict-vs-repair-aware verifier objective**：构造三种 prompt：严格任一错步即 No、允许显式修复、只看最终保留下来的证明；目标是解释 absolute over-accept 有多少来自“模型采用了 repair-aware 口径”。
2. **E72 best-layer causal mediation**：用 E65 最佳层方向而不是固定第 16 层，在 Yes/No 和 A/B logits 上做 patch/ablation；目标是把强 probe 变成更强因果证据。
3. **E73 span-aligned token patch**：人工对齐 E61 的中文/混合语/拼音 error span token，做 span-local patch；目标是证明过程错误位置而不是整条 trace 风格驱动 hidden signal。
4. **E74 larger natural harvesting**：不要盲目扩大所有任务；优先 hard tasks 中已经有 final-correct 的题型和 answer-first/no-gold 变体，按模型分层人审 strict/repaired/unrepaired。
5. **E75 label-free contrastive objective**：避免 A/B 标签，改成 two-pass scoring 或自然语言说明“第一条/第二条”的校准版本；目标是检验 GLM sibling 弱是不是可由 objective 重写修复。

## Artifacts / 主要落盘材料

- E62: `reports/E62_EXTERNAL_P0_SMOKE_20260429.md`
- E63: `reports/E63_GLM_EXPANDED_P0_REPLICATION_20260429.md`
- E64: `reports/E64_GLM_HARD_TASK_EXPANSION_20260429.md`
- E65: `reports/E65_MECHANISTIC_LAYER_SWEEP_20260429.md`
- E66: `reports/E66_CONTRASTIVE_LABEL_CALIBRATION_20260429.md`
- E67: `reports/E67_SPAN_LOCAL_OBSERVABILITY_20260429.md`
- E68: `reports/E68_FILTER_AMPLIFICATION_EXPANDED_20260429.md`
- E69: `reports/E69_STRICT_VS_REPAIR_BOUNDARY_20260429.md`
- E70: `reports/E70_STATISTICS_AUDIT_APPENDIX_20260429.md`
