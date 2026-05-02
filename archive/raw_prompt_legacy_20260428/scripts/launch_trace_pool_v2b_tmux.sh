#!/usr/bin/env bash
set -euo pipefail
PROJECT=/home/Awei/P02_multilingual_process_lens
PY=/home/Awei/miniconda3/envs/passage_prep_py312/bin/python
mkdir -p "$PROJECT/logs" "$PROJECT/data/raw/trace_pool_smoke_v2b"
# Format: gpu model py_path chat_template
JOBS=(
  "0 qwen3_14b_base $PROJECT/src auto"
  "1 deepseek_r1_0528_qwen3_8b $PROJECT/src auto"
  "2 qwen35_9b $PROJECT/.deps/hf5:$PROJECT/src never"
  "3 phi4_mini_reasoning $PROJECT/src auto"
)
for job in "${JOBS[@]}"; do
  read -r gpu model pypath chat <<<"$job"
  session="p02_e02_v2b_${model}"
  log="$PROJECT/logs/${session}.log"
  if tmux has-session -t "$session" 2>/dev/null; then
    echo "session exists: $session"
    continue
  fi
  cmd="cd $PROJECT && source /home/Awei/miniconda3/etc/profile.d/conda.sh && conda activate passage_prep_py312 && CUDA_VISIBLE_DEVICES=$gpu PYTHONPATH=$pypath $PY scripts/run_trace_pool_generate.py --model-key $model --k 1 --max-tasks 8 --max-new-tokens 160 --chat-template $chat --out-dir $PROJECT/data/raw/trace_pool_smoke_v2b 2>&1 | tee $log"
  tmux new-session -d -s "$session" "$cmd"
  echo "launched $session on GPU $gpu chat=$chat -> $log"
done
