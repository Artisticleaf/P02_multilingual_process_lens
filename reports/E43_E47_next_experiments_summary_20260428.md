# E43-E47 Next Experiments Summary / E43-E47 下一阶段实验汇总

Date / 日期: 2026-04-28 CST

## 0. Evaluation audit gate / 先过评估设置审计

Before these experiments, the evaluation-setting audit was completed and passed. / 在这些实验前，已完成并通过评估设置审计。

- Appendix / 附录：`reports/APPENDIX_EVAL_SETTING_AUDIT_20260428.md`.
- Machine audit / 机器审计：`logs/audit_eval_settings_appendix_20260428.json`, passed. / 已通过。
- Project check / 项目检查：`logs/check_project_eval_audit_20260428.json`, passed. / 已通过。
- Important fixes / 关键修正：official chat-template hidden patch now uses `add_special_tokens=False`; Qwen35-9B layer configs now use legal 32-layer IDs `[0, 4, 8, 12, 14, 16, 20, 24, 28, 31]`. / 官方 chat 模板 hidden patch 已避免重复 special token；Qwen35-9B 层号配置已修正。

Interpretation / 解释：historical raw-prompt results are still usable as a named stress-test setting, but chat/post-trained model main results should use official templates. / 历史 raw prompt 结果仍可作为压力测试，但 chat/post-trained 模型的主结果应使用官方模板。

## 1. E43 paraphrase-transfer residual patch / E43 跨改写 residual patch

Question / 问题：E40 的 hidden process evidence 是不是只绑定某个固定词面片段？如果换一种说法，同一类过程语义还能不能迁移？ / E40 的隐藏过程证据是否只是词面 artifact？换表述后同一语义能否迁移？

Design / 设计：six families, two paraphrases per family, valid/invalid siblings for each paraphrase. Donor vectors come from the other paraphrase. Negative control uses a mismatched-family donor. / 6 类任务，每类 2 个改写，每个改写一对 valid/invalid sibling。用另一个改写作 donor；负控用错配家族 donor。

Files / 文件：`data/processed/e43_paraphrase_transfer_20260428.jsonl`, `configs/e43_paraphrase_transfer_pairs.yaml`, `results/E43_paraphrase_transfer_patch/`.

| model / 模型 | prompt setting / prompt 设置 | same-family clean best | same-family mean score | mismatched clean best | mismatched mean score | plain fact / 人话事实 |
|---|---|---:|---:|---:|---:|---|
| Qwen35-9B | official chat, no duplicate special tokens | 12/12 | 5.677 | 12/12 | 6.292 | Cross-paraphrase transfer is strong, but mismatched-family transfer is also strong. / 跨改写很强，但错配家族也很强。 |
| Qwen3-14B-Base | raw base prompt | 12/12 | 2.927 | 11/12 | 3.437 | Same pattern: transfer exists, but it is not family-specific. / 同样存在迁移，但不是家族特异。 |

Scientific interpretation / 科学解释：E43 supports that hidden residual states carry a reusable valid-vs-invalid process signal, but it does not yet prove a family-specific semantic feature. The mismatched-family control being as strong or stronger means the current intervention may be picking up a broad “this reasoning is valid/invalid” direction rather than “without replacement” or “strict interval” as a specific concept. / E43 支持 residual state 中有可复用的有效/无效过程信号，但还不能证明找到了某个家族特异的语义 feature。错配家族同样强，说明当前干预更可能抓到宽泛的“过程有效/无效”方向，而不是某个特定概念。

## 2. E44 MLP direction steering / E44 MLP 方向 steering

Question / 问题：E41 里看到 MLP 参与，那么能不能用一个 leave-one-family-out 的 MLP 方向控制 held-out 家族的 verifier 决策？ / MLP 是否有可复用方向能控制留出家族的判断？

Design / 设计：for each held-out family, build `mean(valid support MLP) - mean(invalid error MLP)` from the other five families. On held-out invalid traces, add the direction; on held-out valid traces, subtract it. Controls are random same-norm direction and opposite direction. / 对每个留出家族，用其他 5 个家族构造 `valid support - invalid error` MLP 方向；对留出 invalid 加方向，对留出 valid 减方向；控制为同范数随机方向和反方向。

Files / 文件：`results/E44_mlp_direction_steering/`.

| model / 模型 | prompt setting / prompt 设置 | best process direction, alpha=1 | random control, alpha=1 | opposite control, alpha=1 | flips | plain fact / 人话事实 |
|---|---|---:|---:|---:|---:|---|
| Qwen35-9B | official chat | mean desired effect 0.130, positive 0.917 | 0.076, positive 0.792 | 0.065, positive 0.750 | 1 | Process direction is slightly better than controls but weak. / 过程方向略强于控制，但效应很弱。 |
| Qwen3-14B-Base | raw base prompt | 0.083, positive 0.667 | 0.083, positive 0.667 | 0.078, positive 0.583 | 0 | No reliable steering advantage over random. / 相比随机没有可靠优势。 |

Scientific interpretation / 科学解释：E44 is a boundary result, not a win. MLP participates in E41, but a naive single MLP direction is not yet a convincing reusable causal feature. The safer mechanism claim remains: process evidence is distributed in middle residual states, with partial MLP participation, but not a clean one-direction MLP knob. / E44 是边界结果，不是成功证明。MLP 在 E41 中参与，但朴素单方向 MLP steering 还不是有说服力的可复用因果 feature。安全说法仍是：过程证据分布在中层 residual state，MLP 部分参与，但还不是一个干净的 MLP 方向旋钮。

## 3. E46 natural harvesting pilot / E46 自然生成挖掘 pilot

