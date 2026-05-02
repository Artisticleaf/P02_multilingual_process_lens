#!/usr/bin/env bash
set -u

ROOT="/home/Awei/P02_multilingual_process_lens"
STATUS="$ROOT/logs/e132_e134_nonthinking_probe_gemma_resume_status_20260430.jsonl"
LOG="$ROOT/logs/e132_e134_nonthinking_probe_gemma_resume_queue_20260430.log"

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
  local best="$2"
  local out_json="$ROOT/results/E132_E134_nonthinking_probe/${model}_e132_e134_nonthinking_probe_chat.json"
  record "$model" "start" 0 "$out_json"
  {
    echo "===== $(stamp) START $model ====="
    python scripts/run_e132_e134_nonthinking_probe.py \
      --model-key "$model" \
      --best-layer "$best" \
      --max-model-len 4096 \
      --layer-window 1 \
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
run_one "gemma4_31b_it" 34
run_one "gemma4_26b_a4b_it" 17
record "__queue__" "all_done" 0 "$STATUS"
