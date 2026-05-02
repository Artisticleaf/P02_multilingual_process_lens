# E61 Language-Route × Error-Taxonomy Grid / E61 语言路径 × 错误类型网格（2026-04-29）

- JSON audit / 机器可读审计：`reports/E61_LANGUAGE_ERROR_GRID_AUDIT_20260429.json`
- Completed models / 已完成模型：gemma4_26b_a4b_it, gemma4_31b_it, qwen35_27b
- Pending models / 待完成模型：none
- Scope / 范围：6 条语言路径 × 8 类错误，每个 cell 一条 valid-correct 和一条 invalid-correct trace；不把标签、span 或人工修正写入 prompt。
- Plain language / 说人话：这一步回答“我们是不是只是在 discount 或少数英文短题上看到现象”。

## Mean Across Completed P0 / 已完成 P0 均值

| objective | type | mean accuracy | mean ACPI accept / sibling error | mean valid accept | note |
|---|---|---:|---:|---:|---|
| `plain_yes_no` | pointwise | 0.757 | 0.424 | 0.938 | single-trace Yes/No / 单条 trace 判断 |
| `careful_yes_no` | pointwise | 0.851 | 0.188 | 0.889 | single-trace Yes/No / 单条 trace 判断 |
| `answer_blind_yes_no` | pointwise | 0.889 | 0.125 | 0.903 | single-trace Yes/No / 单条 trace 判断 |
| `locate_then_judge_yes_no` | pointwise | 0.854 | 0.174 | 0.882 | single-trace Yes/No / 单条 trace 判断 |
| `sibling_comparison` | contrastive | 0.990 | 0.010 | NA | pairwise sibling / 成对判断 |
| `careful_sibling_comparison` | contrastive | 0.986 | 0.014 | NA | pairwise sibling / 成对判断 |

## By Model / 按模型

| model | objective | accuracy | ACPI accept / sibling error | valid accept | yes/pred-A rate |
|---|---|---:|---:|---:|---:|
| `qwen35_27b` | `plain_yes_no` | 0.792 | 0.375 | 0.958 | 0.667 |
| `qwen35_27b` | `careful_yes_no` | 0.875 | 0.104 | 0.854 | 0.479 |
| `qwen35_27b` | `answer_blind_yes_no` | 0.917 | 0.042 | 0.875 | 0.458 |
| `qwen35_27b` | `locate_then_judge_yes_no` | 0.896 | 0.042 | 0.833 | 0.438 |
| `qwen35_27b` | `sibling_comparison` | 1.000 | 0.000 | NA | 0.500 |
| `qwen35_27b` | `careful_sibling_comparison` | 1.000 | 0.000 | NA | 0.500 |
| `gemma4_31b_it` | `plain_yes_no` | 0.771 | 0.458 | 1.000 | 0.729 |
| `gemma4_31b_it` | `careful_yes_no` | 0.927 | 0.146 | 1.000 | 0.573 |
| `gemma4_31b_it` | `answer_blind_yes_no` | 0.917 | 0.167 | 1.000 | 0.583 |
| `gemma4_31b_it` | `locate_then_judge_yes_no` | 0.896 | 0.146 | 0.938 | 0.542 |
| `gemma4_31b_it` | `sibling_comparison` | 1.000 | 0.000 | NA | 0.500 |
| `gemma4_31b_it` | `careful_sibling_comparison` | 1.000 | 0.000 | NA | 0.500 |
| `gemma4_26b_a4b_it` | `plain_yes_no` | 0.708 | 0.438 | 0.854 | 0.646 |
| `gemma4_26b_a4b_it` | `careful_yes_no` | 0.750 | 0.312 | 0.812 | 0.562 |
| `gemma4_26b_a4b_it` | `answer_blind_yes_no` | 0.833 | 0.167 | 0.833 | 0.500 |
| `gemma4_26b_a4b_it` | `locate_then_judge_yes_no` | 0.771 | 0.333 | 0.875 | 0.604 |
| `gemma4_26b_a4b_it` | `sibling_comparison` | 0.969 | 0.031 | NA | 0.510 |
| `gemma4_26b_a4b_it` | `careful_sibling_comparison` | 0.958 | 0.042 | NA | 0.542 |

## Plain Yes/No ACPI Accept by Route / 普通 Yes/No 按语言路径

