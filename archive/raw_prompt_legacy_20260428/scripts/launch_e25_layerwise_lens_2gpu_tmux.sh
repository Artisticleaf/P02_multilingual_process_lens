#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/Awei/P02_multilingual_process_lens"
ENV_SH="/home/Awei/miniconda3/etc/profile.d/conda.sh"
SESSION="p02_e25_layerwise_lens"
OUT_DIR="$ROOT/results/E25_layerwise_verifier_lens"
MANUAL="$ROOT/data/processed/manual_e05_plus_e18_targeted_20260427.jsonl"

mkdir -p "$OUT_DIR" "$ROOT/logs"
tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -n qwen35

tmux send-keys -t "$SESSION:qwen35" "cd '$ROOT' && source '$ENV_SH' && conda activate passage_prep_py312 && export PYTHONPATH='$ROOT/.deps/hf5:$ROOT/src' && CUDA_VISIBLE_DEVICES=0 python scripts/run_layerwise_verifier_lens.py --model-key qwen35_9b --manual-jsonl '$MANUAL' --out-dir '$OUT_DIR' --dtype bfloat16 --device cuda --prompt-langs en,zh 2>&1 | tee 'logs/E25_qwen35_9b_layerwise_lens.log'" C-m

tmux new-window -t "$SESSION" -n qwen14
tmux send-keys -t "$SESSION:qwen14" "cd '$ROOT' && source '$ENV_SH' && conda activate passage_prep_py312 && export PYTHONPATH='$ROOT/.deps/hf5:$ROOT/src' && CUDA_VISIBLE_DEVICES=1 python scripts/run_layerwise_verifier_lens.py --model-key qwen3_14b_base --manual-jsonl '$MANUAL' --out-dir '$OUT_DIR' --dtype bfloat16 --device cuda --prompt-langs en,zh 2>&1 | tee 'logs/E25_qwen3_14b_base_layerwise_lens.log'" C-m

echo "launched tmux session $SESSION"
echo "watch: tmux attach -t $SESSION"
