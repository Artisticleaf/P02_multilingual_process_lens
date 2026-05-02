# E162 Localized vs Random Interpretation / localized 与 random 的阶段性解读

Date / 日期：2026-05-01

## Core Answer / 核心回答

Localized performance supports the project only when it is a differential gain over generic and random controls. / localized 性能只有在相对 generic 和 random 对照有增量时，才真正支持我们的工作。

The strongest pattern is:

- `baseline_regenerate` wrong or repeats the source error. / 从头做错或重复源错误。
- `prefix_continue` continues the wrong prefix. / 直接续写沿着错前缀走。
- `generic_error_prompt` still fails. / 泛泛说可能有错仍失败。
- `random_location_prompt` still fails. / 随机位置对照仍失败。
- `localized_error_prompt` succeeds. / 指出真实局部 span 后成功。

This pattern supports the behavioral premise: if a future hidden monitor can localize the bad span, non-thinking generation can use that local signal to repair. / 这个模式支持行为层前提：如果未来 hidden monitor 能定位坏 span，non-thinking 生成可以利用这个局部信号修复。

Qwen35 current stage does not show strong localized-specific advantage because random and generic prompts often also repair. / 当前 Qwen35 阶段结果并没有显示强 localized-specific 优势，因为 random 和 generic prompt 经常也能修。
Cost note / 成本说明：localized is often shorter in output than generic on Qwen35, but this is not yet a fair total-cost claim because localized prompts themselves are longer. / 在 Qwen35 上 localized 往往比 generic 输出更短，但这还不能算公平的总成本结论，因为 localized prompt 本身更长。

Gemma dense smoke does show the clean localized pattern on `zhi duo wei 3`: baseline, prefix, generic, and random fail; localized and oracle succeed. / Gemma dense smoke 在 `zhi duo wei 3` 上显示了干净的 localized 模式：baseline、续写、generic、random 失败；localized 和 oracle 成功。

## `zhiduowei3` Sample Boundary / `zhiduowei3` 样本边界

`zhi duo wei 3` is not a standard way to write Chinese in a formal math benchmark. / `zhi duo wei 3` 不是正式数学 benchmark 里标准的中文写法。

It is romanized Chinese / pinyin-like transliteration of `至多为 3`, meaning `at most 3`. / 它是 `至多为 3` 的罗马化中文/拼音式转写，意思是“至多为 3”。

It is useful but must be framed narrowly:

- Good use / 好用途：tests romanized Chinese and code-mixed semantic parsing. / 测试罗马化中文和中英/拼音混合语义解析。
- Bad overclaim / 不能过度主张：do not claim it represents standard written Chinese mathematical understanding. / 不能说它代表标准中文数学理解。
- Needed controls / 需要对照：Chinese characters `至多为 3`, pinyin with spaces, English `at most 3`, English `no more than 3`, and symbolic `|x|<=3`. / 需要加中文字符、带空格拼音、英文 at most/no more than、符号表达对照。

Why it stayed in the sample bank / 为什么保留它：

- It produced a real Gemma dense semantic failure in E159. / 它在 E159 中诱发了真实 Gemma dense 语义失败。
- E162 smoke showed a clean repair split: localized and oracle repaired, generic and random did not. / E162 smoke 显示了干净修复分裂：localized 和 oracle 修复，generic 与 random 不修。
- It is therefore high value as a case study, but not enough as a broad Chinese claim by itself. / 因此它是高价值 case study，但单独不足以支撑宽泛中文 claim。

## Random Span Confound / random span 混杂

Qwen35 random-location prompts often trigger global re-auditing. / Qwen35 的 random-location prompt 经常触发全局重审。

This should be recorded as non-thinking global re-audit tendency, not as proof of hidden localized correction. / 这应记为 non-thinking 的全局重审倾向，而不是 hidden 局部纠错证据。

Important wording / 重要措辞：

- We should not say Qwen entered true hidden `thinking` mode. / 不应说 Qwen 进入了真正 hidden thinking 模式。
- We should say the random warning induced visible global rechecking behavior under non-thinking decoding. / 应说随机 warning 在 non-thinking 解码下诱发了可见的全局复查行为。
- `prefix_continue` failures should be recorded as "misled non-thinking continuation by a causal wrong prefix." / `prefix_continue` 失败应如实记录为“因果错误前缀误导 non-thinking 续写”。

## Impact on Next Experiments / 对后续实验设计的影响

1. Report differential localized uplift, not just localized accuracy. / 报告 localized 的相对增量，而不是只报 localized 准确率。
2. Split repair categories: baseline already correct, prefix misled, generic repair, localized-only repair, oracle repair, and random-triggered repair. / 分开统计：从头已正确、前缀带偏、泛泛修复、localized 独有修复、oracle 修复、random 触发修复。
3. Treat Qwen35 as a strong repair/global-audit model, not the cleanest model for localized-specific evidence. / 把 Qwen35 视为强修复/强全局审计模型，而不是最干净的 localized-specific 证据模型。
4. Prioritize Gemma dense for clean localized-vs-random evidence because the smoke already showed the desired split. / 优先用 Gemma dense 寻找干净 localized-vs-random 证据，因为 smoke 已显示目标分裂。
5. Improve random controls: use unrelated problem-text spans, neutral formatting spans, and spans from a different sentence; then report them separately. / 改进 random 对照：使用无关题目 span、中性格式 span、不同句子 span，并分开报告。
6. For E163 hidden-state work, do not infer localization from prompting alone; use teacher-forced replay and compare true error span vs random spans. / E163 不从 prompt 行为直接推断定位；要用 teacher-forced replay 比较真错 span 与 random span。

## Cross-Model Cost View / 跨模型成本视角

Median generated tokens / 生成 token 中位数：

- Qwen35-27B: baseline 431, generic 382, localized 327, oracle 276, random 309. / Qwen35-27B 的输出 token 中位数依次为 431、382、327、276、309。
- Gemma4-31B dense: baseline 382, generic 282, localized 253, oracle 188, random 181. / Gemma4-31B dense 的输出 token 中位数依次为 382、282、253、188、181。
- Gemma4-26B-a4b: baseline 412, generic 343, localized 342, oracle 310, random 308. / Gemma4-26B-a4b 的输出 token 中位数依次为 412、343、342、310、308。

Interpretation / 解释：

- Localized is not uniformly the shortest completion, but it is usually shorter than baseline and often shorter than generic on Qwen35 and Gemma4-31B. / localized 不是统一最短，但通常比 baseline 短，在 Qwen35 和 Gemma4-31B 上也常比 generic 短。
- For Gemma4-26B-a4b, localized does not beat generic on output length, so a “localized is cheaper” claim would be too strong without budget-normalized totals. / 对 Gemma4-26B-a4b，localized 在输出长度上并不优于 generic，因此没有预算归一化之前不能说 localized 更便宜。

## Gemma Dense Token Setting / Gemma dense token 设置

The highmax launcher uses `MAX_NEW_TOKENS=8192` for all full E162 models, including `gemma4_31b_it`. / highmax 队列对所有 E162 全量模型都使用 `MAX_NEW_TOKENS=8192`，包括 `gemma4_31b_it`。

Current status / 当前状态：Qwen35 is still running; Gemma dense full highmax has not started yet. / Qwen35 仍在运行，Gemma dense highmax 全量尚未开始。

Therefore the future Gemma dense full run is correctly configured with the higher token budget, but its output has not yet been produced. / 因此后续 Gemma dense 全量运行的 token 上限已经正确设置，但结果尚未产出。
