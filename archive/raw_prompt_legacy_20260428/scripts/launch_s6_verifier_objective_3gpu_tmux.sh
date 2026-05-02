#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/Awei/P02_multilingual_process_lens"
ENV_SH="/home/Awei/miniconda3/etc/profile.d/conda.sh"
SESSION="p02_s6_verifier_objective"
MANUAL="$ROOT/data/processed/s6_lexical_grid_verifier_subset_20260427.jsonl"
PAIRS="$ROOT/configs/s6_lexical_grid_verifier_pairs.yaml"
ABS_OUT="$ROOT/results/S6_lexical_grid_absolute_verifier"
CON_OUT="$ROOT/results/S6_lexical_grid_contrastive_verifier"
mkdir -p "$ABS_OUT" "$CON_OUT" "$ROOT/logs"

tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -n ver0
models=(qwen35_9b qwen3_14b_base gemma4_e4b_it)
gpus=(0 1 2)
for i in "${!models[@]}"; do
  model="${models[$i]}"
  gpu="${gpus[$i]}"
  pane="ver$i"
  if [[ "$i" -gt 0 ]]; then tmux new-window -t "$SESSION" -n "$pane"; else tmux rename-window -t "$SESSION:0" "$pane"; fi
  tmux send-keys -t "$SESSION:$pane" "cd '$ROOT' && source '$ENV_SH' && conda activate passage_prep_py312 && export PYTHONPATH='$ROOT/.deps/hf5:$ROOT/src' && CUDA_VISIBLE_DEVICES=$gpu python scripts/run_manual_trace_verifier.py --model-key $model --manual-jsonl '$MANUAL' --out-dir '$ABS_OUT' --dtype bfloat16 --device cuda 2>&1 | tee 'logs/S6_${model}_absolute_verifier.log'; CUDA_VISIBLE_DEVICES=$gpu python scripts/run_contrastive_acpi_verifier_smoke.py --model-key $model --manual-jsonl '$MANUAL' --pairs-yaml '$PAIRS' --out-dir '$CON_OUT' --dtype bfloat16 --device cuda 2>&1 | tee 'logs/S6_${model}_contrastive_verifier.log'" C-m
done

echo "launched tmux session $SESSION"
echo "watch: tmux attach -t $SESSION"
