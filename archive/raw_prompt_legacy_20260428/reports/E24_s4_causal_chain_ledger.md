# S4 Causal Chain Ledger / S4 因果链证据台账

Created / 创建时间: 2026-04-27T13:09:22

This table joins manual labels, absolute Yes/No verifier results, contrastive sibling results, and span/module patch probes. / 本表把人工标签、绝对式 Yes/No verifier、兄弟对比和 span/module patch 结果合并为同一条证据链。

## Pair-Level Chain / pair 级链条

| pair | bad | valid | ACPI | trap | abs overaccept | contrastive | span patch | MLP patch | boundary note |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| qwen14_deriv_sum_zh_402_bad_403_valid | 402 | 403 | Y | Y | Y | Y | Y | Y | positive chain |
| qwen14_dabazhe_zh_en_445_bad_442_valid | 445 | 442 | Y | Y | Y | Y | Y | N | positive chain |
| qwen35_discount_zh_234_bad_235_valid | 234 | 235 | Y | Y | Y | Y | Y | Y | positive chain |
| qwen35_ratio_zh_en_261_bad_260_valid | 261 | 260 | Y | Y | Y | Y | Y | N | positive chain |
| qwen14_e18_dabazhe_zh_en_92_bad_91_valid | 180092 | 180091 | Y | Y | Y | N | N | N | contrastive weak, patch weak/missing |
| qwen14_e18_dabazhe_zh_en_92_bad_94_valid | 180092 | 180094 | Y | Y | Y | Y | N | N | patch weak/missing |
| qwen14_e18_dabazhe_final_wrong_93_bad_91_valid | 180093 | 180091 | N | Y | Y | N | N | N |  |
| qwen35_e18_discount_234_bad_181000_valid | 234 | 181000 | Y | Y | Y | Y | Y | N | positive chain |
| qwen35_e18_discount_234_bad_181001_valid | 234 | 181001 | Y | Y | Y | Y | Y | N | positive chain |

## Aggregate / 汇总

- Pairs / pair 数: 9
- Manual ACPI pairs / 人工 ACPI pair: 8
- Absolute-overaccepted ACPI pairs / 被绝对式 verifier 过度接受的 ACPI pair: 8
- ACPI pairs with contrastive signal / 有对比信号的 ACPI pair: 7
- ACPI pairs with robust hidden span signal / 有稳健隐藏 span 信号的 ACPI pair: 6
- ACPI pairs with MLP clean-direction signal / 有 MLP clean-direction 信号的 ACPI pair: 2

Interpretation / 解释：this is selected-pair evidence, not population prevalence. / 这是选择后的 pair 级证据，不代表总体发生率。
