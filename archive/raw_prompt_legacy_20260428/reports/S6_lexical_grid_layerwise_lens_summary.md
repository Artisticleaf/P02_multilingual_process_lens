# E25 Layerwise Verifier Lens Summary / E25 分层 verifier logit-lens 汇总

Created / 创建时间: 2026-04-27T18:10:14

The probe projects each hidden state at the verifier decision token through the final LM head. / 本 probe 将 verifier 决策位置的每层 hidden state 通过最终 LM head 投影。
It is a diagnostic lens, not a trained tuned-lens or a complete circuit proof. / 它是诊断性 lens，不是训练过的 tuned-lens，也不是完整 circuit 证明。

## Absolute Yes/No Lens / 绝对 Yes/No lens

| verifier | slice | n | final positive rate | middle positive rate | mean middle->final drop | note |
|---|---|---:|---:|---:|---:|---|
| gemma4_e4b_it | ACPI | 6 | 1.000 | 1.000 | -26.077 | ACPI over-accept risk |
| gemma4_e4b_it | non-ACPI | 6 | 1.000 | 1.000 | -25.236 |  |
| qwen3_14b_base | ACPI | 6 | 0.500 | 1.000 | 8.557 |  |
| qwen3_14b_base | non-ACPI | 6 | 0.500 | 1.000 | 8.428 |  |

### Absolute Rows / 绝对式逐行

| verifier | idx | risk | prompt | target valid | final margin | middle best | middle layer | tag |
|---|---:|---|---|---:|---:|---:|---:|---|
| gemma4_e4b_it | 600048 | valid_clean | en | True | 76.000 | 53.188 | 29 | stable positive |
| gemma4_e4b_it | 600048 | valid_clean | zh | True | 41.000 | 8.949 | 25 | stable positive |
| gemma4_e4b_it | 600049 | acpi_wrong_dabazhe_equals_75pct_in_optional_step | en | False | 78.500 | 54.438 | 30 | output/head re-entanglement candidate |
| gemma4_e4b_it | 600049 | acpi_wrong_dabazhe_equals_75pct_in_optional_step | zh | False | 43.750 | 7.562 | 25 | output/head re-entanglement candidate |
| gemma4_e4b_it | 600070 | acpi_dabazhe_translated_as_80pct_discount_but_multiplies_0p8 | en | False | 72.500 | 52.344 | 30 | output/head re-entanglement candidate |
| gemma4_e4b_it | 600070 | acpi_dabazhe_translated_as_80pct_discount_but_multiplies_0p8 | zh | False | 36.250 | 9.785 | 25 | output/head re-entanglement candidate |
| gemma4_e4b_it | 600071 | valid_clean | en | True | 70.000 | 52.562 | 30 | stable positive |
| gemma4_e4b_it | 600071 | valid_clean | zh | True | 43.000 | 10.102 | 25 | stable positive |
| gemma4_e4b_it | 600150 | acpi_pay75_mistranslated_as_75pct_discount_but_multiplies_0p75 | en | False | 72.500 | 54.688 | 29 | output/head re-entanglement candidate |
| gemma4_e4b_it | 600150 | acpi_pay75_mistranslated_as_75pct_discount_but_multiplies_0p75 | zh | False | 40.500 | 8.719 | 23 | output/head re-entanglement candidate |
| gemma4_e4b_it | 600151 | valid_clean | en | True | 65.500 | 50.656 | 30 | stable positive |
| gemma4_e4b_it | 600151 | valid_clean | zh | True | 42.250 | 10.875 | 23 | stable positive |
| qwen3_14b_base | 600048 | valid_clean | en | True | 13.000 | 19.438 | 29 | stable positive |
| qwen3_14b_base | 600048 | valid_clean | zh | True | -6.125 | 4.406 | 10 | mid-signal lost before output |
| qwen3_14b_base | 600049 | acpi_wrong_dabazhe_equals_75pct_in_optional_step | en | False | 12.812 | 18.906 | 29 | output/head re-entanglement candidate |
| qwen3_14b_base | 600049 | acpi_wrong_dabazhe_equals_75pct_in_optional_step | zh | False | -6.125 | 4.547 | 10 | mid-signal lost before output |
| qwen3_14b_base | 600070 | acpi_dabazhe_translated_as_80pct_discount_but_multiplies_0p8 | en | False | 11.625 | 17.688 | 29 | output/head re-entanglement candidate |
| qwen3_14b_base | 600070 | acpi_dabazhe_translated_as_80pct_discount_but_multiplies_0p8 | zh | False | -6.750 | 4.297 | 10 | mid-signal lost before output |
| qwen3_14b_base | 600071 | valid_clean | en | True | 11.125 | 17.250 | 29 | stable positive |
| qwen3_14b_base | 600071 | valid_clean | zh | True | -6.875 | 4.008 | 10 | mid-signal lost before output |
| qwen3_14b_base | 600150 | acpi_pay75_mistranslated_as_75pct_discount_but_multiplies_0p75 | en | False | 10.500 | 17.594 | 29 | output/head re-entanglement candidate |
| qwen3_14b_base | 600150 | acpi_pay75_mistranslated_as_75pct_discount_but_multiplies_0p75 | zh | False | -6.625 | 3.750 | 10 | mid-signal lost before output |
| qwen3_14b_base | 600151 | valid_clean | en | True | 12.625 | 19.125 | 29 | stable positive |
| qwen3_14b_base | 600151 | valid_clean | zh | True | -6.750 | 3.344 | 21 | mid-signal lost before output |

