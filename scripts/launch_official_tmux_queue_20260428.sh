#!/usr/bin/env bash
# Sequential four-GPU official experiment queue.  Do not launch a second four-GPU
# queue at the same time; this session intentionally owns GPUs 0,1,2,3.
set -euo pipefail

SESSION="${1:-official_queue_20260428}"
cd /home/Awei/P02_multilingual_process_lens

if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "tmux session already exists: ${SESSION}"
  echo "Attach: tmux attach -t ${SESSION}"
  exit 0
fi

tmux new-session -d -s "${SESSION}" bash -lc '
  set -uo pipefail
  cd /home/Awei/P02_multilingual_process_lens
  source /home/Awei/miniconda3/etc/profile.d/conda.sh
  conda activate passage_prep_py312
  export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
  export PYTHONDONTWRITEBYTECODE=1
  export CUDA_VISIBLE_DEVICES=0,1,2,3
  export MPLENS_MAX_MEMORY="0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB"
  export VLLM_WORKER_MULTIPROC_METHOD=spawn
  mkdir -p logs
  QUEUE_LOG="logs/official_queue_20260428.log"
  STATUS_JSON="logs/official_queue_status_20260428.jsonl"
  : > "${QUEUE_LOG}"
  : > "${STATUS_JSON}"

  run_job() {
    local name="$1"
    local log_file="$2"
    shift 2
    echo "[$(date -Is)] START ${name}" | tee -a "${QUEUE_LOG}"
    "$@" 2>&1 | tee "${log_file}"
    local status=${PIPESTATUS[0]}
    echo "{\"time\":\"$(date -Is)\",\"job\":\"${name}\",\"status\":${status},\"log\":\"${log_file}\"}" >> "${STATUS_JSON}"
    echo "[$(date -Is)] END ${name} status=${status}" | tee -a "${QUEUE_LOG}"
    nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tee -a "${QUEUE_LOG}" || true
    sleep 10
    return 0
  }

  run_job e48_qwen35_9b_hf4 logs/e48_qwen35_9b_hf4_queue_20260428.log \
    python scripts/run_e48_natural_prevalence_official.py \
      --model-key qwen35_9b --device auto --dtype bfloat16 \
      --variants neutral timed_exam answer_first_no_gold bilingual_check \
      --k 2 --max-tasks 12 --batch-size 8 --max-new-tokens 512

  run_job e48_gemma4_31b_it_hf4 logs/e48_gemma4_31b_it_hf4_queue_20260428.log \
    python scripts/run_e48_natural_prevalence_official.py \
      --model-key gemma4_31b_it --device auto --dtype bfloat16 \
      --variants neutral timed_exam answer_first_no_gold bilingual_check \
      --k 2 --max-tasks 12 --batch-size 2 --max-new-tokens 512

  run_job e49_qwen35_27b_answer_anchor_hf4 logs/e49_qwen35_27b_answer_anchor_hf4_queue_20260428.log \
    python scripts/run_e49_hard_task_conditioning_official.py \
      --model-key qwen35_27b --device auto --dtype bfloat16 \
      --variants answer_anchor --k 1 --max-tasks 6 --batch-size 6 --max-new-tokens 2048

  run_job e49_gemma4_26b_a4b_it_nogold_hf4 logs/e49_gemma4_26b_a4b_it_nogold_hf4_queue_20260428.log \
    python scripts/run_e49_hard_task_conditioning_official.py \
      --model-key gemma4_26b_a4b_it --device auto --dtype bfloat16 \
      --variants neutral answer_first_no_gold self_check \
      --k 1 --max-tasks 6 --batch-size 3 --max-new-tokens 2048

  run_job e49_gemma4_26b_a4b_it_answer_anchor_hf4 logs/e49_gemma4_26b_a4b_it_answer_anchor_hf4_queue_20260428.log \
    python scripts/run_e49_hard_task_conditioning_official.py \
      --model-key gemma4_26b_a4b_it --device auto --dtype bfloat16 \
      --variants answer_anchor --k 1 --max-tasks 6 --batch-size 3 --max-new-tokens 2048

  run_job e50_qwen3_14b_base_hf4 logs/e50_qwen3_14b_base_hf4_queue_20260428.log \
    python scripts/run_e50_residual_probe_steering.py \
      --model-key qwen3_14b_base --device auto --dtype bfloat16 \
      --layers 4 8 12 16 20 24 28 32 36 39 \
      --steer-layers 12 20 28 36 --max-model-len 6144

  run_job e48_qwen3_14b_base_vllm4 logs/e48_qwen3_14b_base_vllm4_queue_20260428.log \
    python scripts/run_official_generation_vllm.py \
      --mode e48 --model-key qwen3_14b_base \
      --tensor-parallel-size 4 --gpu-memory-utilization 0.88 \
      --max-model-len 8192 --max-new-tokens 512 --k 2 --max-tasks 12

  run_job e49_qwen25_math_7b_instruct_vllm4 logs/e49_qwen25_math_7b_instruct_vllm4_queue_20260428.log \
    python scripts/run_official_generation_vllm.py \
      --mode e49 --model-key qwen25_math_7b_instruct \
      --variants neutral answer_first_no_gold self_check \
      --tensor-parallel-size 4 --gpu-memory-utilization 0.88 \
      --max-model-len 4096 --max-new-tokens 1536 --k 2 --max-tasks 6

  echo "[$(date -Is)] RUN FINAL AUDITS" | tee -a "${QUEUE_LOG}"
  python scripts/audit_e48_e50_official_results.py 2>&1 | tee logs/audit_e48_e50_official_results_after_queue_20260428.log || true
  python scripts/audit_active_official_workspace.py 2>&1 | tee logs/audit_active_official_workspace_after_queue_20260428.log || true
  echo "[$(date -Is)] QUEUE COMPLETE" | tee -a "${QUEUE_LOG}"
'

echo "Started tmux session: ${SESSION}"
echo "Attach: tmux attach -t ${SESSION}"
echo "Queue log: tail -f /home/Awei/P02_multilingual_process_lens/logs/official_queue_20260428.log"
