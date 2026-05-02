#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/Awei/P02_multilingual_process_lens"
ENV_SH="/home/Awei/miniconda3/etc/profile.d/conda.sh"
SESSION="p02_s6_qwen27_verifier_auto"
MANUAL="data/processed/s6_lexical_grid_verifier_subset_20260427.jsonl"
PAIRS="configs/s6_lexical_grid_verifier_pairs.yaml"
ABS_OUT="results/S6_lexical_grid_absolute_verifier_qwen27"
CON_OUT="results/S6_lexical_grid_contrastive_verifier_qwen27"
mkdir -p "$ROOT/logs" "$ROOT/$ABS_OUT" "$ROOT/$CON_OUT"
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session $SESSION already exists" >&2
  exit 1
fi

tmux new-session -d -s "$SESSION" -n qwen27_auto
cmd="cd '$ROOT' && source '$ENV_SH' && conda activate passage_prep_py312 && export PYTHONPATH='$ROOT/.deps/hf5:$ROOT/src' && export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB' && python scripts/run_manual_trace_verifier.py --model-key qwen35_27b --manual-jsonl '$MANUAL' --out-dir '$ABS_OUT' --dtype bfloat16 --device auto 2>&1 | tee 'logs/S6_qwen35_27b_absolute_verifier.log'; python scripts/run_contrastive_acpi_verifier_smoke.py --model-key qwen35_27b --manual-jsonl '$MANUAL' --pairs-yaml '$PAIRS' --out-dir '$CON_OUT' --dtype bfloat16 --device auto 2>&1 | tee 'logs/S6_qwen35_27b_contrastive_verifier.log'"
tmux send-keys -t "$SESSION:qwen27_auto" "$cmd" C-m
echo "launched tmux session $SESSION"
echo "watch: tmux attach -t $SESSION"
