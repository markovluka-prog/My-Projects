#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_PATH="/etc/init.d/project-book-agent"
BOOT_HOOK_PATH="/usr/local/share/project-book-agent-autostart.sh"
SSH_INIT_PATH="/usr/local/share/ssh-init.sh"
MARKER_START="# project-book-agent autostart"
MARKER_END="# end project-book-agent autostart"
APP_USER="$(stat -c '%U' "$SCRIPT_DIR")"

sudo tee "$SERVICE_PATH" >/dev/null <<EOF
#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$SCRIPT_DIR"
APP_USER="$APP_USER"
PID_FILE="\$APP_DIR/.runtime/agent.pid"
AGENT_ENTRY="\$APP_DIR/update_agent.mjs"

find_pid() {
  if [[ -f "\$PID_FILE" ]]; then
    local pid
    pid="\$(cat "\$PID_FILE")"
    if [[ -n "\$pid" ]] && kill -0 "\$pid" 2>/dev/null; then
      echo "\$pid"
      return 0
    fi
  fi

  local pid
  pid="\$(pgrep -f "node \$AGENT_ENTRY" | tail -n 1 || true)"
  if [[ -n "\$pid" ]]; then
    echo "\$pid"
    return 0
  fi
  return 1
}

run_as_user() {
  if id "\$APP_USER" >/dev/null 2>&1; then
    sudo -u "\$APP_USER" "\$@"
  else
    "\$@"
  fi
}

case "\${1:-}" in
  start)
    if find_pid >/dev/null 2>&1; then
      echo "project-book-agent already running"
      exit 0
    fi
    run_as_user "\$APP_DIR/start_agent.sh"
    ;;
  stop)
    if find_pid >/dev/null 2>&1; then
      run_as_user "\$APP_DIR/stop_agent.sh"
    else
      echo "project-book-agent is not running"
    fi
    ;;
  restart)
    "\$0" stop || true
    sleep 1
    "\$0" start
    ;;
  status)
    if pid="\$(find_pid)"; then
      echo "project-book-agent is running (PID \$pid)"
      exit 0
    fi
    echo "project-book-agent is not running"
    exit 3
    ;;
  *)
    echo "Usage: \$0 {start|stop|restart|status}"
    exit 1
    ;;
esac
EOF

sudo chmod 755 "$SERVICE_PATH"

sudo tee "$BOOT_HOOK_PATH" >/dev/null <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

if [[ -x /etc/init.d/project-book-agent ]]; then
  /etc/init.d/project-book-agent start >>/tmp/project-book-agent-boot.log 2>&1 || true
fi
EOF

sudo chmod 755 "$BOOT_HOOK_PATH"

if ! sudo grep -qF "$MARKER_START" "$SSH_INIT_PATH"; then
  sudo perl -0pi -e 's/\nset \+e\s*\nexec "\$@"/\n\n# project-book-agent autostart\nif [ -x \/usr\/local\/share\/project-book-agent-autostart.sh ]; then\n    \/usr\/local\/share\/project-book-agent-autostart.sh\nfi\n# end project-book-agent autostart\n\nset +e\nexec "\$@"/' "$SSH_INIT_PATH"
fi

if command -v update-rc.d >/dev/null 2>&1; then
  sudo update-rc.d project-book-agent defaults >/dev/null 2>&1 || true
fi

sudo service project-book-agent restart || sudo service project-book-agent start

echo "Installed project-book-agent service"
echo "Service: $SERVICE_PATH"
echo "Boot hook: $BOOT_HOOK_PATH"
