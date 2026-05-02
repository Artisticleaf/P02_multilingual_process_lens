# E35 E31 Qwen3.5-9B Module Patch：linear-attention / self-attention / MLP 分解（2026-04-27）

## 1. 目的

E34 发现：Qwen3.5-9B 在 E31 的几何、组合、不等式 bad trace 上会过度接受，但 support/error residual patch 仍能暴露 hidden process signal。E35 继续问：

> 这些 hidden signal 能不能进一步归因到某类模块：linear attention、full self-attention，还是 MLP？

Qwen3.5-9B 是混合架构：多数层是 `linear_attn`，每隔 4 层左右有 full `self_attn`。因此这次 module patch 同时扫描：`linear_attn`、`self_attn`、`mlp`。

## 2. 文件

- 结果：`results/E35_e31_non_discount_module_patch/qwen35_9b_real_acpi_module_patch.json`
- 日志：`logs/E35_e31_qwen35_9b_module_patch.log`
- 脚本更新：`scripts/run_real_acpi_module_patch_smoke.py` 现在支持 `linear_attn`。

## 3. 主要结果

| pair | best linear_attn | best self_attn | best MLP | 解释 |
|---|---|---|---|---|
| ratio | L0 `+1.500/-0.125` | L11 `+1.000/+0.000` | L0 `+1.000/+0.000` | 比例错误最像早层 lexical/route 语义，linear_attn 最强。 |
| inequality | L0 `+0.187/-0.187` | L3 `+0.062/-0.062` | L10 `+0.188/-0.187` | 不等式模块级信号弱但方向干净。 |
| unit | L0 `+0.000/-0.688` | L15 `+0.000/-0.125` | L1 `+0.000/-0.312` | 主要表现为 bad 注入 valid 会压低 margin，valid 注入 bad 很弱。 |
| geometry | L4 `+0.125/+0.000` | L3 `+0.062/+0.125` | L8 `+0.312/-0.062` | MLP 有最清楚的 module-level 信号，但远小于 residual patch。 |
| combinatorics | L12 `+0.500/+0.000` | L7 `+0.125/-0.125` | L13 `+0.375/-0.000` | linear_attn/MLP 有弱正向信号，单模块不能解释 residual 大效应。 |

## 4. 关键解释

- E34 的 residual patch 很强，例如 combinatorics 是 `+2.250/-3.438`，geometry 是 `+0.500/-3.000`。
- E35 的单模块 patch 明显更小，通常只有 0.1 到 0.5，只有 ratio 的 L0 linear_attn 达到 `+1.500/-0.125`。
- 这说明 Qwen3.5-9B 的 E31 process signal 不是某个模块一次性写入，而更像在早-中层 residual stream 中由 linear-attention、MLP、少量 full attention 共同累积。
- 对过度接受最明显的 geometry/combinatorics，module-level 信号存在但不够单独翻转决策；这再次支持“hidden evidence 有，但最终 absolute Yes/No 阈值没有用好”。

## 5. 对论文机制线的价值

E35 可以支持一个更稳的机制说法：

> 在混合 attention 架构的 Qwen3.5-9B 中，非折扣过程错误的 hidden evidence 不是 single module 或 single head 效应，而是在 residual stream 中分布式累积；MLP 和 linear attention 都参与，但最终 verifier 决策仍可能过度接受。

这和 E33 的 Qwen14 结果一致：单 head/module 效应都小于 residual span patch，所以论文不应该过度声称“发现了一个错误 head”。更可靠的创新点是：

- 局部过程语义错误有可因果干预的 hidden span signal；
- 该信号跨任务族、跨架构存在；
- 但它以分布式 residual evidence 的形式存在，最终输出目标/阈值会重整甚至压过它。
