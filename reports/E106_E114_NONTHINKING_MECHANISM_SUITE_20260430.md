# E106-E114 Non-Thinking Mechanism Suite / 非 thinking 机制套件报告（2026-04-30）

## 1. Scope / 范围

This report summarizes E106-E114, a direct/non-thinking mechanism suite over four P0 or expanded-P0 models:

本报告总结 E106-E114。它不是 thinking-mode 生成实验，而是 direct / non-thinking 机制诊断，覆盖四个 P0 或扩展 P0 模型：

- `qwen35_27b`
- `gemma4_31b_it`
- `gemma4_26b_a4b_it`
- `glm47_flash_candidate`

Core question / 核心问题：

> Does non-thinking still contain process-validity evidence in hidden activations, and can that evidence reduce answer-correct but process-invalid trace selection when plain absolute Yes/No readout over-accepts?

中文说法：

> 关闭显式 thinking 后，模型内部是否仍然有“这个过程对不对”的证据？如果 plain absolute Yes/No verifier 过度接受 ACPI trace，hidden process evidence 能不能把这些风险筛出来？

Execution status / 执行状态：

- Queue script / 队列脚本：`scripts/launch_e106_e114_nonthinking_mechanism_queue_20260430.sh`
- Result dir / 结果目录：`results/E106_E114_nonthinking_mechanism_suite/`
- Status log / 状态日志：`logs/e106_e114_nonthinking_mechanism_status_20260430.jsonl`
- Final queue state / 队列状态：`all_done` at `2026-04-30T01:08:58+08:00`
- Static audit / 静态审计：`py_compile`、launcher `bash -n`、active workspace audit 均通过。
- Smoke / 冒烟测试：Qwen、Gemma4-26B-A4B、GLM 均通过；Gemma4-31B 使用同一通过后的脚本进入正式队列。
- Leakage audit / 泄露审计：四个结果文件均记录 `gold_label_in_prompt_rows=0`、`known_error_span_annotation_in_prompt_rows=0`、`known_error_span_in_prompt_rows=0`、`manual_correction_in_prompt_rows=0`。

Important design correction / 重要设计修正：

E106/E114 的 `base_accept` 使用 E61 同款 `plain_yes_no`，不是 strict-prompt verdict；hidden process direction 来自 strict-prompt final-token residual。这样 E114 测的是“plain absolute 过度接受能否被 hidden gate 降低”，而不是测一个已经很强的 strict prompt。

## 2. E106-E108: Process Signal vs Confidence / 过程信号与置信度

| model | hidden AUC | confidence AUC | partial corr | dir cosine | hidden acc | plain Yes/No acc | matched hidden pair acc | matched Yes/No pair acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `qwen35_27b` | 1.000 | 0.888 | 0.882 | 0.977 | 1.000 | 0.792 | 1.000 | 0.938 |
| `gemma4_31b_it` | 1.000 | 0.991 | 0.812 | 0.989 | 1.000 | 0.771 | 1.000 | 1.000 |
| `gemma4_26b_a4b_it` | 0.970 | 0.832 | 0.737 | 0.935 | 0.938 | 0.698 | 0.917 | 0.688 |
| `glm47_flash_candidate` | 0.997 | 0.978 | 0.650 | 0.994 | 0.958 | 0.771 | 1.000 | 0.958 |

Interpretation / 解释：

- Hidden residual process score is very predictive across all four models. / 四个模型的 hidden residual process score 都能强预测 trace 过程是否有效。
- The process direction and confidence direction are highly aligned (`cosine=0.935-0.994`). / 过程方向和置信度方向高度同轴。
- Therefore, we cannot claim that “error awareness” and “low confidence” are fully independent. / 所以不能说“模型意识到错误”和“模型低置信度”完全无关。
- But hidden process score is not reducible to plain readout confidence: hidden AUC is higher than confidence AUC for Qwen and Gemma26, partial correlation remains positive after controlling readout confidence and entropy, and matched hidden-pair accuracy is usually higher than matched Yes/No pair accuracy. / 但 hidden process score 也不能简单化约为 plain readout confidence：Qwen 和 Gemma26 的 hidden AUC 高于 confidence AUC；控制 readout confidence 和 entropy 后 partial correlation 仍为正；matched pair 上 hidden 通常比 plain Yes/No 更稳定。

Plain-language conclusion / 说人话结论：

