#!/usr/bin/env bash
# start.sh — RBOTZILLA_COINBASE_CLEAN
# Label: COINBASE_CRYPTO_ENGINE
set -euo pipefail

REPO="/home/rfing/RBOTZILLA_COINBASE_CLEAN"
ENGINE="engine/trade_engine.py"
LOG="logs/engine_continuous.out"
VENV=".venv/bin/python"

cd "$REPO"
mkdir -p logs

if [ ! -x "$VENV" ]; then
  echo "FAIL: missing $REPO/.venv — run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

# Kill any stale Coinbase instance (don't kill OANDA!)
pkill -f "RBOTZILLA_COINBASE_CLEAN.*trade_engine" >/dev/null 2>&1 || true
sleep 1

# Clear Python bytecache so code changes always take effect
find "$REPO" -name "*.pyc" -delete 2>/dev/null || true
find "$REPO" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Prevent Python from EVER creating bytecache
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$REPO"

# Load .env so all operator-configured values reach the engine process
if [ -f "$REPO/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO/.env"
  set +a
fi

# Truncate log to avoid binary content from previous runs
: > "$LOG"

nohup "$VENV" -B -u -m engine.trade_engine > "$LOG" 2>&1 &

sleep 2
if pgrep -af "engine.trade_engine|trade_engine.py" >/dev/null; then
  echo "OK: RBOTZILLA_COINBASE_CLEAN engine started (log: $LOG)"
  echo ""
  sleep 3
  tail -n 25 "$LOG" | grep -E -A 15 "RBOTZILLA|COINBASE|ENGINE" || true
  echo ""
else
  echo "FAIL: engine not running — check $LOG"
  exit 1
fi
