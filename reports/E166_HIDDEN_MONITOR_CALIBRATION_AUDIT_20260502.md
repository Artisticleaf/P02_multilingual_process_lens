# E166 Hidden-Monitor Calibration Audit / E166 hidden monitor 校准审计

Date / 日期：`2026-05-02T01:32:47`.

## Plain-Language Result / 说人话结论

- E166 now has full three-model causal replay results. / E166 已有三模型全量因果 replay 结果。
- The prompt uses only the problem and the current prefix; manual error spans are offline labels only. / prompt 只含题目和当前 prefix；人工错步只作离线标签。
- Qwen35 and Gemma31 show strong hidden/component separation between true error-span ends and valid prefixes. / Qwen35 和 Gemma31 的隐藏/组件信号能强地区分真实错步结束点和正确 prefix。
- Gemma MoE also has usable signal, but it is weaker and should be reported separately. / Gemma MoE 也有可用信号，但更弱，应单独报告。
- Yes/No diagnostic logits are not enough for MoE; component states are the main evidence. / Yes/No 诊断 logit 对 MoE 不够，component state 才是主要证据。

## Best Monitor Per Model / 每个模型的最佳 monitor

| model | best key | target-vs-valid AUC | target-vs-non-target AUC | high-precision target recall | valid false-trigger | target top1 | target top2 |
|---|---|---:|---:|---:|---:|---:|---:|
| `qwen35_27b` | `35:residual_hidden_state` | 0.981 | 0.761 | 95.2% | 11.5% | 47.6% | 76.2% |
| `gemma4_31b_it` | `33:post_attention_norm_output` | 0.964 | 0.813 | 88.1% | 11.5% | 54.8% | 92.9% |
| `gemma4_26b_a4b_it` | `17:post_attention_norm_output` | 0.895 | 0.785 | 61.9% | 11.5% | 73.8% | 95.2% |

## Top Component Keys / 组件信号排序

### qwen35_27b

| key | target-vs-valid AUC | target-vs-non-target AUC | target recall @valid90 | valid false-trigger |
|---|---:|---:|---:|---:|
| `35:residual_hidden_state` | 0.981 | 0.761 | 95.2% | 11.5% |
| `35:post_attention_norm_output` | 0.969 | 0.752 | 85.7% | 11.5% |
| `33:token_mixer_output` | 0.947 | 0.772 | 85.7% | 11.5% |
| `34:post_attention_norm_output` | 0.960 | 0.720 | 90.5% | 11.5% |
| `34:residual_hidden_state` | 0.961 | 0.740 | 85.7% | 11.5% |
| `35:input_norm_output` | 0.961 | 0.737 | 83.3% | 11.5% |
| `33:post_attention_norm_output` | 0.943 | 0.758 | 85.7% | 11.5% |
| `34:mlp_output` | 0.951 | 0.680 | 85.7% | 11.5% |

### gemma4_31b_it

| key | target-vs-valid AUC | target-vs-non-target AUC | target recall @valid90 | valid false-trigger |
|---|---:|---:|---:|---:|
| `33:post_attention_norm_output` | 0.964 | 0.813 | 88.1% | 11.5% |
| `33:token_mixer_output` | 0.943 | 0.821 | 78.6% | 11.5% |
| `35:residual_hidden_state` | 0.932 | 0.740 | 83.3% | 11.5% |
| `35:pre_mlp_norm_output` | 0.929 | 0.712 | 88.1% | 11.5% |
| `yes_no_diagnostic` | 0.901 | 0.754 | 73.8% | 11.5% |
| `35:input_norm_output` | 0.902 | 0.763 | 69.0% | 11.5% |
| `33:residual_hidden_state` | 0.895 | 0.762 | 61.9% | 11.5% |
| `33:pre_mlp_norm_output` | 0.892 | 0.795 | 54.8% | 11.5% |

### gemma4_26b_a4b_it

| key | target-vs-valid AUC | target-vs-non-target AUC | target recall @valid90 | valid false-trigger |
|---|---:|---:|---:|---:|
| `17:post_attention_norm_output` | 0.895 | 0.785 | 61.9% | 11.5% |
| `17:token_mixer_output` | 0.824 | 0.751 | 33.3% | 11.5% |
| `17:pre_mlp_norm_output` | 0.835 | 0.703 | 33.3% | 11.5% |
| `17:post_feedforward_norm_output` | 0.788 | 0.728 | 45.2% | 11.5% |
| `17:residual_hidden_state` | 0.809 | 0.754 | 31.0% | 11.5% |
| `16:token_mixer_output` | 0.801 | 0.714 | 28.6% | 11.5% |
| `18:residual_hidden_state` | 0.779 | 0.672 | 38.1% | 11.5% |
| `18:input_norm_output` | 0.786 | 0.734 | 21.4% | 11.5% |

## Interpretation / 解释

- `target-vs-valid AUC` asks: do true wrong-step endpoints look riskier than correct prefixes? / `target-vs-valid AUC` 问的是：真实错步结束点是否比正确 prefix 更像高风险。
- `target-vs-non-target AUC` asks: can the monitor localize the exact wrong boundary rather than merely saying the whole trace is bad? / `target-vs-non-target AUC` 问的是：monitor 是否能定位具体错步，而不是只知道这条 trace 整体不对。
- High-precision threshold is set at the 90th percentile of valid controls, so valid false-trigger is capped near 10% on this calibration set. / 高精度阈值取正确 prefix 的 90 分位，因此本校准集上正确 prefix 误触发约 10%。
- E167 should use these hidden-derived thresholds/spans and keep oracle manual spans only as an upper bound. / E167 应使用这些 hidden-derived 阈值/span，人工 oracle span 只能当上界。
