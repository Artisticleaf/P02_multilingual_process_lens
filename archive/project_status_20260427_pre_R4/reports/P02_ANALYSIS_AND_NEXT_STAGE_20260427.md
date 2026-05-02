# P02 Analysis And Next-Stage Plan

Date: 2026-04-27

## Executive Decision

The project has enough signal to continue, but the claim should be narrowed:

- Stronger claim now supported: several small/open models contain patchable process-validity information in real trace text and synthetic hard anchors, but current verifier-style scoring often fails to use it.
- Claim not yet supported: multilingual/tokenizer mechanisms cause trace-selection failures in naturally generated answer-correct/process-invalid traces across models.
- Immediate next stage should be real-ACPI causal validation, not more synthetic anchor expansion.

## Manual Audit Seed

I manually audited 62 generated traces sentence-by-sentence or step-by-step.

Artifacts:

- Labels: `data/processed/manual_trace_audit_seed_20260427.jsonl`
- Verifier results: `reports/E04_manual_trace_verifier_summary.md`
- Legacy first-token scoring was archived because Chinese Yes/No first-token scoring was unreliable: `results/E04_manual_trace_verifier_first_token_legacy/`

Manual label distribution:

| Label | Count |
|---|---:|
| process-valid | 53 |
| process-invalid | 9 |
| final correct | 44 |
| final wrong | 7 |
| final unknown/missing | 11 |
| output format clean | 22 |
| output format broken/truncated/spill | 40 |
| answer-correct/process-invalid candidates | 2 |

The two ACPI candidates are both Phi derivative traces:

- `idx=190`: correct final answer fragment `2x + 3`, but the trace says `const*k` derivative is zero and describes `x'` as `1x`.
- `idx=191`: correct final answer fragment `2x + 3`, but the trace uses a broken derivative definition and an invalid explanation for the `3x` term.

Important correction: heuristic `red_invalid_cue_final_correct` had false positives. For example, `idx=127` is a clean Qwen3-14B derivative solution; it was marked red only because the regex matched derivative terms too broadly. Manual labels are now the authoritative seed.

## Data-Quality Findings

### 1. Truncation Is A First-Order Confound

Many "bad" traces are not process-invalid; they are incomplete. Examples:

- Qwen3.5 average and derivative traces often stop before the final line.
- Qwen3-14B average traces can stop at `x =` or `Final`.
- DeepSeek/Phi long traces often reason correctly but spend tokens restating instructions and then truncate before `Final answer`.

This means future experiments must separate:

- mathematical process validity;
- final-answer correctness;
- output hygiene and stop behavior.

Combining them into one "correct trace" label hides the mechanism.

### 2. After-Final Spill Is Common

Several Qwen3.5 rows solve the first problem correctly, then continue with:

- a new `<think>` template;
- a repeated `Problem/Reasoning` block;
- a different new problem after the correct final answer.

These traces are process-valid for the target question but unsafe as training trajectories. This directly supports a separate `training_candidate` criterion.

### 3. Cross-Language Semantic Drift Appears In Specific Concepts

The clearest non-trivial drift is Chinese `七五折`:

- Correct Chinese interpretation: pay 75% of original price, so `80 * 0.75 = 60`.
- Error mode: treat it as `75% off`, so pay 25% and infer `20`.

This is a better anchor than generic "Chinese vs English is harder" because it localizes a semantic ambiguity that can be tested with counterfactual wording.

### 4. Process-Unfaithful But Answer-Correct Exists, But Is Rare In Current Pool

Only 2/62 manually audited seed rows are clear ACPI. That is too small for paper-level statistics, but enough to show that the failure mode is real and to seed mechanism experiments.

The current trace pool was generated from very easy tasks; models either solve cleanly or truncate. To find more natural ACPI, the next generation pool should use harder tasks and ambiguity controls rather than simply increasing `k` on the same easy tasks.

## E01/E03 Mechanism Interpretation

### E01 Hard Anchor

Hard synthetic anchors showed:

- `qwen3_14b_base`: process acc `1.00`, IFC false accept `0.00`.
- `ministral3_8b_reasoning`: process acc `0.95`, IFC false accept `0.10`.
- `qwen3_8b_base` and `deepseek_r1_0528_qwen3_8b`: IFC false accept `0.40`.
- `phi4_mini_reasoning` and `glm46v_flash`: weak verifier-style behavior.

