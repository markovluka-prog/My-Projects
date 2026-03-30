#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="$SCRIPT_DIR/.runtime"
PID_FILE="$RUNTIME_DIR/agent.pid"
LOG_FILE="$RUNTIME_DIR/agent.log"
AGENT_ENTRY="$SCRIPT_DIR/update_agent.mjs"

mkdir -p "$RUNTIME_DIR"

EXISTING_PID="$(pgrep -f "node $AGENT_ENTRY" | tail -n 1 || true)"
if [[ -n "$EXISTING_PID" ]]; then
  echo "$EXISTING_PID" >"$PID_FILE"
  echo "Agent already running with PID $EXISTING_PID"
  exit 0
fi

cd "$SCRIPT_DIR"
setsid -f bash -lc "exec node \"$AGENT_ENTRY\" >>\"$LOG_FILE\" 2>&1 </dev/null"
sleep 1

PID="$(pgrep -f "node $AGENT_ENTRY" | tail -n 1 || true)"
if [[ -z "$PID" ]]; then
  echo "Failed to detect agent PID after launch" >&2
  exit 1
fi

echo "$PID" >"$PID_FILE"

echo "Agent started with PID $PID"
echo "Log: $LOG_FILE"
