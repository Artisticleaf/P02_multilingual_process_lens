# Appendix: Backend Compatibility and Throughput Audit / 后端兼容性与吞吐审计

Date / 日期：2026-04-28  
Project / 项目：`/home/Awei/P02_multilingual_process_lens`  
Scope / 范围：解释为什么当前官方结果中 Qwen3.5 与 Gemma4 继续使用 HuggingFace backend，而不强行使用 vLLM；给出本机证据、官方文档依据与后续运行策略。

## 1. Plain-language conclusion / 说人话结论

- **这不是训练卡死。** 当前任务主要是推理/生成与 hidden-state 机制测量，不是梯度训练；HF `device_map=auto` 的长文本自回归生成常见现象就是 GPU 显存占用高、GPU util 波动或偏低。低 util 不等于进程死锁，必须看日志是否还在生成、输出文件是否更新。
- **Qwen3.5 与 Gemma4 在本机 vLLM 0.12.0 下不能作为可靠官方 backend。** 本机 vLLM 对 `Qwen3_5ForConditionalGeneration` 直接报“不支持该 architecture”；Gemma4 会退到 vLLM 的 Transformers fallback，但在加载 multimodal/audio tower 权重时发生权重名/模块名不匹配。
- **这更像“本机 vLLM 版本与新模型架构不匹配”，不是我们的实验 prompt 或 eval 逻辑错误。** 官方 vLLM `v0.12.0` 支持列表还没有 Qwen3.5/Gemma4；官方 latest 文档已经出现 Qwen3.5/Gemma4 条目，说明未来升级 vLLM 可能可行，但升级会改变 inference backend，需要重新跑 backend parity 与官方结果审计。
- **机制实验必须继续用 HF。** 我们要读 hidden states、注册 hooks、做 residual span patch / MLP steering / layer-wise probe；这些是科学测量本身，vLLM 的高吞吐生成接口不能替代 HF 级别的逐层激活访问。
- **黑箱 generation-only 控制实验可以用 vLLM。** 对 `Qwen3ForCausalLM`、`Qwen2.5-Math`、`Phi` 等标准 CausalLM 控制模型，vLLM 可用于 E48/E49 这类只需要生成文本和最终审计的实验；结果必须标注 `backend=vllm`，不要求与 HF 逐 token 一致。

## 2. Local environment / 本机环境

Official runners set / 官方运行设置：

```bash
conda activate passage_prep_py312
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export CUDA_VISIBLE_DEVICES=0,1,2,3
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
```

Observed environment with project `PYTHONPATH` / 使用项目 `PYTHONPATH` 时的环境：

| Component / 组件 | Version / 版本 | Evidence / 证据 |
|---|---:|---|
| Python | 3.12.13 | `logs/backend_compat_environment_project_pythonpath_20260428.json` |
| PyTorch | 2.9.0+cu128 | same / 同上 |
| Transformers | 5.6.2 from `.deps/hf5` | same / 同上 |
| vLLM | 0.12.0 | same / 同上 |
| GPU | 4 × RTX 5090, 32GB each | same / 同上 |

Important note / 重要说明：系统 conda 环境中也有 Transformers 4.57.1，但官方项目 runner 通过 `.deps/hf5` 使用 Transformers 5.6.2；HF 结果应以项目 runner 的版本为准。

## 3. Local model architecture facts / 本地模型架构事实

Local config summary / 本地 `config.json` 摘要见 `logs/backend_compat_local_model_configs_20260428.json`。

| Model key / 模型 | `architectures` | Local structure / 本地结构 | Backend implication / 后端影响 |
|---|---|---|---|
| `qwen35_9b` | `Qwen3_5ForConditionalGeneration` | `text_config` + `vision_config` | New hybrid/conditional-generation family, not standard `Qwen3ForCausalLM`. / 新混合 conditional-generation 家族，不是标准 CausalLM。 |
| `qwen35_27b` | `Qwen3_5ForConditionalGeneration` | `text_config` + `vision_config` | Same risk as 9B. / 与 9B 同类风险。 |
| `gemma4_e4b_it` | `Gemma4ForConditionalGeneration` | `text_config` + `vision_config` + `audio_config` | Multimodal/audio components enter loader path. / 多模态与音频组件进入加载路径。 |
| `gemma4_26b_a4b_it` | `Gemma4ForConditionalGeneration` | `text_config` + `vision_config` + `audio_config` | Same family; medium model amplifies memory/loader risk. / 同家族，中型模型放大内存与 loader 风险。 |
| `gemma4_31b_it` | `Gemma4ForConditionalGeneration` | `text_config` + `vision_config` + `audio_config` | Same family. / 同家族。 |
| `qwen3_14b_base` | `Qwen3ForCausalLM` | text-only CausalLM | vLLM-compatible control candidate. / 可作为 vLLM 控制模型候选。 |

## 4. Official documentation evidence / 官方文档证据

