# Stage Charter: Cross-Model Causal Anchor Smokes

Date: 2026-04-27

## Paper-Level Claim Under Test

Candidate claim: multilingual/tokenization-induced process opacity can create a causal path from surface-language representation differences to process-validity misread and unsafe trace selection. The claim is not accepted yet; this stage should either upgrade it to a cross-model causal hypothesis or downgrade it to a Qwen-family case study.

## Stage Boundary

This is a feasibility + mechanism-localization stage. It is not a method-finalization or paper-integration stage.

## Competing Paths Considered

1. Scale language routing for accuracy. Rejected for now: high collision risk and weak local signal.
2. Continue verifier-filtered distillation. Rejected as novelty: useful hygiene, not a new claim.
3. Build a large trace dataset immediately. Deferred: expensive before knowing which models expose the signal.
4. Cross-model causal anchor matrix. Chosen: highest information gain per GPU-hour.
5. Tokenizer retraining or embedding surgery. Deferred: premature until fragmentation-to-process-risk link is shown.

## Execution Package

Primary branch: run P0 model anchor matrix over tokenizer fragmentation, contextual concept bridge, process-verdict margin, and residual patching.

Audit branch: include negative controls and model-family controls; record base vs post-trained status; do not use the old outcome checkpoint as main evidence.

Contingency branch: if P0 models fail or downloads block, run local models first and create a tokenizer-only registry for remote candidates.

## Budget

At least two evidence units before closeout unless a red audit appears:

- Evidence Unit A: tokenizer/contextual-bridge/process-margin matrix on at least 3 local models.
- Evidence Unit B: causal residual patching on at least 2 models, or a documented failure showing why patching is invalid.

## Stage Progress Update

Completed on 2026-04-27:

- Evidence Unit A exceeded: hard anchor matrix ran on 7 models.
- Evidence Unit B exceeded: final-token and span-specific residual patching ran on 7 models.
- Additional audit unit added: generated trace pools were converted into a process-audit TSV/JSONL for manual labeling.

Provisional stage decision:

- Upgrade to a cross-model causal hypothesis for synthetic anchors: process-validity information is patchable from trace/support-error spans in several model families.
- Do not upgrade to a paper-level claim until the same causal pattern is shown on real generated answer-correct/process-invalid traces.
