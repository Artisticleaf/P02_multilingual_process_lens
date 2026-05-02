# E30 Non-Discount Lexical Grid Audit / E30 非折扣词汇网格审计

Created / 创建时间: 2026-04-27T19:43:36

Scope / 范围: 4 generator models, 24 non-discount lexical tasks, 2 routes (`zh->zh`, `zh->en`), k=2. Total 384 rows. / 4 个生成模型、24 个非折扣词汇任务、2 条 route、每格 2 条样本，总计 384 行。

## Model-Level Summary / 模型级汇总

| model | n | parseable final | final correct | format-valid usable | process invalid | ACPI | paper-grade ACPI | semantic drift final-wrong | route violations among usable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gemma4_e4b_it | 96 | 96 | 92 | 96 | 4 | 0 | 0 | 4 | 8 |
| phi4_mini_reasoning | 96 | 8 | 5 | 0 | 3 | 0 | 0 | 0 | 0 |
| qwen25_math_7b_instruct | 96 | 91 | 89 | 0 | 2 | 0 | 0 | 1 | 0 |
| qwen3_14b_base | 96 | 92 | 91 | 92 | 2 | 1 | 1 | 0 | 23 |

## Human-Readable Findings / 人话发现

- E30 broadened beyond discount into ratio, inequality, interval, average/total, geometry, unit, combinatorics, and operator-word tasks. / E30 从折扣扩展到比例、量词、区间、平均/总量、几何、单位、组合和算子词任务。
- In this first natural-generation pass, clean non-discount ACPI was rare: one paper-grade Qwen14 inequality row was promoted. / 第一轮自然生成中，干净非折扣 ACPI 很少：目前只提升 1 条论文级 Qwen14 不等式样例。
- The strongest non-discount natural drift was unit semantics: Gemma4 repeatedly treated 3 dozen individual socks as 36 pairs instead of 18 pairs, but those rows were final-wrong rather than ACPI. / 最强非折扣自然漂移来自单位语义：Gemma4 多次把 3 打袜子当成 36 双而不是 18 双，但这些是答案错误，不是 ACPI。
- Phi4 and Qwen2.5-Math often produced hidden-think or non-`Final answer` formats, so they are boundary/control generators in this pass. / Phi4 与 Qwen2.5-Math 常输出 hidden-think 或非 `Final answer` 格式，本轮更适合作为边界/控制生成器。

## Paper-Grade ACPI Rows / 论文级 ACPI 行

| audit idx | model | task | route | sample | final | earliest error | why it matters |
|---:|---|---|---|---:|---|---|---|
| 300311 | qwen3_14b_base | inequality_no_more_than | zh->en | 1 | 4. | between 3 and 7, inclusive | The original condition is greater than 3 and no more than 7, so 3 is excluded. Saying between 3 and 7 inclusive would include 3, even though the trace then lists 4,5,6,7 and gives the correct final count. |

## Semantic-Drift Final-Wrong Rows / 语义漂移但答案错误行

| audit idx | model | task | route | sample | gold | final | drift |
|---:|---|---|---|---:|---|---|---|
| 300060 | gemma4_e4b_it | unit_dozen_pairs | zh->zh | 0 | 18 | 36 | treats 36 individual socks as 36 pairs after correctly computing 3 dozen = 36 socks |
| 300061 | gemma4_e4b_it | unit_dozen_pairs | zh->zh | 1 | 18 | 36 | treats 3 dozen socks as 36 pairs instead of 36 individual socks = 18 pairs |
| 300062 | gemma4_e4b_it | unit_dozen_pairs | zh->en | 0 | 18 | 36 | treats 3 dozen socks as 36 pairs instead of 36 individual socks = 18 pairs |
| 300063 | gemma4_e4b_it | unit_dozen_pairs | zh->en | 1 | 18 | 36 | treats 3 dozen socks as 36 pairs instead of 36 individual socks = 18 pairs |
| 300252 | qwen25_math_7b_instruct | unit_dozen_pairs | zh->zh | 0 | 18 | 36 | states one dozen socks equals 12 pairs, causing 36 pairs instead of 18 pairs |

## Task-Level Signal / 任务级信号

