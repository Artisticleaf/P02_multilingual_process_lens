#!/usr/bin/env bash
set -euo pipefail

cd /home/Awei/P02_multilingual_process_lens
mkdir -p logs
LOG=logs/e170_after_e167_watcher_20260502.log

ts() { date --iso-8601=seconds; }
echo "===== START e170_after_e167_watcher $(ts) =====" | tee "$LOG"
while tmux has-session -t e167_hidden_derived_20260502 2>/dev/null; do
  echo "$(ts) waiting for e167_hidden_derived_20260502 to finish" | tee -a "$LOG"
  sleep 300
done
echo "$(ts) e167 session finished; launching E170 thinking-only queue" | tee -a "$LOG"
bash scripts/launch_e170_thinking_only_after_e167_20260502.sh 2>&1 | tee -a "$LOG"
echo "===== END e170_after_e167_watcher $(ts) =====" | tee -a "$LOG"
