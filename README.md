# P02 Multilingual Process Lens

Clean-room project for testing whether multilingual/tokenization representations causally affect process errors, verifier mistakes, and answer-correct/process-invalid trace selection risk.

## Research Spine

We do not treat language routing or verifier filtering as the contribution. The current target is a falsifiable causal chain:

1. tokenizer / surface-language fragmentation perturbs early semantic access;
2. middle layers may reconstruct a contextual concept bridge and process-validity signal;
3. late layers may re-entangle process validity with lexicalization, output language, and format;
4. verifier or selector may misread that state;
5. trace selection may accept answer-correct but process-invalid reasoning.


## Current Project Memory

- Active history / 当前 history: `docs/HISTORY_KG_20260427_R4.md`.
- Active handoff / 当前交接: `docs/HANDOFF.md`.
- Literature and novelty review / 文献与创新性复核: `docs/LITERATURE_AND_NOVELTY_REVIEW_20260427.md`.
- Old project-status docs / 旧项目现状文档: `archive/project_status_20260427_pre_R4/`.

## Directory Layout

- `configs/`: model registry and experiment configs.
- `docs/`: stage charters, handoffs, design notes.
- `data/`: seed tasks, prompts, raw generations, processed labels, human-audit files.
- `experiments/`: runnable experiment packages by evidence unit.
- `results/`: immutable result artifacts by experiment ID.
- `scripts/`: CLI entrypoints for smokes and launches.
- `src/mplens/`: reusable Python package code.
- `logs/`: tmux/stdout/stderr logs.
- `reports/`: generated summaries.

## Environment

Use the existing conda env:

```bash
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
```
