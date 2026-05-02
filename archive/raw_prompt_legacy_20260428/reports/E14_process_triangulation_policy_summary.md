# E14 Process-Consistency Triangulation Policy Smoke

Manual labels: `data/processed/manual_e05_audit_combined_20260427.jsonl`.

This is an oracle simulation over the selected/high-risk manual set. It asks how much safety a conservative rejection radius could buy, and how much clean data it would sacrifice. It is not a deployable detector.

## Overall Policy Trade-Off

| policy | accepted | coverage | clean recall | invalid kept | invalid keep rate | ACPI kept | paper-grade ACPI kept |
|---|---:|---:|---:|---:|---:|---:|---:|
| final_correct_only | 138 | 0.896 | 1.000 | 9 | 0.065 | 9 | 4 |
| format_and_final | 75 | 0.487 | 1.000 | 3 | 0.040 | 3 | 3 |
| same_route_reject_if_any_invalid | 69 | 0.448 | 0.958 | 0 | 0.000 | 0 | 0 |
| same_reason_reject_if_any_invalid | 61 | 0.396 | 0.847 | 0 | 0.000 | 0 | 0 |
| same_task_reject_if_any_invalid | 37 | 0.240 | 0.514 | 0 | 0.000 | 0 | 0 |
| human_training_upper_bound | 72 | 0.468 | 1.000 | 0 | 0.000 | 0 | 0 |

## Reading

- `final_correct_only` estimates the old outcome-only selection risk: it keeps all answer-correct ACPI unless a process check catches them.
- `format_and_final` is safer for training hygiene but still keeps cleanly formatted ACPI such as rows 234, 402, and 445.
- Same-route rejection is the least destructive triangulation radius; same-task rejection is a high-precision but low-coverage upper-bound.
- If expanded data shows same-route rejection catches most paper-grade ACPI while retaining enough clean rows, it becomes a plausible method branch.
