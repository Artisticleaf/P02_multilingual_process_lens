# E02 Trace Process Audit Summary

These are triage labels for manual audit, not ground-truth process labels.

| model | reason lang | n | final correct loose | green cues | red IFC cue | review final-correct | mixed lang |
|---|---|---:|---:|---:|---:|---:|---:|
| deepseek_r1_0528_qwen3_8b | en | 36 | 0.917 | 0.278 | 0.528 | 0.111 | 0.250 |
| deepseek_r1_0528_qwen3_8b | zh | 36 | 1.000 | 0.250 | 0.611 | 0.139 | 0.083 |
| phi4_mini_reasoning | en | 36 | 1.000 | 0.222 | 0.750 | 0.028 | 0.500 |
| phi4_mini_reasoning | zh | 36 | 0.944 | 0.167 | 0.750 | 0.028 | 0.000 |
| qwen35_9b | en | 72 | 0.958 | 0.500 | 0.167 | 0.292 | 0.111 |
| qwen35_9b | zh | 36 | 1.000 | 0.556 | 0.361 | 0.083 | 0.139 |
| qwen3_14b_base | en | 36 | 0.972 | 0.333 | 0.222 | 0.417 | 0.167 |
| qwen3_14b_base | zh | 72 | 0.986 | 0.319 | 0.375 | 0.292 | 0.333 |

## High-Priority Manual Reads

| model | task | in->reason | sample | triage | final | chars |
|---|---|---|---:|---|---|---:|
| deepseek_r1_0528_qwen3_8b | disc_en_25_off | zh->zh | 0 | red_invalid_cue_final_correct | 优惠后价格是60美元。 | 569 |
| deepseek_r1_0528_qwen3_8b | disc_en_25_off | zh->zh | 1 | red_invalid_cue_final_correct | 60 | 655 |
| deepseek_r1_0528_qwen3_8b | disc_en_25_off | zh->zh | 2 | red_invalid_cue_final_correct | 60美元 | 607 |
| deepseek_r1_0528_qwen3_8b | disc_en_25_off | zh->en | 0 | red_invalid_cue_final_correct | 60美元 | 494 |
| deepseek_r1_0528_qwen3_8b | disc_en_25_off | zh->en | 1 | red_invalid_cue_final_correct | Also, ensure that I end with " | 1278 |
| deepseek_r1_0528_qwen3_8b | disc_en_25_off | zh->en | 2 | red_invalid_cue_final_correct | 60美元 | 1232 |
| deepseek_r1_0528_qwen3_8b | disc_en_25_off | en->en | 1 | red_invalid_cue_final_correct | $60" | 2254 |
| deepseek_r1_0528_qwen3_8b | disc_en_25_off | en->en | 2 | red_invalid_cue_final_correct | So, I need to reason step by step in Eng | 1144 |
| deepseek_r1_0528_qwen3_8b | disc_en_25_off | en->zh | 0 | red_invalid_cue_final_correct | 60美元，所以应该写成“60美元” | 633 |
| deepseek_r1_0528_qwen3_8b | disc_en_25_off | en->zh | 1 | red_invalid_cue_final_correct | ：只用中文逐步 | 675 |
| deepseek_r1_0528_qwen3_8b | disc_en_25_off | en->zh | 2 | red_invalid_cue_final_correct | 0.25 | 707 |
| deepseek_r1_0528_qwen3_8b | disc_zh_75_price | zh->zh | 0 | red_invalid_cue_final_correct | 60”。 | 647 |
| deepseek_r1_0528_qwen3_8b | disc_zh_75_price | zh->en | 1 | red_invalid_cue_final_correct | The format is: " | 1311 |
| deepseek_r1_0528_qwen3_8b | disc_zh_75_price | zh->en | 2 | review_no_final_marker | 20美元 | 1293 |
| deepseek_r1_0528_qwen3_8b | disc_zh_75_price | en->zh | 1 | red_invalid_cue_final_correct | 60 | 815 |
| deepseek_r1_0528_qwen3_8b | disc_en_75_off | zh->zh | 0 | review_final_correct_missing_cues | 20美元 | 809 |
| deepseek_r1_0528_qwen3_8b | disc_en_75_off | zh->zh | 1 | review_final_correct_missing_cues | 20美元”。 | 455 |
| deepseek_r1_0528_qwen3_8b | disc_en_75_off | zh->zh | 2 | review_final_correct_missing_cues | 20 | 566 |
| deepseek_r1_0528_qwen3_8b | disc_en_75_off | zh->en | 0 | review_final_correct_missing_cues | 0.25 | 519 |
| deepseek_r1_0528_qwen3_8b | disc_en_75_off | zh->en | 1 | red_invalid_cue_final_correct | Finally, end with " | 1416 |
| deepseek_r1_0528_qwen3_8b | disc_en_75_off | zh->en | 2 | review_final_correct_missing_cues | ：“请用英语逐步 | 1075 |
| deepseek_r1_0528_qwen3_8b | disc_en_75_off | en->en | 0 | review_final_correct_missing_cues | 20 | 1019 |
| deepseek_r1_0528_qwen3_8b | disc_en_75_off | en->en | 1 | red_invalid_cue_final_correct | cou | 1036 |
| deepseek_r1_0528_qwen3_8b | disc_en_75_off | en->en | 2 | red_invalid_cue_final_correct | Now, end with " | 1049 |
| deepseek_r1_0528_qwen3_8b | disc_en_75_off | en->zh | 0 | red_invalid_cue_final_correct | 20”。 | 353 |
| deepseek_r1_0528_qwen3_8b | disc_en_75_off | en->zh | 1 | review_final_correct_missing_cues | 20美元 | 479 |
| deepseek_r1_0528_qwen3_8b | disc_en_75_off | en->zh | 2 | review_final_correct_missing_cues | 80美元，折扣75%，所以支付原价的25% | 469 |
| deepseek_r1_0528_qwen3_8b | ratio_boys_total | zh->zh | 0 | red_invalid_cue_final_correct | 3:5，所以女生是男生的5/3倍 | 1116 |
| deepseek_r1_0528_qwen3_8b | ratio_boys_total | zh->zh | 1 | red_invalid_cue_final_correct | 男生人数乘以（5/3），但需要用中文表达 | 1015 |
| deepseek_r1_0528_qwen3_8b | ratio_boys_total | zh->zh | 2 | red_invalid_cue_final_correct | 要求只用中文逐步 | 504 |
| deepseek_r1_0528_qwen3_8b | ratio_boys_total | zh->en | 0 | red_invalid_cue_final_correct | co | 1949 |
| deepseek_r1_0528_qwen3_8b | ratio_boys_total | zh->en | 1 | red_invalid_cue_final_correct | The instruction is to end with one line  | 1963 |
| deepseek_r1_0528_qwen3_8b | ratio_boys_total | en->en | 0 | red_invalid_cue_final_correct | 40.
</thi | 2078 |
| deepseek_r1_0528_qwen3_8b | ratio_boys_total | en->en | 1 | review_final_correct_missing_cues | 40.

