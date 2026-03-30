#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.runtime/agent.pid"
AGENT_ENTRY="$SCRIPT_DIR/update_agent.mjs"

if [[ ! -f "$PID_FILE" ]]; then
  EXISTING_PID="$(pgrep -f "node $AGENT_ENTRY" | tail -n 1 || true)"
  if [[ -z "$EXISTING_PID" ]]; then
    echo "Agent is not running"
    exit 0
  fi
  echo "$EXISTING_PID" >"$PID_FILE"
fi

PID="$(cat "$PID_FILE")"
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  for _ in {1..20}; do
    if ! kill -0 "$PID" 2>/dev/null; then
      break
    fi
    sleep 0.2
  done
  if kill -0 "$PID" 2>/dev/null; then
    kill -9 "$PID"
  fi
  echo "Agent stopped: $PID"
else
  FALLBACK_PID="$(pgrep -f "node $AGENT_ENTRY" | tail -n 1 || true)"
  if [[ -n "$FALLBACK_PID" ]]; then
    kill "$FALLBACK_PID"
    for _ in {1..20}; do
      if ! kill -0 "$FALLBACK_PID" 2>/dev/null; then
        break
      fi
      sleep 0.2
    done
    if kill -0 "$FALLBACK_PID" 2>/dev/null; then
      kill -9 "$FALLBACK_PID"
    fi
    echo "Agent stopped: $FALLBACK_PID"
  else
    echo "Agent process not found: $PID"
  fi
fi

rm -f "$PID_FILE"
