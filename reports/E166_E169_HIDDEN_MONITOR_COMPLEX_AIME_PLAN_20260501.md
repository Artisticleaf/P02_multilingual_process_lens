# E166-E169 Hidden-Monitor Localized Repair Plan / hidden monitor 局部修复计划

Date / 日期：2026-05-01

## Bottom Line / 说人话结论

The proposal is scientifically reasonable and should become the next main line, but only if `localized` is derived from the hidden monitor, not from human spans. / 这个方案合理，而且应成为下一条主线；但前提是 `localized` 必须来自 hidden monitor，而不是人工给错步。

Current E162/E165 `localized_error_prompt` is a behavioral upper bound: the span is human/manual or construction-known. / 当前 E162/E165 的 localized 是行为上界：span 来自人工审计或构造时已知错步。

The new experiments should test whether a hidden monitor can:

1. detect suspicious prefix positions from residual/MLP/token-mixer states;
2. map the trigger to a visible local span without oracle labels;
3. trigger a non-thinking continuation that repairs traces better or cheaper than generic/random controls;
4. rescue some AIME26 traces that the same model initially solved incorrectly.

## Definitions / 定义

- Hidden monitor / 隐藏监测器：a model-specific scorer that reads hidden residual, MLP output, token-mixer/attention-related output, optional norm output, entropy, and logprob features after a causal prefill prefix. / 在因果 prefill 后读取 hidden residual、MLP、attention/token-mixer、norm、entropy、logprob 等特征并给出风险分数的监测器。
- Hidden-derived localized span / 隐藏导出的局部 span：the visible sentence/formula around the first prefix boundary whose hidden risk crosses a pre-registered threshold. / 第一个超过预注册风险阈值的 prefix 边界附近的可见句子或公式。
- Not oracle / 不是 oracle：manual error span and gold answer are used only for offline evaluation, never to choose the intervention position on target tasks. / 人工错步和答案只用于离线评价，不能用于目标任务选择干预位置。
- Causal prefill / 因果 prefill：the monitor score at prefix `t` uses only tokens up to `t`; later generated tokens are not visible to that score. / prefix t 的分数只能用 t 以前的 token，不能看后文。

## Experiment Structure / 实验结构

### E166. Hidden Monitor Calibration on Hardened Multi-Family Bank

Inputs / 输入：

- Task bank: `data/processed/e164_hardened_multi_family_tasks_20260501.jsonl`.
- Candidate traces: `data/processed/e164_hardened_multi_family_candidate_solutions_20260501.jsonl`.
- Repair cases: `data/processed/e165_hardened_multi_family_repair_cases_20260501.jsonl`.

Design / 设计：

- Split each valid, invalid-answer-correct, and invalid-answer-wrong trace into step boundaries. / 把每条 trace 切成步骤边界。
- Teacher-force replay each prefix. / 对每个 prefix 做 teacher-forced replay。
- Save component features at selected layers: residual hidden state, MLP output, token-mixer/attention output, and norm outputs. / 保存 residual、MLP、attention/token-mixer 和 norm。
- Train simple monitor directions on controlled prefixes: invalid local step vs valid corresponding step. / 用受控题训练简单风险方向。
- Use leave-one-family-out and leave-one-trap-type-out validation. / 做留一 family 和留一错误类型验证。

Primary monitor / 主监测器：

- Start with best-layer residual score because it has the strongest previous evidence. / 先用 best-layer residual，因为历史结果最稳。
- Then test ensemble score: residual + MLP + token-mixer + entropy/logprob anomaly. / 再测试 residual、MLP、token-mixer、entropy/logprob 的 ensemble。

Calibration rule / 阈值规则：

- Choose thresholds on E166 only, not on AIME. / 阈值只在 E166 上定，不能在 AIME 上调。
- Pre-register two policies: `high_precision` with valid false trigger <=10%, and `budgeted_trigger` with trigger rate around 20-30%. / 预注册高精度和预算触发两种策略。

Metrics / 指标：

- Top-1 and top-k overlap with manual error span. / 与人工错步 top-1/top-k 重合。
- First-trigger distance from true error. / 首次触发距离真实错步多远。
- Valid false-trigger rate. / 正确过程误触发率。
- Family transfer performance. / 跨 family 泛化。

### E167. Hidden-Derived Localized Repair on Complex/Multi-Error Bank

Design / 设计：

- Use monitor-selected first trigger, not manual span. / 用 monitor 选出的首次触发点，不用人工 span。
- Truncate the trace at that prefix. / 在该 prefix 截断。
- Continue in non-thinking mode under six controls. / 在 non-thinking 下运行六种条件。

Prompt conditions / prompt 条件：

