# E68 Expanded Filter Amplification / E68 扩展筛选器放大模拟（2026-04-29）

- Result / 结果：`results/E68_filter_amplification_expanded/e68_filter_amplification_expanded.json`
- Audit / 审计：`reports/E68_FILTER_AMPLIFICATION_EXPANDED_AUDIT_20260429.json`
- Plain language / 说人话：如果一个数据管线只保留“答案对”或让模型单独回答 Yes/No，它会留下多少严格过程错误？E68 把不同 filter 放在同一个 balanced valid/invalid pool 上比较。

## Aggregate / 聚合

| slice | models | mean strict ACPI retention | mean valid retention | accepted invalid share |
|---|---:|---:|---:|---:|
| `E60::answer_blind_yes_no` | 4 | 0.183 | 0.975 | 0.157 |
| `E60::careful_sibling_comparison` | 4 | 0.075 | 0.925 | 0.075 |
| `E60::careful_yes_no` | 4 | 0.158 | 0.975 | 0.134 |
| `E60::locate_then_judge_yes_no` | 4 | 0.208 | 0.992 | 0.165 |
| `E60::outcome_only_final_correct` | 4 | 1.000 | 1.000 | 0.500 |
| `E60::plain_yes_no` | 4 | 0.575 | 0.992 | 0.366 |
| `E60::sibling_comparison` | 4 | 0.117 | 0.883 | 0.117 |
| `E61::answer_blind_yes_no` | 4 | 0.099 | 0.885 | 0.095 |
| `E61::careful_sibling_comparison` | 4 | 0.086 | 0.914 | 0.086 |
| `E61::careful_yes_no` | 4 | 0.161 | 0.906 | 0.148 |
| `E61::locate_then_judge_yes_no` | 4 | 0.182 | 0.896 | 0.160 |
| `E61::outcome_only_final_correct` | 4 | 1.000 | 1.000 | 0.500 |
| `E61::plain_yes_no` | 4 | 0.438 | 0.953 | 0.315 |
| `E61::sibling_comparison` | 4 | 0.125 | 0.875 | 0.125 |

## Model-Level Rows / 模型级结果

