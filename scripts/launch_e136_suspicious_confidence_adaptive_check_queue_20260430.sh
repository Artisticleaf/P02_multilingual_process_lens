#!/usr/bin/env bash
set -u

ROOT="/home/Awei/P02_multilingual_process_lens"
STATUS="$ROOT/logs/e136_suspicious_confidence_adaptive_check_status_20260430.jsonl"
LOG="$ROOT/logs/e136_suspicious_confidence_adaptive_check_queue_20260430.log"

cd "$ROOT" || exit 1
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH="$ROOT/.deps/hf5:$ROOT/src"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0,1,2,3}"
export MPLENS_MAX_MEMORY="${MPLENS_MAX_MEMORY:-0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB}"

mkdir -p "$ROOT/logs"
: > "$STATUS"
: > "$LOG"

stamp() {
  date '+%Y-%m-%dT%H:%M:%S'
}

record() {
  local model="$1"
  local phase="$2"
  local code="$3"
  local out="$4"
  printf '{"timestamp":"%s","model_key":"%s","phase":"%s","exit_code":%s,"out":"%s"}\n' "$(stamp)" "$model" "$phase" "$code" "$out" >> "$STATUS"
}

run_one() {
  local model="$1"
  local out_json="$ROOT/results/E136_suspicious_confidence_adaptive_check/${model}_e136_suspicious_confidence_adaptive_check_rowspervariant12.json"
  record "$model" "start" 0 "$out_json"
  {
    echo "===== $(stamp) START $model ====="
    python scripts/run_e136_suspicious_confidence_adaptive_check.py \
      --model-key "$model" \
      --max-model-len 8192 \
      --local-files-only
    code=$?
    echo "===== $(stamp) END $model exit=$code ====="
    test "$code" -eq 0
  } >> "$LOG" 2>&1
  code=$?
  if [[ "$code" -eq 0 ]]; then
    record "$model" "done" 0 "$out_json"
  else
    record "$model" "failed" "$code" "$out_json"
  fi
  return 0
}

record "__queue__" "start" 0 "$STATUS"
run_one "qwen35_27b"
run_one "gemma4_31b_it"
run_one "gemma4_26b_a4b_it"
record "__queue__" "all_done" 0 "$STATUS"
