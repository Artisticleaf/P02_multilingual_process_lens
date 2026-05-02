#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

mkdir -p logs reports results/E106_E114_nonthinking_mechanism_suite
STATUS=logs/e106_e114_nonthinking_mechanism_status_20260430.jsonl
: > "$STATUS"

log_status() {
  local step="$1"
  local status="$2"
  local note="${3:-}"
  python - "$STATUS" "$step" "$status" "$note" <<'PY'
import json
import sys
from datetime import datetime

path, step, status, note = sys.argv[1:5]
row = {"step": step, "status": status, "ts": datetime.now().astimezone().isoformat(timespec="seconds")}
if note:
    row["note"] = note
with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
PY
}

run_step() {
  local step="$1"
  local logfile="$2"
  shift 2
  log_status "$step" start
  "$@" 2>&1 | tee "$logfile"
  log_status "$step" done
}

python -m py_compile scripts/run_e106_e114_nonthinking_mechanism_suite.py

run_step e106_e114_qwen35_27b logs/e106_e114_qwen35_27b_20260430.log \
  python scripts/run_e106_e114_nonthinking_mechanism_suite.py \
    --model-key qwen35_27b \
    --steering-max-items 16 \
    --prefix-max-rows 8 \
    --dilution-max-items 12 \
    --anchor-max-items 48 \
    --local-files-only

run_step e106_e114_gemma4_31b_it logs/e106_e114_gemma4_31b_it_20260430.log \
  python scripts/run_e106_e114_nonthinking_mechanism_suite.py \
    --model-key gemma4_31b_it \
    --steering-max-items 16 \
    --prefix-max-rows 8 \
    --dilution-max-items 12 \
    --anchor-max-items 48 \
    --local-files-only

run_step e106_e114_gemma4_26b_a4b_it logs/e106_e114_gemma4_26b_a4b_it_20260430.log \
  python scripts/run_e106_e114_nonthinking_mechanism_suite.py \
    --model-key gemma4_26b_a4b_it \
    --steering-max-items 16 \
    --prefix-max-rows 8 \
    --dilution-max-items 12 \
    --anchor-max-items 48 \
    --local-files-only

run_step e106_e114_glm47_flash_candidate logs/e106_e114_glm47_flash_candidate_20260430.log \
  python scripts/run_e106_e114_nonthinking_mechanism_suite.py \
    --model-key glm47_flash_candidate \
    --steering-max-items 16 \
    --prefix-max-rows 8 \
    --dilution-max-items 12 \
    --anchor-max-items 48 \
    --local-files-only

log_status all all_done
