#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:180GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

mkdir -p logs results/E166_hardened_hidden_monitor_replay
STATUS=logs/e166_hidden_monitor_replay_status_20260502.jsonl
: > "$STATUS"

ts() { date --iso-8601=seconds; }
record() {
  printf '{"status":"%s","step":"%s","ts":"%s"}\n' "$1" "$2" "$(ts)" >> "$STATUS"
}

run_step() {
  local name="$1"; shift
  local logfile="logs/${name}_20260502.log"
  record start "$name"
  echo "===== START $name $(ts) =====" | tee "$logfile"
  "$@" 2>&1 | tee -a "$logfile"
  echo "===== END $name $(ts) =====" | tee -a "$logfile"
  record done "$name"
}

record start static_audit
python -m py_compile \
  scripts/build_e166_hardened_monitor_prefix_bank.py \
  scripts/audit_e166_hardened_monitor_prefix_bank.py \
  scripts/run_e166_hardened_hidden_monitor_replay.py \
  scripts/summarize_e166_e169_hidden_monitor_kg.py
python scripts/build_e166_hardened_monitor_prefix_bank.py 2>&1 | tee logs/e166_build_prefix_bank_20260502.log
python scripts/audit_e166_hardened_monitor_prefix_bank.py 2>&1 | tee logs/e166_static_audit_20260502.log
record done static_audit

COMMON_ARGS=(
  --prompt-mode generation_prefill
  --prompt-format official_if_chat
  --device auto
  --dtype bfloat16
  --local-files-only
  --tag full_20260502
)

run_step e166_qwen35_27b_hidden_replay \
  python scripts/run_e166_hardened_hidden_monitor_replay.py \
    --model-key qwen35_27b \
    "${COMMON_ARGS[@]}"

run_step e166_gemma4_31b_it_hidden_replay \
  python scripts/run_e166_hardened_hidden_monitor_replay.py \
    --model-key gemma4_31b_it \
    "${COMMON_ARGS[@]}"

run_step e166_gemma4_26b_a4b_it_hidden_replay \
  python scripts/run_e166_hardened_hidden_monitor_replay.py \
    --model-key gemma4_26b_a4b_it \
    "${COMMON_ARGS[@]}"

run_step e166_e169_kg_summary \
  python scripts/summarize_e166_e169_hidden_monitor_kg.py

record all_done all
