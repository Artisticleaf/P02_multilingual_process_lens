#!/usr/bin/env bash
# Launch vLLM official generation for compatible CausalLM controls.
# Current Qwen3.5/Gemma4 ConditionalGeneration checkpoints are not supported by
# vLLM 0.12.0 in this environment; use this for standard CausalLM controls such
# as qwen3_14b_base, qwen25_math_7b_instruct, or phi4_mini_reasoning.
set -euo pipefail

MODE="${1:-e48}"
MODEL_KEY="${2:-qwen3_14b_base}"
SESSION="${3:-${MODE}_${MODEL_KEY}_vllm4}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-}"
if [ "${MODEL_KEY}" = "qwen25_math_7b_instruct" ]; then
  # Local Qwen2.5-Math-7B-Instruct config derives max_position_embeddings=4096;
  # vLLM correctly refuses 8192 unless unsafe override is enabled.
  MAX_MODEL_LEN="${MAX_MODEL_LEN:-4096}"
else
  MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
fi

cd /home/Awei/P02_multilingual_process_lens

tmux new-session -d -s "${SESSION}" "
  set -euo pipefail
  source /home/Awei/miniconda3/etc/profile.d/conda.sh
  conda activate passage_prep_py312
  export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
  export PYTHONDONTWRITEBYTECODE=1
  export VLLM_WORKER_MULTIPROC_METHOD=spawn
  export CUDA_VISIBLE_DEVICES=0,1,2,3
  mkdir -p logs
  python scripts/run_official_generation_vllm.py \
    --mode '${MODE}' \
    --model-key '${MODEL_KEY}' \
    --tensor-parallel-size 4 \
    --gpu-memory-utilization 0.88 \
    --max-model-len '${MAX_MODEL_LEN}' \
    --max-new-tokens \$([ '${MODE}' = 'e49' ] && echo 2048 || echo 512) \
    --k \$([ '${MODE}' = 'e49' ] && echo 1 || echo 2) \
    --max-tasks \$([ '${MODE}' = 'e49' ] && echo 6 || echo 12) \
    2>&1 | tee logs/${MODE}_${MODEL_KEY}_vllm4_tmux_20260428.log
"

echo "Started tmux session: ${SESSION}"
echo "Attach: tmux attach -t ${SESSION}"
