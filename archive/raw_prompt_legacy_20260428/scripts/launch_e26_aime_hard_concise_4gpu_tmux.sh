#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/Awei/P02_multilingual_process_lens"
ENV_SH="/home/Awei/miniconda3/etc/profile.d/conda.sh"
SESSION="p02_e26_aime_hard_concise"
OUT_DIR="$ROOT/data/raw/e26_aime_hard_trace_pool_concise"
TASKS="$ROOT/configs/e26_aime_hard_tasks.yaml"

mkdir -p "$OUT_DIR" "$ROOT/logs"
tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -n aime0

models=(qwen35_9b qwen3_14b_base deepseek_r1_0528_qwen3_8b phi4_mini_reasoning)
gpus=(0 1 2 3)

for i in "${!models[@]}"; do
  model="${models[$i]}"
  gpu="${gpus[$i]}"
  pane="aime$i"
  if [[ "$i" -gt 0 ]]; then
    tmux new-window -t "$SESSION" -n "$pane"
  else
    tmux rename-window -t "$SESSION:0" "$pane"
  fi
  tmux send-keys -t "$SESSION:$pane" "cd '$ROOT' && source '$ENV_SH' && conda activate passage_prep_py312 && export PYTHONPATH='$ROOT/.deps/hf5:$ROOT/src' && CUDA_VISIBLE_DEVICES=$gpu python scripts/run_trace_pool_generate.py --model-key $model --tasks-yaml '$TASKS' --out-dir '$OUT_DIR' --k 1 --max-tasks 3 --routes 'en->en,zh->en' --max-new-tokens 768 --temperature 0.2 --top-p 0.9 --seed 2026042708 --prompt-style concise --out-suffix aime_hard_concise 2>&1 | tee 'logs/E26_${model}_aime_hard_concise.log'" C-m
done

echo "launched tmux session $SESSION"
echo "watch: tmux attach -t $SESSION"
