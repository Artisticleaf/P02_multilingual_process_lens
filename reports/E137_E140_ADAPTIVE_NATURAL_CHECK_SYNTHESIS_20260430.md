# E137-E140 Adaptive Natural Check Synthesis / 自适应自然样本检查阶段报告

Date / 日期：2026-04-30

## Scope / 范围

This stage asks whether the hidden process-risk signal found in controlled non-thinking verifier experiments can transfer to natural hard-task traces, and whether a second-pass checker can use that signal to reduce strict ACPI acceptance. / 本阶段检验：受控非 thinking verifier 实验中的 hidden 过程风险信号，能否迁移到自然困难题 trace；以及二次检查器能否利用该信号降低 strict ACPI 接受率。

Artifacts / 文件：

- E137 threshold calibration / 阈值校准：`scripts/run_e137_hidden_trigger_threshold_calibration.py`, `results/E137_hidden_trigger_threshold_calibration/`
- E138 natural hidden-trigger check / 自然样本 hidden 触发检查：`scripts/run_e138_natural_hidden_trigger_check.py`, `results/E138_natural_hidden_trigger_check/`
- E140 natural rationale audit / 自然样本解释式审计：`scripts/run_e140_natural_check_rationale_audit.py`, `results/E140_natural_check_rationale_audit/`

Mode / 模式：all three are `NG`, `thinking=false`. / 三个实验均为非 thinking。

Leakage boundary / 泄露边界：E137 is offline threshold evaluation only. E138/E140 prompts contain only problem, visible trace, and optionally a hidden-trigger-selected visible excerpt; labels, gold answers, and manual error spans are offline only. E138 uses E131 diagnostic prefix availability, which is label-informed offline, so it must not be described as a deployable online monitor. / E137 只做离线阈值评估。E138/E140 的 prompt 只含题目、可见 trace、以及可选的 hidden 触发可见片段；标签、答案、人工错误 span 只离线使用。E138 使用 E131 的诊断前缀，这些前缀有离线人工标签信息，因此不能把 E138 描述成可部署的实时监控器。

## E137 Threshold Calibration / 阈值校准

E137 calibrates a hidden-trigger threshold on E132/E133 controlled rows. The score is the minimum prefix process-validity projection; lower scores mean stronger process-risk signal. / E137 在 E132/E133 受控行上校准 hidden 触发阈值。分数取前缀过程有效性投影的最小值；分数越低，过程风险越强。

| Model | Threshold=0 invalid recall | Threshold=0 valid false trigger | Chosen threshold | Chosen invalid recall | Chosen valid false trigger | Note |
|---|---:|---:|---:|---:|---:|---|
| Qwen3.5-27B | 12/12 = 1.000 | 2/48 = 0.042 | -5.170 | 12/12 = 1.000 | 0/48 = 0.000 | Clean on controlled rows, but chosen threshold later over-transfers. / 受控行干净，但自然迁移时过保守。 |
| Gemma4-31B-it | 12/12 = 1.000 | 0/48 = 0.000 | 0.000 | 12/12 = 1.000 | 0/48 = 0.000 | Cleanest threshold behavior. / 阈值行为最干净。 |
| Gemma4-26B-A4B-it | 12/12 = 1.000 | 6/48 = 0.125 | -4.193 | 12/12 = 1.000 | 3/48 = 0.062 | No threshold satisfies the planned strict FP constraints. / 没有阈值同时满足预设低误报约束。 |

Plain fact / 说人话事实：Qwen and Gemma31 show a clean controlled hidden signal. Gemma26 also catches all controlled invalid rows, but it triggers more often on suspicious-but-valid controls, so its hidden signal is not an oracle and needs calibration. / Qwen 和 Gemma31 的受控 hidden 信号很干净；Gemma26 也能抓住全部受控 invalid，但会更多误触发正确控制组，因此不是 oracle。

## E138 Natural Hidden-Trigger Check / 自然样本 hidden 触发检查

E138 transfers E137 thresholds to natural final-correct hard-task rows from E119/E146. It compares base pointwise acceptance with triggered second-pass checks. / E138 把 E137 阈值迁移到 E119/E146 的自然困难题 final-correct 行，比较基线 pointwise 接受和 hidden 触发后的二次检查。

