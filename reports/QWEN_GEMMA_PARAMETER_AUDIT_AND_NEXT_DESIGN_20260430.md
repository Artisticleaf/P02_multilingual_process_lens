# Qwen/Gemma Parameter Audit and Next Design / Qwen/Gemma 参数审计与后续设计（2026-04-30）

## 1. Scope / 范围

This report audits the experiment settings for the Qwen3.5/Gemma4 core models only:

本报告只审计 Qwen3.5/Gemma4 核心模型：

- `qwen35_27b` / Qwen3.5-27B
- `gemma4_31b_it` / Gemma4-31B-it
- `gemma4_26b_a4b_it` / Gemma4-26B-A4B-it

GLM is temporarily excluded from the next design. Existing GLM results remain useful boundary evidence, but the immediate clean mainline should first be Qwen/Gemma-only.

GLM 暂时不进入下一阶段主线。已有 GLM 结果仍是边界证据，但现在先把 Qwen/Gemma 主线做干净。

Parameter manifest / 参数清单：

- `configs/qwen_gemma_parameter_profiles_20260430.yaml`

## 2. Primary Sources Checked / 已核对的一手来源

- Local Qwen3.5 model card / 本地 Qwen3.5 模型卡：`/home/Awei/LLM/Model/base/qwen35_27b/README.md`
- Local Qwen3.5 generation config / 本地 Qwen3.5 生成配置：`/home/Awei/LLM/Model/base/qwen35_27b/generation_config.json`
- Local Gemma4 model cards / 本地 Gemma4 模型卡：`/home/Awei/LLM/Model/base/gemma4_31b_it/README.md`, `/home/Awei/LLM/Model/base/gemma4_26b_a4b_it/README.md`
- Local Gemma4 generation configs / 本地 Gemma4 生成配置：`generation_config.json` under both Gemma model dirs.
- Remote model cards for reference / 远程模型卡参考：Qwen3.5-27B `https://huggingface.co/Qwen/Qwen3.5-27B`, Gemma4-31B-it `https://huggingface.co/google/gemma-4-31B-it`.

## 3. What Was Correct / 哪些设置是正确的

### 3.1 Direct/non-thinking verifier / 直接非思考验证器

For `DV` and `MI-DV` experiments, sampling parameters are not the decisive setting because the model is not generating an open-ended answer. It is scored by deterministic `Yes/No` or `A/B` option log-probability, or by teacher-forced hidden-state replay.

对 `DV / 直接验证器` 和 `MI-DV / 直接机制检查`，`temperature/top_p/top_k` 不是关键参数，因为模型不是开放生成，而是在固定 prompt 后打 `Yes/No` 或 `A/B` 的 option log-prob，或做 teacher-forced hidden replay。

Correct settings already used:

已正确使用的设置：

- official chat template when available / 使用官方 chat template；
- `enable_thinking=False` / 关闭显式 thinking；
- rendered chat text tokenized with `add_special_tokens=False` / chat template 渲染后不重复添加 special tokens；
- `bfloat16`, `device_map=auto` / bf16 与多卡自动切分；
- manual labels, gold answers, known trap notes, and known error spans are not in prompts / prompt 不含人工标签、答案、陷阱说明或错误 span。

This means E61, E65, E71, E78, E80, E90, and E106-E114 remain valid as `DV/MI-DV` evidence after mode-scoping.

因此 E61、E65、E71、E78、E80、E90、E106-E114 作为 `DV/MI-DV` 证据仍可保留，但必须标注模式。

### 3.2 Thinking-mode distinction / thinking 模式区分

Qwen3.5 model card states that thinking is the default and non-thinking should be controlled through template/API parameters. Gemma4 model card states that reasoning can be enabled/disabled through `enable_thinking`; medium Gemma models still emit an empty thought channel when disabled.

Qwen3.5 模型卡说明默认是 thinking；non-thinking 需要用 template/API 参数控制。Gemma4 模型卡说明可用 `enable_thinking` 控制；Gemma4 中型模型关闭 thinking 后仍会出现空 thought channel。

Local smoke confirmed:

本地 smoke 已确认：

- Qwen non-thinking template prefix includes an empty `<think>...</think>` block.
- Gemma non-thinking template prefix includes an empty thought channel.
- Both tokenizer and processor templates work under the project `.deps/hf5` Transformers path.

## 4. What Needs Correction or Re-labeling / 需要修正或重标注的设置

### 4.1 Historical NG sampling was uniform, not model-card official / 历史 NG 采样是统一条件，不是模型卡官方参数

E57/E88/E119-style natural non-thinking generation used:

