# E136 Suspicious-Confidence Adaptive Check / 可疑-置信度自适应检查

- Created / 生成时间：`2026-04-30T18:41:30`
- Scope / 范围：stage-1 post-hoc policy simulation on E132/E133 controlled rows, `thinking=false`, 60 rows per model. / 在 E132/E133 受控行上做第一阶段后验策略模拟，每模型 60 条。
- Data / 数据：`data/processed/e132_suspicious_valid_controls_20260430.jsonl`; source scored rows in `results/E132_E133_suspicious_confidence_probe/`. / 人工标签、gold、error span 只作离线评估，不进入 prompt。
- Policy / 策略：base means use the original pointwise Yes/No decision; always-global rechecks every trace; hidden-global/local rechecks only when a hidden process-risk prefix triggers. / base 是原始 Yes/No；always-global 每条都复查；hidden-global/local 只在 hidden 过程风险触发时复查。
- Cost note / 成本说明：脚本为了公平比较预计算了 global check；真实策略成本看 `hidden_*_check_call_rate`，等于 policy-trigger rate。

## Main Results / 主要结果
| Model / 模型 | Hidden trigger all / 总触发 | Hidden trigger valid / 正确触发 | Hidden trigger invalid / 错误触发 | Plain base invalid accept / 普通基线放过错误 | Plain hidden-local invalid accept / hidden-local 放过错误 | Valid accept after hidden-local / hidden-local 保留正确 |
| --- | --- | --- | --- | --- | --- | --- |
| gemma4_26b_a4b_it | 18/60 = 0.300 [0.199, 0.425] | 6/48 = 0.125 [0.059, 0.247] | 12/12 = 1.000 [0.757, 1.000] | 6/12 = 0.500 [0.254, 0.746] | 5/12 = 0.417 [0.193, 0.680] | 48/48 = 1.000 [0.926, 1.000] |
| gemma4_31b_it | 12/60 = 0.200 [0.118, 0.318] | 0/48 = 0.000 [0.000, 0.074] | 12/12 = 1.000 [0.757, 1.000] | 3/12 = 0.250 [0.089, 0.532] | 2/12 = 0.167 [0.047, 0.448] | 48/48 = 1.000 [0.926, 1.000] |
| qwen35_27b | 14/60 = 0.233 [0.144, 0.354] | 2/48 = 0.042 [0.012, 0.140] | 12/12 = 1.000 [0.757, 1.000] | 4/12 = 0.333 [0.138, 0.609] | 1/12 = 0.083 [0.015, 0.354] | 47/48 = 0.979 [0.891, 0.996] |

## Strict-Prompt Diagnostic / strict 口径诊断
| Model / 模型 | Strict base invalid accept / strict 基线放过错误 | Strict hidden-local invalid accept / strict hidden-local 放过错误 | Strict valid accept after hidden-local / strict hidden-local 保留正确 |
| --- | --- | --- | --- |
| gemma4_26b_a4b_it | 1/12 = 0.083 [0.015, 0.354] | 5/12 = 0.417 [0.193, 0.680] | 48/48 = 1.000 [0.926, 1.000] |
| gemma4_31b_it | 1/12 = 0.083 [0.015, 0.354] | 2/12 = 0.167 [0.047, 0.448] | 48/48 = 1.000 [0.926, 1.000] |
| qwen35_27b | 0/12 = 0.000 [0.000, 0.243] | 1/12 = 0.083 [0.015, 0.354] | 45/48 = 0.938 [0.832, 0.979] |

## Interpretation / 说人话解释

- Qwen3.5-27B: hidden trigger caught all 12 repaired strict-invalid traces while only touching 2/48 valid traces. Plain absolute base accepted 4/12 invalid traces; hidden-local reduced that to 1/12 with 47/48 valid retained. / Qwen 的 hidden 触发很像低成本检查开关：大部分正确题不加检查，错误题被集中复查。
- Gemma4-31B-it: the cleanest case. It triggered on 12/12 invalid and 0/48 valid. Hidden-local reduced plain invalid acceptance from 3/12 to 2/12 while preserving 48/48 valid. / Gemma31 的触发边界最干净。
- Gemma4-26B-A4B-it: hidden trigger still catches all invalid traces, but also triggers 6/48 valid traces. Local check accepts 5/12 invalid under both plain and strict policy, worse than strict base. / Gemma26 说明 hidden signal 不能单独当 oracle；局部复查 prompt 会出现 repair-aware 或语义误读。
- The useful scientific fact is not “adaptive checking solved the task.” It is narrower: hidden process-risk can select most risky rows at low call rate, but whether the second pass uses that evidence depends on the check objective and model family. / 这不是说自适应检查已经解决问题，而是说 hidden 风险信号能低成本选中高风险行；二次检查是否有效仍受 objective 和模型族影响。

## Boundary / 边界

- E136 is a post-hoc filter/recheck simulation, not online generation-time intervention. / E136 是后验筛选模拟，不是在线生成时激活干预。
- The invalid rows are controlled repaired strict-invalid traces, not natural unrepaired ACPI. / 这里的错误行是受控 repaired strict-invalid，不是自然未修复 ACPI。
- Local excerpt selection is hidden-trigger based and visible-text only, but it still uses a second prompt. This supports adaptive checking, not direct proof that the base decoder would self-correct without a prompt. / 局部片段由 hidden 触发选择且只含可见文本，但仍是二次 prompt；它支持自适应检查，不等于证明原 decoder 会自动纠错。

## Next / 下一步

- E136-stage2: online semantic-boundary hidden monitoring during generation, then inject a short local-check instruction only at triggered boundaries. / 在线生成中监控语义边界 hidden 信号，只在触发时追加短检查。
- E137: calibrate threshold per model, especially Gemma26, using suspicious-valid controls and confidence-matched rows. / 按模型校准阈值，特别是 Gemma26。
- E138: test natural E119/E146 repaired/unrepaired ACPI with hidden-trigger checking, to see whether this transfers beyond controlled rows. / 把策略迁移到自然 E119/E146 repaired/unrepaired ACPI。
- E139: compare local-check prompt variants: strict any-wrong-step, repair-aware final proof, and error-local-only. / 比较局部检查 prompt 的不同评价口径。

## Artifacts / 文件

- Runner / 运行脚本：`scripts/run_e136_suspicious_confidence_adaptive_check.py`
- Queue / 队列：`scripts/launch_e136_suspicious_confidence_adaptive_check_queue_20260430.sh`
- Status / 状态：`logs/e136_suspicious_confidence_adaptive_check_status_20260430.jsonl`
- Results / 结果：`results/E136_suspicious_confidence_adaptive_check/`
- JSON summary / 机器可读汇总：`reports/E136_SUSPICIOUS_CONFIDENCE_ADAPTIVE_CHECK_20260430.json`
