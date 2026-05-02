# E147-E152 Non-Thinking Unrepaired ACPI Plan / non-thinking 未修复 ACPI 诱发与方法验证计划

Date / 日期：2026-04-30

## Scope / 范围

Thinking-mode work is deferred. This stage focuses on non-thinking generation, direct/non-thinking verification, hidden-triggered checking, and interpretability. / thinking 模式暂缓。本阶段只做 non-thinking 生成、direct/non-thinking verifier、hidden 触发检查和可解释性分析。

Human double-audit reliability is also deferred to paper-finalization. For this stage, final-correct rows still receive structured process labels, but the goal is discovery and mechanism, not final prevalence certification. / 正式双审后置。本阶段仍对 final-correct 行做结构化过程标签，但目标是发现样本与机制分析，不是最终发生率认证。

## Current Scientific Target / 当前科学目标

We want to show that unrepaired ACPI is not just two accidental Gemma26 rows, and that hidden-triggered non-thinking checks can reduce process-invalid trace acceptance across more task families. / 我们要证明未修复 ACPI 不只是 Gemma26 的两个偶然个案，并验证 hidden 触发的 non-thinking 检查能在更多任务族中降低坏过程 trace 的接受率。

Safe wording / 安全说法：

> Unrepaired ACPI can be induced across broader non-thinking task settings; hidden process-risk signals can improve low-cost checking in many settings, but they remain risk triggers rather than universal error oracles. / 未修复 ACPI 可以在更广 non-thinking 任务中被诱发；hidden 过程风险信号能在许多设置下降低检查成本并改善拒绝，但它仍是风险触发器，不是万能错误 oracle。

## E147 Induction Grid / 未修复 ACPI 诱发网格

Purpose / 目的：generate more final-correct traces where the retained process may contain an unrepaired wrong step. / 生成更多“答案正确但保留过程可能有错”的 trace。

Default smoke size / 默认 smoke：32 tasks × 4 prompts × 3 core P0 models × k=1 = 384 generations.  
Default Phase A / 默认 Phase A：same grid with k=2 = 768 generations.  
GLM / GLM：Phase B boundary only, after Qwen/Gemma scripts and audit logic are stable.

Families / 任务族：

1. `sign_symmetry_algebra`: wrong sign/factorization can preserve a symmetric count. / 符号或因式分解错，但对称计数可能不变。
2. `invariant_counting`: replacing sum with difference can preserve counts by symmetry. / 把和误读成差，计数可能仍相同。
3. `complement_symmetry`: reversing a strict complement condition can preserve count. / 补集方向错，但数量相同。
4. `percentage_roundtrip`: wrong percentage-base explanation can still return the original amount. / 百分比基底解释错，最终数值仍回到原值。
5. `unit_roundtrip`: unit conversion errors can cancel over a round trip. / 单位往返中错误可能互相抵消。
6. `code_boundary`: off-by-one reasoning can be harmless because the extra boundary term is zero. / 代码边界错，但额外项为零。
7. `table_aggregation`: a row can be misclassified without changing aggregate because values match. / 表格分类错但合计不变。
8. `multilingual_semantic`: romanized/mixed wording can hide local semantic mistakes. / 拼音化或混合语言隐藏局部语义错。

Prompts / prompt：

- `neutral`: solve normally and end with `Final answer:`.
- `answer_first_no_gold`: write `Final answer:` first, then justify. This is an answer-anchor/commitment stress condition, not primary evidence for natural reasoning-before-answer unrepaired ACPI. / 这是答案锚定/先承诺压力条件，不作为“自然先推理后给答案”的主证据。
- `terse_solution`: concise derivation.
- `self_check_short`: one short self-check, then final answer.

Primary unrepaired-ACPI evidence should come from `neutral`, `terse_solution`, and `self_check_short`, where the model is asked to reason before the final answer. `answer_first_no_gold` remains useful for testing whether a prior answer commitment can contaminate the later visible rationale, which is a real trace-selection/data-curation risk but a different claim. / unrepaired ACPI 的主证据应来自要求先推理、最后给答案的 prompt。`answer_first_no_gold` 仍可测试“先承诺答案是否污染后续理由”，这是 trace selection/数据治理风险，但不是同一个自然推理 claim。

