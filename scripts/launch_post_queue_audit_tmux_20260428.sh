#!/usr/bin/env bash
set -euo pipefail
QUEUE_SESSION="${1:-official_queue_20260428}"
SESSION="${2:-official_post_audit_20260428}"
cd /home/Awei/P02_multilingual_process_lens
if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "tmux session already exists: ${SESSION}"
  exit 0
fi
tmux new-session -d -s "${SESSION}" "bash /home/Awei/P02_multilingual_process_lens/scripts/post_queue_audit_worker_20260428.sh ${QUEUE_SESSION}"
echo "Started post-audit tmux session: ${SESSION}"
echo "Log: tail -f /home/Awei/P02_multilingual_process_lens/logs/official_post_queue_audit_20260428.log"
