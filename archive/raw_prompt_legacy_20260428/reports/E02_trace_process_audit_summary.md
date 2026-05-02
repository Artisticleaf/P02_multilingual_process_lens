# E02 Trace Process Audit Summary

These are triage labels for manual audit, not ground-truth process labels.

| model | reason lang | n | final correct loose | green cues | red IFC cue | review final-correct | mixed lang |
|---|---|---:|---:|---:|---:|---:|---:|
| deepseek_r1_0528_qwen3_8b | en | 32 | 0.625 | 0.469 | 0.000 | 0.156 | 0.156 |
| deepseek_r1_0528_qwen3_8b | zh | 32 | 0.719 | 0.438 | 0.062 | 0.219 | 0.125 |
| phi4_mini_reasoning | en | 32 | 0.469 | 0.281 | 0.031 | 0.156 | 0.500 |
| phi4_mini_reasoning | zh | 32 | 0.562 | 0.281 | 0.031 | 0.250 | 0.094 |
| qwen35_9b | en | 16 | 0.625 | 0.250 | 0.000 | 0.375 | 0.000 |
| qwen35_9b | zh | 16 | 0.875 | 0.438 | 0.000 | 0.438 | 0.125 |
| qwen3_14b_base | en | 16 | 0.750 | 0.250 | 0.000 | 0.500 | 0.062 |
| qwen3_14b_base | zh | 16 | 0.938 | 0.250 | 0.062 | 0.625 | 0.375 |

## High-Priority Manual Reads

| model | task | in->reason | sample | triage | final | chars |
|---|---|---|---:|---|---|---:|
| deepseek_r1_0528_qwen3_8b | area_001 | en->en | 0 | review_final_correct_missing_cues | Step by | 538 |
| deepseek_r1_0528_qwen3_8b | area_001 | zh->zh | 0 | review_final_correct_missing_cues | 20平方单位 | 255 |
| deepseek_r1_0528_qwen3_8b | area_001 | zh->en | 0 | review_final_correct_missing_cues | So, the area should be 20. I | 457 |
| deepseek_r1_0528_qwen3_8b | area_001 | en->zh | 0 | review_final_correct_missing_cues | 平方单位，所以我会假设是平方单位 | 250 |
| deepseek_r1_0528_qwen3_8b | prob_001 | en->zh | 0 | review_final_correct_missing_cues | 3 / 5 | 262 |
| deepseek_r1_0528_qwen3_8b | avg_001 | zh->en | 0 | review_no_final_marker | 了消除分母，我可以将两边 | 241 |
| deepseek_r1_0528_qwen3_8b | percent_001 | zh->zh | 0 | review_final_correct_missing_cues | 60美元 | 250 |
| deepseek_r1_0528_qwen3_8b | percent_001 | en->zh | 0 | review_no_final_marker | 25% | 273 |
| deepseek_r1_0528_qwen3_8b | rem_001 | zh->zh | 0 | review_final_correct_missing_cues | 个数学问题，我可以直接计算 | 224 |
| deepseek_r1_0528_qwen3_8b | rem_001 | zh->en | 0 | review_no_final_marker | 137的倍数部分 | 233 |
| deepseek_r1_0528_qwen3_8b | deriv_001 | zh->en | 0 | review_no_final_marker | x^ | 275 |
| deepseek_r1_0528_qwen3_8b | deriv_001 | en->zh | 0 | review_no_final_marker | x^ | 280 |
| phi4_mini_reasoning | lin_001 | zh->en | 0 | review_no_final_marker | 首先，看看这个方程的结构。左边是2x加上3，右边是11。我的想法是先消去加上的3 | 205 |
| phi4_mini_reasoning | area_001 | zh->en | 0 | review_no_final_marker | 没错的 | 214 |
| phi4_mini_reasoning | area_001 | en->zh | 0 | review_final_correct_missing_cues | 太简单了？有没有可能哪里弄错了？

