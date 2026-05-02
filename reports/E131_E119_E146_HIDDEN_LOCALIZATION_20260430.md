# E131 E119/E146 Hidden Localization / E119/E146 隐藏层定位

- Created / 生成时间：`2026-04-30T15:39:28`
- Mode / 模式：`NG`, `thinking=false`, direct strict verifier replay。
- Source labels / 标签来源：`data/processed/e119_e146_process_audit_official_20260430.jsonl`。
- Verifier prompt / verifier prompt：只包含 problem 与可见 trace prefix；人工标签、gold answer、error span 只用于离线选行和截断点。
- Hidden signal / 隐藏信号：使用 E61 受控任务训练出的过程有效性方向，对 E119/E146 自然困难题 prefix 的 residual / MLP / token-mixer / norm 输出做 teacher-forced 投影。

说人话：E131 问的是，模型 trace 里出现错步、修复标记、最终完成这些时间点时，verifier 内部状态是否跟着移动；以及有些未修复 ACPI 明明内部有“这一步不太对”的信号，最终 Yes/No 是否仍然放行。

## Main Results / 主要结果

### Gemma4-26B-A4B-it

- Result / 结果：`results/E131_e119_e146_hidden_localization/gemma4_26b_a4b_it_e131_hidden_localization_mixed_chat.json`
- Cache / 激活缓存：`results/E131_e119_e146_hidden_localization/gemma4_26b_a4b_it_e131_component_cache_mixed_chat.pt`
- Best hidden/component / 最强方向：`17:residual_hidden_state`；selected layers=[15, 16, 17, 18, 19]
- Leakage audit / 泄露审计：error_span=0, gold=0, labels=0.

| Slice / 切片 | n | accept rate / 接受率, Wilson 95% CI | mean Yes-No | mean best component |
|---|---:|---:|---:|---:|
| strict_valid | 18 | 18/18 = 1.000 [0.824, 1.000] | 4.958 | -0.843 |
| repaired_acpi | 56 | 12/56 = 0.214 [0.127, 0.338] | -4.420 | -4.456 |
| unrepaired_acpi | 10 | 8/10 = 0.800 [0.490, 0.943] | 5.956 | -1.441 |

| Stage / 阶段 | n | accept rate / 接受率, Wilson 95% CI | mean Yes-No | mean best component |
|---|---:|---:|---:|---:|
| first_final_answer_end | 16 | 12/16 = 0.750 [0.505, 0.898] | 3.711 | -1.492 |
| detected_error_marker_end | 10 | 0/10 = 0.000 [0.000, 0.278] | -8.122 | -5.240 |
| post_error_240chars | 10 | 2/10 = 0.200 [0.057, 0.510] | -5.616 | -5.798 |
| repair_trigger_end | 8 | 0/8 = 0.000 [0.000, 0.324] | -8.801 | -5.594 |
| post_repair_240chars | 8 | 0/8 = 0.000 [0.000, 0.324] | -9.508 | -6.758 |
| completion_end | 16 | 12/16 = 0.750 [0.505, 0.898] | 3.930 | -1.439 |

Repaired ACPI stage movement / 已修复 ACPI 的阶段移动：

| Stage / 阶段 | n | accept rate / 接受率, Wilson 95% CI | mean Yes-No | mean best component |
|---|---:|---:|---:|---:|
| first_final_answer_end | 8 | 4/8 = 0.500 [0.215, 0.785] | 1.656 | -2.095 |
| detected_error_marker_end | 8 | 0/8 = 0.000 [0.000, 0.324] | -9.973 | -6.007 |
| post_error_240chars | 8 | 0/8 = 0.000 [0.000, 0.324] | -8.504 | -6.760 |
| repair_trigger_end | 8 | 0/8 = 0.000 [0.000, 0.324] | -8.801 | -5.594 |
| post_repair_240chars | 8 | 0/8 = 0.000 [0.000, 0.324] | -9.508 | -6.758 |
| completion_end | 8 | 4/8 = 0.500 [0.215, 0.785] | 2.094 | -1.988 |

