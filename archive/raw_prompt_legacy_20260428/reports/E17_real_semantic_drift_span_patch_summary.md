# E17 Real Semantic-Drift / Same-Route Span Patch Summary

Clean direction: `valid->bad` should increase Yes-vs-No process-valid margin on the bad trace; `bad->valid` should decrease it on the valid trace.

| model | pair | best clean/effect span | layer | v2b | b2v | abs |
|---|---|---|---:|---:|---:|---:|
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | support_error_span | 3 | 0.750 | -3.812 | 2.281 |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | support_error_span* | 3 | -0.375 | -3.750 | 2.062 |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | trace_span | 20 | 0.500 | -0.375 | 0.438 |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | problem_span | 14 | 2.250 | -1.000 | 1.625 |

## Top Effects

| model | pair | span | layer | v2b | b2v | clean |
|---|---|---|---:|---:|---:|---|
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | support_error_span | 3 | 0.750 | -3.812 | True |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | support_error_span | 1 | -0.250 | -3.812 | False |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | trace_span | 1 | -1.500 | -4.562 | False |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | trace_span | 3 | -1.375 | -4.437 | False |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | trace_span | 8 | -1.250 | -3.812 | False |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | support_error_span | 8 | 1.375 | -1.188 | True |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | problem_span | 1 | -0.375 | -2.312 | False |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | trace_span | 16 | 0.625 | -0.812 | True |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | final_answer_span | 16 | 0.250 | -0.250 | True |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | problem_span | 3 | -0.250 | -0.625 | False |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | support_error_span | 24 | 0.125 | 0.000 | False |
| qwen35_9b | qwen35_discount_zh_234_bad_235_valid | final_answer_span | 3 | -0.500 | -0.563 | False |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | support_error_span | 3 | -0.375 | -3.750 | False |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | support_error_span | 1 | -0.812 | -3.625 | False |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | problem_span | 1 | -0.312 | -2.500 | False |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | support_error_span | 8 | -0.312 | -2.250 | False |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | trace_span | 8 | -3.375 | -5.000 | False |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | problem_span | 8 | -0.063 | -1.000 | False |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | trace_span | 3 | -3.625 | -4.500 | False |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | problem_span | 3 | -0.312 | -1.062 | False |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | trace_span | 1 | -4.000 | -4.625 | False |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | final_answer_span | 1 | -0.375 | -0.938 | False |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | final_answer_span | 8 | -0.312 | -0.563 | False |
| qwen35_9b | qwen35_qiwuzhe_zh_en_229_bad_225_valid | trace_span | 16 | -0.250 | -0.500 | False |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | trace_span | 9 | -2.375 | -3.250 | False |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | trace_span | 14 | -2.250 | -3.125 | False |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | trace_span | 20 | 0.500 | -0.375 | True |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | support_error_span | 20 | 0.375 | -0.125 | True |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | problem_span | 14 | 0.000 | -0.375 | False |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | problem_span | 9 | 0.125 | -0.125 | True |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | support_error_span | 14 | 0.125 | -0.125 | True |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | problem_span | 20 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | trace_span | 30 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | trace_span | 25 | -0.125 | -0.125 | False |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | support_error_span | 25 | 0.000 | 0.000 | False |
| qwen3_14b_base | qwen14_deriv_sum_zh_402_bad_403_valid | support_error_span | 30 | 0.000 | 0.000 | False |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | problem_span | 14 | 2.250 | -1.000 | True |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | trace_span | 9 | -0.500 | -3.500 | False |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | problem_span | 9 | 2.125 | -0.875 | True |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | support_error_span | 14 | -0.375 | -3.250 | False |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | trace_span | 14 | -0.875 | -3.625 | False |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | support_error_span | 9 | 0.500 | -2.250 | True |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | trace_span | 20 | 1.625 | -1.000 | True |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | support_error_span | 20 | 0.750 | -0.625 | True |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | problem_span | 20 | 0.250 | -0.500 | True |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | support_error_span | 25 | 0.125 | -0.125 | True |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | support_error_span | 30 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_disc75_en_zh_358_bad_359_valid | final_answer_span | 20 | 0.125 | 0.000 | False |
