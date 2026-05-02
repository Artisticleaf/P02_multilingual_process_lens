# Appendix A. Evaluation Setting Audit / 附录 A：评估设置审计

Date / 日期: 2026-04-28 CST

This appendix checks the evaluation settings used so far and separates three things: (i) settings that are already correct, (ii) settings that are valid but must be named as a specific prompt family, and (iii) settings that should be corrected in future main results. / 本附录检查目前所有评估设置，并区分三类情况：（i）已经正确，（ii）有效但必须标注为某一 prompt family，（iii）后续主结果应修正的设置。

Audit result / 审计结论：the paper-facing E39-E42 deterministic verifier, hidden-patch settings, and refreshed P0 official-template parity now pass the machine audit in `logs/audit_eval_settings_appendix_20260428.json`. Two concrete issues were found and fixed during this audit: (1) official-template hidden patch now tokenizes rendered chat templates with `add_special_tokens=False`; (2) Qwen35-9B layer-sweep configs now use valid layer IDs `[0, 4, 8, 12, 14, 16, 20, 24, 28, 31]` for its 32 text layers. / 论文主证据相关的 E39-E42 确定性 verifier、hidden patch 设置和刷新后的 P0 官方模板 parity 已经通过 `logs/audit_eval_settings_appendix_20260428.json` 机器审计。本次审计发现并修复了两个具体问题：（1）官方 chat 模板渲染后 hidden patch tokenize 改为 `add_special_tokens=False`；（2）Qwen35-9B 层扫描配置改为其 32 个 text layer 内的合法层号 `[0, 4, 8, 12, 14, 16, 20, 24, 28, 31]`。

## A1. Checklist / 检查表