| slice | mean | models | total scored rows |
|---|---:|---:|---:|
| `en_en` | 0.375 | 3 | 48 |
| `en_zh` | 0.417 | 3 | 48 |
| `mixed` | 0.500 | 3 | 48 |
| `romanized_zh` | 0.542 | 3 | 48 |
| `zh_en` | 0.375 | 3 | 48 |
| `zh_zh` | 0.333 | 3 | 48 |

## Careful Yes/No ACPI Accept by Route / 仔细 Yes/No 按语言路径

| slice | mean | models | total scored rows |
|---|---:|---:|---:|
| `en_en` | 0.167 | 3 | 48 |
| `en_zh` | 0.125 | 3 | 48 |
| `mixed` | 0.292 | 3 | 48 |
| `romanized_zh` | 0.250 | 3 | 48 |
| `zh_en` | 0.167 | 3 | 48 |
| `zh_zh` | 0.125 | 3 | 48 |

## Sibling Accuracy by Route / Sibling 按语言路径

| slice | mean | models | total scored rows |
|---|---:|---:|---:|
| `en_en` | 1.000 | 3 | 48 |
| `en_zh` | 1.000 | 3 | 48 |
| `mixed` | 1.000 | 3 | 48 |
| `romanized_zh` | 0.938 | 3 | 48 |
| `zh_en` | 1.000 | 3 | 48 |
| `zh_zh` | 1.000 | 3 | 48 |

## Plain Yes/No ACPI Accept by Family / 普通 Yes/No 按错误类型

| slice | mean | models | total scored rows |
|---|---:|---:|---:|
| `code_execution` | 0.944 | 3 | 36 |
| `counting_order` | 0.889 | 3 | 36 |
| `geometry_notation` | 0.111 | 3 | 36 |
| `percentage_base` | 1.000 | 3 | 36 |
| `proof_validity` | 0.056 | 3 | 36 |
| `quantifier_inequality` | 0.000 | 3 | 36 |
| `table_interpretation` | 0.389 | 3 | 36 |
| `unit_scale` | 0.000 | 3 | 36 |

## Careful Yes/No ACPI Accept by Family / 仔细 Yes/No 按错误类型

| slice | mean | models | total scored rows |
|---|---:|---:|---:|
| `code_execution` | 0.667 | 3 | 36 |
| `counting_order` | 0.278 | 3 | 36 |
| `geometry_notation` | 0.056 | 3 | 36 |
| `percentage_base` | 0.444 | 3 | 36 |
| `proof_validity` | 0.000 | 3 | 36 |
| `quantifier_inequality` | 0.000 | 3 | 36 |
| `table_interpretation` | 0.056 | 3 | 36 |
| `unit_scale` | 0.000 | 3 | 36 |

## Sibling Accuracy by Family / Sibling 按错误类型

| slice | mean | models | total scored rows |
|---|---:|---:|---:|
| `code_execution` | 1.000 | 3 | 36 |
| `counting_order` | 0.972 | 3 | 36 |
| `geometry_notation` | 1.000 | 3 | 36 |
| `percentage_base` | 1.000 | 3 | 36 |
| `proof_validity` | 0.972 | 3 | 36 |
| `quantifier_inequality` | 1.000 | 3 | 36 |
| `table_interpretation` | 0.972 | 3 | 36 |
| `unit_scale` | 1.000 | 3 | 36 |

## Interpretation / 解释

- Main result: plain pointwise ACPI accept is 0.424 across P0; careful/answer-blind/locate reduce it to 0.188/0.125/0.174. / 主结果：P0 普通 pointwise ACPI 接受为 0.424；careful/answer-blind/locate 分别降到 0.188/0.125/0.174。
- Sibling remains much stronger but is no longer literally perfect in the broader grid: normal/careful sibling accuracy is 0.990/0.986. / sibling 仍明显更强，但在更广 E61 网格中不再字面完美：普通/仔细 sibling 准确率为 0.990/0.986。
- The sibling errors come from `gemma4_26b_a4b_it` and concentrate in `romanized_zh`; this marks transliteration as a harder route, not a solved corner case. / sibling 错误来自 `gemma4_26b_a4b_it`，且集中在 `romanized_zh`；这说明拼音/转写路径是更难路线，不是已解决的边角情况。
- Highest plain pointwise route risks: romanized_zh=0.542, mixed=0.500. / 普通 pointwise 风险最高的语言路径如前。
- Highest plain pointwise family risks: percentage_base=1.000, code_execution=0.944, counting_order=0.889; careful still leaves risk on code_execution=0.667, percentage_base=0.444, counting_order=0.278. / 普通 pointwise 风险最高的错误类型如前；careful 后仍留下这些高风险类型。
- Scientific update: E61 strengthens generalization beyond discount-like examples and sharpens the boundary: contrastive comparison is robust but not an oracle, especially under transliterated-language traces. / 科学更新：E61 加强了‘不是 discount 个例’的泛化证据，同时收紧边界：对比判断很稳，但不是 oracle，尤其在转写语言 trace 上。

