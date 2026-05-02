# E170 Thinking-Only Stage Analysis / E170 thinking-only 阶段分析

Created / 创建时间：`2026-05-02T19:22:48`.

E170 gives only the original E164 hardened problem plus a generic thinking solve template. / E170 只给 E164 加难原题和通用 thinking 解题模板。

| model | n | correct | acc | completion tokens | mean tokens | hit-max | final marker | source |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| qwen35_27b | 21 | 21 | 1.000 | 86141 | 4101.952 | 0 | 21 | `results/E170_thinking_only_hardened_tasks/qwen35_27b_e170_thinking_only_max32768_20260502.json` |
| gemma4_31b_it | 21 | 21 | 1.000 | 54345 | 2587.857 | 0 | 21 | `results/E170_thinking_only_hardened_tasks/gemma4_31b_it_e170_thinking_only_max32768_20260502.json` |
| gemma4_26b_a4b_it | 9 | 6 | 0.667 | 148476 | 16497.333 | 4 | 5 | `logs/e170_thinking_only_gemma4_26b_a4b_it_checkpoint_20260502.jsonl` |
