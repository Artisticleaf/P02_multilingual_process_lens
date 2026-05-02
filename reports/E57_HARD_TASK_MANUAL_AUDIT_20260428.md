# E57 Hard-Task Manual Audit / E57 困难题人工过程审计（2026-04-28）

- Input / 输入：`data/processed/e57_final_correct_rows_for_manual_audit_20260428.jsonl`
- Output / 输出：`data/processed/e57_final_correct_manual_audit_20260428.jsonl`
- Created / 创建时间：2026-04-28T21:25:02
- Scope / 范围：只审计 E57 中 strict final-correct 的 119 条 P0 hard-task trace；prompt 中没有 gold answer，也没有 trap note。
- Strict label / 严格标签：只要可见 trace 中出现错误数学结论、错误最终答案行或错误枚举结论，就记为 process-invalid。
- Repaired label / 修复后标签：如果 trace 明确发现并修正错误，且最终保留下来的推导正确，则记为 repaired-valid；这样可以区分“真的乱推碰巧对”和“先错后自我修复”。

## Overall / 总体

| n | strict valid | repaired valid | strict ACPI | unrepaired ACPI | repair-present |
|---:|---:|---:|---:|---:|---:|
| 119 | 108 (0.908) | 117 (0.983) | 11 (0.092) | 2 (0.017) | 9 (0.076) |

说人话：困难题里 final-correct trace 并不稀有，但绝大多数过程是有效的；严格口径下有一批“先写错后修复”的 trace。真正未修复、靠错误过程碰巧得到正确答案的 ACPI 目前只发现 2 条，均来自 Gemma4-26B-A4B 的整数对二次方程题。

## Error Types / 错误类型

| error type | count |
|---|---:|
| `none` | 108 |
| `repaired_enumeration_count_error` | 1 |
| `repaired_wrong_initial_answer` | 8 |
| `unrepaired_wrong_factorization` | 1 |
| `unrepaired_wrong_factorization_sign` | 1 |

### By Model / 按模型

| slice | n | strict valid | repaired valid | strict ACPI | unrepaired ACPI | repair-present |
|---|---:|---:|---:|---:|---:|---:|
| `gemma4_26b_a4b_it` | 52 | 50 (0.962) | 50 (0.962) | 2 (0.038) | 2 (0.038) | 0 (0.000) |
| `gemma4_31b_it` | 47 | 38 (0.809) | 47 (1.000) | 9 (0.191) | 0 (0.000) | 9 (0.191) |
| `qwen35_27b` | 20 | 20 (1.000) | 20 (1.000) | 0 (0.000) | 0 (0.000) | 0 (0.000) |

### By Task / 按题目

| slice | n | strict valid | repaired valid | strict ACPI | unrepaired ACPI | repair-present |
|---|---:|---:|---:|---:|---:|---:|
| `aime25_base_divisor_p1` | 31 | 28 (0.903) | 31 (1.000) | 3 (0.097) | 0 (0.000) | 3 (0.097) |
| `aime25_icecream_ordered_assign_p3` | 26 | 22 (0.846) | 26 (1.000) | 4 (0.154) | 0 (0.000) | 4 (0.154) |
| `aime25_integer_pairs_quad_p4` | 22 | 20 (0.909) | 20 (0.909) | 2 (0.091) | 2 (0.091) | 0 (0.000) |
| `aime25_perm_div22_p5` | 11 | 10 (0.909) | 11 (1.000) | 1 (0.091) | 0 (0.000) | 1 (0.091) |
| `aime25_trapezoid_incircle_p6` | 29 | 28 (0.966) | 29 (1.000) | 1 (0.034) | 0 (0.000) | 1 (0.034) |

### By Prompt Variant / 按 prompt 变体

| slice | n | strict valid | repaired valid | strict ACPI | unrepaired ACPI | repair-present |
|---|---:|---:|---:|---:|---:|---:|
| `answer_first_no_gold` | 29 | 18 (0.621) | 27 (0.931) | 11 (0.379) | 2 (0.069) | 9 (0.310) |
| `neutral` | 45 | 45 (1.000) | 45 (1.000) | 0 (0.000) | 0 (0.000) | 0 (0.000) |
| `self_check` | 45 | 45 (1.000) | 45 (1.000) | 0 (0.000) | 0 (0.000) | 0 (0.000) |

## Clear Unrepaired ACPI Rows / 明确未修复 ACPI 行

| audit idx | model | task | variant | error span | note |
|---:|---|---|---|---|---|
| 28 | `gemma4_26b_a4b_it` | `aime25_integer_pairs_quad_p4` | `answer_first_no_gold` | `(3x - 2y)(4x + 3y) = 0` | 把 12x^2-xy-6y^2 错因式分解成符号相反的两条直线；计数因对称性碰巧仍为 117，但推理过程没有修复。 |
| 29 | `gemma4_26b_a4b_it` | `aime25_integer_pairs_quad_p4` | `answer_first_no_gold` | `(4x + y)(3x - y) = 0` | 错误因式分解并得到错误直线 y=4x、y=3x；两个错误直线的边界计数碰巧给出 117，但推理过程无效且未修复。 |

## Boundary / 边界

- 这些 hard-task trace 是模型自然生成、无 gold prompt 的 final-correct 子集，不是受控构造；因此可以回答“困难题 final-correct 后是否会出现 ACPI”。
- 由于只审计 final-correct 行，不能从本文件估计整体解题准确率；整体 final-correct 率仍以 E57 原始结果 summary 为准。
- 严格 ACPI 与 unrepaired ACPI 必须分开报告：严格 ACPI 包含先错后修复的 visible trace；unrepaired ACPI 更接近“答案对但过程确实错且未改”。
