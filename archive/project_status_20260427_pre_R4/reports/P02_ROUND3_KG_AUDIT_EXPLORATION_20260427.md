# P02 Round3 KG / Human Audit / Exploratory Experiments

Date: 2026-04-27 CST
Project: `/home/Awei/P02_multilingual_process_lens`

## 1. One-Sentence Update

我们现在的主线应从“自采样蒸馏提升 pass@1”转为：**多语言/表层语义陷阱如何导致 answer-correct/process-invalid trace selection，为什么 absolute verifier 会误收，以及 sibling/triangulation/hidden-span 证据能否把这条因果链坐实**。

## 2. 当前主线任务

### Main Task A: 证明风险真实存在

需要证明的不是“有些模型中文差”，而是更窄、更可检验的事实：同一道数学/语言语义题，模型可能生成最终答案正确但过程语义错误的 trace，且这些 trace 会被 outcome-only 或 absolute verifier 误收。

当前证据：

- `data/processed/manual_e05_audit_combined_20260427.jsonl`: 154 条人工审计，18 条 process-invalid，9 条 strict ACPI，4 条 paper-grade ACPI。
- paper-grade anchors: `234`, `402`, `445`, `178`。
- 结论：存在性成立；频率未知，不能用 selected set 报 prevalence。

### Main Task B: 证明 verifier failure 是链条的一环

当前证据：

- `reports/E06_e05_manual_trace_verifier_summary.md`: 4 个 verifier 的 absolute process-only false accept 都很高。
- Qwen3-14B 最好但仍保留大量 ACPI；DeepSeek/Phi/Qwen3.5 基本强 yes/accept prior。
- `reports/E15_verifier_chain_disagreement_summary.md`: absolute false accept 与 contrastive visibility 可同时出现，说明不是“完全没有过程信号”，而是 objective/threshold/format/language prior 问题。

### Main Task C: 证明机制信号不仅是 final/verdict token

当前证据：

- `reports/E11_real_acpi_span_patch_dense_summary.md`: non-verdict span 有初步 clean effect。
- `reports/E17_real_semantic_drift_span_patch_summary.md`: same-route Qwen14 `358/359` 上，problem/support/trace non-verdict span 的 clean patch effect 很强；Qwen3.5 `234/235` 复现 support_error_span L3。
- 结论：hidden residual 中确实有可 patch 的 process/semantic 信息，但还不能宣称 head/neuron 级定位。

### Main Task D: 形成方法方向，但暂不定稿

候选方法不是简单“路由”，而是 **process-consistency triangulation**：同题多 route/paraphrase/sibling traces 之间比较过程语义，一旦最终答案稳定但过程语义不一致，就保守拒绝或转人工/更强 verifier。

当前证据：

- `reports/E14_process_triangulation_policy_summary.md`: oracle same-route rejection 在 selected set 上可把 ACPI kept 降到 0，同时 clean recall 0.958，但 coverage 只有 0.448。
- 这只是 oracle simulation；后续必须用自动化信号逼近人工标签。

## 3. Human Audit Result

人工审计补充文件：`reports/E16_manual_sibling_audit_notes_20260427.md`。

核心 pair 结论：

| pair | audit value | current use |
|---|---|---|
| `402/403` Qwen14 deriv zh->zh | 最强同 route paper-grade ACPI；答案/格式都干净 | primary causal + verifier pair |
| `234/235` Qwen3.5 discount zh->zh | paper-grade ACPI；valid side 过程正确但 format 风险 | primary contrastive; span patch with caveat |
| `358/359` Qwen14 75% off en->zh | 最干净 same-route semantic drift；bad final wrong | semantic-drift mechanism control |
| `445/442` Qwen14 打八折 zh->en vs zh->zh | 强 lexicalization ACPI，但 cross-route confound | paper example; not clean causal pair |
| `261/260` Qwen3.5 ratio zh->en | self-corrected arithmetic ACPI | data-cleaning risk, weaker paper-grade claim |
| `296/297`, `208/209` | final-wrong/format-nonsense controls | negative controls |

审计修正：没有推翻既有 manual labels；但报告措辞要更严格：self-corrected rows 不应与 unmarked paper-grade ACPI 混为一类。

## 4. Experiments Executed In This Round

### E13 Same-Route Pair Mining

Artifacts:

- `scripts/mine_same_route_pairs.py`
- `data/processed/e13_same_route_pair_bank_20260427.json`
- `reports/E13_same_route_pair_mining_summary.md`

Result:

