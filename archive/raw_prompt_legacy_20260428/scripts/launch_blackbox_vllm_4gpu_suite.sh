#!/usr/bin/env bash
set -euo pipefail

# Unified four-GPU vLLM runner for black-box verifier experiments.
# Usage:
#   scripts/launch_blackbox_vllm_4gpu_suite.sh gemma4_26b_a4b_it core
# Suites:
#   core: s6,e28,e30,e31
#   s6/e28/e30/e31: run one suite
#
# Hidden-state span patch / layerwise / MLP-head experiments should not use
# this script; they need HuggingFace hooks instead of vLLM.

ROOT="/home/Awei/P02_multilingual_process_lens"
ENV_SH="/home/Awei/miniconda3/etc/profile.d/conda.sh"
MODEL_KEY="${1:?model key required}"
SUITE="${2:-core}"
TP="${VLLM_TP:-4}"
GPU_UTIL="${VLLM_GPU_UTIL:-0.88}"
MAX_LEN="${VLLM_MAX_MODEL_LEN:-6144}"
BATCH="${VLLM_BATCH_SIZE:-64}"
DTYPE="${VLLM_DTYPE:-bfloat16}"

run_abs() {
  local tag="$1"
  local manual="$2"
  local out_dir="$3"
  mkdir -p "$ROOT/$out_dir" "$ROOT/logs"
  echo "[vLLM-suite] model=$MODEL_KEY tag=$tag manual=$manual out=$out_dir"
  CUDA_VISIBLE_DEVICES=0,1,2,3 python "$ROOT/scripts/run_manual_trace_verifier_vllm.py" \
    --model-key "$MODEL_KEY" \
    --manual-jsonl "$ROOT/$manual" \
    --out-dir "$ROOT/$out_dir" \
    --dtype "$DTYPE" \
    --tensor-parallel-size "$TP" \
    --gpu-memory-utilization "$GPU_UTIL" \
    --max-model-len "$MAX_LEN" \
    --batch-size "$BATCH" \
    2>&1 | tee "$ROOT/logs/${tag}_${MODEL_KEY}_vllm_abs.log"
}

cd "$ROOT"
source "$ENV_SH"
conda activate passage_prep_py312
export PYTHONPATH="$ROOT/.deps/hf5:$ROOT/src"

case "$SUITE" in
  core)
    run_abs "S6" "data/processed/s6_lexical_grid_verifier_subset_20260427.jsonl" "results/S6_lexical_grid_absolute_verifier_vllm"
    run_abs "E28" "data/processed/e28_counterfactual_answer_masking_20260427.jsonl" "results/E28_counterfactual_answer_masking_absolute_verifier_vllm"
    run_abs "E30" "data/processed/e30_non_discount_verifier_subset_20260427.jsonl" "results/E30_non_discount_absolute_verifier_vllm"
    run_abs "E31" "data/processed/e31_non_discount_counterfactual_20260427.jsonl" "results/E31_non_discount_counterfactual_absolute_verifier_vllm"
    ;;
  s6)
    run_abs "S6" "data/processed/s6_lexical_grid_verifier_subset_20260427.jsonl" "results/S6_lexical_grid_absolute_verifier_vllm"
    ;;
  e28)
    run_abs "E28" "data/processed/e28_counterfactual_answer_masking_20260427.jsonl" "results/E28_counterfactual_answer_masking_absolute_verifier_vllm"
    ;;
  e30)
    run_abs "E30" "data/processed/e30_non_discount_verifier_subset_20260427.jsonl" "results/E30_non_discount_absolute_verifier_vllm"
    ;;
  e31)
    run_abs "E31" "data/processed/e31_non_discount_counterfactual_20260427.jsonl" "results/E31_non_discount_counterfactual_absolute_verifier_vllm"
    ;;
  *)
    echo "Unknown suite: $SUITE" >&2
    exit 2
    ;;
esac
