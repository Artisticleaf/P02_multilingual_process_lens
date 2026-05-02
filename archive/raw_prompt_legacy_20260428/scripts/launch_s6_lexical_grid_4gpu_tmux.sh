#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/Awei/P02_multilingual_process_lens"
ENV_SH="/home/Awei/miniconda3/etc/profile.d/conda.sh"
SESSION="p02_s6_lexical_grid"
OUT_DIR="$ROOT/data/raw/s6_lexical_grid_trace_pool"
TASKS="$ROOT/configs/s6_lexical_paraphrase_grid.yaml"
mkdir -p "$OUT_DIR" "$ROOT/logs"

tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -n gen0

models=(qwen35_9b qwen3_14b_base gemma4_e4b_it deepseek_r1_0528_qwen3_8b)
gpus=(0 1 2 3)

for i in "${!models[@]}"; do
  model="${models[$i]}"
  gpu="${gpus[$i]}"
  pane="gen$i"
  if [[ "$i" -gt 0 ]]; then
    tmux new-window -t "$SESSION" -n "$pane"
  else
    tmux rename-window -t "$SESSION:0" "$pane"
  fi
  tmux send-keys -t "$SESSION:$pane" "cd '$ROOT' && source '$ENV_SH' && conda activate passage_prep_py312 && export PYTHONPATH='$ROOT/.deps/hf5:$ROOT/src' && CUDA_VISIBLE_DEVICES=$gpu python scripts/run_trace_pool_generate.py --model-key $model --tasks-yaml '$TASKS' --out-dir '$OUT_DIR' --k 2 --max-tasks 12 --routes 'zh->zh,zh->en' --max-new-tokens 320 --temperature 0.85 --top-p 0.95 --seed 2026042716 --prompt-style concise --out-suffix s6_lexical_grid 2>&1 | tee 'logs/S6_${model}_lexical_grid.log'" C-m
done

echo "launched tmux session $SESSION"
echo "watch: tmux attach -t $SESSION"
