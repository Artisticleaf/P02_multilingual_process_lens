#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/Awei/P02_multilingual_process_lens"
ENV_SH="/home/Awei/miniconda3/etc/profile.d/conda.sh"
SESSION="p02_e27_qwen27_transfer_auto"
MANUAL="data/processed/e27_transfer_probe_manual_subset_20260427.jsonl"
PAIRS="configs/e27_transfer_probe_pairs.yaml"
ABS_OUT="results/E27_transfer_absolute_verifier"
CON_OUT="results/E27_transfer_contrastive_verifier"
GEN_OUT="data/raw/e27_transfer_trace_generation"

mkdir -p "$ROOT/logs" "$ROOT/$ABS_OUT" "$ROOT/$CON_OUT" "$ROOT/$GEN_OUT"
tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -n qwen27_auto

cmd="cd '$ROOT' && source '$ENV_SH' && conda activate passage_prep_py312 && export PYTHONPATH='$ROOT/.deps/hf5:$ROOT/src' && export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB' && python scripts/run_manual_trace_verifier.py --model-key qwen35_27b --manual-jsonl '$MANUAL' --out-dir '$ABS_OUT' --dtype bfloat16 --device auto 2>&1 | tee 'logs/E27_qwen35_27b_transfer_abs.log'; python scripts/run_contrastive_acpi_verifier_smoke.py --model-key qwen35_27b --manual-jsonl '$MANUAL' --pairs-yaml '$PAIRS' --out-dir '$CON_OUT' --dtype bfloat16 --device auto 2>&1 | tee 'logs/E27_qwen35_27b_transfer_contrastive.log'; python scripts/run_trace_pool_generate.py --model-key qwen35_27b --out-dir '$GEN_OUT' --k 1 --max-tasks 6 --routes 'zh->en' --max-new-tokens 1024 --temperature 0.2 --top-p 0.9 --prompt-style concise --device auto --out-suffix transfer_zh_en 2>&1 | tee 'logs/E27_qwen35_27b_trace_generation_auto.log'"

tmux send-keys -t "$SESSION:qwen27_auto" "$cmd" C-m

echo "launched tmux session $SESSION"
echo "watch: tmux attach -t $SESSION"
