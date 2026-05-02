#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

mkdir -p logs results/E105_tg_closure_policy reports
STATUS=logs/e105_reviewer_stress_status_20260429.jsonl
: > "$STATUS"

log_status() {
  local step="$1"
  local status="$2"
  local note="${3:-}"
  python3 - "$STATUS" "$step" "$status" "$note" <<'PY'
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
  shift
  log_status "$step" start
  "$@"
  log_status "$step" done
}

run_step_allow_fail() {
  local step="$1"
  shift
  log_status "$step" start
  set +e
  "$@"
  local code=$?
  set -e
  if [[ "$code" -eq 0 ]]; then
    log_status "$step" done
  else
    log_status "$step" failed "exit_code=$code"
  fi
  return 0
}

python3 -m py_compile scripts/run_e105_tg_closure_policy.py scripts/summarize_e105_tg_closure_policy.py

# Reviewer stress canary: no wall-time cap, batch_size=1.
run_step e105r_qwen35_canary_16k_no_timecap \
  python3 scripts/run_e105_tg_closure_policy.py \
    --model-key qwen35_27b \
    --task-ids aime25_base_divisor_p1 \
    --policies free_think_16384 final_contract_16384 budgeted_final_16384 \
    --k 1 \
    --batch-size 1 \
    --max-time 0 \
    --out-dir results/E105_tg_closure_policy \
    --checkpoint-jsonl logs/e105r_qwen35_canary16k_checkpoint_20260429.jsonl \
    --local-files-only \
    --seed 20260429

# 32k is a hardware stress test. It may fail under the current 4x32GB setup.
run_step_allow_fail e105r_qwen35_canary_32k_no_timecap \
  python3 scripts/run_e105_tg_closure_policy.py \
    --model-key qwen35_27b \
    --task-ids aime25_base_divisor_p1 \
    --policies final_contract_32768 \
    --k 1 \
    --batch-size 1 \
    --max-time 0 \
    --out-dir results/E105_tg_closure_policy \
    --checkpoint-jsonl logs/e105r_qwen35_canary32k_checkpoint_20260429.jsonl \
    --local-files-only \
    --seed 20260430

log_status all all_done
