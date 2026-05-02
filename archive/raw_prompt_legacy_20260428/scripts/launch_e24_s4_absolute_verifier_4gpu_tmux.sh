#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/Awei/P02_multilingual_process_lens"
ENV_SH="/home/Awei/miniconda3/etc/profile.d/conda.sh"
SESSION="p02_e24_abs_verifier_s4"
OUT_DIR="$ROOT/results/E24_s4_absolute_verifier_combined"
MANUAL="$ROOT/data/processed/manual_e05_plus_e18_targeted_20260427.jsonl"

mkdir -p "$OUT_DIR" "$ROOT/logs"
tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -n abs0

models=(qwen35_9b qwen3_14b_base deepseek_r1_0528_qwen3_8b phi4_mini_reasoning)
gpus=(0 1 2 3)

for i in "${!models[@]}"; do
  model="${models[$i]}"
  gpu="${gpus[$i]}"
  pane="abs$i"
  if [[ "$i" -gt 0 ]]; then
    tmux new-window -t "$SESSION" -n "$pane"
  else
    tmux rename-window -t "$SESSION:0" "$pane"
  fi
  tmux send-keys -t "$SESSION:$pane" "cd '$ROOT' && source '$ENV_SH' && conda activate passage_prep_py312 && export PYTHONPATH='$ROOT/.deps/hf5:$ROOT/src' && CUDA_VISIBLE_DEVICES=$gpu python scripts/run_manual_trace_verifier.py --model-key $model --manual-jsonl '$MANUAL' --out-dir '$OUT_DIR' --dtype bfloat16 --device cuda 2>&1 | tee 'logs/E24_${model}_combined_abs_verifier.log'" C-m
done

echo "launched tmux session $SESSION"
echo "watch: tmux attach -t $SESSION"
