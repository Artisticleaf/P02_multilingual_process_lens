#!/usr/bin/env bash
set -euo pipefail
cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3
mkdir -p logs results/E90_hardtask_component_activation_cache
STATUS=logs/e90_component_cache_status_20260429.jsonl
: > "$STATUS"

echo "{\"status\":\"waiting_for_e85_e89_all_done\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
while true; do
  if [[ -f logs/e85_e89_status_20260429.jsonl ]] && tail -1 logs/e85_e89_status_20260429.jsonl | grep -q '"all_done"'; then
    break
  fi
  sleep 60
done
echo "{\"status\":\"upstream_done\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"

run_step() {
  local name="$1"; shift
  local logfile="logs/${name}_20260429.log"
  echo "{\"step\":\"$name\",\"status\":\"start\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
  echo "===== START $name $(date -Is) =====" | tee "$logfile"
  "$@" 2>&1 | tee -a "$logfile"
  echo "===== END $name $(date -Is) =====" | tee -a "$logfile"
  echo "{\"step\":\"$name\",\"status\":\"done\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
}

python -m py_compile scripts/run_e90_hardtask_component_activation_cache.py

run_step "e90_gemma4_31b_it_repaired_components" \
  python scripts/run_e90_hardtask_component_activation_cache.py \
    --model-key gemma4_31b_it \
    --target-mode repaired_acpi \
    --best-layer 34 \
    --layer-window 2 \
    --device auto \
    --local-files-only

run_step "e90_gemma4_26b_a4b_it_unrepaired_components" \
  python scripts/run_e90_hardtask_component_activation_cache.py \
    --model-key gemma4_26b_a4b_it \
    --target-mode unrepaired_acpi \
    --best-layer 17 \
    --layer-window 2 \
    --device auto \
    --local-files-only

echo "{\"status\":\"all_done\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
