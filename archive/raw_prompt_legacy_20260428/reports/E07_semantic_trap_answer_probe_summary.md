# E07 Semantic Trap Answer Probe Summary

This probe scores candidate final answers without generation. Primary metric uses per-token average logprob to reduce length bias.

## Overall

| model | n | acc avg | acc sum | mean gold-vs-best-wrong avg | mean gold-vs-best-wrong sum |
|---|---:|---:|---:|---:|---:|
| deepseek_r1_0528_qwen3_8b | 56 | 0.125 | 0.286 | -1.510 | -1.995 |
| phi4_mini_reasoning | 56 | 0.304 | 0.286 | -0.905 | -3.012 |
| qwen35_9b | 56 | 0.089 | 0.107 | -1.017 | -2.352 |
| qwen3_14b_base | 56 | 0.696 | 0.696 | 0.722 | 1.893 |

## Route Slices

| model | slice | n | acc avg | margin avg |
|---|---|---:|---:|---:|
| deepseek_r1_0528_qwen3_8b | en->en | 14 | 0.000 | -1.598 |
| deepseek_r1_0528_qwen3_8b | en->zh | 14 | 0.071 | -1.620 |
| deepseek_r1_0528_qwen3_8b | zh->en | 14 | 0.143 | -1.319 |
| deepseek_r1_0528_qwen3_8b | zh->zh | 14 | 0.286 | -1.502 |
| phi4_mini_reasoning | en->en | 14 | 0.357 | -0.410 |
| phi4_mini_reasoning | en->zh | 14 | 0.286 | -0.501 |
| phi4_mini_reasoning | zh->en | 14 | 0.286 | -1.063 |
| phi4_mini_reasoning | zh->zh | 14 | 0.286 | -1.647 |
| qwen35_9b | en->en | 14 | 0.214 | -1.004 |
| qwen35_9b | en->zh | 14 | 0.071 | -0.951 |
| qwen35_9b | zh->en | 14 | 0.071 | -1.083 |
| qwen35_9b | zh->zh | 14 | 0.000 | -1.029 |
| qwen3_14b_base | en->en | 14 | 0.786 | 1.001 |
| qwen3_14b_base | en->zh | 14 | 0.643 | 0.927 |
| qwen3_14b_base | zh->en | 14 | 0.714 | 0.522 |
| qwen3_14b_base | zh->zh | 14 | 0.643 | 0.440 |

## Task Slices

