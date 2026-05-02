# E159 Generation Process ACPI Audit / E159 生成过程 ACPI 审计

- Created at / 生成时间：`2026-05-01T12:31:17`.
- Scope / 范围：E159 三模型 non-thinking 生成，每条 completion 逐条打 process/ACPI 标签。
- Audit actor / 审计者：assistant single-pass process audit. This is useful now, but paper-grade reliability still needs independent human review. / 当前可用于推进实验，但论文级可靠性仍需独立人审复核。

## Main Counts / 主统计

- Rows / 总行数：360.
- Runner final-correct / 运行脚本原始 final-correct：340 (94.4%).
- Audited final-correct / 审计归一化后 final-correct：357 (99.2%).
- Runner false negatives from answer format / 因单位格式造成的自动假错：17.
- Strict process-valid / 严格过程有效：357 (99.2%).
- Strict ACPI / 答案正确但过程含错步：0.
- Unrepaired ACPI / 答案正确、错步未修复：0.
- Clean valid prefill candidates / 干净有效 prefill 种子：357.

## By Model / 按模型

- `gemma4_26b_a4b_it`: n=120, audited final-correct=120 (100.0%), process-valid=120, ACPI=0, format false-negative=6.
- `gemma4_31b_it`: n=120, audited final-correct=117 (97.5%), process-valid=117, ACPI=0, format false-negative=5.
- `qwen35_27b`: n=120, audited final-correct=120 (100.0%), process-valid=120, ACPI=0, format false-negative=6.

## Interpretation / 解释

- E159 generated traces did not naturally produce unrepaired ACPI. / E159 生成 trace 没有自然产出未修复 ACPI。
- The main correction to the runner metrics is answer-format normalization: `100 meters`, `100m`, `3 km`, and `3 kilometers` are semantically correct. / 对 runner 指标的主要修正是答案格式归一化。
- The only true generated reasoning failure after normalization is Gemma4-31B-it on `e159_multilingual_semantic_01`, where it reads `zhi duo wei 3` as divisibility by 3; those rows are wrong-answer traces, not ACPI. / 归一化后唯一真实生成失败是 Gemma dense 把 `zhi duo wei 3` 误读成 3 的倍数；这些是错答 trace，不是 ACPI。
- The answer-preserving task bank remains valuable because its invalid reference traces and future mutations can deliberately create controlled ACPI, and E161 can test whether models can detect/repair those traces. / 保答案任务库仍然重要，因为候选错误过程和后续篡改可以构造受控 ACPI，E161 可以测试模型能否发现和修复。

## Process-Invalid Final-Wrong Examples / 过程错且答案错样本

- `gemma4_31b_it` `solve_neutral` `e159_multilingual_semantic_01`: 多语言语义误读：`zhi duo wei 3` 在本题应为 `at most 3`，不是 3 的倍数。 Final answer is also wrong, so this is not ACPI.
- `gemma4_31b_it` `solve_terse` `e159_multilingual_semantic_01`: 多语言语义误读：`zhi duo wei 3` 在本题应为 `at most 3`，不是 3 的倍数。 Final answer is also wrong, so this is not ACPI.
- `gemma4_31b_it` `solve_self_check` `e159_multilingual_semantic_01`: 多语言语义误读：`zhi duo wei 3` 在本题应为 `at most 3`，不是 3 的倍数。 Final answer is also wrong, so this is not ACPI.

## Format False-Negative Examples / 格式假错示例

- `gemma4_26b_a4b_it` `solve_neutral` `e159_unit_roundtrip_01`: got `100 meters`, gold `100`.
- `gemma4_26b_a4b_it` `solve_terse` `e159_unit_roundtrip_01`: got `100 meters`, gold `100`.
- `gemma4_26b_a4b_it` `solve_self_check` `e159_unit_roundtrip_01`: got `100 meters`, gold `100`.
- `gemma4_26b_a4b_it` `solve_neutral` `e159_unit_roundtrip_03`: got `3 kilometers`, gold `3`.
- `gemma4_26b_a4b_it` `solve_terse` `e159_unit_roundtrip_03`: got `3 km`, gold `3`.
- `gemma4_26b_a4b_it` `solve_self_check` `e159_unit_roundtrip_03`: got `3 kilometers`, gold `3`.
- `gemma4_31b_it` `solve_neutral` `e159_unit_roundtrip_01`: got `100 meters`, gold `100`.
- `gemma4_31b_it` `solve_terse` `e159_unit_roundtrip_01`: got `100m`, gold `100`.
- `gemma4_31b_it` `solve_neutral` `e159_unit_roundtrip_03`: got `3 km`, gold `3`.
- `gemma4_31b_it` `solve_terse` `e159_unit_roundtrip_03`: got `3 km`, gold `3`.
