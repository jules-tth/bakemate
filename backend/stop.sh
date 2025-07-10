#!/usr/bin/env bash
#
# Gracefully stop the BakeMate backend that was launched by startup.sh.
# Looks for the stored PID first; falls back to pgrep if the pidfile is missing.

LOG_DIR="app_files/logs"
PID_FILE="$LOG_DIR/backend.pid"

if [[ -f "$PID_FILE" ]]; then
  PID=$(cat "$PID_FILE")
  if kill -0 "$PID" 2>/dev/null; then
    echo "Stopping backend (PID $PID)…"
    kill "$PID"
    # Give it a moment to exit
    sleep 2
    if kill -0 "$PID" 2>/dev/null; then
      echo "Process still running—sending SIGKILL."
      kill -9 "$PID"
    fi
    echo "✓ Backend stopped."
    rm -f "$PID_FILE"
    exit 0
  else
    echo "No running process found for PID $PID – removing stale pidfile."
    rm -f "$PID_FILE"
  fi
fi

echo "PID file not found. Attempting to locate uvicorn process…"
# Narrow the search to uvicorn instances serving our app directory
PGREP_PATTERN="uvicorn.*$(pwd | sed 's/[^a-zA-Z0-9]/./g')"
PIDS=$(pgrep -f "$PGREP_PATTERN")

if [[ -n "$PIDS" ]]; then
  echo "Found PIDs: $PIDS – sending SIGTERM."
  kill $PIDS
  exit 0
fi

echo "❗ Nothing to stop. Backend is not running."
exit 1

