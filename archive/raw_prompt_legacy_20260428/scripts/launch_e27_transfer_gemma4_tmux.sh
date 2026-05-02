#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/Awei/P02_multilingual_process_lens"
ENV_SH="/home/Awei/miniconda3/etc/profile.d/conda.sh"
SESSION="p02_e27_gemma4_transfer"
MANUAL="data/processed/e27_transfer_probe_manual_subset_20260427.jsonl"
PAIRS="configs/e27_transfer_probe_pairs.yaml"
ABS_OUT="results/E27_transfer_absolute_verifier"
CON_OUT="results/E27_transfer_contrastive_verifier"
GEN_OUT="data/raw/e27_transfer_trace_generation"
GPU="${GPU:-0}"

mkdir -p "$ROOT/logs" "$ROOT/$ABS_OUT" "$ROOT/$CON_OUT" "$ROOT/$GEN_OUT"
tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -n gemma4

cmd="cd '$ROOT' && source '$ENV_SH' && conda activate passage_prep_py312 && export PYTHONPATH='$ROOT/.deps/hf5:$ROOT/src' && CUDA_VISIBLE_DEVICES=$GPU python scripts/run_manual_trace_verifier.py --model-key gemma4_e4b_it --manual-jsonl '$MANUAL' --out-dir '$ABS_OUT' --dtype bfloat16 --device cuda 2>&1 | tee 'logs/E27_gemma4_e4b_it_transfer_abs.log'; CUDA_VISIBLE_DEVICES=$GPU python scripts/run_contrastive_acpi_verifier_smoke.py --model-key gemma4_e4b_it --manual-jsonl '$MANUAL' --pairs-yaml '$PAIRS' --out-dir '$CON_OUT' --dtype bfloat16 --device cuda 2>&1 | tee 'logs/E27_gemma4_e4b_it_transfer_contrastive.log'; CUDA_VISIBLE_DEVICES=$GPU python scripts/run_trace_pool_generate.py --model-key gemma4_e4b_it --out-dir '$GEN_OUT' --k 1 --max-tasks 6 --routes 'zh->en' --max-new-tokens 384 --temperature 0.2 --top-p 0.9 --prompt-style concise --device cuda --out-suffix transfer_zh_en 2>&1 | tee 'logs/E27_gemma4_e4b_it_trace_generation.log'"

tmux send-keys -t "$SESSION:gemma4" "$cmd" C-m

echo "launched tmux session $SESSION on GPU=$GPU"
echo "watch: tmux attach -t $SESSION"