But let me make su | 1570 |
| deepseek_r1_0528_qwen3_8b | ratio_boys_total | en->zh | 0 | red_invalid_cue_final_correct | 40 | 892 |
| deepseek_r1_0528_qwen3_8b | ratio_boys_total | en->zh | 1 | red_invalid_cue_final_correct | Then girls = total - | 2100 |
| deepseek_r1_0528_qwen3_8b | ratio_boys_total | en->zh | 2 | red_invalid_cue_final_correct | Now, is there any trick here? The class  | 2354 |
| deepseek_r1_0528_qwen3_8b | deriv_sum | zh->zh | 1 | red_invalid_cue_final_correct | 直接 | 784 |
| deepseek_r1_0528_qwen3_8b | deriv_sum | zh->en | 0 | green_cues_final_correct |  | 978 |
| deepseek_r1_0528_qwen3_8b | deriv_sum | zh->en | 1 | green_cues_final_correct | 2x + 3 | 1139 |
| deepseek_r1_0528_qwen3_8b | deriv_sum | zh->en | 2 | green_cues_final_correct | 2x + 3 | 897 |
| deepseek_r1_0528_qwen3_8b | deriv_sum | en->en | 1 | red_invalid_cue_final_correct | the derivative of \( x^2 \) is \( 2x \), | 1567 |
| deepseek_r1_0528_qwen3_8b | percent_then_discount | zh->zh | 0 | red_invalid_cue_final_correct | 80美元 | 793 |
| deepseek_r1_0528_qwen3_8b | percent_then_discount | zh->zh | 1 | red_invalid_cue_final_correct | 80美元” | 1013 |
| deepseek_r1_0528_qwen3_8b | percent_then_discount | zh->zh | 2 | red_invalid_cue_final_correct | 80 | 1086 |
| deepseek_r1_0528_qwen3_8b | percent_then_discount | zh->en | 0 | red_invalid_cue_final_correct | 80美元 | 1186 |
| deepseek_r1_0528_qwen3_8b | percent_then_discount | zh->en | 1 | red_invalid_cue_final_correct | Perhaps the problem is that the increase | 2281 |
| deepseek_r1_0528_qwen3_8b | percent_then_discount | zh->en | 2 | red_invalid_cue_final_correct | But in this case, it's a discount after  | 2059 |
| deepseek_r1_0528_qwen3_8b | percent_then_discount | en->en | 0 | red_invalid_cue_final_correct | a | 2021 |
| deepseek_r1_0528_qwen3_8b | percent_then_discount | en->en | 1 | red_invalid_cue_final_correct | Discount by 20% is multiply by 0.80 | 2313 |
| deepseek_r1_0528_qwen3_8b | percent_then_discount | en->en | 2 | red_invalid_cue_final_correct | Reading the problem: "A price is increas | 2395 |
| deepseek_r1_0528_qwen3_8b | percent_then_discount | en->zh | 0 | red_invalid_cue_final_correct | 80美元 | 696 |
| deepseek_r1_0528_qwen3_8b | percent_then_discount | en->zh | 1 | red_invalid_cue_final_correct | 的，确认无误 | 775 |
| deepseek_r1_0528_qwen3_8b | percent_then_discount | en->zh | 2 | red_invalid_cue_final_correct | 80美元 | 1086 |
| phi4_mini_reasoning | disc_en_25_off | zh->zh | 0 | red_invalid_cue_final_correct | 正确的 | 1167 |
| phi4_mini_reasoning | disc_en_25_off | zh->zh | 1 | red_invalid_cue_final_correct | seco | 1158 |
| phi4_mini_reasoning | disc_en_25_off | zh->zh | 2 | red_invalid_cue_final_correct | \boxed{60} | 1130 |
| phi4_mini_reasoning | disc_en_25_off | zh->en | 0 | red_invalid_cue_final_correct | \boxed{60} | 1043 |
| phi4_mini_reasoning | disc_en_25_off | zh->en | 1 | red_invalid_cue_final_correct | \boxed{60} | 1049 |
| phi4_mini_reasoning | disc_en_25_off | zh->en | 2 | red_invalid_cue_final_correct | ** \boxed{60} | 1178 |
| phi4_mini_reasoning | disc_en_25_off | en->en | 0 | red_invalid_cue_final_correct | $\boxed{60}$ | 2453 |
| phi4_mini_reasoning | disc_en_25_off | en->en | 1 | red_invalid_cue_final_correct | $\boxed{60}$ | 2324 |
| phi4_mini_reasoning | disc_en_25_off | en->en | 2 | red_invalid_cue_final_correct | $\boxed{60}$ | 2660 |
| phi4_mini_reasoning | disc_en_25_off | en->zh | 0 | red_invalid_cue_final_correct | \boxed{60} | 1077 |
| phi4_mini_reasoning | disc_en_25_off | en->zh | 1 | red_invalid_cue_final_correct | 60 | 1099 |
| phi4_mini_reasoning | disc_zh_75_price | zh->zh | 1 | red_invalid_cue_final_correct | ：  
Fi | 880 |
| phi4_mini_reasoning | disc_zh_75_price | zh->zh | 2 | red_invalid_cue_final_correct | 60美元 | 1152 |
| phi4_mini_reasoning | disc_zh_75_price | zh->en | 0 | green_cues_final_correct | ** \boxed{60} | 802 |
| phi4_mini_reasoning | disc_zh_75_price | zh->en | 1 | red_invalid_cue_final_correct | 60 | 1236 |
| phi4_mini_reasoning | disc_zh_75_price | zh->en | 2 | red_invalid_cue_final_correct | \boxed{60} | 1140 |
| phi4_mini_reasoning | disc_zh_75_price | en->en | 0 | red_invalid_cue_final_correct | \boxed{60} | 2045 |
| phi4_mini_reasoning | disc_zh_75_price | en->en | 2 | red_invalid_cue_final_correct | \boxed{60} | 1906 |
| phi4_mini_reasoning | disc_zh_75_price | en->zh | 0 | red_invalid_cue_final_correct | 正确的，两 | 1152 |
| phi4_mini_reasoning | disc_zh_75_price | en->zh | 1 | red_invalid_cue_final_correct | 60美元 | 1315 |
| phi4_mini_reasoning | disc_zh_75_price | en->zh | 2 | red_invalid_cue_final_correct | 60美元 | 1268 |
| phi4_mini_reasoning | disc_en_75_off | zh->zh | 0 | red_invalid_cue_final_correct | 正确 | 1181 |
| phi4_mini_reasoning | disc_en_75_off | zh->zh | 1 | red_invalid_cue_final_correct | Final answer: \boxed{20} | 811 |
| phi4_mini_reasoning | disc_en_75_off | zh->zh | 2 | red_invalid_cue_final_correct | 20美元，也就是 | 1164 |
| phi4_mini_reasoning | disc_en_75_off | zh->en | 0 | red_invalid_cue_final_correct | 20美元 | 1197 |
| phi4_mini_reasoning | disc_en_75_off | zh->en | 1 | red_invalid_cue_final_correct | ** \boxed{20} | 1322 |
