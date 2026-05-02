# E139 Check-Rationale Audit / E139 二次检查解释审计

- Created / 生成时间：`2026-04-30T20:42:25`
- Scope / 范围：只审计 E136 中 `base` 或二次 `check` 未能纠错的失败样本；不混入已成功纠错样本。
- Mode / 模式：`non-thinking` verifier generation only. Thinking smoke hit max-token and failed parse, so it is excluded from this failure-mechanism audit.
- Prompt boundary / prompt 边界：prompt 只包含题目、可见 trace，以及 local check 的 hidden-selected 可见片段；人工标签、gold answer、error-span annotation 不进入 prompt。
- Scientific question / 科学问题：E136 中 check 后仍放行，是因为模型看不见错步，还是因为看见错步后按 repair-aware 草稿口径放行？

## Inputs / 输入

- Source data / 源数据：`data/processed/e132_suspicious_valid_controls_20260430.jsonl`
- Source policy results / 源策略结果：`results/E136_suspicious_confidence_adaptive_check/`
- Runner / 运行脚本：`scripts/run_e139_check_rationale_audit.py`
- Queue / 队列脚本：`scripts/launch_e139_check_rationale_audit_queue_20260430.sh`
- Result dir / 结果目录：`results/E139_check_rationale_audit/`
- Queue status / 队列状态：`logs/e139_check_rationale_audit_status_20260430.jsonl` ended with `all_done`.

## Selected Rows / 选样

E139 使用 `selection=failure_only`。一行被选中必须同时满足：人工 strict 过程标签为 invalid，并且 E136 的 base 或 global/local check 至少有一个策略仍接受它。

| model | selected rows | jobs | selected audit idxs | task/variant | routes |
|---|---:|---:|---|---|---|
| `qwen35_27b` | 4 | 8 | 1320034, 1320044, 1320054, 1320059 | percentage_base::repaired_strict_invalid:4 | en_en:1, mixed:1, romanized_zh:1, zh_en:1 |
| `gemma4_31b_it` | 3 | 6 | 1320049, 1320054, 1320059 | percentage_base::repaired_strict_invalid:3 | en_zh:1, mixed:1, romanized_zh:1 |
| `gemma4_26b_a4b_it` | 6 | 12 | 1320034, 1320039, 1320044, 1320049, 1320054, 1320059 | percentage_base::repaired_strict_invalid:6 | en_en:1, en_zh:1, mixed:1, romanized_zh:1, zh_en:1, zh_zh:1 |

All selected rows are `percentage_base::repaired_strict_invalid`: the trace contains an explicit wrong percentage-increase statement, then later computes the final answer with the correct arithmetic. / 所有被选样本都是百分比基底任务中的 repaired strict-invalid：可见 trace 先写出明确错误的语义句，后文又用正确算法得到答案。

Failure policy counts / 失败策略计数：

| model | failed policy counts that caused selection |
|---|---|
| `qwen35_27b` | `plain_always_global_check_accept`:3, `plain_base_no_check_accept`:4, `plain_hidden_global_check_accept`:3, `plain_hidden_local_check_accept`:1, `strict_always_global_check_accept`:3, `strict_hidden_global_check_accept`:3, `strict_hidden_local_check_accept`:1 |
| `gemma4_31b_it` | `plain_always_global_check_accept`:2, `plain_base_no_check_accept`:3, `plain_hidden_global_check_accept`:2, `plain_hidden_local_check_accept`:2, `strict_always_global_check_accept`:2, `strict_base_no_check_accept`:1, `strict_hidden_global_check_accept`:2, `strict_hidden_local_check_accept`:2 |
| `gemma4_26b_a4b_it` | `plain_always_global_check_accept`:5, `plain_base_no_check_accept`:6, `plain_hidden_global_check_accept`:5, `plain_hidden_local_check_accept`:5, `strict_always_global_check_accept`:5, `strict_base_no_check_accept`:1, `strict_hidden_global_check_accept`:5, `strict_hidden_local_check_accept`:5 |

## Main Results / 主要结果

| model | parse ok | strict Yes | repair-aware Yes | wrong step quoted | later repaired Yes | hit max |
|---|---:|---:|---:|---:|---:|---:|
| `qwen35_27b` | 8/8 | 0/8 (0.000) | 5/8 (0.625) | 8/8 | 5/8 | 0/8 |
| `gemma4_31b_it` | 6/6 | 0/6 (0.000) | 6/6 (1.000) | 6/6 | 6/6 | 0/6 |
| `gemma4_26b_a4b_it` | 12/12 | 0/12 (0.000) | 12/12 (1.000) | 12/12 | 12/12 | 2/12 |