### Sibling Errors / sibling 错误明细

| model | objective | task | family | route | order | target | pred | margin |
|---|---|---|---|---|---|---|---|---:|
| `gemma4_26b_a4b_it` | `sibling_comparison` | `e61_romanized_zh_roles_ordered` | `counting_order` | `romanized_zh` | `bad_B` | `B` | `A` | -0.745 |
| `gemma4_26b_a4b_it` | `sibling_comparison` | `e61_romanized_zh_sum_vs_max_table` | `table_interpretation` | `romanized_zh` | `bad_B` | `B` | `A` | -5.251 |
| `gemma4_26b_a4b_it` | `sibling_comparison` | `e61_romanized_zh_multiple_of_six_even` | `proof_validity` | `romanized_zh` | `bad_A` | `A` | `B` | -0.388 |
| `gemma4_26b_a4b_it` | `careful_sibling_comparison` | `e61_romanized_zh_increase_base` | `percentage_base` | `romanized_zh` | `bad_B` | `B` | `A` | -0.927 |
| `gemma4_26b_a4b_it` | `careful_sibling_comparison` | `e61_romanized_zh_strict_inclusive_mix` | `quantifier_inequality` | `romanized_zh` | `bad_B` | `B` | `A` | -3.280 |
| `gemma4_26b_a4b_it` | `careful_sibling_comparison` | `e61_romanized_zh_roles_ordered` | `counting_order` | `romanized_zh` | `bad_B` | `B` | `A` | -1.129 |
| `gemma4_26b_a4b_it` | `careful_sibling_comparison` | `e61_romanized_zh_sum_vs_max_table` | `table_interpretation` | `romanized_zh` | `bad_B` | `B` | `A` | -7.625 |

## Audit / 审计

