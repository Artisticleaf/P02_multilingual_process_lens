# Thinking-Mode Audit and Rerun Plan / thinking 模式审计与重测计划（2026-04-29）

## 0. Executive Conclusion / 核心结论

中文：现有结论必须按推理模式重新分层。受控 verifier/objective 结果主要是 `direct-answer verifier` 条件：脚本用官方 chat template，但显式关闭 thinking，让模型直接给 `Yes/No` 或 `A/B`，便于 option-logprob、hidden state 和组件激活诊断。这些结果仍然有效，但主张只能写成“direct verifier interface 下的 trace-selection 风险”。自然生成结果里，E57/E88 等主要 hard-task 样本使用了 `thinking=false`，所以不能作为 thinking-mode reasoning model 的自然发生率主证据，必须降级为 non-thinking generation 条件结果。当前 thinking-mode 自然证据不足，需要进入 thinking 实验阶段。

English: Existing claims must be mode-scoped. Most controlled verifier/objective results are `direct-answer verifier` experiments: official chat templates are used, but thinking is disabled so that the model directly emits `Yes/No` or `A/B`, enabling option-logprob, hidden-state, and component diagnostics. Those results remain valid, but only as direct-verifier-interface evidence. Hard-task natural generation results such as E57/E88 mainly used `thinking=false`, so they cannot serve as primary evidence for thinking-mode reasoning-model prevalence. They must be downgraded to non-thinking generation results. We now need a dedicated thinking-mode phase.

## 1. Mode Taxonomy / 模式分类

| code | name | plain-language meaning | current scientific use |
|---|---|---|---|
| `DV` | direct-answer verifier | 关闭 thinking，让模型在 assistant 起点直接回答 `Yes/No`、`A/B` 或固定选项；适合 logprob/margin/hidden-state 控制。 | 证明 direct verifier objective/threshold/readout 会错配；不是 thinking verifier。 |
| `TV` | thinking verifier | 开启 thinking，模型先生成思考，再给最终 `Yes/No`、`A/B` 或自然语言判定；必须解析最终决策。 | 目前主线基本未完成，需要重测。 |
| `NG` | non-thinking generation | 关闭 thinking 让模型直接写解题过程和答案。 | 现有 E57/E88 hard-task 自然样本属于这一类，结论需条件化。 |
| `TG` | thinking generation | 开启 thinking 让模型按官方 reasoning 模式解题。 | 当前只有少量 E49/E64 证据，不足以支撑主 claim，需要新阶段。 |
| `MI-DV` | mechanism under direct verifier | 在 `DV` prompt 上读 hidden/residual/MLP/token-mixer 或做 steering。 | 证明 direct verifier prompt 内有过程证据；不等于 thinking 生成路径机制。 |
| `PM` | post-hoc meta-analysis | 读取已有结果做筛选器模拟、统计、发生率汇总。 | 依赖源结果模式；必须分 thinking/non-thinking 分开汇总。 |

## 2. Reclassified Claims / 重新分类后的 claim

### 2.1 Direct-answer verifier claim / 直接判定 verifier claim

Supported by E42/E53/E54/E60/E61/E71/E79/E80/E81/E82/E84/E86 and related hidden diagnostics.

中文安全表述：在 direct-answer verifier interface 下，多语言/表层语义与过程语义错配会产生 strict ACPI trace-selection 风险；pointwise `Yes/No` verifier 会过度接受一部分答案正确但过程无效的 trace；sibling、label-free 和 hidden-state 诊断能更好暴露过程信号。

边界：这不是 thinking verifier 的结论。开启 thinking 后，模型可能先内部检查再作答，接受率可能变化，必须单独测。

### 2.2 Non-thinking generation claim / 非 thinking 生成 claim

Supported by E48/E57/E88 and older E46/E47-style generation diagnostics.

中文安全表述：在 non-thinking/direct generation 条件下，简单自然任务目前未检出 ACPI；hard-task 中 strict ACPI 低到中等，主要来自 answer-first 格式的先错后修；unrepaired ACPI 低频但出现过。

边界：不能写成“thinking reasoning models 自然 unrepaired ACPI 低频/高频”。E57/E88 的 hard-task 主样本使用了 `thinking=false`。

### 2.3 Thinking generation claim / thinking 生成 claim

Current evidence is insufficient. E49 `auto` runs and E64 GLM run contain thinking-mode generation evidence, but coverage is uneven and underpowered.

中文安全表述：目前不能对 thinking-mode P0 模型的自然 ACPI 发生率作 headline 结论。下一阶段要重跑 hard-task/simple natural generation，并按 strict/repaired/unrepaired 人审。

### 2.4 Mechanism claim / 机制 claim

Supported primarily under `MI-DV`: E50/E55/E56/E65/E78/E84/E90.

