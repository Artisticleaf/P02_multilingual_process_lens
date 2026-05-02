#!/usr/bin/env bash
set -euo pipefail
# Optional remote P0 downloads. Use a mirror by passing HF_ENDPOINT, for example:
# HF_ENDPOINT=https://hf-mirror.com bash scripts/plan_remote_downloads.sh qwen35_9b
PROJECT=/home/Awei/P02_multilingual_process_lens
PY=/home/Awei/miniconda3/envs/passage_prep_py312/bin/python
DEST=/home/Awei/LLM/Model/base
if ! command -v huggingface-cli >/dev/null 2>&1; then
  echo "huggingface-cli not found in shell; try conda activate passage_prep_py312" >&2
fi
models=("$@")
if (( ${#models[@]} == 0 )); then
  models=(qwen35_9b ministral3_8b_reasoning gemma4_e4b_it phi4_mini_reasoning glm46v_flash)
fi
for key in "${models[@]}"; do
  repo=$(KEY="$key" $PY - <<'PY'
import os, yaml
project='/home/Awei/P02_multilingual_process_lens'
reg=yaml.safe_load(open(f'{project}/configs/model_registry.yaml'))['models']
print(reg[os.environ['KEY']]['path'])
PY
)
  local_dir="$DEST/${repo//\//__}"
  echo "Would download $key: $repo -> $local_dir"
  echo "Command: HF_ENDPOINT=${HF_ENDPOINT:-https://huggingface.co} huggingface-cli download $repo --local-dir $local_dir --local-dir-use-symlinks False"
done
