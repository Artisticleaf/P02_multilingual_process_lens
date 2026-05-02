#!/usr/bin/env bash
set -euo pipefail

# Unified four-GPU launcher for black-box verifier experiments.
#
# It uses vLLM when the model is supported, and falls back to HuggingFace
# device_map=auto when vLLM cannot load a checkpoint family. Hidden-state,
# residual-patch, layer-lens, and MLP/head mechanism probes should still use
# the dedicated HF hook scripts rather than this black-box runner.
#
# Usage:
#   scripts/launch_blackbox_4gpu_suite.sh MODEL_KEY [core|s6|e28|e30|e31]
# Optional:
#   MPLENS_BACKEND=auto|vllm|hf
#   VLLM_TP=4 VLLM_GPU_UTIL=0.88 VLLM_BATCH_SIZE=64 VLLM_MAX_MODEL_LEN=6144
#   MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'

ROOT="/home/Awei/P02_multilingual_process_lens"
ENV_SH="/home/Awei/miniconda3/etc/profile.d/conda.sh"
MODEL_KEY="${1:?model key required}"
SUITE="${2:-core}"
BACKEND="${MPLENS_BACKEND:-auto}"
TP="${VLLM_TP:-4}"
GPU_UTIL="${VLLM_GPU_UTIL:-0.88}"
MAX_LEN="${VLLM_MAX_MODEL_LEN:-6144}"
BATCH="${VLLM_BATCH_SIZE:-64}"
DTYPE="${MPLENS_DTYPE:-${VLLM_DTYPE:-bfloat16}}"

choose_backend() {
  case "$BACKEND" in
    vllm|hf) echo "$BACKEND" ;;
    auto)
      case "$MODEL_KEY" in
        gemma4_*) echo "hf" ;;
        *) echo "vllm" ;;
      esac
      ;;
    *)
      echo "Unknown MPLENS_BACKEND=$BACKEND; expected auto|vllm|hf" >&2
      exit 2
      ;;
  esac
}

run_abs() {
  local backend="$1"
  local tag="$2"
  local manual="$3"
  local base_out="$4"
  local out_dir="$ROOT/${base_out}_${backend}"
  mkdir -p "$out_dir" "$ROOT/logs"
  echo "[4gpu-suite] backend=$backend model=$MODEL_KEY tag=$tag manual=$manual out=$out_dir"
  if [[ "$backend" == "vllm" ]]; then
    CUDA_VISIBLE_DEVICES=0,1,2,3 python "$ROOT/scripts/run_manual_trace_verifier_vllm.py" \
      --model-key "$MODEL_KEY" \
      --manual-jsonl "$ROOT/$manual" \
      --out-dir "$out_dir" \
      --dtype "$DTYPE" \
      --tensor-parallel-size "$TP" \
      --gpu-memory-utilization "$GPU_UTIL" \
      --max-model-len "$MAX_LEN" \
      --batch-size "$BATCH" \
      2>&1 | tee "$ROOT/logs/${tag}_${MODEL_KEY}_vllm_abs.log"
  else
    export MPLENS_MAX_MEMORY="${MPLENS_MAX_MEMORY:-0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB}"
    CUDA_VISIBLE_DEVICES=0,1,2,3 python "$ROOT/scripts/run_manual_trace_verifier.py" \
      --model-key "$MODEL_KEY" \
      --manual-jsonl "$ROOT/$manual" \
      --out-dir "$out_dir" \
      --dtype "$DTYPE" \
      --device auto \
      --max-model-len "$MAX_LEN" \
      --local-files-only \
      2>&1 | tee "$ROOT/logs/${tag}_${MODEL_KEY}_hf4gpu_abs.log"
  fi
}

cd "$ROOT"
source "$ENV_SH"
conda activate passage_prep_py312
export PYTHONPATH="$ROOT/.deps/hf5:$ROOT/src"

RESOLVED_BACKEND="$(choose_backend)"
echo "[4gpu-suite] resolved backend=$RESOLVED_BACKEND for model=$MODEL_KEY"

case "$SUITE" in
  core)
    run_abs "$RESOLVED_BACKEND" "S6" "data/processed/s6_lexical_grid_verifier_subset_20260427.jsonl" "results/S6_lexical_grid_absolute_verifier"
    run_abs "$RESOLVED_BACKEND" "E28" "data/processed/e28_counterfactual_answer_masking_20260427.jsonl" "results/E28_counterfactual_answer_masking_absolute_verifier"
    run_abs "$RESOLVED_BACKEND" "E30" "data/processed/e30_non_discount_verifier_subset_20260427.jsonl" "results/E30_non_discount_absolute_verifier"
    run_abs "$RESOLVED_BACKEND" "E31" "data/processed/e31_non_discount_counterfactual_20260427.jsonl" "results/E31_non_discount_counterfactual_absolute_verifier"
    ;;
  s6)
    run_abs "$RESOLVED_BACKEND" "S6" "data/processed/s6_lexical_grid_verifier_subset_20260427.jsonl" "results/S6_lexical_grid_absolute_verifier"
    ;;
  e28)
    run_abs "$RESOLVED_BACKEND" "E28" "data/processed/e28_counterfactual_answer_masking_20260427.jsonl" "results/E28_counterfactual_answer_masking_absolute_verifier"
    ;;
  e30)
    run_abs "$RESOLVED_BACKEND" "E30" "data/processed/e30_non_discount_verifier_subset_20260427.jsonl" "results/E30_non_discount_absolute_verifier"
    ;;
  e31)
    run_abs "$RESOLVED_BACKEND" "E31" "data/processed/e31_non_discount_counterfactual_20260427.jsonl" "results/E31_non_discount_counterfactual_absolute_verifier"
    ;;
  *)
    echo "Unknown suite: $SUITE" >&2
    exit 2
    ;;
esac
