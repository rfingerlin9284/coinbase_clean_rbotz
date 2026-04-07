# Dashboard Integration - Complete ✅

## What's New
The position dashboard is now **automatically active** every time the engine starts. It displays:

- 🎯 Real-time position P&L and metrics
- 📊 Strategy information for each trade
- 🔒 OCO (hard stop) levels - SL/TP
- 💰 Profit/loss in USD and percentage
- ⚠️ System health and API status
- ✅ OCO validation checks

## How It Works

### Automatic Activation (Default)
When you run the engine with your normal task:
```
python -u oanda_trading_engine.py
```

The dashboard will:
1. ✅ Initialize on engine startup
2. ✅ Display every 60s (after each scan cycle)
3. ✅ Show all open positions with P&L
4. ✅ Display health checks + API status

### Disable Dashboard (Optional)
If you want to run WITHOUT the dashboard display:
```
RBOT_DASHBOARD_ACTIVE=false python -u oanda_trading_engine.py
```

## Integration Details

**Files Modified:**

1. **`oanda_trading_engine.py`**
   - Line 48: Import PositionDashboard
   - Lines 155-180: Initialize dashboard in `__init__`
   - Lines 2048-2054: Call `sync_and_display()` before each sleep cycle

2. **`util/position_dashboard.py`**
   - Added `engine` parameter to `__init__`
   - Added `sync_and_display()` method - syncs positions from engine and renders

## What You See

Each refresh shows:
```
═══════════════════════════════════════════════════════════════════════════
🤖 RBOTzilla Position Dashboard
Real-time monitoring | Refresh: 2025-03-01T18:15:22+00:00
═══════════════════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────────────────────
PORTFOLIO SUMMARY
────────────────────────────────────────────────────────────────────────────
  Active Positions: 2
  Total P&L:       +$245.32
  Avg Return:      +0.82%
  API Status:      Healthy
  Last Ping:       2025-03-01T18:15:20+00:00

────────────────────────────────────────────────────────────────────────────
OPEN POSITIONS
────────────────────────────────────────────────────────────────────────────

▪ EUR_USD | 📉 SELL
  ────────────────────────────────────────────────────────────────────────
  Strategy:        ema_stack,fibonacci
  Opened:          2025-03-01T17:45:12+00:00
  Size:            15,000 units

  Entry Price:     1.16234
  Current Price:   1.16189

  ⚠️  OCO LEVELS (Hard Stops):
     Stop Loss:      1.16756 (52.2 pips below entry)
     Take Profit:    1.15342 (89.2 pips above entry)

  💰 PROFIT/LOSS AT THIS MOMENT:
     PROFIT    $67.50  (0.29%)

  Status:          HEALTHY
  OCO Orders:      ✅ VALIDATED
  Last Check:      2025-03-01T18:15:15+00:00
```

## Refresh Cycle

The dashboard refreshes:
- ✅ After every 60s fast scan (when slots are open)
- ✅ After every 300s slow scan (when positions are full)
- ✅ Background syncing pulls latest prices from engine
- ✅ JSONL logging to `/tmp/rbotzilla_positions.jsonl` for backtest DB

## System Next Steps

The dashboard now provides the foundation for additional autonomous features:
1. Smart trailing stops (framework ready)
2. Email/SMS alerts on position events
3. Daily loss limit enforcement
4. Multi-pair correlations
5. Regime detection feedback

All integrated into the "set and forget" autonomous system design.

---

**Status:** ✅ **Dashboard Active by Default**
- Initialized on engine startup
- Refresh every 60s in main scan loop
- Human-readable format (non-trader friendly)
- No configuration needed - just start the engine

**Test:** Run `python -u oanda_trading_engine.py` and watch the dashboard appear every 60 seconds.
