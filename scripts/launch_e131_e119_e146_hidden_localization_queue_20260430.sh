#!/usr/bin/env bash
set -u

ROOT="/home/Awei/P02_multilingual_process_lens"
cd "$ROOT"

source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH="$ROOT/.deps/hf5:$ROOT/src"
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

STATUS_LOG="$ROOT/logs/e131_e119_e146_hidden_localization_status_20260430.jsonl"
QUEUE_LOG="$ROOT/logs/e131_e119_e146_hidden_localization_queue_20260430.log"
mkdir -p "$ROOT/logs"

: > "$QUEUE_LOG"
touch "$STATUS_LOG"

record_status() {
  local model="$1"
  local phase="$2"
  local exit_code="$3"
  local out_json="$4"
  python - <<PY >> "$STATUS_LOG"
import json
from datetime import datetime
print(json.dumps({
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "model_key": "$model",
    "phase": "$phase",
    "exit_code": int("$exit_code"),
    "out_json": "$out_json",
}, ensure_ascii=False))
PY
}

run_model() {
  local model="$1"
  local best_layer="$2"
  local out_json="$ROOT/results/E131_e119_e146_hidden_localization/${model}_e131_hidden_localization_mixed_chat.json"
  echo "[$(date '+%F %T')] START $model" | tee -a "$QUEUE_LOG"
  python scripts/run_e131_e119_e146_hidden_localization.py \
    --model-key "$model" \
    --target-mode mixed \
    --include-valid-matched \
    --valid-per-task-prompt 1 \
    --best-layer "$best_layer" \
    --out-dir "$ROOT/results/E131_e119_e146_hidden_localization" \
    --local-files-only \
    >> "$QUEUE_LOG" 2>&1
  local ec=$?
  record_status "$model" "done" "$ec" "$out_json"
  echo "[$(date '+%F %T')] END $model exit=$ec" | tee -a "$QUEUE_LOG"
  return 0
}

record_status "__queue__" "start" 0 "$STATUS_LOG"

run_model "gemma4_26b_a4b_it" 17
run_model "gemma4_31b_it" 34
run_model "qwen35_27b" 34

record_status "__queue__" "all_done" 0 "$STATUS_LOG"
echo "[$(date '+%F %T')] ALL_DONE" | tee -a "$QUEUE_LOG"