> 当前证据说明，hidden 里的“过程是否靠谱”信号包含明显的置信度成分，但不只是置信度。更稳的写法是：process-validity evidence and readout confidence are entangled, but hidden activations retain process-specific information that default Yes/No readout does not fully use.

## 3. E114: Hidden-Gated Verifier / hidden gate 筛选器

Hidden-gated filter is a simulated filter:

hidden gate 是一个模拟筛选器：

```text
accept = plain_absolute_yes_no_accept AND hidden_process_score > 0
```

This is not a new trained model; it asks whether already-existing hidden process evidence can reduce ACPI retention.

这不是训练新模型，而是在问：如果把已经存在的 hidden process evidence 接到筛选器上，能不能减少 ACPI trace 被保留。

| model | ACPI base accept | 95% CI | ACPI gated accept | 95% CI | valid base accept | valid gated accept |
|---|---:|---:|---:|---:|---:|---:|
| `qwen35_27b` | 18/48=0.375 | [0.252, 0.516] | 0/48=0.000 | [0.000, 0.074] | 0.958 | 0.958 |
| `gemma4_31b_it` | 22/48=0.458 | [0.326, 0.597] | 0/48=0.000 | [0.000, 0.074] | 1.000 | 1.000 |
| `gemma4_26b_a4b_it` | 22/48=0.458 | [0.326, 0.597] | 0/48=0.000 | [0.000, 0.074] | 0.854 | 0.792 |
| `glm47_flash_candidate` | 22/48=0.458 | [0.326, 0.597] | 2/48=0.042 | [0.012, 0.140] | 1.000 | 0.958 |

Interpretation / 解释：

- Plain absolute Yes/No keeps 37.5%-45.8% of controlled ACPI invalid traces. / plain absolute Yes/No 会保留 37.5%-45.8% 的受控 ACPI invalid trace。
- Hidden gate reduces ACPI retention to 0%-4.2%. / hidden gate 把 ACPI 保留率降到 0%-4.2%。
- Valid retention is mostly preserved, but Gemma26 loses some valid traces (`0.854 -> 0.792`) and GLM loses a smaller fraction (`1.000 -> 0.958`). / valid trace 基本保留，但 Gemma26 和 GLM 有一定 false rejection。

Plain-language conclusion / 说人话结论：

> non-thinking 并不是“内部没有检查过程”。更像是模型内部已经有一部分过程监控信号，但默认 Yes/No 读出没有稳定使用它。hidden gate 可以把这部分潜力释放出来，但阈值仍需要校准，否则会误伤一部分 valid trace。

## 4. E109: Activation Steering Specificity / 激活干预特异性

| model | process invalid effect | process invalid flips | confidence low effect | confidence low flips |
|---|---:|---:|---:|---:|
| `qwen35_27b` | -0.063 | 0/16 | -0.031 | 0/16 |
| `gemma4_31b_it` | -0.197 | 0/16 | -0.148 | 0/16 |
| `gemma4_26b_a4b_it` | -0.166 | 0/16 | -0.155 | 0/16 |
| `glm47_flash_candidate` | -2.875 | 8/16 | -3.000 | 8/16 |

Interpretation / 解释：

- At `alpha=2`, Qwen and Gemma margins move slightly but do not flip. / 在 `alpha=2` 下，Qwen 和 Gemma 的 margin 有轻微移动，但没有翻转。
- GLM has strong flips under both process-invalid and confidence-low steering. / GLM 在 process-invalid 和 confidence-low 两种方向下都有强翻转。
- Because GLM process and confidence interventions behave similarly, E109 does not causally separate process from confidence. / 因为 GLM 的 process 与 confidence 干预很像，E109 还不能证明二者在因果上分离。

Plain-language conclusion / 说人话结论：

> E109 证明了 GLM 的输出阈值/读出可以被 hidden direction 推动，但还没有证明“过程方向”是一个独立于置信度的完整因果回路。下一步需要做 layer-wise alpha sweep、component patch 和 confidence-matched steering。

## 5. E110: Prefix Emergence / 错误信号何时出现

Selected prefix summaries / 关键 prefix 结果：

