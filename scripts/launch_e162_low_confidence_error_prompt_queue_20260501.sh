#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

STATUS=logs/e162_low_confidence_error_prompt_status_20260501.jsonl
: > "$STATUS"

ts() { date --iso-8601=seconds; }
record() {
  printf '{"status":"%s","step":"%s","ts":"%s"}\n' "$1" "$2" "$(ts)" >> "$STATUS"
}

record start e162_build_case_bank
python scripts/build_e162_low_confidence_error_prompt_cases.py 2>&1 | tee logs/e162_build_case_bank_20260501.log
record done e162_build_case_bank

record start e162_static_audit
python scripts/audit_e162_case_bank_and_prompts.py 2>&1 | tee logs/e162_static_audit_20260501.log
record done e162_static_audit

run_model() {
  local model="$1"
  record start "e162_repair_${model}"
  python scripts/run_e162_low_confidence_error_prompt_repair.py \
    --model-key "$model" \
    --variants baseline_regenerate prefix_continue generic_error_prompt localized_error_prompt oracle_error_prompt random_location_prompt \
    --max-new-tokens 1024 \
    --batch-size 1 \
    --temperature 0.0 \
    --checkpoint-jsonl "logs/e162_repair_${model}_checkpoint_20260501.jsonl" \
    --tag full_20260501 \
    2>&1 | tee "logs/e162_repair_${model}_20260501.log"
  record done "e162_repair_${model}"
}

run_model qwen35_27b
run_model gemma4_31b_it
run_model gemma4_26b_a4b_it

record all_done all
