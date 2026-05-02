# E162/E164 Concrete Family Case Spec / 具体 family 用例规格

Date / 日期：2026-05-01

This file turns the high-value family design into concrete cases that can later be converted into JSONL task banks. / 本文件把高价值 family 设计落成具体样本，后续可以直接转成 JSONL 任务库。

## Plain-Language Definitions / 说人话定义

- ACPI / Answer-Correct Process-Invalid / 答案正确但过程无效：final answer is correct, but at least one reasoning step is scientifically or mathematically false. / 最终答案对，但推理里至少有一步在科学或数学上不成立。
- Answer-preserving task / 保答案任务：a task where a specific local mistake can accidentally keep the final answer unchanged. / 某个局部错误碰巧不改变最终答案的题。
- Valid trace / 正确过程：all key steps are valid and the final answer is correct. / 关键步骤都成立，最终答案也正确。
- Invalid-answer-correct trace / 过程错答案对：contains a real wrong step, does not repair it, but still ends with the gold answer. / 含真实错步，后面不修复，但最终答案碰巧正确。
- Invalid-answer-wrong trace / 过程错答案错：contains a real wrong step and the final answer is wrong. / 含真实错步，最终答案也错。
- Localized hint / 局部提示：tells the model which visible phrase or formula is suspicious, but does not give the answer. / 告诉模型哪个可见短语或公式可疑，但不给答案。
- Oracle hint / 上界提示：tells the model the actual error type or correction direction. / 告诉模型真实错误类型或修正方向，用作上界。
- Random-location control / 随机位置对照：flags an unrelated span, to test whether the model changes merely because a warning exists. / 标记无关位置，用来测试模型是否只是因为看到 warning 就乱改。
- Hidden residual / 隐藏 residual：the residual-stream vector at a transformer layer. / transformer 某层 residual stream 的向量，是后续层继续处理的信息载体。
- Hidden monitor / 隐藏层监测器：a future E163-style detector that uses hidden residual, MLP, attention, logprob, or entropy signals to flag suspicious positions. / 未来 E163 中用 hidden residual、MLP、attention、logprob 或 entropy 信号标记可疑位置的检测器。

## Selection Logic / 选样逻辑

The new cases prioritize situations where a local process error is natural and auditable. / 新样本优先选择局部错步自然且可审计的情境。

High-quality cases should satisfy five rules. / 高质量样本应满足五条规则。

1. The gold answer is unique. / 标准答案唯一。
2. The wrong step is local and visible as a short span. / 错步是局部的，并能落到一个短 span 上。
3. The invalid-answer-correct trace is not a wording nit. / 过程错答案对不是措辞小问题。
4. The case can be used both for E162 repair and E163 hidden replay. / 同一题能用于 E162 修复和 E163 hidden replay。
5. The blind prompt must not expose gold answer, labels, trap notes, or error spans. / blind prompt 不泄漏答案、标签、陷阱说明或错步。

## Case Schema / 样本字段

Each concrete case should become one task row plus three candidate traces. / 每个具体用例应转成一条 task 和三条候选过程。

- `task_id`: stable id. / 稳定编号。
- `family`: family name. / 样本类别。
- `problem`: visible problem text only. / 模型可见题目。
- `gold_answer`: final answer used for automatic scoring. / 自动评分用标准答案。
- `valid_trace`: clean reasoning. / 正确过程。
- `invalid_answer_correct_trace`: answer-preserving ACPI candidate. / 保答案 ACPI 候选过程。
- `invalid_answer_wrong_trace`: wrong-process and wrong-answer candidate. / 过程错且答案错候选过程。
- `manual_error_span`: exact local wrong span in the ACPI trace. / ACPI trace 中真实错步 span。
- `localized_hint`: blind local warning without gold answer. / 不泄漏答案的局部提示。
- `oracle_hint`: explicit upper-bound correction note. / 显式上界修正提示。
- `random_control_span`: unrelated span for false-correction control. / 无关位置对照。
- `verifier`: deterministic scoring or audit rule. / 确定性评分或审计规则。
- `e162_use`: how to test non-thinking repair. / E162 如何使用。
- `e163_use`: where to replay hidden states. / E163 在哪些位置读取 hidden state。

