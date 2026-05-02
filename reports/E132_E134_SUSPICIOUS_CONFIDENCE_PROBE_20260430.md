# E132-E134 Suspicious/Confidence Probe / 可疑但正确与置信度匹配探针

- Created / 生成时间：`2026-04-30T18:04:14`
- Scope / 范围：Qwen3.5-27B、Gemma4-31B-it、Gemma4-26B-A4B-it；`thinking=false` direct verifier replay。
- Dataset / 数据：E132 240-row controlled set; this first probe uses 60 rows per model, 12 per variant. / E132 共 240 条，本次小探针每模型 60 条，每变体 12 条。
- Variants / 变体：`clean_valid`, `suspicious_valid_marker`, `suspicious_valid_alternative`, `low_conf_valid`, `repaired_strict_invalid`。
- Leakage / 泄露：gold answer、manual label、manual error span 只作为离线元数据；verifier prompt 只含 problem 与 visible trace prefix。

说人话：这个实验直接问 reviewer 会问的问题：hidden 的“错误/风险信号”是不是只是在看到 Wait、maybe、double-check 这些犹豫词时乱报警？当前小探针答案是：Qwen/Gemma31 基本不是；Gemma26 有更多误触发，必须如实写成阈值/模型边界。

## Main Results / 主要结果

### Gemma4-26B-A4B-it

- Result / 结果：`results/E132_E133_suspicious_confidence_probe/gemma4_26b_a4b_it_e132_e133_all_chat.json`
- Best component / 最强组件：`17:residual_hidden_state`
- AUC / AUC：hidden=0.960, strict confidence=0.668, plain Yes-No=0.918.
- Matched pairs / 置信度匹配对：n=12, hidden valid>invalid accuracy=1.000, mean distance=1.652.

| Completion slice / completion 切片 | hidden trigger rate score<0, Wilson 95% CI | mean score | strict accept | plain accept |
|---|---:|---:|---:|---:|
| valid_all | 6/48 = 0.125 [0.059, 0.247] | 7.937 | 0.917 | 0.917 |
| suspicious_valid | 5/36 = 0.139 [0.061, 0.287] | 7.518 | 0.917 | 0.917 |
| invalid | 12/12 = 1.000 [0.757, 1.000] | -5.457 | 0.083 | 0.500 |
| clean_valid | 1/12 = 0.083 [0.015, 0.354] | 9.192 | 0.917 | 0.917 |
| suspicious_valid_marker | 2/12 = 0.167 [0.047, 0.448] | 7.726 | 0.917 | 0.917 |
| suspicious_valid_alternative | 1/12 = 0.083 [0.015, 0.354] | 7.066 | 0.917 | 0.917 |
| low_conf_valid | 2/12 = 0.167 [0.047, 0.448] | 7.763 | 0.917 | 0.917 |
| repaired_strict_invalid | 12/12 = 1.000 [0.757, 1.000] | -5.457 | 0.083 | 0.500 |

### Gemma4-31B-it

- Result / 结果：`results/E132_E133_suspicious_confidence_probe/gemma4_31b_it_e132_e133_all_chat.json`
- Best component / 最强组件：`34:residual_hidden_state`
- AUC / AUC：hidden=1.000, strict confidence=0.941, plain Yes-No=1.000.
- Matched pairs / 置信度匹配对：n=12, hidden valid>invalid accuracy=1.000, mean distance=1.655.

| Completion slice / completion 切片 | hidden trigger rate score<0, Wilson 95% CI | mean score | strict accept | plain accept |
|---|---:|---:|---:|---:|
| valid_all | 0/48 = 0.000 [0.000, 0.074] | 5.823 | 1.000 | 1.000 |
| suspicious_valid | 0/36 = 0.000 [0.000, 0.096] | 4.479 | 1.000 | 1.000 |
| invalid | 12/12 = 1.000 [0.757, 1.000] | -7.224 | 0.083 | 0.250 |
| clean_valid | 0/12 = 0.000 [0.000, 0.243] | 9.856 | 1.000 | 1.000 |
| suspicious_valid_marker | 0/12 = 0.000 [0.000, 0.243] | 4.844 | 1.000 | 1.000 |
| suspicious_valid_alternative | 0/12 = 0.000 [0.000, 0.243] | 5.326 | 1.000 | 1.000 |
| low_conf_valid | 0/12 = 0.000 [0.000, 0.243] | 3.268 | 1.000 | 1.000 |
| repaired_strict_invalid | 12/12 = 1.000 [0.757, 1.000] | -7.224 | 0.083 | 0.250 |

