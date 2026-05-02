# E37 E31 Layerwise Verifier Lens Summary / E37 E31 分层 verifier logit-lens 汇总

Created / 创建时间: 2026-04-27T23:21:33

The probe projects each hidden state at the verifier decision token through the final LM head. / 本 probe 将 verifier 决策位置的每层 hidden state 通过最终 LM head 投影。
It is a diagnostic lens, not a trained tuned-lens or a complete circuit proof. / 它是诊断性 lens，不是训练过的 tuned-lens，也不是完整 circuit 证明。

## Absolute Yes/No Lens / 绝对 Yes/No lens

| verifier | slice | n | final positive rate | middle positive rate | mean middle->final drop | note |
|---|---|---:|---:|---:|---:|---|
| qwen35_9b | ACPI | 10 | 0.600 | 0.500 | 5.311 | ACPI over-accept risk |
| qwen35_9b | non-ACPI | 10 | 1.000 | 0.500 | 4.035 |  |
| qwen3_14b_base | ACPI | 10 | 0.500 | 1.000 | 8.037 |  |
| qwen3_14b_base | non-ACPI | 10 | 0.500 | 1.000 | 8.252 |  |

### Absolute Rows / 绝对式逐行

| verifier | idx | risk | prompt | target valid | final margin | middle best | middle layer | tag |
|---|---:|---|---|---:|---:|---:|---:|---|
| qwen35_9b | 310001 | e31_valid_correct | en | True | 4.750 | 15.000 | 23 | stable positive |
| qwen35_9b | 310001 | e31_valid_correct | zh | True | 2.438 | 0.000 | 8 | late-only positive |
| qwen35_9b | 310002 | e31_invalid_correct | en | False | -0.625 | 11.462 | 22 | mid-signal lost before output |
| qwen35_9b | 310002 | e31_invalid_correct | zh | False | -0.500 | 0.000 | 8 | no positive lens signal |
| qwen35_9b | 310007 | e31_valid_correct | en | True | 4.125 | 13.734 | 23 | stable positive |
| qwen35_9b | 310007 | e31_valid_correct | zh | True | 2.000 | 0.000 | 8 | late-only positive |
| qwen35_9b | 310008 | e31_invalid_correct | en | False | 3.375 | 12.852 | 23 | output/head re-entanglement candidate |
| qwen35_9b | 310008 | e31_invalid_correct | zh | False | 1.625 | 0.000 | 8 | output/head re-entanglement candidate |
| qwen35_9b | 310013 | e31_valid_correct | en | True | 3.500 | 14.391 | 23 | stable positive |
| qwen35_9b | 310013 | e31_valid_correct | zh | True | 1.250 | 0.000 | 8 | late-only positive |
| qwen35_9b | 310014 | e31_invalid_correct | en | False | -1.625 | 9.770 | 22 | mid-signal lost before output |
| qwen35_9b | 310014 | e31_invalid_correct | zh | False | -1.750 | 0.000 | 8 | no positive lens signal |
| qwen35_9b | 310019 | e31_valid_correct | en | True | 4.250 | 13.906 | 23 | stable positive |
| qwen35_9b | 310019 | e31_valid_correct | zh | True | 2.125 | 0.000 | 8 | late-only positive |
| qwen35_9b | 310020 | e31_invalid_correct | en | False | 2.500 | 12.641 | 23 | output/head re-entanglement candidate |
| qwen35_9b | 310020 | e31_invalid_correct | zh | False | 1.000 | 0.000 | 8 | output/head re-entanglement candidate |
| qwen35_9b | 310025 | e31_valid_correct | en | True | 4.000 | 13.633 | 23 | stable positive |
| qwen35_9b | 310025 | e31_valid_correct | zh | True | 1.875 | 0.000 | 8 | late-only positive |
| qwen35_9b | 310026 | e31_invalid_correct | en | False | 1.500 | 12.508 | 22 | output/head re-entanglement candidate |
| qwen35_9b | 310026 | e31_invalid_correct | zh | False | 0.625 | 0.000 | 8 | output/head re-entanglement candidate |
| qwen3_14b_base | 310001 | e31_valid_correct | en | True | 12.375 | 18.969 | 29 | stable positive |
| qwen3_14b_base | 310001 | e31_valid_correct | zh | True | -5.875 | 3.961 | 10 | mid-signal lost before output |
| qwen3_14b_base | 310002 | e31_invalid_correct | en | False | 10.125 | 15.469 | 29 | output/head re-entanglement candidate |
| qwen3_14b_base | 310002 | e31_invalid_correct | zh | False | -6.875 | 4.102 | 10 | mid-signal lost before output |
| qwen3_14b_base | 310007 | e31_valid_correct | en | True | 12.375 | 19.312 | 29 | stable positive |
| qwen3_14b_base | 310007 | e31_valid_correct | zh | True | -6.375 | 3.508 | 10 | mid-signal lost before output |
| qwen3_14b_base | 310008 | e31_invalid_correct | en | False | 12.375 | 18.969 | 29 | output/head re-entanglement candidate |
| qwen3_14b_base | 310008 | e31_invalid_correct | zh | False | -6.500 | 3.453 | 10 | mid-signal lost before output |
| qwen3_14b_base | 310013 | e31_valid_correct | en | True | 12.125 | 18.562 | 29 | stable positive |
| qwen3_14b_base | 310013 | e31_valid_correct | zh | True | -6.250 | 3.648 | 10 | mid-signal lost before output |
| qwen3_14b_base | 310014 | e31_invalid_correct | en | False | 10.000 | 14.562 | 29 | output/head re-entanglement candidate |
| qwen3_14b_base | 310014 | e31_invalid_correct | zh | False | -7.250 | 3.750 | 17 | mid-signal lost before output |
| qwen3_14b_base | 310019 | e31_valid_correct | en | True | 12.625 | 19.812 | 29 | stable positive |
| qwen3_14b_base | 310019 | e31_valid_correct | zh | True | -5.750 | 4.008 | 10 | mid-signal lost before output |
| qwen3_14b_base | 310020 | e31_invalid_correct | en | False | 10.250 | 15.500 | 29 | output/head re-entanglement candidate |
| qwen3_14b_base | 310020 | e31_invalid_correct | zh | False | -7.000 | 3.898 | 10 | mid-signal lost before output |
| qwen3_14b_base | 310025 | e31_valid_correct | en | True | 12.125 | 18.062 | 29 | stable positive |
| qwen3_14b_base | 310025 | e31_valid_correct | zh | True | -6.500 | 3.547 | 10 | mid-signal lost before output |
| qwen3_14b_base | 310026 | e31_invalid_correct | en | False | 10.500 | 14.969 | 29 | output/head re-entanglement candidate |
| qwen3_14b_base | 310026 | e31_invalid_correct | zh | False | -7.625 | 3.695 | 10 | mid-signal lost before output |

