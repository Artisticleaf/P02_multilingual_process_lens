# E36 Inequality Boundary Deep Dive / E36 不等式边界样例深挖

Created / 创建时间: 2026-04-27T23:21:11

目的：解释 E31 里 `between 3 and 7, inclusive` 这个边界样例为什么容易被 absolute verifier 接受、同时 residual span patch 又偏弱。这个坏 trace 不是纯错到底：它先写了一个错误/歧义的表层短语，随后又列出了正确集合 `4, 5, 6, 7`，所以它可能把错误证据和纠正证据混在同一条 trace 里。

判读规则：`valid->bad` 为正且 `bad->valid` 为负，说明 support/error span 的隐藏表示能按预期推动 verifier margin；如果只有后续正确列表有效，而完整错误条件短语无效，说明模型更依赖下游修正/答案一致性而不是局部语义错误。

## qwen35_9b

| variant / 变体 | clean? / 是否方向干净 | best layer / 最强层 | valid->bad | bad->valid | base valid | base bad | bad span / 坏 span | valid span / 好 span |
|---|---:|---:|---:|---:|---:|---:|---|---|
| 后续正确列表 | True | 18 | 0.062 | -0.062 | 3.438 | 2.750 | 4, 5, 6, and 7 | 4, 5, 6, and 7 |
| 错误短语+后续修正子句 | True | 8 | 0.188 | -2.563 | 3.438 | 2.750 | between 3 and 7, inclusive. Start by listing the integers greater than 3 and no more than 7 | greater than 3 and no more than 7, so the integers are 4, 5, 6, and 7 |
| 完整条件短语 | True | 8 | 0.188 | -0.688 | 3.438 | 2.750 | between 3 and 7, inclusive | greater than 3 and no more than 7 |
| 下界短语 | True | 14 | 0.062 | -0.250 | 3.438 | 2.750 | between 3 and 7 | greater than 3 |
| 上界/端点短语 | True | 4 | 0.125 | -1.812 | 3.438 | 2.750 | inclusive | no more than 7 |

### 直接解释 / Plain-language interpretation

- 5 个 span 变体中有 5 个出现方向干净的 patch 信号；这不是全无信号，而是局部语义错误的信号不稳定。
- 最强变体是 `错误短语+后续修正子句`，说明 verifier 隐藏状态最容易被这段 span 的表示推动，而不一定是最早的错误短语本身。
- 如果 `完整条件短语` 弱、`错误短语+后续修正子句` 或 `后续正确列表` 强，边界解释就是：坏 trace 同时携带错误 phrase 和正确枚举，absolute verifier 被正确枚举/最终答案拉向接受。

## qwen3_14b_base

| variant / 变体 | clean? / 是否方向干净 | best layer / 最强层 | valid->bad | bad->valid | base valid | base bad | bad span / 坏 span | valid span / 好 span |
|---|---:|---:|---:|---:|---:|---:|---|---|
| 后续正确列表 | False | 6 | -2.000 | -2.500 | 2.625 | 2.500 | 4, 5, 6, and 7 | 4, 5, 6, and 7 |
| 错误短语+后续修正子句 | True | 20 | 0.250 | -0.750 | 2.625 | 2.500 | between 3 and 7, inclusive. Start by listing the integers greater than 3 and no more than 7 | greater than 3 and no more than 7, so the integers are 4, 5, 6, and 7 |
| 完整条件短语 | True | 18 | 0.250 | -0.250 | 2.625 | 2.500 | between 3 and 7, inclusive | greater than 3 and no more than 7 |
| 下界短语 | False | 22 | 0.375 | 0.000 | 2.625 | 2.500 | between 3 and 7 | greater than 3 |
| 上界/端点短语 | True | 12 | 0.125 | -1.500 | 2.625 | 2.500 | inclusive | no more than 7 |

### 直接解释 / Plain-language interpretation

- 5 个 span 变体中有 3 个出现方向干净的 patch 信号；这不是全无信号，而是局部语义错误的信号不稳定。
- 最强变体是 `上界/端点短语`，说明 verifier 隐藏状态最容易被这段 span 的表示推动，而不一定是最早的错误短语本身。
- 如果 `完整条件短语` 弱、`错误短语+后续修正子句` 或 `后续正确列表` 强，边界解释就是：坏 trace 同时携带错误 phrase 和正确枚举，absolute verifier 被正确枚举/最终答案拉向接受。
