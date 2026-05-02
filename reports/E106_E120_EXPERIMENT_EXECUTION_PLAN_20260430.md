# E106-E120 Experiment Execution Plan / 实验执行规划（2026-04-30）

## 0. 当前策略

主线先收紧到 non-thinking / direct-verifier 机制：证明模型不需要显式长 CoT，也能在 hidden residual、token-mixer/attention-related、MLP 中编码 process-validity evidence；但这个证据可能被 readout confidence、final-answer anchor、长自洽后文和 output-label bottleneck 压制。

Thinking 终止机制保留为 P1 小规模诊断，不作为当前主 claim 的必要前提。

## 1. P0 立即执行：E106-E114 non-thinking mechanism suite

统一脚本：`scripts/run_e106_e114_nonthinking_mechanism_suite.py`  
队列脚本：`scripts/launch_e106_e114_nonthinking_mechanism_queue_20260430.sh`  
结果目录：`results/E106_E114_nonthinking_mechanism_suite/`  
状态日志：`logs/e106_e114_nonthinking_mechanism_status_20260430.jsonl`

| ID | 实验 | 要回答的问题 | 实现细节 |
|---|---|---|---|
| E106 | confidence-vs-process 2x2 | hidden 错误信号是不是只是低置信度？ | 在 E61 96 条 valid/invalid trace 上记录 plain absolute Yes/No margin、binary entropy、strict-prompt hidden process score；按 valid/invalid 和 high/low readout confidence 分层。 |
| E107 | matched/partial confidence control | 控制 confidence 后 process signal 是否仍存在？ | confidence-matched valid/invalid pairs；hidden score 对 process label 的 partial correlation 控制 readout confidence 与 entropy。 |
| E108 | process direction vs confidence direction | 两个 hidden direction 是否同轴？ | 每个 held-out task 训练 process-valid direction 与 high-confidence direction，报告 cosine 与 abs cosine。 |
| E109 | steering specificity | process direction 干预是否不同于 confidence direction？ | 对少量 valid 与 over-accepted invalid rows 做 residual patch：process_toward_valid/invalid 与 confidence_toward_high/low，比较 Yes/No margin、confidence 和 flip。 |
| E110 | prefix emergence | 错误信号是在错误步附近出现，还是最终答案后才出现？ | 对 E57/E88/E104 的 audited NG strict ACPI rows 截断到 before-error、error-span-end、repair-trigger、final-answer、completion-end，并投影 E61 process direction。 |
| E111 | long-context dilution | 长自洽后文和答案锚定会不会稀释错误？ | 对 E61 invalid traces 追加 0/300/1200 字符的 self-consistency suffix，比较 hidden score 与 Yes/No margin。 |
| E112 | answer-anchor hidden mediation | final answer anchor 如何影响 hidden/readout？ | 对 E53 shown/removed/masked/wrong 条件重新做 hidden score 与 Yes/No，按 answer condition 与 process validity 汇总。 |
| E114 | hidden-gated verifier | 能否激发 non-thinking 内部潜力降低 ACPI retention？ | 以 plain absolute Yes/No 作为 `base_accept`，模拟 `base_accept AND hidden_process_score>0` 的 filter，比较 base accept、hidden accept、gated accept 对 valid/ACPI 的保留率。 |

### 本轮模型

- `qwen35_27b`
- `gemma4_31b_it`
- `gemma4_26b_a4b_it`
- `glm47_flash_candidate`

### 静态审计与 smoke 状态

- `py_compile`：通过。
- Qwen smoke：通过，8 条 E61 + steering/prefix/dilution/anchor 全链路输出 JSON；修正后 `base_accept` 使用 plain absolute readout，避免用强 strict prompt 掩盖 E114 风险。
- Gemma4-26B-A4B smoke：通过，hook 与 JSON 输出正常。
- GLM-4.7-Flash smoke：通过，hook 与 JSON 输出正常。
- Prompt 泄露边界：strict verifier prompt 只包含 problem 与 visible trace；人工标签、错误 span、修复标签只用于离线分组、prefix 截断和评分。

## 2. P1 thinking 终止机制：E116-E118

| ID | 实验 | 要回答的问题 | 实现细节 |
|---|---|---|---|
| E116 | stop-signal probe | thinking clean stop 是否有 hidden 终止信号？ | 回放 E105 clean-stop、post-final-continuation、hit-max trace；在 `Final answer` 前后、最后 256 tokens、EOS 前 token 采 residual/MLP/token-mixer 和 EOS/continue logits。 |
| E117 | stop steering / early exit | 能否激发终止信号减少 endless thinking？ | 训练 clean-stop minus continue direction；对 final-contract prompt 做小规模 patch 或外部 early-stop policy，比较 token、正确率、post-final continuation。 |
| E118 | TG vs NG same-problem contrast | 显式 CoT 与 latent process signal 差在哪里？ | 同题同模型 TG/NG paired replay，比较 output length、repair markers、hidden process score、clean final stop。 |

P1 不进入当前 tmux 队列。原因：thinking 生成耗时长且 E105 只有一题 clean-stop canary；应先等 P0 non-thinking 结果稳定后再做小规模机制验证。

## 3. P2 统计与审计扩展：E119-E120

| ID | 实验 | 要回答的问题 | 实现细节 |
|---|---|---|---|
| E119 | natural hard-task expansion | 自然 unrepaired ACPI 的置信区间能否收窄？ | 扩大 answer-first/no-gold、algebra、code、table tasks；先 final-correct harvesting，再人工/agent 双审 strict/repaired/unrepaired。 |
| E120 | unified leakage/logic audit package | 论文 appendix 是否可复现可信？ | 每个实验统一输出 prompt leakage counters、span-in-prompt counters、manual label usage、parser rules、CI、negative controls。 |

## 4. 当前执行命令

```bash
tmux new-session -d -s p02_e106_e114_20260430 \
  'cd /home/Awei/P02_multilingual_process_lens && bash scripts/launch_e106_e114_nonthinking_mechanism_queue_20260430.sh 2>&1 | tee logs/e106_e114_nonthinking_mechanism_queue_20260430.log'
```

## 5. 预期论文收益

如果 E106-E114 支持当前假设，我们可以把机制 claim 写得更强但仍谨慎：

> Non-thinking does not mean no process monitoring. Process-validity evidence is already present in hidden activations before explicit CoT, but default pointwise readout can confuse or suppress it under confidence, answer-anchor, long-context self-consistency, and output-format bottlenecks.

中文：

> 关闭显式 thinking 不等于模型没有过程监控。过程有效性证据在 hidden activation 中已经存在；问题是默认 pointwise readout 会被置信度、答案锚定、长自洽上下文和输出格式瓶颈混淆或压制。
