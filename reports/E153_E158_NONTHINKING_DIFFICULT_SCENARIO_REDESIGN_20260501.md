# E153-E158 Non-Thinking Difficult-Scenario Redesign / non-thinking 困难情景重设计（2026-05-01）

## Decision / 决策

The previous E147 Phase-A queue was paused by user instruction. Existing 24 checkpoint rows plus one smoke row are debug-only. `answer_first_no_gold` is no longer part of the primary discovery line; it is retained only as answer-commitment / repair-awareness diagnostic material. / 原 E147 Phase-A 已按用户指令暂停。已有 checkpoint 和 smoke 只作 debug。`answer_first_no_gold` 不再作为主发现线，只保留为答案承诺/修复意识诊断材料。

## New Core Question / 新核心问题

In non-thinking mode, what does a model naturally do on diverse difficult scenarios, and can hidden prefill signals identify or help repair process errors before a blind final verifier would accept them? / 在 non-thinking 模式下，模型面对多样困难情景会自然怎样作答？hidden prefill 信号能否在 blind verifier 接受前识别或帮助修复过程错误？

## E153 Natural Non-Thinking Difficult Scenario Bank / 自然 non-thinking 困难情景库

Purpose / 目的：collect reasoning-first non-thinking traces across broad hard scenarios. / 在广泛困难情景中采集“先推理后答案”的 non-thinking trace。

Prompts / prompt：

- `solve_neutral`: solve carefully, show necessary reasoning, final answer last.
- `solve_terse`: concise derivation, final answer last.
- `solve_self_check`: derive, do one short self-check, final answer last.
- `find_problem_global`: given a problem and a proposed solution trace, identify whether there is an error and where. This is not generation prevalence; it measures natural non-thinking error-finding behavior. / 给题目和候选解，让模型找错；这不是发生率实验，而是自然找错能力实验。
- `find_problem_localize_only`: locate the first questionable step; no repair requested. / 只定位可疑步骤，不要求修复。

Primary generation prompts are the first three. Error-finding prompts are a separate verifier/checker subtask and must not be mixed with natural generation denominators. / 主生成 prompt 是前三个；找错 prompt 是单独 verifier/checker 子任务，不和自然生成分母混合。

## Scenario Families / 情景族

High-quality families have one property: a local wrong step can plausibly be hidden by later fluent or answer-coherent text, while a human can audit the exact local error. / 高质量情景族的共同点：局部错步可能被后文流畅性或答案自洽掩盖，但人工能精确审计错在哪里。

Current core families / 当前核心：

1. algebra sign/factorization / 代数符号与因式分解。
2. counting invariant/symmetry / 计数不变量与对称。
3. code boundary/off-by-one / 代码边界。
4. table aggregation / 表格聚合。
5. unit and percentage base / 单位与百分比基底。
6. multilingual semantic traps / 多语言语义陷阱。
7. proof validity / 证明有效性。

Additional high-value families / 新增高价值情景：

8. probability conditioning: confuse P(A|B) with P(B|A), independence, or base rates. / 概率条件与基率错配。
9. graph/path constraints: shortest path, degree parity, directed vs undirected edges. / 图路径与约束。
10. geometry diagram-free constraints: similar triangles, tangent/incircle constraints, reflection type, angle chasing. / 无图几何约束。
11. recurrence/dynamic programming: wrong base case or transition that coincidentally works on small cases. / 递推/动态规划边界。
12. string/regex parsing: greedy vs non-greedy, inclusive index slicing, Unicode/case normalization. / 字符串与正则解析。
13. temporal/order reasoning: before/after, inclusive dates, time-zone or schedule order. / 时间与顺序推理。
14. causal/counterfactual wording: necessary vs sufficient, if/only-if, intervention vs observation. / 因果与反事实措辞。
15. set/Venn constraints: union/intersection/complement, exactly-one vs at-least-one. / 集合与韦恩图。
16. optimization constraints: local optimum vs global optimum, boundary feasibility. / 优化约束。

Recommended raw materials / 原材料：