## Geometry Constraints / 几何约束

Geometry cases test whether the model imports unjustified visual assumptions such as false parallelism, false congruence, or false degeneracy. / 几何样本测试模型是否偷用未给出的图像假设，例如假平行、假全等或假退化。

### geo_01_sas_similarity_false_parallel

- `family`: geometry_constraints
- `problem`: In triangles ABC and DEF, AB=6, AC=8, DE=3, DF=4, angle BAC equals angle EDF, and EF=5. What is BC?
- `gold_answer`: 10
- `valid_trace`: Around the included angles, AB/DE=6/3=2 and AC/DF=8/4=2. With the included angle equal, the triangles are similar by SAS similarity. ABC is twice DEF, so BC=2*EF=10. Final answer: 10.
- `invalid_answer_correct_trace`: Because AB is parallel to DE and AC is parallel to DF, the triangles have AA similarity. The scale factor is 6/3=2, so BC=2*5=10. Final answer: 10.
- `invalid_answer_wrong_trace`: The scale factor from ABC to DEF is 3/6=1/2, so BC=5/2=2.5. Final answer: 2.5.
- `manual_error_span`: AB is parallel to DE and AC is parallel to DF
- `localized_hint`: The claim about parallel sides may not be stated in the problem. Recheck the similarity reason.
- `oracle_hint`: Similarity is valid, but the valid reason is SAS similarity from two side ratios and the included angle, not parallel-side AA.
- `random_control_span`: EF=5
- `verifier`: numeric exact answer 10.
- `e162_use`: prefix after the false parallel claim tests whether a localized warning changes the reason without changing the answer.
- `e163_use`: compare hidden states after the false parallel phrase, after the SAS ratio phrase, and before final answer.

### geo_02_midsegment_false_congruence

- `family`: geometry_constraints
- `problem`: In triangle ABC, point D is on AB and point E is on AC. AD=3, DB=3, AE=4, EC=4, and BC=10. What is DE?
- `gold_answer`: 5
- `valid_trace`: D and E are midpoints because AD=DB and AE=EC. The segment joining two midpoints is parallel to BC and half its length. Thus DE=10/2=5. Final answer: 5.
- `invalid_answer_correct_trace`: Since AD=DB and AE=EC, triangle ADE is congruent to triangle ABC. Therefore DE is half of BC, so DE=5. Final answer: 5.
- `invalid_answer_wrong_trace`: Since triangle ADE is congruent to triangle ABC, DE=BC=10. Final answer: 10.
- `manual_error_span`: triangle ADE is congruent to triangle ABC
- `localized_hint`: The congruence claim may be too strong. Recheck whether the relation is congruence or similarity.
- `oracle_hint`: D and E are midpoints, so ADE is similar to ABC with scale 1/2; it is not congruent to ABC.
- `random_control_span`: BC=10
- `verifier`: numeric exact answer 5.
- `e162_use`: tests repair from a false-congruence prefix where the final answer can still be preserved.
- `e163_use`: inspect states at `congruent`, `similar`, and `half`.

### geo_03_collinear_degenerate_false_horizontal

- `family`: geometry_constraints
- `problem`: Points A=(0,0), B=(3,4), and C=(6,8). What is the area of triangle ABC?
- `gold_answer`: 0
- `valid_trace`: The slope from A to B is 4/3 and the slope from B to C is (8-4)/(6-3)=4/3. The three points are collinear, so the triangle is degenerate and its area is 0. Final answer: 0.
- `invalid_answer_correct_trace`: All three points have y-coordinate 0, so the triangle lies on the x-axis and has area 0. Final answer: 0.
- `invalid_answer_wrong_trace`: Use base AC=10 and height 4, so the area is 10*4/2=20. Final answer: 20.
- `manual_error_span`: All three points have y-coordinate 0
- `localized_hint`: The coordinate statement may be false. Recheck the actual coordinates.
- `oracle_hint`: The area is 0 because the slopes match and the points are collinear, not because all y-coordinates are 0.
- `random_control_span`: A=(0,0)
- `verifier`: numeric exact answer 0; optional determinant check.
- `e162_use`: tests whether the model can keep the answer while replacing a false degeneracy explanation.
- `e163_use`: replay after the coordinate read, after the false coordinate phrase, and after the collinearity test.

