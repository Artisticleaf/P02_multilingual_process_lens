# S6 Lexical Paraphrase Grid Audit / S6 表层词汇改写网格审计

Created / 创建时间: 2026-04-27T18:05:16

Scope / 范围: 4 generator models, 12 paraphrase/control tasks, 2 routes (`zh->zh`, `zh->en`), k=2. Total 192 rows. / 4 个生成模型、12 个改写/控制任务、2 条 route、每格 2 条样本，总计 192 行。

## Model-Level Summary / 模型级汇总

| model | n | usable trace | final correct | process invalid | ACPI | paper-grade ACPI | semantic drift final-wrong | route violations |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| deepseek_r1_0528_qwen3_8b | 48 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gemma4_e4b_it | 48 | 48 | 42 | 8 | 2 | 2 | 6 | 9 |
| qwen35_9b | 48 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| qwen3_14b_base | 48 | 48 | 42 | 7 | 1 | 1 | 5 | 8 |

## Human-Readable Findings / 人话发现

- Qwen3.5-9B and DeepSeek-Qwen8B did not produce clean auditable traces in this prompt setting: Qwen3.5-9B mostly wrote meta `Thinking Process` plans; DeepSeek emitted prompt-corrupted `<think>` text. / 在此提示设置下，Qwen3.5-9B 主要输出元规划，DeepSeek 输出提示损坏文本，因此不纳入 ACPI 生成率。
- Gemma4 produced two paper-grade ACPI rows: one says `打八折` means paying 75% on a 25%-off task, and one translates `打八折` as `80% discount` while multiplying by 0.8. / Gemma4 产生两条论文级 ACPI。
- Qwen14 produced one paper-grade ACPI row: it translates `sold for 75% of original price` into `75% discount` but still multiplies by 0.75 and gets 60. / Qwen14 产生一条论文级 ACPI。
- Several final-wrong semantic drifts also appeared: especially `七五折/pay75 -> 75% off/pay25`, `pay25 -> 25% off/pay75`, and `打八折/pay80 -> 80% discount/pay20`. / 另有多条答案错误的语义漂移。

## Paper-Grade ACPI Rows / 论文级 ACPI 行

| audit idx | model | task | route | sample | final | earliest error | why it matters |
|---:|---|---|---|---:|---|---|---|
| 600049 | gemma4_e4b_it | disc_25_off_direct | zh->zh | 1 | 60美元 | 或者，如果打八折（即支付 75% 的价格） | 25% off can be computed as pay 75%, but calling that 打八折 is wrong because 八折 means pay 80%. |
| 600070 | gemma4_e4b_it | seq_dabazhe_pay80 | zh->en | 0 | 80 | apply an 80% discount (or multiply by 0.8) | The computation uses pay 80%, but the English phrase 80% discount normally means pay 20%. |
| 600150 | qwen3_14b_base | disc_pay75_en | zh->en | 0 | $60 | sold at a 75% discount of its original price | The Chinese/meaning is sold for 75% of original price; 75% discount would mean pay 25%. The trace then multiplies by 0.75 and gets the correct final answer. |

## Semantic-Drift Final-Wrong Rows / 语义漂移但答案错误行

| audit idx | model | task | route | sample | gold | final | drift |
|---:|---|---|---|---:|---|---|---|
| 600058 | gemma4_e4b_it | disc_zh_qiwu_price | zh->en | 0 | 60 | 20 | treats 七五折/pay75 as 75% off/pay25 |
| 600059 | gemma4_e4b_it | disc_zh_qiwu_price | zh->en | 1 | 60 | $20 | treats 七五折/pay75 as 75% off/pay25 |
| 600064 | gemma4_e4b_it | disc_pay25_explicit | zh->zh | 0 | 20 | 60美元 | treats pay25 as 25% off/pay75 |
| 600065 | gemma4_e4b_it | disc_pay25_explicit | zh->zh | 1 | 20 | 60美元 | treats pay25 as 25% off/pay75 |
| 600066 | gemma4_e4b_it | disc_pay25_explicit | zh->en | 0 | 20 | $60 | treats pay25 as 25% off/pay75 |
| 600067 | gemma4_e4b_it | disc_pay25_explicit | zh->en | 1 | 20 | $60 | treats pay25 as 25% off/pay75 |
| 600155 | qwen3_14b_base | disc_zh_qiwu_price | zh->en | 1 | 60 | 20. | treats 七五折/pay75 as 75% off/pay25 |
| 600160 | qwen3_14b_base | disc_pay25_explicit | zh->zh | 0 | 20 | 60美元。 | treats pay25 as 25% off/pay75 |
| 600161 | qwen3_14b_base | disc_pay25_explicit | zh->zh | 1 | 20 | 60美元。 | treats pay25 as 25% off/pay75 |
| 600162 | qwen3_14b_base | disc_pay25_explicit | zh->en | 0 | 20 | 60 dollars. | treats pay25 as 25% off/pay75 |
| 600167 | qwen3_14b_base | seq_dabazhe_pay80 | zh->en | 1 | 80 | $20. | treats 打八折/pay80 as 80% discount/pay20 |

## Task-Level Signal / 任务级信号

| task | n | final correct | ACPI | semantic drift final-wrong |
|---|---:|---:|---:|---:|
| deriv_coeff_control | 16 | 8 | 0 | 0 |
| deriv_sum_control | 16 | 8 | 0 | 0 |
| disc_25_off_direct | 16 | 8 | 1 | 0 |
| disc_75_off_direct | 16 | 8 | 0 | 0 |
| disc_pay25_explicit | 16 | 1 | 0 | 7 |
| disc_pay75_en | 16 | 8 | 1 | 0 |
| disc_zh_qiwu_price | 16 | 4 | 0 | 3 |
| ratio_boys_girls_control | 16 | 8 | 0 | 0 |
| ratio_boys_total_control | 16 | 8 | 0 | 0 |
| seq_20_off_pay80 | 16 | 8 | 0 | 0 |
| seq_80_discount_pay20 | 16 | 8 | 0 | 0 |
| seq_dabazhe_pay80 | 16 | 7 | 1 | 1 |

## Interpretation / 解释

This S6 grid strengthens the lexical-causality story: the same arithmetic answers reappear under different surface forms, but specific pay/off lexicalizations flip the process semantics. / S6 网格强化了词汇因果故事：相同算术答案在不同表层形式下出现，但 pay/off 词汇化会翻转过程语义。

This is still a targeted grid, not a population prevalence estimate. The usable generator rows are mainly Gemma4 and Qwen14 in this run; Qwen3.5-9B and DeepSeek need prompt/template fixes before generator-side conclusions. / 这仍是定向网格，不是总体发生率；本轮可用生成行主要来自 Gemma4 和 Qwen14。
