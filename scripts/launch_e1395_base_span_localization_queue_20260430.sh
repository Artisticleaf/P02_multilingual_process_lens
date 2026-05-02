#!/usr/bin/env bash
set -u

ROOT="/home/Awei/P02_multilingual_process_lens"
STATUS="$ROOT/logs/e1395_base_span_localization_status_20260430.jsonl"
LOG="$ROOT/logs/e1395_base_span_localization_queue_20260430.log"

mkdir -p "$ROOT/logs" "$ROOT/results/E1395_base_span_localization"
: > "$STATUS"
: > "$LOG"

cd "$ROOT" || exit 1
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH="$ROOT/.deps/hf5:$ROOT/src"
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

stamp() {
  date '+%Y-%m-%dT%H:%M:%S'
}

write_status() {
  local model_key="$1"
  local phase="$2"
  local exit_code="$3"
  local out_path="$4"
  python3 - "$STATUS" "$model_key" "$phase" "$exit_code" "$out_path" <<'PY'
import json, sys
from datetime import datetime
path, model, phase, code, out = sys.argv[1:6]
rec = {
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "model_key": model,
    "phase": phase,
    "exit_code": int(code),
    "out": out,
}
with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
PY
}

run_one() {
  local model_key="$1"
  local out_json="$ROOT/results/E1395_base_span_localization/${model_key}_e1395_base_span_localization.json"
  write_status "$model_key" "start" 0 "$out_json"
  {
    echo "===== $(stamp) START $model_key ====="
    python3 scripts/run_e1395_base_span_localization.py \
      --model-key "$model_key" \
      --out-dir "$ROOT/results/E1395_base_span_localization" \
      --local-files-only
    code=$?
    echo "===== $(stamp) END $model_key exit=$code ====="
    write_status "$model_key" "$(if [ "$code" -eq 0 ]; then echo done; else echo failed; fi)" "$code" "$out_json"
  } >> "$LOG" 2>&1
  # Continue to the next model even if this one failed; status keeps the audit trail.
  return 0
}

write_status "__queue__" "start" 0 "$STATUS"
run_one qwen35_27b
run_one gemma4_31b_it
run_one gemma4_26b_a4b_it
write_status "__queue__" "all_done" 0 "$STATUS"
