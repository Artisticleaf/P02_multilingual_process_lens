# E139.5 Base Span Localization Format-Fixed Audit / 基线错步定位格式修复审计

Date / 日期：2026-04-30

## Purpose / 目的

E139 showed that the second-pass checker can quote the wrong step but still accept the trace under a repair-aware rubric. E139.5 asks a narrower question: before asking for a global accept/reject judgment, can the same model directly localize the visible wrong step under base/no-check and strengthened locate-only prompts? / E139 说明二次检查器能指出错步，但仍可能按 repair-aware 口径接受。E139.5 只问一个更窄的问题：在要求整体接受/拒绝之前，同一个模型能不能直接定位可见错步？

This run also fixes a Gemma31 formatting artifact. The earlier `results/E1395_base_span_localization/gemma4_31b_it_e1395_base_span_localization.json` should not be used for final E139.5 comparison because Gemma31 often produced a valid first answer and then repeated `thought + same answer` until `max_new_tokens`, which polluted `hit_max` and JSON parsing. / 本轮同时修复 Gemma31 的格式伪差：旧结果中 Gemma31 常先给出有效第一答案，然后重复输出，污染了 `hit_max` 和 JSON 解析，因此旧 Gemma31 文件不进入最终横向比较。

## Implementation / 实现

Script / 脚本：`scripts/run_e1395_base_span_localization.py`

Official result directory / 采纳结果目录：`results/E1395_base_span_localization_format_fixed/`

Prompt variants / prompt 变体：

- `base_span_only`: simple locate-only block; no global accept/reject. / 简单只定位错步，不做整体接受/拒绝。
- `strong_span_only`: explicitly says the candidate solution is not the model's CoT, later correct arithmetic does not erase earlier visible wrong steps, and the model must only localize errors. / 强调候选解不是模型自己的 CoT，后文正确计算不抹掉前文可见错步，只做错误定位。
- `direct_json_final_only`: one JSON object only. / 只输出一个 JSON 对象。

Format fix / 格式修复：

- Added stop-at-first-answer: block prompts stop at first `</SPAN_AUDIT>`, JSON prompts stop at the first closing brace. / 加入首个答案即停止。
- Strengthened prompt: no explanation before/after the final block; first generated token should be `<` for block prompts. / 强化 prompt，禁止块前块后解释。
- JSON parser now extracts the first balanced JSON object instead of taking the first `{` and last `}`. / JSON 解析器改为读取第一个完整 JSON 对象。

Leakage boundary / 泄露边界：prompts contain only the problem and visible candidate solution. Manual labels, gold answers, and expected error spans are used only for offline selection/evaluation. / prompt 只含题目和可见候选解；人工标签、答案、错误 span 只离线使用。

## Format Outcome / 格式结果

All three format-fixed runs have `parse_ok=1.0` and `hit_max=0.0`. / 三个模型修复后均 `parse_ok=1.0` 且 `hit_max=0.0`。

| Model | Jobs | Invalid rows | Valid controls | Parse OK | Hit max |
|---|---:|---:|---:|---:|---:|
| Qwen3.5-27B | 48 | 12 | 36 | 1.000 | 0.000 |
| Gemma4-31B-it | 36 | 9 | 27 | 1.000 | 0.000 |
| Gemma4-26B-A4B-it | 72 | 18 | 54 | 1.000 | 0.000 |

## Main Results / 主要结果

| Model | Invalid span hit | Wilson 95% CI | Valid false error | Wilson 95% CI |
|---|---:|---:|---:|---:|
| Qwen3.5-27B | 11/12 = 0.917 | [0.646, 0.985] | 0/36 = 0.000 | [0.000, 0.096] |
| Gemma4-31B-it | 6/9 = 0.667 | [0.354, 0.879] | 0/27 = 0.000 | [0.000, 0.125] |
| Gemma4-26B-A4B-it | 14/18 = 0.778 | [0.548, 0.910] | 3/54 = 0.056 | [0.019, 0.151] |

Plain facts / 说人话事实：

- Qwen can usually locate the wrong percentage-base step even without a repair-aware global judgment. Its only miss is one `direct_json_final_only` mixed-language row; base and strong block prompts locate all selected invalid rows. / Qwen 基本能在只定位 prompt 下圈出错步；唯一漏检是一个 mixed 的直接 JSON 输出。
- Gemma31 format is now clean. It localizes en_zh and mixed wrong steps but consistently misses the romanized_zh wrong step; this is now a semantic/language-route miss, not a formatting failure. / Gemma31 格式已清理干净；它能抓 en_zh 和 mixed，但稳定漏掉 romanized_zh，这是语义/语言路径问题，不是格式问题。
- Gemma26 is more unstable: it localizes many invalid rows, misses mixed rows, and produces three false errors on romanized_zh valid controls. / Gemma26 更不稳定：能抓不少错步，但漏掉 mixed，并在 romanized_zh 正确控制组上有 3 个误报。

## Interpretation / 解释

E139.5 supports the narrower mechanism claim: the models often have enough surface-visible information to point to the wrong step before making a global verifier decision. Therefore E136/E139 failures are not simply “the model cannot see any error.” The harder problem is how the decision objective/readout treats that evidence. / E139.5 支持更窄的机制 claim：模型常常在整体判定前就能定位错步，因此 E136/E139 的失败不能简单说成“模型看不见错误”。更关键的是 objective/readout 如何使用这份证据。

It also gives an important boundary: locate-only ability is not universal. Romanized Chinese and mixed-language traces expose language-route sensitivity, especially for Gemma31/Gemma26. Gemma26 false positives on valid romanized controls show that the process-risk signal/checker is not a perfect oracle and needs calibration. / 但定位能力不是无条件 oracle。罗马拼音中文和混合语言暴露了语言路径敏感性；Gemma26 在正确 romanized 控制组上误报，说明过程风险信号/检查器需要校准。

## Adopted vs Non-Adopted / 采纳与不采纳

Adopted / 采纳：`results/E1395_base_span_localization_format_fixed/`.

Diagnostic only / 仅作调试：`archive/e1395_format_debug_20260430/results/E1395_base_span_localization_gemma31_format_smoke/`, `archive/e1395_format_debug_20260430/results/E1395_base_span_localization_gemma31_format_smoke2/`, `archive/e1395_format_debug_20260430/results/E1395_base_span_localization_smoke/`.

Not adopted for final comparison / 不进入最终横向比较：`archive/e1395_format_debug_20260430/results/E1395_base_span_localization/gemma4_31b_it_e1395_base_span_localization.json`, because it used the pre-fix prompt/parser and contains repetition-induced format artifacts. / 旧 Gemma31 结果存在重复输出导致的格式伪差，不采纳。
