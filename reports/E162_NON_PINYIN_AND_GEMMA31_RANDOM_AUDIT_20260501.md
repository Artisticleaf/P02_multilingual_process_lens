# E162 Non-Pinyin Main Audit and Gemma31 Random Comparison / E162 去拼音主结果与 Gemma31 random 对照

Date / 日期：2026-05-01T23:08:52

## Exclusion / 排除口径

- Original logs are preserved. / 原始日志保留。
- Main-result statistics exclude pinyin/romanized cases containing `zhi duo wei`, `zhengshu`, `shu chu`, or `qiu zhengshu`. / 主结果排除包含这些拼音/罗马化表达的样本。
- These cases may remain exploratory language-trait cases, but they no longer support the main multilingual-semantic claim. / 这些样本可作为探索性语言特质样本，但不进入多语义主 claim。
- Unit answers are judged by numeric equivalence when units are present. / unit 题按数值等价修正判分。

## Main Statistics / 主统计

### qwen35_27b

- Kept / 保留：38 cases, 228 rows.
- Excluded / 排除：5 cases, 30 rows.

| variant | adjusted correct | completion cost/success | total completion tokens | hit-max |
|---|---:|---:|---:|---:|
| `baseline_regenerate` | 38/38 | 495.6 | 18833 | 0 |
| `prefix_continue` | 37/38 | 418.0 | 15465 | 0 |
| `generic_error_prompt` | 38/38 | 627.4 | 23840 | 1 |
| `localized_error_prompt` | 38/38 | 406.1 | 15431 | 0 |
| `oracle_error_prompt` | 38/38 | 328.0 | 12463 | 0 |
| `random_location_prompt` | 38/38 | 580.1 | 22043 | 1 |

### gemma4_31b_it

- Kept / 保留：38 cases, 228 rows.
- Excluded / 排除：5 cases, 30 rows.

| variant | adjusted correct | completion cost/success | total completion tokens | hit-max |
|---|---:|---:|---:|---:|
| `baseline_regenerate` | 38/38 | 358.7 | 13632 | 0 |
| `prefix_continue` | 38/38 | 187.4 | 7121 | 0 |
| `generic_error_prompt` | 38/38 | 304.2 | 11559 | 0 |
| `localized_error_prompt` | 38/38 | 264.6 | 10055 | 0 |
| `oracle_error_prompt` | 38/38 | 207.4 | 7880 | 0 |
| `random_location_prompt` | 38/38 | 202.1 | 7680 | 0 |

### gemma4_26b_a4b_it

- Kept / 保留：38 cases, 228 rows.
- Excluded / 排除：5 cases, 30 rows.

| variant | adjusted correct | completion cost/success | total completion tokens | hit-max |
|---|---:|---:|---:|---:|
| `baseline_regenerate` | 38/38 | 422.2 | 16043 | 0 |
| `prefix_continue` | 38/38 | 276.5 | 10507 | 0 |
| `generic_error_prompt` | 38/38 | 384.1 | 14594 | 0 |
| `localized_error_prompt` | 38/38 | 369.2 | 14030 | 0 |
| `oracle_error_prompt` | 38/38 | 332.5 | 12635 | 0 |
| `random_location_prompt` | 38/38 | 313.6 | 11916 | 0 |

## Gemma31 Localized vs Random / Gemma31 localized 与 random 逐例比较

- Non-pinyin pair count / 去拼音成对样本：38.
- Accuracy / 准确率：localized 38/38, random 38/38.
- Accuracy disagreements / 准确率分歧：0.
- Token delta / token 差：localized - random mean 62.5, median 67.5.

Interpretation / 解读：random is not more accurate on Gemma31 after pinyin removal; it is only shorter in completion tokens. / 去拼音后 random 在 Gemma31 上不是更准，只是输出更短。

Why random is shorter / 为什么 random 更短：

- Random spans often point to broad problem-text fragments. / random span 常指向宽泛题干片段。
- Gemma31 treats those spans as a request to reread the problem and directly recompute. / Gemma31 会把它当成重读题目并直接重算。
- Localized prompts name the specific bad step, so Gemma31 usually explains why that step is wrong before recomputing. / localized 指出具体错步，Gemma31 往往先解释错在哪里再重算。
- Therefore localized carries clearer process evidence, while random carries a shorter but less specific re-solve behavior. / 因此 localized 的过程证据更清楚；random 是更短但不局部的重解。

Top random-cheaper examples / random 更短的代表样本：

| task | family | delta loc-rnd | localized span | random span |
|---|---|---:|---|---|
| `e159_probability_conditioning_03` | `probability_conditioning` | 159 | `the other child has probability 1/2` | `A family has two children` |
| `e159_probability_conditioning_04` | `probability_conditioning` | 141 | `4 kings among 13 ranks, so 4/13` | `A card is drawn from a standard deck` |
| `e159_code_boundary_zero_04` | `code_boundary_zero` | 140 | ``[0:5]` excludes both endpoints` | `What does this Python expression evaluate` |
| `e159_algebra_sign_symmetry_02` | `algebra_sign_symmetry` | 132 | `roots are x=-12 and x=8` | `How many integer x in` |
| `e159_code_boundary_zero_02` | `code_boundary_zero` | 126 | `range(4) gives j=1,2 only` | `What does this Python code print` |
| `e159_multilingual_semantic_02` | `multilingual_semantic` | 125 | `Both endpoints are excluded` | `Count integers x with -4` |
| `e159_proof_invalid_lemma_04` | `proof_invalid_lemma` | 122 | `12 and 3 are both multiples of 3` | `Claim` |
| `e159_temporal_boundary_03` | `temporal_boundary` | 120 | `Count Thursday as day 1` | `If today is Thursday` |

Conclusion / 结论：for main non-pinyin evidence, localized is useful and cheaper than generic, but random is a strong re-solve baseline on Gemma31. / 对去拼音主证据，localized 有用且比 generic 省，但 random 在 Gemma31 上是强重解基线。