历史自然 non-thinking generation 使用：

```text
temperature=0.7, top_p=0.95, top_k=50, max_new_tokens=4096
```

This is a useful project-uniform baseline, but it is not the official model-card setting for Qwen3.5 or Gemma4.

这适合作为项目统一 baseline，但不能写成 Qwen3.5/Gemma4 的官方推荐参数。

Correct labeling:

正确标注：

- `NG_uniform_legacy_baseline / 非思考统一旧基线`

Required rerun for appendix-grade credibility:

为达到 appendix 级可信度，需要补跑：

- `NG_model_card / 非思考模型卡参数复现`

### 4.2 Qwen presence penalty is not implemented in current HF generation / 当前 HF 生成未实现 Qwen presence penalty

Qwen3.5 recommends `presence_penalty` in model-card generation profiles. HF `model.generate` in our current scripts does not natively apply OpenAI-style presence penalty.

Qwen3.5 模型卡推荐 `presence_penalty`；但当前 HF `model.generate` 脚本没有实现 OpenAI 风格的 presence penalty。

Decision:

处理决定：

1. For Qwen model-card generation reruns, either implement a custom logits processor for presence penalty or use a serving backend that supports it.
2. If we do not implement it, every Qwen generation result must explicitly record `presence_penalty_unavailable_in_hf_generate=true`.
3. Existing Qwen TG/NG results remain valid as HF-template experiments, not exact model-card sampling replications.

### 4.3 Generation pad token should use tokenizer pad token / 生成 pad token 应使用 tokenizer 自带 pad

Several generation scripts used `pad_token_id=tok.eos_token_id`. This is not ideal for Gemma4 because the model config uses `pad_token_id=0` and multiple EOS ids.

几个 generation 脚本之前使用 `pad_token_id=tok.eos_token_id`。这对 Gemma4 不理想，因为 Gemma4 配置中 `pad_token_id=0`，并且有多个 EOS id。

Patched scripts / 已修正脚本：

- `scripts/run_e49_hard_task_conditioning_official.py`
- `scripts/run_e103_tg_ng_fair_hardtask.py`
- `scripts/run_e105_tg_closure_policy.py`
- `scripts/run_e101_batch_generation_sensitivity.py`

New rule:

新规则：

```python
pad_token_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
```

Boundary:

边界：

- This patch does not change the already-running E119 process.
- Existing E119 Qwen/Gemma results should be labeled with their original script settings.
- Future reruns use the corrected pad rule.

## 5. Locked Parameter Profiles / 敲定后的参数 profiles

### 5.1 Direct verifier / 直接验证器

Use for E61/E65/E80/E90/E106-style experiments.

用于 E61/E65/E80/E90/E106 等实验。

```text
enable_thinking=false
do_sample=false
scoring=option_logprob_or_teacher_forced_replay
max_model_len=6144 for controlled verifier
max_model_len=8192 for hard-task prefix/cache replay
```

Rationale / 原因：

- No open generation, so model-card sampling parameters do not apply.
- The visible prompts are far shorter than the 256K/262K context windows.
- Left truncation is recorded when it occurs.

### 5.2 Qwen3.5 non-thinking natural generation / Qwen3.5 非思考自然生成

Use two arms:

使用两个条件：

```text
NG_uniform_legacy_baseline:
  temperature=0.7, top_p=0.95, top_k=50, max_new_tokens=4096

NG_model_card_reasoning:
  temperature=1.0, top_p=0.95, top_k=20,
  min_p=0.0, presence_penalty=1.5, repetition_penalty=1.0,
  max_new_tokens=8192
```

If presence penalty is unavailable, record it rather than silently dropping it.

如果无法实现 presence penalty，必须记录，不能静默忽略。

### 5.3 Qwen3.5 thinking generation / Qwen3.5 思考生成

```text
enable_thinking=true
temperature=1.0, top_p=0.95, top_k=20,
min_p=0.0, presence_penalty=1.5, repetition_penalty=1.0,
max_new_tokens=32768
prompt=final-contract
```

Report separately:

必须分别报告：

- fallback answer / fallback 抽取答案；
- explicit final marker / 显式最终答案标记；
- clean final stop / 最终答案后干净停止；
- hit max / 撞 token 上限；
- post-final continuation / 最终答案后继续输出。

### 5.4 Gemma4 non-thinking and thinking generation / Gemma4 非思考与思考生成

Use the same standardized sampling profile for both modes:

Gemma4 模型卡给出跨场景统一采样：

```text
temperature=1.0, top_p=0.95, top_k=64
```

Recommended output budget:

建议输出预算：

