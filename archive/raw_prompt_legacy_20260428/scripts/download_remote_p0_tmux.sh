#!/usr/bin/env bash
set -euo pipefail
PROJECT=/home/Awei/P02_multilingual_process_lens
PY=/home/Awei/miniconda3/envs/passage_prep_py312/bin/python
DEST=/home/Awei/LLM/Model/base
ENDPOINT=${HF_ENDPOINT:-https://hf-mirror.com}
mkdir -p "$PROJECT/logs" "$DEST"
models=("$@")
if (( ${#models[@]} == 0 )); then
  # Gemma 4 currently needs a separate AutoProcessor/model-loading check, so keep it out of the first download wave.
  models=(qwen35_9b ministral3_8b_reasoning phi4_mini_reasoning glm46v_flash)
fi
session="p02_download_remote_p0"
log="$PROJECT/logs/${session}.log"
if tmux has-session -t "$session" 2>/dev/null; then
  echo "session exists: $session"
  exit 0
fi
cmd=$(cat <<BASH
set -euo pipefail
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export HF_ENDPOINT="$ENDPOINT"
export HF_HOME=/home/Awei/LLM/Model/hf_cache
cd "$PROJECT"
echo "HF_ENDPOINT=\$HF_ENDPOINT"
for key in ${models[*]}; do
  repo=\$(KEY="\$key" $PY - <<'PY'
import os, yaml
project='/home/Awei/P02_multilingual_process_lens'
reg=yaml.safe_load(open(f'{project}/configs/model_registry.yaml'))['models']
print(reg[os.environ['KEY']]['path'])
PY
)
  local_dir="$DEST/\$key"
  echo "[\$(date --iso-8601=seconds)] downloading \$key: \$repo -> \$local_dir"
  huggingface-cli download "\$repo" --local-dir "\$local_dir"
  echo "[\$(date --iso-8601=seconds)] done \$key"
done
BASH
)
tmux new-session -d -s "$session" "$cmd 2>&1 | tee '$log'"
echo "launched $session -> $log"
