# E153-E161 Completed Data Synthesis / 已完成数据综合统计

- Created at / 生成时间：`2026-05-01T12:35:08`.
- Scope / 范围：只统计已经完整写入 final JSON 或审计 summary 的数据；正在运行的 checkpoint 不进入科学结论。

## Queue Status / 队列状态

- Last event / 最后事件：`{'status': 'start', 'step': 'e160_thinking_generation_gemma4_31b_it', 'ts': '2026-05-01T11:09:23+08:00'}`.
- Completed steps / 已完成步骤：e159_build_bank, e159_task_bank_audit, e159_e161_scaffold_smoke, e159_nonthinking_generation_qwen35_27b, e159_nonthinking_generation_gemma4_31b_it, e159_nonthinking_generation_gemma4_26b_a4b_it, e160_thinking_generation_qwen35_27b.
- Running or pending / 正在运行或等待：e160_thinking_generation_gemma4_31b_it.

## E153 Generation / E153 自然解题生成

- `gemma4_31b_it`: n=96, manual final correct=93 (96.9%), clean valid prefill candidates=90, language-trait traces=14, unrepaired ACPI=0.
- `qwen35_27b`: n=96, manual final correct=96 (100.0%), clean valid prefill candidates=89, language-trait traces=19, unrepaired ACPI=0.
- `gemma4_26b_a4b_it`: n=96, manual final correct=95 (99.0%), clean valid prefill candidates=95, language-trait traces=15, unrepaired ACPI=0.
- Interpretation / 解释：E153 说明多样化任务能产生大量顺序、可重放的高质量 trace，但没有支持“自然未修复 ACPI 高频存在”。

## E153 Error Finding / E153 找错定位

- `gemma4_26b_a4b_it`: n=128, last-pred correct=113 (88.3%), valid false positives=0/64, invalid false negatives=13/64, invalid location match=56/64, hit-max=2.
- `gemma4_31b_it`: n=128, last-pred correct=121 (94.5%), valid false positives=2/64, invalid false negatives=3/64, invalid location match=58/64, hit-max=2.
- `qwen35_27b`: n=128, last-pred correct=118 (92.2%), valid false positives=9/64, invalid false negatives=1/64, invalid location match=61/64, hit-max=1.
- Interpretation / 解释：这里的强信号是“会解题”和“会审计过程”分离。Qwen 更敏感但更容易误报；Gemma dense 更保守；MoE 最保守，漏报更多。

## E159 Non-Thinking Generation / E159 non-thinking 保答案陷阱生成

- `gemma4_26b_a4b_it`: generated=120, final-correct=114 (95.0%), missing-final-marker=0, hit-max=0, auto repair-marker rows=57.
- `gemma4_31b_it`: generated=120, final-correct=112 (93.3%), missing-final-marker=0, hit-max=0, auto repair-marker rows=48.
- `qwen35_27b`: generated=120, final-correct=114 (95.0%), missing-final-marker=0, hit-max=0, auto repair-marker rows=58.
- Process audit / 过程审计：n=360, audited final-correct=357 (99.2%), process-valid=357 (99.2%), runner format false-negatives=17, unrepaired ACPI=0, clean valid prefill candidates=357.
- Interpretation / 解释：E159 自然生成没有产出 unrepaired ACPI；它的价值转为提供大批干净有效 replay 种子，以及给 E161/E156 的受控 invalid-reference/mutation 机制实验提供任务面。

## E160 Thinking Contrast / E160 thinking 对照

- `qwen35_27b`: generated=120, final-correct=108 (90.0%), missing-final-marker=5, hit-max=16, auto repair-marker rows=120.
- Qwen shared rows / Qwen 同题同 prompt 对照：120 rows; confusion={'nt_correct__th_correct': 108, 'nt_correct__th_wrong': 6, 'nt_wrong__th_wrong': 6}.
- Interpretation / 解释：Qwen thinking 目前因 4096 token 上限产生明显截断，不能简单说 thinking 更好；应先调大 token 或单独审计截断行。

## E161 Controlled Repair / E161 受控找错与修复

- No completed E161 final file yet. / E161 尚无完整 final 文件。

## Claim State / 当前 claim 状态

- C1_solve_vs_audit_separation: strong / 强. E153 已支持：模型会从头做题，但检查已有过程时会误报、漏报或定位错步。
- C2_natural_unrepaired_acpi_prevalence: weak-to-negative for broad prevalence / 对广泛自然高频说法较弱且偏负. E153 多样化自然生成没有发现未修复 ACPI；后续要靠保答案结构与人工过程审计寻找高质量样本。
- C3_answer_preserving_trap_surface: process-audited negative for natural ACPI, strong seed pool / 已过程审计；自然 ACPI 为负，种子池强. E159 已完成并审计 10 类、40 题、三模型 360 条 non-thinking 生成；自然未修复 ACPI 为 0，但得到 357 条干净有效 prefill 种子。
- C4_thinking_contrast: partial / 部分完成. E160 目前只有 Qwen 完整落盘；thinking 因截断较多，不能直接当作性能提升证据。
- C5_hidden_explainability: method fixed, data pending / 方法确定，数据待跑. 隐藏层主方案已确定为审计后 teacher-forced replay；E159/E161 审计后应接 E156 cache。

## Next Analysis Actions / 后续分析动作

- 等待 E160 Gemma dense 和 E161 完整落盘后，用本脚本重跑综合统计。
- 对 E159 process audit 的 357 条 clean-valid 行抽样做第二轮人工复核，再选入 E156 hidden replay。
- 用 E159 invalid reference traces 和 clean-valid generated traces 构造 mutation/prefill 对照，而不是继续期待同一设置自然产出大量 ACPI。
- E161 完成后比较 blind_global、blind_localize_only、oracle_span_repair，判断显式错步提示能否提升 non-thinking 修复。
- 把审计后的 clean-valid、mutated-invalid、natural-wrong、localized-failure 四类样本送入 E156 teacher-forced hidden replay。
