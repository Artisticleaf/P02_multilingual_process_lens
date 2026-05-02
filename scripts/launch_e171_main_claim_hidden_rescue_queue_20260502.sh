#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:180GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

mkdir -p logs results/E171_main_claim_hidden_rescue
STATUS=logs/e171_main_claim_hidden_rescue_status_20260502.jsonl
: > "$STATUS"

MAX_NEW_TOKENS=16384
MAX_MODEL_LEN=8192
VARIANTS=(
  baseline_regenerate
  prefix_continue
  hidden_generic_warning
  hidden_localized_warning
  random_matched_warning
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

record start e171_static_audit
python -m py_compile \
  scripts/build_e171_main_claim_task_bank.py \
  scripts/smoke_e171_main_claim_prompt.py \
  scripts/audit_e171_main_claim_pipeline.py \
  scripts/run_e171_baseline_nonthinking.py \
  scripts/run_e171_hidden_rescue_from_baseline.py \
  scripts/summarize_e171_main_claim_hidden_rescue.py
python scripts/build_e171_main_claim_task_bank.py 2>&1 | tee logs/e171_build_task_bank_20260502.log
python scripts/smoke_e171_main_claim_prompt.py 2>&1 | tee logs/e171_prompt_smoke_20260502.log
python scripts/audit_e171_main_claim_pipeline.py 2>&1 | tee logs/e171_pipeline_audit_20260502.log
record done e171_static_audit

run_logged e171_baseline_qwen35_27b_smoke logs/e171_baseline_qwen35_27b_smoke_20260502.log \
  python scripts/run_e171_baseline_nonthinking.py \
    --model-key qwen35_27b \
    --max-tasks 1 \
    --max-new-tokens 4096 \
    --batch-size 1 \
    --temperature 0.0 \
    --checkpoint-jsonl logs/e171_baseline_qwen35_27b_smoke_checkpoint_20260502.jsonl \
    --local-files-only \
    --tag smoke_20260502

run_model() {
  local model="$1"
  local baseline_json="results/E171_main_claim_hidden_rescue/${model}_e171_baseline_nonthinking_max16384_20260502.json"
  run_logged "e171_baseline_${model}" "logs/e171_baseline_${model}_20260502.log" \
    python scripts/run_e171_baseline_nonthinking.py \
      --model-key "$model" \
      --max-new-tokens "$MAX_NEW_TOKENS" \
      --batch-size 1 \
      --temperature 0.0 \
      --checkpoint-jsonl "logs/e171_baseline_${model}_checkpoint_20260502.jsonl" \
      --local-files-only \
      --tag max16384_20260502

  if [[ "$model" == "qwen35_27b" ]]; then
    run_logged e171_rescue_qwen35_27b_smoke logs/e171_rescue_qwen35_27b_smoke_20260502.log \
      python scripts/run_e171_hidden_rescue_from_baseline.py \
        --model-key qwen35_27b \
        --baseline-json "$baseline_json" \
        --variants "${VARIANTS[@]}" \
        --max-cases 1 \
        --max-new-tokens "$MAX_NEW_TOKENS" \
        --max-model-len "$MAX_MODEL_LEN" \
        --batch-size 1 \
        --temperature 0.0 \
        --checkpoint-jsonl logs/e171_rescue_qwen35_27b_smoke_checkpoint_20260502.jsonl \
        --local-files-only \
        --tag smoke_20260502
  fi

  run_logged "e171_rescue_${model}" "logs/e171_rescue_${model}_20260502.log" \
    python scripts/run_e171_hidden_rescue_from_baseline.py \
      --model-key "$model" \
      --baseline-json "$baseline_json" \
      --variants "${VARIANTS[@]}" \
      --max-new-tokens "$MAX_NEW_TOKENS" \
      --max-model-len "$MAX_MODEL_LEN" \
      --batch-size 1 \
      --temperature 0.0 \
      --checkpoint-jsonl "logs/e171_rescue_${model}_checkpoint_20260502.jsonl" \
      --local-files-only \
      --tag max16384_20260502
}

run_model qwen35_27b
run_model gemma4_31b_it
run_model gemma4_26b_a4b_it

run_logged e171_stage_analysis logs/e171_stage_analysis_20260502.log \
  python scripts/summarize_e171_main_claim_hidden_rescue.py

record all_done all