或者，我是不是应该再确认一下公式的正确性？比 | 230 |
| phi4_mini_reasoning | prob_001 | zh->en | 0 | review_no_final_marker | 红球的数量，而总事件数目就是所有球的数量之和 | 221 |
| phi4_mini_reasoning | prob_001 | en->zh | 0 | review_no_final_marker | So applying the basic probability formul | 713 |
| phi4_mini_reasoning | avg_001 | zh->en | 0 | review_no_final_marker | 9 | 226 |
| phi4_mini_reasoning | percent_001 | zh->en | 0 | review_no_final_marker | 80乘 | 230 |
| phi4_mini_reasoning | ratio_001 | zh->en | 0 | review_no_final_marker | 5×8= | 231 |
| phi4_mini_reasoning | rem_001 | zh->en | 0 | review_no_final_marker | 分。也就是说，对于被除数a，除数b，商q，余数r，它们之间满足关系式a = b  | 232 |
| phi4_mini_reasoning | rem_001 | en->zh | 0 | review_final_correct_missing_cues | Wait, another method I recall is adding  | 612 |
| phi4_mini_reasoning | deriv_001 | zh->en | 0 | review_no_final_marker | 对了，导数的幂法则应该是最开始想到的。就是说，像f(x) = x^n，那么它的导 | 215 |
| qwen35_9b | lin_001 | zh->zh | 0 | review_final_correct_missing_cues | 最后，我们可以验证一下：将 $x = 4$ 代入原方程，左边是 $2 \ | 249 |
| qwen35_9b | lin_001 | zh->en | 0 | review_final_correct_missing_cues | 4 | 355 |
| qwen35_9b | area_001 | zh->zh | 0 | review_final_correct_missing_cues | 20 | 162 |
| qwen35_9b | area_001 | en->zh | 0 | review_final_correct_missing_cues | 20 | 154 |
| qwen35_9b | avg_001 | en->zh | 0 | green_cues_final_correct | <think> | 148 |
| qwen35_9b | percent_001 | en->en | 0 | review_final_correct_missing_cues | <think> | 445 |
| qwen35_9b | percent_001 | zh->zh | 0 | review_final_correct_missing_cues | 60美元 | 105 |
| qwen35_9b | percent_001 | zh->en | 0 | review_final_correct_missing_cues | Calculation | 489 |
| qwen35_9b | ratio_001 | zh->zh | 0 | review_final_correct_missing_cues | 40 | 167 |
| qwen35_9b | ratio_001 | zh->en | 0 | review_final_correct_missing_cues | 40 | 347 |
| qwen35_9b | ratio_001 | en->zh | 0 | review_no_final_marker | 2.  **Solve the Problem | 537 |
| qwen35_9b | rem_001 | en->en | 0 | review_final_correct_missing_cues | 2 | 108 |
| qwen35_9b | rem_001 | zh->zh | 0 | review_final_correct_missing_cues | 2 | 187 |
| qwen35_9b | rem_001 | zh->en | 0 | review_final_correct_missing_cues | 2 | 96 |
| qwen35_9b | rem_001 | en->zh | 0 | review_final_correct_missing_cues | 了验证，我们直接进行除法运算：137 = 9 × 15 + 2 | 211 |
| qwen3_14b_base | lin_001 | en->zh | 0 | review_final_correct_missing_cues | 4 | 202 |
| qwen3_14b_base | area_001 | en->en | 0 | review_final_correct_missing_cues | 20. | 194 |
| qwen3_14b_base | area_001 | zh->zh | 0 | review_final_correct_missing_cues | 20 | 72 |
| qwen3_14b_base | area_001 | zh->en | 0 | review_final_correct_missing_cues | 20. | 275 |
| qwen3_14b_base | area_001 | en->zh | 0 | review_final_correct_missing_cues | 20 | 83 |
| qwen3_14b_base | prob_001 | zh->en | 0 | green_cues_final_correct | 3/5 | 62 |
| qwen3_14b_base | avg_001 | en->zh | 0 | review_final_correct_missing_cues | x = 1 | 225 |
| qwen3_14b_base | percent_001 | en->en | 0 | review_final_correct_missing_cues | $60 | 167 |
| qwen3_14b_base | percent_001 | zh->zh | 0 | review_final_correct_missing_cues | 60美元 | 101 |
| qwen3_14b_base | percent_001 | zh->en | 0 | review_final_correct_missing_cues | 60 | 192 |
| qwen3_14b_base | percent_001 | en->zh | 0 | review_final_correct_missing_cues | 60美元 | 194 |
| qwen3_14b_base | ratio_001 | zh->zh | 0 | review_final_correct_missing_cues | 40 | 133 |
| qwen3_14b_base | ratio_001 | zh->en | 0 | review_final_correct_missing_cues | 40 | 357 |
| qwen3_14b_base | ratio_001 | en->zh | 0 | review_final_correct_missing_cues | 40 | 208 |
| qwen3_14b_base | rem_001 | en->en | 0 | review_final_correct_missing_cues | This means that \(137 = 9 \times 15 + | 482 |
| qwen3_14b_base | rem_001 | zh->zh | 0 | review_final_correct_missing_cues | 2 | 33 |
| qwen3_14b_base | rem_001 | zh->en | 0 | review_final_correct_missing_cues | 2 | 243 |
| qwen3_14b_base | rem_001 | en->zh | 0 | review_final_correct_missing_cues | 2 | 38 |
| qwen3_14b_base | deriv_001 | en->en | 0 | review_final_correct_missing_cues | 2x + 3. | 365 |
| qwen3_14b_base | deriv_001 | zh->zh | 0 | review_no_final_marker | 将两部分相加 | 251 |
| qwen3_14b_base | deriv_001 | en->zh | 0 | red_invalid_cue_final_correct | 2x + 3 | 66 |
| deepseek_r1_0528_qwen3_8b | area_001 | en->en | 0 | review_final_correct_missing_cues | st | 1314 |
| deepseek_r1_0528_qwen3_8b | area_001 | zh->zh | 0 | review_final_correct_missing_cues | 20 | 446 |
| deepseek_r1_0528_qwen3_8b | area_001 | en->zh | 0 | review_final_correct_missing_cues | 20”。 | 428 |
| deepseek_r1_0528_qwen3_8b | avg_001 | zh->en | 0 | green_cues_final_correct | 数字 | 535 |
| deepseek_r1_0528_qwen3_8b | ratio_001 | en->en | 0 | review_final_correct_missing_cues | But in all cases, I get | 1504 |
| deepseek_r1_0528_qwen3_8b | ratio_001 | en->zh | 0 | green_cues_final_correct | Re-reading the system prompt: "请只用中文逐步推理 | 1510 |
| deepseek_r1_0528_qwen3_8b | rem_001 | zh->en | 0 | green_cues_final_correct | 2 | 695 |
| deepseek_r1_0528_qwen3_8b | rem_001 | en->zh | 0 | red_invalid_cue_final_correct | 2 | 724 |
| deepseek_r1_0528_qwen3_8b | deriv_001 | zh->zh | 0 | green_cues_final_correct |  | 835 |
| deepseek_r1_0528_qwen3_8b | deriv_001 | zh->en | 0 | review_final_correct_missing_cues | After reasoning, I end with one line: " | 1206 |
| deepseek_r1_0528_qwen3_8b | deriv_001 | en->zh | 0 | red_invalid_cue_final_correct | 3 * | 789 |
| phi4_mini_reasoning | lin_001 | zh->en | 0 | review_final_correct_missing_cues | 对的 | 708 |
| phi4_mini_reasoning | area_001 | zh->zh | 0 | review_final_correct_missing_cues | 20 | 522 |
| phi4_mini_reasoning | area_001 | zh->en | 0 | review_final_correct_missing_cues | 20 | 642 |
| phi4_mini_reasoning | area_001 | en->zh | 0 | review_final_correct_missing_cues | `20` | 455 |
| phi4_mini_reasoning | prob_001 | zh->en | 0 | green_cues_final_correct | 对的，红球3个，总 | 740 |
| phi4_mini_reasoning | prob_001 | en->zh | 0 | green_cues_final_correct | Alternatively, if I consider all possibl | 2168 |
| phi4_mini_reasoning | avg_001 | zh->zh | 0 | review_final_correct_missing_cues | 正确的 | 730 |
| phi4_mini_reasoning | avg_001 | zh->en | 0 | review_final_correct_missing_cues | 否 | 736 |
| phi4_mini_reasoning | avg_001 | en->zh | 0 | review_final_correct_missing_cues | 11 | 758 |
| phi4_mini_reasoning | percent_001 | zh->en | 0 | green_cues_final_correct | 原价的75% | 752 |