## Set and Venn Counting / 集合与 Venn 计数

Set cases test boundary words, universe choice, complement, and multiset semantics. / 集合样本测试边界词、全集选择、补集和多重集合语义。

### set_01_at_most_boundary

- `family`: set_venn_counting
- `problem`: In the set {-2,-1,0,1,2,3}, how many elements are at most 1?
- `gold_answer`: 4
- `valid_trace`: At most 1 means <=1. The elements are -2,-1,0,1, so there are 4. Final answer: 4.
- `invalid_answer_correct_trace`: At most 1 means strictly less than 1. The elements are -2,-1,0,1, so there are 4. Final answer: 4.
- `invalid_answer_wrong_trace`: At most 1 means strictly less than 1, so the elements are -2,-1,0. There are 3. Final answer: 3.
- `manual_error_span`: At most 1 means strictly less than 1
- `localized_hint`: The boundary meaning of `at most` may be wrong. Recheck whether 1 is included.
- `oracle_hint`: `at most 1` means <=1, so the boundary value 1 is included.
- `random_control_span`: the set {-2,-1,0,1,2,3}
- `verifier`: exact integer answer 4.
- `e162_use`: tests local semantic repair for inclusive boundary words.
- `e163_use`: compare hidden states after `at most`, after listing values, and before the count.

### set_02_complement_wrong_universe

- `family`: set_venn_counting
- `problem`: Let U={1,2,...,12}. Let A be multiples of 2 in U and B be multiples of 3 in U. How many elements of U are not in A union B?
- `gold_answer`: 4
- `valid_trace`: In U, multiples of 2 are 6, multiples of 3 are 4, and overlap multiples of 6 are 2. The union has 6+4-2=8 elements. The complement has 12-8=4. Final answer: 4.
- `invalid_answer_correct_trace`: Use universe {1,2,...,11}. The numbers not divisible by 2 or 3 are 1,5,7,11, so the count is 4. Final answer: 4.
- `invalid_answer_wrong_trace`: Multiples of 2 or 3 are 6+4=10, so the complement has 12-10=2. Final answer: 2.
- `manual_error_span`: Use universe {1,2,...,11}
- `localized_hint`: The universe used for the complement may not match the problem. Recheck U.
- `oracle_hint`: The universe is U={1,...,12}; complement must be taken inside that universe.
- `random_control_span`: multiples of 3
- `verifier`: exact integer answer 4.
- `e162_use`: tests universe correction and complement repair.
- `e163_use`: replay after reading U, after using the wrong universe, and before complement count.

### set_03_multiset_occurrences

- `family`: set_venn_counting
- `problem`: A bag contains red-A, red-A, red-B, blue-A, and red-C. Counting occurrences, how many red items are in the bag?
- `gold_answer`: 4
- `valid_trace`: Counting occurrences means duplicates count separately. The red items are red-A, red-A, red-B, and red-C, so there are 4. Final answer: 4.
- `invalid_answer_correct_trace`: A multiset count ignores duplicates. The red items are red-A, red-A, red-B, and red-C, so the count is 4. Final answer: 4.
- `invalid_answer_wrong_trace`: Ignore the duplicate red-A, leaving red-A, red-B, and red-C. There are 3 red items. Final answer: 3.
- `manual_error_span`: A multiset count ignores duplicates
- `localized_hint`: The duplicate-counting rule may be wrong. Recheck the phrase `Counting occurrences`.
- `oracle_hint`: Counting occurrences means the repeated red-A contributes twice.
- `random_control_span`: blue-A
- `verifier`: exact integer answer 4.
- `e162_use`: tests whether a local warning can switch from distinct-counting to occurrence-counting.
- `e163_use`: inspect hidden states at `occurrences`, at the duplicate token, and before final count.

## Graph Definitions / 图定义

Graph cases test directedness, self-loops, multiedges, walks, paths, and simple paths. / 图样本测试有向性、自环、多重边、walk、path 和 simple path 的定义边界。

### graph_01_directed_reachability

