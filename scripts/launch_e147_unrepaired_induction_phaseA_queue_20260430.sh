#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

STATUS=logs/e147_unrepaired_induction_phaseA_status_20260430.jsonl
: > "$STATUS"

ts() {
  date --iso-8601=seconds
}

record() {
  local status="$1"
  local step="$2"
  printf '{"status":"%s","step":"%s","ts":"%s"}\n' "$status" "$step" "$(ts)" >> "$STATUS"
}

record start e147_build_task_bank
python scripts/build_e147_unrepaired_acpi_induction_tasks.py 2>&1 | tee logs/e147_build_task_bank_20260430.log
record done e147_build_task_bank

record start e147_scaffold_smoke
python scripts/smoke_e147_e152_nonthinking_scaffold.py 2>&1 | tee logs/e147_e152_scaffold_smoke_20260430.log
record done e147_scaffold_smoke

run_model() {
  local model="$1"
  record start "e147_${model}"
  python scripts/run_e147_unrepaired_acpi_induction_generation.py \
    --model-key "$model" \
    --out-dir results/E147_unrepaired_acpi_induction \
    --variants neutral answer_first_no_gold terse_solution self_check_short \
    --k 1 \
    --max-new-tokens 4096 \
    --batch-size 2 \
    --temperature 0.7 \
    --top-p 0.95 \
    --top-k 50 \
    --thinking false \
    --checkpoint-jsonl "logs/e147_${model}_phaseA_k1_checkpoint_20260430.jsonl" \
    2>&1 | tee "logs/e147_${model}_phaseA_k1_20260430.log"
  record done "e147_${model}"
}

run_model qwen35_27b
run_model gemma4_31b_it
run_model gemma4_26b_a4b_it

record start e147_build_audit_sheet
python scripts/build_e147_final_correct_audit_sheet.py 2>&1 | tee logs/e147_build_audit_sheet_20260430.log
record done e147_build_audit_sheet

record all_done all