| model | task | n | acc avg | margin avg |
|---|---|---:|---:|---:|
| deepseek_r1_0528_qwen3_8b | avg_simple | 4 | 0.500 | -0.581 |
| deepseek_r1_0528_qwen3_8b | avg_weighted | 4 | 0.000 | -1.920 |
| deepseek_r1_0528_qwen3_8b | deriv_coeff | 4 | 0.000 | -2.227 |
| deepseek_r1_0528_qwen3_8b | deriv_product_equiv | 4 | 0.000 | -4.285 |
| deepseek_r1_0528_qwen3_8b | deriv_sum | 4 | 0.000 | -2.075 |
| deepseek_r1_0528_qwen3_8b | disc_en_25_off | 4 | 0.250 | -0.447 |
| deepseek_r1_0528_qwen3_8b | disc_en_75_off | 4 | 0.250 | -0.238 |
| deepseek_r1_0528_qwen3_8b | disc_zh_75_price | 4 | 0.500 | -0.262 |
| deepseek_r1_0528_qwen3_8b | frac_simplify | 4 | 0.000 | -1.720 |
| deepseek_r1_0528_qwen3_8b | percent_then_discount | 4 | 0.000 | -1.798 |
| deepseek_r1_0528_qwen3_8b | ratio_boys_girls | 4 | 0.000 | -1.202 |
| deepseek_r1_0528_qwen3_8b | ratio_boys_total | 4 | 0.000 | -1.616 |
| deepseek_r1_0528_qwen3_8b | ratio_girls_boys | 4 | 0.250 | -0.570 |
| deepseek_r1_0528_qwen3_8b | rem_137_9 | 4 | 0.000 | -2.192 |
| phi4_mini_reasoning | avg_simple | 4 | 0.000 | -1.822 |
| phi4_mini_reasoning | avg_weighted | 4 | 0.250 | -1.101 |
| phi4_mini_reasoning | deriv_coeff | 4 | 0.000 | -1.767 |
| phi4_mini_reasoning | deriv_product_equiv | 4 | 0.000 | -3.856 |
| phi4_mini_reasoning | deriv_sum | 4 | 0.000 | -1.519 |
| phi4_mini_reasoning | disc_en_25_off | 4 | 0.500 | 2.307 |
| phi4_mini_reasoning | disc_en_75_off | 4 | 0.750 | 1.467 |
| phi4_mini_reasoning | disc_zh_75_price | 4 | 1.000 | 2.119 |
| phi4_mini_reasoning | frac_simplify | 4 | 0.000 | -4.192 |
| phi4_mini_reasoning | percent_then_discount | 4 | 0.750 | 0.646 |
| phi4_mini_reasoning | ratio_boys_girls | 4 | 0.500 | -1.520 |
| phi4_mini_reasoning | ratio_boys_total | 4 | 0.500 | -0.537 |
| phi4_mini_reasoning | ratio_girls_boys | 4 | 0.000 | -2.009 |
| phi4_mini_reasoning | rem_137_9 | 4 | 0.000 | -0.889 |
| qwen35_9b | avg_simple | 4 | 0.250 | 0.001 |
| qwen35_9b | avg_weighted | 4 | 0.000 | -0.533 |
| qwen35_9b | deriv_coeff | 4 | 0.000 | -1.242 |
| qwen35_9b | deriv_product_equiv | 4 | 0.000 | -2.239 |
| qwen35_9b | deriv_sum | 4 | 0.000 | -1.032 |
| qwen35_9b | disc_en_25_off | 4 | 0.000 | -0.791 |
| qwen35_9b | disc_en_75_off | 4 | 0.250 | -0.440 |
| qwen35_9b | disc_zh_75_price | 4 | 0.000 | -0.921 |
| qwen35_9b | frac_simplify | 4 | 0.250 | -0.173 |
| qwen35_9b | percent_then_discount | 4 | 0.000 | -1.270 |
| qwen35_9b | ratio_boys_girls | 4 | 0.250 | -0.403 |
| qwen35_9b | ratio_boys_total | 4 | 0.000 | -1.327 |
| qwen35_9b | ratio_girls_boys | 4 | 0.250 | -0.363 |
| qwen35_9b | rem_137_9 | 4 | 0.000 | -3.505 |
| qwen3_14b_base | avg_simple | 4 | 1.000 | 2.237 |
| qwen3_14b_base | avg_weighted | 4 | 1.000 | 1.190 |
| qwen3_14b_base | deriv_coeff | 4 | 0.000 | -0.761 |
| qwen3_14b_base | deriv_product_equiv | 4 | 0.000 | -0.787 |
| qwen3_14b_base | deriv_sum | 4 | 0.000 | -0.806 |
| qwen3_14b_base | disc_en_25_off | 4 | 1.000 | 1.731 |
| qwen3_14b_base | disc_en_75_off | 4 | 1.000 | 1.630 |
| qwen3_14b_base | disc_zh_75_price | 4 | 1.000 | 1.311 |
| qwen3_14b_base | frac_simplify | 4 | 1.000 | 0.896 |
| qwen3_14b_base | percent_then_discount | 4 | 1.000 | 0.826 |
| qwen3_14b_base | ratio_boys_girls | 4 | 1.000 | 1.962 |
| qwen3_14b_base | ratio_boys_total | 4 | 0.500 | 0.093 |
| qwen3_14b_base | ratio_girls_boys | 4 | 1.000 | 1.849 |
| qwen3_14b_base | rem_137_9 | 4 | 0.250 | -1.256 |

