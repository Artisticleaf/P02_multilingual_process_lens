#!/usr/bin/env bash
set -euo pipefail
PROJECT=/home/Awei/P02_multilingual_process_lens
PY=/home/Awei/miniconda3/envs/passage_prep_py312/bin/python
export PYTHONPATH="$PROJECT/src:${PYTHONPATH:-}"
mkdir -p "$PROJECT/logs" "$PROJECT/results/E01_anchor_matrix"
session="p02_e01_qwen3_14b_base"
log="$PROJECT/logs/${session}.log"
if tmux has-session -t "$session" 2>/dev/null; then
  echo "session exists: $session"
  exit 0
fi
cmd="cd $PROJECT && source /home/Awei/miniconda3/etc/profile.d/conda.sh && conda activate passage_prep_py312 && CUDA_VISIBLE_DEVICES=0 PYTHONPATH=$PROJECT/src $PY scripts/run_anchor_matrix_smoke.py --model-key qwen3_14b_base --out-dir $PROJECT/results/E01_anchor_matrix 2>&1 | tee $log"
tmux new-session -d -s "$session" "$cmd"
echo "launched $session -> $log"
