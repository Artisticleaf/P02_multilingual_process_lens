# E32 Gemma4 Medium 四卡运行状态与阶段结果（2026-04-27）

## 1. 当前有没有卡死

结论：没有看到训练或实验卡死。

- 2026-04-27 22:07-22:14 CST 期间，四张 RTX 5090 基本空闲：GPU0 约 17 MiB，GPU1/2/3 约 2 MiB，利用率 0%。
- 当时真正运行的是 `gemma4_31b_it` 下载进程，不是训练进程：PID `756393`，命令为 `hf download google/gemma-4-31B-it ...`。
- 下载没有卡死：两个 `.incomplete` safetensors 文件在 25 秒内从约 5.33/5.32 GB 增长到约 5.50/5.49 GB；22:14 时模型目录已到 15 GB，22:16 时已到 17 GB。
- 因此当前瓶颈是模型下载，不是 GPU 计算。GPU 空闲是正常现象。

## 2. 是否应该“所有模型都用四卡 vLLM”

结论：需要统一四卡脚本，但不应该强制所有模型都走 vLLM。

原因很具体：

- vLLM 适合黑箱生成、绝对式 Yes/No verifier 打分、批量 logprob 评分。
- vLLM 不适合 hidden layer、residual span patch、MLP/head 分解，因为这些实验需要中间激活和 hook。
- Gemma4-26B-A4B 在本机 vLLM 0.12.0 下不能稳定加载：补了 `top_k` 后，又在权重加载时报 `model.language_model.layers.0.layer_scalar` 找不到。也就是说这不是“吞吐设置没调好”，而是当前 vLLM/Transformers fallback 与该 checkpoint 结构不完全兼容。
- 同一个 Gemma4-26B-A4B 用 HuggingFace `device_map=auto` 四卡加载可以跑通，且本轮四个核心 verifier 实验已经完成。

所以统一策略应是：黑箱实验优先走四卡 vLLM；vLLM 不支持的模型族自动回退到四卡 HuggingFace；机制实验一律走 HuggingFace hook。

## 3. 已落盘的新运行脚本

- `scripts/launch_blackbox_4gpu_suite.sh`：统一四卡黑箱 verifier suite。默认 `MPLENS_BACKEND=auto`，非 Gemma4 走 vLLM，Gemma4 走 HuggingFace 四卡 `device_map=auto`。
- `scripts/run_manual_trace_verifier.py`：新增 `--max-model-len`、`--max-rows`，并在结果 JSON 里记录 `backend="hf"` 和运行参数。
- `scripts/run_manual_trace_verifier_vllm.py`：保留为 vLLM 批量版本，适合 vLLM 支持的模型。

示例命令：

```bash
scripts/launch_blackbox_4gpu_suite.sh gemma4_26b_a4b_it core
scripts/launch_blackbox_4gpu_suite.sh gemma4_31b_it core
MPLENS_BACKEND=vllm scripts/launch_blackbox_4gpu_suite.sh qwen35_27b core
MPLENS_BACKEND=hf scripts/launch_blackbox_4gpu_suite.sh gemma4_26b_a4b_it e31
```

## 4. Gemma4-26B-A4B 已完成结果

输出目录：

- `results/S6_lexical_grid_absolute_verifier_hf/gemma4_26b_a4b_it_manual_trace_verifier.json`
- `results/E28_counterfactual_answer_masking_absolute_verifier_hf/gemma4_26b_a4b_it_manual_trace_verifier.json`
- `results/E30_non_discount_absolute_verifier_hf/gemma4_26b_a4b_it_manual_trace_verifier.json`
- `results/E31_non_discount_counterfactual_absolute_verifier_hf/gemma4_26b_a4b_it_manual_trace_verifier.json`

关键事实如下。

| 实验 | 提示/目标 | 英文过程错误误接受 | 中文过程错误误接受 | 解释 |
|---|---:|---:|---:|---|
| S6 折扣真实 ACPI | process-only | 1.000 | 1.000 | 26B-A4B 和小 Gemma4 一样，对选出的折扣 ACPI 过程错误完全接受。 |
| S6 折扣真实 ACPI | training-candidate | 0.000 | 0.667 | 英文训练清洗提示更严格，中文仍明显过度接受。 |
| E28 反事实/答案遮蔽 | process-only | 0.778 | 0.667 | 换掉局部无效词汇会压低边际，但二值判断仍常接受。 |
| E28 反事实/答案遮蔽 | training-candidate | 0.222 | 0.667 | 英文训练清洗目标能缓解，中文不稳。 |
| E30 自然非折扣 ACPI | process-only | 1.000 | 1.000 | 唯一非折扣自然 ACPI 仍被完全接受。 |
| E30 自然非折扣 ACPI | training-candidate | 0.000 | 1.000 | 英文清洗目标拒绝，中文清洗目标仍接受。 |
| E31 受控非折扣 | process-only | 0.467 | 0.600 | 26B-A4B 比小 Gemma4 严格，但仍大量接受过程错误。 |
| E31 受控非折扣 | training-candidate | 0.267 | 0.467 | 更严格目标有帮助，但没有解决。 |

如果只看 E31 的答案正确但过程错误（ACPI）行：

- process-only 英文 ACPI 误接受率为 0.800；中文为 0.800。
- training-candidate 英文 ACPI 误接受率为 0.600；中文为 0.400。

这说明 26B-A4B 不是简单复刻小 Gemma4：它在受控非折扣陷阱上更保守一些；但主现象仍存在，即正确最终答案会让绝对 verifier 放过局部过程错误。

## 5. Gemma4-31B 当前状态

- `gemma4_31b_it` 还在下载，未卡死。
- 已开一个 tmux 守护会话：`gemma31_postdownload`。它会等待 PID `756393` 结束，检查 safetensors 是否完整，然后自动运行：

```bash
scripts/launch_blackbox_4gpu_suite.sh gemma4_31b_it core
```

- 守护日志：`logs/gemma4_31b_it_postdownload_hf4gpu_suite_driver.log`。
- 下载日志：`logs/gemma4_31b_it_download.log`。

## 6. 对科研主张的影响

本轮 26B-A4B 结果支持三个更细的说法：

1. 现象不是只出现在小模型。26B-A4B 在 S6/E30 的核心 ACPI 上仍会过度接受。
2. 模型规模变大不等于 verifier 风险自动消失。E31 中 26B-A4B 确实比小 Gemma4 更严格，但 ACPI 误接受仍很高。
3. 目标函数很关键。同一个模型在 process-only 与 training-candidate、英文与中文提示之间差异明显，支持“verifier objective/threshold mismatch”而不是“模型完全看不见错误”。

## 7. 下一步

- 等 `gemma4_31b_it` 下载完成后，自动跑同一套 S6/E28/E30/E31，比较 31B 与 26B-A4B、小 Gemma4、Qwen3.5-27B 的差异。
- 如果 31B 也在 S6/E30 高接受，而在 E31 局部更严格，就可以把结论写成“规模可以改变阈值，但不消除 ACPI trace-selection 风险”。
- 机制实验不要走 vLLM；下一步仍应回到 Qwen14 S6 L14 稳健 span，拆 head/MLP/残差路径。