Component projection means for repaired ACPI / 已修复 ACPI 的组件投影均值：

| Stage / 阶段 | n | residual hidden state | mlp output | token mixer output | post attention norm output | post feedforward norm output | pre mlp norm output |
|---|---:|---:|---:|---:|---:|---:|---:|
| first_final_answer_end | 8 | -2.095 | 0.024 | -1.699 | 0.476 | -8.017 | -0.111 |
| detected_error_marker_end | 8 | -6.007 | -0.026 | -2.212 | -3.684 | -9.816 | -0.271 |
| post_error_240chars | 8 | -6.760 | -0.027 | -2.403 | -4.231 | -10.664 | -0.313 |
| repair_trigger_end | 8 | -5.594 | -0.027 | -2.449 | -3.645 | -9.643 | -0.268 |
| post_repair_240chars | 8 | -6.758 | -0.038 | -2.917 | -4.533 | -10.619 | -0.318 |
| completion_end | 8 | -1.988 | 0.024 | -1.606 | 0.556 | -7.924 | -0.108 |

Unrepaired ACPI stage movement / 未修复 ACPI 的阶段移动：

| Stage / 阶段 | n | accept rate / 接受率, Wilson 95% CI | mean Yes-No | mean best component |
|---|---:|---:|---:|---:|
| first_final_answer_end | 2 | 2/2 = 1.000 [0.342, 1.000] | 8.187 | -1.028 |
| detected_error_marker_end | 2 | 0/2 = 0.000 [0.000, 0.658] | -0.719 | -2.172 |
| post_error_240chars | 2 | 2/2 = 1.000 [0.342, 1.000] | 5.938 | -1.949 |
| completion_end | 2 | 2/2 = 1.000 [0.342, 1.000] | 8.187 | -1.028 |

Component projection means for unrepaired ACPI / 未修复 ACPI 的组件投影均值：

| Stage / 阶段 | n | residual hidden state | mlp output | token mixer output | post attention norm output | post feedforward norm output | pre mlp norm output |
|---|---:|---:|---:|---:|---:|---:|---:|
| first_final_answer_end | 2 | -1.028 | 0.038 | -0.493 | -0.022 | -3.793 | -0.065 |
| detected_error_marker_end | 2 | -2.172 | 0.033 | 0.496 | 0.752 | -4.234 | -0.035 |
| post_error_240chars | 2 | -1.949 | 0.027 | 0.577 | 0.759 | -4.243 | -0.034 |
| completion_end | 2 | -1.028 | 0.038 | -0.493 | -0.022 | -3.793 | -0.065 |

### Gemma4-31B-it

- Result / 结果：`results/E131_e119_e146_hidden_localization/gemma4_31b_it_e131_hidden_localization_mixed_chat.json`
- Cache / 激活缓存：`results/E131_e119_e146_hidden_localization/gemma4_31b_it_e131_component_cache_mixed_chat.pt`
- Best hidden/component / 最强方向：`34:residual_hidden_state`；selected layers=[32, 33, 34, 35, 36]
- Leakage audit / 泄露审计：error_span=0, gold=0, labels=0.

| Slice / 切片 | n | accept rate / 接受率, Wilson 95% CI | mean Yes-No | mean best component |
|---|---:|---:|---:|---:|
| strict_valid | 30 | 30/30 = 1.000 [0.886, 1.000] | 20.165 | 2.962 |
| repaired_acpi | 112 | 42/112 = 0.375 [0.291, 0.467] | -4.075 | -3.165 |

