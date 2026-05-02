#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/Awei/P02_multilingual_process_lens"
ENV_SH="/home/Awei/miniconda3/etc/profile.d/conda.sh"
SESSION="p02_e27_model_pull"
BASE="/home/Awei/LLM/Model/base"
mkdir -p "$BASE/qwen35_27b" "$BASE/gemma4_e4b_it" "$ROOT/logs"

tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -n qwen27

tmux send-keys -t "$SESSION:qwen27" "cd '$ROOT' && source '$ENV_SH' && conda activate passage_prep_py312 && export HF_ENDPOINT='https://hf-mirror.com' && huggingface-cli download Qwen/Qwen3.5-27B --local-dir '$BASE/qwen35_27b' --max-workers 16 2>&1 | tee 'logs/E27_qwen35_27b_download.log'" C-m

tmux new-window -t "$SESSION" -n gemma4
tmux send-keys -t "$SESSION:gemma4" "cd '$ROOT' && source '$ENV_SH' && conda activate passage_prep_py312 && export HF_ENDPOINT='https://hf-mirror.com' && huggingface-cli download google/gemma-4-E4B-it --local-dir '$BASE/gemma4_e4b_it' --max-workers 8 2>&1 | tee 'logs/E27_gemma4_e4b_it_download.log'" C-m

echo "launched tmux session $SESSION"
echo "watch: tmux attach -t $SESSION"