| model | global strict Yes | global repair-aware Yes | local strict Yes | local repair-aware Yes |
|---|---:|---:|---:|---:|
| `qwen35_27b` | 0/4 | 3/4 | 0/4 | 2/4 |
| `gemma4_31b_it` | 0/3 | 3/3 | 0/3 | 3/3 |
| `gemma4_26b_a4b_it` | 0/6 | 6/6 | 0/6 | 6/6 |

Plain-language conclusion / 说人话结论：这些失败样本里，模型不是看不见错步。三模型在解释式审计中都能引用或概括错步，并且 strict trace-as-proof 口径全部判 `No`。E136 的失败主要来自另一个环节：模型看见了错步，但把后文正确计算视为已经修复，于是在 repair-aware 口径下继续判 `Yes`。

This sharpens the claim: hidden risk trigger can select the bad rows, but the second-pass checker must be forced into the right evaluation policy. Otherwise it may read chain-of-thought as a repairable draft rather than as a strict proof. / 这让主张更精确：hidden 风险信号能挑出问题行，但二次检查器必须被约束到正确评价口径；否则它会把 CoT 当可修复草稿，而不是严格证明。

## Examples / 样例

### `qwen35_27b`
- `1320034` `global` `en_en`: wrong step = '"A 25% increase means the final price is 25% of the original"'; strict = `No`, repair-aware = `Yes`; reason = The trace contains a false definition of percentage increase, but the subsequent calculation correctly applies the increase to the original value, effectively discarding the erroneous logic.
- `1320034` `local` `en_en`: wrong step = '"A 25% increase means the final price is 25% of the original"'; strict = `No`, repair-aware = `No`; reason = The trace contains a false premise that is never explicitly retracted or corrected, even though the subsequent calculation accidentally yields the correct result.

### `gemma4_31b_it`
- `1320049` `global` `en_zh`: wrong step = '增加25%表示最终价格是原价的25%'; strict = `No`, repair-aware = `Yes`; reason = The first sentence contains a conceptual error, but the subsequent calculation correctly identifies the increment and adds it to the base.
- `1320049` `local` `en_zh`: wrong step = '增加25%表示最终价格是原价的25%'; strict = `No`, repair-aware = `Yes`; reason = The first sentence contains a conceptual error, but the subsequent calculation correctly treats the 25% as an addition to the original price.

### `gemma4_26b_a4b_it`
- `1320034` `global` `en_en`: wrong step = 'A 25% increase means the final price is 25% of the original, which would be 20.'; strict = `No`, repair-aware = `Yes`; reason = The error was immediately corrected by applying the proper logic for an increase.
- `1320034` `local` `en_en`: wrong step = 'A 25% increase means the final price is 25% of the original, which would be 20.'; strict = `No`, repair-aware = `Yes`; reason = The initial error was immediately corrected by the subsequent correct calculation.

## Audit / 审计

- `qwen35_27b` leakage passed = `True`; labels in prompt = 0, gold in prompt = 0, manual error span annotations in prompt = 0.
- `gemma4_31b_it` leakage passed = `True`; labels in prompt = 0, gold in prompt = 0, manual error span annotations in prompt = 0.
- `gemma4_26b_a4b_it` leakage passed = `True`; labels in prompt = 0, gold in prompt = 0, manual error span annotations in prompt = 0.

Caveats / 边界：

- E139 is not a natural prevalence experiment. It explains a selected E136 failure cluster. / E139 不是自然发生率实验，只解释 E136 的一个失败簇。
- The selected failure cluster is narrow: `percentage_base` repaired strict-invalid traces. It should be expanded to more task families before becoming a broad claim. / 当前失败簇较窄，需要扩展到更多任务族。
- Two Gemma26 romanized-zh generations hit `max_new_tokens`; parsed strict/repair decisions are still available, but those rows should be treated as lower-quality textual examples. / Gemma26 有两条 romanized-zh 生成触顶，判定字段可解析，但文本样例质量较低。
- Thinking-mode E139 is deferred. The smoke run showed thinking can consume the budget before emitting the final audit block, so it needs a separate final-contract prompt and larger token budget. / thinking 版本暂缓，需要单独设计收口 prompt 与更大 token 预算。

## Claim Update / 主张更新

E139 supports the narrower mechanism claim that second-pass verifier failures can occur after error detection: the model detects the wrong step, but the objective/readout makes it answer according to a repair-aware standard. This is different from saying the model has no process signal. / E139 支持更窄、更强的机制说法：二次 verifier 的失败可能发生在“已经看见错步之后”，因为 objective/readout 让它按 repair-aware 标准回答；这不是“模型没有过程信号”。