| Stage / 阶段 | n | accept rate / 接受率, Wilson 95% CI | mean Yes-No | mean best component |
|---|---:|---:|---:|---:|
| first_final_answer_end | 26 | 22/26 = 0.846 [0.665, 0.939] | 12.143 | 0.770 |
| detected_error_marker_end | 16 | 8/16 = 0.500 [0.280, 0.720] | -4.460 | -3.336 |
| post_error_240chars | 16 | 6/16 = 0.375 [0.185, 0.614] | -5.568 | -4.643 |
| repair_trigger_end | 16 | 2/16 = 0.125 [0.035, 0.360] | -12.495 | -5.258 |
| post_repair_240chars | 16 | 2/16 = 0.125 [0.035, 0.360] | -9.246 | -5.115 |
| completion_end | 26 | 16/26 = 0.615 [0.425, 0.776] | 6.559 | 0.154 |

Repaired ACPI stage movement / 已修复 ACPI 的阶段移动：

| Stage / 阶段 | n | accept rate / 接受率, Wilson 95% CI | mean Yes-No | mean best component |
|---|---:|---:|---:|---:|
| first_final_answer_end | 16 | 12/16 = 0.750 [0.505, 0.898] | 7.130 | -0.600 |
| detected_error_marker_end | 16 | 8/16 = 0.500 [0.280, 0.720] | -4.460 | -3.336 |
| post_error_240chars | 16 | 6/16 = 0.375 [0.185, 0.614] | -5.568 | -4.643 |
| repair_trigger_end | 16 | 2/16 = 0.125 [0.035, 0.360] | -12.495 | -5.258 |
| post_repair_240chars | 16 | 2/16 = 0.125 [0.035, 0.360] | -9.246 | -5.115 |
| completion_end | 16 | 6/16 = 0.375 [0.185, 0.614] | -1.945 | -1.601 |

Component projection means for repaired ACPI / 已修复 ACPI 的组件投影均值：

| Stage / 阶段 | n | residual hidden state | mlp output | token mixer output | post attention norm output | post feedforward norm output | pre mlp norm output |
|---|---:|---:|---:|---:|---:|---:|---:|
| first_final_answer_end | 16 | -0.600 | -1.839 | -0.434 | -0.428 | -1.980 | -2.222 |
| detected_error_marker_end | 16 | -3.336 | -1.849 | -1.621 | -1.526 | -2.812 | -2.164 |
| post_error_240chars | 16 | -4.643 | -2.543 | -1.861 | -1.762 | -4.079 | -2.623 |
| repair_trigger_end | 16 | -5.258 | -3.293 | -2.578 | -2.437 | -5.326 | -3.024 |
| post_repair_240chars | 16 | -5.115 | -3.519 | -2.629 | -2.455 | -5.625 | -3.200 |
| completion_end | 16 | -1.601 | -3.258 | -1.179 | -1.101 | -4.176 | -3.031 |

### Qwen3.5-27B

- Result / 结果：`results/E131_e119_e146_hidden_localization/qwen35_27b_e131_hidden_localization_mixed_chat.json`
- Cache / 激活缓存：`results/E131_e119_e146_hidden_localization/qwen35_27b_e131_component_cache_mixed_chat.pt`
- Best hidden/component / 最强方向：`34:residual_hidden_state`；selected layers=[32, 33, 34, 35, 36]
- Leakage audit / 泄露审计：error_span=0, gold=0, labels=0.

| Slice / 切片 | n | accept rate / 接受率, Wilson 95% CI | mean Yes-No | mean best component |
|---|---:|---:|---:|---:|
| strict_valid | 15 | 15/15 = 1.000 [0.796, 1.000] | 3.308 | 1.105 |
| repaired_acpi | 133 | 4/133 = 0.030 [0.012, 0.075] | -3.544 | -2.208 |

