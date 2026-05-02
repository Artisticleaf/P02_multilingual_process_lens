# E08 Trap Representation Bridge Summary

Layerwise contextual target-span cosine probe for discount and derivative semantic traps. Positive margin means the query term is closer to intended/equivalent concepts than to trap concepts.

## Overall Best Layers

| model | best layer | mean margin | min margin |
|---|---:|---:|---:|
| deepseek_r1_0528_qwen3_8b | 20 | -0.001 | -0.067 |
| phi4_mini_reasoning | 16 | -0.003 | -0.057 |
| qwen35_9b | 1 | -0.002 | -0.009 |
| qwen3_14b_base | 25 | 0.014 | -0.072 |

## Best By Contrast

| model | contrast | best layer | mean margin | hard margin | pos cos | neg cos |
|---|---|---:|---:|---:|---:|---:|
| deepseek_r1_0528_qwen3_8b | qiwuzhe_pay75_vs_75off | 1 | -0.005 | -0.005 | 0.604 | 0.609 |
| deepseek_r1_0528_qwen3_8b | youhui25_pay75_vs_75off | 35 | -0.050 | -0.091 | 0.886 | 0.935 |
| deepseek_r1_0528_qwen3_8b | dabazhe_pay80_vs_80discount | 15 | -0.006 | 0.023 | 0.499 | 0.505 |
| deepseek_r1_0528_qwen3_8b | deriv_3x_valid_vs_constant_error | 0 | 0.233 | 0.217 | 0.856 | 0.623 |
| phi4_mini_reasoning | qiwuzhe_pay75_vs_75off | 1 | 0.001 | -0.001 | 0.752 | 0.751 |
| phi4_mini_reasoning | youhui25_pay75_vs_75off | 13 | -0.054 | -0.076 | 0.874 | 0.928 |
| phi4_mini_reasoning | dabazhe_pay80_vs_80discount | 32 | 0.037 | 0.070 | 0.238 | 0.201 |
| phi4_mini_reasoning | deriv_3x_valid_vs_constant_error | 30 | 0.164 | 0.075 | 0.640 | 0.476 |
| qwen35_9b | qiwuzhe_pay75_vs_75off | 1 | -0.001 | 0.001 | 0.976 | 0.977 |
| qwen35_9b | youhui25_pay75_vs_75off | 1 | -0.009 | -0.009 | 0.985 | 0.995 |
| qwen35_9b | dabazhe_pay80_vs_80discount | 4 | -0.001 | -0.000 | 0.946 | 0.947 |
| qwen35_9b | deriv_3x_valid_vs_constant_error | 0 | 0.233 | 0.221 | 0.883 | 0.650 |
| qwen3_14b_base | qiwuzhe_pay75_vs_75off | 1 | -0.005 | -0.012 | 0.652 | 0.657 |
| qwen3_14b_base | youhui25_pay75_vs_75off | 39 | -0.049 | -0.070 | 0.878 | 0.927 |
| qwen3_14b_base | dabazhe_pay80_vs_80discount | 38 | -0.003 | 0.006 | 0.808 | 0.811 |
| qwen3_14b_base | deriv_3x_valid_vs_constant_error | 0 | 0.190 | 0.186 | 0.887 | 0.697 |

## Target Tokenization

