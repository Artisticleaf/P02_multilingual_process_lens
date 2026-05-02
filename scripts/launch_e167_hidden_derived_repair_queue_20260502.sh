#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:180GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

mkdir -p logs results/E167_hidden_derived_repair
STATUS=logs/e167_hidden_derived_repair_status_20260502.jsonl
: > "$STATUS"

MAX_NEW_TOKENS=8192
VARIANTS=(
  baseline_regenerate
  prefix_continue
  hidden_generic_warning
  hidden_localized_warning
  random_matched_warning
  oracle_manual_span
)

ts() { date --iso-8601=seconds; }
record() {
  printf '{"status":"%s","step":"%s","ts":"%s"}\n' "$1" "$2" "$(ts)" >> "$STATUS"
}

run_logged() {
  local step="$1"; shift
  local logfile="$1"; shift
  record start "$step"
  echo "===== START $step $(ts) =====" | tee "$logfile"
  "$@" 2>&1 | tee -a "$logfile"
  echo "===== END $step $(ts) =====" | tee -a "$logfile"
  record done "$step"
}

record start e167_static_audit
python -m py_compile \
  scripts/build_e167_hidden_derived_repair_cases.py \
  scripts/audit_e167_hidden_derived_repair_cases.py \
  scripts/smoke_e167_hidden_derived_prompt.py \
  scripts/run_e167_hidden_derived_repair.py
python scripts/build_e167_hidden_derived_repair_cases.py 2>&1 | tee logs/e167_build_cases_20260502.log
python scripts/audit_e167_hidden_derived_repair_cases.py 2>&1 | tee logs/e167_case_static_audit_20260502.log
python scripts/smoke_e167_hidden_derived_prompt.py 2>&1 | tee logs/e167_prompt_smoke_20260502.log
record done e167_static_audit

run_logged e167_repair_qwen35_27b_smoke logs/e167_repair_qwen35_27b_smoke_20260502.log \
  python scripts/run_e167_hidden_derived_repair.py \
    --model-key qwen35_27b \
    --variants "${VARIANTS[@]}" \
    --hidden-policies high_precision \
    --max-cases 1 \
    --max-new-tokens "$MAX_NEW_TOKENS" \
    --batch-size 1 \
    --temperature 0.0 \
    --checkpoint-jsonl logs/e167_repair_qwen35_27b_smoke_checkpoint_20260502.jsonl \
    --local-files-only \
    --tag smoke_20260502

run_model() {
  local model="$1"
  run_logged "e167_repair_${model}" "logs/e167_repair_${model}_20260502.log" \
    python scripts/run_e167_hidden_derived_repair.py \
      --model-key "$model" \
      --variants "${VARIANTS[@]}" \
      --hidden-policies high_precision \
      --max-new-tokens "$MAX_NEW_TOKENS" \
      --batch-size 1 \
      --temperature 0.0 \
      --checkpoint-jsonl "logs/e167_repair_${model}_checkpoint_20260502.jsonl" \
      --local-files-only \
      --tag high_precision_20260502
}

run_model qwen35_27b
run_model gemma4_31b_it
run_model gemma4_26b_a4b_it

record all_done all
