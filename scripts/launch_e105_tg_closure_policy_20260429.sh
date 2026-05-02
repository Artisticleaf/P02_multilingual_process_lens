#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

mkdir -p logs results/E105_tg_closure_policy reports
STATUS=logs/e105_tg_closure_policy_status_20260429.jsonl
: > "$STATUS"

log_status() {
  local step="$1"
  local status="$2"
  python3 - "$STATUS" "$step" "$status" <<'PY'
import json
import sys
from datetime import datetime

path, step, status = sys.argv[1:4]
with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps({"step": step, "status": status, "ts": datetime.now().astimezone().isoformat(timespec="seconds")}, ensure_ascii=False, sort_keys=True) + "\n")
PY
}

run_step() {
  local step="$1"
  shift
  log_status "$step" start
  "$@"
  log_status "$step" done
}

python3 -m py_compile scripts/run_e105_tg_closure_policy.py scripts/summarize_e105_tg_closure_policy.py

run_step e105_qwen35_tg_closure_k1 \
  python3 scripts/run_e105_tg_closure_policy.py \
    --model-key qwen35_27b \
    --task-ids aime25_base_divisor_p1 aime25_integer_pairs_quad_p4 aime25_trapezoid_incircle_p6 \
    --policies free_think_8192 final_contract_8192 budgeted_final_4096 \
    --k 1 \
    --batch-size 2 \
    --max-time 900 \
    --out-dir results/E105_tg_closure_policy \
    --checkpoint-jsonl logs/e105_qwen35_tg_closure_k1_checkpoint_20260429.jsonl \
    --local-files-only \
    --seed 20260429

run_step e105_summary \
  python3 scripts/summarize_e105_tg_closure_policy.py

log_status all all_done
