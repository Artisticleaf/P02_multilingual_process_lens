# E70 Statistics and Audit Appendix / E70 统计与审计附录（2026-04-29）

- Result / 结果：`results/E70_statistics_audit_appendix/e70_statistics_audit_appendix.json`
- Audit / 审计：`reports/E70_STATISTICS_AUDIT_APPENDIX_AUDIT_20260429.json`
- Plain language / 说人话：E70 不再跑模型，而是给关键比例加置信区间，并检查 E61 结论是不是被某一个错误类型单独撑起来。

## Wilson Intervals / Wilson 区间

| exp | model | objective | metric | k/n | value | 95% CI |
|---|---|---|---|---:|---:|---|
| E60 | `gemma4_26b_a4b_it` | `answer_blind_yes_no` | strict_acpi_accept | 6/30 | 0.200 | [0.095, 0.373] |
| E60 | `gemma4_26b_a4b_it` | `careful_yes_no` | strict_acpi_accept | 9/30 | 0.300 | [0.167, 0.479] |
| E60 | `gemma4_26b_a4b_it` | `locate_then_judge_yes_no` | strict_acpi_accept | 7/30 | 0.233 | [0.118, 0.409] |
| E60 | `gemma4_26b_a4b_it` | `plain_yes_no` | strict_acpi_accept | 15/30 | 0.500 | [0.332, 0.668] |
| E60 | `gemma4_26b_a4b_it` | `careful_sibling_comparison` | sibling_accuracy | 60/60 | 1.000 | [0.940, 1.000] |
| E60 | `gemma4_26b_a4b_it` | `sibling_comparison` | sibling_accuracy | 60/60 | 1.000 | [0.940, 1.000] |
| E60 | `gemma4_31b_it` | `answer_blind_yes_no` | strict_acpi_accept | 7/30 | 0.233 | [0.118, 0.409] |
| E60 | `gemma4_31b_it` | `careful_yes_no` | strict_acpi_accept | 4/30 | 0.133 | [0.053, 0.297] |
| E60 | `gemma4_31b_it` | `locate_then_judge_yes_no` | strict_acpi_accept | 4/30 | 0.133 | [0.053, 0.297] |
| E60 | `gemma4_31b_it` | `plain_yes_no` | strict_acpi_accept | 18/30 | 0.600 | [0.423, 0.754] |
| E60 | `gemma4_31b_it` | `careful_sibling_comparison` | sibling_accuracy | 60/60 | 1.000 | [0.940, 1.000] |
| E60 | `gemma4_31b_it` | `sibling_comparison` | sibling_accuracy | 60/60 | 1.000 | [0.940, 1.000] |
| E60 | `glm47_flash_candidate` | `answer_blind_yes_no` | strict_acpi_accept | 5/30 | 0.167 | [0.073, 0.336] |
| E60 | `glm47_flash_candidate` | `careful_yes_no` | strict_acpi_accept | 5/30 | 0.167 | [0.073, 0.336] |
| E60 | `glm47_flash_candidate` | `locate_then_judge_yes_no` | strict_acpi_accept | 12/30 | 0.400 | [0.246, 0.577] |
| E60 | `glm47_flash_candidate` | `plain_yes_no` | strict_acpi_accept | 18/30 | 0.600 | [0.423, 0.754] |
| E60 | `glm47_flash_candidate` | `careful_sibling_comparison` | sibling_accuracy | 42/60 | 0.700 | [0.575, 0.801] |
| E60 | `glm47_flash_candidate` | `sibling_comparison` | sibling_accuracy | 32/60 | 0.533 | [0.409, 0.654] |
| E60 | `qwen35_27b` | `answer_blind_yes_no` | strict_acpi_accept | 4/30 | 0.133 | [0.053, 0.297] |
| E60 | `qwen35_27b` | `careful_yes_no` | strict_acpi_accept | 1/30 | 0.033 | [0.006, 0.167] |
| E60 | `qwen35_27b` | `locate_then_judge_yes_no` | strict_acpi_accept | 2/30 | 0.067 | [0.018, 0.213] |
| E60 | `qwen35_27b` | `plain_yes_no` | strict_acpi_accept | 18/30 | 0.600 | [0.423, 0.754] |
| E60 | `qwen35_27b` | `careful_sibling_comparison` | sibling_accuracy | 60/60 | 1.000 | [0.940, 1.000] |
| E60 | `qwen35_27b` | `sibling_comparison` | sibling_accuracy | 60/60 | 1.000 | [0.940, 1.000] |
| E61 | `gemma4_26b_a4b_it` | `answer_blind_yes_no` | strict_acpi_accept | 8/48 | 0.167 | [0.087, 0.296] |
| E61 | `gemma4_26b_a4b_it` | `careful_yes_no` | strict_acpi_accept | 15/48 | 0.312 | [0.199, 0.453] |
| E61 | `gemma4_26b_a4b_it` | `locate_then_judge_yes_no` | strict_acpi_accept | 16/48 | 0.333 | [0.217, 0.475] |
| E61 | `gemma4_26b_a4b_it` | `plain_yes_no` | strict_acpi_accept | 21/48 | 0.438 | [0.307, 0.577] |
| E61 | `gemma4_26b_a4b_it` | `careful_sibling_comparison` | sibling_accuracy | 92/96 | 0.958 | [0.898, 0.984] |
| E61 | `gemma4_26b_a4b_it` | `sibling_comparison` | sibling_accuracy | 93/96 | 0.969 | [0.912, 0.989] |
| E61 | `gemma4_31b_it` | `answer_blind_yes_no` | strict_acpi_accept | 8/48 | 0.167 | [0.087, 0.296] |
| E61 | `gemma4_31b_it` | `careful_yes_no` | strict_acpi_accept | 7/48 | 0.146 | [0.072, 0.272] |
| E61 | `gemma4_31b_it` | `locate_then_judge_yes_no` | strict_acpi_accept | 7/48 | 0.146 | [0.072, 0.272] |
| E61 | `gemma4_31b_it` | `plain_yes_no` | strict_acpi_accept | 22/48 | 0.458 | [0.326, 0.597] |
| E61 | `gemma4_31b_it` | `careful_sibling_comparison` | sibling_accuracy | 96/96 | 1.000 | [0.962, 1.000] |
| E61 | `gemma4_31b_it` | `sibling_comparison` | sibling_accuracy | 96/96 | 1.000 | [0.962, 1.000] |
| E61 | `glm47_flash_candidate` | `answer_blind_yes_no` | strict_acpi_accept | 1/48 | 0.021 | [0.004, 0.109] |
| E61 | `glm47_flash_candidate` | `careful_yes_no` | strict_acpi_accept | 4/48 | 0.083 | [0.033, 0.196] |
| E61 | `glm47_flash_candidate` | `locate_then_judge_yes_no` | strict_acpi_accept | 10/48 | 0.208 | [0.117, 0.343] |
| E61 | `glm47_flash_candidate` | `plain_yes_no` | strict_acpi_accept | 23/48 | 0.479 | [0.345, 0.617] |
| E61 | `glm47_flash_candidate` | `careful_sibling_comparison` | sibling_accuracy | 67/96 | 0.698 | [0.600, 0.781] |
| E61 | `glm47_flash_candidate` | `sibling_comparison` | sibling_accuracy | 51/96 | 0.531 | [0.432, 0.628] |
| E61 | `qwen35_27b` | `answer_blind_yes_no` | strict_acpi_accept | 2/48 | 0.042 | [0.012, 0.140] |
| E61 | `qwen35_27b` | `careful_yes_no` | strict_acpi_accept | 5/48 | 0.104 | [0.045, 0.222] |
| E61 | `qwen35_27b` | `locate_then_judge_yes_no` | strict_acpi_accept | 2/48 | 0.042 | [0.012, 0.140] |
| E61 | `qwen35_27b` | `plain_yes_no` | strict_acpi_accept | 18/48 | 0.375 | [0.252, 0.516] |
| E61 | `qwen35_27b` | `careful_sibling_comparison` | sibling_accuracy | 96/96 | 1.000 | [0.962, 1.000] |
| E61 | `qwen35_27b` | `sibling_comparison` | sibling_accuracy | 96/96 | 1.000 | [0.962, 1.000] |

