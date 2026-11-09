#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "=== Starting CodeProOJ Judge System ==="

mkdir -p logs storage/executables storage/submissions storage/testcases storage/results

# Start Judge Server in background
python3 judge-server/main.py > logs/judge-server.log 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > logs/judge-server.pid
echo "Judge Server started with PID $SERVER_PID (Port 9999)"

echo "CodeProOJ Judge System running. Check logs/judge-server.log for details."
