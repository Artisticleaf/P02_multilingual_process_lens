# E36/E37 Queued Mechanism Experiments / E36/E37 已排队机制实验

Date / 日期: 2026-04-27 CST

## Why these experiments / 为什么做这两组实验

E34 showed that four of five E31 non-discount traps have clean residual support/error-span signals, but the inequality-boundary case is weak and still heavily accepted by verifiers. / E34 显示 E31 的五类非折扣陷阱中有四类存在干净 residual support/error-span 信号，但不等式边界样例信号弱，而且仍被 verifier 明显接受。

This boundary is scientifically useful because the bad trace contains both an invalid phrase and an immediate correction: it says `between 3 and 7, inclusive`, but then lists `4, 5, 6, and 7`. / 这个边界样例有科学价值，因为坏 trace 同时包含错误短语和立即修正：它写了 `between 3 and 7, inclusive`，但随后列出了正确集合 `4, 5, 6, and 7`。

Therefore the next question is not just whether a hidden signal exists. The better question is which part of the trace the verifier relies on: the wrong local wording, the later correct enumeration, or the final answer-consistent overall trajectory. / 因此下一步不只是问隐藏信号是否存在，而是问 verifier 到底依赖 trace 的哪一部分：局部错误表述、后续正确枚举，还是与最终答案一致的整体轨迹。

## E36 / E36

E36 splits the same inequality valid/bad pair into five span variants: full condition, lower-bound phrase, upper-bound phrase, downstream correct list, and a longer clause that includes both the wrong wording and the correction. / E36 将同一个不等式 valid/bad pair 拆成五个 span 变体：完整条件、下界短语、上界短语、后续正确列表，以及同时包含错误表述和修正的长子句。

Expected information gain / 预期信息收益：

- If only the downstream correct list produces strong patch effects, the verifier is mainly using later correction/final-answer consistency. / 如果只有后续正确列表产生强 patch 效应，说明 verifier 主要使用后续修正和答案一致性。
- If the full wrong condition produces strong clean effects, the local semantic error is represented but underused at the final decision. / 如果完整错误条件产生强干净效应，说明局部语义错误被表征了，但最终决策没有充分使用。
- If all variants remain weak, inequality boundary wording is a genuine hard case for this verifier lens. / 如果所有变体都弱，说明边界量词确实是该 verifier lens 的困难样例。

Files / 文件：`configs/e36_inequality_boundary_span_variants.yaml`, `scripts/summarize_e36_inequality_boundary.py`.

## E37 / E37

E37 reruns the layerwise verifier logit lens on the E31 non-discount sibling pairs for Qwen14 and Qwen3.5-9B. / E37 在 E31 非折扣 sibling pair 上重新运行分层 verifier logit lens，模型为 Qwen14 和 Qwen3.5-9B。

Purpose / 目的：test whether the residual-patch signal aligns with a middle-layer decision signal that later disappears or gets re-entangled at the final Yes/No output. / 目的在于检验 residual patch 信号是否对应中层决策信号，以及这个信号是否在最终 Yes/No 输出前消失或被重新纠缠。

This directly targets the mechanism claim: hidden evidence may exist, but the absolute verifier objective and threshold can still map it to acceptance. / 这直接对应机制主张：隐藏证据可能存在，但绝对式 verifier 的目标和阈值仍可能把它映射为接受。

## Queue status / 排队状态

`gemma4_31b_it` is still downloading and will run its four-GPU core suite first through `gemma31_postdownload`. To avoid GPU contention, E36/E37 are queued in tmux session `e36_e37_after_gemma31` and will start only after `gemma31_postdownload` ends. / `gemma4_31b_it` 仍在下载，并会先通过 `gemma31_postdownload` 运行四卡核心套件。为了避免抢占 GPU，E36/E37 已排队在 tmux 会话 `e36_e37_after_gemma31` 中，只会在 `gemma31_postdownload` 结束后启动。

Logs / 日志：

- `logs/gemma4_31b_it_postdownload_hf4gpu_suite_driver.log` / Gemma4-31B 下载后核心套件日志。
- `logs/E36_E37_after_gemma31_driver.log` / E36/E37 排队与运行总日志。
- `logs/E36_qwen3_14b_inequality_span_variants.log` and `logs/E36_qwen35_9b_inequality_span_variants.log` / E36 两个模型日志。
- `logs/E37_qwen3_14b_e31_layerwise_lens.log` and `logs/E37_qwen35_9b_e31_layerwise_lens.log` / E37 两个模型日志。
