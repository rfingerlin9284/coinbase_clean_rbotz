# Dashboard Integration - Test & Verification Guide

## Status: ✅ COMPLETE & READY TO TEST

### Changes Made

**1. PositionDashboard Class Updates** (`util/position_dashboard.py`)
   - ✅ Added `engine` parameter to `__init__` (line 116)
   - ✅ New method: `sync_and_display()` (after line 204)
     - Pulls active positions from engine.active_positions
     - Updates metrics with current prices
     - Calls `refresh()` to render to terminal

**2. Trading Engine Integration** (`oanda_trading_engine.py`)
   - ✅ Import: `from util.position_dashboard import PositionDashboard, PositionMetrics` (line 48)
   - ✅ Init: Dashboard initialized in `__init__` (lines 155-180)
   - ✅ Main Loop: `sync_and_display()` call added (lines 2048-2054)
     - Wraps in try/except for error handling
     - Checks env var `RBOT_DASHBOARD_ACTIVE` (default: true)
     - Calls after scan cycle, before sleep

---

## How to Test

### Test 1: Engine Startup (No Changes Needed)
```bash
cd /home/rfing/RBOTZILLA_PHOENIX
python -u oanda_trading_engine.py
```

**Expected Behavior:**
1. Engine starts normally
2. PositionDashboard initializes ("✅ Position Dashboard initialized")
3. Scans for signals every 60 seconds
4. Every scan cycle, dashboard renders to terminal (even if no positions yet)

### Test 2: Dashboard with Active Positions
Once trades are placed, you should see:
```
═══════════════════════════════════════════════════════════════════════════
🤖 RBOTzilla Position Dashboard
Real-time monitoring | Refresh: 2025-03-01T18:15:22+00:00
═══════════════════════════════════════════════════════════════════════════

PORTFOLIO SUMMARY
  Active Positions: 2
  Total P&L:       +$245.32
  Avg Return:      +0.82%

OPEN POSITIONS
  ▪ EUR_USD | 📉 SELL
    Strategy:   ema_stack,fibonacci
    Entry:      1.16234 | Current: 1.16189
    SL:         1.16756 | TP: 1.15342
    P&L:        +$67.50 (+0.29%)
    Status:     HEALTHY ✅
```

### Test 3: Disable Dashboard (Optional)
If you want to suppress the dashboard:
```bash
RBOT_DASHBOARD_ACTIVE=false python -u oanda_trading_engine.py
```

Dashboard won't render, but engine continues normally.

---

## Integration Details

### Where Dashboard Renders
**File:** `oanda_trading_engine.py`, Lines 2048-2054
```python
# ── DASHBOARD: Display position summary and system health ───────
try:
    if self.dashboard and os.getenv('RBOT_DASHBOARD_ACTIVE', 'true').lower() != 'false':
        self.dashboard.sync_and_display()
except Exception as _dashboard_err:
    self.display.warning(f"⚠️ Dashboard render error: {_dashboard_err}")
```

**When It Renders:**
- After every market scan cycle (60s or 300s)
- Right before the engine sleeps waiting for next cycle
- Even if no trades are placed yet

### Active Positions Tracking
- Engine maintains `self.active_positions` dict with position data
- Dashboard's `sync_and_display()` method reads this dict
- Updates metrics: current price, P&L, distance to SL/TP
- Renders human-readable terminal display

### Logging
- Each position change logs to `/tmp/rbotzilla_positions.jsonl`
- Format: JSONL (1 JSON object per line)
- Used for backtest analysis and performance tracking

---

## Checklist: Before Running

- [ ] Engine installed with latest code
- [ ] `util/position_dashboard.py` has `sync_and_display()` method
- [ ] `oanda_trading_engine.py` has import + init + loop integration
- [ ] `util/terminal_display.py` available (for Colors and TerminalDisplay class)
- [ ] No syntax errors (verified with linter)

---

## Next Steps After Verification

Once dashboard is working:

1. **Leave it running** - It will update every 60s automatically
2. **Monitor active positions** - See P&L in real-time
3. **Track strategy performance** - See which detector combos are winning
4. **Plan advanced features:**
   - Smart trailing stops (framework ready)
   - Email/SMS alerts
   - Daily loss limits
   - Multi-pair correlation monitoring

---

## Troubleshooting

### Issue: Dashboard doesn't appear
**Solution:** Check logs for `⚠️ Dashboard render error`
- May be an import issue (missing TerminalDisplay class)
- May be an exception in sync_and_display()

### Issue: No positions showing in dashboard
**This is normal!** Dashboard updates only when:
- Positions are stored in `engine.active_positions`
- Engine has just completed a scan cycle
- Dashboard's `sync_and_display()` is called

If engine is running but no trades placed, you'll see "No open positions" in dashboard.

### Issue: Dashboard rendering looks corrupted
- Likely a terminal width issue (Colors.RESET not applied correctly)
- Solution: Expand terminal window to 100+ characters wide

---

## Current System Architecture

```
Trading Engine (oanda_trading_engine.py)
    ↓
    └── PositionDashboard (util/position_dashboard.py)
            ├── Syncs: engine.active_positions → dashboard.positions
            ├── Display: render_portfolio_summary() → terminal
            ├── Logging: log_to_jsonl() → /tmp/rbotzilla_positions.jsonl
            └── Health: _render_health_checks() → API status, OCO validation
```

Every 60-300 seconds:
1. Engine scans for new signals
2. Places qualifying trades
3. Calls `dashboard.sync_and_display()`
4. Dashboard renders to terminal
5. Engine sleeps until next cycle

---

## Expected Terminal Output (Next 60 Seconds)

```
📡 SCAN: 5 pairs | ✅ 2 passed | ❌ 3 rejected | 🎯 placing 1

───────────────────────────────────────────────────────────
🤖 RBOTzilla Position Dashboard
───────────────────────────────────────────────────────────

PORTFOLIO SUMMARY
  Active Positions: 1
  Total P&L:       +$45.20
  
OPEN POSITIONS
  ▪ GBP_USD | 📈 BUY
    ...position details...

───────────────────────────────────────────────────────────

Slots open (1/5) — rescanning in 60s...
```

Then after 60s, the cycle repeats.

---

**Last Updated:** 2025-03-01
**Integration Status:** ✅ COMPLETE
**Ready for Testing:** YES
