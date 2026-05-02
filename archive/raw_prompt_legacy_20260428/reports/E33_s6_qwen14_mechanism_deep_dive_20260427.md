# E33 S6 Qwen14 机制深挖：中层残差、MLP/Attention、单头扫描（2026-04-27）

## 1. 这次实验回答什么问题

这次不再只问“verifier 会不会接受错误过程”，而是问一个更接近因果机制的问题：

> 对 S6 中最稳健的 Qwen14 真实 ACPI pair，错误/正确的局部词汇语义信号到底在模型哪里起作用？是某一层残差流、MLP、attention，还是单个 attention head？

锚点 pair：`qwen14_s6_pay75_bad150_valid151`。

- bad trace 的错误 span：`sold at a 75% discount of its original price`。
- valid trace 的支持 span：`sold at 75% of the original price`。
- 两条 trace 的最终答案都是 60；bad trace 是答案正确但过程语义错误。
- verifier 是 `qwen3_14b_base` 自己，在英文 process-only prompt 下打 Yes/No margin。

## 2. 实验文件

- Dense residual span patch：`results/S6_lexical_grid_span_patch_dense/qwen3_14b_base_real_acpi_span_patch.json`
- Attention-vs-MLP module patch：`results/S6_lexical_grid_module_patch/qwen3_14b_base_real_acpi_module_patch.json`
- Pre-o_proj attention-head patch：`results/S6_lexical_grid_attention_head_patch/qwen3_14b_base_real_acpi_attention_head_patch.json`
- 新脚本：`scripts/run_real_acpi_attention_head_patch.py`
- 修改脚本：`scripts/run_real_acpi_module_patch_smoke.py` 现在同时支持 `e05_idx` 和 `audit_idx`。

## 3. Dense residual span patch：信号是一个中层残差带，不是单点

把 valid span 的残差向量 patch 到 bad trace 对应 span，记为 `valid->bad`；把 bad span patch 到 valid trace，记为 `bad->valid`。

如果该 span 真的带有过程语义信号，理想方向是：

- `valid->bad` 增加 bad trace 的 Yes-No margin；也就是让模型更像看到正确过程。
- `bad->valid` 降低 valid trace 的 Yes-No margin；也就是把错误过程语义注入正确 trace。

结果非常清楚：

| layer | valid->bad effect | bad->valid effect | 解释 |
|---:|---:|---:|---|
| 0 | +0.875 | -0.875 | 早层已有弱方向信号。 |
| 4 | +1.375 | -0.875 | 信号开始增强。 |
| 8 | +1.625 | -1.125 | 中层前段显著增强。 |
| 9 | +2.000 | -1.250 | 强方向信号。 |
| 10 | +2.375 | -0.875 | 强方向信号。 |
| 11 | +2.625 | -1.000 | 强方向信号。 |
| 12 | +2.750 | -1.000 | 峰值之一。 |
| 13 | +2.750 | -1.000 | 峰值之一。 |
| 14 | +2.750 | -1.000 | 峰值之一，与旧 S6 结果一致。 |
| 15 | +2.875 | -0.750 | valid->bad 最大，但双向略不如 12-14 稳。 |
| 20 | +0.875 | -0.375 | 信号衰减。 |
| 25 | +0.000 | -0.125 | 接近消失。 |
| 30 | +0.125 | +0.000 | 不再是干净双向。 |
| 39 | +0.000 | +0.000 | 输出前残差 patch 已无明显作用。 |

关键科学事实：

- 过程语义信号不是只在 L14 一个点出现，而是从早层开始逐渐增强，在 L12-L15 形成一个强中层残差带，然后在后层快速衰减。
- 这支持“中层混杂/中层过程证据”的说法：模型内部确实存在可被因果 patch 暴露的过程语义信号。
- 但这个信号到最终 Yes/No 决策时没有自动变成拒绝 bad trace；bad trace 的原始 margin 仍为正，说明最终决策层/目标阈值把局部过程错误重新压过去了。