## Contrastive A/B Lens / 对比式 A/B lens

| verifier | pair | n | final target-positive rate | middle target-positive rate | mean middle->final drop |
|---|---|---:|---:|---:|---:|
| qwen35_9b | e31_comb_unordered_bad310026_valid310025 | 4 | 1.000 | 0.500 | 0.879 |
| qwen35_9b | e31_geometry_diameter_bad310020_valid310019 | 4 | 1.000 | 1.000 | 1.577 |
| qwen35_9b | e31_inequality_boundary_bad310008_valid310007 | 4 | 0.750 | 0.500 | 1.071 |
| qwen35_9b | e31_ratio_boys_girls_bad310002_valid310001 | 4 | 1.000 | 1.000 | 1.446 |
| qwen35_9b | e31_unit_dozen_pairs_bad310014_valid310013 | 4 | 0.750 | 0.750 | 1.171 |
| qwen3_14b_base | e31_comb_unordered_bad310026_valid310025 | 4 | 0.750 | 1.000 | 1.641 |
| qwen3_14b_base | e31_geometry_diameter_bad310020_valid310019 | 4 | 0.750 | 1.000 | 1.449 |
| qwen3_14b_base | e31_inequality_boundary_bad310008_valid310007 | 4 | 0.250 | 1.000 | 1.505 |
| qwen3_14b_base | e31_ratio_boys_girls_bad310002_valid310001 | 4 | 0.750 | 1.000 | 1.496 |
| qwen3_14b_base | e31_unit_dozen_pairs_bad310014_valid310013 | 4 | 0.750 | 1.000 | 1.719 |

### Contrastive Rows / 对比式逐行

