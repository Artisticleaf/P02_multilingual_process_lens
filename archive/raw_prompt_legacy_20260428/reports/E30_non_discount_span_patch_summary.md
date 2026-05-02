# E30 Non-Discount Span Patch Summary / E30 非折扣 span patch 总结

Result / 结果: `results/E30_non_discount_span_patch/qwen3_14b_base_real_acpi_span_patch.json`.

Pair / 样本对：Qwen14 `inequality_no_more_than`, valid row `300310` vs ACPI row `300311`.

The ACPI row says `between 3 and 7, inclusive`, which would include 3, but then lists `4,5,6,7` and gives the correct final answer 4. / ACPI 行把“大于3且不超过7”改写成 `between 3 and 7, inclusive`，这个说法会包含 3；但 trace 随后列出 `4,5,6,7` 并给出正确最终答案 4。

## Key Numbers / 关键数字

- Base valid margin / 有效 trace 基线 Yes-No 边际: `2.000`.
- Base bad margin / ACPI trace 基线 Yes-No 边际: `2.125`.
- Both margins are positive, so the verifier accepts both traces before patching. / 两个边际都为正，所以 patch 前 verifier 都接受。
- `support_error_span` at L9/L14 had large effects, but the direction was not the clean S6 pattern: L9 `valid->bad -0.625`, `bad->valid -0.375`; L14 `valid->bad -1.000`, `bad->valid -0.500`. / L9/L14 的 support/error span 有较大影响，但方向不是 S6 那种干净模式。
- Final-answer and verdict-position patches were weak. / final-answer 与 verdict-position patch 较弱。

## Interpretation / 解释

This is not a positive hidden-span causal proof. It is a boundary result. / 这不是正向 hidden-span 因果证明，而是边界结果。

The non-discount inequality pair is useful for verifier-output behavior: absolute verifiers over-accept it, contrastive prompts expose order bias, and locate-only prompts can name the bad phrase. But residual span patching does not yet show the clean `valid support -> more accept` and `bad error -> less accept` causal pattern seen in S6 Qwen14 discount/pay75. / 这条非折扣不等式 pair 对 verifier 输出行为很有用：绝对式 verifier 会过度接受，对比式暴露位置偏置，locate-only 能指出坏短语。但 residual span patch 还没有显示 S6 Qwen14 折扣/pay75 中那种干净的“有效支持 -> 更接受、错误证据 -> 更拒绝”的因果模式。

Practical consequence / 实际含义：next mechanism work should stay anchored on the robust S6 Qwen14 span and use E30 inequality as a negative/contrastive mechanism boundary, unless more non-discount pairs are found. / 机制工作下一步仍应以稳健的 S6 Qwen14 span 为锚点；E30 不等式 pair 先作为机制边界/负控，除非找到更多非折扣稳健 pair。
