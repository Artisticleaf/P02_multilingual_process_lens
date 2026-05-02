#!/usr/bin/env bash
set -euo pipefail

PROJECT=/home/Awei/P02_multilingual_process_lens
LOG_DIR="$PROJECT/logs"
STATUS="$LOG_DIR/e60_objective_ladder_status_20260428.jsonl"
mkdir -p "$LOG_DIR" "$PROJECT/results/E60_objective_ladder"
cd "$PROJECT"

source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH="$PROJECT/.deps/hf5:$PROJECT/src"
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

run_one() {
  local model_key="$1"
  local log="$LOG_DIR/e60_${model_key}_hf4_20260428.log"
  echo "{\"event\":\"start\",\"model_key\":\"$model_key\",\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
  python scripts/run_e60_objective_ladder.py \
    --model-key "$model_key" \
    --prompt-format official_if_chat \
    --device auto \
    --dtype bfloat16 \
    --max-model-len 6144 \
    --local-files-only \
    2>&1 | tee "$log"
  local rc=${PIPESTATUS[0]}
  echo "{\"event\":\"done\",\"model_key\":\"$model_key\",\"rc\":$rc,\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
  return $rc
}

python -m py_compile scripts/run_e60_objective_ladder.py
run_one qwen35_27b
run_one gemma4_31b_it
run_one gemma4_26b_a4b_it

echo "{\"event\":\"all_done\",\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
