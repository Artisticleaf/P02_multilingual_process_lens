# E51 Hard-Task Parser Split / 困难题解析器分流（2026-04-28）

## Plain-language conclusion / 说人话结论

- Strict `Final answer:` extraction remains the trace-selection format criterion. / strict `Final answer:` 仍是 trace-selection 格式标准。
- Boxed extraction tests whether a model solved the benchmark-style problem but ignored our final-line format. / boxed 抽取用于检查模型是否做出了 benchmark-style 答案但没按 final-line 输出。
- Loose tail-number matching is only a debugging diagnostic. / tail-number 只用于排错诊断。

## Overall / 总体

- Rows / 行数: 84
- Strict correct / strict 正确: 0
- Boxed correct / boxed 正确: 6
- Strict-or-boxed correct / strict 或 boxed 正确: 6
- Loose tail correct / tail 诊断正确: 7

## By model and gold-in-prompt / 按模型与是否含 gold 分组

| Model / 模型 | Gold in prompt / prompt 含 gold | n | Strict correct | Boxed correct | Strict or boxed | Loose tail correct |
|---|---:|---:|---:|---:|---:|---:|
| `gemma4_26b_a4b_it` | False | 18 | 0 | 0 | 0 | 1 |
| `gemma4_26b_a4b_it` | True | 6 | 0 | 0 | 0 | 0 |
| `qwen25_math_7b_instruct` | False | 36 | 0 | 6 | 6 | 6 |
| `qwen35_27b` | False | 18 | 0 | 0 | 0 | 0 |
| `qwen35_27b` | True | 6 | 0 | 0 | 0 | 0 |

## Interpretation / 解释

- If boxed correctness is high but strict correctness is low, the bottleneck is output formatting. / 如果 boxed 高但 strict 低，瓶颈是输出格式。
- If both are low, the bottleneck is final-correct trace acquisition. / 如果两者都低，瓶颈是先获得答案正确 trace。
- Current result should guide hard-task next steps: separate benchmark solving from trace-selection formatting. / 当前结果说明后续困难题必须把 benchmark 解题与 trace-selection 格式分开。

JSON result / JSON 结果: `results/E51_hard_task_parser_split/e51_hard_task_parser_split_20260428.json`