- Candidate pair records: 41。
- Same-route: 7；same-reason-lang: 21；same-task: 13。
- 最强 same-route pairs: `402/403`, `234/235`, `358/359`, `261/260`, `183/182`, `208/209`, `296/297`。

Meaning:

- 后续不应再从 isolated rows 做机制大结论；应以 sibling pair 为基本 causal unit。
- `445` 仍重要，但需要继续采样找 zh->en same-route valid sibling。

### E14 Process-Consistency Policy Smoke

Artifacts:

- `scripts/analyze_process_triangulation_policy.py`
- `results/E14_process_triangulation_policy/process_triangulation_policy.json`
- `reports/E14_process_triangulation_policy_summary.md`

Key numbers:

| policy | accepted | coverage | clean recall | invalid kept | ACPI kept | paper-grade ACPI kept |
|---|---:|---:|---:|---:|---:|---:|
| final_correct_only | 138 | 0.896 | 1.000 | 9 | 9 | 4 |
| format_and_final | 75 | 0.487 | 1.000 | 3 | 3 | 3 |
| same_route_reject_if_any_invalid | 69 | 0.448 | 0.958 | 0 | 0 | 0 |
| same_reason_reject_if_any_invalid | 61 | 0.396 | 0.847 | 0 | 0 | 0 |
| same_task_reject_if_any_invalid | 37 | 0.240 | 0.514 | 0 | 0 | 0 |

Meaning:

- outcome-only selection 的风险被实证化：final-correct 会保留全部 9 个 ACPI。
- 单纯 format cleaning 不够：仍保留 3 个 paper-grade ACPI。
- conservative route triangulation 有潜力，但当前是人工 oracle，不能作为自动方法结论。

### E15 Verifier-Chain Disagreement

Artifacts:

- `scripts/analyze_verifier_chain_disagreement.py`
- `results/E15_verifier_chain/verifier_chain_disagreement.json`
- `reports/E15_verifier_chain_disagreement_summary.md`

Key result:

- Overall contrastive acc: 0.703。
- Absolute bad false-accept rate on joined rows: 0.938。
- Pairwise qwen35 discount / ratio rows contrastive 更容易；Qwen14 derivative / 打八折 rows 更难。

Meaning:

- absolute verifier 失败和 contrastive verifier 成功并不矛盾：pairwise comparison 能暴露一部分 process signal。
- 这支持后续把 verifier 从 binary accept/reject 改成 sibling comparison / conservative reject。

### E16 Expanded Contrastive Pair Probe

Artifacts:

- `configs/e16_contrastive_pairs_exploratory.yaml`
- `results/E16_contrastive_pair_expansion/`
- `reports/E16_contrastive_pair_expansion_summary.md`

Overall:

| verifier | rows | acc | mean target margin |
|---|---:|---:|---:|
| Qwen3-14B base | 44 | 0.818 | 1.195 |
| Qwen3.5 9B | 44 | 0.750 | 0.681 |
| Phi-4-mini-reasoning | 44 | 0.568 | -0.181 |
| DeepSeek-R1-Qwen3-8B | 44 | 0.477 | 0.095 |

Important slices:

- Qwen3-14B verifier is perfect on Qwen3.5 traces: qwen35 discount / ratio / qiwuzhe / product all 1.000。
- Qwen3-14B is weaker on its own traces: `402/403` 0.500, `358/359` 0.500, `445/442` 0.750。
- Qwen3.5 verifier is strong on `402/403`, `234/235`, `261/260`, `296/297`, but weak on `358/359` and qiwuzhe drift。
- DeepSeek remains near chance; Phi is unstable and often order/pair sensitive。

Meaning:

- E12 不是偶然，但也不是全模型通用。
- “contrastive helps” 的 claim 应限定为 Qwen-family and selected pair families；DeepSeek negative result 是重要边界。

### E17 Real Semantic-Drift / Same-Route Span Patch

Artifacts:

- `configs/e17_real_semantic_drift_pairs.yaml`
- `results/E17_real_semantic_drift_span_patch/`
- `reports/E17_real_semantic_drift_span_patch_summary.md`

Key results:

| model | pair | best non-verdict span | layer | v2b | b2v | interpretation |
|---|---|---|---:|---:|---:|---|
| Qwen3.5 | `234/235` discount | support_error_span | 3 | 0.750 | -3.812 | reproduces E11; strong support-error signal |
| Qwen3.5 | `229/225` qiwuzhe | support_error_span* | 3 | -0.375 | -3.750 | asymmetric; valid->bad fails, cross-input confounded |
| Qwen3-14B | `402/403` derivative | trace_span | 20 | 0.500 | -0.375 | reproduces E11; smaller but clean |
| Qwen3-14B | `358/359` 75% off | problem_span | 14 | 2.250 | -1.000 | strong same-route semantic-drift signal |