Interpretation:

- The process-validity signal is not Qwen-only, because Ministral also performs well.
- It is not universal, because Phi and GLM are weak on this verifier formulation.
- DeepSeek-R1-Qwen3-8B remains important as a negative/fragility control relative to Qwen3-8B.

### E03 Span Patch

Span patching showed clean effects beyond final verifier position:

- `qwen3_14b_base`: `trace_span L20`, `support_error_span L14`.
- `qwen3_8b_base`: `trace_span/support_error_span L9`.
- `deepseek_r1_0528_qwen3_8b`: `trace_span L5`, `support_error_span L9`.
- `qwen35_9b`: early `trace_span/support_error_span L3`.
- `ministral3_8b_reasoning`: early `trace_span/support_error_span L7`.
- `phi4_mini_reasoning`: `support_error_span L8`.

Interpretation:

- Verdict-position patching remains strongest, so output-token priors are still a confound.
- But process-text spans also causally move the process-validity margin, which is exactly the bridge needed before QKV/MLP localization.
- The layer pattern suggests early-to-mid span features carry process information, while later verifier positions amplify or lexicalize that information.

## E04 Manual Trace Verifier Reliability

E04 evaluates six models as verifiers over the 62-row manual audit seed.

Two modes:

- `process_only`: ignore truncation/format; judge mathematical process.
- `training_candidate`: keep only if final answer is correct, process is valid, and output hygiene is acceptable.

Key results:

| Verifier | process-only best prompt | Process-invalid false accept | training-candidate false accept range |
|---|---|---:|---:|
| qwen3_14b_base | English | 0.556 | 0.829-0.902 |
| qwen3_8b_base | Chinese | 0.667 | 0.854-0.927 |
| qwen35_9b | English | 0.778 | 0.756-0.878 |
| ministral3_8b_reasoning | Chinese | 0.778 | 0.927-0.976 |
| deepseek_r1_0528_qwen3_8b | tie | 1.000 | 0.976-1.000 |
| phi4_mini_reasoning | tie | 1.000 | 0.878-0.976 |

Interpretation:

- Verifier reliability is language- and objective-conditioned, but not in a simple "Chinese worse" direction.
- Qwen3-14B English prompt is the best current process verifier, yet still accepts 5/9 invalid process traces.
- Chinese prompts can improve some models (`qwen3_8b_base` process-only) but harm others (`qwen3_14b_base` process-only).
- Training-data cleaning is much harder than process-only judging. Nearly every verifier over-accepts truncated, after-final-spill, or malformed traces.
- DeepSeek and Phi behave like near-always-yes verifiers on this seed; their high final-answer ability does not translate into reliable process filtering.

This directly supports the user concern: final-answer-correct traces are not enough; even verifier prompts can over-accept process-invalid or format-broken traces.

## Current Causal Chain Status

| Chain Link | Status | Evidence |
|---|---|---|
| Tokenizer/surface language perturbs early access | plausible but weak | tokenizer inventory + cross-language quirks; not causal yet |
| Mid-layer contextual bridge exists | moderate | E01 bridge metrics, but top1 still easy |
| Process-validity signal is separable in hidden state | moderate-to-strong on synthetic | E03 trace/support span patching |
| Late lexicalization/verdict prior confounds verifier output | strong | verdict-position patch dominates E03 |
| Verifier reliability is language/objective conditioned | moderate | E04 prompt-language differences |
| ACPI trace-selection risk exists in real traces | weak seed evidence | 2 manually confirmed ACPI rows |
| Full causal chain on real generated traces | not yet proven | next stage required |

## Next Stage Charter

Stage name: Real-ACPI Causal Validation.

Boundary: real-trace mechanism validation + verifier audit. Not method finalization.

Primary claim under test:

> Naturally generated answer-correct/process-invalid traces contain process-error features that are detectable in hidden states but often missed by verifier-style selection, and this miss rate is conditioned by language/format.

Success criteria:

- At least 30 manually confirmed ACPI traces across at least 3 model families.
- Process-only verifier false accept remains materially above 0.25 for at least 2 verifier models after prompt hardening.
- Residual span patching on real ACPI pairs reproduces the E03 direction in at least 2 model families.
- At least one QKV/MLP decomposition localizes the real-ACPI signal below residual-stream level.

