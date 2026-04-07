#!/bin/bash
# RBOTZILLA TRADING SYSTEM — QUICK START & MONITORING
# PIN: 841921
# Date: 2026-03-02

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       RBOTZILLA TRADING ENGINE — STATUS & COMMANDS              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ─────────────────────────────────────────────────────────────────────
# SECTION 1: QUICK STATUS
# ─────────────────────────────────────────────────────────────────────
echo "📊 TRADING STATE"
echo "─────────────────────────────────────────────────────────────────"
if pgrep -f "oanda_trading_engine.py" > /dev/null 2>&1; then
    echo "✅ Engine: RUNNING (background process)"
    ps aux | grep oanda_trading_engine.py | grep -v grep | awk '{print "   PID: " $2 ", CPU: " $3 "%, Memory: " $4 "%"}'
else
    echo "⛔ Engine: STOPPED"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────
# SECTION 2: LIVE POSITIONS
# ─────────────────────────────────────────────────────────────────────
echo "💰 OPEN POSITIONS"
echo "─────────────────────────────────────────────────────────────────"
python3 scripts/check_positions.py 2>/dev/null | head -20 || echo "   (engine not ready yet; check_positions requires OANDA connection)"
echo ""

# ─────────────────────────────────────────────────────────────────────
# SECTION 3: RECENT SCAN CYCLES
# ─────────────────────────────────────────────────────────────────────
echo "📡 RECENT SCANS (last 30 lines)"
echo "─────────────────────────────────────────────────────────────────"
if [ -f /tmp/rbz_live.log ]; then
    grep -E "SCAN|Placing|UPSIZE|Margin|VIOLATION|rescanning|Positions full" /tmp/rbz_live.log | tail -15 || echo "   (no scans yet)"
else
    echo "   (log not found; engine may not be running)"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────
# SECTION 4: COMMANDS
# ─────────────────────────────────────────────────────────────────────
echo "🎮 QUICK COMMANDS"
echo "─────────────────────────────────────────────────────────────────"
echo "START ENGINE:"
echo "  Ctrl+Shift+B in VS Code (or 'venv/bin/python -u oanda_trading_engine.py')"
echo ""
echo "STOP ENGINE:"
echo "  pkill -f oanda_trading_engine.py"
echo ""
echo "WATCH LIVE TRADING:"
echo "  tail -f /tmp/rbz_live.log | grep -E 'SCAN|Placing|UPSIZE|Margin|slot'"
echo ""
echo "CHECK ACCOUNT BALANCE & POSITIONS:"
echo "  python3 scripts/check_positions.py"
echo ""
echo "REVIEW AUDIT LOG:"
echo "  ls -lh logs/audit_trail.jsonl"
echo ""

# ─────────────────────────────────────────────────────────────────────
# SECTION 5: SYSTEM STATE
# ─────────────────────────────────────────────────────────────────────
echo "⚙️  SYSTEM CONFIGURATION"
echo "─────────────────────────────────────────────────────────────────"
echo "Environment: PRACTICE (Paper Trading)"
echo "Account: 101-001-31210531-001"
echo "Min Notional: \$15,000 (Charter immutable)"
echo "Max Margin: 35% of \$9,910 = \$3,469"
echo "Max Positions: 5 concurrent"
echo "Scan Cadence: 60s (slots available) / 300s (full)"
echo "Min Confidence Gate: 62%"
echo ""
echo "✅ All trading fixes applied (commit f306efc)"
echo "✅ MAS architecture foundation ready (commit eec35a2)"
echo ""
