#!/usr/bin/env bash
set -uo pipefail
QUEUE_SESSION="${1:-official_queue_20260428}"
cd /home/Awei/P02_multilingual_process_lens
LOG=logs/official_post_queue_audit_20260428.log
: > "${LOG}"
echo "[post-audit] waiting for ${QUEUE_SESSION}" | tee -a "${LOG}"
while tmux has-session -t "${QUEUE_SESSION}" 2>/dev/null; do
  date -Is | sed 's/^/[post-audit] still waiting /' | tee -a "${LOG}"
  sleep 120
done
source /home/Awei/miniconda3/etc/profile.d/conda.sh
conda activate passage_prep_py312
export PYTHONPATH=/home/Awei/P02_multilingual_process_lens/.deps/hf5:/home/Awei/P02_multilingual_process_lens/src
echo "[post-audit] queue ended; recomputing E48 audit labels and running checks" | tee -a "${LOG}"
python scripts/recompute_e48_process_audit.py 2>&1 | tee -a "${LOG}"
python -m py_compile scripts/*.py 2>&1 | tee -a "${LOG}"
python scripts/audit_e48_e50_official_results.py 2>&1 | tee logs/audit_e48_e50_official_results_after_queue_20260428.log | tee -a "${LOG}"
python scripts/audit_active_official_workspace.py 2>&1 | tee logs/audit_active_official_workspace_after_queue_20260428.log | tee -a "${LOG}"
echo "[post-audit] complete" | tee -a "${LOG}"
