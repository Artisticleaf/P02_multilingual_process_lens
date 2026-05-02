# E171 Main-Claim Task Bank / E171 主 claim 题库

- Created / 创建时间：`2026-05-02T10:35:03`
- Tasks / 题目数：59
- Dropped duplicate problem+answer rows / 去重丢弃：0

## Sources / 来源

- `configs/e26_aime_hard_tasks.yaml`: 6
- `data/processed/e153_difficult_scenario_tasks_20260501.jsonl`: 32
- `data/processed/e164_hardened_multi_family_tasks_20260501.jsonl`: 21

## Boundary / 边界

- Runtime prompts contain only the original problem; gold answers, trap notes, and labels are offline. / 运行时 prompt 只含原题；答案、陷阱说明、标签只离线使用。
- The AIME rows in `configs/e26_aime_hard_tasks.yaml` are AIME2025 rows; `E26` is an experiment id, not the AIME year. / `E26` 是实验编号，不是 AIME 年份。
