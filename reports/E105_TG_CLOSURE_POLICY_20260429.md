# E105 TG Closure Policy / Qwen thinking 收口策略（2026-04-29）

## 说人话结论

E105 问的是：Qwen thinking 模式下，模型明明经常算到正确数字，但为什么不提交严格的 `Final answer`？这到底是 4096/8192 token 不够，还是 prompt 收口契约不够强？

结果是分层的：

- 8k capped pilot 中，前两条都撞满 8192 token，0/2 有明确 `Final answer` 行；这说明 8k 仍不足以解决 Qwen thinking 的不收口问题。
- 16k/32k no-timecap canary 说明 Qwen 可以提交最终答案，但最好用强 final-contract prompt。`final_contract_16384` 在 16111 tokens 自然停止，`final_contract_32768` 在 13120 tokens 自然停止，二者都以 `Final answer: 70` 结尾。
- 16k free/budgeted prompt 虽然出现 `Final answer`，但没有干净停止：free_think 撞满 16k 后还写了 341 个字符，budgeted_final 撞满 16k 后还写了 6214 个字符。因此只看 final marker 会高估“模型已经提交答案”。

所以当前安全结论是：Qwen TG 的失败不是“没有算到答案”，而是“收口/最终提交策略不稳定”。在 TG 评估里，fallback 抽取到正确数字不能等同于模型做出了严格 final decision。

## 数据来源

| stage | status | source | n | 说明 |
|---|---|---|---:|---|
| `smoke_4096` | `diagnostic` | `results/E105_tg_closure_policy/_smoke/qwen35_27b_e105_tg_closure_policy.json` | 1 | 4096 token smoke；只用于 parser/泄露检查，不作为 E105 主结论。 |
| `capped_pilot_8192` | `superseded_boundary` | `logs/e105_qwen35_tg_closure_k1_checkpoint_20260429.jsonl` | 2 | 8192 token 有 wall-time/batch cap；被 reviewer stress 取代，但保留为 8k 不收口边界。 |
| `reviewer_stress_16384` | `official_canary` | `logs/e105r_qwen35_canary16k_checkpoint_20260429.jsonl` | 3 | 无 wall-time cap 的 16k canary；只覆盖 base_divisor 一题。 |
| `reviewer_stress_32768` | `official_canary` | `logs/e105r_qwen35_canary32k_checkpoint_20260429.jsonl` | 1 | 无 wall-time cap 的 32k final_contract canary；只覆盖 base_divisor 一题。 |

## Stage 汇总

| stage | n | strict final correct | fallback correct | explicit marker | clean final stop | hit max | mean tokens | mean repair markers |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `capped_pilot_8192` | 2 | 0/2 | 1/2 | 0/2 | 0/2 | 2/2 | 8192.0 | 43.5 |
| `reviewer_stress_16384` | 3 | 3/3 | 3/3 | 3/3 | 1/3 | 2/3 | 16293.0 | 103.7 |
| `reviewer_stress_32768` | 1 | 1/1 | 1/1 | 1/1 | 1/1 | 0/1 | 13120.0 | 80.0 |
| `smoke_4096` | 1 | 0/1 | 1/1 | 0/1 | 0/1 | 0/1 | 2064.0 | 13.0 |

## Official Canary 按策略汇总

| policy | n | strict final correct | explicit marker | clean final stop | hit max | mean tokens |
|---|---:|---:|---:|---:|---:|---:|
| `budgeted_final_16384` | 1 | 1/1 | 1/1 | 0/1 | 1/1 | 16384.0 |
| `final_contract_16384` | 1 | 1/1 | 1/1 | 1/1 | 0/1 | 16111.0 |
| `final_contract_32768` | 1 | 1/1 | 1/1 | 1/1 | 0/1 | 13120.0 |
| `free_think_16384` | 1 | 1/1 | 1/1 | 0/1 | 1/1 | 16384.0 |

## Official Canary 95% Wilson CI

- `reviewer_stress_16384` strict final correct: 3/3 = 1.000, 95% CI [0.438, 1.000]
- `reviewer_stress_16384` clean final stop: 1/3 = 0.333, 95% CI [0.061, 0.792]
- `reviewer_stress_16384` hit max: 2/3 = 0.667, 95% CI [0.208, 0.939]
- `reviewer_stress_32768` strict final correct: 1/1 = 1.000, 95% CI [0.207, 1.000]
- `reviewer_stress_32768` clean final stop: 1/1 = 1.000, 95% CI [0.207, 1.000]
- `reviewer_stress_32768` hit max: 0/1 = 0.000, 95% CI [0.000, 0.793]

## 逐行审计摘要

| stage | policy | task | strict | fallback | marker | clean stop | hit max | tokens | post-final chars | stop reason |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `smoke_4096` | `budgeted_final_4096` | `aime25_base_divisor_p1` | 0 | 1 | 0 | 0 | 0 | 2064 |  | `None` |
| `capped_pilot_8192` | `free_think_8192` | `aime25_base_divisor_p1` | 0 | 1 | 0 | 0 | 1 | 8192 |  | `max_new_tokens` |
| `capped_pilot_8192` | `free_think_8192` | `aime25_integer_pairs_quad_p4` | 0 | 0 | 0 | 0 | 1 | 8192 |  | `max_new_tokens` |
| `reviewer_stress_16384` | `free_think_16384` | `aime25_base_divisor_p1` | 1 | 1 | 1 | 0 | 1 | 16384 | 341 | `max_new_tokens` |
| `reviewer_stress_16384` | `final_contract_16384` | `aime25_base_divisor_p1` | 1 | 1 | 1 | 1 | 0 | 16111 | 0 | `model_stop_or_eos` |
| `reviewer_stress_16384` | `budgeted_final_16384` | `aime25_base_divisor_p1` | 1 | 1 | 1 | 0 | 1 | 16384 | 6214 | `max_new_tokens` |
| `reviewer_stress_32768` | `final_contract_32768` | `aime25_base_divisor_p1` | 1 | 1 | 1 | 1 | 0 | 13120 | 0 | `model_stop_or_eos` |

## 泄露与逻辑审计

- Gold answer in prompt rows / prompt 中含答案行数：0
- Known trap note in prompt rows / prompt 中含陷阱说明行数：0
- Leakage audit passed / 泄露审计通过：True
- E105 没有保存 generation-time hidden states；它只回答收口策略问题。后续 E106/E97 应在 final-contract 条件下保存 thought token、repair marker、final decision token 附近的 residual/MLP/token-mixer/attention-related 激活。

## 论文边界

- 16k/32k canary 只覆盖 `aime25_base_divisor_p1`，不能写成 Qwen TG 在困难题上整体优于 NG。
- `Final answer` 出现在中途但继续输出，不等于 clean final decision。严格口径应优先使用 `clean_final_stop` 或显式 final line 后无后续内容。
- 8192 token 失败与 16k/32k 成功共同说明：本地 HF thinking 评估必须显式报告 token budget、wall-time cap、hit-max 和 post-final continuation。
