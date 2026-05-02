#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

mkdir -p logs results/E103_tg_ng_fair_hardtask results/E104_tg_ng_process_audit data/processed
STATUS=logs/e103_e104_qwen_status_20260429.jsonl
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

python3 -m py_compile scripts/run_e103_tg_ng_fair_hardtask.py scripts/build_e104_tg_ng_process_audit_sheet.py

run_step e103_qwen35_tg_ng_k1 \
  python3 scripts/run_e103_tg_ng_fair_hardtask.py \
    --model-key qwen35_27b \
    --task-ids aime25_base_divisor_p1 aime25_integer_pairs_quad_p4 aime25_trapezoid_incircle_p6 \
    --variants neutral self_check answer_first_no_gold \
    --modes NG_baseline NG_matched_sampling TG_official \
    --k 1 \
    --max-new-tokens 4096 \
    --max-time 600 \
    --batch-size 2 \
    --out-dir results/E103_tg_ng_fair_hardtask \
    --checkpoint-jsonl logs/e103_qwen35_tg_ng_k1_checkpoint_20260429.jsonl \
    --local-files-only \
    --seed 20260429

run_step e104_build_audit_sheet \
  python3 scripts/build_e104_tg_ng_process_audit_sheet.py \
    --input-json results/E103_tg_ng_fair_hardtask/qwen35_27b_e103_tg_ng_fair_hardtask.json \
    --out-jsonl data/processed/e104_tg_ng_process_audit_sheet_20260429.jsonl \
    --summary-json results/E104_tg_ng_process_audit/e104_tg_ng_process_audit_sheet_summary.json

log_status all all_done