Failure criteria:

- ACPI is too rare outside artificial prompting.
- Manual labels show most "ACPI" candidates are merely truncation/format artifacts.
- Real-trace span patching fails even on confirmed ACPI pairs.

## Next Experiments

### E05 Real ACPI Harvest

Goal: increase ACPI candidate count.

Design:

- Models: `qwen3_14b_base`, `qwen35_9b`, `deepseek_r1_0528_qwen3_8b`, `phi4_mini_reasoning`, `ministral3_8b_reasoning`.
- Tasks: keep old easy tasks only as controls; add harder ambiguity tasks:
  - Chinese discount semantics: 七五折, 九折, 75% off, reduce by 25%.
  - Ratio denominator traps: boys:girls vs boys:total.
  - derivative/product-rule traps.
  - remainder/modulo long-division traps.
  - average/weighted-average traps.
- Routes: `en->en`, `zh->zh`, `zh->en`, `en->zh`.
- Generation: `k=8`, `temperature=0.9`, `max_new_tokens=384/768` split, because truncation and overthinking must be measured separately.

Manual labels:

- process_valid;
- final_correct;
- format_valid;
- earliest_error_span;
- correction;
- language_mixing;
- whether the trace is usable as an ACPI pair.

### E06 Hardened Verifier Comparison

Goal: test whether false accept is a prompt-format artifact.

Verifier formats:

1. binary Yes/No;
2. JSON `{valid, earliest_error, corrected_step}`;
3. contrastive: show a valid and invalid sibling trace and ask which is cleaner;
4. conservative training filter: default reject unless final/process/format all pass.

Core metric:

- false accept on process-invalid and ACPI rows, split by trace language and prompt language.

### E07 Real-Trace Span Patch

Goal: move from synthetic E03 to real ACPI.

Patch spans:

- `problem_span`;
- `first_error_span`;
- `supporting_valid_span`;
- `final_answer_span`;
- `verdict_pos`.

Initial layers:

- Qwen3-14B: L9/L14/L20/L30.
- Qwen3-8B: L9/L11/L27.
- DeepSeek-Qwen: L5/L9/L27.
- Qwen3.5: L3/L8/L31.
- Ministral: L7/L33.
- Phi: L8/L31.

### E08 QKV/MLP Decomposition

Only start after E07 reproduces.

Prioritized decomposition:

- MLP output patching around best support/error span layers.
- Attention head output patching around the same layers.
- Q/K/V path patching only after head-level localization shows non-trivial effects.

Reason:

- E03 already shows residual-level effects; jumping directly to QKV before real ACPI would be too easy to overinterpret.

## Immediate Execution Completed

I executed E04 in this turn:

- Created 62-row manual audit seed.
- Implemented robust sequence-level Yes/No scoring to avoid Chinese first-token artifacts.
- Ran six verifier models.
- Generated `reports/E04_manual_trace_verifier_summary.md`.

I also executed the E05 harvest smoke:

- Config: `configs/e05_acpi_tasks.yaml`.
- Launcher: `scripts/launch_e05_acpi_harvest_smoke_tmux.sh`.
- Raw traces: `data/raw/e05_acpi_harvest_smoke/`.
- Heuristic audit: `data/processed/e05_acpi_harvest_smoke_audit.json`.
- Rows: 448 total = 4 models x 14 tasks x 4 routes x 2 samples.

Heuristic final-answer rates:

| model | EN reasoning | ZH reasoning | note |
|---|---:|---:|---|
| deepseek_r1_0528_qwen3_8b | 1.000 | 1.000 | very long traces; likely many instruction-restatement tokens |
| phi4_mini_reasoning | 0.982 | 0.982 | EN route has heavy language mixing |
| qwen35_9b | 0.929 | 0.982 | EN repetition rate 0.196 |
| qwen3_14b_base | 1.000 | 0.964 | shortest and cleanest generations |

These are only final-answer heuristics. The next action is manual process audit of E05 rows, prioritizing:

- Chinese discount semantics rows;
- ratio order/denominator rows;
- derivative rows from Phi and DeepSeek;
- rows with high final correctness but low route adherence or repetition.
