# E22 E18 Clean-Sibling Qwen3.5 Span Patch Summary

Clean direction: `valid->bad` should increase Yes-vs-No process-valid margin on the bad trace; `bad->valid` should decrease it on the valid trace.

| model | pair | best clean/effect span | layer | v2b | b2v | abs |
|---|---|---|---:|---:|---:|---:|
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | support_error_span | 3 | 0.250 | -2.438 | 1.344 |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | trace_span | 16 | 0.500 | -0.562 | 0.531 |

## Top Effects

| model | pair | span | layer | v2b | b2v | clean |
|---|---|---|---:|---:|---:|---|
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | trace_span | 3 | -1.500 | -4.438 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | support_error_span | 1 | -0.375 | -3.187 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | trace_span | 1 | -1.625 | -4.437 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | support_error_span | 3 | 0.250 | -2.438 | True |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | trace_span | 8 | -1.375 | -3.937 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | support_error_span | 8 | 1.250 | -1.250 | True |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | trace_span | 16 | 0.500 | -0.500 | True |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | final_answer_span | 3 | -0.500 | -1.125 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | problem_span | 1 | -0.375 | -0.812 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | final_answer_span | 16 | 0.125 | -0.188 | True |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | problem_span | 3 | -0.125 | -0.438 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181000_valid | final_answer_span | 1 | -0.500 | -0.750 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | trace_span | 3 | -1.500 | -5.187 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | trace_span | 1 | -1.625 | -5.063 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | trace_span | 8 | -1.250 | -4.688 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | support_error_span | 1 | -0.250 | -1.625 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | support_error_span | 3 | -0.250 | -1.562 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | support_error_span | 8 | 1.125 | 0.000 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | trace_span | 16 | 0.500 | -0.562 | True |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | final_answer_span | 3 | -0.500 | -1.188 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | problem_span | 1 | -0.375 | -0.688 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | final_answer_span | 16 | 0.125 | -0.188 | True |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | problem_span | 3 | -0.250 | -0.438 | False |
| qwen35_9b | qwen35_e18_discount_234_bad_181001_valid | final_answer_span | 24 | 0.125 | -0.062 | True |
