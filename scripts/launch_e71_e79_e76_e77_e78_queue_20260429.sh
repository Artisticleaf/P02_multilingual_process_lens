#!/usr/bin/env bash
set -euo pipefail
cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3
mkdir -p logs results/E71_repair_objective results/E79_glm_label_free_sibling results/E76_E77_hardtask_hidden_replay results/E78_hidden_probe_false_positive_audit
STATUS=logs/e71_e79_e76_e77_e78_status_20260429.jsonl
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
  run_step "e71_${m}" python scripts/run_e71_repair_objective.py --model-key "$m" --device auto --local-files-only
  run_step "e78_${m}" python scripts/run_e78_hidden_probe_false_positive_audit.py --model-key "$m" --device auto --local-files-only --n-perm 100
done
run_step "e79_glm47_flash_candidate" python scripts/run_e79_glm_label_free_sibling.py --model-key glm47_flash_candidate --device auto --local-files-only
run_step "e76_gemma4_31b_it" python scripts/run_e76_e77_hardtask_hidden_replay.py --model-key gemma4_31b_it --device auto --local-files-only --target-mode repaired_acpi
run_step "e77_gemma4_26b_a4b_it" python scripts/run_e76_e77_hardtask_hidden_replay.py --model-key gemma4_26b_a4b_it --device auto --local-files-only --target-mode unrepaired_acpi

echo "{\"status\":\"all_done\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
