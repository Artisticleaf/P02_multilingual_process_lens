# E153 Error-Finding Audit / E153 找错审计

Scope / 范围：completed E153 non-thinking error-finding files. This report separates first-`ERROR` parsing from last-`ERROR` parsing because some outputs naturally revise their own judgment.

Definitions / 定义：
- `first_pred_correct`: online runner metric; it uses the first `ERROR:` line.
- `last_pred_correct`: post-hoc behavioral metric; it uses the last `ERROR:` line, useful when the model says one decision and then revises it.
- `invalid_location_match_last`: for invalid reference traces, whether the last reported location overlaps the offline human error span.
- `valid_false_positive_last`: for valid reference traces, whether the model still claims an error at the end.

Model summary / 模型摘要：

| model | rows | first correct | last correct | flips | valid false+ first | valid false+ last | invalid false- first | invalid false- last | invalid loc match last |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gemma4_26b_a4b_it | 128 | 113 | 113 | 0 | 0 | 0 | 13 | 13 | 56/64 |
| gemma4_31b_it | 128 | 121 | 121 | 0 | 2 | 2 | 3 | 3 | 58/64 |
| qwen35_27b | 128 | 117 | 118 | 1 | 10 | 9 | 1 | 1 | 61/64 |

Key interpretation / 关键解释：
- Binary error detection and exact localization must be reported separately. A model can say `ERROR: Yes` while pointing to the wrong step.
- First-vs-last differences are scientifically meaningful here: they expose non-thinking self-correction or judgment instability.
- Valid-reference false positives are not noise to discard; they measure over-suspicion and can become control cases for hidden-trigger policies.