| model | stage | n | accept | hidden score | Yes-No |
|---|---|---:|---:|---:|---:|
| `qwen35_27b` | error_span_end | 3 | 0.000 | -2.725 | -6.417 |
| `qwen35_27b` | repair_trigger_end | 6 | 0.000 | -3.236 | -2.687 |
| `qwen35_27b` | completion_end | 6 | 0.000 | -0.345 | -2.104 |
| `gemma4_31b_it` | error_span_end | 8 | 1.000 | 1.011 | 10.516 |
| `gemma4_31b_it` | repair_trigger_end | 8 | 0.000 | -2.131 | -10.711 |
| `gemma4_31b_it` | completion_end | 8 | 0.000 | -2.083 | -11.055 |
| `gemma4_26b_a4b_it` | error_span_end | 2 | 1.000 | -0.959 | 4.625 |
| `gemma4_26b_a4b_it` | repair_trigger_end | 2 | 0.000 | -3.265 | -7.531 |
| `gemma4_26b_a4b_it` | completion_end | 4 | 0.750 | -2.383 | 3.063 |
| `glm47_flash_candidate` | error_span_end | 3 | 0.000 | -0.526 | -2.500 |
| `glm47_flash_candidate` | repair_trigger_end | 4 | 0.000 | -1.230 | -2.875 |
| `glm47_flash_candidate` | completion_end | 4 | 0.000 | -0.763 | -1.750 |

Interpretation / 解释：

- Gemma31 repaired ACPI is the clearest case: before explicit repair markers, strict verifier accepts the prefix; after repair-trigger text, both hidden score and Yes/No margin flip negative. / Gemma31 repaired ACPI 最清楚：显式修复标记之前，strict verifier 接受错误前缀；修复触发文本之后，hidden score 和 Yes/No margin 一起转负。
- Gemma26 is a mismatch case: at error-span end, hidden score is already negative, but Yes/No still accepts; at completion, mixed repaired/unrepaired rows keep 0.75 accept. / Gemma26 是错配案例：错误步结束时 hidden 已经偏负，但 Yes/No 仍接受；完成态混合 repaired/unrepaired 后仍有 0.75 接受。
- Qwen and GLM in this selected set are more conservative. / Qwen 和 GLM 在这批 prefix 中更保守。

Plain-language conclusion / 说人话结论：

> repair marker 指的是 trace 中“Wait / however / let me correct”等显式转折或纠错语句。Gemma31 的结果说明 verifier 在看到这些 marker 后，会从“只看当前前缀似乎能走到答案”切换到“这个 trace 曾经有错步，strict 口径下不该接受”。Gemma26 则说明 hidden 里已经有负信号，但最终 Yes/No 读出仍可能被答案自洽或后文压回 Yes。

## 6. E111: Long-Context / Self-Consistency Dilution

| model | suffix 0 accept/hidden | suffix 300 accept/hidden | suffix 1200 accept/hidden |
|---|---:|---:|---:|
| `qwen35_27b` | 0.000/-6.440 | 0.000/-6.351 | 0.000/-6.584 |
| `gemma4_31b_it` | 0.083/-7.224 | 0.083/-6.853 | 0.000/-3.643 |
| `gemma4_26b_a4b_it` | 0.083/-5.457 | 0.167/-3.517 | 0.167/-1.874 |
| `glm47_flash_candidate` | 0.000/-1.667 | 0.000/-1.530 | 0.000/-1.141 |

Interpretation / 解释：

- Adding long self-consistent suffixes weakens hidden invalid evidence most clearly in Gemma26. / 长自洽后文最明显地削弱 Gemma26 的 hidden invalid evidence。
- Qwen remains robust; Gemma31 and GLM hidden scores move toward valid but readout mostly still rejects. / Qwen 基本不受影响；Gemma31 和 GLM 的 hidden score 朝 valid 方向移动，但读出仍大多拒绝。

Plain-language conclusion / 说人话结论：

> “长上下文”在这里不是超过模型上下文窗口，而是 trace 后半段持续给出自洽、答案一致的解释，可能稀释早期错步的影响。这个信号目前最支持 Gemma26 的“答案自洽/后文稀释”解释。

## 7. E112: Answer Anchor / 答案锚定

E112 shows a stable pattern across P0:

E112 的稳定模式是：

- Valid process + correct shown/removed/masked answer is accepted by Qwen/Gemma; GLM valid acceptance is slightly lower under some masked/removed conditions. / valid process 加正确答案在 shown/removed/masked 条件下大多被接受。
- Wrong final answer makes even valid process traces rejected. / 最终答案故意改错时，即使过程本来 valid，模型也会拒绝。
- Invalid process traces remain rejected in strict replay under the E112 prompt. / invalid process 在 E112 strict replay 中基本被拒绝。

Plain-language conclusion / 说人话结论：

