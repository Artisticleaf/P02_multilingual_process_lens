# E166 Hidden-Monitor Prefix Bank Static Audit / E166 hidden monitor prefix 库静态审计

Date / 日期：2026-05-02

- Passed / 通过：True
- Prefix points / prefix 点：197
- Monitor targets / 监测目标点：42
- Valid control points / 正确过程控制点：61

## Design Meaning / 设计含义

- This bank is for hidden monitor calibration, not generation. / 这个库用于 hidden monitor 校准，不是生成结果。
- Future hidden replay prompts may use only `problem` and `prefix_text`. / 后续 hidden replay prompt 只能使用 `problem` 和 `prefix_text`。
- Manual error spans and gold answers are offline metadata for evaluation only. / 人工错步和答案只作离线评价元数据。
- `monitor_target=true` marks exact manual error-span ends in invalid traces, used for calibration/audit. / `monitor_target=true` 是 invalid trace 中人工错步结束点，用于校准和审计。

## Counts / 计数

### families
- `code_boundary`: 26
- `geometry_constraints`: 30
- `graph_definition`: 30
- `long_table_aggregation`: 25
- `multilingual_semantic`: 31
- `proof_validity`: 25
- `set_venn_counting`: 30

### trace_classes
- `invalid_answer_correct`: 75
- `invalid_answer_wrong`: 61
- `valid`: 61

### boundary_kinds
- `manual_error_span_end`: 42
- `sentence_end`: 155
