# E119 Natural Hard-Task Expansion Plan / 自然困难题扩样计划（2026-04-30）

## 1. Purpose / 目的

E119 is a non-thinking generation (`NG`) expansion for natural hard-task ACPI prevalence. It does not use gold answers or trap notes in prompts.

E119 是 non-thinking generation (`NG`) 自然困难题扩样。生成 prompt 不放 gold answer，也不放 trap note。

Why now / 为什么做：

- E106-E114 shows controlled ACPI and hidden process evidence. / E106-E114 证明了受控 ACPI 与 hidden 过程证据。
- E116-E118 shows thinking has a separate stop/commit bottleneck. / E116-E118 说明 thinking 有额外收口瓶颈。
- Therefore E119 keeps NG separate and asks a prevalence question: how often do final-correct natural hard-task traces contain strict or unrepaired ACPI? / 因此 E119 单独在 NG 下估计自然困难题 final-correct trace 中 strict/unrepaired ACPI 的出现情况。

## 2. Design / 设计

Models / 模型：

- `qwen35_27b`
- `gemma4_31b_it`
- `gemma4_26b_a4b_it`
- `glm47_flash_candidate`

Tasks / 任务：

- 6 AIME-style tasks from `configs/e26_aime_hard_tasks.yaml`.

Prompt variants / prompt 变体：

- `neutral`
- `self_check`
- `answer_first_no_gold`

Generation parameters / 生成参数：

- `thinking=false`
- `k=2`
- `max_new_tokens=4096`
- `temperature=0.7`
- `top_p=0.95`
- `top_k=50`
- `batch_size=2`

Expected rows / 预计行数：

- `4 models * 6 tasks * 3 variants * 2 samples = 144` generated rows.

## 3. Audit Rules / 审计规则

Generation script / 生成脚本：

- `scripts/run_e49_hard_task_conditioning_official.py`

Queue script / 队列：

- `scripts/launch_e119_natural_hardtask_expansion_queue_20260430.sh`

Audit-sheet builder / 审计表构建：

- `scripts/build_e119_natural_hardtask_audit_sheet.py`

Outputs / 输出：

- Results / 结果：`results/E119_natural_hardtask_expansion/`
- Audit sheet / 审计表：`data/processed/e119_natural_hardtask_final_correct_audit_sheet_20260430.jsonl`
- Summary / 摘要：`results/E119_natural_hardtask_expansion/e119_audit_sheet_summary.json`
- Status / 状态：`logs/e119_natural_hardtask_expansion_status_20260430.jsonl`

Final-correct handling / 最终答案处理：

- strict final decision: explicit `Final answer:` or `\boxed{}` only.
- fallback extraction: phrase/tail extraction, recorded separately.
- Manual process audit will be performed only on strict-or-fallback final-correct rows, and labels will not be inserted into prompts.

中文：

- strict final decision 只认明确 `Final answer:` 或 `\boxed{}`。
- fallback 抽取单独记录，不能冒充 strict final decision。
- 只有 strict 或 fallback final-correct 的行进入人工/agent 过程审计；人工标签不进入 prompt。

## 4. Static and Smoke Requirements / 静态与 smoke 要求

Before official queue:

- `py_compile` for E119 builder.
- `bash -n` for queue.
- smoke one Qwen row into `_smoke`.
- active workspace audit passes after whitelisting E119 artifacts.

## 5. Boundary / 边界

E119 will update natural NG prevalence. It will not answer thinking-mode prevalence, thinking verifier behavior, or hidden causal circuit questions.

E119 只更新 NG 自然发生率；它不回答 thinking-mode 发生率、thinking verifier 行为或 hidden 因果 circuit 问题。

