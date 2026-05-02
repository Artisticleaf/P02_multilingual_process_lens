#!/usr/bin/env bash
set -u -o pipefail

PROJECT=/home/Awei/P02_multilingual_process_lens
LOG_DIR="$PROJECT/logs"
STATUS="$LOG_DIR/p0_completion_queue_status_20260428.jsonl"
mkdir -p "$LOG_DIR"

source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH="$PROJECT/.deps/hf5:$PROJECT/src"
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export CUDA_VISIBLE_DEVICES=0,1,2,3

cd "$PROJECT"

run_step() {
  local name="$1"
  shift
  echo "{\"event\":\"start\",\"step\":\"$name\",\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
  echo "[$(date --iso-8601=seconds)] START $name"
  "$@"
  local rc=$?
  echo "[$(date --iso-8601=seconds)] END $name rc=$rc"
  echo "{\"event\":\"end\",\"step\":\"$name\",\"rc\":$rc,\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
  return 0
}

# Natural prevalence is already present for all three current P0 models.  This
# queue fills missing P0 controlled-verifier and mechanism evidence.
echo "{\"event\":\"queue_start\",\"ts\":\"$(date --iso-8601=seconds)\",\"note\":\"E48 natural prevalence already exists for qwen35_27b, gemma4_31b_it, gemma4_26b_a4b_it\"}" >> "$STATUS"

run_step e42_gemma4_26b_a4b_it \
  python scripts/run_e42_official_template_parity.py \
    --model-key gemma4_26b_a4b_it \
    --device auto \
    --dtype bfloat16 \
    --max-model-len 4096 \
    --local-files-only

run_step e44_qwen35_27b \
  python scripts/run_e44_mlp_direction_steering.py \
    --model-key qwen35_27b \
    --device auto \
    --dtype bfloat16 \
    --layers 8,16,24,32,40,48,56,63 \
    --alphas 0.5,1.0 \
    --local-files-only

run_step e50_qwen35_27b \
  python scripts/run_e50_residual_probe_steering.py \
    --model-key qwen35_27b \
    --device auto \
    --dtype bfloat16 \
    --max-model-len 4096 \
    --layers 8 16 24 32 40 48 56 63 \
    --steer-layers 16 32 48 56 \
    --local-files-only

run_step e44_gemma4_31b_it \
  python scripts/run_e44_mlp_direction_steering.py \
    --model-key gemma4_31b_it \
    --device auto \
    --dtype bfloat16 \
    --layers 8,16,24,32,40,48,56,59 \
    --alphas 0.5,1.0 \
    --local-files-only

run_step e50_gemma4_31b_it \
  python scripts/run_e50_residual_probe_steering.py \
    --model-key gemma4_31b_it \
    --device auto \
    --dtype bfloat16 \
    --max-model-len 4096 \
    --layers 8 16 24 32 40 48 56 59 \
    --steer-layers 16 32 48 56 \
    --local-files-only

run_step e44_gemma4_26b_a4b_it \
  python scripts/run_e44_mlp_direction_steering.py \
    --model-key gemma4_26b_a4b_it \
    --device auto \
    --dtype bfloat16 \
    --layers 4,8,12,16,20,24,28,29 \
    --alphas 0.5,1.0 \
    --local-files-only

run_step e50_gemma4_26b_a4b_it \
  python scripts/run_e50_residual_probe_steering.py \
    --model-key gemma4_26b_a4b_it \
    --device auto \
    --dtype bfloat16 \
    --max-model-len 4096 \
    --layers 4 8 12 16 20 24 28 29 \
    --steer-layers 8 16 24 28 \
    --local-files-only

echo "{\"event\":\"queue_done\",\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