- vLLM `v0.12.0` supported-model documentation says model support is keyed by the HuggingFace `architectures` field. In that version, the visible supported list includes `Qwen3ForCausalLM` / `Qwen3MoeForCausalLM` and Gemma3-family architectures, but not our local `Qwen3_5ForConditionalGeneration` or `Gemma4ForConditionalGeneration`. Source / 来源：vLLM v0.12.0 supported models, <https://docs.vllm.ai/en/v0.12.0/models/supported_models/>。
- The same vLLM documentation describes `model_impl=transformers` as a fallback route for some unsupported architectures, but a fallback route is not a guarantee that every Transformers model is compatible with vLLM scheduling/weight loading. Source / 来源：vLLM v0.12.0 supported models, same URL / 同上。
- vLLM latest supported-model documentation now lists `Qwen3_5ForConditionalGeneration` and `Gemma4ForConditionalGeneration`, including Qwen3.5/Gemma4 examples. This means support is moving upstream, but it is not the same as saying our pinned local vLLM 0.12.0 can run them. Source / 来源：vLLM latest supported models, <https://docs.vllm.ai/en/latest/models/supported_models/>。
- vLLM latest Qwen3.5 recipe is explicitly for the newer Qwen3.5 family and discusses deployment details for recent releases; it should be treated as an upgrade target, not as evidence that the current pinned local backend is already valid. Source / 来源：vLLM Qwen3.5 recipe, <https://docs.vllm.ai/projects/recipes/en/latest/Qwen/Qwen3.5.html>。
- HuggingFace Transformers exposes model outputs with `hidden_states`, which is exactly what our residual/span-patching and layer probes need. Source / 来源：HuggingFace Transformers ModelOutput docs, <https://huggingface.co/docs/transformers/master/en/main_classes/output>。

## 5. Local smoke-test evidence / 本机 smoke-test 证据

Smoke helper / 检查脚本：`scripts/check_backend_compatibility.py`。该脚本只检查 vLLM 能否初始化模型，不生成实验样本。

| Test / 测试 | Result / 结果 | Evidence file / 证据文件 | Scientific interpretation / 科学解释 |
|---|---|---|---|
| `qwen35_9b`, vLLM `auto`, TP=4 | failed / 失败 | `logs/backend_compat_qwen35_9b_vllm_auto_20260428.json`; full stdout `logs/backend_compat_qwen35_9b_vllm_auto_full_20260428.log` | vLLM 0.12.0 rejects `Qwen3_5ForConditionalGeneration` at model-config validation. / 在模型配置验证阶段即拒绝该 architecture。 |
| `qwen35_9b`, `model_impl=transformers`, TP=4 | failed / 失败 | `logs/backend_compat_qwen35_9b_vllm_transformers_20260428.json`; full stdout `logs/backend_compat_qwen35_9b_vllm_transformers_full_20260428.log` | Even forced Transformers fallback says this Qwen3.5 implementation is not compatible with vLLM. / 强制 fallback 也不可用。 |
| `gemma4_e4b_it`, vLLM `auto`, TP=1 | failed / 失败 | `logs/backend_compat_gemma4_e4b_it_vllm_auto_20260428.json`; full stdout `logs/backend_compat_gemma4_e4b_it_vllm_auto_full_20260428.log` | vLLM resolves a generic `TransformersMultiModalForCausalLM`, falls back, then fails on audio-tower weight/module mapping. / 退到通用多模态 Transformers backend 后，音频塔权重映射失败。 |

Key local error excerpts / 关键本机错误摘录（为避免冗长，只保留短摘录）：

```text
Qwen3.5 auto: Model architectures ['Qwen3_5ForConditionalGeneration'] are not supported for now.
Qwen3.5 transformers fallback: The Transformers implementation of 'Qwen3_5ForConditionalGeneration' is not compatible with vLLM.
Gemma4 auto: TransformersMultiModalForCausalLM has no vLLM implementation, falling back to Transformers implementation.
Gemma4 auto: no module or parameter named 'model.audio_tower.layers.0.feed_forward1.ffw_layer_1.input_max'.
```

## 6. Why HF remains scientifically necessary / 为什么机制实验仍必须用 HF

For this project, HF is not just a slow implementation detail; it is part of the measurement instrument. / 对本项目而言，HF 不是“慢一点的实现”，而是测量仪器的一部分。

- **Hidden-state access / 隐藏层访问：** E40/E43/E50 need exact layerwise residual states at selected prompt positions. / 需要逐层 residual state。
- **Forward hooks / 前向 hook：** Residual span patch and steering require registering hooks on transformer blocks and replacing specific positions. / patch/steering 需要 hook 指定层与指定 token 位置。
- **MLP/residual decomposition / MLP 与残差分解：** Mechanism claims depend on how the model state changes under controlled interventions, not just on final generated text. / 机制 claim 依赖干预后的状态变化，而不只是最终输出。
- **Reproducibility / 可复现性：** Existing official hidden-state results were generated under HF with audited chat-template and tokenization settings. Changing the backend midstream would require parity reruns. / 中途换后端必须重跑 parity。

Therefore / 因此：

