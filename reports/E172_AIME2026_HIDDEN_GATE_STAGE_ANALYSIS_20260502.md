# E172 AIME2026 Hidden-Gate Stage Analysis / E172 AIME2026 hidden-gate 阶段分析

Created / 创建时间：`2026-05-02T20:41:40`.

Scope / 范围：MathArena `aime_2026` 30题；baseline 为 non-thinking 原题解答，hidden-gate 为分块生成时读取隐藏层风险，触发后进入 non-thinking controlled-check 分支。

Status boundary / 状态边界：截至本次汇总，正式全量没有完成；只有 `qwen35_27b` 有正式 baseline 部分 checkpoint，hidden-gate 只有 `qwen35_27b` smoke。

Claim boundary / claim 边界：hidden-gate 是受控思考触发机制，不是答案 oracle；答案只用于离线评分。partial checkpoint 不能外推为 30 题成绩。

## Landing Summary / 落盘总览

| model | participated | formal baseline state | formal baseline n/correct/acc | formal gate state | smoke gate n/correct/trigger | hidden obs |
|---|---:|---|---:|---|---:|---:|
| qwen35_27b | True | partial_checkpoint_without_done | 10/10/1.000 | not_started | 1/0/1 | 1 |
| gemma4_31b_it | False | not_started | 0/0/NA | not_started | 0/0/0 | 0 |
| gemma4_26b_a4b_it | False | not_started | 0/0/NA | not_started | 0/0/0 | 0 |

## Formal Baseline Rows / 正式 baseline 已落盘题目

Only `qwen35_27b` has formal checkpoint rows. / 只有 `qwen35_27b` 有正式 checkpoint 行。

| idx | task | gold | extracted | correct | tokens | marker | hit max |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | `e172_aime2026_p01` | 277 | 277 | True | 1539 | True | False |
| 2 | `e172_aime2026_p02` | 62 | 62 | True | 2626 | True | False |
| 3 | `e172_aime2026_p03` | 79 | 79 | True | 1168 | True | False |
| 4 | `e172_aime2026_p04` | 70 | 70 | True | 4143 | True | False |
| 5 | `e172_aime2026_p05` | 65 | 65 | True | 1215 | True | False |
| 6 | `e172_aime2026_p06` | 441 | 441 | True | 1363 | True | False |
| 7 | `e172_aime2026_p07` | 396 | 396 | True | 2309 | True | False |
| 8 | `e172_aime2026_p08` | 244 | 244 | True | 2187 | True | False |
| 9 | `e172_aime2026_p09` | 29 | 29 | True | 11382 | True | False |
| 10 | `e172_aime2026_p10` | 156 | 156 | True | 8249 | True | False |

## Hidden-Gate Smoke / hidden-gate smoke

| idx | task | gold | extracted | correct | tokens | marker | hit max | trigger | top risk | threshold |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `e172_aime2026_p01` | 277 | 5 | False | 608 | False | True | True | 1.810 | 1.412 |

## Hidden-State Observations / 隐藏层观测

| model | source | component | visible span | validity score | risk | threshold | crossed | pred_process_valid | yes-minus-no | entropy |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| qwen35_27b | `logs/e172_aime2026_hidden_gate_qwen35_27b_observations_smoke_20260502.jsonl` | `35:residual_hidden_state` | Let $t_P$ be | -1.810 | 1.810 | 1.412 | True | True | 0.688 | 0.063 |

## Interpretation / 综合解释

- Formal AIME2026 completion / 正式题目完成：`qwen35_27b` completed only problems 1-10 in the formal baseline checkpoint, all 10 correct with final markers and no hit-max rows. This is `10/30` coverage, not a complete 30-question score.
- Model coverage / 模型覆盖：`gemma4_31b_it` and `gemma4_26b_a4b_it` were planned in the launcher but have no E172 generated rows or status start events.
- Hidden-gate evidence / hidden-gate 证据：the only hidden observation is the Qwen smoke row. The E166-calibrated `35:residual_hidden_state` risk crossed threshold (`1.810 >= 1.412`) on the valid-looking span `Let $t_P$ be`, which triggered the controlled branch.
- Controlled branch outcome / controlled 分支结果：the smoke controlled branch hit its 512-token cap, produced no final marker, and the fallback extraction was wrong (`5` vs gold `277`). This is a false-positive or over-early-trigger warning for the current E172 gate settings, not a repair success.
- Claim status / 主张状态：E172 currently supports pipeline/task-bank readiness and partial Qwen baseline competence on the first 10 AIME2026 rows. It does not yet support any full-model comparison, AIME2026 30题 accuracy claim, or hidden-gate improvement claim.

Machine-readable KG / 机器可读 KG：`reports/E172_AIME2026_CLAIM_KG_20260502.json`. KG image / KG 图片：`reports/E172_AIME2026_KG_20260502.svg`.