| exp | model | objective | type | strict ACPI retention | valid retention | accepted invalid share |
|---|---|---|---|---:|---:|---:|
| E60 | `gemma4_26b_a4b_it` | `outcome_only_final_correct` | outcome_only | 1.000 | 1.000 | 0.500 |
| E60 | `gemma4_26b_a4b_it` | `answer_blind_yes_no` | pointwise | 0.200 | 0.967 | 0.171 |
| E60 | `gemma4_26b_a4b_it` | `careful_yes_no` | pointwise | 0.300 | 0.967 | 0.237 |
| E60 | `gemma4_26b_a4b_it` | `locate_then_judge_yes_no` | pointwise | 0.233 | 0.967 | 0.194 |
| E60 | `gemma4_26b_a4b_it` | `plain_yes_no` | pointwise | 0.500 | 0.967 | 0.341 |
| E60 | `gemma4_26b_a4b_it` | `careful_sibling_comparison` | contrastive | 0.000 | 1.000 | 0.000 |
| E60 | `gemma4_26b_a4b_it` | `sibling_comparison` | contrastive | 0.000 | 1.000 | 0.000 |
| E60 | `gemma4_31b_it` | `outcome_only_final_correct` | outcome_only | 1.000 | 1.000 | 0.500 |
| E60 | `gemma4_31b_it` | `answer_blind_yes_no` | pointwise | 0.233 | 1.000 | 0.189 |
| E60 | `gemma4_31b_it` | `careful_yes_no` | pointwise | 0.133 | 1.000 | 0.118 |
| E60 | `gemma4_31b_it` | `locate_then_judge_yes_no` | pointwise | 0.133 | 1.000 | 0.118 |
| E60 | `gemma4_31b_it` | `plain_yes_no` | pointwise | 0.600 | 1.000 | 0.375 |
| E60 | `gemma4_31b_it` | `careful_sibling_comparison` | contrastive | 0.000 | 1.000 | 0.000 |
| E60 | `gemma4_31b_it` | `sibling_comparison` | contrastive | 0.000 | 1.000 | 0.000 |
| E60 | `glm47_flash_candidate` | `outcome_only_final_correct` | outcome_only | 1.000 | 1.000 | 0.500 |
| E60 | `glm47_flash_candidate` | `answer_blind_yes_no` | pointwise | 0.167 | 1.000 | 0.143 |
| E60 | `glm47_flash_candidate` | `careful_yes_no` | pointwise | 0.167 | 0.967 | 0.147 |
| E60 | `glm47_flash_candidate` | `locate_then_judge_yes_no` | pointwise | 0.400 | 1.000 | 0.286 |
| E60 | `glm47_flash_candidate` | `plain_yes_no` | pointwise | 0.600 | 1.000 | 0.375 |
| E60 | `glm47_flash_candidate` | `careful_sibling_comparison` | contrastive | 0.300 | 0.700 | 0.300 |
| E60 | `glm47_flash_candidate` | `sibling_comparison` | contrastive | 0.467 | 0.533 | 0.467 |
| E60 | `qwen35_27b` | `outcome_only_final_correct` | outcome_only | 1.000 | 1.000 | 0.500 |
| E60 | `qwen35_27b` | `answer_blind_yes_no` | pointwise | 0.133 | 0.933 | 0.125 |
| E60 | `qwen35_27b` | `careful_yes_no` | pointwise | 0.033 | 0.967 | 0.033 |
| E60 | `qwen35_27b` | `locate_then_judge_yes_no` | pointwise | 0.067 | 1.000 | 0.062 |
| E60 | `qwen35_27b` | `plain_yes_no` | pointwise | 0.600 | 1.000 | 0.375 |
| E60 | `qwen35_27b` | `careful_sibling_comparison` | contrastive | 0.000 | 1.000 | 0.000 |
| E60 | `qwen35_27b` | `sibling_comparison` | contrastive | 0.000 | 1.000 | 0.000 |
| E61 | `gemma4_26b_a4b_it` | `outcome_only_final_correct` | outcome_only | 1.000 | 1.000 | 0.500 |
| E61 | `gemma4_26b_a4b_it` | `answer_blind_yes_no` | pointwise | 0.167 | 0.833 | 0.167 |
| E61 | `gemma4_26b_a4b_it` | `careful_yes_no` | pointwise | 0.312 | 0.812 | 0.278 |
| E61 | `gemma4_26b_a4b_it` | `locate_then_judge_yes_no` | pointwise | 0.333 | 0.875 | 0.276 |
| E61 | `gemma4_26b_a4b_it` | `plain_yes_no` | pointwise | 0.438 | 0.854 | 0.339 |
| E61 | `gemma4_26b_a4b_it` | `careful_sibling_comparison` | contrastive | 0.042 | 0.958 | 0.042 |
| E61 | `gemma4_26b_a4b_it` | `sibling_comparison` | contrastive | 0.031 | 0.969 | 0.031 |
| E61 | `gemma4_31b_it` | `outcome_only_final_correct` | outcome_only | 1.000 | 1.000 | 0.500 |
| E61 | `gemma4_31b_it` | `answer_blind_yes_no` | pointwise | 0.167 | 1.000 | 0.143 |
| E61 | `gemma4_31b_it` | `careful_yes_no` | pointwise | 0.146 | 1.000 | 0.127 |
| E61 | `gemma4_31b_it` | `locate_then_judge_yes_no` | pointwise | 0.146 | 0.938 | 0.135 |
| E61 | `gemma4_31b_it` | `plain_yes_no` | pointwise | 0.458 | 1.000 | 0.314 |
| E61 | `gemma4_31b_it` | `careful_sibling_comparison` | contrastive | 0.000 | 1.000 | 0.000 |
| E61 | `gemma4_31b_it` | `sibling_comparison` | contrastive | 0.000 | 1.000 | 0.000 |
| E61 | `glm47_flash_candidate` | `outcome_only_final_correct` | outcome_only | 1.000 | 1.000 | 0.500 |
| E61 | `glm47_flash_candidate` | `answer_blind_yes_no` | pointwise | 0.021 | 0.833 | 0.024 |
| E61 | `glm47_flash_candidate` | `careful_yes_no` | pointwise | 0.083 | 0.958 | 0.080 |
| E61 | `glm47_flash_candidate` | `locate_then_judge_yes_no` | pointwise | 0.208 | 0.938 | 0.182 |
| E61 | `glm47_flash_candidate` | `plain_yes_no` | pointwise | 0.479 | 1.000 | 0.324 |
| E61 | `glm47_flash_candidate` | `careful_sibling_comparison` | contrastive | 0.302 | 0.698 | 0.302 |
| E61 | `glm47_flash_candidate` | `sibling_comparison` | contrastive | 0.469 | 0.531 | 0.469 |
| E61 | `qwen35_27b` | `outcome_only_final_correct` | outcome_only | 1.000 | 1.000 | 0.500 |
| E61 | `qwen35_27b` | `answer_blind_yes_no` | pointwise | 0.042 | 0.875 | 0.045 |
| E61 | `qwen35_27b` | `careful_yes_no` | pointwise | 0.104 | 0.854 | 0.109 |
| E61 | `qwen35_27b` | `locate_then_judge_yes_no` | pointwise | 0.042 | 0.833 | 0.048 |
| E61 | `qwen35_27b` | `plain_yes_no` | pointwise | 0.375 | 0.958 | 0.281 |
| E61 | `qwen35_27b` | `careful_sibling_comparison` | contrastive | 0.000 | 1.000 | 0.000 |
| E61 | `qwen35_27b` | `sibling_comparison` | contrastive | 0.000 | 1.000 | 0.000 |

