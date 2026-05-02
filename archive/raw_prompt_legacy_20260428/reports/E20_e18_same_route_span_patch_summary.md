# E20 E18 Same-Route Qwen14 Span Patch Summary

Clean direction: `valid->bad` should increase Yes-vs-No process-valid margin on the bad trace; `bad->valid` should decrease it on the valid trace.

| model | pair | best clean/effect span | layer | v2b | b2v | abs |
|---|---|---|---:|---:|---:|---:|
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | problem_span* | 25 | 0.000 | -0.125 | 0.062 |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | final_answer_span | 14 | 0.125 | -0.250 | 0.188 |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | problem_span | 9 | 0.125 | -0.125 | 0.125 |

## Top Effects

| model | pair | span | layer | v2b | b2v | clean |
|---|---|---|---:|---:|---:|---|
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | problem_span | 25 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | problem_span | 30 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | final_answer_span | 9 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | final_answer_span | 25 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | trace_span | 30 | 0.000 | 0.000 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | support_error_span | 30 | 0.000 | 0.000 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | final_answer_span | 14 | -0.125 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | final_answer_span | 30 | 0.000 | 0.000 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | final_answer_span | 20 | 0.000 | 0.000 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | support_error_span | 25 | -0.125 | -0.000 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | trace_span | 25 | -0.250 | -0.000 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | problem_span | 20 | -0.625 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | final_answer_span | 14 | 0.125 | -0.250 | True |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | final_answer_span | 20 | 0.125 | -0.125 | True |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | problem_span | 30 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | trace_span | 30 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | final_answer_span | 9 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | final_answer_span | 25 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | final_answer_span | 30 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | support_error_span | 30 | 0.000 | -0.000 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | problem_span | 25 | 0.000 | 0.000 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | trace_span | 25 | -0.125 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | support_error_span | 25 | -0.125 | 0.000 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_91_valid | trace_span | 14 | -1.625 | -1.250 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | support_error_span | 9 | -1.250 | -1.875 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | problem_span | 9 | 0.125 | -0.125 | True |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | problem_span | 25 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | problem_span | 30 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | trace_span | 25 | -0.125 | -0.250 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | support_error_span | 30 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | final_answer_span | 25 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | trace_span | 30 | 0.000 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | support_error_span | 25 | -0.125 | -0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | final_answer_span | 9 | 0.000 | 0.000 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | final_answer_span | 14 | 0.125 | 0.125 | False |
| qwen3_14b_base | qwen14_e18_dabazhe_zh_en_92_bad_94_valid | final_answer_span | 20 | 0.125 | 0.125 | False |
