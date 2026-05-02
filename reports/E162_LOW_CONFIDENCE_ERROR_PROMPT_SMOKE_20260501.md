# E162 Low-Confidence Error-Prompt Smoke / E162 低置信截断错误提示 smoke

## Pipeline / 流程

E162 tests whether a non-thinking model can recover from a process-wrong prefix when the intervention gives different amounts of error-location information. The prefill is causal: it contains only the problem and the trace prefix before the original final answer. Gold answers, labels, and offline error types are not placed in blind prompts.

E162 测试 non-thinking 模型在看到“已经走错一步的前缀”后，是否能靠不同强度的错误位置信息改回正确答案。prefill 是因果的：只包含题目和原 trace 的前缀，不包含原最终答案之后的内容。blind prompt 不放 gold answer、人工标签或离线错误类型。

Artifacts / 产物：

- Case builder / case 构造：`scripts/build_e162_low_confidence_error_prompt_cases.py`
- Static audit / 静态审计：`scripts/audit_e162_case_bank_and_prompts.py`
- Runner / 运行脚本：`scripts/run_e162_low_confidence_error_prompt_repair.py`
- Case bank / case bank：`data/processed/e162_low_confidence_error_prompt_cases_20260501.jsonl`
- Static audit JSON / 静态审计 JSON：`reports/E162_LOW_CONFIDENCE_ERROR_PROMPT_STATIC_AUDIT_20260501.json`
- Smoke result / smoke 结果：`results/E162_low_confidence_error_prompt_repair/gemma4_31b_it_e162_baseline_regenerate_prefix_continue_generic_error_prompt_localized_error_prompt_oracle_error_prompt_random_location_prompt_smoke_first_sample_20260501.json`

Case bank / 样本库：43 cases total = 3 generated wrong traces + 40 controlled invalid answer-preserving traces. All 43 prefixes exclude `Final answer:`. Static audit checked 258 prompts and passed with zero issues.

样本库：共 43 个 case = 3 个自然生成的“过程错且答案错” trace + 40 个受控“过程错但答案保持” trace。43 个 prefix 都不含 `Final answer:`。静态审计检查 258 个 prompt，0 issue。

## Smoke Sample / 首个样本

Model / 模型：`gemma4_31b_it` dense, non-thinking, temperature 0.0.

Case / 样本：`e162_generated_wrong_gemma4_31b_it_e159_multilingual_semantic_01_solve_neutral`.

Problem / 题目：`Qiu zhengshu x de geshu: -8 <= x <= 8, qie |x| zhi duo wei 3.`

Original failure / 原始错误：Gemma dense reads `zhi duo wei 3` as “multiple/divisible by 3,” not “at most 3,” and outputs 5 instead of gold 7. This is process-wrong and answer-wrong, not ACPI.

原始错误：Gemma dense 把 `zhi duo wei 3` 读成“3 的倍数”，而不是“至多为 3”，所以输出 5 而不是 7。这是“过程错且答案错”，不是 ACPI。

## Prompt Conditions / Prompt 条件

- `baseline_regenerate`: solve from problem only. / 只看题目重新作答。
- `prefix_continue`: continue after the wrong prefix with no warning. / 接着错误前缀续写，不提示错误。
- `generic_error_prompt`: say a hidden monitor raised a low-confidence warning somewhere. / 只泛泛提示“某处低置信”。
- `localized_error_prompt`: flag the visible phrase `must be a multiple of 3` and ask the model to recheck the original wording. / 明确指出 `must be a multiple of 3` 可疑，让模型回看原文。
- `oracle_error_prompt`: explicitly says `zhi duo wei 3` means at most 3, not multiple/divisible by 3. / 上界条件，明确说明 `zhi duo wei 3` 是“至多为 3”。
- `random_location_prompt`: flag unrelated span `Qiu zhengshu x de geshu`. / 随机指出无关位置。

## Smoke Results / Smoke 结果

| condition | final | correct | behavior |
|---|---:|---:|---|
| `baseline_regenerate` | 5 | no | repeats the original semantic misread |
| `prefix_continue` | 5 | no | continues the wrong prefix |
| `generic_error_prompt` | 5 | no | warning is too vague; no repair |
| `localized_error_prompt` | 7 | yes | reinterprets `zhi duo wei 3` as at most 3 |
| `oracle_error_prompt` | 7 | yes | follows oracle semantic hint |
| `random_location_prompt` | 5 | no | checks unrelated phrase, does not false-correct |

中文解释：baseline、直接续写、generic warning、random location 都继续得到错答案 5；localized 和 oracle 都改成正确答案 7。这个 smoke 很干净地支持 E162 的核心假设：泛泛的“可能有错”不足以修复，但局部错误位置提示可以在 non-thinking 模式下触发有效纠错；随机位置不会随便导致误修复。

## Interpretation / 解释

This smoke supports running E162 at larger scale. It also validates the causal-prefix constraint: the model only saw the bad local interpretation before the final answer, and localized/oracle prompts changed the continuation. This is exactly the setting we need before adding automatic logprob or hidden-residual triggers in E163.

这个 smoke 支持扩大 E162。它也验证了因果 prefill 约束：模型只看到最终答案之前的错误局部解释；localized/oracle prompt 改变了后续生成。E163 再把人工 span 替换为 logprob/hidden residual 触发点。
