# E40 Surface-Semantic Residual Span Patch Summary / E40 表层语义 residual span patch 汇总

Created / 创建时间: 2026-04-28T01:49:23

E40 asks whether the new E39 surface-semantic traps contain patchable hidden process evidence. / E40 问的是：E39 新增表层语义陷阱里是否也有可 patch 的隐藏过程证据。
A clean direction means `valid->bad` raises the Yes-minus-No process margin on the bad trace and `bad->valid` lowers it on the valid trace. / 干净方向指 `valid->bad` 提高坏 trace 的 Yes-No 过程边际，同时 `bad->valid` 降低好 trace 的边际。

## qwen35_9b

Clean residual support/error signal: 12/12 pairs. / 干净 residual support/error 信号：12/12 对。

| task / 任务 | clean? | layer | valid->bad | bad->valid | base valid | base bad | bad span / 错误 span | valid span / 支持 span |
|---|---:|---:|---:|---:|---:|---:|---|---|
| coefficient_vs_exponent | True | 4 | 0.937 | -3.500 | 6.688 | 3.438 | The coefficient is the exponent 3 | the coefficient is the number multiplying x^3 |
| each_vs_total | True | 8 | 6.313 | -5.062 | 6.562 | -0.438 | each student read 24 pages | total pages are 4*6 |
| log_base_argument | True | 12 | 2.875 | -0.563 | 7.375 | 3.125 | The base is 8 and the argument is 2 | log base 2 of 8 asks what exponent on 2 gives 8 |
| mean_vs_median | True | 0 | 0.812 | -3.000 | 7.000 | 0.438 | The mean is the middle value of the ordered list, so it is 4 | The mean is the sum divided by the count |
| percent_increase_vs_percent_of | True | 0 | 0.500 | -3.500 | 6.625 | 1.750 | A 20% increase means the new price is 20% of the original | A 20% increase means add 20% of 50 to the original price |
| prob_without_replacement | True | 4 | 4.875 | -1.500 | 3.687 | -2.188 | Without replacement means the first ball is put back before the second draw | Without replacement means the second draw has 2 red balls left out of 4 balls |
| range_vs_average | True | 4 | 4.000 | -3.438 | 5.875 | -0.312 | The range is the average of the numbers | The range is maximum minus minimum |
| reciprocal_vs_additive_inverse | True | 4 | 3.125 | -7.125 | 6.563 | 0.688 | The reciprocal means the additive inverse, -4 | The reciprocal is the number that multiplies by 4 to give 1 |
| round_vs_truncate | True | 14 | 0.250 | -0.250 | 6.250 | 5.125 | Nearest tenth means drop all later digits, so 4.6 | the hundredths digit is 7, so the tenths digit rounds up |
| zh_exclusive_interval | True | 8 | 5.625 | -6.312 | 7.688 | 0.688 | 大于2且小于6包含2和6 | 大于2且小于6，只能取3、4、5 |
| zh_perimeter_vs_area | True | 4 | 2.250 | -5.563 | 7.813 | 1.938 | 周长就是面积 | 周长是四条边长度之和 |
| zh_yi_wan_unit | True | 0 | 1.188 | -3.625 | 6.250 | 2.938 | 1亿等于1000万 | 1亿等于10000万 |

## Interpretation rule / 解释规则

- Many clean pairs support generalization of the hidden process-signal claim beyond discount and E31. / 多数 pair 干净支持 hidden process signal 泛化到折扣和 E31 之外。
- A high bad base margin plus clean patch means the verifier has evidence but the final threshold still accepts. / 坏 trace 基础边际高且 patch 干净，说明有证据但最终阈值仍接受。
- Weak or unclean pairs should become boundary cases, not be hidden in averages. / 弱或不干净 pair 应作为边界样例，而不是被平均值掩盖。