中文安全表述：在 direct verifier prompt 下，hidden residual、MLP/post-feedforward、token-mixer/attention-related activations 含有过程有效性证据；但是这还没有证明 thinking generation 的内部修复路径，也不是完整 named circuit。

下一步要捕捉 thinking trace 中 thought tokens、final decision token、repair marker 附近的 residual/MLP/attention 激活。

## 3. Existing Result Traversal / 已有实验按模式遍历

| experiment group | current mode | current conclusion status | rerun in thinking? | priority | reason |
|---|---|---|---|---:|---|
| E42 official template parity | `DV` | direct Yes/No over-accept vs sibling exposure is valid as direct-verifier evidence. | Yes, as `TV` | P0 | 核心受控现象必须确认 thinking verifier 是否仍过度接受。 |
| E53 answer-anchor ablation | `DV` | final answer anchoring is supported under direct verifier. | Yes, subset | P0 | 需要知道 thinking verifier 是否仍被答案锚定，或是否通过思考消除锚定。 |
| E54 parameterized generalization | `DV` | 18-family generalization valid under direct verifier. | Yes, representative subset | P0 | 顶会主张需要证明不是 direct-interface 特例。 |
| E60 objective ladder | `DV` | careful/answer-blind/locate reduce risk under direct verifier. | Yes, redesigned | P0 | thinking verifier 不能用 first-token logprob，必须生成最终判定并解析。 |
| E61 language-route/error-taxonomy grid | `DV` | broad multilingual/error taxonomy evidence valid under direct verifier. | Yes, core grid or stratified sample | P0 | 当前最强泛化证据，需要 thinking-mode 对照。 |
| E48 simple natural prevalence | `NG` for chat P0 | simple no-leak natural ACPI not observed under non-thinking generation. | Yes | P0 | 简单任务也要确认 thinking generation 是否改变自然过程错误率。 |
| E49 initial hard-task pilots | mixed; some `TG` via `auto=True` | underpowered/older, not enough for headline. | Replace by new TG run | P0 | 作为新阶段 smoke seed，不作为最终结论。 |
| E57 P0 hard-task harvesting | `NG` | hard-task repaired/unrepaired counts are non-thinking-condition evidence. | Yes | P0 | 必须用 thinking mode 重采样后再写自然 hard-task 主结论。 |
| E64 GLM hard-task expansion | `TG` for GLM | GLM thinking-mode hard-task found no ACPI in 8 final-correct rows. | Extend to all P0 | P0 | 这是少数 thinking 证据，但模型覆盖不足。 |
| E83 pooled prevalence audit | `PM` over mixed NG/TG | pooled rate mixed modes, must not be used unqualified. | Recompute after TG runs | P0 | 统计表必须拆分 `NG`/`TG`。 |
| E88 answer-first hard-task sample | `NG` | high strict ACPI mostly answer-first repaired artifacts; unrepaired 1/192. | Yes, but include neutral/self-check too | P0 | 不能把 non-thinking answer-first 当 thinking natural prevalence。 |
| E71 strict vs repair-aware | `DV` | strict vs repair-aware objective distinction supported under direct verifier. | Yes | P0 | thinking verifier 可能天然 repair-aware，需要直接测。 |
| E80 progressive-prefix replay | `DV` + MI-DV | repair marker changes direct verifier Yes/No and hidden projections. | Yes, thinking verifier/generation version | P0 | 要判断模型“看到修复标记后如何读 trace”是否依赖 non-thinking direct decision。 |
| E82 unrepaired case ablation | `DV` | final anchor strong but not all; local algebra subtle. | Yes | P0 | 两条/一条 unrepaired 个案必须经 thinking verifier 复核。 |
| E86 algebra boundary | `DV` | short explicit algebra errors are caught by direct strict pointwise. | Yes, smaller | P1 | 作为负控制，看 thinking verifier 是否也抓短显式错误。 |
| E79/E81 label-free sibling | `DV` | label-free/two-pass improves GLM; core P0 robust. | Yes | P0 | thinking final decision可能缓解或改变 A/B readout bottleneck。 |
| E84/E87 GLM readout mediation | MI-DV/PM | GLM hidden/label-free strong, raw A/B weak under direct interface. | Yes, after TV sibling | P0 | GLM 是最强 readout 错配信号，需 thinking 接口确认。 |
| E50/E55/E56/E65/E78/E90 hidden/mechanism | MI-DV | direct verifier hidden states encode process-validity evidence. | Yes, staged | P0/P1 | thinking 机制不能直接复用 first-token hidden；需捕捉 thought/final decision token。 |
| E58/E68/E89 filter simulations | `PM` | useful but depends on source-mode labels. | Recompute only | P0 | 新 TG/DV-TV 结果落盘后重算。 |
| E59 mutual/self verifier style | `DV` and non-thinking style rewrite | self vs cross evidence is direct-interface style evidence. | Optional | P1 | 可在核心 thinking verifier 稳定后补。 |
| E40/E43/E44 early P1/P2 mechanism controls | mostly `DV`/MI-DV | useful historical controls, not P0 headline. | No immediate rerun | P2 | 优先级低；不应拖慢 thinking 主线。 |
| E62 backend smoke | technical | not a scientific mode result. | No | NA | 仅后端准入。 |
| Qwen2.5-Math archived E49-E52 | archived/P2 | not adopted. | No | NA | 已明确不进入主线。 |

