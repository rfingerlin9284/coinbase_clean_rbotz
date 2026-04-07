bash -lc '
set -euo pipefail

ROOT="/home/rfing/RBOTZILLA_PHOENIX"
PY="$ROOT/venv/bin/python"
LOG="/tmp/rbz.log"
PIDFILE="/tmp/rbotzilla_oanda_engine.pid"

cd "$ROOT"

echo "== RBOTZILLA OANDA BRING-UP =="
echo "ROOT: $ROOT"
[ -x "$PY" ] || { echo "❌ venv python not found at $PY"; exit 1; }
[ -f "$ROOT/.env" ] || { echo "❌ Missing $ROOT/.env (bot cannot connect)."; exit 1; }

# Kill any old engine instances
pkill -f "oanda_trading_engine.py" 2>/dev/null || true
sleep 1

# Minimal connectivity + account sanity (NO secrets printed)
"$PY" - << "PYEOF"
import os, json, requests
from dotenv import load_dotenv

load_dotenv(".env")

token = os.getenv("OANDA_PRACTICE_TOKEN") or os.getenv("OANDA_TOKEN") or ""
acct  = os.getenv("OANDA_PRACTICE_ACCOUNT_ID") or os.getenv("OANDA_ACCOUNT_ID") or ""
if not token or not acct:
    print("❌ Missing OANDA_PRACTICE_TOKEN / OANDA_PRACTICE_ACCOUNT_ID in .env")
    raise SystemExit(2)

base = os.getenv("OANDA_API_BASE") or "https://api-fxpractice.oanda.com"
hdr  = {"Authorization": f"Bearer {token}"}

def get(path):
    r = requests.get(base+path, headers=hdr, timeout=10)
    try:
        j = r.json()
    except Exception:
        j = {"raw": r.text}
    return r.status_code, j

print("✅ Token present (redacted).")
print(f"✅ API base: {base}")
print(f"✅ Configured Account ID: {acct}")

# List accessible accounts (this is the #1 cause of 'I see nothing in UI')
code, j = get("/v3/accounts")
if code != 200:
    print(f"❌ /v3/accounts failed: HTTP {code} -> {j}")
    raise SystemExit(3)

ids = [a.get("id") for a in j.get("accounts", [])]
print("\\nAccounts visible to this token:")
for i in ids:
    marker = " <== CONFIGURED" if i == acct else ""
    print(f" - {i}{marker}")

# Pull summary for configured account
code, j = get(f"/v3/accounts/{acct}/summary")
if code != 200 or "account" not in j:
    print(f"❌ Account summary failed: HTTP {code} -> {j}")
    raise SystemExit(4)

a = j["account"]
print("\\nConfigured account summary:")
for k in ["balance","NAV","marginUsed","unrealizedPL","openTradeCount","openPositionCount"]:
    print(f"  {k}: {a.get(k)}")
PYEOF

echo ""
echo "== Starting engine (FAST scan + FORCE run + unbuffered logs) =="
: > "$LOG"

export RBOT_FORCE_RUN=1
export RBOT_SCAN_FAST_SECONDS="${RBOT_SCAN_FAST_SECONDS:-30}"     # aggressive: 30s
export RBOT_SCAN_SLOW_SECONDS="${RBOT_SCAN_SLOW_SECONDS:-300}"    # only when full
export RBOT_MIN_SIGNAL_CONFIDENCE="${RBOT_MIN_SIGNAL_CONFIDENCE:-0.70}"
export RBOT_MAX_NEW_TRADES_PER_CYCLE="${RBOT_MAX_NEW_TRADES_PER_CYCLE:-3}"
export RBOT_SCAN_LOG_TOP_N="${RBOT_SCAN_LOG_TOP_N:-8}"

nohup "$PY" -u oanda_trading_engine.py >> "$LOG" 2>&1 &
echo $! > "$PIDFILE"
sleep 2

echo "✅ Engine PID: $(cat "$PIDFILE")"
echo ""
echo "== LIVE LOG (last 120 lines) =="
tail -n 120 "$LOG" | sed -e "s/\r//g" || true

echo ""
echo "== What you should see next =="
echo "1) Repeating scan lines every ${RBOT_SCAN_FAST_SECONDS}s while slots exist:"
echo "   SCAN: ... placing ..."
echo "2) If it finds signals but won’t trade, you’ll see explicit rejection reasons:"
echo "   confidence_below_threshold / no_signal / already_active_symbol / CHARTER VIOLATION / margin gate"
echo "3) If it places a trade, you’ll see: → Placing SYMBOL BUY/SELL ..."
echo ""
echo "== Follow the log live =="
echo "tail -f $LOG"
'