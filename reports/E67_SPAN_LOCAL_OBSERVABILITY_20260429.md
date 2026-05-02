# E67 Span-Local Observability / E67 span-local 可观测性审计（2026-04-29）

- Result / 结果：`results/E67_span_local_observability/e67_span_local_observability.json`
- Audit / 审计：`reports/E67_SPAN_LOCAL_OBSERVABILITY_AUDIT_20260429.json`
- Plain language / 说人话：我们没有把错误 span 告诉模型；这里只是在事后看，人工记录的错误短语能不能在多语言 trace 里按字符串找到，以及这种“表层可见性”是否影响 verifier 失败和 hidden probe。

## Literal Span Presence / 字面 span 是否出现

| literal error_span found | n invalid traces |
|---|---:|
| `False` | 39 |
| `True` | 9 |

## Plain Pointwise Acceptance by Span Observability / 按 span 可观测性划分的普通单点接受

| literal found | n model-rows | mean plain ACPI accept |
|---|---:|---:|
| `False` | 156 | 0.404 |
| `True` | 36 | 0.583 |

## Hidden Probe Rejection by Span Observability / 按 span 可观测性划分的 hidden probe 拒绝

| literal found | n model-rows | mean hidden rejects ACPI |
|---|---:|---:|
| `False` | 156 | 1.000 |
| `True` | 36 | 0.972 |

## Route Slices / 语言路径切片

| route | verifier rows | mean plain ACPI accept | hidden rows | mean hidden rejects ACPI |
|---|---:|---:|---:|---:|
| `en_en` | 32 | 0.406 | 32 | 1.000 |
| `en_zh` | 32 | 0.406 | 32 | 1.000 |
| `mixed` | 32 | 0.469 | 32 | 1.000 |
| `romanized_zh` | 32 | 0.594 | 32 | 1.000 |
| `zh_en` | 32 | 0.406 | 32 | 0.969 |
| `zh_zh` | 32 | 0.344 | 32 | 1.000 |

## Interpretation / 解释

- Surface span matching is brittle / 表层 span 匹配很脆：E61 的错误 span 以规范英文记录，到了中文、混合语和拼音路线时常常不能字面匹配。这说明真正的错误定位不能依赖简单字符串匹配。 / Literal string matching is brittle across multilingual routes.
- Hidden states generalize beyond literal spans / hidden state 超出字面 span：即便错误短语不能字面找到，E65 best-layer probe 仍能高比例拒绝 strict ACPI，说明过程证据不是简单抄录英文错误短语。 / Best-layer probes still reject many strict ACPI rows even without literal span matches.
- Boundary / 边界：E67 不是 span patch causal proof；它给 E67/E65 之后的下一步指向 token-level patching、translated-span alignment、以及 route-specific localization。 / E67 is not causal span patching; it motivates token-level patching and translated-span alignment.

## Audit / 审计

- PASS: E61 span metadata rows — 48
- PASS: qwen35_27b E61 result exists — results/E61_language_error_grid/qwen35_27b_e61_language_error_grid_chat.json
- PASS: gemma4_31b_it E61 result exists — results/E61_language_error_grid/gemma4_31b_it_e61_language_error_grid_chat.json
- PASS: gemma4_26b_a4b_it E61 result exists — results/E61_language_error_grid/gemma4_26b_a4b_it_e61_language_error_grid_chat.json
- PASS: glm47_flash_candidate E61 result exists — results/E61_language_error_grid/glm47_flash_candidate_e61_language_error_grid_chat.json
- PASS: qwen35_27b E65 result exists — results/E65_mechanistic_layer_sweep/qwen35_27b_e65_e61_layer_sweep.json
- PASS: gemma4_31b_it E65 result exists — results/E65_mechanistic_layer_sweep/gemma4_31b_it_e65_e61_layer_sweep.json
- PASS: gemma4_26b_a4b_it E65 result exists — results/E65_mechanistic_layer_sweep/gemma4_26b_a4b_it_e65_e61_layer_sweep.json
- PASS: glm47_flash_candidate E65 result exists — results/E65_mechanistic_layer_sweep/glm47_flash_candidate_e65_e61_layer_sweep.json
