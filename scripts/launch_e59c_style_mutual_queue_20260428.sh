#!/usr/bin/env bash
set -e -u -o pipefail

PROJECT=/home/Awei/P02_multilingual_process_lens
LOG_DIR="$PROJECT/logs"
STATUS="$LOG_DIR/e59c_style_mutual_queue_status_20260428.jsonl"
mkdir -p "$LOG_DIR"

source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH="$PROJECT/.deps/hf5:$PROJECT/src"
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export CUDA_VISIBLE_DEVICES=0,1,2,3

cd "$PROJECT"

echo "{\"event\":\"queue_start\",\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"

run_step() {
  local name="$1"
  shift
  echo "{\"event\":\"start\",\"step\":\"$name\",\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
  echo "[$(date --iso-8601=seconds)] START $name"
  "$@"
  local rc=$?
  echo "[$(date --iso-8601=seconds)] END $name rc=$rc"
  echo "{\"event\":\"end\",\"step\":\"$name\",\"rc\":$rc,\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
  return $rc
}

for source in qwen35_27b gemma4_31b_it gemma4_26b_a4b_it; do
  run_step "e59c_rewrite_${source}" \
    python scripts/run_e59c_style_rewrite.py \
      --model-key "$source" \
      --device auto \
      --dtype bfloat16 \
      --max-new-tokens 256 \
      --local-files-only
done

run_step e59c_audit_rewrites python scripts/audit_e59c_style_rewrite.py

for verifier in qwen35_27b gemma4_31b_it gemma4_26b_a4b_it; do
  run_step "e59c_cross_verifier_${verifier}" \
    python scripts/run_e59c_cross_verifier_style.py \
      --verifier-model-key "$verifier" \
      --device auto \
      --dtype bfloat16 \
      --max-model-len 4096 \
      --local-files-only
done

run_step e59c_post_py_compile python -m py_compile scripts/run_e59c_style_rewrite.py scripts/audit_e59c_style_rewrite.py scripts/run_e59c_cross_verifier_style.py

echo "{\"event\":\"queue_done\",\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
