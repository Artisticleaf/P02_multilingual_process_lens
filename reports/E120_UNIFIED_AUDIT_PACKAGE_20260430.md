# E120 Unified Audit Package / 统一审计包（2026-04-30）

## 1. Purpose / 目的

This package summarizes official-facing audit facts after E106-E118. It is an appendix scaffold, not a new model experiment.

本包汇总 E106-E118 后的官方审计事实。它是 appendix 草稿，不是新的模型实验。

## 2. Mode Boundary / 模式边界

| mode | meaning | current use |
|---|---|---|
| DV | direct/non-thinking verifier | E42/E60/E61/E106-E114 verifier results |
| MI-DV | direct verifier mechanism inspection | E65/E78/E90/E106-E114 hidden/component probes |
| NG | non-thinking generation | E57/E88 natural hard-task samples |
| TG | thinking generation | E92/E103/E105 generation diagnostics |
| MI-TG | thinking mechanism replay | E116-E118 stop-signal replay |
| PM | post-hoc simulation/statistics | E58/E83/E89/E120 |

## 3. E106-E114 Audit / non-thinking 机制审计

| model | hidden AUC | confidence AUC | partial corr | cosine | ACPI base | ACPI gated | valid gated | leakage |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `gemma4_26b_a4b_it` | 0.970 | 0.832 | 0.737 | 0.935 | 0.458 | 0.000 | 0.792 | PASS |
| `gemma4_31b_it` | 1.000 | 0.991 | 0.812 | 0.989 | 0.458 | 0.000 | 1.000 | PASS |
| `glm47_flash_candidate` | 0.997 | 0.978 | 0.650 | 0.994 | 0.458 | 0.042 | 0.958 | PASS |
| `qwen35_27b` | 1.000 | 0.888 | 0.882 | 0.977 | 0.375 | 0.000 | 0.958 | PASS |

Key boundary / 关键边界：process signal and confidence are highly aligned; hidden gate works as a diagnostic filter, not a calibrated deployed verifier.

## 4. E116-E118 Audit / thinking 收口审计

- Model / 模型：`qwen35_27b`
- Mode / 模式：`MI-TG`
- Component cache shape / 激活缓存形状：`[61, 15, 5120]`
- Selected stop key / stop 方向：`34:residual_hidden_state`
- Stop positive mean / clean-stop 均值：`29.345`
- Stop negative mean / continuation 均值：`-8.438`
- Stop threshold / 阈值：`10.453`
- Policy candidates / 候选点：`10`
- Either-stop rate / 触发率：`0.600`
- Stopped correct candidates / 早停且正确：`6/9`
- Mean token savings among stopped / 触发样本平均省 token：`1318.333`
- Leakage / 泄露：`PASS`

Boundary / 边界：Qwen-only, post-hoc, small-sample; useful as a stop/commit signal, not a full causal circuit.

## 5. Remaining Risks / 剩余风险

- Natural unrepaired ACPI prevalence still needs larger E119 harvesting. / 自然 unrepaired ACPI 仍需要 E119 扩样。
- Thinking verifier (`TV`) remains separate from direct first-token verifier (`DV`). / thinking verifier 仍需和 direct first-token verifier 分开。
- Hidden probes need threshold calibration and cross-model replication before being described as deployable filters. / hidden probe 需要阈值校准和跨模型复现。
- E116 stop signal is distinct from process-validity signal; do not merge them into one claim. / E116 stop 信号不能和过程有效性信号混成一个 claim。

## 6. Current Safe Claim / 当前安全 claim

> Controlled strict ACPI trace-selection risk is robust in direct/non-thinking verifier settings. Hidden activations contain process-validity evidence, but confidence, objective, threshold, answer anchoring, repair-aware reading, long self-consistency, and output/readout format determine whether final decisions use it. Thinking adds a separate stop/commit bottleneck: a model can have valid process evidence and still fail to submit and stop cleanly.

中文：

> 在 direct/non-thinking verifier 中，受控 strict ACPI trace-selection 风险稳健存在。hidden activation 中有过程有效性证据，但最终决策是否使用它，取决于置信度、目标、阈值、答案锚定、repair-aware 阅读、长自洽后文和输出读出格式。thinking 又额外引入 stop/commit 瓶颈：模型可以已经有有效过程证据，却仍然不能稳定提交并停止。