Meaning:

- E17 is the strongest new causal result: Qwen14 same-route semantic drift has clean non-verdict patch effects。
- `problem_span` dominance in `358/359` means the model/verifier may encode the problem surface semantics itself differently, not only trace error span。This is scientifically interesting but requires controls: same problem token patch vs trace patch vs support/error phrase patch。
- Qwen3.5 qiwuzhe pair shows why cross-input pairs are risky: b2v direction moves, but v2b does not improve bad-trace margin。

## 5. Updated Claim Status

| claim | status | reason |
|---|---|---|
| old pass@8/self-distillation main claim | downgraded | innovation and performance basis insufficient |
| answer-correct/process-invalid risk exists | active | 9 strict ACPI, 4 paper-grade ACPI |
| absolute verifier over-accepts ACPI | strong active | E06 across 4 models |
| contrastive sibling comparison helps | active but bounded | Qwen14/Qwen3.5 strong; DeepSeek/Phi weak |
| hidden non-verdict process signal exists | active exploratory | E11/E17 positive in selected pairs |
| tokenizer/contextual bridge | weak/revised | E08 discount cosine not enough |
| process-consistency triangulation method | speculative but upgraded | E14 oracle + E16/E17 support, but no automatic detector yet |

## 6. Next Stage Charter

Recommended next stage: `S3 sibling-controlled causal localization + automatic triangulation proxy`。

### Primary branch: sibling-controlled data expansion

Goal: get enough clean same-route pairs before expensive mechanistic localization。

Tasks:

1. Generate more Qwen3-14B `percent_then_discount zh->en` samples to find same-route valid sibling for `445`。
2. Generate more Qwen3.5 `disc_en_25_off zh->zh` samples to replace `235` with format-clean valid sibling。
3. Add same-route pairs for DeepSeek/Phi only if manual audit finds clean examples; otherwise keep them as negative verifier controls。
4. Build stratified audit sheet: model × task family × route × final correctness × format cleanliness。

Stop rule: if <8 clean same-route ACPI/semantic-drift pairs after targeted generation, do not run head/MLP decomposition at scale。

### Mechanism branch: decompose only robust spans

Targets:

- Qwen14 `358/359`: problem_span L9/L14/L20; support_error_span L9/L20; trace_span L20。
- Qwen14 `402/403`: trace/support L20。
- Qwen3.5 `234/235`: support_error_span L3/L8。

Experiments:

1. Attention-vs-MLP patching at selected layers。
2. Head-level patching only at selected attention layers。
3. MLP activation patch / neuron attribution only after attention-vs-MLP identifies a module。
4. Negative controls: patch unrelated same-length spans, final_answer_span-only, valid-vs-valid pairs, final-wrong format controls。

Stop rule: if module-level effects do not reproduce clean v2b/b2v directions, do not claim mechanism localization。

### Method branch: automatic process-consistency triangulation

Prototype policy:

1. Generate 2-4 route/paraphrase variants。
2. Use pairwise contrastive verifier with balanced order and prompt language。
3. Reject if process semantics disagree or if contrastive margins are low/unstable。
4. Preserve clean recall by only applying strict rejection to high-risk task families identified by E07/E13。

Metrics:

- ACPI kept rate。
- paper-grade ACPI kept rate。
- clean recall。
- coverage。
- contrastive order-bias gap。
- cost per accepted clean trace。

### Audit branch: human labels remain authoritative

Near-term human audit queue:

1. Same-route candidate rows around `445` and `234`。
2. More discount lexicalization examples: 七五折, 打八折, 75% off, 25% off, “discount by” vs “sold at”。
3. More derivative coefficient/constant confusion examples。
4. Negative controls where final answer is wrong or format is broken, to prevent overclaiming。

## 7. Bottom Line

这一轮把项目从“零散 smoke”推进到一条更清晰的因果链：

1. 人工审计确认 ACPI/semantic drift 存在。
2. absolute verifier 会大量误收。
3. contrastive sibling comparison 在 Qwen family 上能恢复一部分可见性。
4. selected same-route pairs 上 non-verdict span patch 有因果信号。
5. triangulation 有方法潜力，但必须从 oracle simulation 走向自动 proxy。

下一步不应急着写大论文主张；应集中构造 same-route pair bank，并只在最强 spans 上做机制分解。
