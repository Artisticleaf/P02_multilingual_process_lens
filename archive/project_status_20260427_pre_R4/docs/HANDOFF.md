# Handoff

Date: 2026-04-27 CST
Project folder: `/home/Awei/P02_multilingual_process_lens`

Old `/home/Awei/LLM/passage` contents were moved to the hidden archive recorded in `/home/Awei/trashbin/.latest_passage_archive`.

Do not start `codex-taskboard continuous` mode.

## Environment

```bash
cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/src
```

For Qwen3.5 / Ministral3, use hf5 first:

```bash
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
```

Avoid hf5 for older Qwen/DeepSeek unless needed.

## Latest Project Memory

- Knowledge graph / stage charter: `docs/HISTORY_KG_20260427_R3.md`.
- Round3 consolidated report: `reports/P02_ROUND3_KG_AUDIT_EXPLORATION_20260427.md`.
- Human sibling audit notes: `reports/E16_manual_sibling_audit_notes_20260427.md`.

## Current Main Claim

Downgrade old pass@8/self-distillation as main contribution. Current active claim:

> Multilingual/surface-form traps can create answer-correct but process-invalid trace-selection risk. Absolute verifiers over-accept these traces, while sibling contrastive comparison and selected non-verdict hidden spans expose part of the process/error signal. Process-consistency triangulation is a plausible method branch but not yet proven automatically.

## Key Results

Manual audit:

- `data/processed/manual_e05_audit_combined_20260427.jsonl`: 154 rows; 18 process-invalid; 9 strict ACPI; 4 paper-grade ACPI.
- Paper-grade anchors: `234`, `402`, `445`, `178`.
- Best same-route / near-route pairs are recorded in `data/processed/e13_same_route_pair_bank_20260427.json`.

Verifier reliability:

- `reports/E06_e05_manual_trace_verifier_summary.md`: absolute verifier false-accept remains high across DeepSeek, Phi, Qwen3.5, Qwen3-14B.
- Qwen3-14B is best but still accepts many ACPI.

Contrastive verifier:

- `reports/E16_contrastive_pair_expansion_summary.md`: 11-pair expanded contrastive result.
- Qwen3-14B acc 0.818, Qwen3.5 acc 0.750, Phi acc 0.568, DeepSeek acc 0.477.
- Claim should be bounded: contrastive helps Qwen-family verifiers, not all small models.

Span patch:

- `reports/E17_real_semantic_drift_span_patch_summary.md`.
- Qwen14 same-route `358/359` has strong non-verdict effects: problem_span L14 v2b=2.250, b2v=-1.000; support/trace spans also show clean effects.
- Qwen3.5 `234/235` support_error_span L3 reproduces clean effect: v2b=0.750, b2v=-3.812.
- Qwen3.5 `229/225` is asymmetric/cross-input confounded; do not overclaim.

Triangulation policy:

- `reports/E14_process_triangulation_policy_summary.md`.
- final-correct-only keeps 9 ACPI and 4 paper-grade ACPI.
- format+final still keeps 3 paper-grade ACPI.
- same-route oracle rejection removes ACPI on the selected set with clean recall 0.958 and coverage 0.448; needs automatic proxy.

## Next Best Stage

Stage: `S3 sibling-controlled causal localization + automatic triangulation proxy`.

Primary branch:

1. Generate more same-route siblings for `445` Qwen14 `percent_then_discount zh->en`.
2. Generate format-clean same-route valid sibling for `234` Qwen3.5 `disc_en_25_off zh->zh`.
3. Reach at least 8 clean same-route ACPI/semantic-drift pairs before large head/MLP localization.

Mechanism branch:

1. Decompose robust spans only: Qwen14 `358/359` L9/L14/L20, Qwen14 `402/403` L20, Qwen3.5 `234/235` L3/L8.
2. Run attention-vs-MLP patching before head/neuron-level work.
3. Include negative controls: valid-vs-valid, unrelated same-length spans, final-answer-only, format nonsense pairs.

Method branch:

1. Prototype process-consistency triangulation with route/paraphrase variants and balanced contrastive verifier prompts.
2. Metrics: ACPI kept, paper-grade ACPI kept, clean recall, coverage, order-bias gap, cost per accepted clean trace.

## Useful Commands

```bash
# Rebuild summaries
PYTHONPATH=src python scripts/summarize_manual_trace_verifier.py \
  --results-dir results/E06_e05_manual_trace_verifier \
  --out reports/E06_e05_manual_trace_verifier_summary.md \
  --label-file data/processed/manual_e05_audit_seed_20260427.jsonl \
  --title "E06 E05 Manual Trace Verifier Summary"

PYTHONPATH=src python scripts/summarize_contrastive_acpi_verifier.py \
  --results-dir results/E16_contrastive_pair_expansion \
  --out reports/E16_contrastive_pair_expansion_summary.md

PYTHONPATH=src python scripts/summarize_real_acpi_span_patch.py \
  --results-dir results/E17_real_semantic_drift_span_patch \
  --out reports/E17_real_semantic_drift_span_patch_summary.md
```
