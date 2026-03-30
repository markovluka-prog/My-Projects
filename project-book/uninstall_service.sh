#!/usr/bin/env bash
set -euo pipefail

SERVICE_PATH="/etc/init.d/project-book-agent"
BOOT_HOOK_PATH="/usr/local/share/project-book-agent-autostart.sh"
SSH_INIT_PATH="/usr/local/share/ssh-init.sh"
MARKER_START="# project-book-agent autostart"
MARKER_END="# end project-book-agent autostart"

if [[ -x "$SERVICE_PATH" ]]; then
  sudo service project-book-agent stop || true
fi

if command -v update-rc.d >/dev/null 2>&1; then
  sudo update-rc.d -f project-book-agent remove >/dev/null 2>&1 || true
fi

sudo rm -f "$SERVICE_PATH" "$BOOT_HOOK_PATH"

if sudo grep -qF "$MARKER_START" "$SSH_INIT_PATH"; then
  sudo perl -0pi -e 's/\n# project-book-agent autostart\nif \[ -x \/usr\/local\/share\/project-book-agent-autostart\.sh \]; then\n    \/usr\/local\/share\/project-book-agent-autostart\.sh\nfi\n# end project-book-agent autostart\n//' "$SSH_INIT_PATH"
fi

echo "Uninstalled project-book-agent service"
