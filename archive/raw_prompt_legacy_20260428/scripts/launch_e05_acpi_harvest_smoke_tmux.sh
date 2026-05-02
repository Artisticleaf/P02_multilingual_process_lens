#!/usr/bin/env bash
set -euo pipefail
PROJECT=/home/Awei/P02_multilingual_process_lens
CONDA_SH=/home/Awei/miniconda3/etc/profile.d/conda.sh
ENV=passage_prep_py312
OUT=$PROJECT/data/raw/e05_acpi_harvest_smoke
mkdir -p "$OUT" "$PROJECT/logs"
launch_one(){
  local session=$1 gpu=$2 model=$3 pypath=$4 chat=$5 maxtok=$6
  local log="$PROJECT/logs/${session}.log"
  tmux new-session -d -s "$session" "bash -lc 'set -euo pipefail; cd $PROJECT; source $CONDA_SH; conda activate $ENV; export CUDA_VISIBLE_DEVICES=$gpu; export PYTHONPATH=$pypath; python scripts/run_trace_pool_generate.py --model-key $model --tasks-yaml configs/e05_acpi_tasks.yaml --out-dir $OUT --k 2 --max-tasks 14 --temperature 0.9 --top-p 0.95 --max-new-tokens $maxtok --chat-template $chat 2>&1 | tee $log'"
  echo "launched $session gpu=$gpu model=$model chat=$chat max_new=$maxtok"
}
launch_one p02_e05_harvest_qwen3_14b_base 0 qwen3_14b_base "$PROJECT/src" never 512
launch_one p02_e05_harvest_qwen35_9b 1 qwen35_9b "$PROJECT/.deps/hf5:$PROJECT/src" never 512
launch_one p02_e05_harvest_deepseek_r1_0528_qwen3_8b 2 deepseek_r1_0528_qwen3_8b "$PROJECT/src" auto 768
launch_one p02_e05_harvest_phi4_mini_reasoning 3 phi4_mini_reasoning "$PROJECT/src" auto 768
