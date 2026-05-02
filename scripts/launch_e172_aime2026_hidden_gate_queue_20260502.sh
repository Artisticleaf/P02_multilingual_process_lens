#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:180GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

mkdir -p logs results/E172_aime2026_hidden_gate
STATUS=logs/e172_aime2026_hidden_gate_status_20260502.jsonl
: > "$STATUS"

MAX_BASELINE_TOKENS=16384
MAX_FIRST_PASS_TOKENS=16384
MAX_CONTROLLED_TOKENS=4096
MAX_MODEL_LEN=8192
CHUNK_TOKENS=96
OBSERVE_EVERY_TOKENS=96

ts() { date --iso-8601=seconds; }
record() {
  printf '{"status":"%s","step":"%s","ts":"%s"}\n' "$1" "$2" "$(ts)" >> "$STATUS"
}

run_logged() {
  local step="$1"; shift
  local logfile="$1"; shift
  record start "$step"
  echo "===== START $step $(ts) =====" | tee "$logfile"
  "$@" 2>&1 | tee -a "$logfile"
  echo "===== END $step $(ts) =====" | tee -a "$logfile"
  record done "$step"
}

record start e172_static_audit
python -m py_compile \
  scripts/build_e172_aime2026_task_bank.py \
  scripts/smoke_e172_aime2026_prompt.py \
  scripts/audit_e172_aime2026_pipeline.py \
  scripts/run_e172_aime2026_nonthinking_baseline.py \
  scripts/run_e172_aime2026_hidden_gate_realtime.py \
  scripts/summarize_e172_aime2026_hidden_gate.py
python scripts/build_e172_aime2026_task_bank.py 2>&1 | tee logs/e172_build_aime2026_task_bank_20260502.log
python scripts/smoke_e172_aime2026_prompt.py 2>&1 | tee logs/e172_prompt_smoke_20260502.log
python scripts/audit_e172_aime2026_pipeline.py 2>&1 | tee logs/e172_pipeline_audit_20260502.log
record done e172_static_audit

run_logged e172_baseline_qwen35_27b_smoke logs/e172_baseline_qwen35_27b_smoke_20260502.log \
  python scripts/run_e172_aime2026_nonthinking_baseline.py \
    --model-key qwen35_27b \
    --max-tasks 1 \
    --max-new-tokens 4096 \
    --batch-size 1 \
    --temperature 0.0 \
    --checkpoint-jsonl logs/e172_aime2026_baseline_qwen35_27b_smoke_checkpoint_20260502.jsonl \
    --local-files-only \
    --tag smoke_20260502

run_logged e172_hidden_gate_qwen35_27b_smoke logs/e172_hidden_gate_qwen35_27b_smoke_20260502.log \
  python scripts/run_e172_aime2026_hidden_gate_realtime.py \
    --model-key qwen35_27b \
    --max-tasks 1 \
    --max-first-pass-tokens 1024 \
    --max-controlled-tokens 512 \
    --chunk-tokens 96 \
    --observe-every-tokens 96 \
    --max-model-len "$MAX_MODEL_LEN" \
    --temperature 0.0 \
    --checkpoint-jsonl logs/e172_aime2026_hidden_gate_qwen35_27b_smoke_checkpoint_20260502.jsonl \
    --observation-jsonl logs/e172_aime2026_hidden_gate_qwen35_27b_observations_smoke_20260502.jsonl \
    --local-files-only \
    --tag smoke_20260502

run_model() {
  local model="$1"
  run_logged "e172_baseline_${model}" "logs/e172_baseline_${model}_20260502.log" \
    python scripts/run_e172_aime2026_nonthinking_baseline.py \
      --model-key "$model" \
      --max-new-tokens "$MAX_BASELINE_TOKENS" \
      --batch-size 1 \
      --temperature 0.0 \
      --checkpoint-jsonl "logs/e172_aime2026_baseline_${model}_checkpoint_20260502.jsonl" \
      --local-files-only \
      --tag max16384_20260502

  run_logged "e172_hidden_gate_${model}" "logs/e172_hidden_gate_${model}_20260502.log" \
    python scripts/run_e172_aime2026_hidden_gate_realtime.py \
      --model-key "$model" \
      --max-first-pass-tokens "$MAX_FIRST_PASS_TOKENS" \
      --max-controlled-tokens "$MAX_CONTROLLED_TOKENS" \
      --chunk-tokens "$CHUNK_TOKENS" \
      --observe-every-tokens "$OBSERVE_EVERY_TOKENS" \
      --max-model-len "$MAX_MODEL_LEN" \
      --temperature 0.0 \
      --checkpoint-jsonl "logs/e172_aime2026_hidden_gate_${model}_checkpoint_20260502.jsonl" \
      --observation-jsonl "logs/e172_aime2026_hidden_gate_${model}_observations_20260502.jsonl" \
      --local-files-only \
      --tag max16384_20260502
}

run_model qwen35_27b
run_model gemma4_31b_it
run_model gemma4_26b_a4b_it

run_logged e172_stage_analysis logs/e172_stage_analysis_20260502.log \
  python scripts/summarize_e172_aime2026_hidden_gate.py

record all_done all
