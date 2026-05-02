# E172 AIME2026 Prompt Smoke / E172 AIME2026 prompt smoke

- task_id: `e172_aime2026_p01`
- problem_idx: `1`
- dataset_repo: `MathArena/aime_2026`
- baseline_offline_field_hits: `{}`
- gate_offline_field_hits: `{}`
- gold_answer_string_occurs_in_problem_text: `False`

## Baseline Prompt / baseline prompt

```text
Solve the following AIME 2026 problem carefully in non-thinking mode. Show only the reasoning needed to justify the answer; do not give the final answer before the reasoning. End with exactly one line `Final answer: <integer>`.

Problem: Patrick started walking at a constant rate along a straight road from school to the park. One hour after Patrick left, Tanya started running along the same road from school to the park. One hour after Tanya left, Jose started bicycling along the same road from school to the park. Tanya ran at a constant rate of $2$ miles per hour faster than Patrick walked, Jose bicycled at a constant rate of $7$ miles per hour faster than Tanya ran, and all three arrived at the park at the same time. The distance from the school to the park is $\frac{m}{n}$ miles, where $m$ and $n$ are relatively prime positive integers. Find $m + n$.
```

## Hidden-Gate Prompt Shape / hidden-gate prompt 形状

```text
A hidden monitor flagged this visible span as potentially abnormal: `Tanya's speed is p+2`. The signal came from hidden/component state while running non-thinking generation, not from a gold answer. Stay in non-thinking mode, do a short controlled check of the flagged span against the problem, correct it if needed, and continue. End with exactly one line `Final answer: <integer>`.

Problem: Patrick started walking at a constant rate along a straight road from school to the park. One hour after Patrick left, Tanya started running along the same road from school to the park. One hour after Tanya left, Jose started bicycling along the same road from school to the park. Tanya ran at a constant rate of $2$ miles per hour faster than Patrick walked, Jose bicycled at a constant rate of $7$ miles per hour faster than Tanya ran, and all three arrived at the park at the same time. The distance from the school to the park is $\frac{m}{n}$ miles, where $m$ and $n$ are relatively prime positive integers. Find $m + n$.

Partial solution so far:
Let Patrick's walking speed be p miles per hour, so Tanya's speed is p+2.
```

## Boundary / 边界

- Baseline prompt uses only the problem. / baseline prompt 只使用题干。
- Hidden-gate prompt uses problem, model-generated prefix, and hidden-derived visible span. / hidden-gate prompt 使用题干、模型已生成 prefix、hidden 导出的可见 span。
- The gold answer and dataset revision are never rendered into runtime prompts. / 答案和数据集版本不进入运行时 prompt。
