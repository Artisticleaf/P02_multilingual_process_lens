#!/usr/bin/env bash
set -euo pipefail
cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3
mkdir -p logs results/E92_thinking_hard_task_natural data/processed
STATUS=logs/e92_thinking_hard_task_status_20260429.jsonl
: > "$STATUS"

K="${E92_K:-2}"
MAX_TASKS="${E92_MAX_TASKS:-6}"
MAX_NEW_TOKENS="${E92_MAX_NEW_TOKENS:-3072}"
BATCH_SIZE="${E92_BATCH_SIZE:-1}"
VARIANTS=(neutral answer_first_no_gold self_check)

run_step() {
  local name="$1"; shift
  local logfile="logs/${name}_20260429.log"
  echo "{\"step\":\"$name\",\"status\":\"start\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
  echo "===== START $name $(date -Is) =====" | tee "$logfile"
  "$@" 2>&1 | tee -a "$logfile"
  echo "===== END $name $(date -Is) =====" | tee -a "$logfile"
  echo "{\"step\":\"$name\",\"status\":\"done\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
}

run_model() {
  local model="$1"
  local temperature="$2"
  local top_p="$3"
  local top_k="$4"
  run_step "e92_${model}_thinking_k${K}" \
    python scripts/run_e49_hard_task_conditioning_official.py \
      --model-key "$model" \
      --variants "${VARIANTS[@]}" \
      --k "$K" \
      --max-tasks "$MAX_TASKS" \
      --max-new-tokens "$MAX_NEW_TOKENS" \
      --batch-size "$BATCH_SIZE" \
      --temperature "$temperature" \
      --top-p "$top_p" \
      --top-k "$top_k" \
      --thinking true \
      --allow-final-fallback \
      --device auto \
      --local-files-only \
      --out-dir results/E92_thinking_hard_task_natural \
      --seed 20260429
}

python -m py_compile scripts/run_e49_hard_task_conditioning_official.py scripts/build_e92_thinking_hard_task_audit_sheet.py

# E91 local model-card settings:
# Qwen thinking: temperature=1.0, top_p=0.95, top_k=20.
# Gemma4 thinking: temperature=1.0, top_p=0.95, top_k=64.
# GLM local default evaluation: temperature=1.0, top_p=0.95; top_k is disabled here.
run_model qwen35_27b 1.0 0.95 20
run_model gemma4_31b_it 1.0 0.95 64
run_model gemma4_26b_a4b_it 1.0 0.95 64
run_model glm47_flash_candidate 1.0 0.95 0

run_step "e92_build_audit_sheet" python scripts/build_e92_thinking_hard_task_audit_sheet.py

echo "{\"status\":\"all_done\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