| verifier | pair | prompt | order | final margin | middle best | middle layer | tag |
|---|---|---|---|---:|---:|---:|---|
| qwen35_9b | e31_comb_unordered_bad310026_valid310025 | en | bad_A | 0.625 | 4.484 | 22 | stable positive |
| qwen35_9b | e31_comb_unordered_bad310026_valid310025 | en | bad_B | 1.125 | -0.266 | 23 | late-only positive |
| qwen35_9b | e31_comb_unordered_bad310026_valid310025 | zh | bad_A | 0.375 | 2.734 | 20 | stable positive |
| qwen35_9b | e31_comb_unordered_bad310026_valid310025 | zh | bad_B | 0.750 | -0.562 | 21 | late-only positive |
| qwen35_9b | e31_geometry_diameter_bad310020_valid310019 | en | bad_A | 0.375 | 4.289 | 22 | stable positive |
| qwen35_9b | e31_geometry_diameter_bad310020_valid310019 | en | bad_B | 2.375 | 2.781 | 23 | stable positive |
| qwen35_9b | e31_geometry_diameter_bad310020_valid310019 | zh | bad_A | 0.250 | 2.832 | 12 | stable positive |
| qwen35_9b | e31_geometry_diameter_bad310020_valid310019 | zh | bad_B | 0.750 | 0.156 | 23 | stable positive |
| qwen35_9b | e31_inequality_boundary_bad310008_valid310007 | en | bad_A | -0.375 | 3.527 | 22 | mid-signal lost before output |
| qwen35_9b | e31_inequality_boundary_bad310008_valid310007 | en | bad_B | 0.750 | -0.844 | 23 | late-only positive |
| qwen35_9b | e31_inequality_boundary_bad310008_valid310007 | zh | bad_A | 0.125 | 2.539 | 12 | stable positive |
| qwen35_9b | e31_inequality_boundary_bad310008_valid310007 | zh | bad_B | 0.125 | -0.312 | 19 | late-only positive |
| qwen35_9b | e31_ratio_boys_girls_bad310002_valid310001 | en | bad_A | 0.250 | 4.301 | 17 | stable positive |
| qwen35_9b | e31_ratio_boys_girls_bad310002_valid310001 | en | bad_B | 3.000 | 2.969 | 23 | stable positive |
| qwen35_9b | e31_ratio_boys_girls_bad310002_valid310001 | zh | bad_A | 0.625 | 2.734 | 20 | stable positive |
| qwen35_9b | e31_ratio_boys_girls_bad310002_valid310001 | zh | bad_B | 0.750 | 0.406 | 23 | stable positive |
| qwen35_9b | e31_unit_dozen_pairs_bad310014_valid310013 | en | bad_A | -0.375 | 4.000 | 22 | mid-signal lost before output |
| qwen35_9b | e31_unit_dozen_pairs_bad310014_valid310013 | en | bad_B | 1.500 | 0.375 | 23 | stable positive |
| qwen35_9b | e31_unit_dozen_pairs_bad310014_valid310013 | zh | bad_A | 0.750 | 2.653 | 22 | stable positive |
| qwen35_9b | e31_unit_dozen_pairs_bad310014_valid310013 | zh | bad_B | 0.250 | -0.219 | 19 | late-only positive |
| qwen3_14b_base | e31_comb_unordered_bad310026_valid310025 | en | bad_A | -0.156 | 3.031 | 29 | mid-signal lost before output |
| qwen3_14b_base | e31_comb_unordered_bad310026_valid310025 | en | bad_B | 3.156 | 3.188 | 29 | stable positive |
| qwen3_14b_base | e31_comb_unordered_bad310026_valid310025 | zh | bad_A | 1.938 | 2.344 | 29 | stable positive |
| qwen3_14b_base | e31_comb_unordered_bad310026_valid310025 | zh | bad_B | 1.000 | 3.938 | 29 | stable positive |
| qwen3_14b_base | e31_geometry_diameter_bad310020_valid310019 | en | bad_A | -1.125 | 2.375 | 29 | mid-signal lost before output |
| qwen3_14b_base | e31_geometry_diameter_bad310020_valid310019 | en | bad_B | 2.312 | 1.766 | 10 | stable positive |
| qwen3_14b_base | e31_geometry_diameter_bad310020_valid310019 | zh | bad_A | 1.500 | 2.594 | 29 | stable positive |
| qwen3_14b_base | e31_geometry_diameter_bad310020_valid310019 | zh | bad_B | 0.750 | 2.500 | 29 | stable positive |
| qwen3_14b_base | e31_inequality_boundary_bad310008_valid310007 | en | bad_A | -2.156 | 1.789 | 27 | mid-signal lost before output |
| qwen3_14b_base | e31_inequality_boundary_bad310008_valid310007 | en | bad_B | 2.125 | 1.500 | 10 | stable positive |
| qwen3_14b_base | e31_inequality_boundary_bad310008_valid310007 | zh | bad_A | -0.188 | 1.434 | 27 | mid-signal lost before output |
| qwen3_14b_base | e31_inequality_boundary_bad310008_valid310007 | zh | bad_B | -0.062 | 1.018 | 10 | mid-signal lost before output |
| qwen3_14b_base | e31_ratio_boys_girls_bad310002_valid310001 | en | bad_A | -0.688 | 2.969 | 29 | mid-signal lost before output |
| qwen3_14b_base | e31_ratio_boys_girls_bad310002_valid310001 | en | bad_B | 3.031 | 2.094 | 29 | stable positive |
| qwen3_14b_base | e31_ratio_boys_girls_bad310002_valid310001 | zh | bad_A | 1.688 | 2.859 | 29 | stable positive |
| qwen3_14b_base | e31_ratio_boys_girls_bad310002_valid310001 | zh | bad_B | 0.875 | 2.969 | 29 | stable positive |
| qwen3_14b_base | e31_unit_dozen_pairs_bad310014_valid310013 | en | bad_A | -0.656 | 3.469 | 29 | mid-signal lost before output |
| qwen3_14b_base | e31_unit_dozen_pairs_bad310014_valid310013 | en | bad_B | 2.781 | 2.062 | 10 | stable positive |
| qwen3_14b_base | e31_unit_dozen_pairs_bad310014_valid310013 | zh | bad_A | 1.688 | 3.562 | 29 | stable positive |
| qwen3_14b_base | e31_unit_dozen_pairs_bad310014_valid310013 | zh | bad_B | 0.625 | 2.219 | 29 | stable positive |
