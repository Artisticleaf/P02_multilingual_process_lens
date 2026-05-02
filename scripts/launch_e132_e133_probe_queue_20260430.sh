#!/usr/bin/env bash
set -u

ROOT="/home/Awei/P02_multilingual_process_lens"
STATUS="$ROOT/logs/e132_e133_probe_status_20260430.jsonl"
QUEUE_LOG="$ROOT/logs/e132_e133_probe_queue_20260430.log"
OUT_DIR="$ROOT/results/E132_E133_suspicious_confidence_probe"

mkdir -p "$ROOT/logs" "$OUT_DIR"

source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH="$ROOT/.deps/hf5:$ROOT/src"
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

record_status() {
  local model="$1"
  local phase="$2"
  local code="$3"
  local out="$4"
  python - "$STATUS" "$model" "$phase" "$code" "$out" <<'PY'
import json, sys
from datetime import datetime
path, model, phase, code, out = sys.argv[1:]
with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model_key": model,
        "phase": phase,
        "exit_code": int(code),
        "out": out,
    }, ensure_ascii=False) + "\n")
PY
}

run_model() {
  local model="$1"
  local log="$ROOT/logs/e132_e133_${model}_rows12_20260430.log"
  record_status "$model" "start" 0 "$log"
  set +e
  python "$ROOT/scripts/run_e132_e133_suspicious_confidence_probe.py" \
    --model-key "$model" \
    --rows-per-variant 12 \
    --local-files-only \
    --out-dir "$OUT_DIR" \
    > "$log" 2>&1
  local code=$?
  set -e
  record_status "$model" "done" "$code" "$log"
  return "$code"
}

: > "$STATUS"
: > "$QUEUE_LOG"
record_status "__queue__" "start" 0 "$STATUS"

FAIL=0
for model in qwen35_27b gemma4_31b_it gemma4_26b_a4b_it; do
  if ! run_model "$model"; then
    FAIL=1
  fi
done

if [[ "$FAIL" -eq 0 ]]; then
  record_status "__queue__" "all_done" 0 "$STATUS"
else
  record_status "__queue__" "finished_with_failures" "$FAIL" "$STATUS"
fi

exit "$FAIL"
