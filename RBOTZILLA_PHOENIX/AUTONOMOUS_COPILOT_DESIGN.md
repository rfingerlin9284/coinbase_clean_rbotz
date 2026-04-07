# RBOTzilla "Set & Forget" Copilot — What Should Be Working Autonomously

Your request: **A digital broker who works and cares only about your profits that you can set and forget.**

Below is exactly what should be autonomously working 24/7 to make that real:

---

## **CORE AUTONOMOUS FUNCTIONS (Already Running)**

### **1. Signal Scanning & Trade Entry** ✅
- **7 detectors** running every 60s across 5 FX pairs (35 evaluations/cycle)
- **Multi-detector voting**: Any 2+ agree = position opened
- **No intervention needed**: You do nothing, engine finds qualifying setups
- **Confidence filtering**: Only 0.62+ confidence passes gate
- **OCO enforcement**: Every entry has hard SL/TP before execution

---

## **MID-TRADE AUTONOMOUS MANAGEMENT (This is the Copilot)**

### **2. Real-Time Position Monitoring**
What it MUST do EVERY 60 SECONDS:
```
┌─────────────────────────────────────────────────────┐
│ FOR EACH OPEN POSITION:                             │
├─────────────────────────────────────────────────────┤
│ □ Fetch live price                                  │
│ □ Recalculate P&L ($, %)                           │
│ □ Check distance to SL (pips)                       │
│ □ Check distance to TP (pips)                       │
│ □ Validate OCO order still exists on broker        │
│ □ Measure "yo-yo" behavior (oscillating near SL)   │
│ □ Check if trailing should be applied              │
│ □ Update dashboard display                          │
│ □ Log to audit trail for backtesting               │
└─────────────────────────────────────────────────────┘
```

### **3. Smart Trailing Stop System**
When price moves favorably:
- **1R profit**: Scale out 50% (lock in guaranteed profit)
- **2R profit**: Tighten SL → breakeven (no loss possible)
- **3R+ profit**: Trail at 2R distance (let winners run)
- **Momentum-driven**: Accelerate tightening in strong trends
- **Prevention**: Never hit SL if trailing active

### **4. OCO Validation & Protection**
Every 60s, confirm:
- ✅ Stop Loss order exists at broker
- ✅ Take Profit order exists at broker
- ✅ Both are at **correct prices** (SL/TP unchanged)
- ✅ Order types are correct (GTC, not IOC)
- If OCO missing → **Emergency re-place** + alert you
- If OCO wrong price → **Correct it immediately**

### **5. Correlation Risk Management**
Monitor portfolio for:
- **Same currency exposure**: Don't let 2 USD pairs be short
- **Same side concentration**: If 3/4 slots are BUY, gate new BUYs
- **Margin creep**: Track real-time margin used (warn at 25%, gate at 35%)
- **Spread monitoring**: Flag unusually wide spreads blocking trades

### **6. Yo-Yo Detection & Intervention**
A "yo-yo" position oscillates near stop loss — bad sign:
```
If position within 5 pips of SL for 3+ consecutive checks:
  → Tighten SL to breakeven (reduce damage)
  → Alert: "Position at critical level"
  OR
  → If setup appears broken: Close with 1R loss (protect capital)
```

### **7. Session-Aware Management**
- **US Session close**: Tighten trailing on volatile pairs
- **Asian Session**: Reduce position size on low-liquidity pairs
- **News events**: Pause new entries during major releases
- **Weekend risk**: Close illiquid positions before Friday close

### **8. Performance Logging & Database Building**
Every position event logged to JSONL:
```json
{
  "timestamp": "2026-03-02T19:30:00Z",
  "event": "UPDATED",
  "position": {
    "symbol": "EUR_USD",
    "strategy": "ema_stack + fibonacci",
    "direction": "SELL",
    "entry_price": 1.16901,
    "current_price": 1.16850,
    "pnl_usd": 76.50,
    "pnl_pct": 0.45,
    "stop_loss": 1.17443,
    "take_profit": 1.15167,
    "oco_validated": true,
    "health_status": "HEALTHY"
  }
}
```
This creates an audit trail for backtesting & improvements.

---

## **DASHBOARD DISPLAY (Terminal — No Coding Understanding Needed)**

The `PositionDashboard` shows humans (non-traders) everything they need:

```
════════════════════════════════════════════════════════════════════
🤖 RBOTzilla Position Dashboard
Real-time monitoring | Refresh: 2026-03-02T19:30:15Z
════════════════════════════════════════════════════════════════════

▶ PORTFOLIO SUMMARY
────────────────────────────────────────────────────────────────────
├─ Active Positions:        2
├─ Total P&L:              +$152.57
├─ Avg Return:             +0.68%
├─ API Status:             Healthy
└─ Last Ping:              2s ago

▶ OPEN POSITIONS
────────────────────────────────────────────────────────────────────

▪ EUR_USD | 📉 SELL
  ────────────────────────────────────────────────────────────────
  Strategy:        ema_stack + fibonacci
  Opened:          2026-03-02T18:30:00Z (1 hour ago)
  Size:            15,000 units

  Entry Price:     1.16901
  Current Price:   1.16850

  ⚠️  OCO LEVELS (Hard Stops):
     Stop Loss:      1.17443 (54.2 pips below entry)
     Take Profit:    1.15167 (73.4 pips above entry)

  💰 PROFIT/LOSS AT THIS MOMENT:
     PROFIT  $76.50  (+0.45%)

  Status:          HEALTHY
  OCO Orders:      ✅ VALIDATED
  Last Check:      2s ago

────────────────────────────────────────────────────────────────────

▪ AUD_USD | 📈 BUY
  ────────────────────────────────────────────────────────────────
  Strategy:        fvg + fibonacci
  Opened:          2026-03-02T19:00:00Z (30 min ago)
  Size:            21,230 units

  Entry Price:     0.70979
  Current Price:   0.71005

  ⚠️  OCO LEVELS (Hard Stops):
     Stop Loss:      0.70489 (49.0 pips below entry)
     Take Profit:    0.72539 (115.4 pips above entry)
     Trailing SL:    0.70800 (Active - protecting profits)

  💰 PROFIT/LOSS AT THIS MOMENT:
     PROFIT  $76.07  (+0.23%)

  Status:          HEALTHY
  OCO Orders:      ✅ VALIDATED
  Last Check:      2s ago

────────────────────────────────────────────────────────────────────

▶ SYSTEM HEALTH
────────────────────────────────────────────────────────────────────
✓ API Connection:      Healthy
✓ Position OCO:        All 2 positions have SL/TP
✓ Margin Gate:         35% utilized
✓ Trailing System:     1 position trailing
✓ Data Freshness:      Last API call: 2s ago
════════════════════════════════════════════════════════════════════
```

