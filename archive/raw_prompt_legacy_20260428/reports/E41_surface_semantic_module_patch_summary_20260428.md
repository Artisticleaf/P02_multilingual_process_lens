# E41 Surface-Semantic Module Patch Summary / E41 表层语义模块 patch 汇总

Created / 创建时间: 2026-04-28T00:41:20

Goal / 目标：在 E40 已经出现强 residual span-patch 信号的 E39 新语义族上，进一步拆分到 attention/linear-attention 与 MLP 模块输出。This is a module-level smoke test, not a full circuit proof. / 这是模块级 smoke test，不是完整 circuit 证明。

| model | pair / 语义对 | best module / 最强模块 | layer | valid->bad | bad->valid | clean rows | plain read / 人话解释 |
|---|---|---|---:|---:|---:|---:|---|
| qwen35_9b | e41_qwen35_each_vs_total_bad390062_valid390061 | mlp | 4 | 0.375 | -0.062 | 7/8 | MLP carries the strongest local process signal / 最强局部过程信号在 MLP |
| qwen35_9b | e41_qwen35_percent_increase_bad390042_valid390041 | mlp | 8 | 0.375 | -0.062 | 3/8 | MLP carries the strongest local process signal / 最强局部过程信号在 MLP |
| qwen35_9b | e41_qwen35_reciprocal_bad390032_valid390031 | mlp | 4 | 0.250 | -0.062 | 1/8 | MLP carries the strongest local process signal / 最强局部过程信号在 MLP |
| qwen35_9b | e41_qwen35_zh_exclusive_interval_bad390112_valid390111 | mlp | 12 | 0.375 | -0.062 | 3/8 | MLP carries the strongest local process signal / 最强局部过程信号在 MLP |
| qwen3_14b_base | e41_qwen14_each_vs_total_bad390062_valid390061 | self_attn | 20 | 0.125 | -0.250 | 1/10 | attention output also carries a weak local signal / attention 输出也有弱局部信号 |
| qwen3_14b_base | e41_qwen14_prob_without_replacement_bad390052_valid390051 | mlp | 12 | 0.125 | -0.375 | 2/10 | MLP carries the strongest local process signal / 最强局部过程信号在 MLP |
| qwen3_14b_base | e41_qwen14_range_vs_average_bad390012_valid390011 | mlp | 8 | 0.125 | 0.000 | 0/10 | MLP carries the strongest local process signal / 最强局部过程信号在 MLP |
| qwen3_14b_base | e41_qwen14_zh_exclusive_interval_bad390112_valid390111 | mlp | 20 | 0.500 | -0.250 | 8/10 | MLP carries the strongest local process signal / 最强局部过程信号在 MLP |

## Interpretation / 解释

- Single-module effects are much smaller than E40 residual effects. / 单模块效应明显小于 E40 residual 效应。
- The strongest clean effects usually appear in MLP outputs, especially for Qwen3.5-9B and the Chinese exclusive-interval pair in Qwen14. / 最强干净效应通常出现在 MLP 输出，尤其是 Qwen3.5-9B 以及 Qwen14 的中文严格区间 pair。
- This supports a distributed residual-state story with MLP participation, not a single-module or single-head circuit. / 这支持“分布式 residual state + MLP 参与”的故事，而不是单模块或单头 circuit。
- For a top-conference paper, the next mechanistic step should test whether these MLP effects are reusable across paraphrases and whether ablating them changes final Yes/No decisions, rather than merely reporting patch deltas. / 如果要达到顶会论文标准，下一步机制实验应测试这些 MLP 效应是否跨改写复用，以及消融它们是否改变最终 Yes/No 决策，而不只是报告 patch delta。
