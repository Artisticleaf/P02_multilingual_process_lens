#!/usr/bin/env bash
set -euo pipefail

PROJECT=/home/Awei/P02_multilingual_process_lens
CONDA_SH=/home/Awei/miniconda3/etc/profile.d/conda.sh
ENV=passage_prep_py312
PY=/home/Awei/miniconda3/envs/$ENV/bin/python
OUT=$PROJECT/data/raw/e18_targeted_sibling_expansion

mkdir -p "$OUT" "$PROJECT/logs"

launch_one() {
  local session=$1 gpu=$2 model=$3 pypath=$4 chat=$5 maxtok=$6 k=$7 routes=$8 seed=$9
  local log="$PROJECT/logs/${session}.log"
  if tmux has-session -t "$session" 2>/dev/null; then
    echo "session exists: $session"
    return
  fi
  local cmd="cd $PROJECT && source $CONDA_SH && conda activate $ENV && CUDA_VISIBLE_DEVICES=$gpu PYTHONPATH=$pypath $PY scripts/run_trace_pool_generate.py --model-key $model --tasks-yaml configs/e18_targeted_sibling_tasks.yaml --out-dir $OUT --out-suffix e18_${seed} --routes '$routes' --k $k --max-tasks 6 --temperature 0.95 --top-p 0.95 --max-new-tokens $maxtok --chat-template $chat --seed $seed 2>&1 | tee $log"
  tmux new-session -d -s "$session" "$cmd"
  echo "launched $session gpu=$gpu model=$model routes=$routes k=$k max_new=$maxtok -> $log"
}

# The four jobs intentionally occupy all four visible GPUs. The two Qwen jobs
# target the known paper-grade anchors; DeepSeek/Phi are boundary controls.
launch_one p02_e18_qwen3_14b_base 0 qwen3_14b_base "$PROJECT/src" never 512 6 "zh->en,zh->zh,en->zh" 2026042701
launch_one p02_e18_qwen35_9b 1 qwen35_9b "$PROJECT/.deps/hf5:$PROJECT/src" never 512 6 "zh->zh,zh->en,en->en" 2026042702
launch_one p02_e18_deepseek_r1_0528_qwen3_8b 2 deepseek_r1_0528_qwen3_8b "$PROJECT/src" auto 768 3 "zh->zh,zh->en,en->en,en->zh" 2026042703
launch_one p02_e18_phi4_mini_reasoning 3 phi4_mini_reasoning "$PROJECT/src" auto 768 3 "zh->zh,zh->en,en->en,en->zh" 2026042704
