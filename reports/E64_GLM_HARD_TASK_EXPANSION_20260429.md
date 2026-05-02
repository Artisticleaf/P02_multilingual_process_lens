# E64 GLM Hard-Task Expansion / E64 GLM 困难题扩展采样（2026-04-29）

- Generation / 生成：`results/E64_natural_hard_task_expansion/glm47_flash_candidate_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json`
- Manual audit / 人审：`results/E64_natural_hard_task_expansion/glm47_flash_candidate_e64_final_correct_manual_audit.jsonl`
- Audit / 审计：`reports/E64_GLM_HARD_TASK_EXPANSION_AUDIT_20260429.json`
- Plain language / 说人话：把 GLM-4.7-Flash 也放进 AIME-style hard-task 自然生成采样里看。结果是它 final-correct 少，且这 8 条 final-correct trace 人审后都是过程有效；没有发现新的自然 ACPI。

## Generation Summary / 生成汇总

| generated | final-correct | strict marker missing | gold answer in prompt | trap note in prompt |
|---:|---:|---:|---:|---:|
| 72 | 8 (0.111) | 64 | 0 | 0 |

## Manual Process Audit / 人工过程审计

| n final-correct audited | strict valid | repaired valid | strict ACPI | unrepaired ACPI |
|---:|---:|---:|---:|---:|
| 8 | 8 (1.000) | 8 (1.000) | 0 (0.000) | 0 (0.000) |

### By Task / 按题目

| task | n | strict valid | strict ACPI |
|---|---:|---:|---:|
| `aime25_base_divisor_p1` | 6 | 6 | 0 |
| `aime25_icecream_ordered_assign_p3` | 2 | 2 | 0 |

### By Prompt Variant / 按 prompt 变体

| variant | n | strict valid | strict ACPI |
|---|---:|---:|---:|
| `answer_first_no_gold` | 3 | 3 | 0 |
| `neutral` | 2 | 2 | 0 |
| `self_check` | 3 | 3 | 0 |

## Boundary / 边界

- E64 does not contradict the controlled ACPI claim; it reinforces the prevalence boundary: natural unrepaired ACPI is not easy to harvest from hard tasks, especially for GLM in this small k=4 sample. / E64 不反驳受控 ACPI 主张；它强化自然发生率边界：困难题自然未修复 ACPI 并不容易采到，尤其 GLM 在这个 k=4 小样本中 final-correct 本身较少。
- Because only final-correct rows are manually process-audited, E64 cannot estimate overall reasoning quality beyond the reported final-correct rate. / 由于只对 final-correct 行做人审，E64 不能估计整体推理质量，只能报告 final-correct 率与其过程有效性。
- The generation prompts contain no gold answer and no trap note, so these rows are natural hard-task traces rather than answer-anchored controlled traces. / 生成 prompt 不含 gold answer 或 trap note，因此这些是自然困难题 trace，不是 answer-anchor 受控 trace。

## Audit / 审计

- PASS: E64 GLM generation output exists — results/E64_natural_hard_task_expansion/glm47_flash_candidate_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json
- PASS: manual reviewed index set matches final-correct rows — final=[2, 3, 6, 7, 10, 11, 28, 33]; manual=[2, 3, 6, 7, 10, 11, 28, 33]
- PASS: no gold answer in prompts — 0
- PASS: no trap note in prompts — 0