- Overall / 总体：PASS
| status | check | detail |
|---|---|---|
| PASS | E61 data row count | rows=96 |
| PASS | E61 pair count | pairs=48 |
| PASS | E61 route count | ['en_en', 'en_zh', 'mixed', 'romanized_zh', 'zh_en', 'zh_zh'] |
| PASS | E61 family count | ['code_execution', 'counting_order', 'geometry_notation', 'percentage_base', 'proof_validity', 'quantifier_inequality', 'table_interpretation', 'unit_scale'] |
| PASS | E61 metadata flag false: gold_label_in_prompt | bad=[] count=0 |
| PASS | E61 metadata flag false: known_error_span_in_prompt | bad=[] count=0 |
| PASS | E61 metadata flag false: known_error_span_annotation_in_prompt | bad=[] count=0 |
| PASS | E61 metadata flag false: manual_correction_in_prompt | bad=[] count=0 |
| PASS | E61 pair valid/bad integrity | bad_pairs=[] count=0 |
| PASS | E61 prompt source does not insert support_span | support_span |
| PASS | E61 prompt source does not insert error_span | error_span |
| PASS | E61 prompt source does not insert manual_correction | manual_correction |
| PASS | E61 prompt source does not insert manual_process_valid | manual_process_valid |
| PASS | E61 prompt source does not insert known_error_span | known_error_span |
| PASS | E61 prompt source does not insert gold_label | gold_label |
| PASS | E61 result exists for qwen35_27b | results/E61_language_error_grid/qwen35_27b_e61_language_error_grid_chat.json |
| PASS | qwen35_27b row count | rows=576 |
| PASS | qwen35_27b chat template used | True |
| PASS | qwen35_27b prompt format | official_if_chat |
| PASS | qwen35_27b leakage audit zero | {'gold_label_in_prompt_rows': 0, 'known_error_span_annotation_in_prompt_rows': 0, 'known_error_span_in_prompt_rows': 0, 'manual_correction_in_prompt_rows': 0, 'note_zh': '错误句子本身作为 trace 内容出现，这是被审计对象；error_span/support_span/manual_correction 不进入 prompt。'} |
| PASS | qwen35_27b objective counts | {('pointwise', 'plain_yes_no'): 96, ('pointwise', 'careful_yes_no'): 96, ('pointwise', 'answer_blind_yes_no'): 96, ('pointwise', 'locate_then_judge_yes_no'): 96, ('contrastive', 'sibling_comparison'): 96, ('contrastive', 'careful_sibling_comparison'): 96} |
| PASS | qwen35_27b sibling order balance | {('sibling_comparison', 'bad_A'): 48, ('sibling_comparison', 'bad_B'): 48, ('careful_sibling_comparison', 'bad_A'): 48, ('careful_sibling_comparison', 'bad_B'): 48} |
| PASS | E61 result exists for gemma4_31b_it | results/E61_language_error_grid/gemma4_31b_it_e61_language_error_grid_chat.json |
| PASS | gemma4_31b_it row count | rows=576 |
| PASS | gemma4_31b_it chat template used | True |
| PASS | gemma4_31b_it prompt format | official_if_chat |
| PASS | gemma4_31b_it leakage audit zero | {'gold_label_in_prompt_rows': 0, 'known_error_span_annotation_in_prompt_rows': 0, 'known_error_span_in_prompt_rows': 0, 'manual_correction_in_prompt_rows': 0, 'note_zh': '错误句子本身作为 trace 内容出现，这是被审计对象；error_span/support_span/manual_correction 不进入 prompt。'} |
| PASS | gemma4_31b_it objective counts | {('pointwise', 'plain_yes_no'): 96, ('pointwise', 'careful_yes_no'): 96, ('pointwise', 'answer_blind_yes_no'): 96, ('pointwise', 'locate_then_judge_yes_no'): 96, ('contrastive', 'sibling_comparison'): 96, ('contrastive', 'careful_sibling_comparison'): 96} |
| PASS | gemma4_31b_it sibling order balance | {('sibling_comparison', 'bad_A'): 48, ('sibling_comparison', 'bad_B'): 48, ('careful_sibling_comparison', 'bad_A'): 48, ('careful_sibling_comparison', 'bad_B'): 48} |
| PASS | E61 result exists for gemma4_26b_a4b_it | results/E61_language_error_grid/gemma4_26b_a4b_it_e61_language_error_grid_chat.json |
| PASS | gemma4_26b_a4b_it row count | rows=576 |
| PASS | gemma4_26b_a4b_it chat template used | True |
| PASS | gemma4_26b_a4b_it prompt format | official_if_chat |
| PASS | gemma4_26b_a4b_it leakage audit zero | {'gold_label_in_prompt_rows': 0, 'known_error_span_annotation_in_prompt_rows': 0, 'known_error_span_in_prompt_rows': 0, 'manual_correction_in_prompt_rows': 0, 'note_zh': '错误句子本身作为 trace 内容出现，这是被审计对象；error_span/support_span/manual_correction 不进入 prompt。'} |
| PASS | gemma4_26b_a4b_it objective counts | {('pointwise', 'plain_yes_no'): 96, ('pointwise', 'careful_yes_no'): 96, ('pointwise', 'answer_blind_yes_no'): 96, ('pointwise', 'locate_then_judge_yes_no'): 96, ('contrastive', 'sibling_comparison'): 96, ('contrastive', 'careful_sibling_comparison'): 96} |
| PASS | gemma4_26b_a4b_it sibling order balance | {('sibling_comparison', 'bad_A'): 48, ('sibling_comparison', 'bad_B'): 48, ('careful_sibling_comparison', 'bad_A'): 48, ('careful_sibling_comparison', 'bad_B'): 48} |

## Boundary / 边界

- E61 is a controlled trace-selection generalization experiment, not a natural prevalence estimate. / E61 是受控 trace-selection 泛化实验，不是自然发生率估计。
- Error spans and support spans exist in the data file for post-hoc audit, but the runner does not insert them into prompts. / 数据文件中有 error/support span 供事后审计，但 runner 不会把它们插入 prompt。
- Sibling comparison is a contrastive diagnostic; mechanism interventions remain separate oracle diagnostics. / sibling 是对比诊断；机制干预仍是单独的 oracle 诊断。
