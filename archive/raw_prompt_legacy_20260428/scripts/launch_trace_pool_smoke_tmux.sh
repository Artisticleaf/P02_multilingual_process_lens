#!/usr/bin/env bash
set -euo pipefail
PROJECT=/home/Awei/P02_multilingual_process_lens
PY=/home/Awei/miniconda3/envs/passage_prep_py312/bin/python
mkdir -p "$PROJECT/logs" "$PROJECT/data/raw/trace_pool_smoke"
declare -a JOBS=(
  "0 qwen3_8b_base"
  "1 deepseek_r1_0528_qwen3_8b"
  "2 qwen25_math_7b_instruct"
  "3 llama32_3b"
)
for job in "${JOBS[@]}"; do
  gpu=${job%% *}
  model=${job#* }
  session="p02_e02_trace_${model}"
  log="$PROJECT/logs/${session}.log"
  if tmux has-session -t "$session" 2>/dev/null; then
    echo "session exists: $session"
    continue
  fi
  cmd="cd $PROJECT && source /home/Awei/miniconda3/etc/profile.d/conda.sh && conda activate passage_prep_py312 && CUDA_VISIBLE_DEVICES=$gpu PYTHONPATH=$PROJECT/src $PY scripts/run_trace_pool_generate.py --model-key $model --k 2 --out-dir $PROJECT/data/raw/trace_pool_smoke 2>&1 | tee $log"
  tmux new-session -d -s "$session" "$cmd"
  echo "launched $session on GPU $gpu -> $log"
done
