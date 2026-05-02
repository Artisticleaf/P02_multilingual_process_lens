# E19 Real ACPI Module Patch Summary

Goal: decompose robust residual-span effects into attention-output vs MLP-output replacement on the same verifier prompt. This remains a smoke test: module output replacement is not a full circuit proof.

| model | pair | best module | span | layer | v2b effect | b2v effect | clean direction |
|---|---|---|---|---:|---:|---:|---:|
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | mlp | trace_span | 1 | 1.250 | -0.062 | 3/24 |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | mlp | trace_span | 1 | 0.312 | -0.188 | 5/24 |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | mlp | trace_span | 9 | 0.375 | -0.250 | 4/30 |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | mlp | support_error_span | 14 | 1.750 | -0.375 | 6/30 |

## Interpretation Guardrails

- A clean direction means valid-to-bad increases the bad trace's Yes-No margin and bad-to-valid decreases the valid trace's margin.
- If attention and MLP both move the margin, the result localizes below residual stream but not to a single head/neuron.
- Strong effects on `problem_span` indicate surface semantics can be encoded before the reasoning trace is read; they need same-problem and paraphrase controls before mechanistic overclaiming.
