#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:180GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

mkdir -p logs results/E172_aime2026_hidden_gate

ts() { date --iso-8601=seconds; }

smoke_baseline() {
  local model="$1"
  echo "===== START e172_baseline_${model}_smoke $(ts) ====="
  python scripts/run_e172_aime2026_nonthinking_baseline.py \
    --model-key "$model" \
    --max-tasks 1 \
    --max-new-tokens 4096 \
    --batch-size 1 \
    --temperature 0.0 \
    --checkpoint-jsonl "logs/e172_aime2026_baseline_${model}_smoke_checkpoint_20260503.jsonl" \
    --local-files-only \
    --tag smoke_20260503 2>&1 | tee "logs/e172_baseline_${model}_smoke_20260503.log"
  echo "===== END e172_baseline_${model}_smoke $(ts) ====="
}

smoke_hidden_gate() {
  local model="$1"
  echo "===== START e172_hidden_gate_${model}_smoke $(ts) ====="
  python scripts/run_e172_aime2026_hidden_gate_realtime.py \
    --model-key "$model" \
    --max-tasks 1 \
    --max-first-pass-tokens 1024 \
    --max-controlled-tokens 512 \
    --chunk-tokens 96 \
    --observe-every-tokens 96 \
    --max-model-len 8192 \
    --temperature 0.0 \
    --checkpoint-jsonl "logs/e172_aime2026_hidden_gate_${model}_smoke_checkpoint_20260503.jsonl" \
    --observation-jsonl "logs/e172_aime2026_hidden_gate_${model}_observations_smoke_20260503.jsonl" \
    --local-files-only \
    --tag smoke_20260503 2>&1 | tee "logs/e172_hidden_gate_${model}_smoke_20260503.log"
  echo "===== END e172_hidden_gate_${model}_smoke $(ts) ====="
}

echo "===== E149 GEMMA4 SMOKE $(ts) ====="

echo ""
echo "========== Gemma4-31B-IT dense =========="
smoke_baseline gemma4_31b_it
smoke_hidden_gate gemma4_31b_it

echo ""
echo "========== Gemma4-26B-A4B-IT MoE =========="
smoke_baseline gemma4_26b_a4b_it
smoke_hidden_gate gemma4_26b_a4b_it

echo ""
echo "===== E149 GEMMA4 SMOKE DONE $(ts) ====="