### Qwen3.5-27B

- Result / 结果：`results/E132_E133_suspicious_confidence_probe/qwen35_27b_e132_e133_all_chat.json`
- Best component / 最强组件：`34:residual_hidden_state`
- AUC / AUC：hidden=1.000, strict confidence=0.447, plain Yes-No=0.988.
- Matched pairs / 置信度匹配对：n=12, hidden valid>invalid accuracy=1.000, mean distance=1.215.

| Completion slice / completion 切片 | hidden trigger rate score<0, Wilson 95% CI | mean score | strict accept | plain accept |
|---|---:|---:|---:|---:|
| valid_all | 2/48 = 0.042 [0.012, 0.140] | 4.905 | 0.938 | 1.000 |
| suspicious_valid | 2/36 = 0.056 [0.015, 0.181] | 4.367 | 0.944 | 1.000 |
| invalid | 12/12 = 1.000 [0.757, 1.000] | -6.440 | 0.000 | 0.333 |
| clean_valid | 0/12 = 0.000 [0.000, 0.243] | 6.518 | 0.917 | 1.000 |
| suspicious_valid_marker | 1/12 = 0.083 [0.015, 0.354] | 4.816 | 1.000 | 1.000 |
| suspicious_valid_alternative | 0/12 = 0.000 [0.000, 0.243] | 3.966 | 0.917 | 1.000 |
| low_conf_valid | 1/12 = 0.083 [0.015, 0.354] | 4.320 | 0.917 | 1.000 |
| repaired_strict_invalid | 12/12 = 1.000 [0.757, 1.000] | -6.440 | 0.000 | 0.333 |

## Interpretation / 解析

- Qwen 与 Gemma31：hidden residual score 在 valid/suspicious-valid 和 repaired strict-invalid 之间分离很强；可疑但正确 completion 的误触发很低。说明信号不是简单看到 `Wait/check/maybe` 就报警。
- Gemma26：invalid 仍 12/12 触发，但 valid false trigger 更高。这和 E78/E131 里 Gemma26 的 valid false rejection 一致，说明它的过程方向边界更脆，需要阈值校准和 suspicious-valid 控制组。
- Confidence-matched pair 在三个模型上都是 12/12 hidden valid>invalid，但当前匹配距离还不够小，属于第一版探针证据。下一版要扩大样本并做更严格的 matching/regression。
- Plain Yes/No 对 invalid 的接受仍存在，尤其 Gemma26 plain accept 6/12；hidden score 在这些 case 上给出更强拒绝信号，支持 adaptive checking trigger 的必要性。

## E134 Window Audit / E134 窗口审计

- Audit sheet / 审计表：`data/processed/e134_trigger_window_audit_sheet_20260430.jsonl`
- Rows / 行数：209；threshold=0.0；radius=240.
- Preliminary labels / 初步标签：`{'marker_only_prefix_control_not_policy_trigger': 58, 'true_error_near_error_candidate': 47, 'strict_invalid_after_repair_or_completion_candidate': 45, 'true_error_candidate': 36, 'false_trigger_suspicious_valid_candidate': 21, 'false_trigger_clean_valid_candidate': 2}`
- Note / 注意：`suspicion_marker_end` 是 marker-only prefix control，不应作为部署策略误触发率；真正 policy trigger 应从 post_suspicion、error、final、completion 等有语义内容的边界算。

## Boundary / 边界

- This is a 60-row-per-model probe, not final prevalence. / 这是小探针，不是最终发生率估计。
- E132 variants are controlled/synthetic; next expansion must add more task families and natural hard-task suspicious-valid rows. / E132 是受控构造，后续要扩到更多任务和自然样本。
- Hidden score threshold 0 is inherited from E61 direction centering; it is not deployment-calibrated. / 0 阈值来自 E61 方向中心化，不是部署校准阈值。
- Manual labels and spans were not used in prompts. / 人工标签和 span 没有进入 prompt。
