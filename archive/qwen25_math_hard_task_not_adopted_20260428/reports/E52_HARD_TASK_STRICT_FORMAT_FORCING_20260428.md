# E52 Hard-Task Strict-Format Forcing / 困难题严格格式强制（2026-04-28）

## Plain-language conclusion / 说人话结论

- Stronger instructions did **not** solve the hard-task trace-selection bottleneck: strict `Final answer:` correct remains 0/96. / 更强格式指令没有解决困难题 trace-selection 瓶颈：strict `Final answer:` 正确仍是 0/96。
- The same run produced 14/96 benchmark-style boxed-correct outputs, so some failures are not inability to solve the math problem; they are an objective/format mismatch. / 同一次运行有 14/96 个 benchmark-style boxed 正确输出，说明部分失败不是不会解题，而是目标/格式错配。
- Manual audit found 2 clear answer-correct/process-invalid boxed-only traces on the divisibility-by-22 task, but these are not official strict trace-selection positives because the final-line contract is missing. / 人工审计发现 2 个明确的 boxed-only 答案正确但过程无效样本，出现在 22 整除题；但它们缺少 final-line，因此不能算官方 strict trace-selection 阳性。
- Six trapezoid boxed-correct rows contain a radius/base-`r` notation collision; we mark them ambiguous rather than counting them as clear process-invalid evidence. / 6 个梯形 boxed-correct 行存在半径与底边 `r` 的符号混杂；保守记为 ambiguous，不纳入明确 process-invalid 计数。

## Counts / 数量

- Rows / 行数: 96
- Strict correct / strict 正确: 0
- Boxed correct diagnostic / boxed 诊断正确: 14
- Clear process-invalid among boxed-correct / boxed-correct 中明确过程无效: 2
- Ambiguous notation-collision boxed-correct / boxed-correct 中符号混杂 ambiguous: 6
- Valid boxed-only / 过程有效但格式不合格: 6
- Leak check / 泄漏检查: passed

## By prompt variant / 按 prompt 变体

| Variant / 变体 | n | Strict correct | Boxed correct | Clear invalid boxed | Ambiguous boxed | Valid boxed-only |
|---|---:|---:|---:|---:|---:|---:|
| `first_and_last` | 24 | 0 | 5 | 1 | 2 | 2 |
| `format_guard` | 24 | 0 | 1 | 0 | 0 | 1 |
| `short_solution` | 24 | 0 | 4 | 0 | 2 | 2 |
| `strict_contract` | 24 | 0 | 4 | 1 | 2 | 1 |

## By task / 按题目

| Task / 题目 | n | Strict correct | Boxed correct | Clear invalid boxed | Ambiguous boxed | Valid boxed-only |
|---|---:|---:|---:|---:|---:|---:|
| `aime25_base_divisor_p1` | 16 | 0 | 6 | 0 | 0 | 6 |
| `aime25_geometry_reflection_p2` | 16 | 0 | 0 | 0 | 0 | 0 |
| `aime25_icecream_ordered_assign_p3` | 16 | 0 | 0 | 0 | 0 | 0 |
| `aime25_integer_pairs_quad_p4` | 16 | 0 | 0 | 0 | 0 | 0 |
| `aime25_perm_div22_p5` | 16 | 0 | 2 | 2 | 0 | 0 |
| `aime25_trapezoid_incircle_p6` | 16 | 0 | 6 | 0 | 6 | 0 |

## Scientific interpretation / 科学解释

- For hard tasks, final-correct acquisition and final-line compliance are separate variables. / 对困难题，拿到正确答案与遵守 final-line 是两个变量。
- E52 strengthens the claim that verifier/selector objectives matter: a model can produce a correct answer under benchmark conventions while still being unusable for strict trace selection. / E52 强化了“verifier/selector objective 很关键”的说法：模型能按 benchmark 习惯给出正确答案，但仍不满足 strict trace selection。
- E52 does **not** prove hard-task natural ACPI under the official strict parser; it exposes where the bottleneck is. / E52 没有证明官方 strict parser 下的困难题自然 ACPI；它定位了瓶颈。
- The clear divisibility-by-22 rows are useful seed cases for the next causal experiment: build paired valid/invalid traces with the same final answer and patch residual/error spans. / 22 整除题的明确 invalid 行适合做下一步因果实验种子：构造同答案的 valid/invalid pair，再做 residual/error-span patch。

## Files / 文件

- Raw E52 result / 原始 E52 结果: `results/E52_hard_task_strict_format_forcing/qwen25_math_7b_instruct_e52_hard_task_strict_format_forcing.json`
- Manual audit JSON / 人工审计 JSON: `results/E52_hard_task_strict_format_forcing/e52_manual_audit_20260428.json`