## 4. Thinking-Phase Experiment Plan / thinking 阶段实验计划

| new id | name | source experiments to revisit | models | implementation sketch | expected information |
|---|---|---|---|---|---|
| E91 | Thinking-mode config/parser audit | all P0 chat templates | qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it, glm47_flash_candidate | Render `enable_thinking=True`; verify thought/final delimiters; implement parser for final `Yes/No`, `A/B`, `Final answer`; use official generation params. | 防止把 thinking 输出当 first-token logprob；建立统一可复现设置。 |
| E92 | Thinking hard-task natural harvesting | E57/E88/E64 | all P0 | AIME-style no-gold tasks; variants `neutral`, `answer_first_no_gold`, `self_check`; k>=8; official sampling; manual audit final-correct rows into strict/repaired/unrepaired. | 重新估计 thinking-mode natural strict/unrepaired ACPI。 |
| E93 | Thinking simple-task natural prevalence | E48 | core P0 + GLM | E48 simple no-leak surface-semantic tasks in thinking mode; audit final-correct process validity. | 判断简单任务 0 ACPI 是否只在 non-thinking 下成立。 |
| E94 | Thinking verifier objective ladder | E42/E53/E54/E60/E61 | all P0 | For each trace, ask thinking verifier to inspect then output final `Yes/No`; parse final decision; compare plain/careful/answer-blind/locate/sibling. | 判断 direct-verifier over-accept 是否在 deliberative verifier 中保留。 |
| E95 | Thinking sibling/readout study | E79/E81/E84/E87 | all P0, focus GLM | Generate final A/B decisions with both orders, plus label-free two-pass final Yes/No; compare raw labels, two-order, label-free. | 判断 GLM raw A/B bottleneck是否是 direct logprob 接口特例。 |
| E96 | Thinking strict-vs-repair-aware and hard-case ablation | E71/E80/E82/E86 | all P0 | Use thinking verifier on repaired/unrepaired hard cases and algebra boundary; include final removed/masked/wrong. | 判断 thinking 模型是否默认 repair-aware，以及 unrepaired case 是否仍漏判。 |
| E97 | Thinking mechanism capture | E65/E78/E90 | start Gemma31/Gemma26/GLM | Cache hidden/residual/MLP/token-mixer at prompt end, repair marker, thought tokens, and final decision token; train/probe directions with leakage controls. | 把机制 claim 从 direct verifier prompt 推到 thinking trace/final decision。 |
| E98 | Thinking filter simulation | E58/E68/E83/E89 | post-hoc | Recompute outcome-only, direct-verifier, thinking-verifier, sibling, label-free, strict/repair-aware filters separately. | 给论文 appendix 一张 mode-scoped data governance 风险表。 |
| E99 | Thinking self/cross verifier | E59 | optional all P0 | Source-model generated thinking traces judged by self and cross thinking verifiers, source-blinded. | 判断 self-verifier 合理性是否在 thinking verifier 中仍成立。 |

## 5. Official Parameter Notes / 官方参数记录

- Qwen3.5 local README: thinking mode is default; recommended thinking generation parameters include `temperature=1.0`, `top_p=0.95`, `top_k=20`; non-thinking/instruct is a separate mode. / Qwen3.5 本地 README 明确 thinking 默认开启，non-thinking 是单独直接回答模式。
- Gemma4 local README: thinking is configurable; best-practice sampling is `temperature=1.0`, `top_p=0.95`, `top_k=64`; thinking enabled by `<|think|>` via template. / Gemma4 本地 README 明确可配置 thinking，推荐采样参数如上。
- GLM-4.7-Flash local README: default evaluation setting lists `temperature=1.0`, `top-p=0.95`, large max-new-token budget; vLLM deployment uses a reasoning parser. / GLM README 给出默认评估参数并强调 reasoning parser。

## 6. Immediate Policy / 立即执行规则

1. Any future claim must include mode label: `DV`, `TV`, `NG`, `TG`, `MI-DV`, or `PM`.
2. E57/E88 hard-task prevalence must be cited as `NG` only until E92 finishes.
3. E42/E60/E61 verifier claims must be cited as `DV` only until E94 finishes.
4. Hidden/mechanism claims must be cited as `MI-DV` only until E97 finishes.
5. Post-hoc filter simulations must not mix `NG` and `TG` source pools without a visible stratified table.