| model | case | concept | target | n toks | tokens |
|---|---|---|---|---:|---|
| deepseek_r1_0528_qwen3_8b | zh_qiwuzhe | pay75 | 七五折 | 3 | `ä¸ĥ äºĶ æĬĺ` |
| deepseek_r1_0528_qwen3_8b | en_pay75_original | pay75 | 75% of the original price | 7 | `7 5 % Ġof Ġthe Ġoriginal Ġprice` |
| deepseek_r1_0528_qwen3_8b | en_25off | pay75 | 25% off | 4 | `2 5 % Ġoff` |
| deepseek_r1_0528_qwen3_8b | zh_youhui25 | pay75 | 优惠25% | 4 | `ä¼ĺæĥł 2 5 %` |
| deepseek_r1_0528_qwen3_8b | en_75off | off75 | 75% off | 4 | `7 5 % Ġoff` |
| deepseek_r1_0528_qwen3_8b | zh_youhui75 | off75 | 优惠75% | 4 | `ä¼ĺæĥł 7 5 %` |
| deepseek_r1_0528_qwen3_8b | zh_dabazhe | pay80 | 打八折 | 3 | `æīĵ åħ« æĬĺ` |
| deepseek_r1_0528_qwen3_8b | en_pay80_original | pay80 | 80% of the original price | 7 | `8 0 % Ġof Ġthe Ġoriginal Ġprice` |
| deepseek_r1_0528_qwen3_8b | en_20off | pay80 | 20% off | 4 | `2 0 % Ġoff` |
| deepseek_r1_0528_qwen3_8b | en_80discount | off80 | 80% discount | 4 | `8 0 % Ġdiscount` |
| deepseek_r1_0528_qwen3_8b | zh_deriv_3x_valid | linear_derivative_valid | (3x)'=3 | 6 | `( 3 x )' = 3` |
| deepseek_r1_0528_qwen3_8b | en_deriv_3x_valid | linear_derivative_valid | (3x)' = 3 | 7 | `Ġ'( 3 x )' Ġ= Ġ 3` |
| deepseek_r1_0528_qwen3_8b | zh_deriv_3x_bad_constant | linear_derivative_bad_constant | 3x是常数 | 5 | `3 x æĺ¯ å¸¸ æķ°` |
| deepseek_r1_0528_qwen3_8b | en_deriv_3x_bad_constant | linear_derivative_bad_constant | 3x is a constant | 5 | `3 x Ġis Ġa Ġconstant` |
| phi4_mini_reasoning | zh_qiwuzhe | pay75 | 七五折 | 3 | `ä¸ĥ äºĶ æĬĺ` |
| phi4_mini_reasoning | en_pay75_original | pay75 | 75% of the original price | 6 | `75 % Ġof Ġthe Ġoriginal Ġprice` |
| phi4_mini_reasoning | en_25off | pay75 | 25% off | 3 | `25 % Ġoff` |
| phi4_mini_reasoning | zh_youhui25 | pay75 | 优惠25% | 3 | `ä¼ĺæĥł 25 %` |
| phi4_mini_reasoning | en_75off | off75 | 75% off | 3 | `75 % Ġoff` |
| phi4_mini_reasoning | zh_youhui75 | off75 | 优惠75% | 3 | `ä¼ĺæĥł 75 %` |
| phi4_mini_reasoning | zh_dabazhe | pay80 | 打八折 | 3 | `æīĵ åħ« æĬĺ` |
| phi4_mini_reasoning | en_pay80_original | pay80 | 80% of the original price | 6 | `80 % Ġof Ġthe Ġoriginal Ġprice` |
| phi4_mini_reasoning | en_20off | pay80 | 20% off | 3 | `20 % Ġoff` |
| phi4_mini_reasoning | en_80discount | off80 | 80% discount | 3 | `80 % Ġdiscount` |
| phi4_mini_reasoning | zh_deriv_3x_valid | linear_derivative_valid | (3x)'=3 | 6 | `( 3 x )' = 3` |
| phi4_mini_reasoning | en_deriv_3x_valid | linear_derivative_valid | (3x)' = 3 | 7 | `Ġ'( 3 x )' Ġ= Ġ 3` |
| phi4_mini_reasoning | zh_deriv_3x_bad_constant | linear_derivative_bad_constant | 3x是常数 | 5 | `3 x æĺ¯ å¸¸ æķ°` |
| phi4_mini_reasoning | en_deriv_3x_bad_constant | linear_derivative_bad_constant | 3x is a constant | 5 | `3 x Ġis Ġa Ġconstant` |
| qwen35_9b | zh_qiwuzhe | pay75 | 七五折 | 3 | `ä¸ĥ äºĶ æĬĺ` |
| qwen35_9b | en_pay75_original | pay75 | 75% of the original price | 7 | `7 5 % Ġof Ġthe Ġoriginal Ġprice` |
| qwen35_9b | en_25off | pay75 | 25% off | 4 | `2 5 % Ġoff` |
| qwen35_9b | zh_youhui25 | pay75 | 优惠25% | 4 | `ä¼ĺæĥł 2 5 %` |
| qwen35_9b | en_75off | off75 | 75% off | 4 | `7 5 % Ġoff` |
| qwen35_9b | zh_youhui75 | off75 | 优惠75% | 4 | `ä¼ĺæĥł 7 5 %` |
| qwen35_9b | zh_dabazhe | pay80 | 打八折 | 3 | `æīĵ åħ« æĬĺ` |
| qwen35_9b | en_pay80_original | pay80 | 80% of the original price | 7 | `8 0 % Ġof Ġthe Ġoriginal Ġprice` |
| qwen35_9b | en_20off | pay80 | 20% off | 4 | `2 0 % Ġoff` |
| qwen35_9b | en_80discount | off80 | 80% discount | 4 | `8 0 % Ġdiscount` |
| qwen35_9b | zh_deriv_3x_valid | linear_derivative_valid | (3x)'=3 | 6 | `( 3 x )' = 3` |
| qwen35_9b | en_deriv_3x_valid | linear_derivative_valid | (3x)' = 3 | 7 | `Ġ'( 3 x )' Ġ= Ġ 3` |
| qwen35_9b | zh_deriv_3x_bad_constant | linear_derivative_bad_constant | 3x是常数 | 4 | `3 x æĺ¯ å¸¸æķ°` |
| qwen35_9b | en_deriv_3x_bad_constant | linear_derivative_bad_constant | 3x is a constant | 5 | `3 x Ġis Ġa Ġconstant` |
| qwen3_14b_base | zh_qiwuzhe | pay75 | 七五折 | 3 | `ä¸ĥ äºĶ æĬĺ` |
| qwen3_14b_base | en_pay75_original | pay75 | 75% of the original price | 7 | `7 5 % Ġof Ġthe Ġoriginal Ġprice` |
| qwen3_14b_base | en_25off | pay75 | 25% off | 4 | `2 5 % Ġoff` |
| qwen3_14b_base | zh_youhui25 | pay75 | 优惠25% | 4 | `ä¼ĺæĥł 2 5 %` |
| qwen3_14b_base | en_75off | off75 | 75% off | 4 | `7 5 % Ġoff` |
| qwen3_14b_base | zh_youhui75 | off75 | 优惠75% | 4 | `ä¼ĺæĥł 7 5 %` |
| qwen3_14b_base | zh_dabazhe | pay80 | 打八折 | 3 | `æīĵ åħ« æĬĺ` |
| qwen3_14b_base | en_pay80_original | pay80 | 80% of the original price | 7 | `8 0 % Ġof Ġthe Ġoriginal Ġprice` |
| qwen3_14b_base | en_20off | pay80 | 20% off | 4 | `2 0 % Ġoff` |
| qwen3_14b_base | en_80discount | off80 | 80% discount | 4 | `8 0 % Ġdiscount` |
| qwen3_14b_base | zh_deriv_3x_valid | linear_derivative_valid | (3x)'=3 | 6 | `( 3 x )' = 3` |
| qwen3_14b_base | en_deriv_3x_valid | linear_derivative_valid | (3x)' = 3 | 7 | `Ġ'( 3 x )' Ġ= Ġ 3` |
| qwen3_14b_base | zh_deriv_3x_bad_constant | linear_derivative_bad_constant | 3x是常数 | 5 | `3 x æĺ¯ å¸¸ æķ°` |
| qwen3_14b_base | en_deriv_3x_bad_constant | linear_derivative_bad_constant | 3x is a constant | 5 | `3 x Ġis Ġa Ġconstant` |
