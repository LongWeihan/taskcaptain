#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PRODUCTS_UI_PORT:-8765}"
LOG_DIR="$PWD/logs"
LOG_FILE="${LOG_DIR}/server.log"
mkdir -p "${LOG_DIR}"
PID="$(ss -ltnp 2>/dev/null | awk -v p=":${PORT}" '$4 ~ p {print $NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | head -n1 || true)"
if [[ -n "${PID}" ]]; then
  echo "Stopping existing service on port ${PORT} (pid ${PID})"
  kill "${PID}" || true
  for _ in $(seq 1 20); do
    sleep 0.5
    CUR="$(ss -ltnp 2>/dev/null | awk -v p=":${PORT}" '$4 ~ p {print $NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | head -n1 || true)"
    if [[ -z "${CUR}" ]]; then
      break
    fi
  done
  CUR="$(ss -ltnp 2>/dev/null | awk -v p=":${PORT}" '$4 ~ p {print $NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | head -n1 || true)"
  if [[ -n "${CUR}" ]]; then
    echo "Process still holds port ${PORT}; forcing kill ${CUR}"
    kill -9 "${CUR}" || true
    sleep 1
  fi
fi
: > "${LOG_FILE}"
exec ./run.sh