Core aggregate / 核心汇总：

| Model | Rows | Invalid rows | Valid rows | Base invalid accept | Zero-threshold trigger | E137-threshold trigger | Best strict-local invalid accept |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | 24 | 19 repaired | 5 | 2/19 = 0.105 | 20/24 = 0.833 | 3/24 = 0.125 | zero strict-local: 0/19 = 0.000 |
| Gemma4-31B-it | 26 | 16 repaired | 10 | 6/16 = 0.375 | 17/26 = 0.654 | 17/26 = 0.654 | strict-local: 2/16 = 0.125 |
| Gemma4-26B-A4B-it | 16 | 8 repaired + 2 unrepaired | 6 | 6/10 = 0.600 | 14/16 = 0.875 | 8/16 = 0.500 | strict-local: 5/10 = 0.500 |

Important details / 关键细节：

- Qwen: threshold 0 triggers all 19 repaired ACPI rows and one valid row; strict-local recheck reduces invalid acceptance from 2/19 to 0/19 while keeping valid acceptance 5/5. The E137 chosen threshold is too conservative on natural rows and triggers only 3/19 repaired rows. / Qwen 的 0 阈值自然迁移好；E137 选择阈值在自然样本中过保守。
- Gemma31: threshold 0 triggers all 16 repaired ACPI rows and 1/10 valid rows; strict-local reduces invalid acceptance from 6/16 to 2/16. Default-local is worse than base because it reads repaired CoT more permissively. / Gemma31 支持 strict 二次检查，但 default-local 会按可修复草稿读，反而更宽。
- Gemma26: threshold 0 triggers all invalid rows including the two unrepaired ACPI rows, but strict-local still accepts both unrepaired cases and many repaired cases. E137 chosen threshold misses the unrepaired rows entirely. / Gemma26 的 hidden 触发能响，但二次语义检查仍放过关键 unrepaired 两例；校准阈值还会漏掉它们。

Plain fact / 说人话事实：for Qwen and Gemma31, natural repaired ACPI often has a hidden risk signal, and a strict second-pass objective can use it. For Gemma26, the hidden trigger alone is not enough: the model may still fail to understand or enforce the local algebra error. / 对 Qwen 和 Gemma31，自然 repaired ACPI 常有 hidden 风险信号，strict 二次检查能利用它；对 Gemma26，仅有 hidden 触发不够，它可能仍无法理解或执行局部代数错误检查。

## E140 Natural Check-Rationale Audit / 自然样本解释式审计

E140 asks the same model to explain the second-pass judgment on selected E138 rows, separating strict trace-as-proof and repair-aware final-surviving-proof decisions. / E140 要求同一模型解释 E138 选中样本上的二次判断，并区分 strict trace-as-proof 和 repair-aware final-surviving-proof 两种口径。

| Model | Audit jobs | Parse OK | Error recognized | Strict accept | Repair-aware accept | Main failure mode |
|---|---:|---:|---:|---:|---:|---|
| Qwen3.5-27B | 8 | 8/8 | 8/8 = 1.000 | 0/8 = 0.000 | 5/8 = 0.625 | Sees error; repair-aware accepts. / 能看见错，但 repair-aware 接受。 |
| Gemma4-31B-it | 20 | 20/20 | 8/20 = 0.400 | 12/20 = 0.600 | 20/20 = 1.000 | Often says no wrong step; always repair-aware accepts. / 常说没错，且总按 repair-aware 接受。 |
| Gemma4-26B-A4B-it | 20 | 20/20 | 2/20 = 0.100 | 15/20 = 0.750 | 19/20 = 0.950 | Mostly no error seen; unrepaired cases all missed. / 大多没看见错误；unrepaired 全漏。 |

Unrepaired boundary / 未修复边界：Gemma26 has 4 E140 audit jobs over the two unrepaired ACPI rows. It recognized 0/4 errors, gave strict Yes 4/4, and repair-aware Yes 4/4. The explanations say the wrong factorization/case analysis is correct. / Gemma26 两条 unrepaired ACPI 的 4 个审计任务中，错步识别 0/4，strict 接受 4/4，repair-aware 接受 4/4；解释文本把错误因式分解/分类讨论说成正确。