Question / 问题：如果不给模型塞错误 span，只让它自然解这些表层语义题，会不会自然产生 answer-correct but process-invalid traces？ / 不放入已知错误，只自然解题，会不会自然生成 ACPI？

Design / 设计：neutral solve prompts on the six E43 families. Qwen35-27B uses official chat template and model-generation defaults; Gemma4-31B-it uses official chat template and model-generation defaults. Known error spans are not prompt inputs. / 对 E43 6 类题使用中性解题提示。Qwen35-27B 与 Gemma4-31B-it 都用官方 chat 模板和模型默认采样参数；已知错误 span 不进入 prompt。

Files / 文件：`results/E46_E47_conditioned_generation/e46_qwen35_27b_conditioned_generation.json`, `results/E46_E47_conditioned_generation/e46_gemma4_31b_it_conditioned_generation.json`.

| model / 模型 | samples | final-correct | final-correct process-invalid | main observation / 主要观察 |
|---|---:|---:|---:|---|
| Qwen35-27B | 12 | 8 | 0 | Correct traces were process-valid under pilot audit; failures were mostly truncation/no final answer. / 答案正确样本在 pilot 审计下过程有效；失败多为截断或无最终答案。 |
| Gemma4-31B-it | 6 | 5 | 0 | Same: neutral prompts did not naturally produce ACPI in this small sample. / 同样，中性提示小样本未自然产生 ACPI。 |

Scientific interpretation / 科学解释：this does not refute the controlled ACPI claim. It says natural prevalence is not established by a tiny neutral-prompt pilot. To make a top-tier natural-prevalence claim, we need larger budgets, varied prompts, and perhaps contexts that naturally invite lexical ambiguity, while still not injecting the known error span. / 这不反驳受控 ACPI 主张，只说明小规模中性提示还不能证明自然发生率。若要做顶会级自然发生率，需要更大预算、更多提示风格，以及自然诱发表层歧义的上下文，同时仍不能把已知错误 span 塞进 prompt。

## 4. E47 AIME hard-task final-correct conditioning / E47 AIME 难题答案正确条件化

Question / 问题：AIME24/25 这类难题上，先拿到答案正确 trace 后是否能看到 ACPI？ / 在 AIME 难题上，如果先获得答案正确 trace，是否能看到 ACPI？

Design / 设计：Qwen35-27B, official chat template, thinking enabled, 3 AIME-2025 tasks, 2 samples per task, 512 max new tokens. Public answers are used only after generation as filters, not in prompts. / Qwen35-27B，官方 chat 模板，thinking 开启，3 道 AIME-2025，每题 2 样本，512 max new tokens。公开答案只在生成后做过滤，不进入 prompt。

File / 文件：`results/E46_E47_conditioned_generation/e47_qwen35_27b_conditioned_generation.json`.

Result / 结果：0/6 final-correct traces. Therefore no ACPI estimate is possible in this pilot. / 6 条中 0 条答案正确，因此本 pilot 不能估计 ACPI。

Scientific interpretation / 科学解释：hard-task evidence remains a gap. Current AIME runs still measure generation difficulty more than verifier ACPI risk. The next hard-task step should increase sampling budget and max tokens, use stronger models if available, and only then audit final-correct candidates for process validity. / 难题证据仍是缺口。目前 AIME 运行主要测生成难度，而不是 verifier ACPI 风险。下一步应增加采样预算和 max tokens，使用更强模型，并只对答案正确候选做过程审计。

## 5. Reliability and leakage audit / 可靠性与泄露审计

Machine audit / 机器审计：`logs/audit_e43_e47_next_experiments_20260428.json`, passed. / 已通过。

- E43 data are balanced: 6 families × 2 paraphrases × valid/invalid = 24 rows; support/error spans are present in the appropriate traces. / E43 数据均衡，support/error span 在相应 trace 中存在。
- Chat/post-trained model runs use official chat templates and `add_special_tokens=False` after rendering. / chat/post-trained 模型使用官方 chat 模板，渲染后不重复加 special token。
- E44 uses leave-one-family-out construction, so the held-out family is not used to build its direction. / E44 采用留一族构造，留出家族不参与方向构建。
- E46/E47 prompts are generated from the problem only; known error spans and gold answers are not inserted into generation prompts. / E46/E47 prompt 只来自题目；已知错误 span 和 gold answer 不进入生成 prompt。
- E46 final-correct process audit is conservative and under-sensitive; it should be treated as pilot audit, not final natural-prevalence measurement. / E46 过程审计保守且可能漏检，应视为 pilot 审计，不是最终自然发生率测量。

## 6. What this means for the paper / 对论文主线的意义

The new experiments make the story more precise. / 新实验让主线更精确。

- Stronger: hidden process evidence transfers across paraphrases, so E40 is not merely a fixed-token artifact. / 更强：隐藏过程证据能跨改写迁移，所以 E40 不只是固定 token artifact。
- More conservative: mismatched-family transfer is also strong, so we should not yet claim a specific semantic circuit for each lexical trap family. / 更保守：错配家族也强，因此还不能声称每类陷阱都有特异 semantic circuit。
- Mechanism boundary: naive MLP steering is weak; MLP participation is real but not sufficient as a one-direction causal knob. / 机制边界：朴素 MLP steering 弱；MLP 参与真实存在，但不是一个单方向因果旋钮。
- Prevalence boundary: neutral natural generation and AIME pilots did not yet produce ACPI candidates; natural prevalence and hard-task conditioning remain the biggest missing pieces. / 发生率边界：中性自然生成和 AIME pilot 还没产生 ACPI 候选；自然发生率和难题条件化仍是最大缺口。

