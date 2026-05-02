# E66 Contrastive Label Calibration / E66 对比式标签校准（2026-04-29）

- Result / 结果：`results/E66_contrastive_label_calibration/e66_contrastive_label_calibration.json`
- Audit / 审计：`reports/E66_CONTRASTIVE_LABEL_CALIBRATION_AUDIT_20260429.json`
- Plain language / 说人话：sibling comparison 让模型比较 A/B 两条 trace，但 A/B 字母本身也可能有先验。E66 把“模型懂不懂哪条过程错”和“输出头偏爱 A 还是 B”拆开看。

## Calibration Table / 校准表

| exp | model | objective | raw acc | pred_A | global A-B bias | calibrated row acc | order-canceled pair acc | both/one/none pairs |
|---|---|---|---:|---:|---:|---:|---:|---|
| E60 | `gemma4_26b_a4b_it` | `careful_sibling_comparison` | 1.000 | 0.500 | 0.994 | 1.000 | 1.000 | 30/0/0 |
| E60 | `gemma4_26b_a4b_it` | `sibling_comparison` | 1.000 | 0.500 | 1.287 | 1.000 | 1.000 | 30/0/0 |
| E60 | `gemma4_31b_it` | `careful_sibling_comparison` | 1.000 | 0.500 | -1.861 | 1.000 | 1.000 | 30/0/0 |
| E60 | `gemma4_31b_it` | `sibling_comparison` | 1.000 | 0.500 | -1.671 | 1.000 | 1.000 | 30/0/0 |
| E60 | `glm47_flash_candidate` | `careful_sibling_comparison` | 0.700 | 0.633 | -0.087 | 0.617 | 0.667 | 13/16/1 |
| E60 | `glm47_flash_candidate` | `sibling_comparison` | 0.533 | 0.833 | 0.579 | 0.650 | 0.600 | 4/24/2 |
| E60 | `qwen35_27b` | `careful_sibling_comparison` | 1.000 | 0.500 | 0.919 | 1.000 | 1.000 | 30/0/0 |
| E60 | `qwen35_27b` | `sibling_comparison` | 1.000 | 0.500 | 0.219 | 1.000 | 1.000 | 30/0/0 |
| E61 | `gemma4_26b_a4b_it` | `careful_sibling_comparison` | 0.958 | 0.542 | 2.091 | 0.948 | 0.958 | 44/4/0 |
| E61 | `gemma4_26b_a4b_it` | `sibling_comparison` | 0.969 | 0.510 | 1.316 | 0.958 | 0.979 | 45/3/0 |
| E61 | `gemma4_31b_it` | `careful_sibling_comparison` | 1.000 | 0.500 | -0.556 | 1.000 | 1.000 | 48/0/0 |
| E61 | `gemma4_31b_it` | `sibling_comparison` | 1.000 | 0.500 | -1.941 | 1.000 | 1.000 | 48/0/0 |
| E61 | `glm47_flash_candidate` | `careful_sibling_comparison` | 0.698 | 0.510 | -0.121 | 0.667 | 0.750 | 21/25/2 |
| E61 | `glm47_flash_candidate` | `sibling_comparison` | 0.531 | 0.885 | 0.762 | 0.635 | 0.625 | 3/45/0 |
| E61 | `qwen35_27b` | `careful_sibling_comparison` | 1.000 | 0.500 | 0.691 | 1.000 | 1.000 | 48/0/0 |
| E61 | `qwen35_27b` | `sibling_comparison` | 1.000 | 0.500 | 0.349 | 1.000 | 1.000 | 48/0/0 |

## Interpretation / 解释

- Core P0 boundary / 核心 P0 边界：Qwen35-27B、Gemma4-31B 和多数 Gemma4-26B-A4B 条件下，raw sibling 已经接近或达到 1.0；校准不是主因。 / For the core P0 models, raw sibling is already near-perfect, so calibration is not the main explanation.
- GLM boundary / GLM 边界：GLM-4.7-Flash 的 raw sibling 明显受 A/B 或位置偏置影响；简单全局校准只能小幅改善，order-canceled pair accuracy 也仍明显低于核心 P0。这说明 GLM 不只是输出格式坏，而是 contrastive process discrimination 本身也更弱。 / GLM has strong A/B or position bias; simple calibration helps only partly, so contrastive process discrimination is weaker than in core P0.
- Scientific update / 科学更新：我们的 claim 应把 sibling comparison 写成“通常更强、能暴露很多 absolute 没用好的过程信号”，而不是“所有模型上必然完美”。这反而给论文增加一个机制点：verifier 决策还会被输出头标签先验重整。 / The claim should say sibling is usually stronger and exposes many underused process signals, not that it is always perfect; this adds a mechanism point about output-head label priors.

## Audit / 审计

- PASS: input exists gemma4_26b_a4b_it_e60_objective_ladder_chat.json — results/E60_objective_ladder/gemma4_26b_a4b_it_e60_objective_ladder_chat.json
- PASS: input exists gemma4_31b_it_e60_objective_ladder_chat.json — results/E60_objective_ladder/gemma4_31b_it_e60_objective_ladder_chat.json
- PASS: input exists glm47_flash_candidate_e60_objective_ladder_chat.json — results/E60_objective_ladder/glm47_flash_candidate_e60_objective_ladder_chat.json
- PASS: input exists qwen35_27b_e60_objective_ladder_chat.json — results/E60_objective_ladder/qwen35_27b_e60_objective_ladder_chat.json
- PASS: input exists gemma4_26b_a4b_it_e61_language_error_grid_chat.json — results/E61_language_error_grid/gemma4_26b_a4b_it_e61_language_error_grid_chat.json
- PASS: input exists gemma4_31b_it_e61_language_error_grid_chat.json — results/E61_language_error_grid/gemma4_31b_it_e61_language_error_grid_chat.json
- PASS: input exists glm47_flash_candidate_e61_language_error_grid_chat.json — results/E61_language_error_grid/glm47_flash_candidate_e61_language_error_grid_chat.json
- PASS: input exists qwen35_27b_e61_language_error_grid_chat.json — results/E61_language_error_grid/qwen35_27b_e61_language_error_grid_chat.json