> final answer anchor 确实很强：答案错会压倒过程有效性。但答案锚定不是 ACPI over-accept 的唯一原因，因为 E114 中 plain absolute Yes/No 对答案正确但过程错的 trace 仍有 37.5%-45.8% 接受率，而 hidden gate 能把它们筛掉。

## 8. Updated Evidence Chain / 更新后的证据链

Current strongest chain / 当前最强证据链：

1. Controlled ACPI traces make plain absolute Yes/No over-accept in all four models. / 受控 ACPI trace 会让四个模型的 plain absolute Yes/No 过度接受。
2. Hidden residual states encode process-validity information with high AUC. / hidden residual 里有高 AUC 的过程有效性信息。
3. This information is entangled with confidence but not fully reducible to confidence. / 这个信息和置信度缠在一起，但不能完全化约为置信度。
4. Hidden gate sharply reduces ACPI retention while mostly keeping valid traces. / hidden gate 能显著降低 ACPI 保留率，并大体保留 valid trace。
5. Prefix replay shows when repair markers appear, hidden/readout state can flip from accept to reject; Gemma26 also shows hidden negative evidence without corresponding Yes/No rejection. / prefix replay 说明修复标记出现时 hidden/readout 会从接受转向拒绝；Gemma26 还显示 hidden 已有负证据但 Yes/No 没用好。
6. Long self-consistent suffixes can dilute invalid evidence, especially for Gemma26. / 长自洽后文会稀释 invalid evidence，Gemma26 最明显。

Safe claim after E106-E114 / E106-E114 后的安全 claim：

> In direct/non-thinking verifier settings, process-validity evidence is already present in hidden activations. Plain absolute Yes/No readout can over-accept ACPI traces because it does not consistently use that evidence under confidence, answer-anchor, repair-aware reading, long self-consistency, and output/readout bottlenecks. A simple hidden gate can reduce controlled ACPI retention, but threshold calibration and thinking-mode replication remain necessary.

中文：

> 在 direct/non-thinking verifier 设置下，过程有效性证据已经存在于 hidden activations 中。plain absolute Yes/No 之所以会过度接受 ACPI trace，不是因为模型内部完全看不到问题，而是它没有稳定地把这些证据用于最终判定；置信度、答案锚定、repair-aware 阅读、长自洽后文和输出读出瓶颈都会影响这一点。一个简单 hidden gate 已经能降低受控 ACPI 保留率，但阈值校准和 thinking-mode 复核仍然必须继续做。

## 9. Boundaries / 边界

- E106-E114 are `MI-DV` and direct/non-thinking diagnostics, not thinking-generation prevalence. / E106-E114 是 `MI-DV` 和 direct/non-thinking 诊断，不是 thinking 生成发生率。
- Hidden probe / hidden gate does not prove a complete circuit. / hidden probe 和 hidden gate 还不能证明完整 circuit。
- E109 does not yet causally separate process from confidence. / E109 还没有因果地区分 process 与 confidence。
- Natural unrepaired ACPI prevalence still comes from previous NG hard-task audits; E106-E114 does not expand natural prevalence. / 自然 unrepaired ACPI 发生率仍来自此前 NG 困难题审计；E106-E114 没有扩大自然样本。
- Thresholds are not calibrated on a held-out deployment set. / hidden gate 阈值还没有在独立部署集上校准。

## 10. Next Experiments / 下一步实验

Priority next steps / 优先下一步：

1. E116 stop-signal probe: capture residual/MLP/token-mixer states around final answer, post-final continuation, and EOS/continue logits in Qwen thinking clean-stop vs endless-thinking cases. / 捕捉 thinking 收口与不停思考的 hidden 终止信号。
2. E117 stop steering or early-exit policy: test whether a clean-stop direction or external hidden-gated policy reduces endless thinking without harming final correctness. / 测试能否减少 endless thinking。
3. E118 TG vs NG paired mechanism contrast: compare same-problem thinking and non-thinking traces under matched sampling and replay prompts. / 同题比较 thinking 与 non-thinking 的 hidden/process/readout 差异。
4. E119 natural hard-task expansion: enlarge answer-first/no-gold and add algebra/code/table variants to tighten unrepaired ACPI confidence intervals. / 扩大自然困难样本，收窄 unrepaired ACPI 置信区间。
5. E120 unified leakage/logic audit package: emit prompt leakage counters, parser rules, CI, manual-label usage, and negative controls for appendix. / 统一附录审计包。

