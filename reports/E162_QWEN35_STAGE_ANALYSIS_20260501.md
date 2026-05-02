# E162 Qwen35 Stage Analysis / Qwen35 阶段性分析

Date / 日期：2026-05-01

This is a stage audit of `qwen35_27b` E162 highmax checkpoint, not the final E162 analysis. / 这是 `qwen35_27b` E162 highmax checkpoint 的阶段性审计，不是 E162 最终全量分析。

## Scope / 范围

- Source / 数据源：`logs/e162_repair_qwen35_27b_highmax_checkpoint_20260501.jsonl`.
- Current rows / 当前行数：121 / 258.
- Retained rows / 断点保留：65 rows from the old 1024-token checkpoint had final markers and no hit-max. / 65 条旧 checkpoint 行有 final marker 且未 hit-max，被保留。
- Newly generated highmax rows / highmax 新生成：56 rows with `max_new_tokens=8192`. / 56 条在 8192 token 上限下新生成。
- Non-thinking status / 非 thinking 状态：new highmax rows record `thinking=false`; chat-template rows also record `chat_template_enable_thinking_false_requested=true`. / 新 highmax 行记录 `thinking=false`；使用 chat template 的新行还记录 `chat_template_enable_thinking_false_requested=true`。

## Current Statistics / 当前统计

By prompt variant / 按 prompt：

| variant | rows | final-correct | hit-max | no-final | new highmax rows |
|---|---:|---:|---:|---:|---:|
| baseline_regenerate | 21 | 21 | 0 | 0 | 11 |
| prefix_continue | 20 | 19 | 0 | 0 | 8 |
| generic_error_prompt | 20 | 20 | 0 | 0 | 9 |
| localized_error_prompt | 20 | 20 | 0 | 0 | 9 |
| oracle_error_prompt | 20 | 20 | 0 | 0 | 9 |
| random_location_prompt | 20 | 20 | 0 | 0 | 10 |

By family / 按 family：

| family | rows | final-correct | hit-max | no-final |
|---|---:|---:|---:|---:|
| algebra_sign_symmetry | 24 | 24 | 0 | 0 |
| code_boundary_zero | 24 | 24 | 0 | 0 |
| counting_complement | 24 | 24 | 0 | 0 |
| graph_definition | 24 | 24 | 0 | 0 |
| multilingual_semantic | 24 | 23 | 0 | 0 |
| probability_conditioning | 1 | 1 | 0 | 0 |

Main stage reading / 阶段性判断：

- Highmax fixed the truncation problem observed at 1024 tokens. / highmax 解决了 1024 token 下的截断问题。
- Qwen is very strong at answer recovery on the covered rows: 120/121 final-correct so far. / Qwen 在已覆盖行上的答案恢复很强：目前 120/121 final-correct。
- The only current final-wrong row is `e159_multilingual_semantic_04 / prefix_continue`, where an invalid prefix misleads the model into treating `zhengshu` as positive integers. / 当前唯一错答是 `e159_multilingual_semantic_04 / prefix_continue`，错误前缀把模型带偏为“正整数”解释。
- Random-location prompts often still lead Qwen to find the true error. This is scientifically important but also a confound: it means Qwen has a generic re-audit tendency, not only localized-span repair. / 随机位置提示常常仍让 Qwen 找到真错；这很重要，但也是混杂因素：说明 Qwen 有泛化重审倾向，而不只是局部 span 修复。

## Standard Samples / 标准样本

### 1. Standard Baseline Correct / 标准从头作答正确

- Task / 任务：`e159_multilingual_semantic_01`, `baseline_regenerate`.
- Problem / 题目：`Qiu zhengshu x de geshu: -8 <= x <= 8, qie |x| zhi duo wei 3.`
- Gold / 标准答案：7.
- Model final / 模型答案：7.
- Why standard / 为什么标准：from the problem alone, Qwen correctly reads `zhi duo wei 3` as `at most 3`, i.e. `|x|<=3`, and counts `-3,-2,-1,0,1,2,3`. / 只看题目时，Qwen 正确把 `zhi duo wei 3` 读成“至多为 3”，也就是 `|x|<=3`，并数出 7 个值。

### 2. Standard Localized Repair / 标准局部修复

- Task / 任务：`e159_multilingual_semantic_01`, `localized_error_prompt`.
- Bad prefix / 错误前缀："`zhi duo wei 3` means at least 3 in magnitude, but the listed values -3 through 3 give 7."
- Localized span / 局部 span：`means at least 3 in magnitude`.
- Model final / 模型答案：7.
- Why standard / 为什么标准：Qwen explicitly says `zhi duo` means "at most" and replaces the bad semantic step before continuing. / Qwen 明确说 `zhi duo` 是“至多”，并在继续前替换错误语义步骤。

### 3. Standard Code Boundary Repair / 标准代码边界修复

- Task / 任务：`e159_code_boundary_zero_01`, `localized_error_prompt`.
- Bad prefix / 错误前缀：`range(0,6) gives i=1,2,3,4`.
- Gold / 标准答案：-20.
- Model final / 模型答案：-20.
- Why standard / 为什么标准：Qwen correctly repairs Python `range(0,6)` to `0,1,2,3,4,5`; the omitted endpoints contribute zero, so the answer stays `-20` but the process becomes valid. / Qwen 正确把 Python `range(0,6)` 修为 `0,1,2,3,4,5`；被漏掉的端点贡献为 0，所以答案仍是 `-20`，但过程被修正。

