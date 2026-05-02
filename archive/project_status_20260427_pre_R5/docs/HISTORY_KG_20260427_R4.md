# P02 History Knowledge Graph R4 / P02 历史知识图谱 R4

Date / 日期: 2026-04-27 CST
Project / 项目: `/home/Awei/P02_multilingual_process_lens`

This is the active project memory after archiving older status documents. / 本文件是归档旧状态文档后的当前项目记忆。

## 0. Active Claim / 当前主张

Paper-level claim candidate / 论文级候选主张：

> 多语言/表层语义陷阱会产生 answer-correct but process-invalid（答案正确但过程无效，ACPI）的 trace-selection risk（轨迹选择风险）；这些风险并不只是“答案错/格式坏”，而可能由 surface lexicalization（表层词汇化）、process semantics（过程语义）、verifier objective/threshold（验证器目标与阈值）之间的错配共同造成。真实 trace（生成轨迹）中存在可被 sibling comparison（兄弟轨迹对比）或 residual/module span patch（残差流/模块 span patch）暴露的 process/error-span signal（过程/错误 span 信号），但 absolute Yes/No verifier（绝对式是/否验证器）往往会过度接受。

Current stage / 当前阶段：`S3 sibling-controlled causal localization + automatic triangulation proxy`（S3：兄弟对控制的因果定位 + 自动三角测量 proxy）。

## 1. Mainlines / 五条主线

| Mainline / 主线 | Question / 问题 | Current status / 当前状态 |
|---|---|---|
| A. Natural ACPI existence / 真实 ACPI 存在性 | Do real generated traces contain final-correct but process-invalid reasoning? / 真实生成轨迹是否有答案正确但过程错误？ | Active. E05 had 9 strict ACPI and 4 paper-grade ACPI; E18 added new direct same-route Qwen14 paper-grade ACPI `180092`. |
| B. Verifier reliability / verifier 可靠性 | Do absolute verifiers filter these risks? / 绝对 verifier 能否筛掉这些风险？ | Strong failure evidence. E06 showed high false accept; E21 shows Qwen14 can fail even in contrastive mode on a new hard same-route lexical ACPI; E23 shows contrastive succeeds on clean Qwen3.5 discount pairs. |
| C. Multilingual surface-semantic mechanism / 多语言表层语义机制 | Are errors tied to surface lexicalization rather than random math mistakes? / 错误是否来自表层语义词汇化而非随机数学错误？ | Stronger after E18: `打八折` lexicalized as English `80% discount` while the computation uses pay80. |
| D. Hidden process/error signal / 隐藏过程与错误信号 | Is process-validity information represented in non-verdict spans? / 非 verdict span 是否含过程有效性信息？ | Active but bounded. E22 clean sibling patch for Qwen3.5 survives; E19 module patch localizes part of robust effects to MLP outputs; E20 Qwen14 new pair is weak, so not universal. |
| E. Sibling/triangulation mitigation / 兄弟对比与三角测量缓解 | Can pairwise comparison or conservative consistency reduce risk? / 对比与一致性策略能否降低风险？ | Promising but not final. E23 contrastive is perfect on clean Qwen3.5 siblings; E21 is mixed/negative on hard Qwen14 打八折, so automatic proxy must be conservative. |

## 2. Evidence Ledger / 证据台账

| ID / 编号 | Artifact / 产物 | Finding / 发现 | Status / 状态 |
|---|---|---|---|
| E05/E06 | `reports/E05_manual_acpi_audit_combined_summary.md`, `reports/E06_e05_manual_trace_verifier_summary.md` | Manual ACPI exists; absolute verifiers over-accept invalid/ACPI traces. / 人工确认 ACPI 存在；绝对 verifier 过度接受。 | Core evidence / 核心证据 |
| E16/E17 | `reports/E16_contrastive_pair_expansion_summary.md`, `reports/E17_real_semantic_drift_span_patch_summary.md` | Qwen-family contrastive helps selected pairs; non-verdict residual span patch works on selected same-route/semantic-drift pairs. / Qwen 系对比有帮助；部分非 verdict span 有因果信号。 | Active with caveats / 有边界 |
| E18 | `reports/E18_S3_TARGETED_SIBLING_EXPANSION_AND_AUDIT_20260427.md` | Four-GPU targeted expansion generated 360 rows; manual audit found new direct same-route Qwen14 ACPI `180092` and clean Qwen3.5 valid siblings `181000/181001/181002/181004`. / 四卡定向扩展生成 360 行；新增 Qwen14 同 route ACPI，并找到 Qwen3.5 干净 sibling。 | New S3 evidence / 新 S3 证据 |
| E19 | `reports/E19_real_acpi_module_patch_summary.md` | MLP-output patch reproduces several robust residual effects. / MLP 输出 patch 复现部分稳健残差信号。 | Hidden-layer upgrade / 隐藏层升级 |
| E20/E21 | `reports/E20_e18_same_route_span_patch_summary.md`, `reports/E21_e18_contrastive_verifier_summary.md` | New Qwen14 打八折 pair is hard: absolute and contrastive objectives can prefer the bad trace; span patch is weak. / 新 Qwen14 打八折 pair 很难：绝对与对比目标都可能偏向坏轨迹；span patch 弱。 | Boundary evidence / 边界证据 |
| E22/E23 | `reports/E22_e18_clean_sibling_span_patch_summary.md`, `reports/E23_e18_clean_sibling_contrastive_summary.md` | Qwen3.5 `234` survives clean-sibling replacement: support/error span patch and contrastive verification both work. / Qwen3.5 `234` 在替换为干净 sibling 后仍成立。 | Strong positive update / 强正向更新 |
| Literature / 文献 | `docs/LITERATURE_AND_NOVELTY_REVIEW_20260427.md` | Generic process supervision, verifier benchmark, multilingual hidden-representation, and patching claims have high collision risk; P02 should emphasize multilingual lexical ACPI + objective mismatch + hidden span signal. / 泛化过程监督、多语言隐藏表示、patching 方法本身容易撞车；P02 应强调多语言词汇化 ACPI、目标错配和隐藏 span 信号。 | Novelty guardrail / 创新边界 |

