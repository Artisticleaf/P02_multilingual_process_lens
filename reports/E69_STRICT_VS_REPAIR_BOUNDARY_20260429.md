# E69 Strict vs Repair-Aware Boundary / E69 严格 trace-selection 与修复口径边界（2026-04-29）

- Result / 结果：`results/E69_strict_vs_repair_boundary/e69_strict_vs_repair_boundary.json`
- Audit / 审计：`reports/E69_STRICT_VS_REPAIR_BOUNDARY_AUDIT_20260429.json`
- Plain language / 说人话：我们现在要非常诚实地区分两件事：一条 trace 里出现了错误局部步骤，和这条 trace 后面有没有把错误纠正回来。前者对应严格过程筛选，后者对应 repair-aware 阅读。

## Overall / 总体

| strict ACPI rows | explicit repair/override | no clear repair marker | error span found in text |
|---:|---:|---:|---:|
| 78 | 55 (0.705) | 23 (0.295) | 26 (0.333) |

## By Dataset / 按数据集

| dataset | strict ACPI | explicit repair/override | no clear repair marker |
|---|---:|---:|---:|
| `E42` | 12 | 9 (0.750) | 3 (0.250) |
| `E54` | 18 | 14 (0.778) | 4 (0.222) |
| `E61` | 48 | 32 (0.667) | 16 (0.333) |

## Interpretation / 解释

- Strict claim / 严格主张：E42/E54/E61 的 invalid-correct rows 仍然是 strict process-invalid，因为可见 trace 中出现了错误数学/语义/执行断言。严格过程监督、可审计证明、教材解答筛选等场景确实会要求这样的 trace 被拒绝。 / These rows remain strict process-invalid because a visible false local assertion appears in the trace.
- Repair-aware boundary / 修复口径边界：很多 controlled trace 也包含后续纠正或覆盖语句；如果某个 verifier 的目标是“最终保留下来的推理是否正确”，它接受这些 trace 并不一定是纯失败。 / Many controlled traces also contain later corrections; a repair-aware verifier may accept them for a different objective.
- Paper wording / 论文表述：主文应使用 `strict trace-selection risk`，并单独报告 E57 的 `unrepaired ACPI`。不能把所有 controlled strict-invalid examples 都说成“未修复乱推碰巧对”。 / The paper should say strict trace-selection risk and separately report unrepaired ACPI; do not imply all controlled examples are unrepaired.
- Why this still matters / 为什么仍重要：训练数据筛选、过程奖励模型和可解释 verifier 经常要求每个可见步骤都可靠；一个 false step 即使后来被改正，也会污染可监督过程数据和 sibling/pointwise 选择目标。 / This still matters because process-supervision filters often require every visible step to be reliable.

## Examples / 示例

| dataset | task | error span | repair markers |
|---|---|---|---|
| `E42` | `mean_vs_median` | `The mean is the middle value of the ordered list, so it is 4` | `still` |
| `E42` | `range_vs_average` | `The range is the average of the numbers` | `But, for the requested` |
| `E42` | `coefficient_vs_exponent` | `The coefficient is the exponent 3` | `NA` |
| `E42` | `reciprocal_vs_additive_inverse` | `The reciprocal means the additive inverse, -4` | `NA` |
| `E42` | `percent_increase_vs_percent_of` | `A 20% increase means the new price is 20% of the original` | `Still` |
| `E42` | `prob_without_replacement` | `Without replacement means the first ball is put back before the second draw` | `Then using` |
| `E42` | `each_vs_total` | `each student read 24 pages` | `NA` |
| `E42` | `log_base_argument` | `The base is 8 and the argument is 2` | `Using the actual` |
| `E42` | `round_vs_truncate` | `Nearest tenth means drop all later digits, so 4.6` | `But` |
| `E42` | `zh_perimeter_vs_area` | `周长就是面积` | `可是, 应当` |

## Audit / 审计

- PASS: E42 data exists — data/processed/e42_e39_objective_focus_20260428.jsonl
- PASS: E54 data exists — data/processed/e54_parameterized_no_leak_generalization_20260428.jsonl
- PASS: E61 data exists — data/processed/e61_language_error_grid_20260429.jsonl