| Stage / 阶段 | n | accept rate / 接受率, Wilson 95% CI | mean Yes-No | mean best component |
|---|---:|---:|---:|---:|
| first_final_answer_end | 24 | 5/24 = 0.208 [0.092, 0.405] | -4.516 | -1.667 |
| detected_error_marker_end | 19 | 0/19 = 0.000 [0.000, 0.168] | -6.579 | -2.387 |
| post_error_240chars | 19 | 0/19 = 0.000 [0.000, 0.168] | -3.033 | -2.961 |
| repair_trigger_end | 19 | 1/19 = 0.053 [0.009, 0.246] | -2.513 | -3.539 |
| post_repair_240chars | 19 | 0/19 = 0.000 [0.000, 0.168] | -2.842 | -3.958 |
| completion_end | 24 | 7/24 = 0.292 [0.149, 0.492] | -0.615 | 0.107 |

Repaired ACPI stage movement / 已修复 ACPI 的阶段移动：

| Stage / 阶段 | n | accept rate / 接受率, Wilson 95% CI | mean Yes-No | mean best component |
|---|---:|---:|---:|---:|
| first_final_answer_end | 19 | 0/19 = 0.000 [0.000, 0.168] | -6.579 | -2.387 |
| detected_error_marker_end | 19 | 0/19 = 0.000 [0.000, 0.168] | -6.579 | -2.387 |
| post_error_240chars | 19 | 0/19 = 0.000 [0.000, 0.168] | -3.033 | -2.961 |
| repair_trigger_end | 19 | 1/19 = 0.053 [0.009, 0.246] | -2.513 | -3.539 |
| post_repair_240chars | 19 | 0/19 = 0.000 [0.000, 0.168] | -2.842 | -3.958 |
| completion_end | 19 | 2/19 = 0.105 [0.029, 0.314] | -1.586 | -0.112 |

Component projection means for repaired ACPI / 已修复 ACPI 的组件投影均值：

| Stage / 阶段 | n | residual hidden state | mlp output | token mixer output | post attention norm output |
|---|---:|---:|---:|---:|---:|
| first_final_answer_end | 19 | -2.387 | -1.440 | -1.327 | -3.165 |
| detected_error_marker_end | 19 | -2.387 | -1.440 | -1.327 | -3.165 |
| post_error_240chars | 19 | -2.961 | -1.617 | -1.339 | -3.719 |
| repair_trigger_end | 19 | -3.539 | -1.728 | -1.310 | -4.956 |
| post_repair_240chars | 19 | -3.958 | -2.089 | -1.535 | -5.434 |
| completion_end | 19 | -0.112 | 0.476 | -0.627 | -0.985 |

## Interpretation / 解析

- Qwen3.5-27B 与 Gemma4-31B-it：strict-valid rows 的 Yes/No margin 和 residual/component 投影为正；repaired ACPI 在 error/repair prefix 上明显转负，说明过程错误不是只在输出文字里，verifier 内部状态也有对应移动。
- Gemma4-26B-A4B-it：两条 unrepaired ACPI 在错误标记附近被拒绝，但 completion 阶段又被接受；best component score 仍低于 strict-valid。这是当前最有价值的错配证据：内部有较弱/负向过程信号，最终 Yes/No 仍被答案自洽和后文牵回。
- MLP/token-mixer/attention 相关组件的分数也随 prefix 变化，但本报告只把它们作为 component-level observability；真正的因果组件结论仍需要后续 E122/E126 做 activation steering 或 span patch。
- 本结果支持“过程证据存在但被 objective/threshold/readout/answer-anchor/repair-aware policy 错配使用”的链条；不支持把 hidden probe 写成完整机制电路，也不支持说自然 unrepaired ACPI 高频。

## Audit Boundary / 审计边界

- Direct/non-thinking verifier replay only；不代表 thinking verifier 的完整行为。
- E61 方向来自受控任务，E131 是跨任务投影诊断；这增强泛化证据，但不是因果干预。
- Error spans and manual labels are never included in verifier prompts; they are offline audit metadata used for selecting prefixes. / 错误 span 与人工标签没有进入 verifier prompt。
- Accept-rate CI uses Wilson 95%; mean Yes-No/component CI in JSON uses normal approximation and should be treated as descriptive. / 接受率用 Wilson 95%，均值 CI 只是描述性。
