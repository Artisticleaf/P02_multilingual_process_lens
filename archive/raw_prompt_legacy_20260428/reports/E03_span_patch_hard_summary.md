# E03 Span Patch Hard Summary

Clean means `valid->bad` increases the process-valid margin and `bad->valid` decreases it.

| model | best clean span/layer | v2b | b2v | strongest trace span | strongest support/error span | rows |
|---|---|---:|---:|---|---|---:|
| deepseek_r1_0528_qwen3_8b | verdict_pos L27 | 4.150 | -4.250 | trace_span L5 | support_error_span L9 | 150 |
| glm46v_flash | trace_span L10 | 0.225 | -0.138 | trace_span L10 | support_error_span L10 | 150 |
| ministral3_8b_reasoning | verdict_pos L33 | 1.625 | -0.750 | trace_span L7 | support_error_span L7 | 150 |
| phi4_mini_reasoning | verdict_pos L31 | 3.600 | -2.150 | trace_span L8 | support_error_span L8 | 125 |
| qwen35_9b | verdict_pos L31 | 3.250 | -2.775 | trace_span L3 | support_error_span L3 | 125 |
| qwen3_14b_base | verdict_pos L30 | 4.625 | -4.625 | trace_span L20 | support_error_span L14 | 150 |
| qwen3_8b_base | verdict_pos L27 | 2.400 | -2.700 | trace_span L9 | support_error_span L9 | 125 |

## Per-Model Top Effects

### deepseek_r1_0528_qwen3_8b

| span | layer | v2b | b2v | abs | clean |
|---|---:|---:|---:|---:|---|
| verdict_pos | 27 | 4.150 | -4.250 | 4.200 | True |
| verdict_pos | 35 | 0.900 | -5.850 | 3.375 | True |
| trace_span | 5 | 2.450 | -1.675 | 2.362 | True |
| trace_span | 9 | 1.300 | -2.700 | 2.050 | True |
| support_error_span | 9 | 0.750 | -3.150 | 2.050 | True |
| support_error_span | 5 | 0.550 | -3.350 | 2.050 | True |
| support_error_span | 12 | 0.650 | -3.200 | 2.075 | True |
| trace_span | 18 | 1.750 | -1.950 | 1.950 | True |
| trace_span | 12 | 0.900 | -2.700 | 1.800 | True |
| final_clause_span | 9 | 1.350 | -2.150 | 1.750 | True |
| final_clause_span | 5 | 1.800 | -1.225 | 1.662 | True |
| final_clause_span | 18 | 1.050 | -1.750 | 1.500 | True |

### glm46v_flash

| span | layer | v2b | b2v | abs | clean |
|---|---:|---:|---:|---:|---|
| trace_span | 10 | 0.225 | -0.138 | 0.319 | True |
| verdict_pos | 39 | 0.087 | -0.250 | 0.669 | True |
| verdict_pos | 30 | 0.113 | -0.150 | 0.631 | True |
| support_error_span | 10 | 0.212 | -0.037 | 0.162 | True |
| final_clause_span | 7 | 0.250 | 0.037 | 0.256 | False |
| trace_span | 7 | 0.188 | -0.025 | 0.381 | True |
| final_clause_span | 20 | 0.175 | 0.025 | 0.238 | False |
| final_clause_span | 19 | 0.212 | 0.075 | 0.206 | False |
| support_error_span | 7 | 0.163 | 0.037 | 0.250 | False |
| support_error_span | 20 | 0.025 | -0.100 | 0.087 | True |
| trace_span | 19 | 0.200 | 0.087 | 0.231 | False |
| support_error_span | 19 | 0.013 | -0.075 | 0.081 | True |

### ministral3_8b_reasoning

| span | layer | v2b | b2v | abs | clean |
|---|---:|---:|---:|---:|---|
| verdict_pos | 33 | 1.625 | -0.750 | 1.187 | True |
| verdict_pos | 25 | 0.975 | -1.050 | 1.013 | True |
| trace_span | 7 | 1.038 | -0.238 | 0.638 | True |
| trace_span | 8 | 0.975 | -0.263 | 0.619 | True |
| trace_span | 10 | 0.850 | -0.300 | 0.575 | True |
| support_error_span | 7 | 0.450 | -0.550 | 0.500 | True |
| support_error_span | 8 | 0.350 | -0.650 | 0.500 | True |
| final_clause_span | 10 | 0.600 | -0.287 | 0.444 | True |
| support_error_span | 10 | 0.450 | -0.400 | 0.425 | True |
| final_clause_span | 8 | 0.525 | -0.250 | 0.387 | True |
| trace_span | 17 | 0.225 | -0.475 | 0.400 | True |
| final_clause_span | 7 | 0.475 | -0.188 | 0.331 | True |