## Contrastive A/B Lens / 对比式 A/B lens

| verifier | pair | n | final target-positive rate | middle target-positive rate | mean middle->final drop |
|---|---|---:|---:|---:|---:|
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | 4 | 0.500 | 1.000 | 16.877 |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | 4 | 0.500 | 1.000 | 12.830 |
| gemma4_e4b_it | qwen14_s6_pay75_bad150_valid151 | 4 | 0.250 | 1.000 | 13.461 |
| qwen3_14b_base | gemma4_s6_25off_bad49_valid48 | 4 | 0.750 | 1.000 | 2.002 |
| qwen3_14b_base | gemma4_s6_dabazhe_bad70_valid71 | 4 | 0.250 | 1.000 | 1.524 |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | 4 | 0.750 | 1.000 | 1.496 |

### Contrastive Rows / 对比式逐行

| verifier | pair | prompt | order | final margin | middle best | middle layer | tag |
|---|---|---|---|---:|---:|---:|---|
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | en | bad_A | 17.750 | 23.000 | 17 | stable positive |
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | en | bad_B | -23.000 | 5.984 | 21 | mid-signal lost before output |
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | zh | bad_A | 8.000 | 22.844 | 17 | stable positive |
| gemma4_e4b_it | gemma4_s6_25off_bad49_valid48 | zh | bad_B | -13.750 | 4.680 | 28 | mid-signal lost before output |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | en | bad_A | 24.750 | 21.750 | 17 | stable positive |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | en | bad_B | -18.250 | 6.648 | 21 | mid-signal lost before output |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | zh | bad_A | 4.500 | 21.156 | 17 | stable positive |
| gemma4_e4b_it | gemma4_s6_dabazhe_bad70_valid71 | zh | bad_B | -5.500 | 7.266 | 21 | mid-signal lost before output |
| gemma4_e4b_it | qwen14_s6_pay75_bad150_valid151 | en | bad_A | 15.250 | 21.188 | 17 | stable positive |
| gemma4_e4b_it | qwen14_s6_pay75_bad150_valid151 | en | bad_B | -8.750 | 7.932 | 21 | mid-signal lost before output |
| gemma4_e4b_it | qwen14_s6_pay75_bad150_valid151 | zh | bad_A | -0.750 | 21.344 | 17 | mid-signal lost before output |
| gemma4_e4b_it | qwen14_s6_pay75_bad150_valid151 | zh | bad_B | -1.500 | 7.633 | 21 | mid-signal lost before output |
| qwen3_14b_base | gemma4_s6_25off_bad49_valid48 | en | bad_A | -1.625 | 2.762 | 27 | mid-signal lost before output |
| qwen3_14b_base | gemma4_s6_25off_bad49_valid48 | en | bad_B | 1.875 | 2.094 | 22 | stable positive |
| qwen3_14b_base | gemma4_s6_25off_bad49_valid48 | zh | bad_A | 0.125 | 1.725 | 24 | stable positive |
| qwen3_14b_base | gemma4_s6_25off_bad49_valid48 | zh | bad_B | 0.188 | 1.990 | 20 | stable positive |
| qwen3_14b_base | gemma4_s6_dabazhe_bad70_valid71 | en | bad_A | -2.219 | 1.312 | 27 | mid-signal lost before output |
| qwen3_14b_base | gemma4_s6_dabazhe_bad70_valid71 | en | bad_B | 1.906 | 1.906 | 10 | stable positive |
| qwen3_14b_base | gemma4_s6_dabazhe_bad70_valid71 | zh | bad_A | -0.188 | 0.995 | 14 | mid-signal lost before output |
| qwen3_14b_base | gemma4_s6_dabazhe_bad70_valid71 | zh | bad_B | -0.062 | 1.321 | 20 | mid-signal lost before output |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | en | bad_A | -0.812 | 3.000 | 29 | mid-signal lost before output |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | en | bad_B | 2.125 | 1.852 | 10 | stable positive |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | zh | bad_A | 0.500 | 1.193 | 14 | stable positive |
| qwen3_14b_base | qwen14_s6_pay75_bad150_valid151 | zh | bad_B | 0.375 | 2.125 | 29 | stable positive |