#!/usr/bin/env bash
set -euo pipefail

PROJECT=/home/Awei/P02_multilingual_process_lens
LOG_DIR="$PROJECT/logs"
STATUS="$LOG_DIR/e61_language_error_grid_status_20260429.jsonl"
mkdir -p "$LOG_DIR" "$PROJECT/results/E61_language_error_grid"
cd "$PROJECT"

source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH="$PROJECT/.deps/hf5:$PROJECT/src"
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3
export TRANSFORMERS_OFFLINE=1

run_one() {
  local model_key="$1"
  local log="$LOG_DIR/e61_${model_key}_hf4_20260429.log"
  echo "{\"event\":\"start\",\"experiment\":\"E61\",\"model_key\":\"$model_key\",\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
  python scripts/run_e61_language_error_grid.py \
    --model-key "$model_key" \
    --prompt-format official_if_chat \
    --device auto \
    --dtype bfloat16 \
    --max-model-len 6144 \
    --local-files-only \
    2>&1 | tee "$log"
  local rc=${PIPESTATUS[0]}
  echo "{\"event\":\"done\",\"experiment\":\"E61\",\"model_key\":\"$model_key\",\"rc\":$rc,\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
  return $rc
}

python -m py_compile scripts/run_e61_language_error_grid.py scripts/audit_e61_language_error_grid.py
run_one qwen35_27b
run_one gemma4_31b_it
run_one gemma4_26b_a4b_it
python scripts/audit_e61_language_error_grid.py

echo "{\"event\":\"all_done\",\"experiment\":\"E61\",\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