## Most Negative Gold Margins

| model | task | route | gold | pred avg | margin avg | trap |
|---|---|---|---|---|---:|---|
| deepseek_r1_0528_qwen3_8b | deriv_product_equiv | zh->en | 2x+3 | 3x^2 + 6x | -4.997 | Product rule or expansion; same answer as x^2+3x. |
| deepseek_r1_0528_qwen3_8b | deriv_product_equiv | zh->zh | 2x+3 | 3x^2 + 6x | -4.254 | Product rule or expansion; same answer as x^2+3x. |
| deepseek_r1_0528_qwen3_8b | deriv_product_equiv | en->en | 2x+3 | 3x^2 + 6x | -4.176 | Product rule or expansion; same answer as x^2+3x. |
| deepseek_r1_0528_qwen3_8b | deriv_product_equiv | en->zh | 2x+3 | 3x^2 + 6x | -3.714 | Product rule or expansion; same answer as x^2+3x. |
| deepseek_r1_0528_qwen3_8b | rem_137_9 | en->zh | 2 | 1 | -3.094 | Long division late arithmetic error. |
| deepseek_r1_0528_qwen3_8b | avg_weighted | zh->zh | 85 | 255 | -3.003 | Total is 3*85; do not average 80 and 90 only. |
| deepseek_r1_0528_qwen3_8b | frac_simplify | zh->zh | 3/4 | 0.75 | -2.834 | Divide by common factor, do not subtract. |
| deepseek_r1_0528_qwen3_8b | rem_137_9 | zh->zh | 2 | 1 | -2.413 | Long division late arithmetic error. |
| deepseek_r1_0528_qwen3_8b | deriv_sum | zh->en | 2x+3 | 2x + 3 | -2.394 | Power rule and linear term. |
| deepseek_r1_0528_qwen3_8b | deriv_coeff | en->zh | 6x+1 | 6x + 1 | -2.372 | Coefficient and x derivative. |
| deepseek_r1_0528_qwen3_8b | deriv_coeff | zh->en | 6x+1 | 6x + 1 | -2.282 | Coefficient and x derivative. |
| deepseek_r1_0528_qwen3_8b | avg_weighted | en->zh | 85 | 255 | -2.270 | Total is 3*85; do not average 80 and 90 only. |
| deepseek_r1_0528_qwen3_8b | deriv_sum | zh->zh | 2x+3 | 2x + 3 | -2.231 | Power rule and linear term. |
| deepseek_r1_0528_qwen3_8b | deriv_coeff | en->en | 6x+1 | 6x + 1 | -2.131 | Coefficient and x derivative. |
| deepseek_r1_0528_qwen3_8b | deriv_coeff | zh->zh | 6x+1 | 6x + 1 | -2.125 | Coefficient and x derivative. |
| deepseek_r1_0528_qwen3_8b | percent_then_discount | en->zh | 80 | 100 | -2.116 | Sequential percentage changes: 80*1.25*0.8. |
| deepseek_r1_0528_qwen3_8b | percent_then_discount | en->en | 80 | 100 | -2.109 | Sequential percentage changes: 80*1.25*0.8. |
| deepseek_r1_0528_qwen3_8b | avg_weighted | zh->en | 85 | 255 | -2.058 | Total is 3*85; do not average 80 and 90 only. |
| phi4_mini_reasoning | frac_simplify | zh->zh | 3/4 | 6/8 | -6.494 | Divide by common factor, do not subtract. |
| phi4_mini_reasoning | deriv_product_equiv | zh->en | 2x+3 | 3x^2 + 6x | -4.877 | Product rule or expansion; same answer as x^2+3x. |
| phi4_mini_reasoning | frac_simplify | zh->en | 3/4 | 6/8 | -4.344 | Divide by common factor, do not subtract. |
| phi4_mini_reasoning | frac_simplify | en->zh | 3/4 | 6/8 | -3.948 | Divide by common factor, do not subtract. |
| phi4_mini_reasoning | ratio_boys_girls | zh->zh | 40 | 24 | -3.820 | Do not confuse boys:girls with boys:total. |
| phi4_mini_reasoning | deriv_product_equiv | en->zh | 2x+3 | x^2 + 3x | -3.705 | Product rule or expansion; same answer as x^2+3x. |
| phi4_mini_reasoning | deriv_product_equiv | zh->zh | 2x+3 | 2x + 3 | -3.428 | Product rule or expansion; same answer as x^2+3x. |
| phi4_mini_reasoning | deriv_product_equiv | en->en | 2x+3 | x^2 + 3x | -3.413 | Product rule or expansion; same answer as x^2+3x. |
| phi4_mini_reasoning | ratio_boys_girls | zh->en | 40 | 24 | -2.824 | Do not confuse boys:girls with boys:total. |
| phi4_mini_reasoning | avg_simple | en->en | 11 | 5 | -2.750 | Total is 3*9, not 9+3. |
| phi4_mini_reasoning | deriv_coeff | zh->en | 6x+1 | 6x + 1 | -2.546 | Coefficient and x derivative. |
| phi4_mini_reasoning | ratio_girls_boys | zh->zh | 40 | 24 | -2.451 | Ratio order is reversed relative to boys:girls. |
| phi4_mini_reasoning | deriv_sum | en->en | 2x+3 | 2x + 3 | -2.416 | Power rule and linear term. |
| phi4_mini_reasoning | deriv_coeff | zh->zh | 6x+1 | 6x + 1 | -2.366 | Coefficient and x derivative. |
| phi4_mini_reasoning | ratio_girls_boys | en->zh | 40 | 15 | -2.340 | Ratio order is reversed relative to boys:girls. |
| phi4_mini_reasoning | ratio_boys_total | en->zh | 40 | 15 | -2.280 | Here 3/8 is boys:total, unlike boys:girls 3:5. |
| phi4_mini_reasoning | ratio_girls_boys | zh->en | 40 | 24 | -1.994 | Ratio order is reversed relative to boys:girls. |
| phi4_mini_reasoning | frac_simplify | en->en | 3/4 | 6/8 | -1.982 | Divide by common factor, do not subtract. |
| qwen35_9b | rem_137_9 | zh->zh | 2 | 1 | -3.988 | Long division late arithmetic error. |
| qwen35_9b | rem_137_9 | zh->en | 2 | 1 | -3.781 | Long division late arithmetic error. |
| qwen35_9b | rem_137_9 | en->en | 2 | 1 | -3.344 | Long division late arithmetic error. |
| qwen35_9b | rem_137_9 | en->zh | 2 | 1 | -2.906 | Long division late arithmetic error. |
| qwen35_9b | deriv_product_equiv | zh->en | 2x+3 | 3x^2 + 6x | -2.818 | Product rule or expansion; same answer as x^2+3x. |
| qwen35_9b | deriv_product_equiv | en->en | 2x+3 | 3x^2 + 6x | -2.206 | Product rule or expansion; same answer as x^2+3x. |
| qwen35_9b | deriv_product_equiv | zh->zh | 2x+3 | 3x^2 + 6x | -2.134 | Product rule or expansion; same answer as x^2+3x. |
| qwen35_9b | percent_then_discount | zh->en | 80 | 100 | -1.807 | Sequential percentage changes: 80*1.25*0.8. |
| qwen35_9b | deriv_product_equiv | en->zh | 2x+3 | 3x^2 + 6x | -1.800 | Product rule or expansion; same answer as x^2+3x. |
| qwen35_9b | percent_then_discount | zh->zh | 80 | 100 | -1.653 | Sequential percentage changes: 80*1.25*0.8. |
| qwen35_9b | disc_zh_75_price | en->zh | 60 | 80 | -1.630 | Chinese 七五折 means pay 75%, not 75% off. |
| qwen35_9b | deriv_coeff | zh->en | 6x+1 | 6x + 1 | -1.538 | Coefficient and x derivative. |
| qwen35_9b | disc_en_25_off | en->en | 60 | 80 | -1.500 | 25% off means pay 75%. |
| qwen35_9b | ratio_boys_total | zh->en | 40 | 24 | -1.469 | Here 3/8 is boys:total, unlike boys:girls 3:5. |
| qwen35_9b | disc_zh_75_price | en->en | 60 | 80 | -1.410 | Chinese 七五折 means pay 75%, not 75% off. |
| qwen35_9b | ratio_boys_total | zh->zh | 40 | 15 | -1.389 | Here 3/8 is boys:total, unlike boys:girls 3:5. |
| qwen35_9b | disc_en_25_off | en->zh | 60 | 80 | -1.259 | 25% off means pay 75%. |
| qwen35_9b | ratio_boys_total | en->zh | 40 | 24 | -1.258 | Here 3/8 is boys:total, unlike boys:girls 3:5. |
| qwen3_14b_base | rem_137_9 | zh->zh | 2 | 1 | -3.775 | Long division late arithmetic error. |
| qwen3_14b_base | rem_137_9 | zh->en | 2 | 1 | -2.313 | Long division late arithmetic error. |
| qwen3_14b_base | deriv_sum | zh->zh | 2x+3 | 2x + 3 | -1.086 | Power rule and linear term. |
| qwen3_14b_base | deriv_product_equiv | zh->zh | 2x+3 | 2x + 3 | -0.982 | Product rule or expansion; same answer as x^2+3x. |
| qwen3_14b_base | deriv_sum | en->zh | 2x+3 | 2x + 3 | -0.934 | Power rule and linear term. |
| qwen3_14b_base | deriv_coeff | zh->zh | 6x+1 | 6x + 1 | -0.917 | Coefficient and x derivative. |
| qwen3_14b_base | deriv_coeff | en->zh | 6x+1 | 6x + 1 | -0.847 | Coefficient and x derivative. |
| qwen3_14b_base | deriv_product_equiv | en->zh | 2x+3 | 2x + 3 | -0.775 | Product rule or expansion; same answer as x^2+3x. |
| qwen3_14b_base | deriv_product_equiv | zh->en | 2x+3 | 2x + 3 | -0.756 | Product rule or expansion; same answer as x^2+3x. |
| qwen3_14b_base | deriv_coeff | zh->en | 6x+1 | 6x + 1 | -0.739 | Coefficient and x derivative. |
| qwen3_14b_base | deriv_sum | zh->en | 2x+3 | 2x + 3 | -0.714 | Power rule and linear term. |
| qwen3_14b_base | deriv_product_equiv | en->en | 2x+3 | 2x + 3 | -0.637 | Product rule or expansion; same answer as x^2+3x. |
| qwen3_14b_base | ratio_boys_total | en->zh | 40 | 15 | -0.601 | Here 3/8 is boys:total, unlike boys:girls 3:5. |
| qwen3_14b_base | deriv_coeff | en->en | 6x+1 | 6x + 1 | -0.540 | Coefficient and x derivative. |
| qwen3_14b_base | ratio_boys_total | zh->zh | 40 | 24 | -0.524 | Here 3/8 is boys:total, unlike boys:girls 3:5. |
| qwen3_14b_base | rem_137_9 | en->zh | 2 | 8 | -0.500 | Long division late arithmetic error. |
| qwen3_14b_base | deriv_sum | en->en | 2x+3 | 2x + 3 | -0.491 | Power rule and linear term. |
| qwen3_14b_base | disc_zh_75_price | zh->en | 60 | 60 | 0.256 | Chinese 七五折 means pay 75%, not 75% off. |
