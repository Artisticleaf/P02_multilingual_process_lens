#!/usr/bin/env bash
set -euo pipefail
PROJECT=/home/Awei/P02_multilingual_process_lens
PY=/home/Awei/miniconda3/envs/passage_prep_py312/bin/python
export PYTHONPATH="$PROJECT/src:${PYTHONPATH:-}"
mkdir -p "$PROJECT/logs" "$PROJECT/results/E01_anchor_matrix"
# Qwen3.5-9B and Ministral3 require a newer HF loader; keep them in loader audit for now.
declare -a JOBS=(
  "0 phi4_mini_reasoning"
  "1 glm46v_flash"
)
for job in "${JOBS[@]}"; do
  gpu=${job%% *}
  model=${job#* }
  session="p02_e01_${model}"
  log="$PROJECT/logs/${session}.log"
  if tmux has-session -t "$session" 2>/dev/null; then
    echo "session exists: $session"
    continue
  fi
  cmd="cd $PROJECT && source /home/Awei/miniconda3/etc/profile.d/conda.sh && conda activate passage_prep_py312 && CUDA_VISIBLE_DEVICES=$gpu PYTHONPATH=$PROJECT/src $PY scripts/run_anchor_matrix_smoke.py --model-key $model --out-dir $PROJECT/results/E01_anchor_matrix 2>&1 | tee $log"
  tmux new-session -d -s "$session" "$cmd"
  echo "launched $session on GPU $gpu -> $log"
done
