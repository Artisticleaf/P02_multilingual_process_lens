# E58 Distillation-Filter Simulation / E58 蒸馏式筛选器模拟（2026-04-28）

- JSON / 机器可读结果：`results/E58_distillation_filter_simulation/e58_filter_simulation_20260428.json`
- Scope / 范围：不跑新模型，只读取 E42/E53/E54/E56/E57 已审计官方结果，模拟不同筛选器会保留多少 ACPI 风险。
- Plain language / 说人话：如果训练数据筛选只看“答案对不对”，它会把答案正确但过程错误的 trace 一起收进去；如果让 verifier 单独回答 Yes/No，它会少收一些坏 trace，但仍系统性漏过；如果把同题同答案的一好一坏 sibling 并排比较，坏 trace 基本暴露。

## Main Filter Comparison / 主筛选器对比

| experiment | pool | filter | mean ACPI in accepted | mean valid retention | mean invalid retention | accepted ACPI / accepted |
|---|---|---|---:|---:|---:|---:|
| E42 | controlled_12_family | absolute_yes_no_process | 0.333 | 1.000 | 0.500 | 18/54 |
| E42 | controlled_12_family | outcome_only_final_correct | 0.500 | 1.000 | 1.000 | 36/72 |
| E42 | controlled_12_family | sibling_comparison | 0.000 | 1.000 | 0.000 | 0/72 |
| E53 | answer_anchor_masked | absolute_yes_no_process | 0.244 | 1.000 | 0.333 | 12/48 |
| E53 | answer_anchor_removed | absolute_yes_no_process | 0.263 | 1.000 | 0.361 | 13/49 |
| E53 | answer_anchor_shown | absolute_yes_no_process | 0.333 | 1.000 | 0.500 | 18/54 |
| E53 | answer_anchor_shown | outcome_only_visible_answer | 0.500 | 1.000 | 1.000 | 36/72 |
| E53 | answer_anchor_wrong | absolute_yes_no_process | 0.075 | 0.917 | 0.083 | 3/36 |
| E53 | answer_anchor_wrong | outcome_only_visible_answer | NA | 0.000 | 0.000 | 0/0 |
| E54 | parameterized_18_family | absolute_yes_no_process | 0.382 | 0.981 | 0.611 | 33/86 |
| E54 | parameterized_18_family | outcome_only_final_correct | 0.500 | 1.000 | 1.000 | 54/108 |
| E54 | parameterized_18_family | sibling_comparison | 0.000 | 1.000 | 0.000 | 0/108 |
| E56 | controlled_12_family_hidden_residual_loto | residual_probe_loto_diagnostic | 0.077 | 1.000 | 0.083 | 3/39 |
| E57 | p0_hard_task_final_correct_repaired_label | outcome_only_final_correct | 0.013 | 1.000 | 1.000 | 2/119 |
| E57 | p0_hard_task_final_correct_strict_label | outcome_only_final_correct | 0.077 | 1.000 | 1.000 | 11/119 |

## E42/E54 Controlled Pools / E42/E54 受控池

- E42 has 12 same-problem/same-final-answer valid/invalid pairs; E54 expands this to 18 parameterized task families. / E42 有 12 组同题同答案的一好一坏 trace；E54 扩展到 18 个参数化任务族。
- Outcome-only accepts every trace in these pools, so accepted ACPI is 0.500 by construction. This is not a result about model judgment; it is the risk of using final answer alone. / 只看最终答案会全收，因此 ACPI 比例按构造就是 0.500；这不是模型判断结果，而是答案筛选本身的风险。
- Absolute Yes/No reduces but does not remove ACPI: E42 P0 invalid retention is 0.500, while E54 invalid retention is 0.500-0.667 depending on model. / absolute Yes/No 能减少但不能清除 ACPI：E42 中 P0 invalid retention 为 0.500，E54 中不同模型为 0.500-0.667。
- Sibling comparison has 0.000 accepted ACPI in E42/E54 P0 runs because all pair-selection decisions are correct. / sibling comparison 在 E42/E54 的 P0 运行中 accepted ACPI 为 0，因为成对选择全对。

## E53 Answer Anchor / E53 答案锚定

