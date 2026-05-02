# E116-E118 Thinking Stop-Signal Report / thinking 收口信号报告（2026-04-30）

## 1. Scope / 范围

E116-E118 是 Qwen3.5-27B thinking-mode 的 post-hoc mechanism replay，不做新生成。它复用 E105/E103 保存的 thinking traces，在 final-answer line、answer-phrase line、post-final continuation、completion end 等位置捕捉：

- residual hidden state
- MLP output
- token-mixer / attention-related output
- norm outputs
- EOS logit vs continuation-token logit margin

Files / 文件：

- Script / 脚本：`scripts/run_e116_e118_thinking_stop_signal_suite.py`
- Queue / 队列：`scripts/launch_e116_e118_thinking_stop_signal_queue_20260430.sh`
- Result / 结果：`results/E116_E118_thinking_stop_signal/qwen35_27b_e116_e118_thinking_stop_signal_suite.json`
- Activation cache / 激活缓存：`results/E116_E118_thinking_stop_signal/qwen35_27b_e116_e118_component_points.pt`
- Plan / 计划：`reports/E116_E120_EXECUTION_PLAN_20260430.md`

Audit / 审计：

- `py_compile` passed.
- Launcher `bash -n` passed.
- Smoke passed on 1 E105 row.
- Formal queue completed `all_done` at `2026-04-30T01:30:06+08:00`.
- Active workspace audit passed after completion.
- Leakage counters: `gold_answer_in_prompt_rows=0`, `known_trap_note_in_prompt_rows=0`, `manual_labels_in_prompt_rows=0`, `manual_spans_in_prompt_rows=0`.

## 2. E116 Stop-Signal Probe / 收口信号

Data / 数据：

- Source rows: 12 saved thinking traces.
- Activation points: 61.
- Component cache shape: `[61, 15, 5120]`.
- Selected layers: hidden indices 33/34/35.
- Selected stop key: `34:residual_hidden_state`.

Stop-direction training was diagnostic and small-sample:

stop direction 是小样本诊断：

- Positive: clean-stop points where the model wrote an explicit final answer and naturally stopped.
- Negative: hit-max completion-end points and post-final continuation points.

| stop label | n | mean stop score | mean EOS-minus-continuation | mean process score |
|---|---:|---:|---:|---:|
| clean_stop_positive | 6 | 29.345 | -3.781 | 1.662 |
| post_final_continue_negative | 7 | -8.957 | -5.912 | 1.645 |
| unfinished_continue_negative | 10 | -8.075 | -12.904 | 1.290 |
| pre_stop_candidate_ambiguous | 16 | 1.962 | -13.361 | 2.099 |
| ambiguous | 22 | -2.910 | -8.707 | 1.711 |

Selected residual stop direction:

- Positive mean: 29.345
- Negative mean: -8.438
- Threshold: 10.453

Interpretation / 解释：

> Qwen thinking 在“写完答案并真正停止”的位置，与“已经写过答案但继续写”或“撞 token 上限还没收口”的位置，residual hidden state 有明显差异。这个差异不是 process-validity score 本身，因为各组 process score 都大多为正；它更像是“是否应该结束输出”的状态信号。

EOS margin 也有方向性，但弱于 hidden stop score：

- clean-stop 的 EOS-minus-continuation 均值是 -3.781；
- unfinished continuation 是 -12.904；
- post-final continuation 是 -5.912。

这说明 EOS readout 也有 stop 信息，但在这些样本里 EOS 仍通常没有超过常见 continuation token，所以单靠 EOS logit 不是可靠停止规则。

## 3. E117 Post-Hoc Early-Stop Policy / 早停策略模拟

Policy simulation:

```text
candidate = first final-answer line or last answer-phrase line
stop if hidden_stop_score >= 10.453 OR eos_margin >= -6.903
```

| metric | value |
|---|---:|
| final-like candidates | 10 |
| hit-max candidates | 8 |
| final-correct candidates | 9 |
| either-stop rate | 0.600 |
| hidden-stop rate | 0.400 |
| eos-stop rate | 0.400 |
| stopped correct candidates | 6 |
| mean token savings among stopped candidates | 1318.333 |

Important detail / 重要细节：

- The policy stopped 6 candidates, and all 6 were final-correct. / 触发早停的 6 个 candidate 都是 final-correct。
- It did not stop the one known incorrect candidate. / 它没有停在那个已知错误 candidate 上。
- But it missed 3 final-correct candidates. / 但它漏掉了 3 个 final-correct candidate。

Interpretation / 解释：

> 当前 stop signal 有信息收益：它能在一部分“答案已经写出但模型还在继续”的 trace 上提示可以停止，并节省 token。但它还不是可靠部署策略，因为 recall 不够，且阈值来自同一小样本，没有独立校准。

## 4. E118 TG vs NG Contrast / thinking 与 non-thinking 对比

E118 pulls in the existing E102 TG/NG strict-verifier replay summary.

E118 读取 E102 已有 TG/NG 对比：

- NG traces averaged about 1124 completion tokens and had explicit final markers.
- TG traces averaged about 4352 completion tokens in E102 and often lacked strict final markers or hit max.
- TG fallback answers can be correct, but fallback extraction is not a clean final decision.

Interpretation / 解释：

> 当前最稳的 TG/NG 差异不是“thinking 一定更会做题”，而是 thinking 暴露了收口/最终决策问题。模型可能已经在思考中得到答案，但不会稳定提交并停止；non-thinking 则更像压缩输出，反而更容易给出一个可解析的 final answer。

## 5. Scientific Implications / 科学含义

E116-E118 支持一个更细的机制观点：

> process-validity monitoring and stop/commit monitoring are related but not identical. A trace can have positive process-validity scores while still lacking a strong stop/commit signal.

中文：

> “过程对不对”和“是否该提交并停止”不是同一个信号。一个 trace 的过程有效性分数可以是正的，但模型仍然没有稳定进入“收口/提交”状态。

This matters for our main claim:

这对主 claim 的意义是：

- Non-thinking hidden process evidence already exists, but default readout may not use it. / non-thinking hidden 里已有过程证据，但默认读出可能不用。
- Thinking can expose more self-checking, but it introduces a separate final-decision/stop bottleneck. / thinking 会暴露更多自检，但也引入 final-decision/stop 瓶颈。
- ACPI-style trace-selection risk and endless-thinking risk are different failure modes, but both show hidden evidence/readout mismatch. / ACPI trace-selection 风险和 endless-thinking 风险不是同一种失败，但都体现 hidden evidence 与最终读出的错配。

## 6. Boundaries / 边界

- E116-E118 is Qwen-only. / 目前只做了 Qwen。
- Stop direction uses only a small post-hoc sample; it is not a full causal circuit. / stop direction 是小样本 post-hoc，不是完整因果回路。
- The early-stop policy is a diagnostic simulation, not a deployment recommendation. / 早停策略是诊断模拟，不是部署建议。
- The result does not estimate natural unrepaired ACPI prevalence. / 本实验不估计自然 unrepaired ACPI 发生率。

## 7. Next / 下一步

1. E119: expand natural hard-task harvesting after separating NG/TG and strict/fallback final decisions. / 扩大自然困难题采样。
2. E120: build unified appendix audit package across official experiments. / 构建统一审计附录。
3. Optional E121: repeat E116 on Gemma31/Gemma26 if their thinking traces can be collected with clean final markers. / 如果 Gemma thinking 能采到 clean final marker，再复现 stop-signal。
4. Optional E122: confidence-matched stop-direction control, to test whether stop score is just EOS/readout confidence. / 做 confidence-matched stop control。

