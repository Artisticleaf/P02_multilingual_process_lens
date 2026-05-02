#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:180GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

mkdir -p logs results/E170_thinking_only_hardened_tasks
STATUS=logs/e170_thinking_only_status_20260502.jsonl
: > "$STATUS"

MAX_NEW_TOKENS=32768

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

record start e170_static_audit
python -m py_compile \
  scripts/run_e170_thinking_only_hardened_tasks.py \
  scripts/smoke_e170_thinking_only_prompt.py \
  scripts/summarize_e170_thinking_only.py
python scripts/smoke_e170_thinking_only_prompt.py 2>&1 | tee logs/e170_prompt_smoke_20260502.log
record done e170_static_audit

run_model() {
  local model="$1"
  run_logged "e170_thinking_only_${model}" "logs/e170_thinking_only_${model}_20260502.log" \
    python scripts/run_e170_thinking_only_hardened_tasks.py \
      --model-key "$model" \
      --max-new-tokens "$MAX_NEW_TOKENS" \
      --batch-size 1 \
      --temperature 0.0 \
      --checkpoint-jsonl "logs/e170_thinking_only_${model}_checkpoint_20260502.jsonl" \
      --local-files-only \
      --tag max32768_20260502
}

run_model qwen35_27b
run_model gemma4_31b_it
run_model gemma4_26b_a4b_it

run_logged e170_stage_analysis logs/e170_stage_analysis_20260502.log \
  python scripts/summarize_e170_thinking_only.py

record all_done all
