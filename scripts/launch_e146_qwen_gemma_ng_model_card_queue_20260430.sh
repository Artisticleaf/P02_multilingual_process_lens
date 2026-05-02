#!/usr/bin/env bash
set -u -o pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

STATUS=logs/e146_qwen_gemma_ng_model_card_status_20260430.jsonl
OUT_DIR=results/E146_qwen_gemma_ng_model_card_hf_profile
DONE_DIR="$OUT_DIR/_status"
mkdir -p logs "$OUT_DIR" "$DONE_DIR"
: > "$STATUS"

ts() {
  date --iso-8601=seconds
}

record() {
  local status="$1"
  local step="$2"
  local detail="${3:-}"
  python - "$STATUS" "$status" "$step" "$(ts)" "$detail" <<'PY'
import json, sys
path, status, step, ts, detail = sys.argv[1:6]
row = {"status": status, "step": step, "ts": ts}
if detail:
    row["detail"] = detail
with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
PY
}

write_marker() {
  local marker="$1"
  local step="$2"
  local code="${3:-0}"
  python - "$marker" "$step" "$code" "$(ts)" <<'PY'
import json, sys
path, step, code, ts = sys.argv[1:5]
with open(path, "w", encoding="utf-8") as f:
    json.dump({"step": step, "exit_code": int(code), "ts": ts}, f, ensure_ascii=False, indent=2, sort_keys=True)
    f.write("\n")
PY
}

wait_for_e119() {
  local dep_status=logs/e119_natural_hardtask_expansion_status_20260430.jsonl
  record start wait_for_e119 "waiting for existing E119 queue to finish or release GPUs"
  while true; do
    if [[ -f "$dep_status" ]] && grep -q '"status":"all_done"' "$dep_status"; then
      record done wait_for_e119 "E119 all_done observed"
      return 0
    fi
    if tmux has-session -t p02_e119_20260430 2>/dev/null; then
      sleep 60
      continue
    fi
    if pgrep -af 'run_e49_hard_task_conditioning_official.py' >/dev/null 2>&1; then
      sleep 60
      continue
    fi
    record fail_missing_done_signal wait_for_e119 "E119 ended without all_done; continuing because GPUs appear released"
    return 0
  done
}

run_step() {
  local step="$1"
  local log="$2"
  shift 2
  local done_marker="$DONE_DIR/${step}_DONE.json"
  local fail_marker="$DONE_DIR/${step}_FAILED.json"
  if [[ -f "$done_marker" ]]; then
    record skipped "$step" "done marker exists"
    return 0
  fi
  record start "$step"
  rm -f "$fail_marker"
  set +e
  "$@" 2>&1 | tee "$log"
  local code=${PIPESTATUS[0]}
  set -u -o pipefail
  if [[ "$code" -eq 0 ]]; then
    write_marker "$done_marker" "$step" "$code"
    record done "$step"
  else
    write_marker "$fail_marker" "$step" "$code"
    nvidia-smi > "logs/${step}_gpu_snapshot_20260430.log" 2>&1 || true
    record fail "$step" "exit_code=${code}; continuing to next step"
  fi
  return 0
}

run_model() {
  local model="$1"
  local temperature="$2"
  local top_p="$3"
  local top_k="$4"
  local step="e146_${model}_ng_model_card_hf_profile"
  run_step "$step" "logs/${step}_20260430.log" \
    python scripts/run_e49_hard_task_conditioning_official.py \
      --model-key "$model" \
      --out-dir "$OUT_DIR" \
      --variants neutral self_check answer_first_no_gold \
      --k 2 \
      --max-tasks 6 \
      --max-new-tokens 8192 \
      --batch-size 2 \
      --temperature "$temperature" \
      --top-p "$top_p" \
      --top-k "$top_k" \
      --thinking false \
      --checkpoint-jsonl "logs/${step}_checkpoint_20260430.jsonl"
}

record start e146_queue

run_step preflight logs/e146_preflight_20260430.log \
  bash -lc 'python -m py_compile scripts/run_e49_hard_task_conditioning_official.py scripts/build_e119_natural_hardtask_audit_sheet.py scripts/smoke_qwen_gemma_next_stage_queue.py && python scripts/smoke_qwen_gemma_next_stage_queue.py'

wait_for_e119

run_model qwen35_27b 1.0 0.95 20
run_model gemma4_31b_it 1.0 0.95 64
run_model gemma4_26b_a4b_it 1.0 0.95 64

run_step e146_build_audit_sheet logs/e146_build_audit_sheet_20260430.log \
  python scripts/build_e119_natural_hardtask_audit_sheet.py \
    --in-dir "$OUT_DIR" \
    --out-jsonl /home/Awei/P02_multilingual_process_lens/data/processed/e146_qwen_gemma_model_card_final_correct_audit_sheet_20260430.jsonl \
    --summary-json /home/Awei/P02_multilingual_process_lens/results/E146_qwen_gemma_ng_model_card_hf_profile/e146_audit_sheet_summary.json

record all_done e146_queue