- Self-contained synthetic templates with programmatically computed answers for code/table/counting/probability/set tasks. / 可程序计算答案的自构模板。
- Public contest-style tasks only when short and auditable, e.g. AIME/AMC-style math, but avoid relying on them alone. / 可审计的竞赛短题，但不能只靠它们。
- Mini code snippets and table snippets generated locally, no external hidden answers in prompts. / 本地生成代码/表格片段。
- Native/translated multilingual variants produced from our own templates, with romanized and mixed-language variants as stress routes. / 自有模板的多语言版本。
- Handwritten valid solution skeletons for later mutation/probe tasks, stored as offline material, not shown during natural generation. / 后续篡改用的正确解骨架，离线保存。

## E154 Structured Audit / 结构化审计

For each natural trace, record / 每条自然 trace 记录：

- final answer correctness;
- strict process label;
- repair-aware process label;
- unrepaired ACPI if final answer correct and retained proof depends on a wrong step;
- wrong-answer + process error if answer wrong and process wrong;
- self-check markers;
- number of explicit corrections;
- first wrong step span;
- repair span if any;
- whether final answer appears before, during, or after reasoning.

This audit is single-pass structured for now; formal double audit is deferred. / 当前先做单轮结构化审计，正式双审后置。

## E155 Mutation and Probe Set / 篡改与探针集

Minimal mutations remain useful as clean probes, but we add larger mutations now. / 最小篡改仍适合探针，但现在加入更大篡改。

Immediate mutation types / 现在加入：

1. local semantic flip: inclusive/exclusive, at most/at least, before/after. / 局部语义翻转。
2. algebra/sign/factor replacement. / 代数符号或因式替换。
3. boundary/index mutation. / 边界或索引篡改。
4. aggregation/category mutation. / 聚合或分类篡改。
5. multi-step coherent wrong proof: replace 2-4 consecutive lines with a plausible but wrong derivation. / 多步连贯错误证明。
6. wrong repair insertion: insert a fake correction that appears to repair but actually preserves the wrong premise. / 伪修复。
7. suffix rationalization: keep a wrong local step but add a fluent answer-coherent suffix. / 后缀合理化。
8. distractor detour: insert a valid but irrelevant detour before returning to a wrong step. / 无关正确绕路。
9. answer-consistent wrong derivation: force the derivation to end at the known correct answer via invalid cancellation. / 答案一致但过程错的推导。

Use now / 现在适合加入：types 1-7. Types 8-9 are useful but should be added after smoke because they can be harder to audit. / 建议先加入 1-7，8-9 后续加。

## E156 Prefill Hidden Localization / prefill hidden 定位

Feed original and mutated traces to the model in direct/non-thinking verifier/checker prompts, teacher-forced through the visible text. / 把原始和篡改 trace 送入 direct/non-thinking verifier/checker prompt，并在 prefill 中读 hidden。

Measure / 测量：

- hidden risk score before/after mutation span;
- residual/MLP/token-mixer/attention-related movement;
- Yes/No margin at completion;
- whether signal appears before final answer;
- whether answer-coherent suffix dilutes signal.

## E157 Natural Error-Finding and Assisted Repair / 自然找错与辅助修复

Two subtasks / 两个子任务：

1. Natural non-thinking error-finding: give problem + trace, ask the model to directly state whether there is a wrong step and where. / 给题目和 trace，让模型 non-thinking 直接找错。
2. Hidden-assisted repair: after prefill, provide a neutral warning tied to the hidden-selected visible window, e.g. "A monitor flagged the following excerpt as potentially risky; check only whether it is valid." / hidden 辅助修复：给 hidden 选出的窗口和中性警告。

For wrong-answer traces, test whether hidden-assisted local checking can correct light errors. Report separately from ACPI. / 对答案错且过程错的 trace，测试 hidden-assisted local check 能否修复轻度错误；这不算 ACPI，单独报告。

Assistance levels / 辅助等级：

- blind global: whole trace only;
- blind locate-only: whole trace, ask first questionable step;
- hidden-window: hidden-selected visible excerpt, without saying it is definitely wrong;
- oracle-span: human error span, upper bound only.

## E158 Explainability Cards / 可解释性个案卡

Representative cases should include / 代表个案包括：

- natural strict-valid;
- natural repaired ACPI;
- natural unrepaired ACPI if found;
- wrong-answer process-error that hidden-assisted check can correct;
- mutation where hidden signal fires and checker succeeds;
- mutation where hidden signal fires but checker fails.

