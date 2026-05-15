#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

banner() {
  clear
  cat <<'MENU'
+--------------------------------------------------+
| EV-CYBER-ACADEMY                                |
| EV-SubHunter                                    |
+--------------------------------------------------+
| 1) Launch Web Dashboard                         |
| 2) Launch Terminal CLI                          |
| 3) Install/Update Dependencies                  |
+--------------------------------------------------+
MENU
}

ensure_venv() {
  if [[ ! -d "$VENV_DIR" ]]; then
    echo "[+] Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
  fi
}

install_deps() {
  ensure_venv
  echo "[+] Installing dependencies inside .venv..."
  "$VENV_DIR/bin/python" -m pip install --upgrade pip
  "$VENV_DIR/bin/pip" install -r "$ROOT_DIR/requirements.txt"
}

ensure_deps() {
  ensure_venv
  if [[ ! -f "$VENV_DIR/bin/flask" ]]; then
    install_deps
  fi
}

launch_web() {
  ensure_deps
  echo "[+] Dashboard: http://127.0.0.1:5000"
  if [[ -n "${EVSUBHUNTER_PASSWORD:-}" ]]; then
    echo "[+] Custom password active from EVSUBHUNTER_PASSWORD"
  else
    echo "[+] Default password: adminsubhunter"
  fi
  "$VENV_DIR/bin/python" "$ROOT_DIR/dashboard.py"
}

launch_cli() {
  ensure_deps
  read -r -p "Target domain: " target
  read -r -p "Custom wordlist path (optional): " wordlist
  if [[ -n "$wordlist" ]]; then
    "$VENV_DIR/bin/python" "$ROOT_DIR/subhunter.py" -d "$target" -w "$wordlist"
  else
    "$VENV_DIR/bin/python" "$ROOT_DIR/subhunter.py" -d "$target"
  fi
}

banner
read -r -p "Select option: " choice

case "$choice" in
  1) launch_web ;;
  2) launch_cli ;;
  3) install_deps ;;
  *) echo "Invalid option" && exit 1 ;;
esac
