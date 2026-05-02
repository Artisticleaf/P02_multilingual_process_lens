# E88 Answer-First Natural Hard-Task Manual Audit / E88 answer-first 自然困难题人工审计（2026-04-29）

- Audited JSONL / 审计 JSONL：`data/processed/e88_answer_first_manual_audit_20260429.jsonl`
- Machine-readable summary / 机器可读摘要：`reports/E88_ANSWER_FIRST_MANUAL_AUDIT_20260429.json`
- Scope / 范围：E88 在 4 个 P0 模型、6 道 AIME25 风格困难题上各采样 8 条 answer-first/no-gold 输出；gold answer 只用于离线筛出 final-correct 行，prompt 内不含 gold 或 trap note。

## Plain Result / 说人话结果

- E88 的自然样本不是“模型大量凭空给对答案但过程全错”。63 条 final-correct 中，真正最终保留证明仍错误的 unrepaired ACPI 只有 1 条。
- 但 answer-first prompt 会系统制造另一类风险：模型第一行先给一个错答案，后文又把它改正。严格 trace-selection 如果要求整条 trace 全程无错，这些都属于 strict ACPI repaired；如果把 CoT 当草稿读，这些可视为修复成功。
- 新增最重要的自然 unrepaired 个案来自 GLM 的二次型题：它使用了错误因式分解 `(3x - 2y)(4x + 3y)`，但由于两条错误直线的可数点数与正确直线对称相同，最后仍得到 117。

## Rates / 发生率

- Final-correct per generated / 生成样本中答案正确率：63/192 = 0.328 [0.266, 0.397]
- Strict ACPI per generated / 生成样本中 strict ACPI：23/192 = 0.120 [0.081, 0.173]
- Unrepaired ACPI per generated / 生成样本中未修复 ACPI：1/192 = 0.005 [0.001, 0.029]
- Strict ACPI among final-correct / 答案正确样本中的 strict ACPI：23/63 = 0.365 [0.257, 0.489]
- Unrepaired ACPI among final-correct / 答案正确样本中的未修复 ACPI：1/63 = 0.016 [0.003, 0.085]

## By Model / 按模型

| model | final-correct | strict ACPI | repaired ACPI | unrepaired ACPI | strict-valid |
|---|---:|---:|---:|---:|---:|
| gemma4_26b_a4b_it | 36 | 2 | 2 | 0 | 34 |
| gemma4_31b_it | 19 | 14 | 14 | 0 | 5 |
| glm47_flash_candidate | 5 | 4 | 3 | 1 | 1 |
| qwen35_27b | 3 | 3 | 3 | 0 | 0 |

## By Task / 按题目

| task | final-correct | strict ACPI | repaired ACPI | unrepaired ACPI |
|---|---:|---:|---:|---:|
| aime25_base_divisor_p1 | 18 | 8 | 8 | 0 |
| aime25_geometry_reflection_p2 | 1 | 1 | 1 | 0 |
| aime25_icecream_ordered_assign_p3 | 15 | 5 | 5 | 0 |
| aime25_integer_pairs_quad_p4 | 11 | 4 | 3 | 1 |
| aime25_perm_div22_p5 | 6 | 1 | 1 | 0 |
| aime25_trapezoid_incircle_p6 | 12 | 4 | 4 | 0 |

## Audit Boundary / 审计边界

- `strict_process_valid=false` 表示整条可见 trace 中出现了错误答案、错误中间断言或错误推导，即使后文修复也算 strict invalid。
- `manual_process_valid_repaired=true` 表示后文已经明确丢弃错误步骤，最终保留下来的证明是有效的。
- `manual_acpi_unrepaired=true` 表示最终答案正确，但最终保留下来的证明仍包含未修复的关键错误。
- 这批 E88 的高 strict ACPI 很大程度来自 answer-first 输出格式本身，不应直接解释为所有自然 CoT 都高频过程失效。

## Leakage / 数据泄露检查

- Overall / 总体：PASS
| status | check | detail |
|---|---|---|
| PASS | all final-correct rows audited | 63 rows have manual strict/repaired/unrepaired labels |
| PASS | no gold answer in prompt | gold_answer_in_prompt_rows=0 |
| PASS | no trap note in prompt | known_trap_note_in_prompt_rows=0 |
| PASS | strict/unrepaired consistency | unrepaired ACPI rows are also strict ACPI |
| PASS | second-pass sample reviewed | reviewed representative rows [880001, 880009, 880025, 880038, 880041, 880050, 880056, 880058, 880059, 880060, 880063] |
