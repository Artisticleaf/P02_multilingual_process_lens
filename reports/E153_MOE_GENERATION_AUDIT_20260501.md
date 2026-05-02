# E153 MoE Generation Audit / E153 MoE 解题生成审计

Scope / 范围：Gemma4-26B-A4B-it 的 E153 non-thinking generation。该模型是 MoE，单独报告，不并入 dense 统计。

Key result / 关键结果：

| model | rows | auto final correct | manual final correct | ambiguous boundary | clean valid prefill candidates | language-trait traces | unrepaired ACPI |
|---|---:|---:|---:|---:|---:|---:|---:|
| gemma4_26b_a4b_it | 96 | 89 | 95 | 1 | 95 | 15 | 0 |

Findings / 发现：
- Automatic false negatives are mostly answer-normalization issues: quoted string `'bcd'` and unit answers such as `120 meters` are semantically correct.
- The only non-normalization disagreement is `e153_graph_path_constraints_02` under `solve_neutral`: the model answers `No` because the prompt does not state connectivity. A disconnected graph with a triangle and a separate edge has degrees `1,1,2,2,2` but no Euler trail over all edges. This is an ambiguous prompt-boundary case, not a clean wrong-answer failure.
- No unrepaired ACPI was found in MoE generation. The MoE output is therefore consistent with dense generation on the main point: natural reasoning-first unrepaired ACPI did not appear in this E153 generation setting.
- The MoE-specific value is boundary sensitivity and potential routing stability analysis, not current evidence of broad natural unrepaired ACPI prevalence.

Use / 用法：
- Use clean valid rows as mutation/prefill seeds only after excluding ambiguous graph-boundary rows.
- Keep the graph-boundary row as a language/definition-boundary case card.
- Do not pool this MoE statistic with dense models without an explicit architecture slice.

Artifacts / 产物：`data/processed/e153_moe_generation_audit_20260501.jsonl`, `results/E153_nonthinking_difficult_scenario_generation/e153_moe_generation_audit_summary_20260501.json`.
