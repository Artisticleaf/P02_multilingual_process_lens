# P0 Model Cluster Update / P0 模型簇更新（2026-04-28）

## Plain-language decision / 说人话决定

- P0 now means: the strongest locally available, recent, open-weight medium models that can carry the paper's main cross-model claim. / P0 现在表示：本地已可用、较新、较强、开源权重中等规模模型，足以支撑论文主结论。
- Current core P0 is `qwen35_27b`, `gemma4_31b_it`, and `gemma4_26b_a4b_it`. / 当前核心 P0 是 `qwen35_27b`、`gemma4_31b_it`、`gemma4_26b_a4b_it`。
- External P0 candidates now being downloaded are Nemotron Cascade 2 30B-A3B, GLM-4.7-Flash, and user-approved EXAONE 4.5 33B; they are not official evidence models until smoke-tested. / 当前正在下载的外部 P0 候选是 Nemotron Cascade 2 30B-A3B、GLM-4.7-Flash 和用户确认的 EXAONE 4.5 33B；通过 smoke test 前不算官方证据模型。
- Smaller or older models are controls, not headline evidence. / 小模型或旧模型只做控制，不做主证据。
- Qwen2.5-Math-7B is now P2 legacy: E49-E52 results are useful for bottleneck diagnosis and seed discovery, but should not be framed as frontier-model evidence. / Qwen2.5-Math-7B 现在是 P2 旧控制：E49-E52 结果可用于瓶颈诊断和种子发现，但不能作为前沿模型证据。

## Strict trace-selection / 严格 trace-selection

Strict trace-selection means that a generated reasoning trace is eligible for selection only if it satisfies all of the following:

中文：严格 trace-selection 指一个生成的推理过程只有同时满足以下条件，才可以被选入“可比较 trace”集合：

1. The prompt does not reveal the gold answer or known trap. / prompt 不能泄露 gold answer 或已知陷阱。
2. The answer is extracted only from a line that starts with `Final answer:`. / 答案只能从行首 `Final answer:` 抽取。
3. For hard-task official counts, boxed-only answers such as `\boxed{279}` are benchmark diagnostics, not strict trace-selection positives. / 对困难题官方计数，只有 `\boxed{279}` 这种 boxed-only 输出只能算 benchmark 诊断，不算 strict trace-selection 阳性。
4. The final answer must match the gold answer under a predeclared normalizer. / 最终答案必须按预注册 normalizer 与 gold answer 一致。
5. If the final answer is correct, the reasoning process is separately audited as process-valid, process-invalid, or ambiguous. / 如果答案正确，推理过程还要单独审为过程有效、过程无效或 ambiguous。
6. The ACPI event is counted only when final answer is correct and the process is clearly invalid. / 只有答案正确且过程明确无效，才计为 ACPI。

Why this matters:

中文：为什么要这么严：

- It prevents a parser from counting echoed prompt text such as `Given final answer: 16` as the model's answer. / 防止 parser 把 prompt 中回显的 `Given final answer: 16` 当成模型答案。
- It separates benchmark solving from trace-selection usability. / 区分“模型解出题”与“模型输出了可用于 trace-selection 的格式”。
- It prevents us from mixing different objectives in one table. / 防止把不同目标的结果混在同一张表里。
- It makes verifier failure claims auditable: the selected trace has a known answer and an independently labeled process. / 让 verifier failure 主张可审计：被选中的 trace 有确定答案和独立过程标签。

## Updated local tiers / 更新后的本地分层

| Tier / 层级 | Models / 模型 | Role / 作用 |
|---|---|---|
| P0 core | `qwen35_27b`, `gemma4_31b_it`, `gemma4_26b_a4b_it` | Main cross-model evidence on recent medium open-weight models. / 最新中等开源模型的主证据。 |
| P1 controls | `qwen35_9b`, `qwen3_14b_base`, `qwen3_8b_base`, `deepseek_r1_0528_qwen3_8b`, `ministral3_8b_reasoning`, `gemma4_e4b_it`, `phi4_mini_reasoning`, `glm46v_flash` | Transfer, ablation, mechanism, or company-diversity controls. / 迁移、消融、机制或公司多样性控制。 |
| P2 legacy | `qwen25_math_7b_instruct`, `llama32_3b` | Legacy/negative controls only; do not headline. / 旧模型或负控制，不做主结论。 |

## External candidates / 外部候选