- `family`: graph_definition
- `problem`: A directed graph has vertices A,B,C,D and edges A->B, B->C, C->B, D->D. Counting A itself, how many vertices are reachable from A?
- `gold_answer`: 3
- `valid_trace`: From A, we can stay at A, go to B, and then go to C. There is no edge from A, B, or C to D. Reachable vertices are A,B,C, so the count is 3. Final answer: 3.
- `invalid_answer_correct_trace`: Treat the directed edges as undirected. From A, the reachable vertices are A,B,C, so the count is 3. Final answer: 3.
- `invalid_answer_wrong_trace`: Every vertex that appears in any edge is reachable from A, so A,B,C,D all count. Final answer: 4.
- `manual_error_span`: Treat the directed edges as undirected
- `localized_hint`: The graph direction rule may be wrong. Recheck whether edges can be reversed.
- `oracle_hint`: The graph is directed. The undirected shortcut happens not to change this count, but the valid method is directed reachability.
- `random_control_span`: vertices A,B,C,D
- `verifier`: exact integer answer 3; optional graph reachability script.
- `e162_use`: tests repair of directionality errors.
- `e163_use`: replay after reading `directed`, after edge D->A, and after reachable set construction.

### graph_02_self_loop_degree

- `family`: graph_definition
- `problem`: In an undirected multigraph, vertex v has edges (v,v), (v,u), and (v,w). A self-loop contributes 2 to degree. What is the degree of v?
- `gold_answer`: 4
- `valid_trace`: The self-loop (v,v) contributes 2. The two ordinary incident edges contribute 1 each. The degree is 2+1+1=4. Final answer: 4.
- `invalid_answer_correct_trace`: A self-loop contributes only 1 to degree. Therefore the degree is 2+1+1=4. Final answer: 4.
- `invalid_answer_wrong_trace`: A self-loop contributes only 1, plus (v,u) and (v,w), so the degree is 1+1+1=3. Final answer: 3.
- `manual_error_span`: A self-loop contributes only 1 to degree
- `localized_hint`: The self-loop contribution may contradict the problem statement. Recheck it.
- `oracle_hint`: The problem explicitly says a self-loop contributes 2 to degree.
- `random_control_span`: vertex v
- `verifier`: exact integer answer 4.
- `e162_use`: tests whether models obey an explicit definition over a memorized or mistaken rule.
- `e163_use`: inspect states at `self-loop`, `contributes 2`, and the final sum.

### graph_03_simple_path_vs_walk

- `family`: graph_definition
- `problem`: A directed graph has edges A->B, B->A, B->C, C->D, and A->D. A simple path cannot repeat vertices. How many simple paths go from A to D?
- `gold_answer`: 2
- `valid_trace`: The simple paths are A->D and A->B->C->D. The walk A->B->A->D repeats A, so it is not simple. There are 2 simple paths. Final answer: 2.
- `invalid_answer_correct_trace`: A simple path may repeat vertices. The simple paths are A->D and A->B->C->D, so there are 2. Final answer: 2.
- `invalid_answer_wrong_trace`: A simple path may repeat vertices, so A->D, A->B->C->D, and A->B->A->D all count. There are 3. Final answer: 3.
- `manual_error_span`: A simple path may repeat vertices
- `localized_hint`: The definition of simple path may be wrong. Recheck the problem statement.
- `oracle_hint`: A simple path cannot repeat vertices, so A->B->A->D must be excluded.
- `random_control_span`: edge A->D
- `verifier`: exact integer answer 2; optional DFS enumerator.
- `e162_use`: tests repair from a walk/path definition error.
- `e163_use`: replay after reading definition, after repeated-vertex candidate, and before final count.

## Long Table Aggregation / 长表格聚合

Table cases test AND/OR filters, zero-row aggregation, duplicate rows, and percentage denominators. / 表格样本测试 AND/OR 筛选、零行聚合、重复行和百分比分母。

### table_01_and_filter_zero_amount_exclusion

