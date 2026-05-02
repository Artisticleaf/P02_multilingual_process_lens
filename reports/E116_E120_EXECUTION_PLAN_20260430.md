# E116-E120 Execution Plan / 实验执行规划（2026-04-30）

## 1. Strategy / 策略

E106-E114 已经证明 direct/non-thinking hidden activations 中有强 process-validity evidence，但它也暴露了一个边界：process signal 与 confidence 高度缠绕。下一步不应盲目扩大 claim，而应优先回答两个问题：

1. thinking 模式里“已经得到答案却不停”的收口问题，是否在 hidden/residual/MLP/token-mixer 和 EOS/continue readout 上有可见信号；
2. non-thinking 与 thinking 的差异，是外显 CoT 长短的差异，还是 hidden monitoring/readout 使用方式的差异。

## 2. E116-E118 Immediate Queue / 立即执行队列

Script / 脚本：`scripts/run_e116_e118_thinking_stop_signal_suite.py`  
Queue / 队列：`scripts/launch_e116_e118_thinking_stop_signal_queue_20260430.sh`  
Result dir / 结果目录：`results/E116_E118_thinking_stop_signal/`  
Status log / 状态日志：`logs/e116_e118_thinking_stop_signal_status_20260430.jsonl`

| ID | 实验 | 具体要确认的信息 | 实现方案 |
|---|---|---|---|
| E116 | thinking stop-signal probe | Qwen thinking 在 clean stop、hit-max endless thinking、post-final continuation 这些位置，EOS/continue logits 和 residual/MLP/token-mixer 是否有系统差别。 | 复放 E105/E103 已保存 trace；在 final-answer line、answer-phrase line、post-final +256/+1024 chars、completion_end 捕捉 selected layers 的 residual、MLP、token-mixer/attention-related activations；同时计算 EOS logit 与 continuation token 最大 logit 的 margin。 |
| E117 | post-hoc early-stop policy | 如果模型已经写出 final answer line，hidden stop direction 或 EOS margin 是否足以提示“应该停”，从而减少 endless thinking。 | 用 clean-stop 点作为正例、hit-max completion/post-final continuation 作为负例，训练小样本 stop direction；模拟在 first final-like point 停止，报告 token savings、final-correct retention 和 hit-max 覆盖。 |
| E118 | TG vs NG mechanism contrast | thinking 与 non-thinking 的差别是否主要体现在输出长度/收口，还是 strict verifier hidden process score 也系统变化。 | 读取 E102 既有 TG/NG paired replay summary，和 E116 的 stop-signal 结果合并解释；不把 fallback 数字当作 strict final decision。 |

Static/smoke status / 静态与 smoke：

- `py_compile scripts/run_e116_e118_thinking_stop_signal_suite.py` passed. / 编译通过。
- Smoke: Qwen 1-row replay passed; hook、position mapping、EOS margin、JSON/pt 输出正常。 / 冒烟测试通过。
- Leakage rule: source prompts are reconstructed from original E105/E103 prompts; gold/final labels and manual status are used only offline for grouping and policy simulation. / 泄露边界：模型输入不加入 gold、标签或人工错误信息。

Formal queue parameters / 正式队列参数：

- model: `qwen35_27b`
- source rows: up to 8 E105 closure-policy/canary rows + 6 E103 TG rows
- max replay context: 8192 tokens
- layers: best layer 34 with window 1, i.e. hidden indices 33/34/35

## 3. E119 Natural Hard-Task Expansion / 自然困难题扩样

E119 不和 E116-E118 混在同一个队列里。原因是 E119 是新生成加人工审计，会引入长时间排队和人工审查；E116-E118 是 post-hoc mechanism replay，应该先快速完成，避免互相阻塞。

Planned implementation / 计划实现：

- Extend `answer_first_no_gold` and `neutral/self_check` hard-task generation after E116-E118 finishes. / E116-E118 后扩展 answer-first/no-gold 与 neutral/self_check 困难题生成。
- Keep `thinking=false` and `thinking=true` results separated. / NG/TG 分开。
- Use strict final marker, fallback extraction, hit-max, repaired ACPI, unrepaired ACPI as separate fields. / strict final、fallback、hit-max、repaired/unrepaired 分开。
- Manual/agentic audit only on final-correct rows; audit labels never enter prompts. / 只审 final-correct 行，标签不入 prompt。

## 4. E120 Unified Audit Package / 统一审计包

E120 will be a paper-appendix package that scans official result JSON/JSONL files and emits:

E120 将作为论文附录审计包，扫描官方 JSON/JSONL 并输出：

- mode tag (`DV`, `TV`, `NG`, `TG`, `MI-DV`, `MI-TG`, `PM`);
- prompt leakage counters;
- parser/fallback usage;
- manual-label usage boundaries;
- Wilson confidence intervals for key accept/prevalence rates;
- negative-control notes for hidden probes and first-token readout artifacts.

## 5. Current Claim Boundary / 当前 claim 边界

E116-E118 只能加强 thinking 收口机制和 TG/NG 差异解释；它不会单独证明自然 ACPI 高频，也不会证明完整因果 circuit。若 E116 看到 stop signal，我们可以说：

> There is a measurable hidden/readout signal associated with stopping after a final answer, but current evidence remains post-hoc and small-sample.

中文：

> 模型在写出最终答案后是否该停止，可能有可测的 hidden/readout 信号；但目前它仍是小样本 post-hoc 证据，不是完整因果回路证明。

