# E34 E31 非折扣机制泛化：5 类陷阱的 support/error span dense patch（2026-04-27）

## 1. 这次实验的目的

E33 证明了 S6 折扣锚点里，Qwen14 的过程语义信号出现在中层 residual stream。E34 问的是更关键的泛化问题：

> 这种“局部过程错误 span 在 hidden state 里有因果信号”的现象，是否只属于折扣/翻译 pair，还是也出现在 E31 的非折扣陷阱里？

我们在 E31 的 5 个受控非折扣陷阱上做 support/error span residual patch：

1. 比例分母：`男生占全班的2/3` vs `男生占总人数的2/5`
2. 不等式边界：`between 3 and 7, inclusive` vs `greater than 3 and no more than 7`
3. 单位语义：`一打袜子等于12双袜子` vs `一打等于12只袜子`
4. 直径/半径：`半径是10厘米` vs `半径是10÷2=5厘米`
5. 无序组合：`the order matters` vs `The committee is unordered`

测试模型：

- `qwen3_14b_base`：之前 S6 机制锚点模型，E31 里相对严格。
- `qwen35_9b`：E31 里更容易过度接受，适合作为“风险模型”的机制对照。

## 2. 输出文件

- Pair 配置：`configs/e31_non_discount_span_patch_pairs.yaml`
- Qwen3.5-9B pair 配置：`configs/e31_non_discount_span_patch_pairs_qwen35_9b.yaml`
- Qwen14 结果：`results/E34_e31_non_discount_span_patch_dense/qwen3_14b_base_real_acpi_span_patch.json`
- Qwen3.5-9B 结果：`results/E34_e31_non_discount_span_patch_dense/qwen35_9b_real_acpi_span_patch.json`

## 3. Qwen14：4/5 个非折扣陷阱有强 hidden process signal

Qwen14 的绝对式 process-only verifier 对 E31 比较严格：5 个 invalid-correct 中，它只明显接受不等式边界那个 bad trace。这个实验仍然有价值，因为它告诉我们：模型为什么能拒绝，以及哪类错误隐藏信号弱。

| pair | bad 原始 margin | 最佳层 | valid->bad | bad->valid | 干净层数 | 解释 |
|---|---:|---:|---:|---:|---:|---|
| ratio | -0.625 | L4 | +1.500 | -1.625 | 23/40 | 强双向信号；模型能看到比例分母错误。 |
| inequality | +2.500 | L19 | +0.250 | -0.375 | 5/40 | 弱信号；这是 Qwen14 实际过度接受的边界例子。 |
| unit | -0.875 | L11 | +1.125 | -1.375 | 21/40 | 强双向信号；模型能看到“一打=12双”的错误。 |
| geometry | -0.750 | L4 | +3.000 | -1.625 | 27/40 | 最强双向信号；直径/半径错误在 hidden state 里很清楚。 |
| combinatorics | -0.250 | L10 | +2.125 | -1.750 | 26/40 | 强双向信号；无序组合语义可被 patch 暴露。 |

关键事实：

- 4/5 个非折扣陷阱都有大量 clean-direction layers。
- 平均层效果在 L0-L20 都比较强，L23 后快速衰减。
- 不等式边界是明确边界：它是 Qwen14 唯一强接受的 invalid-correct 行，也是 hidden span patch 最弱、方向最不稳定的行。

这支持一个更细的机制说法：

> 当局部过程错误在中层 residual stream 形成强双向信号时，Qwen14 往往能拒绝；当该信号弱或被语境重整时，绝对 verifier 更可能过度接受。

## 4. Qwen3.5-9B：过度接受更多，但 hidden span 仍有可 patch 信号

Qwen3.5-9B 的 bad 原始 margin 更危险：不等式、几何、组合三个 invalid-correct bad trace 都是正 margin，也就是绝对式 process-only 会接受。

| pair | bad 原始 margin | 最佳层 | valid->bad | bad->valid | 干净层数 | 解释 |
|---|---:|---:|---:|---:|---:|---|
| ratio | -0.750 | L0 | +3.188 | -1.437 | 17/32 | 强信号；模型拒绝该 bad trace。 |
| inequality | +2.750 | L5 | ≈0.000 | -1.062 | 15/32 | 有不对称信号，但 valid->bad 很弱；仍过度接受。 |
| unit | -1.625 | L4 | +0.375 | -2.500 | 12/32 | 有信号，主要体现为 bad 注入 valid 会显著降低 margin。 |
| geometry | +1.938 | L10 | +0.500 | -3.000 | 12/32 | 过度接受，但 hidden patch 能强烈降低 valid trace margin。 |
| combinatorics | +1.125 | L5 | +2.250 | -3.438 | 17/32 | 过度接受，但 hidden signal 很强。 |

关键事实：

- Qwen3.5-9B 并不是完全看不到错误；多个 bad span 注入 valid trace 会把 Yes-No margin 大幅压低。
- 但是最终 bad trace 仍可保持正 margin，特别是不等式、几何、组合。这正是 objective/threshold mismatch 的机制版本：hidden evidence 有，但最终二值阈值没有把它变成拒绝。
- Qwen3.5-9B 的有效层带更靠前：L0-L13 比较强，L16 后迅速衰减；这可能和 Qwen3.5 的混合 linear/full attention 架构有关，但目前只能作为观察，不应过度解释。

## 5. 和 S6 折扣机制的关系

E33 的 S6 折扣 pair 显示：Qwen14 support/error residual patch 在 L12-L15 最强，峰值约 `+2.750/-1.000`。

E34 的 E31 非折扣结果显示：

- 强 hidden process signal 不只出现在折扣表达上。
- 比例、单位、几何、组合这四类都能通过 residual span patch 暴露局部过程语义。
- 不等式边界是一个真实薄弱点：自然 E30 和受控 E31 都显示它容易被 verifier 接受，而且 hidden patch 也更弱。

因此我们可以把论文主张写得更稳：

> 不是所有表层/过程错误都有同样强的 hidden signal；但在多个任务族中，局部过程语义错误确实能在中层 residual state 中形成可因果干预的信号。绝对 verifier 是否拒绝，取决于这个信号是否足够强、是否被最终答案和输出阈值压过。

## 6. 对 claim 的增强和边界

增强点：

1. 折扣不是孤例。E31 的非折扣任务族里也有可 patch 的过程/error span 信号。
2. hidden signal 和 verifier 决策不是同一件事。Qwen3.5-9B 在几何/组合上有强 hidden signal，但仍接受 bad trace。
3. 不等式边界是可解释的薄弱点：它的 hidden signal 弱，且多个模型都容易过度接受。

边界：

- E31 是人工受控诊断集，不是自然发生率统计。
- 当前 patch 是 residual span-level，不是 neuron/feature-level。
- Qwen3.5-9B 架构含 linear attention，层带位置不能直接和 Qwen14 一一对齐。

## 7. 下一步最值得做什么

1. 在 E31 的 geometry/comb/inequality 上做 module patch，验证 Qwen3.5-9B 的强 hidden signal 是 MLP 主导还是 attention/linear-attention 主导。
2. 对 inequality 做专门拆解：比较 `between ... inclusive`、`greater than`、`no more than`、最终列举 `4,5,6,7` 四个 span，找出为什么它最容易被过度接受。
3. 把 E34 的结果和 error-span extraction 对齐：看模型能定位的错误是否正好对应 patch 强的 span。
