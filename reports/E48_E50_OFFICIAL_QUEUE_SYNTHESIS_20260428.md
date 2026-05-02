# E48-E50 Official Queue Synthesis / 官方队列综合分析（2026-04-28）

## 1. What was run / 实际跑了什么

English: We ran the official post-cleanup queue for natural surface-semantic prevalence, hard-task final-correct conditioning, and residual-state mechanism controls. Qwen3.5/Gemma4 P0 models used HuggingFace because vLLM 0.12.0 cannot reliably initialize their conditional-generation/multimodal checkpoints. Compatible CausalLM controls used vLLM.

中文：本轮跑完了清理后官方队列，覆盖自然表层语义发生率、困难题 final-correct conditioning、以及 residual-state 机制控制。Qwen3.5/Gemma4 P0 模型使用 HuggingFace；兼容的 CausalLM 控制模型使用 vLLM。

Important post-hoc audit fixes / 重要事后审计修正：

- E48 parser and regex were tightened after manual review. / 人工复核后收紧了 E48 parser 和正则。
- E49 final-answer parser is now line-anchored; echoed text such as `Given final answer: 16` no longer counts as a model-emitted final answer. / E49 final-answer parser 改为行首锚定；模型复述 `Given final answer: 16` 不再算作输出了 final-answer 行。
- All fixes changed only derived labels/summaries, not model completions. Pre-fix JSONs were archived under `archive/logic_error_quarantine_20260428/`. / 修正只改变派生标签和 summary，不改变模型输出；修正前 JSON 已归档。

## 2. E48 natural prevalence / E48 自然发生率

No gold answer or known error span was inserted into the E48 prompts. / E48 prompt 不插入 gold answer 或已知错误片段。

| Model / 模型 | Backend / 后端 | Rows / 行数 | Final-correct / 答案正确 | Audited ACPI / 审计后 ACPI | Main weak task / 主要薄弱题 |
|---|---:|---:|---:|---:|---|
| Qwen3.5-9B | HF | 96 | 89 | 0 | `zh_yi_wan_unit`, small misses on probability/Chinese tasks |
| Qwen3.5-27B | HF | 96 | 85 | 0 | `zh_yi_wan_unit`, probability without replacement |
| Gemma4-26B-A4B-it | HF | 48 | 42 | 0 | `zh_yi_wan_unit`, probability without replacement |
| Gemma4-31B-it | HF | 96 | 88 | 0 | `zh_yi_wan_unit` |
| Qwen3-14B Base | vLLM | 96 | 73 | 0 | more general final-answer/format misses; `zh_yi_wan_unit` remains hard |

Plain-language finding / 说人话结论：

- In small official no-leak samples, these models usually either solve the easy surface-semantic task correctly with a valid process, or they miss the final answer. / 在无泄露小样本里，模型通常要么答案和过程都对，要么答案错/格式错。
- We did **not** observe robust natural ACPI on these simple tasks after human audit. / 人工审计后没有观察到稳健的自然 ACPI。
- This does **not** refute the controlled ACPI claim. It says that simple natural prompts are not enough to estimate the real trace-selection risk. / 这不否定 controlled ACPI；它说明简单自然 prompt 不足以估计真实 trace-selection 风险。
- `zh_yi_wan_unit` is a recurring capability failure: models often fail the Chinese numeric-unit conversion itself, so it is not useful for answer-correct/process-invalid prevalence unless we condition on final correctness. / `一万/万` 单位题是反复出现的能力失败：模型常直接答案错，因此不适合自然 ACPI 估计，除非先条件化 final correctness。

## 3. E49 hard tasks / E49 困难题

No-gold hard-task runs / 无 gold 困难题：

| Model / 模型 | Backend / 后端 | Rows / 行数 | Strict final-correct / 严格 final-correct | Strict final marker missing / 缺 final marker | Gold in prompt / prompt 含 gold |
|---|---:|---:|---:|---:|---:|
| Qwen3.5-27B | HF | 18 | 0 | 18 | 0 |
| Gemma4-26B-A4B-it | HF | 18 | 0 | 18 | 0 |
| Qwen2.5-Math-7B-Instruct | vLLM | 36 | 0 | 36 | 0 |

Answer-anchor diagnostics / answer-anchor 诊断：

| Model / 模型 | Rows / 行数 | Strict final-correct after line-anchor fix / 行首锚定后严格 final-correct | Note / 说明 |
|---|---:|---:|---|
| Qwen3.5-27B | 6 | 0 | Previous 1/6 was a parser false positive caused by echoed `Given final answer`. / 之前 1/6 是模型复述 given answer 造成的 parser 假阳性。 |
| Gemma4-26B-A4B-it | 6 | 0 | The model reasoned but did not emit the required strict final line. / 模型有推理但没有输出严格 final 行。 |

