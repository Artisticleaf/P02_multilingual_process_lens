#!/usr/bin/env bash
set -u -o pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

STATUS=logs/e121_e126_next_stage_status_20260430.jsonl
DONE_DIR=results/E121_E126_next_stage_status
mkdir -p logs "$DONE_DIR" results/E121_e119_e146_component_localization results/E122_component_steering_audit results/E123_unrepaired_case_deepdive results/E124_broad_unrepaired_harvest
: > "$STATUS"

ts() { date --iso-8601=seconds; }

record() {
  local status="$1"
  local step="$2"
  local detail="${3:-}"
  python - "$STATUS" "$status" "$step" "$(ts)" "$detail" <<'PY'
import json, sys
path, status, step, ts, detail = sys.argv[1:6]
row = {"status": status, "step": step, "ts": ts}
if detail:
    row["detail"] = detail
with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
PY
}

write_marker() {
  local marker="$1"
  local step="$2"
  local code="${3:-0}"
  python - "$marker" "$step" "$code" "$(ts)" <<'PY'
import json, sys
path, step, code, ts = sys.argv[1:5]
with open(path, "w", encoding="utf-8") as f:
    json.dump({"step": step, "exit_code": int(code), "ts": ts}, f, ensure_ascii=False, indent=2, sort_keys=True)
    f.write("\n")
PY
}

run_step() {
  local step="$1"
  local log="$2"
  shift 2
  local done_marker="$DONE_DIR/${step}_DONE.json"
  local fail_marker="$DONE_DIR/${step}_FAILED.json"
  if [[ -f "$done_marker" ]]; then
    record skipped "$step" "done marker exists"
    return 0
  fi
  record start "$step"
  rm -f "$fail_marker"
  set +e
  "$@" 2>&1 | tee "$log"
  local code=${PIPESTATUS[0]}
  set -u -o pipefail
  if [[ "$code" -eq 0 ]]; then
    write_marker "$done_marker" "$step" "$code"
    record done "$step"
  else
    write_marker "$fail_marker" "$step" "$code"
    nvidia-smi > "logs/${step}_gpu_snapshot_20260430.log" 2>&1 || true
    record fail "$step" "exit_code=${code}; continuing"
  fi
  return 0
}

record start e121_e126_queue

run_step preflight logs/e121_e126_preflight_20260430.log \
  bash -lc 'python -m py_compile scripts/run_e90_hardtask_component_activation_cache.py scripts/run_e122_component_steering_audit.py scripts/run_e123_unrepaired_case_deepdive.py scripts/run_e124_broad_unrepaired_harvest.py scripts/build_e124_broad_audit_sheet.py scripts/finalize_e119_e146_process_audit.py'

# E121: component localization on the new E119/E146 official labels.
run_step e121_gemma26_unrepaired_components logs/e121_gemma26_unrepaired_components_20260430.log \
  python scripts/run_e90_hardtask_component_activation_cache.py \
    --model-key gemma4_26b_a4b_it \
    --audit-jsonl data/processed/e119_e146_process_audit_official_20260430.jsonl \
    --out-dir results/E121_e119_e146_component_localization \
    --target-mode unrepaired_acpi \
    --best-layer 17 \
    --layer-window 2 \
    --max-model-len 8192 \
    --device auto

run_step e121_gemma31_repaired_components logs/e121_gemma31_repaired_components_20260430.log \
  python scripts/run_e90_hardtask_component_activation_cache.py \
    --model-key gemma4_31b_it \
    --audit-jsonl data/processed/e119_e146_process_audit_official_20260430.jsonl \
    --out-dir results/E121_e119_e146_component_localization \
    --target-mode repaired_acpi \
    --best-layer 34 \
    --layer-window 2 \
    --max-model-len 8192 \
    --device auto

# E122: small component steering diagnostics.
run_step e122_gemma26_component_steering logs/e122_gemma26_component_steering_20260430.log \
  python scripts/run_e122_component_steering_audit.py \
    --model-key gemma4_26b_a4b_it \
    --best-layer 17 \
    --max-target-rows 10 \
    --alphas -2.0 2.0 \
    --components residual mlp token_mixer \
    --max-model-len 8192 \
    --device auto

run_step e122_gemma31_component_steering logs/e122_gemma31_component_steering_20260430.log \
  python scripts/run_e122_component_steering_audit.py \
    --model-key gemma4_31b_it \
    --best-layer 34 \
    --max-target-rows 10 \
    --alphas -2.0 2.0 \
    --components residual mlp token_mixer \
    --max-model-len 8192 \
    --device auto

# E123: deep dive on the two unrepaired ACPI cases.
run_step e123_gemma26_unrepaired_deepdive logs/e123_gemma26_unrepaired_deepdive_20260430.log \
  python scripts/run_e123_unrepaired_case_deepdive.py \
    --verifier-model-key gemma4_26b_a4b_it \
    --best-layer 17 \
    --max-model-len 8192 \
    --device auto

# E124: high-yield broad harvest. Start with answer-first because prior
# natural unrepaired ACPI is concentrated there.
run_step e124_qwen35_27b_answer_first logs/e124_qwen35_27b_answer_first_20260430.log \
  python scripts/run_e124_broad_unrepaired_harvest.py \
    --model-key qwen35_27b \
    --variants answer_first_no_gold \
    --k 4 \
    --max-new-tokens 4096 \
    --batch-size 2 \
    --temperature 1.0 \
    --top-p 0.95 \
    --top-k 20 \
    --thinking false \
    --checkpoint-jsonl logs/e124_qwen35_27b_answer_first_checkpoint_20260430.jsonl

run_step e124_gemma4_31b_answer_first logs/e124_gemma4_31b_answer_first_20260430.log \
  python scripts/run_e124_broad_unrepaired_harvest.py \
    --model-key gemma4_31b_it \
    --variants answer_first_no_gold \
    --k 4 \
    --max-new-tokens 4096 \
    --batch-size 2 \
    --temperature 1.0 \
    --top-p 0.95 \
    --top-k 64 \
    --thinking false \
    --checkpoint-jsonl logs/e124_gemma4_31b_answer_first_checkpoint_20260430.jsonl

run_step e124_gemma4_26b_answer_first logs/e124_gemma4_26b_answer_first_20260430.log \
  python scripts/run_e124_broad_unrepaired_harvest.py \
    --model-key gemma4_26b_a4b_it \
    --variants answer_first_no_gold \
    --k 4 \
    --max-new-tokens 4096 \
    --batch-size 2 \
    --temperature 1.0 \
    --top-p 0.95 \
    --top-k 64 \
    --thinking false \
    --checkpoint-jsonl logs/e124_gemma4_26b_answer_first_checkpoint_20260430.jsonl

run_step e124_build_audit_sheet logs/e124_build_audit_sheet_20260430.log \
  python scripts/build_e124_broad_audit_sheet.py

record all_done e121_e126_queue
