# E65 Mechanistic Layer Sweep / E65 机制层扫描（2026-04-29）

- Audit / 审计：`reports/E65_MECHANISTIC_LAYER_SWEEP_AUDIT_20260429.json`
- Plain language / 说人话：E65 不再只看第 16 层，而是在 E61 的 96 条多语言/多错误类型 trace 上扫描每一层 final-token residual，看哪一层最能线性区分 strict valid 与 strict invalid。

## Best Layer Summary / 最佳层汇总

| model | layers | items | best layer | LOTO accuracy | mean valid score | mean invalid score |
|---|---:|---:|---:|---:|---:|---:|
| `qwen35_27b` | 65 | 96 | 34 | 1.000 | 5.699 | -5.676 |
| `gemma4_31b_it` | 61 | 96 | 34 | 1.000 | 8.715 | -8.683 |
| `gemma4_26b_a4b_it` | 31 | 96 | 17 | 0.927 | 8.297 | -8.250 |
| `glm47_flash_candidate` | 48 | 96 | 27 | 0.979 | 1.869 | -1.851 |

## Interpretation / 解释

- Hidden evidence is broad / 隐藏证据更广：四个 P0/扩展 P0 模型在 E61 上都存在可线性读出的 strict process-validity residual 方向，最佳层准确率从 0.927 到 1.000。 / All four models show linearly recoverable strict process-validity directions on E61, with best-layer accuracy from 0.927 to 1.000.
- GLM is especially informative / GLM 特别有信息：GLM 的 A/B sibling 行为较弱，但 layer 27 residual probe 达到 0.979。这说明它并非没有过程有效性证据，而是输出决策/对比标签使用没有稳定调用这些证据。 / GLM has weak A/B sibling behavior but a 0.979 residual probe at layer 27, so the evidence exists internally but is not reliably used by the output decision.
- Mechanism boundary / 机制边界：E65 是 representation-level diagnostic，不是完整电路；它还没有说明哪些 head/neuron 写入该方向，也没有做路径特异 causal mediation。 / E65 is a representation diagnostic, not a full circuit; it does not identify heads/neurons or prove path-specific mediation.
- Next mechanism step / 下一步机制：E66/E67-style work should combine best-layer directions with output-head/label-bias mediation and span-local patching. / Next, combine best-layer directions with output-head/label-bias mediation and span-local patching.

## Audit / 审计

- PASS: qwen35_27b E65 result exists — results/E65_mechanistic_layer_sweep/qwen35_27b_e65_e61_layer_sweep.json
- PASS: qwen35_27b model key — qwen35_27b
- PASS: qwen35_27b dataset E61 — E61
- PASS: qwen35_27b no prompt leakage labels — 0
- PASS: gemma4_31b_it E65 result exists — results/E65_mechanistic_layer_sweep/gemma4_31b_it_e65_e61_layer_sweep.json
- PASS: gemma4_31b_it model key — gemma4_31b_it
- PASS: gemma4_31b_it dataset E61 — E61
- PASS: gemma4_31b_it no prompt leakage labels — 0
- PASS: gemma4_26b_a4b_it E65 result exists — results/E65_mechanistic_layer_sweep/gemma4_26b_a4b_it_e65_e61_layer_sweep.json
- PASS: gemma4_26b_a4b_it model key — gemma4_26b_a4b_it
- PASS: gemma4_26b_a4b_it dataset E61 — E61
- PASS: gemma4_26b_a4b_it no prompt leakage labels — 0
- PASS: glm47_flash_candidate E65 result exists — results/E65_mechanistic_layer_sweep/glm47_flash_candidate_e65_e61_layer_sweep.json
- PASS: glm47_flash_candidate model key — glm47_flash_candidate
- PASS: glm47_flash_candidate dataset E61 — E61
- PASS: glm47_flash_candidate no prompt leakage labels — 0