Selected cases / 代表样本：
## judgment_flips
- qwen35_27b e153_code_boundary_02 find_problem_global valid_reference: manual_error=False, first=True, last=False, loc=`NONE`; excerpt: ERROR: Yes | LOCATION: "The terms are 0,-3,-4,-3,0" | REASON: The calculation for i=1 is incorrect because 1 * (1 - 4) equals -3, but the term for i=2 is 2 * (2 - 4) = -4, and the term for i=3 is 3 * (3 - 4) = -3, which matches the list, however the term for i=1 is actually -3, so the list 0, -3, -4, -3, 0 is actually correct for i=0,1,2,3,4? Let me re-calcu...
## valid_false_positive_last
- gemma4_31b_it e153_graph_path_constraints_02 find_problem_global valid_reference: manual_error=False, first=True, last=True, loc=`"A connected graph with exactly two odd-degree vertices has an Euler trail."`; excerpt: The proposed solution correctly identifies that a connected graph with exactly two odd-degree vertices has an Euler trail. However, it fails to verify if a graph with the given degree sequence (1, 1, 2, 2, 2) is necessarily connected. In this specific case, the sum of degrees is 8, and the number of vertices is 5. A graph with these degrees must be connected...
- gemma4_31b_it e153_graph_path_constraints_02 find_problem_localize_only valid_reference: manual_error=False, first=True, last=True, loc=`A connected graph with exactly two odd-degree vertices has an Euler trail.`; excerpt: The proposed solution assumes the graph is connected without verifying if a graph with degrees 1, 1, 2, 2, 2 must be connected. However, a graph with these degrees could be disconnected (e.g., a path of 2 vertices and a cycle of 3 vertices), in which case it would not have an Euler trail. |  | ERROR: Yes | LOCATION: A connected graph with exactly two odd-deg...
- qwen35_27b e153_algebra_sign_factor_01 find_problem_global valid_reference: manual_error=False, first=True, last=True, loc=`"Factor 12x^2 - xy - 6y^2 as (3x+2y)(4x-3y)"`; excerpt: ERROR: Yes | LOCATION: "Factor 12x^2 - xy - 6y^2 as (3x+2y)(4x-3y)" | REASON: The proposed factorization is incorrect because expanding (3x+2y)(4x-3y) yields 12x^2 - xy - 6y^2, which matches the original equation, but the subsequent derivation of y = -3x/2 and y = 4x/3 from these factors is algebraically wrong; the correct roots are y = -3x/2 and y = 4x/3 on...
- qwen35_27b e153_algebra_sign_factor_01 find_problem_localize_only valid_reference: manual_error=False, first=True, last=True, loc=`"Factor 12x^2 - xy - 6y^2 as (3x+2y)(4x-3y)"`; excerpt: ERROR: Yes | LOCATION: "Factor 12x^2 - xy - 6y^2 as (3x+2y)(4x-3y)"
- qwen35_27b e153_code_boundary_01 find_problem_localize_only valid_reference: manual_error=False, first=True, last=True, loc=`"The terms are -6,-10,-12,-12,-10,-6,0"`; excerpt: ERROR: Yes | LOCATION: "The terms are -6,-10,-12,-12,-10,-6,0"
- qwen35_27b e153_code_boundary_02 find_problem_localize_only valid_reference: manual_error=False, first=True, last=True, loc=`"The terms are 0,-3,-4,-3,0"`; excerpt: ERROR: Yes | LOCATION: "The terms are 0,-3,-4,-3,0"
- qwen35_27b e153_counting_invariant_01 find_problem_localize_only valid_reference: manual_error=False, first=True, last=True, loc=`"For x+y=5 there are 36 choices of x in [-15,20]"`; excerpt: ERROR: Yes | LOCATION: "For x+y=5 there are 36 choices of x in [-15,20]"
- qwen35_27b e153_counting_invariant_02 find_problem_localize_only valid_reference: manual_error=False, first=True, last=True, loc=`"no subset has sum 7.5"`; excerpt: ERROR: Yes | LOCATION: "no subset has sum 7.5"
## invalid_false_negative_last
- gemma4_26b_a4b_it e153_algebra_sign_factor_01 find_problem_localize_only invalid_reference: manual_error=True, first=False, last=False, loc=`Thus y=3x/2 or y=-4x/3`; excerpt: ERROR: No | LOCATION: Thus y=3x/2 or y=-4x/3
- gemma4_26b_a4b_it e153_counting_invariant_02 find_problem_localize_only invalid_reference: manual_error=True, first=False, last=False, loc=`subsets with sum less than half are the desired subsets`; excerpt: ERROR: No | LOCATION: subsets with sum less than half are the desired subsets
- gemma4_26b_a4b_it e153_geometry_constraints_01 find_problem_global invalid_reference: manual_error=True, first=False, last=False, loc=`NONE`; excerpt: The proposed solution uses a property that is true for tangential quadrilaterals (the sum of opposite sides are equal), but it incorrectly applies it to the individual leg. In a tangential trapezoid, the sum of the bases equals the sum of the legs ($a + b = c + d$). Since it is an isosceles trapezoid, the two legs are equal ($c = d$), so $a + b = 2c$, which ...
- gemma4_26b_a4b_it e153_geometry_constraints_02 find_problem_global invalid_reference: manual_error=True, first=False, last=False, loc=`NONE`; excerpt: The proposed solution is correct. A point reflection through the origin $(0,0)$ maps a point $(x, y)$ to $(-x, -y)$. For the point $(2,3)$, this results in $(-2,-3)$. |  | ERROR: No | LOCATION: NONE | REASON: The reasoning and the final answer are correct.
- gemma4_26b_a4b_it e153_geometry_constraints_02 find_problem_localize_only invalid_reference: manual_error=True, first=False, last=False, loc=`NONE`; excerpt: ERROR: No | LOCATION: NONE
- gemma4_26b_a4b_it e153_graph_path_constraints_02 find_problem_localize_only invalid_reference: manual_error=True, first=False, last=False, loc=`All vertices must have even degree for an Euler trail`; excerpt: ERROR: No | LOCATION: All vertices must have even degree for an Euler trail
- gemma4_26b_a4b_it e153_probability_conditioning_01 find_problem_localize_only invalid_reference: manual_error=True, first=False, last=False, loc=`so a positive means the condition is more likely than not`; excerpt: ERROR: No | LOCATION: so a positive means the condition is more likely than not
- gemma4_26b_a4b_it e153_recurrence_dp_02 find_problem_localize_only invalid_reference: manual_error=True, first=False, last=False, loc=`f(n)=2f(n-1)-f(n-2)`; excerpt: ERROR: No | LOCATION: f(n)=2f(n-1)-f(n-2)
## invalid_location_miss_last
- gemma4_26b_a4b_it e153_algebra_sign_factor_02 find_problem_localize_only invalid_reference: manual_error=True, first=True, last=True, loc=`The roots are x=-6 and x=4`; excerpt: ERROR: Yes | LOCATION: The roots are x=-6 and x=4
- gemma4_26b_a4b_it e153_unit_percentage_01 find_problem_localize_only invalid_reference: manual_error=True, first=True, last=True, loc=`Increasing by 25 adds 20`; excerpt: ERROR: Yes | LOCATION: Increasing by 25 adds 20
- gemma4_31b_it e153_algebra_sign_factor_02 find_problem_global invalid_reference: manual_error=True, first=True, last=True, loc=`The roots are x=-6 and x=4`; excerpt: The proposed solution contains several errors. First, the roots of $(x-6)(x+4)=0$ are $x=6$ and $x=-4$, not $x=-6$ and $x=4$. Second, the problem asks for the sum of the integers, not the magnitude of the sum. |  | ERROR: Yes | LOCATION: The roots are x=-6 and x=4 | REASON: The roots of (x-6)(x+4)=0 are x=6 and x=-4.
- gemma4_31b_it e153_algebra_sign_factor_02 find_problem_localize_only invalid_reference: manual_error=True, first=True, last=True, loc=`The roots are x=-6 and x=4`; excerpt: The first questionable reasoning step occurs when the roots of the equation $(x-6)(x+4)=0$ are identified. The roots are $x=6$ and $x=-4$, but the solution states they are $x=-6$ and $x=4$. |  | ERROR: Yes | LOCATION: The roots are x=-6 and x=4
- qwen35_27b e153_algebra_sign_factor_01 find_problem_global invalid_reference: manual_error=True, first=True, last=True, loc=`"Counting integer pairs in the symmetric box gives 117"`; excerpt: ERROR: Yes | LOCATION: "Counting integer pairs in the symmetric box gives 117" | REASON: The correct count is 101, derived from 51 pairs for $y=3x/2$ (where $x$ is even) and 51 pairs for $y=-4x/3$ (where $x$ is a multiple of 3), minus 1 for the double-counted origin $(0,0)$.
- qwen35_27b e153_algebra_sign_factor_01 find_problem_localize_only invalid_reference: manual_error=True, first=True, last=True, loc=`"Counting integer pairs in the symmetric box gives 117."`; excerpt: ERROR: Yes | LOCATION: "Counting integer pairs in the symmetric box gives 117."

Artifacts / 产物：`data/processed/e153_error_finding_audit_20260501.jsonl`, `results/E153_nonthinking_error_finding/e153_error_finding_audit_summary_20260501.json`.