| model | condition | outcome-only ACPI | absolute ACPI in accepted | absolute invalid retention |
|---|---|---:|---:|---:|
| `qwen35_27b` | `shown` | 0.500 | 0.333 | 0.500 |
| `qwen35_27b` | `removed` | NA | 0.200 | 0.250 |
| `qwen35_27b` | `masked` | NA | 0.294 | 0.417 |
| `qwen35_27b` | `wrong` | NA | 0.083 | 0.083 |
| `gemma4_31b_it` | `shown` | 0.500 | 0.333 | 0.500 |
| `gemma4_31b_it` | `removed` | NA | 0.294 | 0.417 |
| `gemma4_31b_it` | `masked` | NA | 0.294 | 0.417 |
| `gemma4_31b_it` | `wrong` | NA | 0.000 | 0.000 |
| `gemma4_26b_a4b_it` | `shown` | 0.500 | 0.333 | 0.500 |
| `gemma4_26b_a4b_it` | `removed` | NA | 0.294 | 0.417 |
| `gemma4_26b_a4b_it` | `masked` | NA | 0.143 | 0.167 |
| `gemma4_26b_a4b_it` | `wrong` | NA | 0.143 | 0.167 |

Interpretation / 解释：正确最终答案像锚一样把 absolute verifier 往 Yes 拉；wrong-final condition 会显著压低 invalid 接受。但 removed/masked 仍有非零 invalid retention，所以不能把机制简化成“只看 final answer”。

## E56 Residual Diagnostic / E56 残差诊断

| model | accepted ACPI | valid retention | invalid retention | note |
|---|---:|---:|---:|---|
| `qwen35_27b` | 0.077 | 1.000 | 0.083 | LOTO hidden-state diagnostic, not deployable filter |
| `gemma4_31b_it` | 0.077 | 1.000 | 0.083 | LOTO hidden-state diagnostic, not deployable filter |
| `gemma4_26b_a4b_it` | 0.077 | 1.000 | 0.083 | LOTO hidden-state diagnostic, not deployable filter |

Interpretation / 解释：残差 probe 不是生产筛选器，因为它用到了 hidden state 和受控标签训练；但它说明 hidden state 中确实有可读出的过程有效性证据。它和 absolute 输出之间的差距，就是“证据存在但 Yes/No 决策没用好”的核心证据之一。

## E57 Hard-Task Appendix / E57 困难题附录

| model | label policy | accepted traces | accepted ACPI | accepted ACPI rate |
|---|---|---:|---:|---:|
| `qwen35_27b` | `strict` | 20 | 0 | 0.000 |
| `qwen35_27b` | `repaired` | 20 | 0 | 0.000 |
| `gemma4_31b_it` | `strict` | 47 | 9 | 0.191 |
| `gemma4_31b_it` | `repaired` | 47 | 0 | 0.000 |
| `gemma4_26b_a4b_it` | `strict` | 52 | 2 | 0.038 |
| `gemma4_26b_a4b_it` | `repaired` | 52 | 2 | 0.038 |

Interpretation / 解释：困难题 final-correct 子集里，strict ACPI 主要是“先错后修复”的 visible trace；用 repaired 标签后，未修复 ACPI 很少。E58 因此不应把 hard-task 当作高频 ACPI 证据，而应作为边界条件：困难题 ACPI 存在，但当前 P0 小样本中不高频。

## Audit / 审计

- Overall / 总体：PASS
| status | check | detail |
|---|---|---|
| PASS | P0 record coverage | Counter({'qwen35_27b': 15, 'gemma4_31b_it': 15, 'gemma4_26b_a4b_it': 15}) |
| PASS | E42/E54 outcome-only retains 50% ACPI by construction | controlled pools have one valid and one invalid final-correct trace per task |
| PASS | Sibling filters are pair-selection events | sibling rows are not independent single-trace rows |
| PASS | E57 only uses manual final-correct rows | manual audit file contains final-correct rows only |
| PASS | No model inference in E58 | E58 reads existing JSON/JSONL outputs only |

## Decision for Mainline / 对主线的决定

- Use E58 mainly on E42/E54/E53 controlled pools, because they isolate the causal-chain risk cleanly. / E58 主证据应放在 E42/E54/E53 受控池，因为它们干净隔离了因果链风险。
- Keep E57 as hard-task appendix, not prevalence headline. / E57 放在困难题附录，不作为高发生率 headline。
- The safe paper statement is: outcome-only and absolute pointwise filtering can retain ACPI traces; sibling comparison suppresses them much more strongly; hidden residual diagnostics show the process signal exists even when absolute Yes/No underuses it. / 安全论文表述：只看答案和 absolute 单点筛选都会保留 ACPI；sibling comparison 明显更能压制；hidden residual 诊断显示过程信号存在，只是 absolute Yes/No 没充分使用。
