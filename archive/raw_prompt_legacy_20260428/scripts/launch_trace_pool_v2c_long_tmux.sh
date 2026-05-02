#!/usr/bin/env bash
set -euo pipefail
PROJECT=/home/Awei/P02_multilingual_process_lens
PY=/home/Awei/miniconda3/envs/passage_prep_py312/bin/python
mkdir -p "$PROJECT/logs" "$PROJECT/data/raw/trace_pool_smoke_v2c_long"
JOBS=(
  "0 deepseek_r1_0528_qwen3_8b"
  "1 phi4_mini_reasoning"
)
for job in "${JOBS[@]}"; do
  read -r gpu model <<<"$job"
  session="p02_e02_v2c_${model}"
  log="$PROJECT/logs/${session}.log"
  if tmux has-session -t "$session" 2>/dev/null; then
    echo "session exists: $session"
    continue
  fi
  cmd="cd $PROJECT && source /home/Awei/miniconda3/etc/profile.d/conda.sh && conda activate passage_prep_py312 && CUDA_VISIBLE_DEVICES=$gpu PYTHONPATH=$PROJECT/src $PY scripts/run_trace_pool_generate.py --model-key $model --k 1 --max-tasks 8 --max-new-tokens 512 --chat-template auto --out-dir $PROJECT/data/raw/trace_pool_smoke_v2c_long 2>&1 | tee $log"
  tmux new-session -d -s "$session" "$cmd"
  echo "launched $session on GPU $gpu -> $log"
done
