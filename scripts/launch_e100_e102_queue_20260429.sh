#!/usr/bin/env bash
set -euo pipefail
cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

mkdir -p logs results/E100_batch_invariance_audit results/E101_batch_generation_sensitivity results/E102_thinking_nonthinking_hidden_contrast reports
STATUS=logs/e100_e102_status_20260429.jsonl
: > "$STATUS"

run_step() {
  local name="$1"; shift
  local logfile="logs/${name}_20260429.log"
  echo "{\"step\":\"$name\",\"status\":\"start\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
  echo "===== START $name $(date -Is) =====" | tee "$logfile"
  "$@" 2>&1 | tee -a "$logfile"
  echo "===== END $name $(date -Is) =====" | tee -a "$logfile"
  echo "{\"step\":\"$name\",\"status\":\"done\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
}

python -m py_compile \
  scripts/run_e100_batch_invariance_audit.py \
  scripts/run_e101_batch_generation_sensitivity.py \
  scripts/run_e102_thinking_nonthinking_hidden_contrast.py \
  scripts/summarize_e100_e102.py

run_step "e100_qwen35_batch_invariance" \
  python scripts/run_e100_batch_invariance_audit.py \
    --model-key qwen35_27b \
    --batch-sizes 1 2 4 \
    --max-per-source 6 \
    --best-layer 34 \
    --layer-window 1 \
    --max-model-len 4096 \
    --device auto \
    --local-files-only

run_step "e102_qwen35_thinking_nonthinking_hidden_contrast" \
  python scripts/run_e102_thinking_nonthinking_hidden_contrast.py \
    --model-key qwen35_27b \
    --max-per-source 6 \
    --best-layer 34 \
    --layer-window 1 \
    --max-model-len 8192 \
    --device auto \
    --local-files-only

run_step "e101_qwen35_batch_generation_sensitivity" \
  python scripts/run_e101_batch_generation_sensitivity.py \
    --model-key qwen35_27b \
    --batch-sizes 1 2 4 \
    --max-tasks 2 \
    --max-new-tokens 512 \
    --temperature 1.0 \
    --top-p 0.95 \
    --top-k 20 \
    --device auto \
    --local-files-only

run_step "e100_e102_summary" \
  python scripts/summarize_e100_e102.py

echo "{\"status\":\"all_done\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
