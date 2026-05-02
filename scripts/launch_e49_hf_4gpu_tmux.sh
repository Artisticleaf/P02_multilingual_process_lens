#!/usr/bin/env bash
# Launch official E49 hard-task generation in tmux so it survives Codex/SSH drops.
set -euo pipefail

SESSION="${1:-e49_qwen35_27b_hf4}"
cd /home/Awei/P02_multilingual_process_lens

tmux new-session -d -s "${SESSION}" "
  set -euo pipefail
  source /home/Awei/miniconda3/etc/profile.d/conda.sh
  conda activate passage_prep_py312
  export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
  export PYTHONDONTWRITEBYTECODE=1
  export CUDA_VISIBLE_DEVICES=0,1,2,3
  export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
  mkdir -p logs
  python scripts/run_e49_hard_task_conditioning_official.py \
    --model-key qwen35_27b \
    --device auto \
    --dtype bfloat16 \
    --variants neutral answer_first_no_gold self_check \
    --k 1 \
    --max-tasks 6 \
    --batch-size 6 \
    --max-new-tokens 2048 \
    2>&1 | tee logs/e49_qwen35_27b_hf4_tmux_20260428.log
"

echo "Started tmux session: ${SESSION}"
echo "Attach: tmux attach -t ${SESSION}"
echo "Monitor: nvidia-smi dmon -s pucm"
