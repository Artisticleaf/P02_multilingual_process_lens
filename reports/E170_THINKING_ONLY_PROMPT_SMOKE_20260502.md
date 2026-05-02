# E170 Thinking-Only Prompt Smoke / E170 thinking-only prompt smoke

- task_id: `e164_geo_01_multistep_sas_similarity`
- family: `geometry_constraints`
- prompt_variant: `thinking_only_template`
- leakage_hits_from_offline_non_problem_fields: `{}`
- gold_answer_string_occurs_in_problem_text: `True`

## Rendered Prompt / 渲染 prompt

```text
Solve the following problem carefully. Show the reasoning needed to justify the result. Do not give the final answer before the reasoning. End with exactly one line `Final answer: <answer>`.

Problem: Use exact arithmetic. In triangle ABC, AB=24, AC=32, and angle BAC equals angle EDF in triangle DEF. In triangle DEF, DE=9, DF=12, and EF=15. Point G lies on BC with BG:GC=2:3. What is GC? Report only the requested value.
```

## Boundary / 边界

- This prompt contains only the original problem and the generic solve template. / prompt 只包含原题和通用解题模板。
- It contains no repair prefix, no localized span, no random span, no oracle hint, and no candidate trace. / 不包含修复 prefix、localized span、random span、oracle hint 或候选过程。
- The gold answer string may appear as an ordinary number in the problem text; that is not counted as answer leakage for original-problem solving. / 答案字符串可能作为普通题干数字出现；原题解答中这不算答案泄漏。
