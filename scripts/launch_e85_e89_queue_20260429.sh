#!/usr/bin/env bash
set -euo pipefail
cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3
mkdir -p logs \
  results/E85_hardtask_full_hidden_cache \
  results/E86_algebra_equivalence_adversarial \
  results/E87_glm_readout_intervention \
  results/E88_answer_first_natural_sample \
  results/E89_repair_policy_filter_simulation
STATUS=logs/e85_e89_status_20260429.jsonl
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

python -m py_compile \
  scripts/run_e85_hardtask_full_hidden_cache.py \
  scripts/run_e86_algebra_equivalence_adversarial.py \
  scripts/run_e87_glm_readout_intervention.py \
  scripts/build_e88_answer_first_audit_sheet.py \
  scripts/run_e89_repair_policy_filter_simulation.py

# E85: key-prefix hidden cache for known repaired/unrepaired hard-task ACPI cases.
run_step "e85_gemma4_31b_it_repaired" python scripts/run_e85_hardtask_full_hidden_cache.py --model-key gemma4_31b_it --device auto --local-files-only --target-mode repaired_acpi --best-layer 34
run_step "e85_gemma4_26b_a4b_it_unrepaired" python scripts/run_e85_hardtask_full_hidden_cache.py --model-key gemma4_26b_a4b_it --device auto --local-files-only --target-mode unrepaired_acpi --best-layer 17

# E86: algebra-equivalence adversarial ACPI generalization across expanded P0.
for m in qwen35_27b gemma4_31b_it gemma4_26b_a4b_it glm47_flash_candidate; do
  run_step "e86_${m}" python scripts/run_e86_algebra_equivalence_adversarial.py --model-key "$m" --device auto --local-files-only
done

# E87/E89 are post-hoc and cheap, but run after E86 so E89 can include E86 if present.
run_step "e87_glm47_readout_intervention" python scripts/run_e87_glm_readout_intervention.py

# E88: larger natural answer-first/no-gold generation. Gold/trap are not in prompts; gold is used offline only for final-correct filtering.
for m in qwen35_27b gemma4_31b_it gemma4_26b_a4b_it glm47_flash_candidate; do
  run_step "e88_${m}_answer_first_k8" python scripts/run_e49_hard_task_conditioning_official.py --model-key "$m" --variants answer_first_no_gold --k 8 --max-tasks 6 --max-new-tokens 1536 --batch-size 2 --thinking false --device auto --local-files-only --out-dir results/E88_answer_first_natural_sample --seed 20260429
done
run_step "e88_build_audit_sheet" python scripts/build_e88_answer_first_audit_sheet.py

run_step "e89_repair_policy_filter_simulation" python scripts/run_e89_repair_policy_filter_simulation.py

echo "{\"status\":\"all_done\",\"ts\":\"$(date -Is)\"}" >> "$STATUS"