### 4. Standard Counting Complement Repair / 标准补集计数修复

- Task / 任务：`e159_counting_complement_01`, `localized_error_prompt`.
- Bad prefix / 错误前缀：`desired subsets are those with sum less than half; complement symmetry gives 32`.
- Gold / 标准答案：32.
- Model final / 模型答案：32.
- Why standard / 为什么标准：Qwen flags the direction error, re-derives the complement bijection, and keeps the correct count. / Qwen 指出方向错误，重新用补集双射推导，并保留正确计数。

## Abnormal Samples / 异常样本

### 1. Random Location Still Repairs True Error / 随机位置也修复真错

- Task / 任务：`e159_graph_definition_01`, `random_location_prompt`.
- Random span / 随机 span：`A connected graph has degrees 1`.
- True bad step / 真实错步：`All vertices must have even degree for an Euler trail`.
- Gold / 标准答案：Yes.
- Model final / 模型答案：Yes.
- Why abnormal / 为什么异常：the random span is not the wrong reasoning step, but Qwen still notices that Euler trail allows exactly two odd vertices. This is useful, but it is not evidence that the random/localized span found the error; it is generic re-auditing. / 随机 span 并不是真错步，但 Qwen 仍发现 Euler trail 允许恰好两个奇度顶点。这有价值，但不能证明随机/局部 span 找到了错；这是泛化重审。

### 2. Prefix Misleads Model Despite Correct Baseline / 前缀带偏模型，尽管从头能做对

- Task / 任务：`e159_multilingual_semantic_04`, `prefix_continue`.
- Problem / 题目：`Shu chu -2 dao 4 zhi jian de zhengshu geshu, including both endpoints.`
- Bad prefix / 错误前缀：``zhengshu` means positive integers only, but including -2 through 4 gives 7.`
- Baseline final / 从头作答：7.
- Prefix final / 续写答案：4.
- Why abnormal / 为什么异常：Qwen accepts the wrong semantic premise in `prefix_continue` and counts only positive integers `1,2,3,4`. Generic/localized/oracle/random prompts repair it back to 7. / Qwen 在 `prefix_continue` 中接受错误语义前提，只数正整数 `1,2,3,4`；泛泛、局部、oracle、随机提示都能把它修回 7。

### 3. Random Location Repairs Multilingual Error / 随机位置修复多语言错误

- Task / 任务：`e159_multilingual_semantic_04`, `random_location_prompt`.
- Random span / 随机 span：problem text fragment `Shu chu -2 dao 4 zhi jian de zhengshu ges`.
- Model final / 模型答案：7.
- Why abnormal / 为什么异常：the random span overlaps broad problem wording, not the explicit bad prefix span, yet Qwen rechecks `zhengshu` and fixes the semantic error. This again shows random-location controls are not always inert for Qwen. / 随机 span 是题目宽泛片段，不是显式错误前缀 span，但 Qwen 仍重新检查 `zhengshu` 并修正语义错。这说明随机位置对 Qwen 不一定是惰性对照。

### 4. Hit-Max Resolved by Highmax / 截断由 highmax 解决

- Task / 任务：`e159_algebra_sign_symmetry_01`, `baseline_regenerate`.
- Old 1024-token run / 旧 1024 运行：hit-max, no final marker.
- Highmax run / 高 token 运行：1672 tokens, final marker found, final `127`, correct.
- Why abnormal / 为什么异常：this row looked like a failure only because the token cap was too small. The highmax rerun shows the correct interpretation is "incomplete generation under 1024", not answer failure. / 这行在旧设置下像失败，但只是 token cap 太小；highmax 证明它应解释为 1024 下生成未完成，不是答案失败。

## Interim Claim Update / 阶段性 claim 更新

- Qwen35 non-thinking can often repair controlled process-invalid prefixes, but this is not specific to localized prompts. / Qwen35 non-thinking 经常能修复受控错误前缀，但这种能力不只出现在 localized prompt。
- The strongest Qwen abnormal pattern is generic re-auditing: random-location prompts often trigger a full recheck and true-error repair. / Qwen 最强的异常模式是泛化重审：随机位置提示也经常触发全局复查和真错修复。
- The best future statistic is not just final accuracy; we must separate `localized-only repair`, `generic repair`, `random-triggered repair`, `prefix misled`, and `baseline already correct`. / 后续不能只看最终正确率，必须分开统计：只有局部提示能修、泛泛提示能修、随机提示也能修、前缀带偏、从头本来就会。
- `e159_multilingual_semantic_04 / prefix_continue` is a high-value sample for the project: from scratch Qwen solves correctly, but a wrong causal prefix can mislead non-thinking continuation; error prompts restore performance. / `e159_multilingual_semantic_04 / prefix_continue` 是高价值样本：Qwen 从头能做对，但错误因果前缀会带偏 non-thinking 续写；错误提示能恢复性能。

Detailed sampled rows / 详细抽样行：`reports/E162_QWEN35_STAGE_SAMPLE_CASES_20260501.json`.