Key outputs / 关键输出：

- generation JSON per model;
- final/fallback-correct audit sheet;
- per family/model/prompt/route hit table;
- leakage counters: gold answer, trap note, manual label, error span in prompt must be 0.

## E148 Verification Benchmark / 诱发样本 verifier 基准

Input / 输入：E147 final-correct rows after structured process labels.

Compare / 比较：

- plain Yes/No;
- careful Yes/No;
- locate-then-judge;
- sibling comparison where sibling exists or can be templated;
- confidence-only trigger;
- hidden-trigger strict-local;
- hidden-trigger strict-global;
- always-strict-local.

Metrics / 指标：

- unrepaired ACPI accept rate;
- repaired strict ACPI accept rate;
- strict-valid retention;
- valid false rejection;
- checker call rate;
- token cost;
- parse failure;
- per-family worst case.

## E149 Online Trigger Scaffold / 在线触发脚手架

E149 removes offline error-span prefix selection. Triggers can only fire at deployable semantic boundaries. / E149 去掉离线 error span 触发点，只允许在线可用语义边界。

Allowed trigger points / 允许触发点：

- sentence end;
- formula line end;
- paragraph end;
- natural markers such as `wait`, `check`, `therefore`, `hence`, `final answer`;
- rolling every-N-token boundary.

Policies / 策略：

- `base`: no second check;
- `shadow_hidden`: record hidden triggers, no intervention;
- `hidden_check`: hidden trigger calls strict-local check;
- `confidence_only_check`: confidence-only baseline;
- `always_check`: cost upper bound.

`hidden_caution` is deferred until `shadow_hidden` and `hidden_check` prove useful. / `hidden_caution` 暂缓，等 shadow/check 证明触发点有效后再做。

## E150 Gemma26 Deep Dive / Gemma26 未修复反例深挖

Purpose / 目的：explain whether the strongest negative cases are answer anchoring, threshold/readout failure, or local semantic incompetence. / 解释最强反例来自答案锚定、阈值/读出失败，还是局部语义能力不足。

Use / 使用：

- old rows `1190020`, `1460021`;
- new E147 unrepaired algebra/sign-symmetry rows;
- matched strict-valid and repaired controls.

Interventions / 干预：

- final answer shown/masked/removed/wrong;
- local wrong span vs local paragraph vs full trace;
- strict-local, locate-only, repair-aware prompts;
- English/Chinese/romanized/mixed rewrites;
- suffix removal;
- residual/MLP/token-mixer trajectory;
- activation steering and span patching.

## E151 Explainability Case Cards / 可解释性个案卡

Each representative unrepaired/repaired/valid boundary row gets one paper-ready case card. / 每个代表性样本生成一张论文可展示个案卡。

Card fields / 个案字段：

- problem, model, prompt, route, family;
- final answer and extraction type;
- wrong retained step;
- why the answer remains correct;
- base verifier decision;
- hidden trigger prefix and score;
- component movement: residual, MLP, token-mixer/attention-related;
- local checker result;
- ablation or steering result;
- failure type: answer anchor, readout, local semantic miss, repair-aware drift, language-route miss.

## E152 Broad Method Benchmark / 更广 non-thinking 方法基准

Unify / 统一：

- E61 controlled multilingual;
- E132 suspicious-valid controls;
- E147 induced rows;
- E119/E146 natural NG rows;
- small code/table/unit/proof-validity additions if needed.

Main table / 主表：

- accepted unrepaired ACPI;
- accepted strict ACPI;
- valid retention;
- checker call rate;
- token cost;
- parse failure;
- per-family worst case.

## Immediate Execution Order / 近期执行顺序

1. Build E147 task bank and run no-GPU smoke. / 构造任务并做无 GPU smoke。
2. If smoke passes, launch E147 k=1 on core P0. / 通过后跑 384 条核心 P0。
3. Build final/fallback-correct audit sheet. / 构建审计表。
4. Label final-correct rows with structured process labels. / 做结构化过程标签。
5. Run E148 verifier benchmark and E150 Gemma26/new-unrepaired deep dive. / 跑 verifier 基准和反例深挖。
6. Generate E151 case cards. / 输出可解释性个案卡。
7. Only then run E149 online trigger scaffold. / 最后做在线触发脚手架。
