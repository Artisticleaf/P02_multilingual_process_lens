#!/usr/bin/env bash
set -uo pipefail

PROJECT=/home/Awei/P02_multilingual_process_lens
LOG_DIR="$PROJECT/logs"
STATUS="$LOG_DIR/e62_external_p0_smoke_status_20260429.jsonl"
mkdir -p "$LOG_DIR" "$PROJECT/results/E62_external_p0_smoke"
cd "$PROJECT"

source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH="$PROJECT/.deps/hf5:$PROJECT/src"
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3
export TRANSFORMERS_OFFLINE=1

run_one() {
  local model_key="$1"
  local mode="$2"
  local log="$LOG_DIR/e62_${model_key}_${mode}_20260429.log"
  echo "{\"event\":\"start\",\"experiment\":\"E62\",\"model_key\":\"$model_key\",\"mode\":\"$mode\",\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
  local args=(python scripts/run_e62_candidate_smoke.py --model-key "$model_key" --device auto --dtype bfloat16 --max-model-len 2048 --max-new-tokens 8 --local-files-only)
  if [[ "$mode" == "static" ]]; then
    args+=(--skip-hf-dynamic)
  fi
  timeout 3600 "${args[@]}" 2>&1 | tee "$log"
  local rc=${PIPESTATUS[0]}
  echo "{\"event\":\"done\",\"experiment\":\"E62\",\"model_key\":\"$model_key\",\"mode\":\"$mode\",\"rc\":$rc,\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
  return 0
}

python -m py_compile scripts/run_e62_candidate_smoke.py
# Static check all candidates first. Dynamic is attempted only where config/tokenizer smoke is plausible.
run_one nemotron_cascade2_30b_a3b_candidate static
run_one glm47_flash_candidate static
run_one exaone45_33b_candidate static
run_one nemotron_cascade2_30b_a3b_candidate dynamic
run_one glm47_flash_candidate dynamic
# EXAONE 4.5 requires vendor/forked Transformers according to local README and AutoConfig fails in current env;
# keep static-only unless the environment is upgraded.
echo "{\"event\":\"skip_dynamic\",\"experiment\":\"E62\",\"model_key\":\"exaone45_33b_candidate\",\"reason\":\"current transformers AutoConfig fails; README requests forked transformers/vllm\",\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
python scripts/audit_e62_external_p0_smoke.py 2>&1 | tee "$LOG_DIR/e62_external_p0_smoke_audit_20260429.log"
echo "{\"event\":\"all_done\",\"experiment\":\"E62\",\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
