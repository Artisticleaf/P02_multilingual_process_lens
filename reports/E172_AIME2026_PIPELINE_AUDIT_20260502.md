# E172 AIME2026 Pipeline Audit / E172 AIME2026 pipeline 审计

- Passed / 通过：`True`
- Tasks / 题目数：30
- Errors / 错误：`[]`
- Warnings / 警告：`[]`

## Definitions / 定义

- `baseline_nonthinking`: Chat template is requested with enable_thinking=False when supported; prompt contains only the problem.
- `hidden_gate`: A teacher-forced component monitor scores the current generated prefix; crossing the calibrated E166 threshold triggers a non-thinking controlled-check branch.
- `controlled_thinking`: The second branch is still rendered with enable_thinking=False; the control is a short visible check instruction derived from hidden risk, not long-CoT thinking mode.

## Guards / 防错点

- AIME 2026 answers are offline scoring metadata only.
- Hidden observations are made on causal prefixes of the model's own generation.
- The hidden gate records every observation with risk score, threshold, token count, and visible span.
- The gate can trigger only from hidden/component risk, never from comparing to the gold answer.
- Baseline, observed-prefix, and gated branch rows keep mode and prompt fields explicit for audit.