- `family`: long_table_aggregation
- `problem`: Table rows are: 1 West paid Apr 12; 2 West unpaid Apr 9; 3 East paid Apr 7; 4 West paid Mar 5; 5 West paid Apr 6; 6 West paid Apr 0. Sum amount where region=West AND status=paid AND month=Apr.
- `gold_answer`: 18
- `valid_trace`: Rows matching all three conditions are 1, 5, and 6. The sum is 12+6+0=18. Final answer: 18.
- `invalid_answer_correct_trace`: Rows with amount 0 should be excluded before checking the filter, so row 6 is not a real matching row. Matching rows are 1 and 5, and the sum is 12+6=18. Final answer: 18.
- `invalid_answer_wrong_trace`: The filter uses OR, so include rows 1,2,3,4,5,6. The sum is 12+9+7+5+6+0=39. Final answer: 39.
- `manual_error_span`: Rows with amount 0 should be excluded before checking the filter
- `localized_hint`: The zero-amount row handling may be wrong. Recheck whether matching rows with amount 0 still satisfy the filter.
- `oracle_hint`: Row 6 satisfies West, paid, and Apr; its amount is 0, so including or excluding it does not change the sum, but excluding it as a nonmatch is a process error.
- `random_control_span`: row 6
- `verifier`: exact integer answer 18; optional table filter script.
- `e162_use`: tests whether localized logical-connector warnings repair aggregation.
- `e163_use`: replay after condition parsing, after row selection, and before summation.

### table_02_zero_row_false_match

- `family`: long_table_aggregation
- `problem`: Table rows are: 1 North paid 5; 2 South refunded 8; 3 East paid 0; 4 North paid 0. Sum amount for rows where region=North AND status=refunded.
- `gold_answer`: 0
- `valid_trace`: No row has both region North and status refunded. The sum over an empty matching set is 0. Final answer: 0.
- `invalid_answer_correct_trace`: Row 4 is North and refunded with amount 0. The sum is 0. Final answer: 0.
- `invalid_answer_wrong_trace`: Row 2 is refunded, so include amount 8. Final answer: 8.
- `manual_error_span`: Row 4 is North and refunded
- `localized_hint`: The claimed matching row may not satisfy both filter conditions. Recheck row 4.
- `oracle_hint`: Row 4 is North paid, not North refunded; there are zero matching rows.
- `random_control_span`: amount 0
- `verifier`: exact integer answer 0; optional table filter script.
- `e162_use`: tests whether the model can distinguish true zero-row answers from false zero-valued matches.
- `e163_use`: replay after row 4, after filter decision, and before empty-sum answer.

### table_03_percentage_denominator_swap

- `family`: long_table_aggregation
- `problem`: Table rows are: 1 West active pass; 2 West active pass; 3 West active fail; 4 West active fail; 5 West inactive pass; 6 East active pass; 7 East active fail. Among active West rows, what percent pass?
- `gold_answer`: 50%
- `valid_trace`: Active West rows are 1,2,3,4. Two pass, so the percent is 2/4=50%. Final answer: 50%.
- `invalid_answer_correct_trace`: The denominator should be all active rows. Active rows are 1,2,3,4,6,7; three pass and three fail, so 3/6=50%. Final answer: 50%.
- `invalid_answer_wrong_trace`: Use all West rows. Rows 1,2,3,4,5 include three pass out of five, so 60%. Final answer: 60%.
- `manual_error_span`: The denominator should be all active rows
- `localized_hint`: The denominator may not match `active West`. Recheck the conditioning group.
- `oracle_hint`: The denominator is active West rows only, not all active rows and not all West rows.
- `random_control_span`: row 7
- `verifier`: exact normalized answer 50%.
- `e162_use`: tests denominator repair in percentage tasks.
- `e163_use`: replay after reading the target group, after denominator selection, and before percentage.

## Code Boundary / 代码边界

Code cases test executable semantics such as `range`, negative index, empty input, and short-circuit evaluation. / 代码样本测试可执行语义，例如 `range`、负索引、空输入和短路求值。

### code_01_range_start_zero

- `family`: code_boundary
- `problem`: What does this Python code print?

