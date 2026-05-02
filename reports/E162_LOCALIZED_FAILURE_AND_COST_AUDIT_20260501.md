# E162 Localized Failure and Completion Cost Audit / E162 localized 失败与 completion 成本审计

Date / 日期：2026-05-01T20:15:46

## Adjustment / 修正口径

- Prompt tokens are treated as nearly free because prompts are automatically generated. / 按用户要求，prompt tokens 基本不计入主要成本。
- Primary cost is completion tokens. / 主要成本口径是 completion tokens。
- Unit-format false negatives are corrected when numeric value matches gold. / unit 题如果 `100 m` 对 gold `100`、`3 km` 对 gold `3`，按数值等价修正为正确。

## Cost Per Success / 单次成功 completion 成本

### qwen35_27b

| variant | raw correct | adjusted correct | total completion tokens | raw cost/success | adjusted cost/success | hit-max |
|---|---:|---:|---:|---:|---:|---:|
| baseline_regenerate | 41/43 | 43/43 | 21288 | 519.2 | 495.1 | 0 |
| prefix_continue | 37/43 | 38/43 | 19304 | 521.7 | 508.0 | 0 |
| generic_error_prompt | 41/43 | 43/43 | 25841 | 630.3 | 601.0 | 1 |
| localized_error_prompt | 41/43 | 43/43 | 17853 | 435.4 | 415.2 | 0 |
| oracle_error_prompt | 41/43 | 43/43 | 14616 | 356.5 | 339.9 | 0 |
| random_location_prompt | 41/43 | 42/43 | 34469 | 840.7 | 820.7 | 2 |

### gemma4_31b_it

| variant | raw correct | adjusted correct | total completion tokens | raw cost/success | adjusted cost/success | hit-max |
|---|---:|---:|---:|---:|---:|---:|
| baseline_regenerate | 37/43 | 39/43 | 15821 | 427.6 | 405.7 | 0 |
| prefix_continue | 37/43 | 39/43 | 8206 | 221.8 | 210.4 | 0 |
| generic_error_prompt | 38/43 | 39/43 | 13429 | 353.4 | 344.3 | 0 |
| localized_error_prompt | 38/43 | 40/43 | 11538 | 303.6 | 288.4 | 0 |
| oracle_error_prompt | 40/43 | 42/43 | 9258 | 231.4 | 220.4 | 0 |
| random_location_prompt | 38/43 | 40/43 | 8994 | 236.7 | 224.8 | 0 |

### gemma4_26b_a4b_it

| variant | raw correct | adjusted correct | total completion tokens | raw cost/success | adjusted cost/success | hit-max |
|---|---:|---:|---:|---:|---:|---:|
| baseline_regenerate | 40/43 | 42/43 | 18076 | 451.9 | 430.4 | 0 |
| prefix_continue | 36/43 | 38/43 | 12457 | 346.0 | 327.8 | 0 |
| generic_error_prompt | 37/43 | 38/43 | 16854 | 455.5 | 443.5 | 0 |
| localized_error_prompt | 39/43 | 40/43 | 17058 | 437.4 | 426.4 | 0 |
| oracle_error_prompt | 41/43 | 43/43 | 14175 | 345.7 | 329.7 | 0 |
| random_location_prompt | 38/43 | 40/43 | 13968 | 367.6 | 349.2 | 0 |

## Localized Failures / localized 失败

- Raw localized failures / 原始 localized 失败：11.
- Unit-format false negatives / unit 格式假阴性：5.
- Adjusted true localized failures / 修正后真实 localized 失败：6.

- `gemma4_31b_it` `e159_multilingual_semantic_04`: final `4` vs gold `7`, span ``zhengshu` means positive integers only`, tokens 253.
- `gemma4_31b_it` `e159_multilingual_semantic_01`: final `5` vs gold `7`, span `must be a multiple of 3`, tokens 317.
- `gemma4_31b_it` `e159_multilingual_semantic_01`: final `2` vs gold `7`, span `is a multiple of 3`, tokens 271.
- `gemma4_26b_a4b_it` `e159_multilingual_semantic_01`: final `12` vs gold `7`, span `means at least 3 in magnitude`, tokens 469.
- `gemma4_26b_a4b_it` `e159_multilingual_semantic_01`: final `5` vs gold `7`, span `must be a multiple of 3`, tokens 816.
- `gemma4_26b_a4b_it` `e159_multilingual_semantic_01`: final `5` vs gold `7`, span `is a multiple of 3`, tokens 716.

## Hidden Follow-Up / hidden 后续

- Hidden deep-dive is not needed for unit-format rows; they are scoring false negatives. / unit 格式行不需要 hidden 深挖，它们是判分假阴性。
- Hidden deep-dive is useful for the remaining romanized multilingual semantic failures. / 剩余罗马化多语言语义失败值得做 hidden 深挖。
- Compare true-error localized prompts against oracle prompts at problem end, wrong-prefix end, localized prompt end, and completion end. / 比较 true-error localized 与 oracle，在题目末尾、错误前缀末尾、localized prompt 末尾、completion 末尾的 hidden 状态。

