#!/usr/bin/env bash
set -euo pipefail
cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3
mkdir -p logs results/E81_label_free_sibling_fulloption_check
STATUS=logs/e81_trace1_fulloption_status_20260429.jsonl
: > "$STATUS"
run_step() {
  local name="$1"; shift
  local logfile="logs/${name}_20260429.log"
  echo "{\"step\":\"$name\",\"status\":\"start\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
  echo "===== START $name $(date -Is) =====" | tee "$logfile"
  "$@" 2>&1 | tee -a "$logfile"
  echo "===== END $name $(date -Is) =====" | tee -a "$logfile"
  echo "{\"step\":\"$name\",\"status\":\"done\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
}
for m in qwen35_27b gemma4_31b_it gemma4_26b_a4b_it glm47_flash_candidate; do
  run_step "e81_trace1_full_${m}" python scripts/run_e79_glm_label_free_sibling.py --model-key "$m" --device auto --local-files-only --out-dir results/E81_label_free_sibling_fulloption_check --formats trace1_trace2 --score-mode full_option
done
echo "{\"status\":\"all_done\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
