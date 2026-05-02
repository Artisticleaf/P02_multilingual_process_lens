#!/usr/bin/env bash
set -euo pipefail

PROJECT=/home/Awei/P02_multilingual_process_lens
CONDA_SH=/home/Awei/miniconda3/etc/profile.d/conda.sh
ENV_NAME=passage_prep_py312
OUT_DIR="$PROJECT/results/E03_span_patch_hard"

mkdir -p "$PROJECT/logs" "$OUT_DIR"

launch_one() {
  local session=$1
  local gpu=$2
  local model=$3
  local py_path=$4
  local log="$PROJECT/logs/${session}.log"
  tmux new-session -d -s "$session" "bash -lc '
    set -euo pipefail
    cd \"$PROJECT\"
    source \"$CONDA_SH\"
    conda activate \"$ENV_NAME\"
    export CUDA_VISIBLE_DEVICES=\"$gpu\"
    export PYTHONPATH=\"$py_path\"
    python scripts/run_span_patch_smoke.py \
      --model-key \"$model\" \
      --config configs/anchor_hard_smoke.yaml \
      --anchor-result-dir results/E01_anchor_matrix_hard \
      --out-dir \"$OUT_DIR\" \
      --dtype bfloat16 \
      2>&1 | tee \"$log\"
  '"
  echo "launched $session gpu=$gpu model=$model log=$log"
}

launch_one p02_e03_span_qwen3_14b_base 0 qwen3_14b_base "$PROJECT/src"
launch_one p02_e03_span_qwen3_8b_base 1 qwen3_8b_base "$PROJECT/src"
launch_one p02_e03_span_deepseek_r1_0528_qwen3_8b 2 deepseek_r1_0528_qwen3_8b "$PROJECT/src"
launch_one p02_e03_span_qwen35_9b 3 qwen35_9b "$PROJECT/.deps/hf5:$PROJECT/src"

echo "Use: tmux ls; tail -f $PROJECT/logs/p02_e03_span_*.log"
