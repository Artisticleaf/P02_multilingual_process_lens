# E09 Real ACPI Span Patch Summary

Clean direction: `valid->bad` should increase Yes-vs-No process-valid margin on the bad trace; `bad->valid` should decrease it on the valid trace.

| model | pair | best clean/effect span | layer | v2b | b2v | abs |
|---|---|---|---:|---:|---:|---:|
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | verdict_pos | 31 | 4.125 | -2.562 | 3.344 |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | verdict_pos | 31 | 4.375 | -2.750 | 3.562 |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | verdict_pos | 30 | 0.750 | -0.750 | 0.750 |

## Top Effects

| model | pair | span | layer | v2b | b2v | clean |
|---|---|---|---:|---:|---:|---|
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | verdict_pos | 31 | 4.125 | -2.562 | True |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | support_error_span | 3 | 0.750 | -3.812 | True |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | trace_span | 3 | -1.375 | -4.437 | False |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | trace_span | 8 | -1.250 | -3.812 | False |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | support_error_span | 8 | 1.375 | -1.188 | True |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | problem_span | 3 | -0.250 | -0.625 | False |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | final_answer_span | 3 | -0.500 | -0.563 | False |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | problem_span | 31 | 0.000 | 0.000 | False |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | trace_span | 31 | 0.000 | 0.000 | False |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | support_error_span | 31 | 0.000 | 0.000 | False |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | final_answer_span | 31 | 0.000 | 0.000 | False |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | verdict_pos | 8 | 0.125 | 0.188 | False |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | verdict_pos | 31 | 4.375 | -2.750 | True |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | trace_span | 8 | -0.500 | -4.250 | False |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | trace_span | 3 | -0.875 | -4.500 | False |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | support_error_span | 3 | 1.000 | -1.562 | True |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | problem_span | 3 | 0.375 | -0.625 | True |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | support_error_span | 8 | 0.625 | -0.125 | True |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | verdict_pos | 8 | 0.125 | -0.562 | True |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | problem_span | 8 | 0.250 | -0.312 | True |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | final_answer_span | 3 | -0.250 | -0.562 | False |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | verdict_pos | 3 | 0.125 | -0.062 | True |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | final_answer_span | 8 | -0.125 | -0.188 | False |
| qwen35_9b | qwen35_ratio_zh_en_261_bad_260_valid | problem_span | 31 | 0.000 | 0.000 | False |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | verdict_pos | 30 | 0.750 | -0.750 | True |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | trace_span | 9 | -2.375 | -3.250 | False |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | trace_span | 14 | -2.250 | -3.125 | False |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | trace_span | 20 | 0.500 | -0.375 | True |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | support_error_span | 20 | 0.375 | -0.125 | True |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | problem_span | 14 | 0.000 | -0.375 | False |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | problem_span | 9 | 0.125 | -0.125 | True |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | support_error_span | 14 | 0.125 | -0.125 | True |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | verdict_pos | 14 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | problem_span | 20 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | trace_span | 30 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | verdict_pos | 9 | -0.125 | -0.125 | False |
