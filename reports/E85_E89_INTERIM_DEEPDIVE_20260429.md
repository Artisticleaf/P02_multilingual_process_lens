# E85-E89 Interim Deep-Dive / 阶段性深挖记录（2026-04-29）

- Machine status / 机器状态：统一队列 `scripts/launch_e85_e89_queue_20260429.sh` 已在 tmux `p02_e85_e89_20260429` 中运行；状态日志是 `logs/e85_e89_status_20260429.jsonl`。
- Scope / 范围：E85/E86/E87 已落盘；E88 大规模 answer-first/no-gold 自然采样仍在运行；E89 已做一次 interim 汇总，队列会在 E88 后重跑。
- Plain language / 说人话：目前新增结果没有推翻主 claim，但让主 claim 更细：不是所有“代数错误 + 答案正确”的短 trace 都会被 absolute verifier 漏过；真正危险的是长 trace、答案锚定、局部错误隐蔽、后续推导自洽，以及读出格式把 hidden 证据压坏。

## E85 Full Hidden Cache / 完整 hidden cache

Artifacts / 产物：`results/E85_hardtask_full_hidden_cache/`。

| model/case type | cache shape | key fact |
|---|---:|---|
| `gemma4_31b_it` repaired ACPI | 54 x 61 x 5376 | strict verifier accepts early wrong-answer prefixes but rejects after repair markers |
| `gemma4_26b_a4b_it` unrepaired ACPI | 10 x 31 x 2816 | strict verifier accepts all key prefixes, including erroneous factorization and completion |

Concrete facts / 具体事实：

- Gemma31 repaired ACPI: `error_span_end` accept 0.889, `first_final_answer_end` accept 1.000, but `repair_trigger_end` accept 0.111, `post_repair_240chars` accept 0.000, `completion_end` accept 0.111. / Gemma31 修复型 ACPI：错误答案前缀会被接受；出现修复信号后，同一个 strict prompt 多数转为拒绝。
- Gemma31 best-layer score also moves from positive around the first wrong answer to negative after repair (`first_final_answer_end` mean +1.248; `post_repair_240chars` mean -2.941). / Gemma31 最佳层分数也从错误答案附近偏 valid 转为修复后偏 invalid。
- Gemma26 unrepaired ACPI: accept rate is 1.000 at every key prefix, including `error_span_end` and `completion_end`; however best-layer scores are not cleanly valid (`completion_end` mean -0.797). / Gemma26 未修复 ACPI：每个关键前缀都被接受，但 hidden 最佳层并不干净地支持 valid。
- Scientific meaning / 科学含义：E85 strengthens the hidden-evidence-to-decision mismatch story. Gemma26 is not merely “no hidden signal”; it is a case where the output decision says Yes despite a weak/negative hidden projection. / E85 加强“hidden 证据到输出决策错配”：Gemma26 不是完全没有 hidden 信号，而是输出 Yes 没有跟 hidden 投影一致。

## E86 Algebra-Equivalence Boundary / 代数等价边界实验

Artifacts / 产物：`results/E86_algebra_equivalence_adversarial/`。

Design / 设计：12 controlled sibling pairs: factorization sign-symmetry and root-product sign-invariance. Invalid traces have a local algebraic error but preserve the final answer through symmetry/product invariance. Prompts contain only problem and visible trace(s); labels/error spans are offline only. / 12 组受控 sibling：因式分解符号对称与根乘积符号不变。invalid trace 有局部代数错步，但最终答案因对称或乘积不变仍正确。

| verifier | strict pointwise invalid accept | strict pointwise valid accept | raw A/B sibling accuracy | label-free two-pass accuracy |
|---|---:|---:|---:|---:|
| `qwen35_27b` | 0.000 | 0.583 | 0.792 | 0.958 |
| `gemma4_31b_it` | 0.000 | 0.500 | 0.875 | 0.750 |
| `gemma4_26b_a4b_it` | 0.000 | 0.500 | 0.750 | 0.833 |
| `glm47_flash_candidate` | 0.000 | 0.500 | 0.333 | 0.667 |

Interpretation / 解释：

- This is a boundary result, not a failure of the project. / 这是边界结果，不是项目失败。
- In short, explicit algebra traces, every P0 strict pointwise verifier catches the invalid algebraic step. / 在短而显式的代数 trace 里，所有 P0 strict pointwise verifier 都能抓住 invalid 代数错步。
- The same strict prompt over-rejects many valid terse traces: valid accept is only 0.500-0.583. / 但同一 strict prompt 也会误拒很多正确短解，valid accept 只有 0.500-0.583。
- Therefore the dangerous Gemma26 hard-task cases are not explained by “any sign error is invisible.” A better explanation is long-context answer coherence plus local subtlety plus final-answer anchoring. / 因此 Gemma26 困难题危险案例不能简化成“任何符号错都看不见”；更像是长上下文、后续答案自洽、局部隐蔽和最终答案锚定共同作用。
- GLM remains a readout boundary: raw A/B sibling accuracy is only 0.333 on E86, while label-free improves to 0.667 but is still not oracle. / GLM 继续是读出边界：E86 raw A/B 只有 0.333，无标签提升到 0.667 但仍不是 oracle。

