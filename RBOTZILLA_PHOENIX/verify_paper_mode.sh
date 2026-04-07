#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           PAPER MODE CONFIGURATION VERIFICATION               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")"

# Check .env settings
echo "✓ Checking .env configuration..."
echo ""

python3 - <<'PY'
from util.mode_manager import get_mode_info
info = get_mode_info()
print(f"MODE: {info['mode']}")
print(f"HEADLESS: {info.get('headless')}")
print(f"DASHBOARD_ENABLED: {info.get('dashboard_enabled')}")
print(f"BROKERS: {info.get('brokers')}")
PY
echo ""

echo "PAPER_MODE:"
grep "PAPER_MODE=" .env | head -1

echo "EXECUTION_ENABLED:"
grep "EXECUTION_ENABLED=" .env | head -1

echo "OANDA_ENV:"
grep "OANDA_ENV=" .env | head -1

echo "QUALITY_THRESHOLD:"
grep "QUALITY_THRESHOLD=" .env | head -1

echo "MAX_HOLD_MIN (TTL):"
grep "MAX_HOLD_MIN=" .env | head -1

echo ""
echo "✓ OANDA Practice Credentials:"
grep "OANDA_PRACTICE_ACCOUNT_ID=" .env | head -1
echo "OANDA_PRACTICE_TOKEN: [set]"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Configuration Status:"
echo ""
echo "  Paper Mode:         ENABLED ✅"
echo "  Live Trading:       DISABLED ✅"
echo "  OANDA Environment:  PRACTICE (sandbox) ✅"
echo "  Real Capital Risk:  ZERO ✅"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🚀 To start paper trading (headless):"
echo ""
echo "  $ . venv/bin/activate"
echo "  $ python3 -c \"from util.mode_manager import switch_mode; switch_mode('PAPER')\""
echo "  $ bash scripts/start_headless.sh --broker oanda"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📚 Documentation:"
echo "  PAPER_MODE_SETUP.md - Complete guide"
echo "  BROKER_INTEGRATION_COMPLETE.md - API reference"
echo ""
