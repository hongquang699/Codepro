#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "=== Stopping CodeProOJ Judge System ==="

if [ -f logs/judge-server.pid ]; then
    PID=$(cat logs/judge-server.pid)
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        echo "Judge Server (PID $PID) stopped."
    fi
    rm -f logs/judge-server.pid
else
    pkill -f "judge-server/main.py" || true
    echo "Judge processes terminated."
fi