## E87 GLM Readout Intervention / GLM 读出干预

Artifacts / 产物：`reports/E87_GLM_READOUT_INTERVENTION_20260429.md`, `results/E87_glm_readout_intervention/`。

| decision rule | accuracy |
|---|---:|
| raw A/B single order | 0.542 |
| global A/B bias centered | 0.667 |
| two-order antisymmetric A/B | 0.812 |
| hidden readout replacement | 1.000 |
| label-free two-pass replacement | 0.958 |

Plain meaning / 说人话：

- If GLM truly could not see process errors, hidden readout and label-free readout should not recover performance. / 如果 GLM 真看不见过程错误，hidden 读出和无标签读出不该恢复性能。
- Instead, raw A/B is weak, bias centering helps, asking both orders helps more, and hidden/label-free readouts are near-perfect. / 结果是 raw A/B 弱，去偏有帮助，交换顺序反对称更好，hidden/无标签读出接近完美。
- Scientific claim should be: GLM has process-validity evidence, but the raw output-label interface can distort it. / 科学表述应是：GLM 内部有过程有效性证据，但 raw 输出标签接口会扭曲它。
- Boundary / 边界：E87 is a readout/decision-rule intervention, not an activation patch or full circuit proof. / E87 是读出/决策规则干预，不是激活 patch，也不是完整 circuit 证明。

## E88 Running / E88 正在运行

- Current queue step at report time: `e88_qwen35_27b_answer_first_k8`. / 写报告时队列正在跑 qwen 的 E88。
- E88 uses `answer_first_no_gold` only; gold answer and trap notes are not in prompts. / E88 只使用 `answer_first_no_gold`；gold answer 和 trap note 不进 prompt。
- After generation, `scripts/build_e88_answer_first_audit_sheet.py` will collect final-correct rows into `data/processed/e88_answer_first_final_correct_audit_sheet_20260429.jsonl` for manual/agent process audit. / 生成完成后会把 final-correct 行整理成人审表。
- No prevalence claim should be updated until E88 generation finishes and final-correct rows are audited. / E88 完成并审计前，不更新自然发生率结论。

## Interim Scientific Update / 阶段性科学更新

Safe updated claim / 安全更新主张：

> Controlled strict ACPI risk remains robust, and hard-task unrepaired ACPI remains a real but low-frequency phenomenon. Hidden residual states encode process-validity evidence, but whether the verifier decision uses it depends on objective, threshold, final-answer anchoring, repair-aware reading, context length/local subtlety, and output-label/readout format.
>
> 受控 strict ACPI 风险仍稳健；困难题未修复 ACPI 真实存在但当前低频。hidden residual state 编码了过程有效性证据，但 verifier 决策是否用上它，取决于目标、阈值、最终答案锚定、修复感知阅读、上下文长度/局部隐蔽性，以及输出标签/读出格式。

What E86 changes / E86 改变了什么：

- It weakens any over-broad statement that “absolute verifier misses algebraic ACPI in general.” / 它削弱“absolute verifier 一般都会漏掉代数 ACPI”的过宽说法。
- It strengthens the need for context-sensitive explanation: short exposed errors are caught; long answer-coherent traces can still be accepted. / 它强化了上下文解释的必要性：短而显式的错误能被抓住，长且答案自洽的 trace 仍可能被接受。
- It gives a useful negative control for top-tier reviewers: our phenomenon is not an artifact of every constructed invalid trace being accepted. / 它给顶会审稿人一个有用负控制：我们的现象不是“构造什么 invalid 都会被接受”的工件。

Next required before final E85-E89 synthesis / 最终综合前还需要：

1. Let E88 finish across all four P0 models. / 等 E88 在四个 P0 模型上跑完。
2. Audit final-correct E88 rows manually/agentically for strict valid, repaired ACPI, and unrepaired ACPI. / 人工/agent 审计 E88 final-correct 行。
3. Rerun E89 after E88 so filter simulation includes new prevalence rows if usable. / E88 后重跑 E89。
4. Run active workspace audit after all new artifacts are whitelisted and present. / 所有新产物在白名单中且存在后跑 active workspace audit。