```python
total = 0
for i in range(0, 6):
    total += i * (i - 5)
print(total)
```
- `gold_answer`: -20
- `valid_trace`: `range(0,6)` gives 0,1,2,3,4,5. The terms are 0,-4,-6,-6,-4,0, whose sum is -20. Final answer: -20.
- `invalid_answer_correct_trace`: `range(0,6)` skips 0 and gives 1,2,3,4,5. The terms are -4,-6,-6,-4,0, whose sum is -20. Final answer: -20.
- `invalid_answer_wrong_trace`: `range(0,6)` includes 6, so add 6*(6-5)=6 to -20 and get -14. Final answer: -14.
- `manual_error_span`: range(0,6) skips 0
- `localized_hint`: The Python `range` boundary rule may be wrong. Recheck whether the start value is included.
- `oracle_hint`: Python `range(0,6)` includes 0 and excludes 6.
- `random_control_span`: total=0
- `verifier`: run Python or exact integer answer -20.
- `e162_use`: tests repair of range boundary errors where the skipped term is zero.
- `e163_use`: replay at `range(0,6)`, after term enumeration, and before summation.

### code_02_negative_index_symmetric_value

- `family`: code_boundary
- `problem`: What does this Python code print? `arr=[7,0,7]; print(arr[-1]+arr[1])`
- `gold_answer`: 7
- `valid_trace`: In Python, `arr[-1]` is the last element, which is 7, and `arr[1]` is 0. The sum is 7. Final answer: 7.
- `invalid_answer_correct_trace`: In Python, `arr[-1]` is the first element, which is 7, and `arr[1]` is 0. The sum is 7. Final answer: 7.
- `invalid_answer_wrong_trace`: Negative index -1 is invalid, so the code raises an error. Final answer: Error.
- `manual_error_span`: arr[-1] is the first element
- `localized_hint`: The negative-index rule may be wrong. Recheck how Python indexes `-1`.
- `oracle_hint`: In Python, `arr[-1]` means the last element, not the first element.
- `random_control_span`: arr[1]
- `verifier`: run Python; printed answer `7`.
- `e162_use`: tests whether a localized warning fixes process semantics even when the final answer is preserved by symmetry.
- `e163_use`: replay after token `-1`, after element lookup, and before final print.

### code_03_short_circuit_side_effect

- `family`: code_boundary
- `problem`: What does this Python code print?

```python
x = 0
def bump():
    global x
    x += 1
    return True
if False and bump():
    x += 10
print(x)
```
- `gold_answer`: 0
- `valid_trace`: In `False and bump()`, Python short-circuits and does not call `bump`. The body does not run, so x remains 0. Final answer: 0.
- `invalid_answer_correct_trace`: `bump()` is called inside the `and`, but because the left side is False, x remains 0. Final answer: 0.
- `invalid_answer_wrong_trace`: `bump()` is called, so x becomes 1. The body does not run, so the print is 1. Final answer: 1.
- `manual_error_span`: bump() is called inside the `and`
- `localized_hint`: The short-circuit evaluation claim may be wrong. Recheck whether `bump()` is called.
- `oracle_hint`: `False and bump()` does not evaluate `bump()` in Python.
- `random_control_span`: x+=10
- `verifier`: run Python; printed answer `0`.
- `e162_use`: tests repair of side-effect reasoning under short-circuit logic.
- `e163_use`: replay after `False and`, after `bump()`, and before print.

## Multilingual Semantics / 多语言语义

Multilingual cases test whether Chinese, English, pinyin, and mixed constraints map to the same mathematical condition. / 多语言样本测试中文、英文、拼音和混合表达是否映射到同一个数学条件。

### multi_01_pinyin_zhi_duo_wei

- `family`: multilingual_semantic
- `problem`: Qiu zhengshu x de geshu: -8 <= x <= 8, qie |x| zhi duo wei 3.
- `gold_answer`: 7
- `valid_trace`: `zhi duo wei 3` means at most 3, so |x|<=3. The integers are -3,-2,-1,0,1,2,3, giving 7 values. Final answer: 7.
- `invalid_answer_correct_trace`: `zhi duo wei 3` means a multiple of 3. The valid integers are -3,-2,-1,0,1,2,3, giving 7 values. Final answer: 7.
- `invalid_answer_wrong_trace`: `zhi duo wei 3` means a multiple of 3. In the range, |x| is 0,3,6, so x is -6,-3,0,3,6. There are 5 values. Final answer: 5.
- `manual_error_span`: zhi duo wei 3 means a multiple of 3
- `localized_hint`: The meaning of `zhi duo wei 3` may be wrong. Recheck whether it means `at most 3`.
- `oracle_hint`: `zhi duo wei 3` means `至多为 3`, i.e. at most 3 or <=3.
- `random_control_span`: -8 <= x <= 8
- `verifier`: exact integer answer 7.
- `e162_use`: already shown useful in smoke; localized prompt repaired Gemma dense while generic prompt did not.
- `e163_use`: align states for pinyin `zhi duo wei`, Chinese `至多为`, English `at most`, and symbol `<=`.