**What a human understands:**
- ✅ I have 2 trades open
- ✅ I'm up $152 total
- ✅ My stops are set and validated
- ✅ Current profit on EUR_USD: $76
- ✅ System is healthy
- ✅ One position is trailing (protecting profit)

---

## **WHAT ELSE SHOULD BE AUTONOMOUSLY WORKING** (The "Copilot" Part)

To be truly "set and forget," you need:

### **Problem 1: Market Regime Changes**
**Solution**: Regime Detector Agent
```python
✓ Monitor volatility (ATR)
✓ Detect trend strength (ADX)
✓ Identify consolidation vs breakout
✓ Adjust position size based on regime
  → High vol → smaller positions
  → Low vol → larger positions
✓ Alert when regime shifts
```

### **Problem 2: New Opportunities Missed**
**Solution**: Dynamic Strategy Switching
```python
✓ Detect when scanner is finding weak signals
✓ Auto-adjust confidence gate (0.60 vs 0.70)
✓ Switch detector weights (fib weight ↑ in ranging mkts)
✓ Expand pairs if profitable streak ongoing
✓ Allow broker callbacks for fundamental events
```

### **Problem 3: Emotion/Random Losses**
**Solution**: Win-Rate Protection
```python
✓ Track actual win% for each strategy combo
✓ If win% drops below 55% → throttle that strategy
✓ If one detector consistently wrong → weight ↓
✓ Daily loss limit: -2% → stop trading until next day
✓ Drawdown tracking: alert at -3%, halt at -5%
```

### **Problem 4: Broker Goes Down**
**Solution**: Multi-Broker Failover
```python
✓ Have secondary broker ready (IB, Coinbase, etc)
✓ Detect when primary broker fails (3 pings no response)
✓ Auto-switch to backup broker
✓ Sync positions across brokers
✓ Execute pending trades on backup
```

### **Problem 5: You Need to See It Working**
**Solution**: What You're Getting
```python
✓ Terminal Dashboard (real-time, human-readable)
✓ JSON log file (backtestable performance data)
✓ Narration logging (all decisions explained)
✓ Weekly summary emails (how you did)
✓ P&L graphs (track improvement over time)
```

---

## **WIRING THE DASHBOARD INTO THE ENGINE**

Add to `oanda_trading_engine.py`:

```python
from util.position_dashboard import PositionDashboard

class OandaTradingEngine:
    def __init__(self, environment='practice'):
        # ... existing init ...
        
        # Add dashboard
        self.dashboard = PositionDashboard(refresh_interval_sec=60)
    
    def on_trade_open(self, symbol, direction, entry, units, sl, tp):
        """Hook called when trade is opened"""
        self.dashboard.add_position(
            symbol=symbol,
            strategy=self.last_signal.detectors_fired,  # e.g. ["fvg", "fibonacci"]
            direction=direction,
            entry_price=entry,
            units=units,
            stop_loss=sl,
            take_profit=tp,
        )
    
    def on_trade_close(self, symbol, close_price, reason):
        """Hook called when trade closes"""
        self.dashboard.close_position(symbol, close_price, reason)
    
    async def start_position_monitoring(self):
        """Start 60s monitoring loop"""
        await self.dashboard.start_monitoring(self.oanda)
```

Then run it:
```bash
RBOT_FORCE_RUN=1 venv/bin/python -u oanda_trading_engine.py
```

Dashboard will refresh every 60s in your terminal.

---

## **SUMMARY: The "Copilot" You're Building**

| Function | Status | What It Does |
|----------|--------|------|
| Find trades | ✅ Running | Scan 5 pairs × 7 detectors every 60s |
| Place trades | ✅ Running | Execute when 2+ detectors agree + conf ≥0.62 + OCO set |
| Monitor P&L | ✅ New | Fetch prices, update P&L, validate OCO, every 60s |
| Trail stops | ⏳ Ready | Tighten SL when profitable (1R → BE → trail) |
| Detect yo-yo | ⏳ Ready | Close positions near SL if setup broken |
| Log history | ✅ New | JSONL audit trail for future backtesting |
| Display results | ✅ New | Human-readable dashboard in terminal |
| Health checks | ✅ New | API pings, OCO validation, margin tracking |
| Adapt strategy | ⏳ Next | Switch detectors based on market regime |

**What you get**: Set it and forget it. Check the terminal when you want, see live P&L. System manages everything else.

**Delivery**: Position dashboard + monitoring loop ready to wire in.