Plain-language finding / 说人话结论：

- The hard-task bottleneck is still **obtaining auditable final-correct traces**, not proving ACPI absence. / 困难题瓶颈仍然是先得到可审计的 final-correct trace，不是证明 ACPI 不存在。
- Models often produce long partial reasoning or boxed answers, but not the required line `Final answer: <integer>`. / 模型常输出长推理或 boxed answer，但不按我们要求输出 `Final answer: <integer>` 行。
- For future hard-task work, we need two separate tracks: benchmark-style answer extraction (`\boxed{}` allowed) and trace-selection-style strict final-line extraction. / 后续困难题需要分两条：benchmark 风格允许 `\boxed{}`，trace-selection 风格继续严格 final 行。

## 4. E50 mechanism controls / E50 机制控制

| Model / 模型 | Best residual-probe layer / 最佳层 | LOTO accuracy / 留一任务准确率 | Random control mean / 随机控制均值 | Absolute verifier accepts invalid rows / absolute 接受 invalid | Accepts valid rows / 接受 valid |
|---|---:|---:|---:|---:|---:|
| Qwen3.5-9B | 16 | 0.9167 | 0.4531 | 0.4167 | 1.0000 |
| Qwen3-14B Base | 24 | 0.9583 | 0.4708 | 0.2500 | 1.0000 |

Plain-language finding / 说人话结论：

- The residual-state process signal replicated beyond Qwen3.5: Qwen3-14B also has a strong valid-vs-invalid process direction in middle/late residual states. / residual-state 过程信号跨模型复现：Qwen3-14B 也有强 valid-vs-invalid 方向。
- This strengthens the causal-chain claim at the hidden-state level: the process signal exists before the final Yes/No decision, yet absolute verifier thresholds can still over-accept invalid traces. / 这加强了隐藏层层面的因果链：过程信号在最终 Yes/No 决策前已经存在，但 absolute verifier 阈值仍可能过度接受 invalid trace。
- Steering is stronger in Qwen3-14B than in Qwen3.5-9B at the tested layers: Qwen3-14B layer 28/36 interventions show large expected-sign effects and multiple margin flips. / Qwen3-14B 的 steering 比 Qwen3.5-9B 更强：第 28/36 层出现大幅同向效应和多次 margin 翻转。
- We should still avoid claiming a complete circuit. The safe claim is: **distributed middle/late residual-state process evidence with causal intervention effects; MLP participation remains partial, not a single knob.** / 仍不能声称完整 circuit。安全说法是：**中后层残差态中存在分布式过程证据，并有因果干预效应；MLP 参与是部分的，不是单一开关。**

## 5. Backend and throughput facts / 后端与吞吐事实

- Qwen2.5-Math vLLM initially failed because `max_model_len=8192` exceeded local `max_position_embeddings=4096`; retry with `max_model_len=4096` succeeded. / Qwen2.5-Math vLLM 初次失败是因为 `max_model_len=8192` 超过本地 4096；改成 4096 后成功。
- vLLM throughput was much higher for compatible CausalLM controls. / 对兼容 CausalLM，vLLM 吞吐明显更高。
- HF remains necessary for hidden states, hooks, residual patching, and Qwen3.5/Gemma4 P0 compatibility. / hidden state、hook、residual patch、以及 Qwen3.5/Gemma4 P0 兼容性仍需要 HF。

## 6. What this means for the paper claim / 对论文主张的影响

Supported more strongly / 得到更强支持：

- Controlled answer-correct/process-invalid risk still stands. / controlled ACPI 风险仍成立。
- Absolute verifier over-accept remains visible in E42/E50. / absolute verifier 过度接受在 E42/E50 中仍清楚。
- Hidden residual process evidence is now supported in both Qwen3.5-9B and Qwen3-14B. / hidden residual 过程证据已在两个 Qwen 系模型上支持。

Weakened or bounded / 需要收窄的部分：

- Natural ACPI prevalence on simple tasks is low/undetected after strict audit. / 简单题自然 ACPI 发生率在严格审计后很低或未检出。
- Hard-task ACPI is not yet measurable because final-correct traces were not obtained under strict trace-selection formatting. / 困难题 ACPI 暂不可测，因为严格 trace-selection 格式下没得到 final-correct trace。
- Any claim about “common natural occurrence” would overstate current evidence. / 不能声称“自然普遍发生”。

