# E60 Objective Ladder / E60 过程检查目标梯度（2026-04-29）

- JSON audit / 机器可读审计：`reports/E60_OBJECTIVE_LADDER_AUDIT_20260429.json`
- Scope / 范围：在当前 P0 三模型上，比较普通 absolute Yes/No、更严格的过程检查 prompt、answer-blind prompt、先定位再判断 prompt，以及 sibling comparison。
- Plain language / 说人话：更明确地要求模型“仔细检查过程”确实能显著降低 over-accept，但不能保证清零；把一好一坏 sibling 并排比较仍然最稳。

## Mean Across P0 / P0 均值

| objective | type | mean accuracy | mean ACPI accept | mean valid accept | note |
|---|---|---:|---:|---:|---|
| `plain_yes_no` | pointwise | 0.711 | 0.567 | 0.989 | baseline absolute verifier / 普通 absolute verifier |
| `careful_yes_no` | pointwise | 0.911 | 0.156 | 0.978 | strict line-by-line wording / 严格逐行检查措辞 |
| `answer_blind_yes_no` | pointwise | 0.889 | 0.189 | 0.967 | tells model to cover final answer / 要求不要被最终答案锚定 |
| `locate_then_judge_yes_no` | pointwise | 0.922 | 0.144 | 0.989 | internal error-localization then Yes/No / 内部定位错误后再 Yes/No |
| `sibling_comparison` | contrastive | 1.000 | 0.000 | 1.000 | pairwise sibling objective / 成对 sibling 目标 |
| `careful_sibling_comparison` | contrastive | 1.000 | 0.000 | 1.000 | pairwise sibling objective / 成对 sibling 目标 |

## By Model / 按模型

| model | objective | accuracy | ACPI accept | valid accept | yes/pred rate |
|---|---|---:|---:|---:|---:|
| `qwen35_27b` | `plain_yes_no` | 0.700 | 0.600 | 1.000 | 0.800 |
| `qwen35_27b` | `careful_yes_no` | 0.967 | 0.033 | 0.967 | 0.500 |
| `qwen35_27b` | `answer_blind_yes_no` | 0.900 | 0.133 | 0.933 | 0.533 |
| `qwen35_27b` | `locate_then_judge_yes_no` | 0.967 | 0.067 | 1.000 | 0.533 |
| `qwen35_27b` | `sibling_comparison` | 1.000 | 0.000 | 1.000 | 0.500 |
| `qwen35_27b` | `careful_sibling_comparison` | 1.000 | 0.000 | 1.000 | 0.500 |
| `gemma4_31b_it` | `plain_yes_no` | 0.700 | 0.600 | 1.000 | 0.800 |
| `gemma4_31b_it` | `careful_yes_no` | 0.933 | 0.133 | 1.000 | 0.567 |
| `gemma4_31b_it` | `answer_blind_yes_no` | 0.883 | 0.233 | 1.000 | 0.617 |
| `gemma4_31b_it` | `locate_then_judge_yes_no` | 0.933 | 0.133 | 1.000 | 0.567 |
| `gemma4_31b_it` | `sibling_comparison` | 1.000 | 0.000 | 1.000 | 0.500 |
| `gemma4_31b_it` | `careful_sibling_comparison` | 1.000 | 0.000 | 1.000 | 0.500 |
| `gemma4_26b_a4b_it` | `plain_yes_no` | 0.733 | 0.500 | 0.967 | 0.733 |
| `gemma4_26b_a4b_it` | `careful_yes_no` | 0.833 | 0.300 | 0.967 | 0.633 |
| `gemma4_26b_a4b_it` | `answer_blind_yes_no` | 0.883 | 0.200 | 0.967 | 0.583 |
| `gemma4_26b_a4b_it` | `locate_then_judge_yes_no` | 0.867 | 0.233 | 0.967 | 0.600 |
| `gemma4_26b_a4b_it` | `sibling_comparison` | 1.000 | 0.000 | 1.000 | 0.500 |
| `gemma4_26b_a4b_it` | `careful_sibling_comparison` | 1.000 | 0.000 | 1.000 | 0.500 |

## Interpretation / 解释

- Plain Yes/No reproduces E42/E54: mean ACPI accept is 0.567 across P0, with valid accept near 0.989. / 普通 Yes/No 复现 E42/E54：P0 平均 ACPI 接受为 0.567，valid 接受约 0.989。
- Careful process wording helps a lot: mean ACPI accept falls to 0.156, but it is not zero and differs by model. / 更严格过程措辞很有帮助：平均 ACPI 接受降到 0.156，但没有清零，且有模型差异。
- Answer-blind wording also helps but is weaker than careful line-by-line wording for Qwen/Gemma4-31B and similar for Gemma4-26B-A4B. / answer-blind 措辞也有帮助，但在 Qwen/Gemma4-31B 上弱于逐行检查措辞，在 Gemma4-26B-A4B 上接近。
- Locate-then-judge helps but still leaves ACPI, which means asking the model to internally locate errors is not equivalent to forcing a reliable external comparison. / 先定位再判断有帮助但仍留下 ACPI，说明要求模型内部定位错误不等于强制可靠外部比较。
- Sibling comparison remains 1.000 accurate for both normal and careful sibling prompts. / 普通 sibling 与 careful sibling 均保持 1.000 准确。