## Interpretation / 解释

- Outcome-only is maximally risky in controlled ACPI pools: it keeps all answer-correct invalid traces by definition. / 只看答案在受控 ACPI 池中最危险：它按定义保留所有答案正确但过程有错的 trace。
- Plain pointwise Yes/No keeps a large fraction of strict ACPI while also keeping nearly all valid traces; this is the core trace-selection risk. / 普通单点 Yes/No 会保留大量 strict ACPI，同时几乎保留所有 valid trace，这是核心筛选风险。
- Careful and answer-blind pointwise filters reduce risk but do not define a universal fix. / 仔细检查和 answer-blind 会降风险，但不是通用修复。
- Sibling filters suppress strict ACPI strongly for core P0, but GLM makes the expanded-P0 story more nuanced because A/B contrastive discrimination can itself be weak. / sibling 对核心 P0 压制很强，但 GLM 说明扩展 P0 中 A/B 对比判别本身也可能弱。

## Audit / 审计

- PASS: E60 input gemma4_26b_a4b_it_e60_objective_ladder_chat.json — results/E60_objective_ladder/gemma4_26b_a4b_it_e60_objective_ladder_chat.json
- PASS: E60 input gemma4_31b_it_e60_objective_ladder_chat.json — results/E60_objective_ladder/gemma4_31b_it_e60_objective_ladder_chat.json
- PASS: E60 input glm47_flash_candidate_e60_objective_ladder_chat.json — results/E60_objective_ladder/glm47_flash_candidate_e60_objective_ladder_chat.json
- PASS: E60 input qwen35_27b_e60_objective_ladder_chat.json — results/E60_objective_ladder/qwen35_27b_e60_objective_ladder_chat.json
- PASS: E61 input gemma4_26b_a4b_it_e61_language_error_grid_chat.json — results/E61_language_error_grid/gemma4_26b_a4b_it_e61_language_error_grid_chat.json
- PASS: E61 input gemma4_31b_it_e61_language_error_grid_chat.json — results/E61_language_error_grid/gemma4_31b_it_e61_language_error_grid_chat.json
- PASS: E61 input glm47_flash_candidate_e61_language_error_grid_chat.json — results/E61_language_error_grid/glm47_flash_candidate_e61_language_error_grid_chat.json
- PASS: E61 input qwen35_27b_e61_language_error_grid_chat.json — results/E61_language_error_grid/qwen35_27b_e61_language_error_grid_chat.json