### multi_02_no_more_than_boundary

- `family`: multilingual_semantic
- `problem`: Scores are 68, 70, 71, and 72. How many scores are no more than 70?
- `gold_answer`: 2
- `valid_trace`: `No more than 70` means <=70. The scores 68 and 70 count, so the answer is 2. Final answer: 2.
- `invalid_answer_correct_trace`: `No more than 70` means strictly less than 70. The scores 68 and 70 count, so the answer is 2. Final answer: 2.
- `invalid_answer_wrong_trace`: `No more than 70` means strictly less than 70, so only 68 counts. Final answer: 1.
- `manual_error_span`: No more than 70 means strictly less than 70
- `localized_hint`: The boundary meaning of `no more than` may be wrong. Recheck whether 70 counts.
- `oracle_hint`: `No more than 70` means <=70, so 70 is included.
- `random_control_span`: Scores are 68, 70, 71, and 72
- `verifier`: exact integer answer 2.
- `e162_use`: tests English boundary semantics without pinyin.
- `e163_use`: compare hidden states for `no more than`, `at most`, `<=`, and Chinese `不超过`.

### multi_03_mixed_exactly_qiahao

- `family`: multilingual_semantic
- `problem`: In the list [1,2,2,3,4], count numbers qiahao equal to 2. Here qiahao means exactly.
- `gold_answer`: 2
- `valid_trace`: `qiahao` means exactly, so count entries equal to 2. The two 2s count, giving 2. Final answer: 2.
- `invalid_answer_correct_trace`: `qiahao` means at least. The entries equal to 2 are the two 2s, giving 2. Final answer: 2.
- `invalid_answer_wrong_trace`: `qiahao` means at least, so 2,2,3,4 count. There are 4. Final answer: 4.
- `manual_error_span`: qiahao means at least
- `localized_hint`: The mixed-language word `qiahao` may be misread. Recheck the definition in the problem.
- `oracle_hint`: The problem defines `qiahao` as exactly, not at least.
- `random_control_span`: [1,2,2,3,4]
- `verifier`: exact integer answer 2.
- `e162_use`: tests whether an explicit local definition overrides a more familiar comparative meaning.
- `e163_use`: replay after the definition sentence and after applying the filter.

## Proof Validity / 证明有效性

Proof cases are the closest to ACPI because a conclusion can be true while the proof uses a false lemma, invalid converse, or illegal algebraic move. / 证明样本最接近 ACPI，因为结论可以为真，但证明使用假引理、错误逆命题或非法代数步骤。

### proof_01_true_claim_false_converse

- `family`: proof_validity
- `problem`: Decide true or false: If an integer n is divisible by 6, then n is divisible by 3.
- `gold_answer`: True
- `valid_trace`: If n is divisible by 6, then n=6k for some integer k. Since 6k=3*(2k), n is divisible by 3. Final answer: True.
- `invalid_answer_correct_trace`: Every integer divisible by 3 is divisible by 6, so an integer divisible by 6 is divisible by 3. Final answer: True.
- `invalid_answer_wrong_trace`: 6 and 3 are different divisors, so divisibility by 6 does not imply divisibility by 3. Final answer: False.
- `manual_error_span`: Every integer divisible by 3 is divisible by 6
- `localized_hint`: The divisibility implication may be reversed. Recheck the direction.
- `oracle_hint`: The true implication is 6|n implies 3|n; the converse 3|n implies 6|n is false.
- `random_control_span`: integer n
- `verifier`: boolean answer True.
- `e162_use`: tests repair of converse errors while the conclusion remains true.
- `e163_use`: compare hidden states for false converse, correct implication, and final truth label.

### proof_02_even_square_false_lemma

