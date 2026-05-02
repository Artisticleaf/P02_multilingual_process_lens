# Experiment Design Review

Date: 2026-04-27

## What We Started

- E01 anchor matrix over local P0/control models.
- E02 tiny real trace-pool generation over local models.
- Remote P0 model downloads started via tmux, excluding Gemma 4 until its tokenizer/processor loading issue is resolved.

## Current Local E01 Signals

- Qwen3-14B-Base is the strongest local process-verifier anchor on synthetic cases: process accuracy 1.0, invalid-final-correct false accept 0.0.
- Qwen3-8B-Base is positive but imperfect: process accuracy 0.8125, invalid-final-correct false accept 0.375.
- DeepSeek-R1-0528-Qwen3-8B is meaningfully worse than Qwen3-8B-Base on these synthetic process cases: process accuracy 0.6875, invalid-final-correct false accept 0.5.
- Qwen2.5-Math-7B-Instruct and Llama3.2-3B both show serious verifier-style failures in this smoke. Treat them as controls, not as proof that the causal chain is false.

## Design Problems Found

1. Contextual-bridge top1 is too easy and saturates. We patched the metric to include hard negative margin and early-bridge layer. Next version needs more confusable terms and sentence-level paraphrases.
2. Synthetic invalid-final-correct traces are still artificial. They are useful for anchor calibration but cannot support the paper-level claim alone.
3. Residual patching currently patches the final verifier-token position only. It gives useful causal evidence but may conflate process signal with verdict-token priors.
4. Qwen3-14B late patching has an unexpected bad-to-valid positive effect. This is a red audit item: inspect per-case margins before interpreting as clean process-causality.
5. E02 generation prompts cause some models to repeat the prompt. The next trace-pool prompt should use stricter stop conditions, chat templates for instruct models, and shorter max_new_tokens.

## Next Corrections

- Add hard/confusable term set: e.g. numerator/denominator, factor/multiple, derivative/integral, median/mean, remainder/quotient.
- Add span-specific patching at problem term, first wrong step, arithmetic operator, final answer, and verifier verdict positions.
- Separate output languages and verdict formats: Yes/No, JSON validity, earliest-error-step, free critique.
- Build a deterministic final-answer parser per task type before process labeling.
- Use real generated ACPI pairs for causal patching; synthetic pairs remain calibration only.

## Update After E01-Hard / E02-Audit / E03-Span

- Hard/confusable anchors are now in `configs/anchor_hard_smoke.yaml`.
- Span-specific patching is implemented in `scripts/run_span_patch_smoke.py` and summarized in `reports/E03_span_patch_hard_summary.md`.
- Generated trace triage is implemented in `scripts/build_trace_process_audit_sheet.py`; outputs are in `data/processed/trace_process_audit_sheet_v2b_v2c.*`.
- The "final verifier token only" confound is reduced but not eliminated: trace/support-error spans have clean effects, but verdict-position patching remains strongest in most models.
- Next correction: move residual patching to manually labeled real ACPI pairs, then decompose the strongest residual sites into attention Q/K/V paths and MLP outputs.

## Remote P0 Status

- Download session: `p02_download_remote_p0`.
- Log: `logs/p02_download_remote_p0.log`.
- First wave: `qwen35_9b`, `ministral3_8b_reasoning`, `phi4_mini_reasoning`, `glm46v_flash`.
- Gemma 4 tokenizer loading failed under current Transformers with `AttributeError("'list' object has no attribute 'keys'")`; handle later with AutoProcessor/newer Transformers or downgrade to tokenizer-only external baseline.