1. `baseline_regenerate`: solve from the original problem. / 从题目重做。
2. `prefix_continue`: continue from the truncated prefix, no warning. / 从截断 prefix 直接续写。
3. `hidden_generic_warning`: monitor says something nearby is low-confidence, no span. / 只说附近低置信。
4. `hidden_localized_warning`: monitor quotes the visible span around the trigger. / 引用 hidden 触发附近的可见 span。
5. `random_matched_warning`: same warning style at matched random prefix/span. / 同样格式的随机位置对照。
6. `oracle_manual_span`: human span upper bound, reported separately. / 人工错步上界，单独报告。

Metrics / 指标：

- Final accuracy and strict process validity. / 最终答案正确率和严格过程有效性。
- Repair success on invalid-answer-wrong traces. / 错答案 trace 是否被修对。
- Preservation/correction on invalid-answer-correct ACPI traces. / 过程错答案对 trace 是否改正过程且不破坏答案。
- Completion-token cost per successful repair. / 每次成功修复 completion token 成本。
- Localized-only advantage over generic and random. / hidden-localized 相对 generic/random 的差分收益。
- False correction on valid prefixes. / 正确 prefix 是否被误改。

### E168. AIME26 Baseline Failure Harvest

Purpose / 目的：

Test whether hidden monitor can rescue tasks the model originally could not solve, not merely polish easy controlled traces. / 测 hidden monitor 是否能救回模型原本不会做的题，而不只是修受控简单 trace。

Models / 模型：

- `qwen35_27b`
- `gemma4_31b_it`
- `gemma4_26b_a4b_it`

Source policy / 题源策略：

- Build a verified AIME26 I/II task bank from public post-contest sources. / 从赛后公开来源构造 AIME26 I/II 题库。
- Store source URL, contest, problem id, and answer key metadata. / 保存来源 URL、场次、题号、答案元数据。
- Prompts contain problem text only; answers and solution notes are offline scoring metadata. / prompt 只含题面，答案和解析只离线评分。
- Because AIME26 is public by 2026-05-01, contamination must be tracked. / AIME26 已公开，必须记录污染风险。

Baseline definition / “不会做”的定义：

- Deterministic non-thinking baseline: temperature 0, max_new_tokens high enough, final marker required. / 确定性 non-thinking 基线。
- A model-task pair enters rescue only if baseline final answer is wrong, missing, or hit-max without final marker. / 只有 baseline 错、缺 final 或 hit-max 才进 rescue。
- Optional robust failure: k=3 sampled baselines all wrong. / 可加更严格版本：k=3 全错。

### E169. AIME26 Hidden-Triggered Non-Thinking Rescue

Triggering / 触发：

- Replay the failed baseline trace prefix by prefix. / 对失败 baseline trace 做逐 prefix replay。
- Use the pre-registered E166 monitor threshold. / 用 E166 预注册阈值。
- Select the first crossing as the intervention point. / 第一次过阈值作为干预点。
- The selected warning span is the visible sentence/formula around that trigger. / warning span 是触发点附近可见句子/公式。

Interventions / 干预：

1. `prefix_continue_no_warning`
2. `hidden_generic_warning`
3. `hidden_localized_warning`
4. `random_matched_warning`
5. `oracle_human_error_span` as upper bound only after human audit
6. `baseline_regenerate_same_budget`

Success criteria / 成功标准：

- Primary: wrong-to-correct conversion on model-task pairs where baseline failed. / 主指标：baseline 失败的模型-题目对被转成正确答案。
- Secondary: process audit confirms the correction is not just final-answer guessing. / 次指标：过程审计确认不是瞎猜答案。
- Cost: hidden-localized succeeds with fewer completion tokens than full regenerate or generic recheck. / 成本：hidden-localized 比从头重做或泛泛重审更省 completion token。
- Specificity: random matched warning does not achieve the same rescue rate. / 特异性：随机位置不能达到同等救回率。

## Key Risks / 主要风险

- Hidden monitor may detect symptoms, not root causes. / hidden monitor 可能抓到症状而非根因。
- AIME26 may be contaminated in pretraining; requiring baseline failure reduces but does not remove this concern. / AIME26 可能有预训练污染；baseline 失败能降低但不能消除问题。
- A model may need a global new solution, not local repair. / 有些题需要整体重解，不是局部修复能解决。
- Random/generic warnings may trigger global re-solving, especially in Qwen. / random/generic 可能诱发全局重解，尤其 Qwen。
- MoE Gemma should be reported separately because routing instability may affect monitor scores. / MoE Gemma 因路由不稳定应单独报告。

## Decision / 决策

Proceed, but in order:

1. E166 hidden monitor calibration on hardened controlled bank. / 先在加难受控题库校准 hidden monitor。
2. E167 hidden-derived localized repair on complex/multi-error bank. / 再做 hidden-derived localized 修复。
3. E168 AIME26 baseline failure harvest. / 再筛 AIME26 中模型原本不会做的题。
4. E169 AIME26 hidden-trigger rescue. / 最后做 AIME26 hidden-trigger rescue。

Do not run AIME rescue before E166/E167 pass; otherwise a positive result would be hard to interpret. / E166/E167 没通过前不要直接跑 AIME rescue，否则正结果也难解释。
