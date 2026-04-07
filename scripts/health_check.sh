#!/usr/bin/env bash
# health_check.sh — RBOTZILLA_COINBASE_CLEAN
# Label: COINBASE_CRYPTO_ENGINE
# Checks: engine process, recent narration events, broker connectivity
set -euo pipefail

REPO="/home/rfing/RBOTZILLA_COINBASE_CLEAN"
cd "$REPO"

echo ""
echo "=== COINBASE ENGINE PROCESS ==="
if pgrep -af "RBOTZILLA_COINBASE_CLEAN.*trade_engine" >/dev/null; then
  echo "RUNNING"
else
  echo "NOT RUNNING"
fi

echo ""
echo "=== LAST 5 NARRATION EVENTS ==="
if [ -f logs/narration.jsonl ]; then
  tail -n 5 logs/narration.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
  try:
    e = json.loads(line)
    print(f\"  {e.get('timestamp','')[-25:-7]}  {e.get('event_type',''):38}  {e.get('symbol','')}\")
  except Exception:
    pass
"
else
  echo "narration.jsonl not found"
fi

echo ""
echo "=== COINBASE BROKER STATUS ==="
.venv/bin/python - <<'PY'
import sys
sys.path.insert(0, ".")
try:
    from brokers.coinbase_connector import get_coinbase_connector
    c = get_coinbase_connector()
    print("  Coinbase connector loaded OK")
except Exception as e:
    print(f"  ERROR: {e}")
PY

echo ""
