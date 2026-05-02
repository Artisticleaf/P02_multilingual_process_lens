# E63 GLM Expanded-P0 Replication / E63 GLM 扩展 P0 复现（2026-04-29）

- Audit / 审计：`reports/E63_GLM_EXPANDED_P0_REPLICATION_AUDIT_20260429.json`
- Model / 模型：`glm47_flash_candidate` (`GLM-4.7-Flash`), admitted by E62. / 由 E62 准入的扩展 P0 模型。
- Plain language / 说人话：GLM 证明“单条 trace 的 Yes/No 过程审查会过度接受 ACPI”这个现象能跨到第三个模型家族；但它也提醒我们，A/B sibling 不是无条件 oracle，因为这个模型有明显的 A/B 标签或位置偏置。

## Main Metrics / 主结果

| experiment | plain pointwise ACPI accept | valid accept | stricter pointwise best | sibling accuracy | careful sibling accuracy | note |
|---|---:|---:|---:|---:|---:|---|
| E42 controlled parity | 0.417 | 1.000 | NA | 0.625 | NA | E42 A/B pred_A_rate=0.875 |
| E60 objective ladder | 0.600 | 1.000 | answer-blind/careful=0.167/0.167 | 0.533 | 0.700 | A/B bias remains, especially plain sibling |
| E61 language/error grid | 0.479 | 1.000 | answer-blind/careful=0.021/0.083 | 0.531 | 0.698 | broad grid reproduces pointwise risk |

## Contrastive Label/Position Bias / 对比式标签/位置偏置

| source | objective | row accuracy | pred_A_rate | pairs both orders correct | one-order-only pairs | pair summed target-margin > 0 |
|---|---|---:|---:|---:|---:|---:|
| E42 | contrastive | 0.625 | 0.875 | 3/12 | 9/12 | 9/12 |
| E60 | sibling_comparison | 0.533 | 0.833 | 4/30 | 24/30 | 18/30 |
| E60 | careful_sibling_comparison | 0.700 | 0.633 | 13/30 | 16/30 | 20/30 |
| E61 | sibling_comparison | 0.531 | 0.885 | 3/48 | 45/48 | 30/48 |
| E61 | careful_sibling_comparison | 0.698 | 0.510 | 21/48 | 25/48 | 36/48 |

- Interpretation / 解释：如果模型真正稳定地比较过程，bad_A 和 bad_B 两个顺序都应选中 invalid trace；GLM 大量出现“只有 bad_A 正确、bad_B 错误”的情况，说明输出头/标签先验或位置先验会压过过程信号。 / If sibling comparison were fully reliable, both orders would be correct. GLM often gets only one order right, so label/position priors can overpower process evidence.
- Claim update / 主张更新：E63 支持 `absolute pointwise over-acceptance` 与 `stricter process prompts reduce but do not eliminate risk`；同时要求论文把 sibling 写成“强诊断但需标签/位置校准”，不能写成所有模型上的天然 oracle。 / E63 supports pointwise over-acceptance and objective-ladder mitigation, but sibling must be described as a strong diagnostic requiring label/position calibration, not as an unconditional oracle.

## Mechanism Smoke / 机制 smoke

- E55 layer-16 residual probe accuracy: absolute=0.708, contrastive=0.667. / E55 第 16 层 residual 探针有弱到中等过程信号。
- E56 layer-16 component probe accuracy: residual=0.708, token-mixer=0.750, MLP=0.667. / E56 第 16 层组件探针显示 token-mixer/residual/MLP 都有一些线性可读信息。
- Boundary / 边界：GLM 的第 16 层 patch 效应弱且不稳定，不能作为强因果机制证据；后续 E65/E66 应做层扫描和路径特异中介，寻找是否存在更强层位或是否确实是 GLM 的机制边界。 / Layer-16 patching is weak and unstable; E65/E66 should test whether stronger layers/path-specific mediation exist.

## Audit / 审计

- PASS: e42 output exists — results/E42_official_template_parity/glm47_flash_candidate_e42_official_template_parity_chat.json
- PASS: e60 output exists — results/E60_objective_ladder/glm47_flash_candidate_e60_objective_ladder_chat.json
- PASS: e61 output exists — results/E61_language_error_grid/glm47_flash_candidate_e61_language_error_grid_chat.json
- PASS: e55 output exists — results/E55_residual_to_logit_mediation/glm47_flash_candidate_e55_residual_to_logit_mediation.json
- PASS: e56 output exists — results/E56_component_decomposition/glm47_flash_candidate_e56_component_decomposition.json
- PASS: e42 model key — glm47_flash_candidate
- PASS: e42 uses official chat template — True
- PASS: e42 prompt format — official_if_chat
- PASS: e42 local files only — True
- PASS: e60 model key — glm47_flash_candidate
- PASS: e60 uses official chat template — True
- PASS: e60 prompt format — official_if_chat
- PASS: e60 local files only — True
- PASS: e61 model key — glm47_flash_candidate
- PASS: e61 uses official chat template — True
- PASS: e61 prompt format — official_if_chat
- PASS: e61 local files only — True
- PASS: e55 model key — glm47_flash_candidate
- PASS: e55 uses official chat template — True
- PASS: e55 prompt format — official_if_chat
- PASS: e55 local files only — True
- PASS: e56 model key — glm47_flash_candidate
- PASS: e56 uses official chat template — True
- PASS: e56 prompt format — official_if_chat
- PASS: e56 local files only — True
- PASS: e60 leakage gold_label_in_prompt_rows — 0
- PASS: e60 leakage known_error_span_annotation_in_prompt_rows — 0
- PASS: e60 leakage manual_correction_in_prompt_rows — 0
- PASS: e61 leakage gold_label_in_prompt_rows — 0
- PASS: e61 leakage known_error_span_annotation_in_prompt_rows — 0
- PASS: e61 leakage manual_correction_in_prompt_rows — 0
- PASS: e61 leakage known_error_span_in_prompt_rows — 0