## 3. Updated Claim Status / 主张状态更新

Upgraded / 升级：

1. `打八折 -> 80% discount` is no longer only an old cross-route example. E18 produced a direct same-route Qwen14 paper-grade ACPI `180092` with valid siblings `180091` and `180094`. / “打八折 -> 80% discount” 不再只是旧的 cross-route 例子；E18 产生了同 route 论文级 ACPI 和有效 sibling。
2. Qwen3.5 `234` is stronger: E18 produced format-clean valid siblings, and E22/E23 preserved hidden-span and contrastive signals. / Qwen3.5 `234` 更强：新干净 sibling 保留了 hidden-span 与对比信号。
3. Hidden-layer interpretability is stronger after E19: MLP-output patch explains part of robust residual effects. / E19 后隐藏层可解释性更强：MLP 输出解释了部分稳健残差信号。

Downgraded or bounded / 降级或边界：

1. Sibling comparison is not universally sufficient: E21 shows Qwen14 fails on its own hard `打八折` ACPI. / sibling 对比不是万能的；E21 显示 Qwen14 在自身 hard pair 上失败。
2. Residual/module patching should not be claimed for every ACPI: E20 is weak on the new Qwen14 pair. / 不应宣称每个 ACPI 都可 patch；E20 在新 Qwen14 pair 上较弱。
3. DeepSeek/Phi triage rates are not ACPI prevalence: random checks show format spill, prompt echo, and long self-check artifacts. / DeepSeek/Phi 初筛率不是 ACPI 频率，随机复核多为格式与提示泄漏。

## 4. Five-Mainline Adequacy / 五条主线是否足够

Conclusion / 结论：五条主线足够，但必须作为一条因果证据链来写，而不是五个独立实验。

Required integration / 必须整合为：

1. A shows existence / A 证明存在性。
2. C explains why these errors arise in multilingual surface forms / C 解释多语言表层形式如何触发错误。
3. B shows why absolute verifier selection is unsafe / B 证明绝对 verifier 选择不安全。
4. D shows the error/process information can exist in hidden non-verdict spans / D 证明隐藏非 verdict span 可携带过程信号。
5. E tests whether sibling comparison or triangulation can mitigate risk / E 测试兄弟对比或三角测量是否能缓解风险。

Additional cross-cutting layer / 额外横向层：audit controls（审计控制）、order-bias controls（顺序偏差控制）、format/truncation separation（格式/截断分离）、pre-registered downgrade rules（预注册降级规则）。

## 5. Reliability And Leakage Audit / 可靠性与泄露审计

- No training leakage / 无训练泄露：E18 samples are newly generated and manually labeled after generation; no model is trained on them.
- Format and process separated / 格式与过程分离：manual labels include `manual_process_valid`, `manual_final_correct`, `manual_format_valid`, `manual_route_valid`.
- Order balanced / 顺序平衡：contrastive experiments use both `bad_A` and `bad_B`.
- Selected-set warning / 选择集警告：manual audit is high-risk targeted sampling, not population prevalence.
- Human audit role / 人工审计角色：Codex-as-human labels were created sentence by sentence for selected rows; a secondary random sample checked DeepSeek/Phi triage false positives.
- Hidden patch limitation / 隐藏 patch 限制：E19 module patch is below residual level but not yet head/neuron circuit proof.

## 6. Next Actions / 下一步行动

1. Expand clean same-route pair bank to at least 8 pairs across discount, ratio, and derivative families. / 扩展干净同 route pair bank 至至少 8 对，覆盖折扣、比例、导数。
2. Run head-level patching only on robust module targets: Qwen3.5 `234/181000` support_error L3; Qwen14 `358/359` support_error L14; Qwen14 `402/403` trace L9/L20. / 只在稳健模块目标上做 head-level patch。
3. Build automatic triangulation proxy: absolute verifier + contrastive margin + route-consistency conservative reject. / 构建自动三角测量 proxy：绝对 verifier、对比 margin、route consistency 保守拒绝。
4. Add paraphrase and same-problem controls for `打八折` vs `20% off/pay80` vs `80% discount/pay20`. / 为打八折、20% off/pay80、80% discount/pay20 添加同题改写控制。
5. Keep Qwen14 E21/E20 negative result in the paper as an honest boundary condition. / 在论文中保留 Qwen14 E21/E20 负结果，作为诚实边界。