Plain fact / 说人话事实：E140 separates two failure types. Qwen mostly has the evidence and can explain the wrong step, but a repair-aware reading still accepts. Gemma31 is mixed: local scope helps, yet it often fails to name the wrong step. Gemma26 unrepaired rows are a deeper semantic local-check failure, not just a Yes/No readout issue. / E140 把失败分成两类：Qwen 多数能看到并解释错步，但 repair-aware 口径仍接受；Gemma31 介于中间；Gemma26 的 unrepaired 例子是更深的局部语义检查失败，不只是 Yes/No 读出问题。

## Claim Update / 主张更新

Supported / 支持：

- Natural repaired ACPI traces in Qwen/Gemma31 carry hidden process-risk signals; those signals can be used by a strict second-pass checker to reduce over-acceptance. / Qwen/Gemma31 的自然 repaired ACPI 中存在 hidden 过程风险信号，strict 二次检查能利用它降低过度接受。
- The major failure is not always absence of evidence. E139.5 and E140 show models can often localize or describe the wrong step, but the final objective/readout can still treat the CoT as a repairable draft. / 主要失败不总是“没有证据”；模型常能定位或描述错步，但最终 objective/readout 可能仍把 CoT 当可修复草稿。
- Suspicious-but-valid controls matter. E137 shows Qwen/Gemma31 can separate many suspicious correct traces from invalid traces, while Gemma26 has higher false triggers. / 可疑但正确控制组很重要；Qwen/Gemma31 能较好区分，Gemma26 误触发更高。

Boundaries / 边界：

- E138 is diagnostic, not deployable online monitoring, because its prefix set comes from E131 offline analysis. / E138 是诊断实验，不是可部署在线监控。
- Thresholds do not transfer perfectly. Qwen's E137 threshold is clean on controlled rows but misses many natural repaired ACPI rows. / 阈值迁移不完美；Qwen 的 E137 阈值在自然样本中过保守。
- Gemma26 unrepaired ACPI remains the strongest negative case: hidden trigger can fire, but both global/local rationale checks still accept. / Gemma26 未修复 ACPI 是最关键反例：hidden 触发了，但全局/局部解释式检查仍接受。

Current revised claim / 当前修订 claim：

Controlled strict ACPI risk is robust, and natural hard-task repaired ACPI often exposes hidden residual/process-risk signals. In stronger P0 models, a strict second-pass objective can use those signals to reject traces that a pointwise verifier may over-accept. However, the signal is not a complete error oracle: threshold transfer, language route, repair-aware reading, and local semantic competence determine whether hidden evidence becomes a correct verifier decision. / 受控 strict ACPI 风险稳健，自然困难题 repaired ACPI 常暴露 hidden residual/process-risk 信号。在更强 P0 模型中，strict 二次检查可利用这些信号拒绝 pointwise verifier 可能过度接受的 trace。但该信号不是完整错误 oracle：阈值迁移、语言路径、repair-aware 阅读和局部语义能力，决定 hidden 证据是否能转化成正确 verifier 决策。

## Next Experiments / 下一步实验

- E141 taxonomy from E140 / 基于 E140 做失败分类：no new GPU needed; sample rationales and classify whether failures are no-error-seen, repair-aware accept, final-answer anchor, or local algebra miss. / 不需要 GPU，抽样解释文本做失败类型表。
- E142 online trigger scaffold / 在线触发脚手架：remove label-informed prefixes and trigger from deployable prefix points such as sentence boundaries, repair markers, final-answer markers, and rolling hidden scores. / 去掉离线错误 span，改用可部署前缀点。
- E144 caution-token intervention / 警示 token 干预：when a hidden risk signal fires during prefill or generation, insert a short caution/check instruction and test whether non-thinking checking improves without always using long CoT. / hidden 风险出现时插入短警示，测试非 thinking 是否能低成本改善。
- Gemma26 unrepaired deep dive / Gemma26 未修复深挖：activation steering or stricter local algebra prompts should test whether the unrepaired failure is threshold, readout, or missing semantic competence. / 通过激活 steering 或更严格局部代数 prompt 区分阈值、读出和语义能力问题。
