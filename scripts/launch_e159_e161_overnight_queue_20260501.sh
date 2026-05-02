#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

STATUS=logs/e159_e161_overnight_status_20260501.jsonl
: > "$STATUS"

ts() { date --iso-8601=seconds; }
record() {
  printf '{"status":"%s","step":"%s","ts":"%s"}\n' "$1" "$2" "$(ts)" >> "$STATUS"
}

record start e159_build_bank
python scripts/build_e159_answer_preserving_task_bank.py 2>&1 | tee logs/e159_build_bank_20260501.log
record done e159_build_bank

record start e159_task_bank_audit
python scripts/audit_e159_task_bank.py 2>&1 | tee logs/e159_task_bank_audit_20260501.log
record done e159_task_bank_audit

record start e159_e161_scaffold_smoke
python scripts/smoke_e159_e161_scaffold.py 2>&1 | tee logs/e159_e161_scaffold_smoke_20260501.log
record done e159_e161_scaffold_smoke

run_e159_model() {
  local model="$1"
  record start "e159_nonthinking_generation_${model}"
  python scripts/run_e159_e160_answer_preserving_generation.py \
    --model-key "$model" \
    --experiment E159_answer_preserving_generation \
    --thinking false \
    --out-dir results/E159_answer_preserving_difficult_generation \
    --variants solve_neutral solve_terse solve_self_check \
    --k 1 \
    --max-new-tokens 4096 \
    --batch-size 2 \
    --temperature 0.7 \
    --top-p 0.95 \
    --top-k 50 \
    --checkpoint-jsonl "logs/e159_generation_${model}_k1_checkpoint_20260501.jsonl" \
    2>&1 | tee "logs/e159_generation_${model}_k1_20260501.log"
  record done "e159_nonthinking_generation_${model}"
}

run_e160_model() {
  local model="$1"
  record start "e160_thinking_generation_${model}"
  python scripts/run_e159_e160_answer_preserving_generation.py \
    --model-key "$model" \
    --experiment E160_thinking_answer_preserving_generation \
    --thinking true \
    --out-dir results/E160_thinking_answer_preserving_generation \
    --variants solve_neutral solve_terse solve_self_check \
    --k 1 \
    --max-new-tokens 8192 \
    --batch-size 1 \
    --temperature 0.7 \
    --top-p 0.95 \
    --top-k 50 \
    --checkpoint-jsonl "logs/e160_thinking_generation_${model}_k1_checkpoint_20260501.jsonl" \
    2>&1 | tee "logs/e160_thinking_generation_${model}_k1_20260501.log"
  record done "e160_thinking_generation_${model}"
}

run_e161_model() {
  local model="$1"
  record start "e161_error_repair_${model}"
  python scripts/run_e161_answer_preserving_error_repair.py \
    --model-key "$model" \
    --out-dir results/E161_answer_preserving_error_repair \
    --variants blind_global blind_localize_only oracle_span_repair \
    --max-new-tokens 768 \
    --batch-size 1 \
    --temperature 0.0 \
    --checkpoint-jsonl "logs/e161_error_repair_${model}_checkpoint_20260501.jsonl" \
    2>&1 | tee "logs/e161_error_repair_${model}_20260501.log"
  record done "e161_error_repair_${model}"
}

# Natural non-thinking induction across core P0.
run_e159_model qwen35_27b
run_e159_model gemma4_31b_it
run_e159_model gemma4_26b_a4b_it

# Thinking COT contrast first on dense models; MoE thinking is deferred unless
# explicitly needed because it is more expensive and architecture-specific.
run_e160_model qwen35_27b
run_e160_model gemma4_31b_it

# Controlled error finding / oracle-span repair across core P0.
run_e161_model qwen35_27b
run_e161_model gemma4_31b_it
run_e161_model gemma4_26b_a4b_it

record all_done all