- E40/E43/E44/E50 and future hidden-layer/MLP experiments: **HF only**.
- E48/E49 generation-only controls: **vLLM allowed only when the model architecture initializes cleanly**, with `backend=vllm` recorded.
- Qwen3.5/Gemma4 official P0 runs: **HF four-GPU `device_map=auto` until a new vLLM environment is separately validated**.

## 7. Throughput policy / 吞吐策略

**Current safe policy / 当前安全策略：**

1. Use one tmux queue owning all four GPUs for P0 HF jobs. / 使用一个 tmux 队列独占四卡跑 P0 HF 任务。
2. For HF generation, use `device_map=auto`, `MPLENS_MAX_MEMORY`, larger batch where safe, and persistent logs. / HF 使用自动切分、显存上限和日志。
3. For compatible CausalLM controls, use vLLM TP=4 in the same queue after HF jobs or in a separate queue only when GPUs are idle. / 标准 CausalLM 控制可在 GPU 空闲或排队后用 vLLM TP=4。
4. Do not run two four-GPU sessions concurrently. / 不并发跑两个四卡任务，避免显存冲突和吞吐互相拖垮。
5. Mark every result with backend and decoding settings. / 每个结果记录 backend 与 decoding 设置。

**Why average GPU util may look low / 为什么平均 GPU util 可能低：**

- Autoregressive decoding is sequential over generated tokens. / 自回归生成按 token 串行。
- Multi-GPU `device_map=auto` is model parallelism, not data-parallel training; some GPUs wait for layers on other GPUs. / `device_map=auto` 是模型并行，不是训练式数据并行。
- Long prompts and Python-side post-processing introduce CPU/tokenizer overhead. / 长 prompt 与 Python 后处理会造成 CPU/tokenizer 开销。
- Hidden-state runs deliberately disable some cache paths (`use_cache=False`) to make layer states and patching correct. / 机制实验为了正确读层状态常禁用部分 cache。

## 8. Upgrade path if we later want vLLM Qwen3.5/Gemma4 / 未来若要升级 vLLM 的安全路径

Do **not** upgrade the active official environment in place. / 不要原地升级当前官方环境。

Recommended path / 推荐路径：

1. Create a new conda env, e.g. `passage_prep_vllm_latest_compat`. / 新建独立环境。
2. Install a vLLM version whose official docs list Qwen3.5/Gemma4 support. / 安装官方列出支持的 vLLM 版本。
3. Run `scripts/check_backend_compatibility.py` for `qwen35_9b`, `qwen35_27b`, `gemma4_e4b_it`, `gemma4_26b_a4b_it`, `gemma4_31b_it`. / 先做 smoke。
4. Rerun E42 official-template parity on at least one small and one medium model. / 重跑 E42 parity。
5. Compare HF vs vLLM output distributions on E48 generation-only tasks; do not mix backend results without tags. / 对比 HF/vLLM 分布，不能混标签。
6. Only then promote vLLM Qwen3.5/Gemma4 to official generation backend. / 通过后再升级为官方生成后端。

## 9. Appendix statement for paper / 可放入论文附录的短版表述

English:

> We used HuggingFace Transformers for Qwen3.5/Gemma4 P0 runs because the pinned local vLLM 0.12.0 environment could not reliably initialize these conditional-generation/multimodal checkpoints. Local smoke tests rejected `Qwen3_5ForConditionalGeneration` directly, and Gemma4 fell back to a generic Transformers multimodal backend before failing on weight/module mapping. vLLM was used only for compatible text-only CausalLM generation controls. Mechanistic measurements used HuggingFace because residual-state extraction, layer hooks, and activation patching are part of the measurement procedure.

中文：

> 我们对 Qwen3.5/Gemma4 P0 模型使用 HuggingFace Transformers，是因为本机固定的 vLLM 0.12.0 环境无法可靠初始化这些 conditional-generation / multimodal checkpoint。本机 smoke test 显示，`Qwen3_5ForConditionalGeneration` 会被 vLLM 直接拒绝；Gemma4 虽会退到通用 Transformers multimodal backend，但随后在权重/模块映射上失败。vLLM 只用于架构兼容的 text-only CausalLM 生成控制实验。机制测量使用 HuggingFace，因为 residual state 提取、层级 hook 与 activation patch 本身就是测量过程的一部分。

## 10. Files created by this audit / 本审计新增文件

- `scripts/check_backend_compatibility.py`
- `logs/backend_compat_environment_project_pythonpath_20260428.json`
- `logs/backend_compat_environment_20260428.json`
- `logs/backend_compat_local_model_configs_20260428.json`
- `logs/backend_compat_qwen35_9b_vllm_auto_20260428.json`
- `logs/backend_compat_qwen35_9b_vllm_transformers_20260428.json`
- `logs/backend_compat_gemma4_e4b_it_vllm_auto_20260428.json`
- `logs/backend_compat_qwen35_9b_vllm_auto_full_20260428.log`
- `logs/backend_compat_qwen35_9b_vllm_transformers_full_20260428.log`
- `logs/backend_compat_gemma4_e4b_it_vllm_auto_full_20260428.log`
- Superseded early smoke logs archived at `archive/backend_smoke_misc_20260428/` / 早期已被替代的 smoke 日志已归档。
