# E27 Transfer Trace Generation Audit / E27 跨模型轨迹生成审计

Date / 日期: 2026-04-27 CST
Inputs / 输入:

- `data/raw/e27_transfer_trace_generation/qwen35_27b_trace_pool_smoke_v2_transfer_zh_en.json`
- `data/raw/e27_transfer_trace_generation/gemma4_e4b_it_trace_pool_smoke_v2_transfer_zh_en.json`

Scope / 范围: six zh->en transfer smoke tasks from the existing simple-task pool. / 来自既有简单任务池的 6 个 zh->en 迁移 smoke 任务。

## 1. Summary / 汇总

| model / 模型 | rows / 行数 | usable trace format / 可用轨迹格式 | strict final-correct / 严格答案正确 | ACPI candidates / ACPI 候选 | important finding / 重要发现 |
|---|---:|---:|---:|---:|---|
| qwen35_27b | 6 | 0 | 0 | 0 | Loader works, but outputs are meta-planning `Thinking Process` notes rather than final reasoning traces. / 可加载，但输出是元规划 `Thinking Process`，不是可用最终推理轨迹。 |
| gemma4_e4b_it | 6 | 6 | 5 | 0 | One surface semantic drift: `打七五折` is treated as `75% off`, final `$20` instead of `$60`. / 一条表层语义漂移：把 `打七五折` 当作 `75% off`，答案 `$20` 而非 `$60`。 |

Interpretation / 解释：this is a loader/transfer smoke, not a prevalence estimate. / 这是加载与迁移 smoke，不是发生率估计。

## 2. Row Audit / 逐行审计

### Qwen3.5-27B / Qwen3.5-27B

All six rows begin with meta-instructions such as `Thinking Process:` and analyze the prompt constraints. / 6 行均以 `Thinking Process:` 等元指令开头，分析提示约束。

Although the raw text contains the literal phrase `Final answer:` inside the copied constraint, it does not provide a clean final answer line. / 虽然原文中因为复述约束而出现字面 `Final answer:`，但没有给出干净最终答案行。

| task / 任务 | gold / 标准答案 | audit / 审计 |
|---|---|---|
| `disc_en_25_off` | 60 | meta-planning only; not a usable trace / 仅元规划，不是可用轨迹 |
| `disc_zh_75_price` | 60 | meta-planning; correctly explains `七五折` as pay75 inside the plan, but no final trace / 元规划中正确解释七五折为付 75%，但无最终轨迹 |
| `disc_en_75_off` | 20 | meta-planning only / 仅元规划 |
| `ratio_boys_total` | 40 | meta-planning only / 仅元规划 |
| `deriv_sum` | `2x+3` | meta-planning only / 仅元规划 |
| `percent_then_discount` | 80 | meta-planning only / 仅元规划 |

Conclusion / 结论：Qwen3.5-27B can be loaded locally with `device_map=auto`, but generation needs a stricter chat template or prompt that forbids meta-planning and forces one final answer line. / Qwen3.5-27B 可本地多卡加载，但生成需要更严格 chat template 或提示，禁止元规划并强制一个最终答案行。

### Gemma4 E4B-it / Gemma4 E4B-it

| task / 任务 | gold / 标准答案 | generated final / 生成答案 | process audit / 过程审计 | label / 标签 |
|---|---|---|---|---|
| `disc_en_25_off` | 60 | 60 | correct 25% off calculation / 正确计算 25% off | valid / 有效 |
| `disc_zh_75_price` | 60 | `$20` | treats `打七五折` as `75% off`; in Chinese commerce it should mean pay 75% / 把 `打七五折` 当成 75% off；中文商业语境应为支付 75% | semantic drift, final-wrong / 语义漂移且答案错 |
| `disc_en_75_off` | 20 | `$20` | correct 75% off calculation / 正确计算 75% off | valid / 有效 |
| `ratio_boys_total` | 40 | 40 | correct total/girls calculation / 正确计算总人数与女生人数 | valid / 有效 |
| `deriv_sum` | `2x+3` | `2x + 3` | correct derivative / 正确求导 | valid / 有效 |
| `percent_then_discount` | 80 | `$80` | correctly interprets `打八折` as 80% of price / 正确把 `打八折` 解释为支付 80% | valid / 有效 |

Conclusion / 结论：Gemma4 does not produce ACPI in this tiny smoke, but it reproduces the surface-lexical drift family: discount lexicalization can flip `pay 75%` into `75% off`. / Gemma4 在这个小 smoke 中没有产生 ACPI，但复现了表层词汇漂移族：折扣词汇化可把“支付 75%”翻成“优惠 75%”。

## 3. Reliability Notes / 可靠性说明

- No row was used for training or fine-tuning. / 没有任何行用于训练或微调。
- Qwen3.5-27B rows are excluded from ACPI counting because they are prompt-analysis artifacts, not final reasoning traces. / Qwen3.5-27B 行被排除出 ACPI 计数，因为它们是提示分析产物，不是最终推理轨迹。
- Gemma4 `disc_zh_75_price` is not ACPI because the final answer is wrong; it supports semantic-drift risk but not answer-correct/process-invalid risk. / Gemma4 `disc_zh_75_price` 不是 ACPI，因为最终答案错误；它支持语义漂移风险，但不支持答案正确但过程错误。
- The result should be reported as qualitative transfer evidence only. / 该结果只能作为定性迁移证据报告。

## 4. Next Step / 下一步

Run a stricter transfer-generation resampling round / 运行更严格的迁移生成重采样：

1. Qwen3.5-27B: remove explicit wording that can be copied as meta-planning; require `Start solving now.` and stop after first clean `Final answer:` line. / 移除容易被复述为元规划的提示措辞，要求立即求解并在第一条干净 `Final answer:` 后停止。
2. Gemma4: sample `打七五折`, `打八折`, `优惠75%`, `20% off`, and paraphrases to estimate drift repeatability. / 对 Gemma4 重采 `打七五折`、`打八折`、`优惠75%`、`20% off` 与改写，估计漂移复现率。
3. Only if final-correct/process-invalid traces appear, add them to sibling comparison and hidden-span patching. / 只有出现 final-correct/process-invalid 轨迹后，才加入 sibling 对比与 hidden-span patch。
