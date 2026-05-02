#!/usr/bin/env bash
set -euo pipefail
cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
mkdir -p logs results/E53_answer_anchor_ablation results/E54_parameterized_no_leak_generalization results/E55_residual_to_logit_mediation results/E56_component_decomposition results/E57_p0_hard_task_final_correct_harvesting

echo "[queue] start $(date -Is) host=$(hostname) visible=${CUDA_VISIBLE_DEVICES:-all}"
python -m py_compile scripts/run_e53_answer_anchor_ablation.py scripts/build_e54_parameterized_generalization.py scripts/run_e55_residual_to_logit_mediation.py scripts/run_e56_component_decomposition.py scripts/run_e42_official_template_parity.py scripts/run_e49_hard_task_conditioning_official.py
python scripts/build_e54_parameterized_generalization.py

run_or_skip() {
  local out="$1"; shift
  if [[ -s "$out" ]]; then
    echo "[queue] skip existing $out"
  else
    echo "[queue] run $(date -Is): $*"
    "$@"
    echo "[queue] done $(date -Is): $out"
  fi
}

models=(qwen35_27b gemma4_31b_it gemma4_26b_a4b_it)
for m in "${models[@]}"; do
  echo "[queue] ===== model $m $(date -Is) ====="
  run_or_skip "results/E53_answer_anchor_ablation/${m}_e53_answer_anchor_ablation.json" \
    python scripts/run_e53_answer_anchor_ablation.py --model-key "$m" --device auto --local-files-only
  run_or_skip "results/E54_parameterized_no_leak_generalization/${m}_e42_official_template_parity_chat.json" \
    python scripts/run_e42_official_template_parity.py --model-key "$m" --manual-jsonl data/processed/e54_parameterized_no_leak_generalization_20260428.jsonl --pairs-yaml configs/e54_parameterized_no_leak_pairs.yaml --out-dir results/E54_parameterized_no_leak_generalization --device auto --local-files-only
  run_or_skip "results/E55_residual_to_logit_mediation/${m}_e55_residual_to_logit_mediation.json" \
    python scripts/run_e55_residual_to_logit_mediation.py --model-key "$m" --device auto --local-files-only
  run_or_skip "results/E56_component_decomposition/${m}_e56_component_decomposition.json" \
    python scripts/run_e56_component_decomposition.py --model-key "$m" --device auto --local-files-only
  run_or_skip "results/E57_p0_hard_task_final_correct_harvesting/${m}_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json" \
    python scripts/run_e49_hard_task_conditioning_official.py --model-key "$m" --variants neutral answer_first_no_gold self_check --k 4 --max-tasks 6 --max-new-tokens 1536 --batch-size 3 --thinking false --device auto --local-files-only --out-dir results/E57_p0_hard_task_final_correct_harvesting
done

echo "[queue] finished $(date -Is)"
