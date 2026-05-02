# E162/E163 High-Value Family Design / 高价值 family 设计

This design supports two next-stage experiments:

- E162: low-confidence truncation plus error-prompt repair. / 低置信截断 + 错误提示修复。
- E163: hidden residual / MLP / attention replay and trigger discovery. / hidden residual、MLP、attention replay 与触发点发现。

Core principle / 核心原则：each task should have paired traces when possible: valid trace, invalid-but-answer-correct trace, and invalid-answer-wrong trace. This lets the same problem support ACPI, repair, and hidden-state analysis. / 每题尽量配三种 trace：正确过程、过程错但答案对、过程错且答案错；同一题可以同时支持 ACPI、修复和隐藏状态分析。

## Priority Families / 优先 family

1. Proof validity / 证明有效性
   - Why / 原因：closest to ACPI. A conclusion may be true while the proof uses a false lemma, invalid converse, missing precondition, or quantifier swap. / 最接近 ACPI：结论可以为真，但证明用了假引理、逆命题、漏前提或量词错换。
   - Templates / 模板：true theorem with false lemma; converse misuse; exists/for-all confusion; induction missing step; theorem precondition violated.
   - Best use / 用途：E162 for local repair of converse/precondition errors; E163 for separating answer-state from proof-validity-state.

2. Multilingual semantics / 多语言语义
   - Why / 原因：directly aligned with multilingual process lens; E159 already found Gemma dense misreading `zhi duo wei 3`. / 与主线直接相关，E159 已发现 Gemma dense 误读 `zhi duo wei 3`。
   - Templates / 模板：`zhi duo wei` / at most / no more than; at least / no fewer than; exactly; Chinese-English mixed constraints; pinyin transliteration plus math notation.
   - Best use / 用途：E162 for localized semantic repair; E163 for checking whether Chinese, English, pinyin, and mixed forms converge to similar hidden states.

3. Long table aggregation / 长表格聚合
   - Why / 原因：local row/condition errors are easy to hide inside a long context. / 局部行筛选和条件错误容易被长上下文掩盖。
   - Templates / 模板：multi-condition AND vs OR filtering; zero matching rows; duplicated rows as transactions vs duplicate records; denominator changes in percentages; group-then-filter vs filter-then-group.
   - Best use / 用途：E162 for row/filter repair; E163 for replay after reading the table, after filtering, and before aggregation.

4. Graph definitions / 图定义
   - Why / 原因：definition boundaries are crisp and model errors are easy to audit. / 定义边界清楚，错步容易审计。
   - Templates / 模板：directed reachability vs undirected connectivity; self-loop degree contribution; multiedge counting; walk/path/simple path; connected vs strongly connected.
   - Best use / 用途：E162 for localized definition repair; E163 for observing whether directionality, multiplicity, and repeated-vertex constraints are represented internally.

5. Geometry constraints / 几何约束
   - Why / 原因：models often import visual assumptions such as false parallelism, false perpendicularity, or unjustified similarity. / 模型容易偷用图像假设，例如假平行、假垂直、未证相似。
   - Templates / 模板：SAS similarity but false AA explanation; angle chasing with hidden parallel trap; degenerate triangle condition; tangent-radius perpendicularity; two-configuration angle/length cases.
   - Best use / 用途：E162 for degeneracy and multi-configuration repair; E163 for false similarity/parallel hidden-state separation.

6. Code boundary / 代码边界
   - Why / 原因：program execution gives objective gold, and boundary mistakes are precise. / 可程序验证，边界错误精确。
   - Templates / 模板：Python `range` end-exclusive; negative indexing; empty list/string; short-circuit side effects; sliding-window off-by-one.
   - Best use / 用途：E162 for negative-index, empty-input, and short-circuit repair; E163 for range/off-by-one state tracking.

7. Set/Venn counting / 集合与 Venn
   - Why / 原因：at least/at most/exactly, complement universe, and inclusion-exclusion create answer-preserving traps. / 至少/至多/恰好、补集全集、容斥容易制造保答案陷阱。
   - Templates / 模板：at least one vs exactly one; at most two vs fewer than two; complement relative to wrong universe; set difference precedence; multiset occurrence vs distinct item.
   - Best use / 用途：E162 for semantic/local repair; E163 for overlap-region and complement-state replay.

## Top 20 Sample Types / Top 20 样本类型

1. True conclusion with false lemma. / 结论真但引理假。
2. `zhi duo wei` / at most / no more than boundary semantics. / 多语言边界词。
3. Long-table percentage denominator changes. / 长表格百分比分母变化。
4. Directed graph treated as undirected while answer is preserved. / 有向图错当无向图但答案碰巧保持。
5. Geometry false parallel causing invalid AA similarity, with SAS available. / 假平行导致错误 AA 相似，但 SAS 可证。
6. Code short-circuit with side effects. / 代码短路副作用。
7. `at most k` vs `< k` with boundary controlled. / 至多与小于的边界控制。
8. Converse misuse with independently true conclusion. / 逆命题误用但结论另有证明。
9. Zero-row table aggregation. / 表格筛选后零行。
10. Self-loop degree contribution. / 自环度数贡献。
11. Negative indexing plus empty input. / 负索引与空输入。
12. Complement relative to wrong universe. / 补集全集错误。
13. Degenerate triangle condition. / 退化三角形条件。
14. Chinese-English mixed exactly/at least/at most filters. / 中英混合边界筛选。
15. Duplicate row as transaction vs duplicate record. / 重复行语义。
16. Simple path vs walk. / 简单路径与 walk 混用。
17. Python `range` off-by-one with zero endpoint. / `range` 闭开边界和零端点。
18. Three-set exactly-one vs at-least-one confusion. / 三集合“恰好一个”和“至少一个”混淆。
19. Geometry two-configuration case with one branch omitted. / 几何双构型漏一支。
20. Induction proof missing the real inductive step. / 归纳证明漏关键步。

## Quality Controls / 质量控制

- Every task needs a unique gold answer. / 每题必须有唯一答案。
- Ambiguous terms must be defined in the problem, especially path/walk/simple path and duplicate-row semantics. / 歧义术语必须题内定义。
- ACPI traces must contain a real invalid reasoning step, not a wording nit. / ACPI trace 必须有真实错步，不是措辞小错。
- Gold answer, labels, trap notes, and error spans stay offline for blind conditions. / blind 条件不泄漏答案、标签、陷阱说明或错步。
- Table and code tasks should be program-checkable. / 表格和代码题优先程序验证。
- Multilingual tasks should have Chinese, English, pinyin, and mixed variants for hidden-state alignment. / 多语言题保留中文、英文、拼音和混合版本，便于 hidden-state 对齐。
