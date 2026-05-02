# E171 Main-Claim Hidden Rescue Stage Analysis / E171 主 claim hidden rescue 阶段分析

Created / 创建时间：`2026-05-02T13:33:42`.

Scope / 范围：E171 keeps only original-problem non-thinking baseline failures, then uses a hidden monitor over the model's own wrong trace to choose a causal truncation point. / E171 只保留原题 non-thinking baseline 做错的题，再在模型自己的错误 trace 上用 hidden monitor 选择因果截断点。

Claim boundary / claim 边界：`hidden_generic_warning` and `hidden_localized_warning` are text interventions derived from hidden signals. The hidden measurement itself is the teacher-forced component cache saved in `.pt`. / `hidden_generic_warning` 与 `hidden_localized_warning` 是由 hidden 信号导出的文字干预；真正的 hidden 测量是保存的 `.pt` component cache。

## qwen35_27b

- Source / 来源：`results/E171_main_claim_hidden_rescue/qwen35_27b_e171_hidden_rescue_max16384_20260502.json`
- Baseline-wrong cases / baseline 错题 case：1; complete variant sets / 变体齐全：1.
- Hidden threshold crossed / hidden 阈值触发：0; fallback top-risk / 未触发时 top-risk fallback：1.
- Leakage counts / 泄漏计数：`{'gold_answer_in_prompt_rows': 0, 'manual_label_in_prompt_rows': 0, 'localized_prompt_rows': 1, 'random_prompt_rows': 1}`.

| variant | n | rescued | rescue rate | completion tokens | cost/success | mean tokens | hit-max | final marker |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_regenerate | 1 | 0 | 0.000 | 473 | NA | 473 | 0 | 1 |
| prefix_continue | 1 | 0 | 0.000 | 250 | NA | 250 | 0 | 1 |
| hidden_generic_warning | 1 | 0 | 0.000 | 359 | NA | 359 | 0 | 1 |
| hidden_localized_warning | 1 | 0 | 0.000 | 219 | NA | 219 | 0 | 1 |
| random_matched_warning | 1 | 0 | 0.000 | 481 | NA | 481 | 0 | 1 |

### Paired Deltas / 配对差异

| left vs right | pairs | left wins | right wins | p(left better) | two-sided p | acc delta | mean token delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| hidden_localized_warning - prefix_continue | 1 | 0 | 0 | NA | NA | 0.000 | -31 |
| hidden_localized_warning - hidden_generic_warning | 1 | 0 | 0 | NA | NA | 0.000 | -140 |
| hidden_localized_warning - random_matched_warning | 1 | 0 | 0 | NA | NA | 0.000 | -262 |
| hidden_localized_warning - baseline_regenerate | 1 | 0 | 0 | NA | NA | 0.000 | -254 |
| hidden_generic_warning - prefix_continue | 1 | 0 | 0 | NA | NA | 0.000 | 109 |

## gemma4_31b_it

- Source / 来源：`results/E171_main_claim_hidden_rescue/gemma4_31b_it_e171_hidden_rescue_max16384_20260502.json`
- Baseline-wrong cases / baseline 错题 case：3; complete variant sets / 变体齐全：3.
- Hidden threshold crossed / hidden 阈值触发：0; fallback top-risk / 未触发时 top-risk fallback：3.
- Leakage counts / 泄漏计数：`{'gold_answer_in_prompt_rows': 0, 'manual_label_in_prompt_rows': 0, 'localized_prompt_rows': 3, 'random_prompt_rows': 3}`.

| variant | n | rescued | rescue rate | completion tokens | cost/success | mean tokens | hit-max | final marker |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_regenerate | 3 | 0 | 0.000 | 1089 | NA | 363 | 0 | 3 |
| prefix_continue | 3 | 0 | 0.000 | 565 | NA | 188.333 | 0 | 3 |
| hidden_generic_warning | 3 | 0 | 0.000 | 935 | NA | 311.667 | 0 | 3 |
| hidden_localized_warning | 3 | 0 | 0.000 | 648 | NA | 216 | 0 | 3 |
| random_matched_warning | 3 | 0 | 0.000 | 918 | NA | 306 | 0 | 3 |

### Paired Deltas / 配对差异

| left vs right | pairs | left wins | right wins | p(left better) | two-sided p | acc delta | mean token delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| hidden_localized_warning - prefix_continue | 3 | 0 | 0 | NA | NA | 0.000 | 27.667 |
| hidden_localized_warning - hidden_generic_warning | 3 | 0 | 0 | NA | NA | 0.000 | -95.667 |
| hidden_localized_warning - random_matched_warning | 3 | 0 | 0 | NA | NA | 0.000 | -90 |
| hidden_localized_warning - baseline_regenerate | 3 | 0 | 0 | NA | NA | 0.000 | -147 |
| hidden_generic_warning - prefix_continue | 3 | 0 | 0 | NA | NA | 0.000 | 123.333 |

## gemma4_26b_a4b_it

- Source / 来源：`results/E171_main_claim_hidden_rescue/gemma4_26b_a4b_it_e171_hidden_rescue_max16384_20260502.json`
- Baseline-wrong cases / baseline 错题 case：2; complete variant sets / 变体齐全：2.
- Hidden threshold crossed / hidden 阈值触发：2; fallback top-risk / 未触发时 top-risk fallback：0.
- Leakage counts / 泄漏计数：`{'gold_answer_in_prompt_rows': 0, 'manual_label_in_prompt_rows': 0, 'localized_prompt_rows': 2, 'random_prompt_rows': 2}`.

| variant | n | rescued | rescue rate | completion tokens | cost/success | mean tokens | hit-max | final marker |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_regenerate | 2 | 0 | 0.000 | 808 | NA | 404 | 0 | 2 |
| prefix_continue | 2 | 0 | 0.000 | 513 | NA | 256.500 | 0 | 2 |
| hidden_generic_warning | 2 | 1 | 0.500 | 620 | 620.000 | 310 | 0 | 2 |
| hidden_localized_warning | 2 | 1 | 0.500 | 480 | 480.000 | 240 | 0 | 2 |
| random_matched_warning | 2 | 1 | 0.500 | 539 | 539.000 | 269.500 | 0 | 2 |

### Paired Deltas / 配对差异

| left vs right | pairs | left wins | right wins | p(left better) | two-sided p | acc delta | mean token delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| hidden_localized_warning - prefix_continue | 2 | 1 | 0 | 0.500 | 1.000 | 0.500 | -16.500 |
| hidden_localized_warning - hidden_generic_warning | 2 | 0 | 0 | NA | NA | 0.000 | -70 |
| hidden_localized_warning - random_matched_warning | 2 | 0 | 0 | NA | NA | 0.000 | -29.500 |
| hidden_localized_warning - baseline_regenerate | 2 | 1 | 0 | 0.500 | 1.000 | 0.500 | -164 |
| hidden_generic_warning - prefix_continue | 2 | 1 | 0 | 0.500 | 1.000 | 0.500 | 53.500 |