| item / 项目 | official or methodological requirement / 官方或方法要求 | project setting / 项目设置 | status / 状态 | action / 处理 |
|---|---|---|---|---|
| Model loading / 模型加载 | Use local checkpoint with correct architecture and eval mode. / 使用正确 checkpoint 与 eval 模式。 | `load_causal_lm(..., trust_remote_code=True)`, `model.eval()`, `torch.no_grad()` for scoring. / 本项目使用 `trust_remote_code=True`、`eval()`、`no_grad()`。 | ✅ | No change. / 无需修改。 |
| Large model placement / 大模型放置 | HF/Accelerate recommends `device_map="auto"` for big-model inference; lower precision can reduce memory. / HF/Accelerate 建议大模型推理用 `device_map="auto"`，低精度可省显存。 | 27B/31B use `--device auto` plus `MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'`. / 27B/31B 使用四卡 auto device map 与显存上限。 | ✅ | Keep. / 保持。 |
| Floating dtype / 数值精度 | Model configs use bf16 or auto dtype where available. / 模型配置使用 bf16 或 auto dtype。 | HF runner uses `bfloat16`; Gemma/Qwen local configs are compatible. / HF runner 使用 bf16。 | ✅ | Keep; paper notes bf16 inference. / 论文注明 bf16 推理。 |
| Base vs chat prompts / base 与 chat prompt | HF chat-model docs require model-specific `apply_chat_template`; duplicated special tokens should be avoided. / HF 文档要求 chat 模型使用 `apply_chat_template`，且后续 tokenize 不应重复加 special token。 | Historical primary runs used raw audit prompts for all models; this is a valid raw-prompt stress test but not the official chat-template setting for Qwen35/Gemma. / 历史主结果对所有模型使用 raw audit prompt；它是有效的 raw-prompt 压力测试，但不是 Qwen35/Gemma 官方 chat-template 设置。 | ⚠️ corrected / 已修正验证 | Added E42 official-template parity and official-template Qwen35 hidden patch. Future main chat-model runs should use `official_if_chat`. / 已补 E42 官方模板 parity 和 Qwen35 官方模板 hidden patch；后续 chat 模型主结果用 `official_if_chat`。 |
| Chat thinking mode / chat thinking 模式 | Qwen3.5 and Gemma4 support thinking/non-thinking controls; short classification should avoid uncontrolled long thoughts. / Qwen3.5 与 Gemma4 支持 thinking/non-thinking；短分类应避免不可控长思考。 | Official parity uses `enable_thinking=False`, matching direct Yes/No or A/B evaluation. / 官方模板 parity 使用 `enable_thinking=False`。 | ✅ | Keep for classifier/verifier. / 分类器/verifier 保持。 |
| Teacher-forced Yes/No scoring / teacher-forced 是/否评分 | For binary classification, deterministic logprob scoring does not use sampling parameters. / 二分类 teacher forcing 不使用采样参数。 | We sum option token log-probs and use Yes-minus-No margin; no generation randomness. / 项目对选项 token logprob 求和，用 Yes-No margin。 | ✅ | Keep; report as deterministic scorer. / 保持，论文注明确定性 scorer。 |
| Option normalization / 选项归一 | Must avoid single-string tokenization artifacts. / 需避免单一字符串 tokenization artifact。 | Multiple forms are scored: `Yes`, ` Yes`, lower-case; A/B variants. / 使用多个 Yes/No 与 A/B 表面形式取最大分。 | ✅ | Keep. / 保持。 |
| Chat-template tokenization / chat 模板 tokenize | If `apply_chat_template(tokenize=False)` is used, tokenize later with `add_special_tokens=False`. / 若模板先输出字符串，后续 tokenize 应用 `add_special_tokens=False`。 | New official parity script does this. Historical raw prompts use `add_special_tokens=True`, which is correct for raw text. / 新官方 parity 已使用；历史 raw prompt 使用 special token 是正确的。 | ✅ | Keep. / 保持。 |
| Chat-template hidden-patch tokenization / chat 模板 hidden patch tokenize | Same no-duplicate-special-token rule applies to hidden-state patching. / hidden patch 也必须遵守不重复 special token 的规则。 | `run_real_acpi_span_patch_smoke.py` now records `add_special_tokens=False` when `used_chat_template=True`; official Qwen35 rerun confirms this. / 脚本现记录 chat 模板下 `add_special_tokens=False`，并已复跑 Qwen35 官方模板。 | ✅ corrected / 已修正 | Use the rerun result, not the earlier duplicate-special-token run. / 使用复跑结果，不使用早先重复 special token 的运行。 |
| Contrastive order balance / 对比顺序平衡 | Pairwise comparison must control A/B position bias. / 对比必须控制 A/B 位置偏差。 | E42 runs both `bad_A` and `bad_B`; reports `pred_A_rate` and bad_A/bad_B accuracy. / E42 同时跑 bad_A/bad_B 并报告位置偏差。 | ✅ | Keep. / 保持。 |
| Locate-only generation / 仅定位生成 | HF generation docs say greedy is suitable for short non-creative outputs but can repeat on long outputs; model cards may recommend sampling for open generation. / HF 文档指出 greedy 适合短输出但长输出易重复；模型卡对开放生成常建议采样。 | Historical locate-only used deterministic greedy; this made outputs reproducible but caused Qwen/Gemma formatting artifacts. / 历史 locate-only 用 greedy，复现性强但出现格式 artifact。 | ⚠️ supplementary / 辅助结果 | Treat locate-only as diagnostic, not primary evidence. Future locate runs should use official chat template and report malformed outputs. / locate-only 只作诊断；未来用官方模板并报告坏格式。 |
| Locate-then-judge / 先定位再判断 | Generated span output must be parsed conservatively and malformed outputs counted. / span 生成应保守解析，格式坏应计入失败。 | E42 keeps malformed outputs as failures; Gemma31 instability is reported. / E42 没有丢弃坏格式，Gemma31 不稳定已报告。 | ✅ | Keep. / 保持。 |
| Hidden-state patching / 隐藏层 patch | For causal intervention, no labels or error spans may enter the prompt; spans are only used to select hidden positions. / 因果干预不能把标签或错误 span 放进 prompt；span 只用于定位隐藏向量。 | Patch prompts contain only problem + trace; support/error spans are used post-tokenization for positions. / patch prompt 只有题目和 trace；span 仅用于定位。 | ✅ | Keep. / 保持。 |
| Official-template hidden patch / 官方模板 hidden patch | Chat-model hidden-state probes should be checked under the model's official chat wrapper. / chat 模型 hidden-state probe 应检查官方 chat wrapper。 | Historical E40 Qwen35 used raw prompt; official-template rerun now gives clean `12/12`. / 历史 E40 Qwen35 是 raw；现已补官方模板，干净 `12/12`。 | ✅ corrected / 已修正验证 | Use official-template patch results as robustness in paper. / 论文使用作稳健性。 |
| Layer-sweep configs / 层扫描配置 | Probe layer IDs must be inside the model's text-layer range. / probe 层号必须位于模型 text layer 范围内。 | Qwen35-9B has 32 text layers; stale layer IDs `32/36/39` were removed from Qwen35 configs and replaced with final valid layer `31`. / Qwen35-9B 有 32 个 text layer；旧配置中的 `32/36/39` 已移除并替换为合法末层 `31`。 | ✅ corrected / 已修正 | Future layer sweeps use audited configs. Historical scripts had filtered invalid IDs, but the config is now explicit. / 后续层扫描用审计后配置；历史脚本曾自动过滤非法层号，但现在配置显式正确。 |
| Data leakage / 数据泄露 | Known labels/error spans must not be inserted into verifier prompts. / 已知标签/错误 span 不得进入 verifier prompt。 | E42 audit found no prompt-like stored keys except `prompt_lang`; known spans used only for post-hoc scoring. / E42 审计未发现 prompt 泄露。 | ✅ | Keep audits in appendix. / 审计放附录。 |
| Manual labels / 人工标签 | ACPI labels must require process-invalid + final-correct, not just answer status. / ACPI 标签必须同时满足过程错、答案对。 | E39/E42 audit checks 12 tasks, balanced variants, exact support/error span presence, ACPI labels. / E39/E42 审计检查任务平衡与标签一致。 | ✅ | Keep. / 保持。 |
| vLLM vs HF backend / vLLM 与 HF 后端 | Use vLLM when architecture is supported; use HF fallback otherwise. / 架构支持则 vLLM，高风险/不支持则 HF fallback。 | Qwen35/Gemma conditional-generation families are not reliably supported by current vLLM; HF four-GPU fallback is used. / Qwen35/Gemma 当前 vLLM 不稳，使用 HF 四卡 fallback。 | ✅ | Keep; do not force vLLM. / 保持，不强制 vLLM。 |

