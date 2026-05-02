# E167 Hidden-Derived Repair Case Static Audit / E167 hidden-derived 修复样本静态审计

- Passed / 通过：`True`.
- Cases / 样本数：274.
- By model / 按模型：`{'gemma4_26b_a4b_it': 95, 'gemma4_31b_it': 90, 'qwen35_27b': 89}`.
- By policy / 按策略：`{'budgeted': 133, 'high_precision': 141}`.
- Trigger sources / 触发来源：`{'fallback_top_risk_no_threshold_crossing': 94, 'first_threshold_crossing': 180}`.
- Trigger boundary kinds / hidden 触发边界类型：`{'sentence_end': 274}`.
- Manual-target trigger rows / hidden 触发正好命中人工错步结束点：0.
- Offline manual span equals hidden span rows / 离线人工 span 与 hidden span 完全相同：0.
- Offline hidden span contains manual span rows / hidden span 包含人工 span：231.
- Invalid rows / invalid trace rows：252.

## Issues / 问题

- None.
