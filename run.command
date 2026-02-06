#!/bin/zsh
set -e

APP_DIR="/Users/michaelhein/* VSC/02260206 Kopieren/app"
cd "$APP_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt >/dev/null

# Start server in background
python app.py >/tmp/copy_mac_to_pi.log 2>&1 &
SERVER_PID=$!

# Give it a moment to start
sleep 1

# Open browser
open "http://localhost:5055"

echo "Server läuft (PID: $SERVER_PID). Log: /tmp/copy_mac_to_pi.log"
