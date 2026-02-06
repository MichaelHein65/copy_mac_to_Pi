#!/bin/zsh
set -e

APP_DIR="/Users/michaelhein/* VSC/02260206 Kopieren/app"
PID_FILE="/tmp/copy_mac_to_pi.pid"
LOG_FILE="/tmp/copy_mac_to_pi.log"
PORT=5055

cd "$APP_DIR"

function is_running() {
  if [ -f "$PID_FILE" ]; then
    local pid
    pid=$(cat "$PID_FILE" 2>/dev/null || true)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
  fi
  return 1
}

function start_server() {
  if [ ! -d ".venv" ]; then
    python3 -m venv .venv
  fi
  source .venv/bin/activate
  pip install -r requirements.txt >/dev/null

  python app.py >"$LOG_FILE" 2>&1 &
  local pid=$!
  echo "$pid" > "$PID_FILE"
  sleep 1
  echo "Server gestartet (PID: $pid). Log: $LOG_FILE"
  open "http://localhost:$PORT"
}

function stop_server() {
  if is_running; then
    local pid
    pid=$(cat "$PID_FILE")
    kill "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "Server gestoppt (PID: $pid)"
  else
    echo "Kein Server gefunden."
  fi
}

case "$1" in
  stop)
    stop_server
    ;;
  start|"" )
    if is_running; then
      echo "Server läuft bereits (PID: $(cat "$PID_FILE")). Öffne Browser..."
      open "http://localhost:$PORT"
    else
      start_server
    fi
    ;;
  *)
    echo "Usage: ./run.command [start|stop]"
    ;;
esac