Best current framing / 当前最稳妥表述：

> Surface-semantic and multilingual traps can induce answer-correct/process-invalid traces under controlled trace construction. Verifiers often contain recoverable process evidence in residual states, but absolute Yes/No objectives and thresholds can fail to use that evidence, producing over-acceptance. In natural generation, the observed prevalence depends strongly on task difficulty, final-correct conditioning, and formatting/extraction; simple no-leak prompts did not produce robust natural ACPI in our current sample.

中文：

> 表层语义和多语言陷阱可以在受控 trace 构造下诱发“答案正确但过程无效”的 trace。Verifier 的 residual states 中往往存在可恢复的过程证据，但 absolute Yes/No 目标和阈值可能没有正确利用这些证据，从而过度接受 invalid trace。在自然生成中，发生率强依赖任务难度、final-correct 条件化和格式/解析；当前简单无泄露 prompt 样本没有产生稳健自然 ACPI。

## 7. Next high-information experiments / 下一步高信息收益实验

1. **Hard-task parser split / 困难题 parser 分流**：同时报告 strict final-line accuracy 和 benchmark-style `\boxed{}` accuracy。Purpose: distinguish “cannot solve” from “does not follow trace-selection output format.” / 目的：区分模型不会做题和不遵守 trace-selection 输出格式。
2. **Final-correct harvesting / final-correct trace 采样池**：对 hard tasks 用 larger-K vLLM-compatible models or answer-first constrained prompts 采样，先收集 final-correct traces，再人工审计 process validity。/ 先拿到答案正确 trace，再讨论 ACPI。
3. **Mechanism localization / 机制定位**：在 Qwen3-14B layer 24/28/36 上做 token-position patch、residual-vs-MLP-vs-attention split。/ 解释强 steering 来自哪里。
4. **Verifier-objective intervention / verifier 目标干预**：比较 absolute Yes/No、contrastive sibling、span-localized question 三种 objective 在同一 hidden-state signal 上的利用差异。/ 证明“有证据但目标/阈值没用好”。
5. **Broader task bank / 更广任务库**：加入非 discount、非小学算术的 lexical/process traps，例如 unit conversion, conditional probability wording, base notation, set inclusion, geometry-language traps。/ 避免例子过窄。

## 8. Files / 文件

- E48 results: `results/E48_natural_prevalence_official/`
- E49 results: `results/E49_hard_task_conditioning_official/`
- E50 results: `results/E50_residual_probe_steering/`
- Backend appendix: `reports/APPENDIX_BACKEND_COMPATIBILITY_AND_THROUGHPUT_20260428.md`
- Audit logs: `logs/audit_e48_e50_official_results_20260428.json`, `logs/audit_active_official_workspace_20260428.json`

## 9. E51 hard-task parser split addendum / E51 困难题解析器分流补充

After the line-anchored strict parser fix, we ran E51 to separate strict trace-selection formatting from benchmark-style answer extraction.

行首锚定 strict parser 修正后，我们补跑 E51，用来区分 trace-selection strict 格式和 benchmark-style 答案抽取。

| Parser / 解析方式 | Correct rows / 正确行数 | Meaning / 含义 |
|---|---:|---|
| Strict `Final answer:` line | 0 / 84 | No current hard-task row satisfies the strict trace-selection output format with a correct answer. / 当前困难题没有任何行同时满足 strict final-line 和答案正确。 |
| `\boxed{}` benchmark-style | 6 / 84 | Qwen2.5-Math solves some hard tasks but ignores our strict final-line format. / Qwen2.5-Math 有些题会做，但不按 strict final-line 输出。 |
| Loose tail integer | 7 / 84 | Diagnostic only; one extra Gemma row ends with the right number but not in a reliable answer format. / 仅作诊断；额外一个 Gemma 行尾数字正确，但不可靠。 |

Key implication / 关键含义：

- Hard-task bottleneck is mixed: for Qwen2.5-Math, part of the bottleneck is formatting; for Qwen3.5/Gemma4, current samples mostly still fail final-correct acquisition. / 困难题瓶颈是混合的：Qwen2.5-Math 部分是格式问题；Qwen3.5/Gemma4 当前样本主要还是拿不到答案正确 trace。
- Future hard-task experiments must report both benchmark-style correctness and trace-selection strict-format correctness. / 后续困难题必须同时报告 benchmark-style correctness 和 trace-selection strict-format correctness。

E51 files / E51 文件：`reports/E51_HARD_TASK_PARSER_SPLIT_20260428.md`, `results/E51_hard_task_parser_split/e51_hard_task_parser_split_20260428.json`.