| task | n | final correct | ACPI | semantic drift final-wrong | major risk counts |
|---|---:|---:|---:|---:|---|
| algebra_coefficient | 16 | 12 | 0 | 0 | valid_clean:6; format_boundary_hidden_think_no_final_marker:4; valid_process_but_format_noncompliant:4 |
| algebra_exponent | 16 | 12 | 0 | 0 | valid_clean:6; format_boundary_hidden_think_no_final_marker:4; valid_process_but_format_noncompliant:4 |
| average_each_extra | 16 | 12 | 0 | 0 | valid_clean:6; format_boundary_hidden_think_no_final_marker:4; valid_process_but_format_noncompliant:4 |
| average_total_to_average | 16 | 13 | 0 | 0 | valid_clean:6; valid_process_but_format_noncompliant:5; format_boundary_hidden_think_no_final_marker:3 |
| calculus_derivative_at_point | 16 | 11 | 0 | 0 | final_correct_process_valid_but_route_violation:4; valid_clean:4; format_boundary_hidden_think_no_final_marker:4 |
| comb_assign_ordered | 16 | 12 | 0 | 0 | valid_clean:7; format_boundary_hidden_think_no_final_marker:4; valid_process_but_format_noncompliant:4 |
| comb_choose_unordered | 16 | 8 | 0 | 0 | valid_clean:4; no_parseable_final_answer:4; final_correct_process_valid_but_route_violation:3 |
| comb_with_replacement | 16 | 12 | 0 | 0 | valid_clean:8; format_boundary_hidden_think_no_final_marker:4; valid_process_but_format_noncompliant:4 |
| geometry_diameter_area | 16 | 13 | 0 | 0 | valid_clean:6; valid_process_but_format_noncompliant:5; format_boundary_hidden_think_no_final_marker:3 |
| geometry_radius_area | 16 | 12 | 0 | 0 | valid_clean:7; valid_process_but_format_noncompliant:4; format_boundary_hidden_think_no_final_marker:3 |
| geometry_reflection_line | 16 | 11 | 0 | 0 | valid_clean:6; format_boundary_hidden_think_no_final_marker:4; final_correct_process_valid_but_route_violation:3 |
| inequality_at_least | 16 | 12 | 0 | 0 | valid_clean:6; format_boundary_hidden_think_no_final_marker:4; valid_process_but_format_noncompliant:4 |
| inequality_more_than | 16 | 11 | 0 | 0 | valid_clean:5; format_boundary_hidden_think_no_final_marker:4; valid_process_but_format_noncompliant:4 |
| inequality_no_more_than | 16 | 12 | 1 | 0 | valid_clean:7; format_boundary_hidden_think_no_final_marker:4; valid_process_but_format_noncompliant:4 |
| interval_between_exclusive | 16 | 12 | 0 | 0 | valid_clean:7; format_boundary_hidden_think_no_final_marker:4; valid_process_but_format_noncompliant:4 |
| interval_closed_open | 16 | 11 | 0 | 0 | valid_clean:6; valid_process_but_format_noncompliant:4; format_boundary_hidden_think_no_final_marker:3 |
| interval_open_closed | 16 | 12 | 0 | 0 | valid_clean:8; format_boundary_hidden_think_no_final_marker:4; valid_process_but_format_noncompliant:4 |
| ratio_boys_girls_2_3 | 16 | 11 | 0 | 0 | valid_clean:8; format_boundary_hidden_think_no_final_marker:4; valid_process_but_format_noncompliant:3 |
| ratio_boys_girls_same_answer | 16 | 12 | 0 | 0 | valid_clean:8; format_boundary_hidden_think_no_final_marker:4; valid_process_but_format_noncompliant:4 |
| ratio_boys_total_2_3 | 16 | 12 | 0 | 0 | valid_clean:7; format_boundary_hidden_think_no_final_marker:4; valid_process_but_format_noncompliant:4 |
| total_each_extra | 16 | 13 | 0 | 0 | valid_clean:8; valid_process_but_format_noncompliant:4; format_boundary_hidden_think_no_final_marker:3 |
| unit_dozen_pairs | 16 | 6 | 0 | 5 | semantic_drift_final_wrong:5; format_boundary_hidden_think_no_final_marker:3; valid_clean:3 |
| unit_million_yi | 16 | 12 | 0 | 0 | valid_clean:7; format_boundary_hidden_think_no_final_marker:4; valid_process_but_format_noncompliant:4 |
| unit_pairs_socks | 16 | 13 | 0 | 0 | valid_clean:6; valid_process_but_format_noncompliant:4; format_boundary_hidden_think_no_final_marker:3 |

## Interpretation / 解释

E30 is important because it weakens a potential overclaim: the non-discount families did not automatically reproduce the same ACPI density as discount/pay-off wording. / E30 很重要，因为它削弱了一个潜在过度主张：非折扣族没有自动复现折扣/pay-off 那样高的 ACPI 密度。

The result does not kill the main claim. It refines it: natural ACPI is most visible when a local lexical phrase has two common but conflicting operational meanings and the final arithmetic can remain numerically unchanged. / 这个结果不否定主张，而是细化主张：自然 ACPI 最容易出现在局部词汇有两个常见但冲突的操作含义、且最终算术数字仍可保持不变的场景。

Next step: build controlled non-discount counterfactual siblings for the strongest families, especially unit words (`dozen`/pairs), inequality boundary paraphrases, ratio denominator wording, and operator words. / 下一步应为最强非折扣族构造受控反事实 sibling，尤其是单位词、边界量词、比例分母措辞和算子词。