- `family`: proof_validity
- `problem`: Decide true or false: For every integer n, n^2+n is even.
- `gold_answer`: True
- `valid_trace`: n^2+n=n(n+1), the product of two consecutive integers. One of them is even, so the product is even. Final answer: True.
- `invalid_answer_correct_trace`: For every integer n, both n^2 and n are even, so n^2+n is even. Final answer: True.
- `invalid_answer_wrong_trace`: For n=1, n^2+n=1+1=2, which is odd, so the claim is false. Final answer: False.
- `manual_error_span`: both n^2 and n are even
- `localized_hint`: The parity lemma may be false. Recheck whether every integer n is even.
- `oracle_hint`: The conclusion is true because n and n+1 are consecutive; it is not true that n and n^2 are always even.
- `random_control_span`: n^2+n
- `verifier`: boolean answer True.
- `e162_use`: tests repair of false lemma in a true theorem.
- `e163_use`: replay after the false lemma, after the consecutive-integers proof, and before truth label.

### proof_03_illegal_division_preserved_roots

- `family`: proof_validity
- `problem`: Decide true or false: For real x, if x^2=1 then x=1 or x=-1.
- `gold_answer`: True
- `valid_trace`: x^2=1 means x^2-1=0, so (x-1)(x+1)=0. Therefore x=1 or x=-1. Final answer: True.
- `invalid_answer_correct_trace`: From (x-1)(x+1)=0, divide by x-1 to get x+1=0, so x=-1. By symmetry, x=1 is also possible. Thus x=1 or x=-1. Final answer: True.
- `invalid_answer_wrong_trace`: Divide by x-1 to get x+1=0, so the only solution is x=-1. Therefore the statement with `or x=1` is false. Final answer: False.
- `manual_error_span`: divide by x-1
- `localized_hint`: The algebraic division step may be invalid for one possible solution. Recheck it.
- `oracle_hint`: Dividing by x-1 can lose the solution x=1; use the zero-product rule instead.
- `random_control_span`: real x
- `verifier`: boolean answer True.
- `e162_use`: tests repair of illegal algebraic manipulation in a proof.
- `e163_use`: replay after the factorization, after illegal division, and before the truth label.

## Immediate Build Plan / 直接构建计划

The next runnable experiment should be E164, not a replacement for E162. / 下一个可运行实验应命名为 E164，不替代正在跑的 E162。

1. Build a JSONL bank from this spec. / 从本规格构造 JSONL 样本库。
2. Static audit before any model call. / 任何模型调用前先做静态审计。
3. Smoke the first case only. / 先只跑第一个样本。
4. Inspect the first result manually. / 人工审计首条结果。
5. Queue full non-thinking generation and repair only after smoke passes. / smoke 通过后再排全量 non-thinking 生成和修复。

Planned E164 artifacts / 计划产物：

- `data/processed/e164_high_value_concrete_family_tasks_20260501.jsonl`
- `data/processed/e164_high_value_concrete_family_candidate_solutions_20260501.jsonl`
- `reports/E164_HIGH_VALUE_CONCRETE_FAMILY_STATIC_AUDIT_20260501.json`
- `results/E164_high_value_concrete_family_generation/`
- `results/E165_high_value_concrete_family_error_prompt_repair/`

Recommended first smoke sample / 推荐首个 smoke 样本：

- `multi_01_pinyin_zhi_duo_wei`, because it already reproduced a real Gemma dense semantic failure in E159 and repaired under localized E162 prompting. / 推荐 `multi_01_pinyin_zhi_duo_wei`，因为它已经在 E159 复现 Gemma dense 真实语义失败，并在 E162 localized prompt 中被修复。

Recommended family priority / 推荐优先级：

1. Proof validity / 证明有效性：closest to ACPI and strongest for paper framing. / 最接近 ACPI，也最适合论文主线。
2. Multilingual semantics / 多语言语义：directly tied to multilingual process lens and current Gemma failure. / 直接连接 multilingual process lens 和当前 Gemma 错误。
3. Graph definitions and code boundary / 图定义与代码边界：verifiable, crisp, and easy to localize. / 可程序验证、边界清楚、易定位。
4. Long table aggregation / 长表格聚合：good for realistic applied settings, but needs careful parser/verifier. / 贴近真实应用，但需要更细的解析和验证。
5. Geometry constraints / 几何约束：high value but needs strict wording to avoid ambiguity. / 价值高，但题目措辞必须严格避免歧义。