## E61 Leave-One-Family / E61 留一错误类型敏感性

| model | objective | metric | base | min LOO | max LOO | range |
|---|---|---|---:|---:|---:|---:|
| `gemma4_26b_a4b_it` | `plain_yes_no` | E61_strict_acpi_accept_leave_one_family | 0.438 | 0.357 | 0.500 | 0.143 |
| `gemma4_26b_a4b_it` | `careful_yes_no` | E61_strict_acpi_accept_leave_one_family | 0.312 | 0.214 | 0.357 | 0.143 |
| `gemma4_26b_a4b_it` | `answer_blind_yes_no` | E61_strict_acpi_accept_leave_one_family | 0.167 | 0.095 | 0.190 | 0.095 |
| `gemma4_26b_a4b_it` | `locate_then_judge_yes_no` | E61_strict_acpi_accept_leave_one_family | 0.333 | 0.238 | 0.381 | 0.143 |
| `gemma4_26b_a4b_it` | `sibling_comparison` | E61_sibling_accuracy_leave_one_family | 0.969 | 0.964 | 0.976 | 0.012 |
| `gemma4_26b_a4b_it` | `careful_sibling_comparison` | E61_sibling_accuracy_leave_one_family | 0.958 | 0.952 | 0.964 | 0.012 |
| `gemma4_31b_it` | `plain_yes_no` | E61_strict_acpi_accept_leave_one_family | 0.458 | 0.381 | 0.524 | 0.143 |
| `gemma4_31b_it` | `careful_yes_no` | E61_strict_acpi_accept_leave_one_family | 0.146 | 0.048 | 0.167 | 0.119 |
| `gemma4_31b_it` | `answer_blind_yes_no` | E61_strict_acpi_accept_leave_one_family | 0.167 | 0.048 | 0.190 | 0.143 |
| `gemma4_31b_it` | `locate_then_judge_yes_no` | E61_strict_acpi_accept_leave_one_family | 0.146 | 0.071 | 0.167 | 0.095 |
| `gemma4_31b_it` | `sibling_comparison` | E61_sibling_accuracy_leave_one_family | 1.000 | 1.000 | 1.000 | 0.000 |
| `gemma4_31b_it` | `careful_sibling_comparison` | E61_sibling_accuracy_leave_one_family | 1.000 | 1.000 | 1.000 | 0.000 |
| `glm47_flash_candidate` | `plain_yes_no` | E61_strict_acpi_accept_leave_one_family | 0.479 | 0.405 | 0.524 | 0.119 |
| `glm47_flash_candidate` | `careful_yes_no` | E61_strict_acpi_accept_leave_one_family | 0.083 | 0.024 | 0.095 | 0.071 |
| `glm47_flash_candidate` | `answer_blind_yes_no` | E61_strict_acpi_accept_leave_one_family | 0.021 | 0.000 | 0.024 | 0.024 |
| `glm47_flash_candidate` | `locate_then_judge_yes_no` | E61_strict_acpi_accept_leave_one_family | 0.208 | 0.119 | 0.238 | 0.119 |
| `glm47_flash_candidate` | `sibling_comparison` | E61_sibling_accuracy_leave_one_family | 0.531 | 0.524 | 0.536 | 0.012 |
| `glm47_flash_candidate` | `careful_sibling_comparison` | E61_sibling_accuracy_leave_one_family | 0.698 | 0.667 | 0.726 | 0.060 |
| `qwen35_27b` | `plain_yes_no` | E61_strict_acpi_accept_leave_one_family | 0.375 | 0.286 | 0.429 | 0.143 |
| `qwen35_27b` | `careful_yes_no` | E61_strict_acpi_accept_leave_one_family | 0.104 | 0.071 | 0.119 | 0.048 |
| `qwen35_27b` | `answer_blind_yes_no` | E61_strict_acpi_accept_leave_one_family | 0.042 | 0.000 | 0.048 | 0.048 |
| `qwen35_27b` | `locate_then_judge_yes_no` | E61_strict_acpi_accept_leave_one_family | 0.042 | 0.000 | 0.048 | 0.048 |
| `qwen35_27b` | `sibling_comparison` | E61_sibling_accuracy_leave_one_family | 1.000 | 1.000 | 1.000 | 0.000 |
| `qwen35_27b` | `careful_sibling_comparison` | E61_sibling_accuracy_leave_one_family | 1.000 | 1.000 | 1.000 | 0.000 |

## Interpretation / 解释

- The main pointwise ACPI-acceptance effect has wide but nonzero uncertainty because controlled pools are intentionally diagnostic, not massive benchmark samples. / 单点 ACPI 接受率的区间较宽，因为这些池是诊断集而不是海量 benchmark。
- E61 leave-one-family checks show whether a result depends on one error family; high ranges flag where the paper should avoid overgeneralizing. / E61 留一检查告诉我们结论是否被某一类错误单独驱动；range 高时论文不能过度泛化。
- GLM rows should be reported as expanded-P0 boundary evidence, not mixed into the original core-P0 headline without qualification. / GLM 应作为扩展 P0 边界证据报告，不能不加限定地混入核心 P0 headline。
