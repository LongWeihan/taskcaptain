#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PRODUCTS_UI_PORT:-8765}"
HOST="${PRODUCTS_UI_HOST:-127.0.0.1}"
LOG_DIR="$PWD/logs"
LOG_FILE="${LOG_DIR}/server.log"
mkdir -p "${LOG_DIR}" "$PWD/workspace" "$PWD/data/products" "$PWD/data/trash" "$PWD/data/claw-profiles" "$PWD/runs"
PID="$(ss -ltnp 2>/dev/null | awk -v p=":${PORT}" '$4 ~ p {print $NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | head -n1 || true)"

if [[ -n "${PID}" ]]; then
  echo "taskcaptain is already running on http://${HOST}:${PORT} (pid ${PID})"
  echo "log: ${LOG_FILE}"
  echo "If you want to restart it: ./restart.sh"
  exit 0
fi

nohup python3 app/server.py >>"${LOG_FILE}" 2>&1 &
NEW_PID=$!
sleep 1
if ss -ltnp 2>/dev/null | grep -q ":${PORT}"; then
  echo "taskcaptain started on http://${HOST}:${PORT} (pid ${NEW_PID})"
  echo "log: ${LOG_FILE}"
  exit 0
else
  echo "failed to start taskcaptain; check log: ${LOG_FILE}" >&2
  exit 1
fi
