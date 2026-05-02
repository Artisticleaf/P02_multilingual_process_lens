# E159-E161 Overnight Experiment Plan / E159-E161 过夜实验计划

Scope / 范围：围绕 non-thinking 主线，补充更强的 answer-preserving 困难样本、thinking COT 对照、以及受控找错/修复上界实验。

## Why / 为什么做

- E153 显示 dense/MoE 在自然 reasoning-first 解题中几乎都能做对，没有自然未修复 ACPI。这说明“单纯变难”不一定产生 ACPI；我们需要专门构造局部错误可以保留最终答案的场景。
- 顶刊/顶会需要的不只是个案：需要跨任务族、跨模型、跨模式的边界图谱。E159 扩展“可诱发性”，E160 补 thinking 对照，E161 测 blind 找错和 oracle-span 上界。
- 隐藏层解释不能直接建立在未审计生成上。E159/E160/E161 先产生可审计样本池，之后 E156 hidden replay 只对审计后的样本做 teacher-forced activation capture。

## Experiments / 实验

### E159 answer-preserving non-thinking generation

- Task bank：40 tasks = 10 families × 4 tasks.
- Families：algebra sign symmetry, counting complement, code boundary zero terms, table zero swaps, unit/percentage roundtrip, multilingual semantic, proof invalid lemma, graph definition, probability conditioning, temporal boundary.
- Prompt：只给题目，要求先推理后最终答案；不显示答案、trap note、人工标签或错误 span。
- Models：Qwen35-27B, Gemma4-31B-it, Gemma4-26B-A4B-it.
- Size：40 tasks × 3 prompts × 3 models = 360 generations.

### E160 thinking COT contrast

- Same 40 tasks and same three prompt variants.
- Mode：`enable_thinking=true`.
- Models：dense first, Qwen35-27B and Gemma4-31B-it. MoE thinking is deferred because it is more expensive and routing-specific.
- Size：40 tasks × 3 prompts × 2 dense models = 240 generations.
- Purpose：test whether thinking COT reduces semantic slips, increases repair, or changes ACPI/error-awareness patterns relative to non-thinking.

### E161 controlled error-finding and oracle-span repair

- Input：80 candidate traces = each E159 task has one valid reference and one invalid answer-preserving reference.
- Prompt variants：
  - `blind_global`: decide whether any wrong step exists.
  - `blind_localize_only`: only locate the first questionable step.
  - `oracle_span_repair`: explicitly says a hidden monitor flagged a visible span; this is an upper-bound intervention, not a blind detector.
- Models：Qwen35-27B, Gemma4-31B-it, Gemma4-26B-A4B-it.
- Size：80 candidate traces × 3 prompt variants × 3 models = 720 jobs.

## Safety / 如何保证不出错

- Static audit before launch：`py_compile` all new scripts; `bash -n` launcher.
- Scaffold smoke before launch：build task bank, verify 40 tasks and 80 candidate traces, inspect first generation prompt, confirm blind prompts do not expose error span, confirm oracle-span condition does expose the span only by design.
- Leakage policy：generation prompts contain only problem text. E161 blind prompts contain problem and proposed solution only. Only `oracle_span_repair` exposes the offline error span, and this is recorded as an explicit intervention condition.
- Queue discipline：single tmux queue, sequential model runs, no concurrent GPU jobs.
- Output discipline：checkpoints are JSONL; final outputs are JSON; status file records start/done per step.

## Expected outputs / 预期产物

- `data/processed/e159_answer_preserving_tasks_20260501.jsonl`
- `data/processed/e159_answer_preserving_candidate_solutions_20260501.jsonl`
- `results/E159_answer_preserving_difficult_generation/`
- `results/E160_thinking_answer_preserving_generation/`
- `results/E161_answer_preserving_error_repair/`
- `logs/e159_e161_overnight_status_20260501.jsonl`

## Claim boundary / claim 边界

E159-E161 are not final paper claims by themselves. They are sample-creation and behavioral-boundary experiments. Their outputs must be audited before being used for claims about ACPI prevalence, repair, or hidden-state localization.
