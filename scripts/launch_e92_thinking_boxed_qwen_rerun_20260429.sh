#!/usr/bin/env bash
set -euo pipefail
cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

mkdir -p logs results/E92_thinking_hard_task_natural
STATUS=logs/e92_thinking_boxed_qwen_rerun_status_20260429.jsonl
: > "$STATUS"

NAME=e92_qwen35_27b_thinking_boxed_k2_max8192
LOG=logs/${NAME}_20260429.log
CHECKPOINT=results/E92_thinking_hard_task_natural/${NAME}_checkpoint.jsonl

echo "{\"step\":\"$NAME\",\"status\":\"start\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
echo "===== START $NAME $(date -Is) =====" | tee "$LOG"

python -m py_compile scripts/run_e49_hard_task_conditioning_official.py
python scripts/run_e49_hard_task_conditioning_official.py \
  --model-key qwen35_27b \
  --variants thinking_boxed_neutral thinking_boxed_answer_after thinking_boxed_self_check \
  --k 2 \
  --max-tasks 6 \
  --max-new-tokens 8192 \
  --batch-size 2 \
  --temperature 1.0 \
  --top-p 0.95 \
  --top-k 20 \
  --thinking true \
  --allow-final-fallback \
  --checkpoint-jsonl "$CHECKPOINT" \
  --device auto \
  --local-files-only \
  --out-dir results/E92_thinking_hard_task_natural \
  --seed 20260429 \
  2>&1 | tee -a "$LOG"

echo "===== END $NAME $(date -Is) =====" | tee -a "$LOG"
echo "{\"step\":\"$NAME\",\"status\":\"done\",\"ts\":\"$(date -Is)\",\"checkpoint\":\"$CHECKPOINT\"}" >> "$STATUS"
echo "{\"status\":\"all_done\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