```text
NG_model_card: max_new_tokens=8192
TG_model_card: max_new_tokens=8192
Escalate TG to 16384 if hit-max rate > 0.30 in smoke.
```

## 6. Qwen/Gemma-Only Next Experiments / 只看 Qwen/Gemma 的后续实验

### E119-QG audit / E119 Qwen/Gemma 人审

Use already generated Qwen/Gemma E119 rows. Do not wait for GLM if the immediate paper mainline excludes GLM.

使用已经生成的 Qwen/Gemma E119 行。如果主线暂时排除 GLM，不必等 GLM 才开始 Qwen/Gemma 审计。

Purpose / 目的：

- Estimate natural `strict ACPI`, `repaired ACPI`, and `unrepaired ACPI` for Qwen/Gemma only.

### E146-QG NG model-card rerun / Qwen/Gemma 非思考模型卡参数复现

Rerun natural hard tasks with model-card sampling profiles.

用模型卡参数重跑自然困难题。

Purpose / 目的：

- Separate “project-uniform sampling” from “official/model-card sampling”.
- Check whether ACPI prevalence is stable under the officially recommended sampling regime.

### E131-QG token-level localization / token 级错误定位

Save selected-layer all-token process scores around error spans, repair markers, answer spans, and random spans.

保存错误 span、修复标记、答案 span、随机 span 附近的 selected-layer 全 token 过程分数。

Purpose / 目的：

- Show whether non-thinking error-awareness signal aligns with the actual error location.

### E132-QG residual span patch / residual 错误片段因果替换

Patch invalid error-span residuals with valid sibling residuals, and reverse-patch valid spans with invalid residuals.

把 invalid 错误 span 的 residual 替换成 valid sibling 的 residual，并做反向替换。

Purpose / 目的：

- Move from correlation to local causal evidence.

### E133-QG component patch / 组件级片段替换

Patch residual, MLP, and token-mixer/attention-related outputs separately.

分别替换 residual、MLP、token-mixer/attention-related 输出。

Purpose / 目的：

- Identify which component path carries the actionable error signal.

### E123-QG process-confidence-stop disentanglement / 过程、置信度、停止信号解缠

Use confidence-matched pairs and entropy controls; for Qwen thinking rows also control stop score.

使用置信度匹配样本和 entropy 控制；Qwen thinking 行额外控制 stop score。

Purpose / 目的：

- Answer whether “error awareness” is merely low confidence.

### E121-QG thinking verifier objective / Qwen/Gemma 思考验证器目标阶梯

Thinking verifier must generate a full judgment and final parsed decision. No first-token option-logprob.

thinking verifier 必须完整生成判断并解析最终 Yes/No，不能使用首 token logprob。

Purpose / 目的：

- Test whether direct-verifier ACPI over-accept survives under thinking verifier.

### E143-QG final-contract thinking natural generation / 思考最终答案契约自然生成

Run Qwen/Gemma thinking with final-contract prompts and model-card sampling.

用 final-contract prompt 和模型卡参数跑 Qwen/Gemma thinking。

Purpose / 目的：

- Estimate thinking-mode natural ACPI without confusing fallback numbers with final decisions.

## 7. Queue Safety Requirements / 队列防呆要求

Every future tmux queue should:

后续 tmux 队列必须：

1. Write `start`, `done`, `fail`, or `fail_missing_done_signal` to a JSONL status file.
2. Write a `_DONE.json` file only after output validation passes.
3. On nonzero exit, write `_FAILED.json`, save stderr tail and GPU snapshot, then continue to the next experiment.
4. If a prior `_DONE.json` exists, skip the step for resumability.
5. Run static audit and smoke before formal runs.
6. Never put manual labels, known spans, gold answers, or trap notes in model prompts unless the run is explicitly labeled non-prevalence.
7. Load only one large model at a time.

## 8. Bottom Line / 结论

The current Qwen/Gemma verifier/mechanism results are mostly parameter-valid because they are deterministic direct-verifier or teacher-forced replay experiments. The natural generation results are scientifically useful but should be relabeled as a project-uniform sampling baseline. For a top-tier paper, rerun Qwen/Gemma natural generation under model-card sampling profiles, then prioritize token-level localization and span-level causal patching.

当前 Qwen/Gemma 的 verifier/mechanism 结果大体参数可信，因为它们主要是确定性 direct verifier 或 teacher-forced replay。自然生成结果有科学价值，但应标注为项目统一采样 baseline。为了顶会/顶刊主线，需要用模型卡参数补跑 Qwen/Gemma 自然生成，然后优先做 token 级定位和 span 级因果 patch。