| Candidate / 候选 | Why consider it / 为什么考虑 | Current recommendation / 当前建议 |
|---|---|---|
| `LGAI-EXAONE/EXAONE-4.5-33B` | 33B dense VLM from LG; Artificial Analysis lists it near the 30B class, and the model card reports strong reasoning benchmarks. / LG 的 33B dense VLM，在 30B 档有竞争力，model card 也报告强 reasoning。 | User-approved P0 external candidate; currently queued for download after Nemotron and GLM. Promote only after license and backend smoke checks. / 用户已确认的 P0 外部候选；当前排在 Nemotron 和 GLM 之后下载。必须通过许可和后端 smoke check 后再转为官方 P0。 |
| `zai-org/GLM-4.7-Flash` | 30B-A3B MoE, Chinese/English, MIT license; model card positions it as strong 30B-class model. / 30B-A3B MoE，中英双语，MIT；model card 自称 30B 档强模型。 | P1 candidate by default; promote to P0 only if local smoke test and current leaderboard match P0. / 默认 P1 候选；本地 smoke 与榜单接近 P0 后再升。 |
| `nvidia/Nemotron-Cascade-2-30B-A3B` | 30B-A3B open MoE with explicit reasoning/agentic focus. / 30B-A3B 开放 MoE，主打 reasoning/agentic。 | P0 candidate for external diversity if vLLM >= 0.17.1 can be installed in a separate env; do not perturb current env. / 若可在独立环境部署 vLLM>=0.17.1，可做外部多样性 P0 候选；不要污染当前环境。 |
| `XiaomiMiMo/MiMo-V2-Flash` | Competitive reasoning/agentic MoE, but 309B total / 15B active. / reasoning/agentic 竞争力强，但总参 309B、激活 15B。 | Not a 30B local-medium model; treat as P0-external only if quantized deployment is feasible. / 不是 30B 本地中等模型；只有量化可部署时才做 P0-external。 |
| Mistral Small 4 family | Important non-Chinese/non-Google family if an open-weight medium checkpoint is available. / 若有可用中等开源权重，是重要的非中/非 Google 对照。 | Candidate remains unresolved until exact open-weight checkpoint, size, and loader support are verified. / 需确认具体 checkpoint、尺寸和 loader 后再定级。 |

## Source-backed rationale / 有来源依据的理由

- Artificial Analysis reported that Qwen3.5 27B and Gemma 4 31B are leading sub-32B open-weight models and that Qwen3.5/Gemma 4 are pushing the sub-32B class forward. / Artificial Analysis 报告 Qwen3.5 27B 与 Gemma 4 31B 是 sub-32B 开源权重领先模型，说明它们适合作为 P0。
- The same Artificial Analysis small-model page ranks 4B-40B open-weight models and lists Gemma 4 26B A4B, EXAONE 4.5 33B, Nemotron Cascade 2 30B A3B, and GLM-related 30B-class models near the relevant tier. / 同一小模型榜单列出了 Gemma 4 26B A4B、EXAONE 4.5 33B、Nemotron Cascade 2 30B A3B 与 GLM 30B 档模型，适合候选池。
- Qwen3.5-27B's model card recommends newer vLLM/SGLang paths; our local vLLM 0.12 incompatibility is therefore a deployment-version issue, not evidence that the model is unsuitable. / Qwen3.5-27B model card 推荐较新 vLLM/SGLang；本地 vLLM 0.12 不兼容是部署版本问题，不代表模型不适合。
- EXAONE 4.5 and GLM-4.7-Flash model cards both require newer/forked Transformers/vLLM paths, so they should be tested in isolated environments. / EXAONE 4.5 与 GLM-4.7-Flash 都需要较新或 fork 的 Transformers/vLLM，因此应在隔离环境测试。

## Policy for interpreting old results / 旧结果解释策略

- Results from P0 models can support the paper's main generalization claim. / P0 结果可支撑论文主泛化主张。
- P1 results can support mechanism transfer, ablation, or robustness claims, but should be explicitly labeled as controls. / P1 结果可支撑机制迁移、消融或稳健性，但必须标注为控制实验。
- P2 results should be used only for pipeline debugging, parser/format bottleneck discovery, or seed-case construction. / P2 结果只用于管线调试、parser/格式瓶颈发现或种子样本构造。
- E52's Qwen2.5-Math conclusion is now: hard-task format/objective mismatch exists in a legacy math-control model and produced useful seed traces; it is not a frontier-model natural prevalence result. / E52 的 Qwen2.5-Math 结论现在表述为：旧数学控制模型中存在困难题格式/目标错配，并产生有用种子；它不是前沿模型自然发生率结果。

## Sources / 来源

- Artificial Analysis sub-32B article: https://artificialanalysis.ai/articles/sub-32b-open-weights/
- Artificial Analysis small open-source models: https://artificialanalysis.ai/models/open-source/small
- Qwen3.5-27B model card: https://huggingface.co/Qwen/Qwen3.5-27B
- Gemma 4 31B model card: https://huggingface.co/google/gemma-4-31B-it
- EXAONE 4.5 33B model card: https://huggingface.co/LGAI-EXAONE/EXAONE-4.5-33B
- GLM-4.7-Flash model card: https://huggingface.co/zai-org/GLM-4.7-Flash
- Nemotron Cascade 2 30B-A3B model card: https://huggingface.co/nvidia/Nemotron-Cascade-2-30B-A3B
- MiMo-V2-Flash model card: https://huggingface.co/XiaomiMiMo/MiMo-V2-Flash
