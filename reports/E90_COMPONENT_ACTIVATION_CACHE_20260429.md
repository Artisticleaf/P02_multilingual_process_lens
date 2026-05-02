# E90 Component Activation Cache / E90 组件激活缓存（2026-04-29）

- Scope / 范围：在 hard-task repaired/unrepaired ACPI 个案上缓存 selected layers 的 final-token 激活，包括 residual hidden state、token-mixer/attention output、MLP output，以及可用 norm outputs。
- Plain language / 说人话：这不是完整 circuit 证明，而是在同一 strict verifier prompt 下，观察“错误前缀、修复触发点、修复后、完整 trace”这些关键位置的 hidden/residual/MLP 信号如何跟 Yes/No 决策一起移动。

## Main Finding / 主要发现

- Gemma31 repaired ACPI：错误前缀和第一行错误 final answer 仍被 strict verifier 接受；出现 Wait/Correction 风格修复后，Yes-No logit 从强正转强负，best-layer residual、token-mixer、MLP/post-FF 等组件也同步向 invalid 方向移动。
- Gemma26 unrepaired ACPI：完整 trace 仍被接受；best-layer residual 分数偏弱/负，token-mixer 与 attention-norm 在 error prefix 反而偏正，说明这里不是简单“残差里有一个强 invalid 方向但输出头不用”，而是组件证据本身更混杂，最终决策又被答案一致性拉回 Yes。
- 因此 E90 支持一个更细的机制说法：过程有效性信号不是只在 residual 里；MLP/post-feedforward 与 token-mixer/attention 也携带阶段性变化，但不同模型/个案中这些组件对最终 Yes/No 读出的贡献会错配。

## gemma4_26b_a4b_it / unrepaired_acpi

- Cache shape / 缓存形状：`[10, 35, 2816]`；best hidden layer / 最佳 hidden 层：`17`；selected layers / 选中层：`[15, 16, 17, 18, 19]`。
- Leakage audit / 泄露审计：gold=0, labels=0, error_spans=0。

| stage | n | accept | Yes-No | residual | token-mixer | MLP | post-attn-norm | post-FF-norm | input-norm | pre-MLP-norm |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| completion_end | 2 | 1.000 | 7.125 | -0.902 | -0.185 | 0.039 | 0.612 | -3.983 | -2.437 | -0.043 |
| error_span_end | 2 | 1.000 | 4.625 | -0.959 | 1.073 | 0.044 | 2.060 | -2.836 | -1.573 | 0.032 |
| first_final_answer_end | 2 | 1.000 | 7.125 | -0.902 | -0.185 | 0.039 | 0.612 | -3.983 | -2.437 | -0.043 |
| last_final_answer_end | 2 | 1.000 | 7.125 | -0.902 | -0.185 | 0.039 | 0.612 | -3.983 | -2.437 | -0.043 |
| post_repair_240chars | 1 | 0.000 | -3.000 | -2.623 | 0.083 | 0.041 | -0.060 | -5.891 | -2.815 | -0.087 |
| repair_trigger_end | 1 | 0.000 | -5.438 | -0.263 | 0.642 | 0.043 | 1.359 | -2.253 | -0.851 | 0.048 |

Top component shifts / 最大组件位移：

- first_final_answer_end_to_repair_trigger_end: 19:post_feedforward_norm_output +2.389; 18:token_mixer_output +2.216; 17:post_feedforward_norm_output +1.730; 15:post_feedforward_norm_output +1.655; 17:input_norm_output +1.587
- error_span_end_to_completion_end: 16:input_norm_output -2.792; 19:post_feedforward_norm_output -2.572; 18:token_mixer_output -2.572; 15:post_feedforward_norm_output -2.281; 18:post_attention_norm_output -2.013
- error_span_end_to_post_repair_240chars: 19:residual_hidden_state -3.984; 19:post_feedforward_norm_output -3.938; 18:post_feedforward_norm_output -3.578; 17:post_feedforward_norm_output -3.056; 18:residual_hidden_state -2.944

## gemma4_31b_it / repaired_acpi

- Cache shape / 缓存形状：`[54, 35, 5376]`；best hidden layer / 最佳 hidden 层：`34`；selected layers / 选中层：`[32, 33, 34, 35, 36]`。
- Leakage audit / 泄露审计：gold=0, labels=0, error_spans=0。

| stage | n | accept | Yes-No | residual | token-mixer | MLP | post-attn-norm | post-FF-norm | input-norm | pre-MLP-norm |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| completion_end | 9 | 0.111 | -9.062 | -1.431 | -1.263 | -2.994 | -1.150 | -4.299 | -6.511 | -2.365 |
| error_span_end | 9 | 0.889 | 8.128 | 0.373 | 0.554 | -0.126 | 0.480 | 0.297 | -4.251 | -0.868 |
| first_final_answer_end | 9 | 1.000 | 10.972 | 0.813 | 0.781 | -0.073 | 0.673 | 0.482 | -4.216 | -0.794 |
| last_final_answer_end | 9 | 0.111 | -9.062 | -1.431 | -1.263 | -2.994 | -1.150 | -4.299 | -6.511 | -2.365 |
| post_repair_240chars | 9 | 0.000 | -13.010 | -3.200 | -1.812 | -2.819 | -1.741 | -4.423 | -6.627 | -2.329 |
| repair_trigger_end | 9 | 0.111 | -11.181 | -2.877 | -1.565 | -2.438 | -1.494 | -3.761 | -5.355 | -1.985 |

Top component shifts / 最大组件位移：

- first_final_answer_end_to_repair_trigger_end: 36:residual_hidden_state -5.682; 36:post_feedforward_norm_output -4.598; 34:post_feedforward_norm_output -4.244; 35:residual_hidden_state -3.975; 34:residual_hidden_state -3.690
- error_span_end_to_completion_end: 34:post_feedforward_norm_output -4.596; 32:residual_hidden_state +4.373; 35:input_norm_output -4.047; 36:post_feedforward_norm_output -3.895; 36:residual_hidden_state -3.892
- error_span_end_to_post_repair_240chars: 36:residual_hidden_state -4.913; 34:post_feedforward_norm_output -4.720; 36:post_feedforward_norm_output -4.223; 35:input_norm_output -3.933; 35:residual_hidden_state -3.637

## Boundary / 边界

- E90 缓存的是关键 prefix 的 final-token activations，不是全 token 全层轨迹。
- 组件方向来自 E61 controlled language/error grid 的 strict verifier 方向；它能做对比诊断，但不能单独证明训练时的因果生成路径。
- 当前未做 activation patch/causal mediation 到每个组件的输出 logits；下一步应在 E90 缓存基础上做 component-level patch 或 logit-lens/介入读出。
