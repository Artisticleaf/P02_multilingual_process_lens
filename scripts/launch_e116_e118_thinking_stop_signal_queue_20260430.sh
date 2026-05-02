#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

STATUS=logs/e116_e118_thinking_stop_signal_status_20260430.jsonl
: > "$STATUS"

ts() {
  date --iso-8601=seconds
}

record() {
  local status="$1"
  local step="$2"
  printf '{"status":"%s","step":"%s","ts":"%s"}\n' "$status" "$step" "$(ts)" >> "$STATUS"
}

record start e116_e118_qwen35_27b
python scripts/run_e116_e118_thinking_stop_signal_suite.py \
  --model-key qwen35_27b \
  --max-e105-rows 8 \
  --max-e103-tg 6 \
  --max-model-len 8192 \
  --out-dir results/E116_E118_thinking_stop_signal
record done e116_e118_qwen35_27b

record all_done all
