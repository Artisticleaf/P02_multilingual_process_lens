# E100-E102 Batch/Mode Hidden Contrast / batch 与 thinking 模式机制审计（2026-04-29）

## 说人话结论

- E100 检查固定 token 序列在 batch=1/2/4 下 residual、MLP、token-mixer、logits 是否改变；这是为了排除 batch size 污染 hidden 机制结论。
- E101 是小样本生成敏感性，不作为自然发生率；它只回答 batch size 会不会让现场生成内容不同。
- E102 比较已有 Qwen thinking/non-thinking trace 的内容长度、收口情况、repair marker，以及同一 strict verifier hidden process-validity 读数。

## E100 固定序列 batch 不变性

| batch | component | n | min cosine | max rel L2 | max abs |
|---:|---|---:|---:|---:|---:|
| 1 | 33:input_norm_output | 17 | 1 | 0 | 0 |
| 1 | 33:mlp_output | 17 | 1 | 0 | 0 |
| 1 | 33:post_attention_norm_output | 17 | 1 | 0 | 0 |
| 1 | 33:residual_hidden_state | 17 | 1 | 0 | 0 |
| 1 | 33:token_mixer_output | 17 | 1 | 0 | 0 |
| 1 | 34:input_norm_output | 17 | 1 | 0 | 0 |
| 1 | 34:mlp_output | 17 | 1 | 0 | 0 |
| 1 | 34:post_attention_norm_output | 17 | 1 | 0 | 0 |
| 1 | 34:residual_hidden_state | 17 | 1 | 0 | 0 |
| 1 | 34:token_mixer_output | 17 | 1 | 0 | 0 |
| 1 | 35:input_norm_output | 17 | 1 | 0 | 0 |
| 1 | 35:mlp_output | 17 | 1 | 0 | 0 |
| 1 | 35:post_attention_norm_output | 17 | 1 | 0 | 0 |
| 1 | 35:residual_hidden_state | 17 | 1 | 0 | 0 |
| 1 | 35:token_mixer_output | 17 | 1 | 0 | 0 |
| 1 | logits | 17 | 1 | 0 | 0 |
| 2 | 33:residual_hidden_state | 17 | 1 | 0.01062 | 0.5 |
| 2 | 34:mlp_output | 17 | 0.9997 | 0.02609 | 0.1016 |
| 2 | 34:residual_hidden_state | 17 | 1 | 0.01134 | 0.5 |
| 2 | 34:token_mixer_output | 17 | 0.9998 | 0.02213 | 0.09241 |
| 2 | 35:residual_hidden_state | 17 | 0.9999 | 0.0114 | 0.5 |
| 2 | logits | 17 | 0.9999 | 0.01308 | 0.25 |
| 4 | 33:residual_hidden_state | 17 | 0.9999 | 0.01306 | 0.75 |
| 4 | 34:mlp_output | 17 | 0.9997 | 0.02625 | 0.09375 |
| 4 | 34:residual_hidden_state | 17 | 0.9999 | 0.0165 | 1 |
| 4 | 34:token_mixer_output | 17 | 0.9997 | 0.02526 | 0.1073 |
| 4 | 35:residual_hidden_state | 17 | 0.9999 | 0.01181 | 0.5 |
| 4 | logits | 17 | 0.9998 | 0.02362 | 0.3125 |

## E101 小样本生成敏感性

| batch | mode | n | mean tokens | hit max | final marker | final correct |
|---:|---|---:|---:|---:|---:|---:|
| 1 | NG_neutral | 2 | 512 | 1 | 0 | 0 |
| 1 | TG_boxed_neutral | 2 | 512 | 1 | 0 | 0 |
| 2 | NG_neutral | 2 | 512 | 1 | 0 | 0 |
| 2 | TG_boxed_neutral | 2 | 512 | 1 | 0 | 0 |
| 4 | NG_neutral | 2 | 512 | 1 | 0 | 0 |
| 4 | TG_boxed_neutral | 2 | 512 | 1 | 0 | 0 |

## E102 thinking vs non-thinking trace 读数

| slice type | slice | n | mean tokens | hit max | accept | Yes-No |
|---|---|---:|---:|---:|---:|---:|
| all | all | 17 | 2643 | 0.1176 | 0.7059 | 1.86 |
| generation_mode | NG | 9 | 1124 | 0 | 0.6667 | 2.458 |
| generation_mode | TG | 8 | 4352 | 0.25 | 0.75 | 1.188 |
| source | NG_E57 | 6 | 1025 | 0 | 1 | 4.813 |
| source | NG_E88_answer_first | 3 | 1322 | 0 | 0 | -2.25 |
| source | TG_E92 | 6 | 3072 | 0 | 0.6667 | 1 |
| source | TG_E92_boxed_truncated | 2 | 8192 | 1 | 1 | 1.75 |

### Paired same-task/same-variant deltas

| task | variant | TG tokens | NG tokens | delta tokens | delta Yes-No | delta best residual |
|---|---|---:|---:|---:|---:|---:|
| aime25_base_divisor_p1 | neutral | 3072 | 934 | 2138 | -4.875 | -1.068 |
| aime25_base_divisor_p1 | neutral | 3072 | 934 | 2138 | -4.625 | -2.073 |
| aime25_base_divisor_p1 | answer_first_no_gold | 3072 | 1415 | 1657 | 5.5 | 3.124 |
| aime25_base_divisor_p1 | answer_first_no_gold | 3072 | 1415 | 1657 | 5.25 | 3.112 |
| aime25_base_divisor_p1 | self_check | 3072 | 1014 | 2058 | -3 | -0.9822 |

## 边界

- E100/E102 是 replay，不是新生成；它们适合做机制审计，不适合估计自然发生率。
- E101 的 token 上限故意很低，目的是避免 endless thinking；hit-max 本身就是要记录的现象。
