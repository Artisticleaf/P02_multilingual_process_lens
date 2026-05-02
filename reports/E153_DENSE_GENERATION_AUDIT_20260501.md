# E153 Dense Generation Audit / E153 dense 解题生成审计

Scope / 范围：Qwen35-27B 和 Gemma4-31B-it 的 E153 non-thinking generation，均为 dense 模型；MoE Gemma 单独后置分析。

Key definitions / 关键定义：
- `causal_prefill_usable`: trace 的可见顺序适合做因果 prefill 分析；它可以是正确 trace，也可以是错误 trace，用于研究模型怎样走向错误。
- `clean_valid_prefill_candidate`: 主 prefill/篡改种子；要求最终答案正确、最终保留推理有效、先推理后答案、没有显式修复/重想 marker、任务本身没有明显歧义。
- `language_trait_use`: 语言特质分析样本；包括语义误读、任务歧义、自检/重算语言、格式归一化问题、非典型推理顺序等。

Dense model summary / dense 模型摘要：

| model | rows | auto final correct | manual final correct | clean valid prefill candidates | language-trait traces | unrepaired ACPI |
|---|---:|---:|---:|---:|---:|---:|
| qwen35_27b | 96 | 90 | 96 | 89 | 19 | 0 |
| gemma4_31b_it | 96 | 88 | 93 | 90 | 14 | 0 |

Main findings / 主要发现：
- Qwen35-27B: all 96/96 rows are manually final-correct after normalizing quoted strings and unit suffixes. No unrepaired ACPI was found in this dense generation set.
- Gemma4-31B-it: 93/96 rows are manually final-correct. The 3 real failures are all the same pinyin multilingual semantic task under three prompts.
- The 11 automatic false negatives are parser issues, not model failures: quoted string `'bcd'` and unit forms such as `120m` or `120 meters` should count as correct.
- Both dense models mostly produce derivation-first traces under these prompts. This supports using many rows for causal prefill, but clean valid seeds should exclude ambiguous graph/Euler rows and explicit rethinking markers.
- The most informative dense failure is Gemma4-31B-it on `e153_multilingual_semantic_01`: it misreads romanized Chinese `zhi duo wei 4` as value/digit/tens/units conditions instead of `at most 4`. This is a high-value language-trait and multilingual semantic robustness sample.
- The first-sample phenomenon remains important: solving from scratch can be correct, while checking another trace can localize poorly. Generation competence and error-localization competence must be analyzed separately.

Error cases / 真错误样本：
- gemma4_31b_it e153_multilingual_semantic_01 solve_neutral: gold `9`, extracted `2`; multilingual_semantic_misparse; Final answer 2; model turns 至多为4 into |x|=4.
- gemma4_31b_it e153_multilingual_semantic_01 solve_terse: gold `9`, extracted `0`; multilingual_semantic_misparse; Final answer 0; model misreads both integer polarity and the pinyin phrase.
- gemma4_31b_it e153_multilingual_semantic_01 solve_self_check: gold `9`, extracted `1`; multilingual_semantic_misparse; Final answer 1; self-check reinforces the wrong semantic parse.

Normalization fixes / 自动解析假错：
- qwen35_27b e153_string_regex_parsing_02 solve_neutral: gold `bcd`, extracted `'bcd'` -> correct by `quoted_string_equivalent`.
- qwen35_27b e153_string_regex_parsing_02 solve_terse: gold `bcd`, extracted `'bcd'` -> correct by `quoted_string_equivalent`.
- qwen35_27b e153_string_regex_parsing_02 solve_self_check: gold `bcd`, extracted `'bcd'` -> correct by `quoted_string_equivalent`.
- qwen35_27b e153_unit_percentage_02 solve_neutral: gold `120`, extracted `120 meters` -> correct by `unit_suffix_equivalent`.
- qwen35_27b e153_unit_percentage_02 solve_terse: gold `120`, extracted `120 m` -> correct by `unit_suffix_equivalent`.
- qwen35_27b e153_unit_percentage_02 solve_self_check: gold `120`, extracted `120 meters` -> correct by `unit_suffix_equivalent`.
- gemma4_31b_it e153_string_regex_parsing_02 solve_neutral: gold `bcd`, extracted `'bcd'` -> correct by `quoted_string_equivalent`.
- gemma4_31b_it e153_string_regex_parsing_02 solve_terse: gold `bcd`, extracted `'bcd'` -> correct by `quoted_string_equivalent`.
- gemma4_31b_it e153_string_regex_parsing_02 solve_self_check: gold `bcd`, extracted `'bcd'` -> correct by `quoted_string_equivalent`.
- gemma4_31b_it e153_unit_percentage_02 solve_neutral: gold `120`, extracted `120m` -> correct by `unit_suffix_equivalent`.
- gemma4_31b_it e153_unit_percentage_02 solve_terse: gold `120`, extracted `120m` -> correct by `unit_suffix_equivalent`.

Next use / 后续使用：
- Main prefill/mutation seed pool: use `clean_valid_prefill_candidate=true` rows first.
- Language-behavior pool: use `language_trait_use=true`, especially Gemma multilingual misreads, Qwen rethinking/checking traces, and graph ambiguity rows.
- Do not pool MoE with dense in the same headline statistic; MoE should be audited separately because routing may add instability.

Artifacts / 产物：`data/processed/e153_dense_generation_audit_20260501.jsonl`, `results/E153_nonthinking_difficult_scenario_generation/e153_dense_generation_audit_summary_20260501.json`.
