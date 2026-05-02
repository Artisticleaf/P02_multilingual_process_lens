# E87 GLM Readout Intervention / GLM 读出干预诊断（2026-04-29）

- JSON: `results/E87_glm_readout_intervention/glm47_flash_candidate_e87_readout_intervention.json`
- Scope / 范围：不做新推理，读取 E84 的 GLM A/B logits、label-free margin 和 hidden margin。
- Plain language / 说人话：如果 GLM 真的看不出哪条 trace 有错，那么换任何读出方式都救不了；如果只是 A/B 标签读出有偏，那么去掉标签/顺序偏置后准确率会明显恢复。

| decision rule | n | accuracy | mean margin |
|---|---:|---:|---:|
| `raw_ab_single_order` | 96 | 0.542 | 0.214 |
| `global_bias_centered_ab` | 96 | 0.667 | 0.214 |
| `two_order_antisymmetric_ab` | 48 | 0.812 | 0.214 |
| `hidden_readout_replacement` | 48 | 1.000 | 2.729 |
| `label_free_two_pass_replacement` | 48 | 0.958 | 4.219 |

## Interpretation / 解释

- `raw_ab_single_order` is the ordinary one-shot A/B sibling decision. / `raw_ab_single_order` 是普通单次 A/B sibling 判断。
- `global_bias_centered_ab` subtracts the average A-minus-B prior from all rows. / `global_bias_centered_ab` 只减去全局 A/B 标签先验。
- `two_order_antisymmetric_ab` asks both orders and keeps the antisymmetric part, so stable A/B label bias cancels. / `two_order_antisymmetric_ab` 同一对 trace 交换顺序问两次，只保留反对称信号，从而抵消稳定标签偏置。
- `hidden_readout_replacement` uses the E84 residual validity margin instead of A/B label logits. / `hidden_readout_replacement` 不看 A/B 输出头，而看 E84 残差过程有效性 margin。
- `label_free_two_pass_replacement` checks each trace pointwise and compares No-Yes invalid scores. / `label_free_two_pass_replacement` 分别检查两条 trace，再比较 No-Yes invalid 分数。

Main scientific boundary / 科学边界：E87 证明的是 GLM 的主要失败位于读出/输出格式层面；它不声称已经定位到完整神经 circuit。
