#!/usr/bin/env bash
set -u -o pipefail

PROJECT=/home/Awei/P02_multilingual_process_lens
BASE=/home/Awei/LLM/Model/base
LOG_DIR="$PROJECT/logs"
STATUS="$LOG_DIR/p0_candidate_download_status_20260428.jsonl"
mkdir -p "$LOG_DIR" "$BASE"

source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312

download_one() {
  local repo="$1"
  local local_dir="$2"
  local key="$3"
  mkdir -p "$local_dir"
  echo "{\"event\":\"start\",\"model_key\":\"$key\",\"repo\":\"$repo\",\"local_dir\":\"$local_dir\",\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"

  local mirror_rc=1
  for attempt in 1 2 3; do
    echo "[$(date --iso-8601=seconds)] mirror attempt $attempt/3: $repo -> $local_dir"
    HF_ENDPOINT=https://hf-mirror.com huggingface-cli download "$repo" \
      --local-dir "$local_dir" \
      --resume-download \
      --max-workers 8
    mirror_rc=$?
    echo "{\"event\":\"mirror_done\",\"attempt\":$attempt,\"model_key\":\"$key\",\"repo\":\"$repo\",\"rc\":$mirror_rc,\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
    if [[ $mirror_rc -eq 0 ]]; then
      echo "{\"event\":\"done\",\"source\":\"hf-mirror\",\"model_key\":\"$key\",\"repo\":\"$repo\",\"local_dir\":\"$local_dir\",\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
      return 0
    fi
    sleep 10
  done

  echo "[$(date --iso-8601=seconds)] mirror failed; trying original Hugging Face: $repo"
  unset HF_ENDPOINT
  local hf_rc=1
  for attempt in 1 2 3; do
    echo "[$(date --iso-8601=seconds)] hf attempt $attempt/3: $repo -> $local_dir"
    huggingface-cli download "$repo" \
      --local-dir "$local_dir" \
      --resume-download \
      --max-workers 8
    hf_rc=$?
    echo "{\"event\":\"hf_done\",\"attempt\":$attempt,\"model_key\":\"$key\",\"repo\":\"$repo\",\"rc\":$hf_rc,\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
    if [[ $hf_rc -eq 0 ]]; then
      echo "{\"event\":\"done\",\"source\":\"huggingface\",\"model_key\":\"$key\",\"repo\":\"$repo\",\"local_dir\":\"$local_dir\",\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
      return 0
    fi
    sleep 10
  done

  echo "{\"event\":\"failed\",\"model_key\":\"$key\",\"repo\":\"$repo\",\"local_dir\":\"$local_dir\",\"mirror_rc\":$mirror_rc,\"hf_rc\":$hf_rc,\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
  return $hf_rc
}

download_one "nvidia/Nemotron-Cascade-2-30B-A3B" "$BASE/nemotron_cascade2_30b_a3b" "nemotron_cascade2_30b_a3b_candidate"
download_one "zai-org/GLM-4.7-Flash" "$BASE/glm47_flash" "glm47_flash_candidate"
download_one "LGAI-EXAONE/EXAONE-4.5-33B" "$BASE/exaone45_33b" "exaone45_33b_candidate"

echo "{\"event\":\"all_done\",\"ts\":\"$(date --iso-8601=seconds)\"}" >> "$STATUS"
