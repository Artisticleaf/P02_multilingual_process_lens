#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
export MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:160GiB'
export CUDA_VISIBLE_DEVICES=0,1,2,3

STATUS=logs/e153_phaseA_status_20260501.jsonl
: > "$STATUS"

ts() { date --iso-8601=seconds; }
record() {
  printf '{"status":"%s","step":"%s","ts":"%s"}\n' "$1" "$2" "$(ts)" >> "$STATUS"
}

record start e153_build_bank
python scripts/build_e153_difficult_scenario_bank.py 2>&1 | tee logs/e153_build_bank_20260501.log
record done e153_build_bank

record start e153_scaffold_smoke
python scripts/smoke_e153_e158_scaffold.py 2>&1 | tee logs/e153_scaffold_smoke_20260501.log
record done e153_scaffold_smoke

run_gen_model() {
  local model="$1"
  record start "e153_generation_${model}"
  python scripts/run_e153_nonthinking_difficult_scenario_generation.py \
    --model-key "$model" \
    --out-dir results/E153_nonthinking_difficult_scenario_generation \
    --variants solve_neutral solve_terse solve_self_check \
    --k 1 \
    --max-new-tokens 4096 \
    --batch-size 2 \
    --temperature 0.7 \
    --top-p 0.95 \
    --top-k 50 \
    --checkpoint-jsonl "logs/e153_generation_${model}_k1_checkpoint_20260501.jsonl" \
    2>&1 | tee "logs/e153_generation_${model}_k1_20260501.log"
  record done "e153_generation_${model}"
}

run_error_model() {
  local model="$1"
  record start "e153_error_finding_${model}"
  python scripts/run_e153_nonthinking_error_finding.py \
    --model-key "$model" \
    --out-dir results/E153_nonthinking_error_finding \
    --variants find_problem_global find_problem_localize_only \
    --max-new-tokens 512 \
    --batch-size 1 \
    --temperature 0.0 \
    --checkpoint-jsonl "logs/e153_error_finding_${model}_checkpoint_20260501.jsonl" \
    2>&1 | tee "logs/e153_error_finding_${model}_20260501.log"
  record done "e153_error_finding_${model}"
}

run_gen_model qwen35_27b
run_gen_model gemma4_31b_it
run_gen_model gemma4_26b_a4b_it

run_error_model qwen35_27b
run_error_model gemma4_31b_it
run_error_model gemma4_26b_a4b_it

record all_done all

