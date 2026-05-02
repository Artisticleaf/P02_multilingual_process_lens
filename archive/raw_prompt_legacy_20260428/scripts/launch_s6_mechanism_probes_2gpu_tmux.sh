#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/Awei/P02_multilingual_process_lens"
SESSION="p02_s6_mechanism_probes"
CONDA="/home/Awei/miniconda3/etc/profile.d/conda.sh"
PYTHONPATH_VALUE="$ROOT/.deps/hf5:$ROOT/src"
MANUAL="$ROOT/data/processed/s6_lexical_grid_verifier_subset_20260427.jsonl"
PAIRS="$ROOT/configs/s6_lexical_grid_span_patch_pairs.yaml"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session $SESSION already exists" >&2
  exit 1
fi

run_cmd() {
  local gpu="$1"; shift
  local name="$1"; shift
  local cmd="$*"
  tmux new-window -t "$SESSION" -n "$name" "cd '$ROOT' && source '$CONDA' && conda activate passage_prep_py312 && export PYTHONPATH='$PYTHONPATH_VALUE' && CUDA_VISIBLE_DEVICES=$gpu $cmd; echo; echo '[done] $name'; exec bash"
}

tmux new-session -d -s "$SESSION" -n qwen14_patch "cd '$ROOT' && source '$CONDA' && conda activate passage_prep_py312 && export PYTHONPATH='$PYTHONPATH_VALUE' && CUDA_VISIBLE_DEVICES=0 python scripts/run_real_acpi_span_patch_smoke.py --model-key qwen3_14b_base --manual-jsonl '$MANUAL' --pairs-yaml '$PAIRS' --out-dir '$ROOT/results/S6_lexical_grid_span_patch' --layers 9,14,20,25,30 --spans support_error_span,trace_span,final_answer_span 2>&1 | tee '$ROOT/logs/S6_qwen14_span_patch.log'; echo; echo '[done] qwen14_patch'; exec bash"
run_cmd 1 gemma4_patch "python scripts/run_real_acpi_span_patch_smoke.py --model-key gemma4_e4b_it --manual-jsonl '$MANUAL' --pairs-yaml '$PAIRS' --out-dir '$ROOT/results/S6_lexical_grid_span_patch' --layers 8,14,20,28,36 --spans support_error_span,trace_span,final_answer_span 2>&1 | tee '$ROOT/logs/S6_gemma4_span_patch.log'"
run_cmd 2 qwen14_lens "python scripts/run_layerwise_verifier_lens.py --model-key qwen3_14b_base --manual-jsonl '$MANUAL' --pairs-yaml '$PAIRS' --out-dir '$ROOT/results/S6_lexical_grid_layerwise_lens' --prompt-langs en,zh --max-len 4096 2>&1 | tee '$ROOT/logs/S6_qwen14_layerwise_lens.log'"
run_cmd 3 gemma4_lens "python scripts/run_layerwise_verifier_lens.py --model-key gemma4_e4b_it --manual-jsonl '$MANUAL' --pairs-yaml '$PAIRS' --out-dir '$ROOT/results/S6_lexical_grid_layerwise_lens' --prompt-langs en,zh --max-len 4096 2>&1 | tee '$ROOT/logs/S6_gemma4_layerwise_lens.log'"

echo "launched tmux session $SESSION"
tmux ls | grep "$SESSION" || true
