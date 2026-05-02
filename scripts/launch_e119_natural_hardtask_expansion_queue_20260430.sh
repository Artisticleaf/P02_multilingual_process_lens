#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

STATUS=logs/e119_natural_hardtask_expansion_status_20260430.jsonl
: > "$STATUS"

ts() {
  date --iso-8601=seconds
}

record() {
  local status="$1"
  local step="$2"
  printf '{"status":"%s","step":"%s","ts":"%s"}\n' "$status" "$step" "$(ts)" >> "$STATUS"
}

run_model() {
  local model="$1"
  record start "e119_${model}"
  python scripts/run_e49_hard_task_conditioning_official.py \
    --model-key "$model" \
    --out-dir results/E119_natural_hardtask_expansion \
    --variants neutral self_check answer_first_no_gold \
    --k 2 \
    --max-tasks 6 \
    --max-new-tokens 4096 \
    --batch-size 2 \
    --temperature 0.7 \
    --top-p 0.95 \
    --top-k 50 \
    --thinking false \
    --checkpoint-jsonl "logs/e119_${model}_ng_k2_checkpoint_20260430.jsonl" \
    2>&1 | tee "logs/e119_${model}_ng_k2_20260430.log"
  record done "e119_${model}"
}

run_model qwen35_27b
run_model gemma4_31b_it
run_model gemma4_26b_a4b_it
run_model glm47_flash_candidate

record start e119_build_audit_sheet
python scripts/build_e119_natural_hardtask_audit_sheet.py 2>&1 | tee logs/e119_build_audit_sheet_20260430.log
record done e119_build_audit_sheet

record all_done all
