# E40 Surface-Semantic Residual Span Patch Summary / E40 表层语义 residual span patch 汇总

Created / 创建时间: 2026-04-28T00:30:47

E40 asks whether the new E39 surface-semantic traps contain patchable hidden process evidence. / E40 问的是：E39 新增表层语义陷阱里是否也有可 patch 的隐藏过程证据。
A clean direction means `valid->bad` raises the Yes-minus-No process margin on the bad trace and `bad->valid` lowers it on the valid trace. / 干净方向指 `valid->bad` 提高坏 trace 的 Yes-No 过程边际，同时 `bad->valid` 降低好 trace 的边际。

## qwen35_9b

Clean residual support/error signal: 11/12 pairs. / 干净 residual support/error 信号：11/12 对。

| task / 任务 | clean? | layer | valid->bad | bad->valid | base valid | base bad | bad span / 错误 span | valid span / 支持 span |
|---|---:|---:|---:|---:|---:|---:|---|---|
| coefficient_vs_exponent | True | 8 | 0.375 | -0.375 | 3.875 | 3.062 | The coefficient is the exponent 3 | the coefficient is the number multiplying x^3 |
| each_vs_total | True | 8 | 3.375 | -3.188 | 3.438 | -0.625 | each student read 24 pages | total pages are 4*6 |
| log_base_argument | True | 4 | 0.062 | -1.250 | 3.562 | 2.125 | The base is 8 and the argument is 2 | log base 2 of 8 asks what exponent on 2 gives 8 |
| mean_vs_median | False | 4 | 0.000 | -1.438 | 3.250 | -0.375 | The mean is the middle value of the ordered list, so it is 4 | The mean is the sum divided by the count |
| percent_increase_vs_percent_of | True | 0 | 0.750 | -1.313 | 3.125 | 0.875 | A 20% increase means the new price is 20% of the original | A 20% increase means add 20% of 50 to the original price |
| prob_without_replacement | True | 4 | 3.062 | -0.688 | 2.438 | -1.250 | Without replacement means the first ball is put back before the second draw | Without replacement means the second draw has 2 red balls left out of 4 balls |
| range_vs_average | True | 4 | 1.250 | -1.438 | 3.062 | 0.875 | The range is the average of the numbers | The range is maximum minus minimum |
| reciprocal_vs_additive_inverse | True | 0 | 1.250 | -4.562 | 3.438 | 0.500 | The reciprocal means the additive inverse, -4 | The reciprocal is the number that multiplies by 4 to give 1 |
| round_vs_truncate | True | 20 | 0.000 | -0.000 | 2.875 | 2.562 | Nearest tenth means drop all later digits, so 4.6 | the hundredths digit is 7, so the tenths digit rounds up |
| zh_exclusive_interval | True | 8 | 3.062 | -4.187 | 3.687 | 0.125 | 大于2且小于6包含2和6 | 大于2且小于6，只能取3、4、5 |
| zh_perimeter_vs_area | True | 4 | 1.750 | -2.625 | 3.625 | 0.875 | 周长就是面积 | 周长是四条边长度之和 |
| zh_yi_wan_unit | True | 0 | 1.375 | -3.875 | 3.750 | 0.375 | 1亿等于1000万 | 1亿等于10000万 |

## qwen3_14b_base

Clean residual support/error signal: 10/12 pairs. / 干净 residual support/error 信号：10/12 对。

| task / 任务 | clean? | layer | valid->bad | bad->valid | base valid | base bad | bad span / 错误 span | valid span / 支持 span |
|---|---:|---:|---:|---:|---:|---:|---|---|
| coefficient_vs_exponent | True | 0 | 2.250 | -3.125 | 3.250 | -0.750 | The coefficient is the exponent 3 | the coefficient is the number multiplying x^3 |
| each_vs_total | True | 12 | 2.500 | -3.750 | 3.000 | -1.500 | each student read 24 pages | total pages are 4*6 |
| log_base_argument | True | 16 | 2.375 | -1.875 | 3.875 | -0.250 | The base is 8 and the argument is 2 | log base 2 of 8 asks what exponent on 2 gives 8 |
| mean_vs_median | True | 12 | 0.875 | -2.000 | 3.125 | -0.750 | The mean is the middle value of the ordered list, so it is 4 | The mean is the sum divided by the count |
| percent_increase_vs_percent_of | True | 4 | 1.250 | -1.125 | 3.375 | 0.875 | A 20% increase means the new price is 20% of the original | A 20% increase means add 20% of 50 to the original price |
| prob_without_replacement | True | 8 | 4.000 | -0.625 | 1.875 | -1.875 | Without replacement means the first ball is put back before the second draw | Without replacement means the second draw has 2 red balls left out of 4 balls |
| range_vs_average | True | 16 | 2.750 | -2.750 | 2.875 | -1.000 | The range is the average of the numbers | The range is maximum minus minimum |
| reciprocal_vs_additive_inverse | True | 16 | 2.250 | -3.000 | 2.875 | -0.750 | The reciprocal means the additive inverse, -4 | The reciprocal is the number that multiplies by 4 to give 1 |
| round_vs_truncate | False | 28 | -0.125 | -0.125 | 1.625 | 2.375 | Nearest tenth means drop all later digits, so 4.6 | the hundredths digit is 7, so the tenths digit rounds up |
| zh_exclusive_interval | True | 14 | 3.125 | -3.000 | 2.875 | -0.875 | 大于2且小于6包含2和6 | 大于2且小于6，只能取3、4、5 |
| zh_perimeter_vs_area | True | 14 | 1.750 | -1.250 | 1.875 | -1.500 | 周长就是面积 | 周长是四条边长度之和 |
| zh_yi_wan_unit | False | 8 | -0.500 | -2.250 | 2.750 | 0.375 | 1亿等于1000万 | 1亿等于10000万 |

## Interpretation rule / 解释规则

- Many clean pairs support generalization of the hidden process-signal claim beyond discount and E31. / 多数 pair 干净支持 hidden process signal 泛化到折扣和 E31 之外。
- A high bad base margin plus clean patch means the verifier has evidence but the final threshold still accepts. / 坏 trace 基础边际高且 patch 干净，说明有证据但最终阈值仍接受。
- Weak or unclean pairs should become boundary cases, not be hidden in averages. / 弱或不干净 pair 应作为边界样例，而不是被平均值掩盖。
