# E171 Main-Claim Prompt Smoke / E171 主 claim prompt smoke

- task_id: `e171_aime25_base_divisor_p1`
- family: `aime25_mixed_hard`
- task_source: `configs/e26_aime_hard_tasks.yaml`
- prompt_variant: `baseline_nonthinking_original_problem`
- offline_non_problem_leakage_hits: `{}`
- gold_answer_string_occurs_in_problem_text: `False`

## Rendered Prompt / 渲染 prompt

```text
Solve the following problem carefully. Show the reasoning needed to justify the result. Do not give the final answer before the reasoning. End with exactly one line `Final answer: <answer>`.

Problem: Find the sum of all integer bases $b>9$ for which $17_{b}$ is a divisor of $97_{b}$.
```

## Boundary / 边界

- This prompt contains only a generic solve instruction and the original problem. / prompt 只含通用解题指令和原题。
- It contains no hidden score, no repair prefix, no localized span, no random span, no oracle hint, no trap note, and no gold answer field. / 不包含 hidden 分数、修复 prefix、localized span、random span、oracle hint、陷阱说明或答案字段。
- If the gold answer string appears in the problem as an ordinary number, it is recorded separately and not treated as leakage. / 如果答案字符串作为普通题干数字出现，单独记录，不算泄漏。
