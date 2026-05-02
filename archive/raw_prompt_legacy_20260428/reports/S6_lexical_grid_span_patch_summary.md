# E09 Real ACPI Span Patch Summary

Clean direction: `valid->bad` should increase Yes-vs-No process-valid margin on the bad trace; `bad->valid` should decrease it on the valid trace.

| model | pair | best clean/effect span | layer | v2b | b2v | abs |
|---|---|---|---:|---:|---:|---:|
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | support_error_span | 14 | 0.125 | -0.125 | 0.125 |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | support_error_span | 8 | 0.250 | -0.125 | 0.188 |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | support_error_span | 14 | 2.750 | -1.000 | 1.875 |

## Top Effects

| model | pair | span | layer | v2b | b2v | clean |
|---|---|---|---:|---:|---:|---|
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | trace_span | 8 | -5.000 | -6.250 | False |
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | support_error_span | 8 | -0.125 | -0.500 | False |
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | trace_span | 14 | -2.875 | -3.250 | False |
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | trace_span | 20 | -0.875 | -1.250 | False |
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | support_error_span | 14 | 0.125 | -0.125 | True |
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | support_error_span | 20 | 0.125 | 0.000 | False |
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | final_answer_span | 14 | -1.000 | -1.125 | False |
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | final_answer_span | 20 | -0.500 | -0.625 | False |
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | support_error_span | 28 | 0.000 | 0.000 | False |
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | support_error_span | 36 | 0.000 | 0.000 | False |
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | trace_span | 28 | 0.000 | 0.000 | False |
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | trace_span | 36 | 0.000 | 0.000 | False |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | support_error_span | 8 | 0.250 | -0.125 | True |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | support_error_span | 28 | 0.000 | 0.000 | False |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | support_error_span | 36 | 0.000 | 0.000 | False |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | trace_span | 28 | 0.000 | 0.000 | False |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | trace_span | 36 | 0.000 | 0.000 | False |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | final_answer_span | 28 | 0.000 | 0.000 | False |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | final_answer_span | 36 | 0.000 | 0.000 | False |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | support_error_span | 14 | 0.000 | 0.125 | False |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | trace_span | 20 | -0.500 | -0.375 | False |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | final_answer_span | 8 | -0.125 | 0.000 | False |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | final_answer_span | 14 | -0.875 | -0.375 | False |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | final_answer_span | 20 | -0.375 | 0.125 | False |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | support_error_span | 14 | 2.750 | -1.000 | True |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | support_error_span | 9 | 2.000 | -1.250 | True |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | trace_span | 14 | -0.625 | -3.250 | False |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | trace_span | 20 | 1.750 | -0.500 | True |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | trace_span | 9 | -1.250 | -3.000 | False |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | support_error_span | 20 | 0.875 | -0.375 | True |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | trace_span | 25 | 0.125 | -0.375 | True |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | final_answer_span | 25 | 0.125 | -0.250 | True |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | final_answer_span | 30 | 0.125 | -0.250 | True |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | support_error_span | 25 | 0.000 | -0.125 | True |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | support_error_span | 30 | 0.125 | 0.000 | False |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | final_answer_span | 9 | 0.000 | -0.125 | True |