## Audit / 审计

- Overall / 总体：PASS
| status | check | detail |
|---|---|---|
| PASS | E60 result exists for qwen35_27b | results/E60_objective_ladder/qwen35_27b_e60_objective_ladder_chat.json |
| PASS | qwen35_27b row count | rows=360 |
| PASS | qwen35_27b chat template used | True |
| PASS | qwen35_27b prompt format | official_if_chat |
| PASS | qwen35_27b leakage audit zero | {'gold_label_in_prompt_rows': 0, 'known_error_span_annotation_in_prompt_rows': 0, 'manual_correction_in_prompt_rows': 0, 'note_zh': '错误句子本身作为 trace 内容出现，这是被审计对象；error_span/support_span/manual_correction 不进入 prompt。'} |
| PASS | qwen35_27b objective counts | {('pointwise', 'plain_yes_no'): 60, ('pointwise', 'careful_yes_no'): 60, ('pointwise', 'answer_blind_yes_no'): 60, ('pointwise', 'locate_then_judge_yes_no'): 60, ('contrastive', 'sibling_comparison'): 60, ('contrastive', 'careful_sibling_comparison'): 60} |
| PASS | qwen35_27b E60 plain reproduces E42 | E60=0.5/1.0 E42=0.5/1.0 |
| PASS | qwen35_27b E60 plain reproduces E54 | E60=0.6666666666666666/1.0 E54=0.6666666666666666/1.0 |
| PASS | E60 result exists for gemma4_31b_it | results/E60_objective_ladder/gemma4_31b_it_e60_objective_ladder_chat.json |
| PASS | gemma4_31b_it row count | rows=360 |
| PASS | gemma4_31b_it chat template used | True |
| PASS | gemma4_31b_it prompt format | official_if_chat |
| PASS | gemma4_31b_it leakage audit zero | {'gold_label_in_prompt_rows': 0, 'known_error_span_annotation_in_prompt_rows': 0, 'manual_correction_in_prompt_rows': 0, 'note_zh': '错误句子本身作为 trace 内容出现，这是被审计对象；error_span/support_span/manual_correction 不进入 prompt。'} |
| PASS | gemma4_31b_it objective counts | {('pointwise', 'plain_yes_no'): 60, ('pointwise', 'careful_yes_no'): 60, ('pointwise', 'answer_blind_yes_no'): 60, ('pointwise', 'locate_then_judge_yes_no'): 60, ('contrastive', 'sibling_comparison'): 60, ('contrastive', 'careful_sibling_comparison'): 60} |
| PASS | gemma4_31b_it E60 plain reproduces E42 | E60=0.5/1.0 E42=0.5/1.0 |
| PASS | gemma4_31b_it E60 plain reproduces E54 | E60=0.6666666666666666/1.0 E54=0.6666666666666666/1.0 |
| PASS | E60 result exists for gemma4_26b_a4b_it | results/E60_objective_ladder/gemma4_26b_a4b_it_e60_objective_ladder_chat.json |
| PASS | gemma4_26b_a4b_it row count | rows=360 |
| PASS | gemma4_26b_a4b_it chat template used | True |
| PASS | gemma4_26b_a4b_it prompt format | official_if_chat |
| PASS | gemma4_26b_a4b_it leakage audit zero | {'gold_label_in_prompt_rows': 0, 'known_error_span_annotation_in_prompt_rows': 0, 'manual_correction_in_prompt_rows': 0, 'note_zh': '错误句子本身作为 trace 内容出现，这是被审计对象；error_span/support_span/manual_correction 不进入 prompt。'} |
| PASS | gemma4_26b_a4b_it objective counts | {('pointwise', 'plain_yes_no'): 60, ('pointwise', 'careful_yes_no'): 60, ('pointwise', 'answer_blind_yes_no'): 60, ('pointwise', 'locate_then_judge_yes_no'): 60, ('contrastive', 'sibling_comparison'): 60, ('contrastive', 'careful_sibling_comparison'): 60} |
| PASS | gemma4_26b_a4b_it E60 plain reproduces E42 | E60=0.5/1.0 E42=0.5/1.0 |
| PASS | gemma4_26b_a4b_it E60 plain reproduces E54 | E60=0.5/0.9444444444444444 E54=0.5/0.9444444444444444 |
| PASS | E60 prompt source does not insert support_span | support_span |
| PASS | E60 prompt source does not insert error_span | error_span |
| PASS | E60 prompt source does not insert manual_correction | manual_correction |
| PASS | E60 prompt source does not insert known_error_spans | known_error_spans |
| PASS | E60 prompt source does not insert manual_process_valid | manual_process_valid |

## Boundary / 边界

- E60 is still a controlled verifier-objective experiment over E42/E54 pools, not a natural prevalence estimate. / E60 仍是基于 E42/E54 池的受控 verifier-objective 实验，不是自然发生率估计。
- The result supports an objective/prompt/threshold mismatch claim: better objectives reduce risk, but pairwise comparison remains more reliable. / 该结果支持 objective/prompt/threshold 错配主张：更好的目标会降低风险，但成对比较仍更可靠。
