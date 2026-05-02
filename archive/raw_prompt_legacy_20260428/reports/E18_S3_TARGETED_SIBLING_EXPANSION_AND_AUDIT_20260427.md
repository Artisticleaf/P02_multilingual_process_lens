# E18-S3 Targeted Sibling Expansion And Audit / E18-S3 定向同题兄弟扩展与审计

Date / 日期: 2026-04-27 CST

## 1. Goal / 目标

E18 starts the S3 stage: expand same-route sibling evidence around the current paper-grade anchors, especially:

- Qwen3-14B `percent_then_discount zh->en`: find a same-route valid sibling for the old `445` 打八折 lexicalization ACPI.
- Qwen3.5 `disc_en_25_off zh->zh`: replace the old valid sibling `235` with a format-clean same-route valid sibling for bad row `234`.
- DeepSeek/Phi: keep as boundary controls, not as primary mechanistic anchors unless manual audit finds clean pairs.

中文说明：E18 是 S3 阶段的启动实验，目标是围绕当前论文级锚点扩展“同模型、同题、同输入语言、同推理语言”的 sibling pair（兄弟轨迹对）。重点是为 Qwen3-14B 的“打八折 -> 80% discount”错误找到同 route 有效 sibling，并为 Qwen3.5 的 `234` 折扣 ACPI 找到格式干净的有效 sibling。

## 2. Execution / 执行

Artifacts / 产物：

- Generation config / 生成配置: `configs/e18_targeted_sibling_tasks.yaml`
- Four-GPU launcher / 四卡启动脚本: `scripts/launch_e18_targeted_siblings_4gpu_tmux.sh`
- Generator update / 生成脚本更新: `scripts/run_trace_pool_generate.py` now supports `--routes`, `--seed`, and `--out-suffix`.
- Triage update / 初筛脚本更新: `scripts/build_trace_process_audit_sheet.py` now includes E05/E18 task-specific cues.
- Raw generations / 原始生成: `data/raw/e18_targeted_sibling_expansion/`
- Triage sheet / 初筛表: `data/processed/e18_targeted_trace_audit_sheet.jsonl`, `data/processed/e18_targeted_trace_audit_sheet.tsv`
- Manual audit / 人工审计: `data/processed/e18_manual_targeted_audit_20260427.jsonl`
- Combined labels / 合并标签: `data/processed/manual_e05_plus_e18_targeted_20260427.jsonl`

Throughput / 吞吐：all four RTX 5090 GPUs were used concurrently.

| model | gpu | rows | route/task focus |
|---|---:|---:|---|
| `qwen3_14b_base` | 0 | 108 | `zh->en`, `zh->zh`, `en->zh`; 打八折、七五折、75% off、ratio、derivative |
| `qwen35_9b` | 1 | 108 | `zh->zh`, `zh->en`, `en->en`; clean sibling replacement for `234` |
| `deepseek_r1_0528_qwen3_8b` | 2 | 72 | boundary/control generation |
| `phi4_mini_reasoning` | 3 | 72 | boundary/control generation |
| total / 总计 | 4 GPUs | 360 | targeted sibling expansion |

## 3. Manual Audit / 人工审计

Manual targeted audit covered 32 high-information rows. Labels separate process validity, final correctness, route adherence, and format/training-candidate hygiene.

| slice / 切片 | count / 数量 |
|---|---:|
| audited rows / 已审计行 | 32 |
| process-invalid / 过程无效 | 8 |
| final-correct / 答案正确 | 25 |
| format-broken / 格式破损 | 9 |
| strict ACPI / 严格 ACPI | 1 |
| paper-grade ACPI / 论文级 ACPI | 1 |

### 3.1 New Direct Same-Route Paper-Grade ACPI / 新增同 route 论文级 ACPI

New row: `audit_idx=180092`, Qwen3-14B, `percent_then_discount`, `zh->en`, sample 2.

Reading / 逐句审计：

- The problem says `先上涨25%，再打八折`; correct semantics: increase 80 to 100, then pay 80%, final 80.
- The trace says `Now apply the 80% discount`, which in English means pay 20%, but then computes `100 * 0.80 = 80`.
- Final answer is correct, but the English lexicalized process is invalid.

This directly fixes the prior weakness of old `445`: E18 now has a same-route valid sibling from the same generation batch.

Valid siblings / 有效兄弟样本：

- `audit_idx=180091`: clean English same-route valid trace, final 80.
- `audit_idx=180094`: clean English same-route valid trace, explicitly says 20% discount/pay80, final 80.

### 3.2 Clean Replacement Siblings For Qwen3.5 Row 234 / Qwen3.5 行 234 的干净有效 sibling

E18 produced multiple format-clean valid same-route traces for `disc_en_25_off zh->zh`:

- `181000`, `181001`, `181002`, `181004`: process-valid, final-correct, format-clean.
- These replace old valid side `235`, whose process was valid but format/training hygiene was weak.

This strengthens the causal and contrastive evidence around original bad row `234` (`打八折，即原价的75%`).

### 3.3 Boundary Controls / 边界控制

A secondary random audit of DeepSeek/Phi high-priority rows found many red triage rows are not clean ACPI:

- DeepSeek often has correct reasoning but prompt restatement, no clean final marker, or instruction spill.
- Phi often produces long self-checking traces; some rows hallucinate numbers or produce nonsense after a correct derivation.
- No new clean paper-grade ACPI was promoted from the random DeepSeek/Phi sample in this round.

Interpretation / 解释：the high red-cue rate in `reports/E18_targeted_trace_audit_triage_summary.md` is useful for triage but cannot be treated as ground truth frequency.

