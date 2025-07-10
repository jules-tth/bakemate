#!/usr/bin/env bash

# Simple startup script for the BakeMate backend.
# Starts the FastAPI server in the background and writes output to a log file.

LOG_DIR="app_files/logs"
LOG_FILE="$LOG_DIR/backend.log"
VENV_DIR=".venv"
APP_ENGINE="${VENV_DIR}/bin/uvicorn"

mkdir -p "$LOG_DIR"

# Run the application in the background with nohup so it keeps running
# after the shell exits. Redirect stdout and stderr to the log file.
if [ ! -f "${APP_ENGINE}" ]; then
	echo "App Engine: ${APP_ENGINE} missing, please run 'make setup' to setup python venv"
	exit 1
fi
nohup ${VENV_DIR}/bin/uvicorn main:app --host 0.0.0.0 --port 8000 > "$LOG_FILE" 2>&1 &

# Optionally store the PID so the service can be managed later.
echo $! > "$LOG_DIR/backend.pid"

echo "Backend started with PID $(cat $LOG_DIR/backend.pid). Logs: $LOG_FILE"