## 4. MLP vs Attention：MLP L14 是最大干净 module，但不是完整解释

Module patch 把某一层的 `self_attn` 或 `mlp` 输出在目标 span 上替换。

最重要结果：

| span | layer | module | valid->bad | bad->valid | 解释 |
|---|---:|---|---:|---:|---|
| support_error_span | 14 | mlp | +0.375 | -0.125 | 最大且方向干净的 module 级结果。 |
| support_error_span | 9 | mlp | +0.250 | -0.125 | 早中层 MLP 也有方向信号。 |
| support_error_span | 9 | self_attn | +0.125 | -0.125 | attention 有弱方向信号。 |
| support_error_span | 14 | self_attn | +0.125 | -0.125 | attention 有弱方向信号。 |
| trace_span | 9 | self_attn | +0.250 | -0.125 | 全 trace attention patch 有信号，但不如局部 residual 干净。 |

解释要谨慎：

- L14 MLP 的方向最干净，但效应只有 `+0.375/-0.125`，远小于同层 residual span patch 的 `+2.750/-1.000`。
- 这说明残差信号不是单个 MLP 输出就能完全解释；它更像是多个层/模块积累后的 residual state。
- 因此我们现在能说“MLP 尤其是 L14 MLP 参与了过程语义信号”，但还不能说“错误由某个 MLP neuron/circuit 单独编码”。

## 5. 单 attention head 扫描：没有发现一个可以单独解释现象的头

这次扫描了 L9/L14/L20 的 40 个 attention heads，在 `support_error_span` 上 patch pre-o_proj head vector。

结果：

- 120 个 head patch 中有 62 个方向干净。
- 但单个 head 的最大效应只有 `+0.125/-0.125`。
- 最强 clean head：L9 H14，`valid->bad=+0.125`，`bad->valid=-0.125`。
- 各层平均单头效应都很小：L9 mean abs half 约 0.067，L14 约 0.081，L20 约 0.080。

这说明：

- attention head 不是完全无关；不少 head 的方向是对的。
- 但没有一个单头能解释 residual patch 的大效应。
- 更合理的机制假设是：过程语义信号分布在多个 heads/modules 中，在中层 residual stream 汇聚；最终 Yes/No 输出头/目标阈值再把它重整为“仍然接受”。

## 6. 对主 claim 的贡献

这次 E33 给主张补了一块机制证据：

1. **不是纯表面现象**：只替换 `75% discount` vs `75% of original price` 的 span residual，就能双向改变 verifier 的 Yes/No margin。
2. **不是单个词或单个头的玩具效应**：强信号出现在 L12-L15 的中层残差带，单 head 效应很小。
3. **MLP 有参与，但不是全部**：L14 MLP 是最强 module-level clean result，但远小于 residual patch。
4. **支持 objective/threshold mismatch**：模型内部有过程错误信号，但最终 absolute Yes/No 仍接受 bad trace，说明问题不只是“模型看不见”，而是“看见了但最终决策没有用好”。

## 7. 边界和下一步

当前边界：

- 这是一个强锚点 pair，不是统计普遍性证明。
- head patch 是 pre-o_proj head slice 替换，不等同于完整 path patching。
- module patch 不是 neuron/SAE 级解释，还不能说具体 feature 是什么。

下一步最有信息收益的机制实验：

1. 对 L12-L15 做更细的 path patch：MLP 输入、MLP gate/up/down、attention o_proj input/output 分开。
2. 对 support/error span 做 span-token 级热区：看 `75% discount` 中到底是 `discount`、`75%`、还是组合短语贡献最大。
3. 用同一机制 probe 跑 E31 的 inequality/diameter/unit 三个非折扣陷阱，判断中层残差带是否是共性机制，而不是折扣 pair 特例。
4. 如果时间允许，再做 SAE/transcoder；但当前更优先的是先证明“多个任务族都有中层 residual process signal”。
