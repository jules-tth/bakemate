#!/usr/bin/env bash
#
# BakeMate backend startup script
# ───────────────────────────────
# • Honors environment overrides (HOST, PORT, APP_MODULE, LOG_DIR, VENV_DIR)
# • Refuses to launch if an instance is already running
# • Falls back to system-wide uvicorn if venv binary missing
# • Logs stdout/stderr to rotating file (via logrotate snippet hint)

set -euo pipefail

# ───────── Config ─────────
APP_MODULE=${APP_MODULE:-main:app}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
LOG_DIR=${LOG_DIR:-app_files/logs}
PID_FILE="$LOG_DIR/backend.pid"
LOG_FILE="$LOG_DIR/backend.log"
VENV_DIR=${VENV_DIR:-.venv}
APP_ENGINE="$VENV_DIR/bin/uvicorn"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p "$LOG_DIR"

# ───────── Safety checks ─────────
if [[ -f "$PID_FILE" ]]; then
  RUNNING_PID=$(cat "$PID_FILE")
  if kill -0 "$RUNNING_PID" 2>/dev/null; then
    echo "⚠️  BakeMate backend is already running (PID $RUNNING_PID)."
    echo "    If this is stale, delete $PID_FILE and retry."
    exit 1
  else
    echo "Stale PID file detected — removing."
    rm -f "$PID_FILE"
  fi
fi

# Prefer venv uvicorn; fall back to global
if [[ ! -x "$APP_ENGINE" ]]; then
  if command -v uvicorn >/dev/null 2>&1; then
    echo "🔍 venv uvicorn not found; falling back to system uvicorn."
    APP_ENGINE=$(command -v uvicorn)
  else
    echo "❌ uvicorn executable not found. Run 'make setup' first."
    exit 1
  fi
fi

# ───────── Launch ─────────
echo "[$DATE] Starting BakeMate backend → $HOST:$PORT"
nohup "$APP_ENGINE" "$APP_MODULE" --host "$HOST" --port "$PORT" \
      >> "$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
sleep 1  # give uvicorn a beat to initialize

if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "✅  Backend started (PID $(cat "$PID_FILE")). Logs → $LOG_FILE"
else
  echo "❌  Backend failed to start. See $LOG_FILE for details."
  rm -f "$PID_FILE"
  exit 1
fi