## A2. Official-template parity check / 官方模板 parity 检查

The most important discovered issue was prompt formatting for chat/post-trained models. Historical raw prompts are still interpretable as a prompt-family stress test, but paper-grade claims should include official-template robustness. / 最重要发现是 chat/post-trained 模型的 prompt 格式。历史 raw prompt 可解释为一种 prompt-family 压力测试，但论文级主张应加入官方模板稳健性。

E42 official-template parity reruns deterministic pointwise and contrastive scoring on the same E42 focus set. / E42 官方模板 parity 在同一批 E42 focus set 上复跑确定性点式和对比式评分。

| model / 模型 | official prompt / 官方 prompt | absolute process ACPI accept | valid accept | contrastive acc | interpretation / 解释 |
|---|---|---:|---:|---:|---|
| Qwen35-9B | chat template, `enable_thinking=False` | 0.417 | 1.000 | 1.000 | Official template reduces absolute over-acceptance but does not remove it; contrastive fully exposes errors. / 官方模板降低过度接受但不消除；对比式完全暴露错误。 |
| Qwen35-27B | chat template, `enable_thinking=False` | 0.500 | 1.000 | 1.000 | Same causal pattern as raw prompts, with lower absolute false accept. / 与 raw prompt 同一因果模式，但绝对误接受降低。 |
| Qwen3-14B-Base | raw prompt, base model | 0.250 | 1.000 | 0.958 | Base model does not require chat wrapper; previous setting is retained. / base 模型不需要 chat wrapper，沿用 raw。 |
| Gemma4-31B-it | chat template, `enable_thinking=False` | 0.500 | 1.000 | 1.000 | Official template strengthens contrastive behavior and preserves absolute ACPI acceptance. / 官方模板让对比式更强，同时保留绝对式 ACPI 接受。 |
| Gemma4-26B-A4B-it | chat template, `enable_thinking=False` | 0.500 | 1.000 | 1.000 | P0 core replication: absolute over-acceptance remains while contrastive comparison is perfect. / P0 核心复现：absolute 过度接受仍存在，而 contrastive comparison 满分。 |