## 4. Follow-Up Experiments / 后续实验

### 4.1 E21: Contrastive Verifier On New Qwen14 打八折 Pair / 对新增 Qwen14 打八折 pair 的对比 verifier

Artifacts / 产物：`reports/E21_e18_contrastive_verifier_summary.md`.

| verifier / 验证器 | rows | acc | mean target margin | reading / 解读 |
|---|---:|---:|---:|---|
| `qwen35_9b` | 12 | 0.667 | 0.083 | partly detects the lexical ACPI but margins are small |
| `qwen3_14b_base` | 12 | 0.333 | -0.438 | fails badly on its own new 打八折 ACPI pair |

Important: this is a negative/boundary result. The new pair is a hard surface-lexicalization failure: absolute Qwen14 verifier assigns higher process-valid margin to the bad trace than to the valid trace, and Qwen14 contrastive judging often selects the valid trace as invalid.

### 4.2 E20: Span Patch On New Qwen14 打八折 Pair / 对新增 Qwen14 打八折 pair 的 span patch

Artifacts / 产物：`reports/E20_e18_same_route_span_patch_summary.md`.

Result: residual patching on the new direct same-route Qwen14 ACPI pair is weak and mostly final-answer-span dominated. It does not reproduce the strong non-verdict effect seen in Qwen14 `358/359`.

Interpretation / 解读：this is an important guardrail. Not every same-route lexical ACPI exposes a clean process span under the current Yes/No verifier objective. The claim should remain: hidden process/error-span signal exists in selected robust pairs, not in all ACPI pairs.

### 4.3 E22: Clean-Sibling Span Patch For Original Qwen3.5 Bad Row 234 / 对 Qwen3.5 原 bad row 234 的干净 sibling span patch

Artifacts / 产物：`reports/E22_e18_clean_sibling_span_patch_summary.md`.

| pair / 配对 | best span / 最佳 span | layer / 层 | v2b | b2v | reading / 解读 |
|---|---|---:|---:|---:|---|
| `234_bad / 181000_valid` | support_error_span | 3 | 0.250 | -2.438 | clean non-verdict signal survives with format-clean valid sibling |
| `234_bad / 181001_valid` | trace_span | 16 | 0.500 | -0.562 | second clean sibling also works, weaker but aligned |

This is the strongest S3 positive causal update: replacing the old format-confounded valid sibling does not remove the Qwen3.5 non-verdict patch effect.

### 4.4 E23: Contrastive Verifier With Clean Qwen3.5 Siblings / 干净 Qwen3.5 sibling 的对比 verifier

Artifacts / 产物：`reports/E23_e18_clean_sibling_contrastive_summary.md`.

| verifier / 验证器 | rows | acc | mean target margin |
|---|---:|---:|---:|
| `qwen3_14b_base` | 8 | 1.000 | 2.141 |
| `qwen35_9b` | 8 | 1.000 | 0.594 |

Interpretation / 解读：once the valid sibling is format-clean and same-route, Qwen-family contrastive verification is very strong on the Qwen3.5 discount ACPI, while absolute verification had previously over-accepted the bad row.

### 4.5 E19: Module-Level Hidden-State Patch / 模块级隐藏状态 patch

Artifacts / 产物：`reports/E19_real_acpi_module_patch_summary.md`.

| model / 模型 | pair / 配对 | best module / 最佳模块 | span / span | layer / 层 | v2b | b2v |
|---|---|---|---|---:|---:|---:|
| `qwen3_14b_base` | `358_bad/359_valid` | MLP | support_error_span | 14 | 1.750 | -0.375 |
| `qwen3_14b_base` | `402_bad/403_valid` | MLP | trace_span | 9 | 0.375 | -0.250 |
| `qwen35_9b` | `234_bad/235_valid` | MLP | trace_span | 1 | 1.250 | -0.062 |
| `qwen35_9b` | `229_bad/225_valid` | MLP | trace_span | 1 | 0.312 | -0.188 |

Interpretation / 解读：the robust residual effects are partly attributable to MLP outputs, not only whole residual streams. This is still a smoke test, not a head/neuron circuit proof.

## 5. Claim Update / 主张更新

Upgrade / 升级：

- We now have a new direct same-route Qwen14 `打八折 -> 80% discount` ACPI (`180092`) plus valid siblings (`180091`, `180094`).
- Qwen3.5 `234` remains strong after replacing the format-broken valid sibling with clean E18 siblings; both contrastive verification and span patch survive.
- Module-level patching gives the hidden-layer branch a more solid black-box interpretability footing.

Downgrade / 降级或边界：

- The new Qwen14 打八折 pair is hard for the current verifier objective: contrastive and residual patching are weak or reversed. This prevents overclaiming that sibling comparison always solves ACPI.
- DeepSeek/Phi remain boundary controls with many format/prompt-spill artifacts; do not use their triage rates as ACPI prevalence.

## 6. Reliability Audit / 可靠性审计

- Data leakage / 数据泄露: E18 generations are newly produced from fixed task prompts; labels are manual post-hoc audit and are not used to train any model in this project.
- Route confound / route 混杂: manual labels explicitly separate `manual_route_valid` from `manual_process_valid`; route violations are not counted as process invalid unless the math/semantics is wrong.
- Format confound / 格式混杂: format-clean valid siblings are now available for Qwen3.5 `234`, reducing the old `235` confound.
- Triage false positives / 初筛误报: regex red-cue rows are only audit candidates; random DeepSeek/Phi checks showed many are valid-but-format-broken or prompt spill.
- Verifier order bias / 验证器顺序偏差: E21/E23 use balanced `bad_A` and `bad_B` orders.