### phi4_mini_reasoning

| span | layer | v2b | b2v | abs | clean |
|---|---:|---:|---:|---:|---|
| verdict_pos | 31 | 3.600 | -2.150 | 3.538 | True |
| verdict_pos | 24 | 2.688 | -2.413 | 2.950 | True |
| verdict_pos | 16 | 2.400 | -1.900 | 2.175 | True |
| support_error_span | 8 | 2.163 | -0.575 | 1.794 | True |
| trace_span | 8 | 1.425 | -0.838 | 2.019 | True |
| final_clause_span | 8 | 0.950 | -0.487 | 2.006 | True |
| trace_span | 14 | -0.375 | -1.663 | 1.644 | False |
| problem_span | 16 | -0.000 | -0.863 | 0.831 | False |
| verdict_pos | 14 | 0.425 | -0.350 | 0.688 | True |
| trace_span | 16 | -0.275 | -1.038 | 1.081 | False |
| final_clause_span | 16 | 0.588 | -0.150 | 1.019 | True |
| support_error_span | 14 | -0.025 | -0.725 | 0.825 | False |

### qwen35_9b

| span | layer | v2b | b2v | abs | clean |
|---|---:|---:|---:|---:|---|
| verdict_pos | 31 | 3.250 | -2.775 | 3.013 | True |
| verdict_pos | 24 | 2.800 | -2.775 | 2.787 | True |
| trace_span | 3 | 0.350 | -3.025 | 1.762 | True |
| trace_span | 8 | 0.575 | -2.575 | 1.575 | True |
| support_error_span | 3 | 0.775 | -1.875 | 1.350 | True |
| support_error_span | 8 | 1.275 | -1.375 | 1.325 | True |
| final_clause_span | 3 | -0.050 | -2.300 | 1.175 | False |
| problem_span | 3 | 0.100 | -1.825 | 0.988 | True |
| final_clause_span | 8 | 0.025 | -1.525 | 0.850 | True |
| problem_span | 8 | 0.075 | -0.925 | 0.500 | True |
| trace_span | 16 | 0.350 | -0.625 | 0.488 | True |
| final_clause_span | 16 | 0.300 | -0.600 | 0.450 | True |

### qwen3_14b_base

| span | layer | v2b | b2v | abs | clean |
|---|---:|---:|---:|---:|---|
| verdict_pos | 30 | 4.625 | -4.625 | 4.625 | True |
| verdict_pos | 39 | 14.325 | 5.925 | 10.125 | False |
| trace_span | 20 | 3.900 | -1.375 | 2.638 | True |
| trace_span | 14 | 2.850 | -2.075 | 2.462 | True |
| trace_span | 9 | 2.375 | -2.425 | 2.400 | True |
| support_error_span | 14 | 2.750 | -2.000 | 2.375 | True |
| support_error_span | 9 | 2.200 | -2.525 | 2.363 | True |
| trace_span | 10 | 2.550 | -2.150 | 2.350 | True |
| support_error_span | 10 | 2.275 | -2.400 | 2.337 | True |
| final_clause_span | 20 | 2.200 | -1.000 | 1.600 | True |
| final_clause_span | 9 | 0.975 | -1.925 | 1.450 | True |
| final_clause_span | 14 | 1.275 | -1.350 | 1.312 | True |

### qwen3_8b_base

| span | layer | v2b | b2v | abs | clean |
|---|---:|---:|---:|---:|---|
| verdict_pos | 27 | 2.400 | -2.700 | 2.550 | True |
| verdict_pos | 35 | -0.400 | -4.500 | 2.600 | False |
| support_error_span | 9 | 0.700 | -2.650 | 1.775 | True |
| trace_span | 9 | 1.200 | -2.100 | 1.650 | True |
| support_error_span | 11 | 0.850 | -2.400 | 1.625 | True |
| trace_span | 11 | 1.350 | -1.800 | 1.575 | True |
| trace_span | 18 | 1.750 | -0.950 | 1.350 | True |
| final_clause_span | 11 | 0.700 | -1.350 | 1.075 | True |
| final_clause_span | 9 | 0.550 | -1.500 | 1.075 | True |
| final_clause_span | 18 | 1.000 | -0.650 | 0.825 | True |
| support_error_span | 18 | 0.900 | -0.500 | 0.700 | True |
| problem_span | 9 | -0.550 | -1.400 | 0.975 | False |