Conclusion / 结论：the official-template check does not overturn the main claim. It makes the quantitative claim more conservative: raw prompts show stronger over-acceptance for Qwen35, while official templates still show non-trivial over-acceptance and near-perfect or perfect sibling recovery. / 官方模板检查不推翻主结论，但让数字表述更保守：raw prompt 下 Qwen35 过度接受更强，官方模板下仍有非平凡过度接受，且 sibling 恢复接近满分或满分。

## A3. Official-template hidden patch check / 官方模板 hidden patch 检查

Because Qwen35-9B is a chat/post-trained model, E40 residual patching was rerun with `official_if_chat` prompt formatting. / 由于 Qwen35-9B 是 chat/post-trained 模型，E40 residual patch 已用 `official_if_chat` 复跑。

Result / 结果：`reports/E40_official_template_span_patch_summary_20260428.md` shows clean residual support/error signal on `12/12` E39 pairs after the corrected chat-template tokenization. The result file records `used_chat_template=True`, `add_special_tokens=False`, `rows=120`, and valid layers `[0, 4, 8, 12, 14, 16, 20, 24, 28, 31]`. The strongest example is Chinese strict interval at L8, `valid->bad +5.625`, `bad->valid -6.312`. / 修正 chat-template tokenization 后，结果显示 E39 12/12 对都有干净 residual support/error 信号。结果文件记录 `used_chat_template=True`、`add_special_tokens=False`、`rows=120`，层号为合法的 `[0, 4, 8, 12, 14, 16, 20, 24, 28, 31]`。最强是中文严格区间 L8。

Interpretation / 解释：the hidden process evidence is not an artifact of raw prompt formatting. / 隐藏过程证据不是 raw prompt 格式 artifact。

## A4. What should be reported in the paper / 论文中应如何报告

- Main verifier tables should report both raw-audit prompt and official-template robustness for chat models. / 主 verifier 表应同时报告 raw audit prompt 与 chat 模型官方模板稳健性。
- Absolute false-accept rates from raw prompts should be described as a stress-test setting, not as the only model-native setting. / raw prompt 的绝对误接受率应称为压力测试设置，不应说成唯一模型原生设置。
- Locate-only generation should be diagnostic only; central claims should rely on deterministic logprob scoring, contrastive scoring, and hidden-state patching. / locate-only 只作诊断；核心主张依赖确定性 logprob、对比式评分和 hidden-state patch。
- Future E43-E47 experiments should default to `official_if_chat` for chat/post-trained models and raw prompts for base models. / 后续 E43-E47 默认 chat/post-trained 模型用 `official_if_chat`，base 模型用 raw。

## A5. Sources / 参考来源

Verified on 2026-04-28. / 2026-04-28 已核对。

- Hugging Face chat templates: https://huggingface.co/docs/transformers/main/chat_templating
- Hugging Face generation strategies: https://huggingface.co/docs/transformers/main/en/generation_strategies
- Hugging Face Accelerate big-model inference: https://huggingface.co/docs/accelerate/main/en/usage_guides/big_modeling
- Qwen3.5-9B model card: https://huggingface.co/Qwen/Qwen3.5-9B/blob/main/README.md
- Gemma4-31B-it model card: https://huggingface.co/google/gemma-4-31B-it

## A6. Audit artifacts / 审计产物

- E42 integrity audit: the raw-prompt audit is archived under `archive/raw_prompt_legacy_20260428/`; active official-template parity is checked by `logs/audit_eval_settings_appendix_20260428.json`. / raw-prompt 审计已归档；当前官方模板 parity 由该日志检查。
- Evaluation-setting machine audit: `logs/audit_eval_settings_appendix_20260428.json`.
- Project environment check: `logs/check_project_eval_audit_20260428.json`.
- Official-template parity results: `results/E42_official_template_parity/`.
- Official-template Qwen35 hidden patch: `results/E40_official_template_span_patch/` and `reports/E40_official_template_span_patch_summary_20260428.md`.
- Corrected config retained active: `configs/e39_surface_semantic_pairs_qwen35_9b.yaml`. / 当前保留的修正配置为该文件。
