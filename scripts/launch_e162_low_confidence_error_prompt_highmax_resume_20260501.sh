#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

STATUS=logs/e162_low_confidence_error_prompt_highmax_status_20260501.jsonl
: > "$STATUS"

MAX_NEW_TOKENS=8192
VARIANTS=(baseline_regenerate prefix_continue generic_error_prompt localized_error_prompt oracle_error_prompt random_location_prompt)

ts() { date --iso-8601=seconds; }
record() {
  printf '{"status":"%s","step":"%s","ts":"%s"}\n' "$1" "$2" "$(ts)" >> "$STATUS"
}

resume_source_for_model() {
  local model="$1"
  local high="logs/e162_repair_${model}_highmax_checkpoint_20260501.jsonl"
  local old="logs/e162_repair_${model}_checkpoint_20260501.jsonl"
  if [[ -s "$high" ]]; then
    printf '%s\n' "$high"
  elif [[ -s "$old" ]]; then
    printf '%s\n' "$old"
  else
    printf '\n'
  fi
}

record start e162_highmax_static_audit
python scripts/build_e162_low_confidence_error_prompt_cases.py 2>&1 | tee logs/e162_highmax_build_case_bank_20260501.log
python scripts/audit_e162_case_bank_and_prompts.py 2>&1 | tee logs/e162_highmax_static_audit_20260501.log
record done e162_highmax_static_audit

run_model() {
  local model="$1"
  local resume_source
  resume_source="$(resume_source_for_model "$model")"
  local checkpoint="logs/e162_repair_${model}_highmax_checkpoint_20260501.jsonl"
  local logfile="logs/e162_repair_${model}_highmax_20260501.log"
  local step="e162_highmax_repair_${model}"

  record start "$step"
  cmd=(
    python scripts/run_e162_low_confidence_error_prompt_repair.py
    --model-key "$model"
    --variants "${VARIANTS[@]}"
    --max-new-tokens "$MAX_NEW_TOKENS"
    --batch-size 1
    --temperature 0.0
    --checkpoint-jsonl "$checkpoint"
    --tag highmax_20260501
  )
  if [[ -n "$resume_source" ]]; then
    cmd+=(--resume-from-checkpoint "$resume_source")
  fi
  printf 'Running %s with max_new_tokens=%s resume_source=%s\n' "$model" "$MAX_NEW_TOKENS" "${resume_source:-NONE}" | tee "$logfile"
  "${cmd[@]}" 2>&1 | tee -a "$logfile"
  record done "$step"
}

run_model qwen35_27b
run_model gemma4_31b_it
run_model gemma4_26b_a4b_it

record all_done all
