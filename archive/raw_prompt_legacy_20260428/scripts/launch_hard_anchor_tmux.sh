#!/usr/bin/env bash
set -euo pipefail
PROJECT=/home/Awei/P02_multilingual_process_lens
PY=/home/Awei/miniconda3/envs/passage_prep_py312/bin/python
mkdir -p "$PROJECT/logs" "$PROJECT/results/E01_anchor_matrix_hard"
# gpu model PYTHONPATH
JOBS=(
  "0 qwen3_14b_base $PROJECT/src"
  "1 qwen3_8b_base $PROJECT/src"
  "2 deepseek_r1_0528_qwen3_8b $PROJECT/src"
  "3 qwen35_9b $PROJECT/.deps/hf5:$PROJECT/src"
)
for job in "${JOBS[@]}"; do
  read -r gpu model pypath <<<"$job"
  session="p02_e01_hard_${model}"
  log="$PROJECT/logs/${session}.log"
  if tmux has-session -t "$session" 2>/dev/null; then
    echo "session exists: $session"
    continue
  fi
  cmd="cd $PROJECT && source /home/Awei/miniconda3/etc/profile.d/conda.sh && conda activate passage_prep_py312 && CUDA_VISIBLE_DEVICES=$gpu PYTHONPATH=$pypath $PY scripts/run_anchor_matrix_smoke.py --model-key $model --config $PROJECT/configs/anchor_hard_smoke.yaml --out-dir $PROJECT/results/E01_anchor_matrix_hard 2>&1 | tee $log"
  tmux new-session -d -s "$session" "$cmd"
  echo "launched $session on GPU $gpu -> $log"
done
