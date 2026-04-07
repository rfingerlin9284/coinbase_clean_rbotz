# 🤖 MEGA PROMPT: Complete AI Agent Rebuild Guide

## Purpose

This document provides AI agents (Claude, ChatGPT, etc.) with comprehensive instructions to:
1. **Understand** the complete RBOTZILLA system architecture
2. **Rebuild** the entire system from GitHub clone
3. **Extend** the system with new features
4. **Debug** issues systematically
5. **Optimize** performance and reliability

---

## System Overview for AI

### What is RBOTZILLA?

RBOTZILLA PHOENIX is a **multi-agent autonomous trading bot** that:
- Trades **3 forex pairs** on **OANDA**
- Uses **7+ technical strategies** with AI-powered aggregation
- Implements **hard risk limits** (charter system)
- Provides **real-time monitoring** via VS Code tasks
- Supports **paper and live trading** modes

### Core Philosophy

1. **Safety First**: Hard stops (charter) > soft limits
2. **Modular Design**: Strategies, brokers, agents are pluggable
3. **Observable**: Every event logged to JSONL narration file
4. **Testable**: Can backtest any strategy immediately
5. **Reproducible**: Git history + clean baseline = reliable rebuilds

---

## Quick Rebuild (5 Minutes)

```bash
# 1. Clone
git clone https://github.com/rfingerlin9284/rbotzilla_pheonix.git && cd rbotzilla_pheonix

# 2. Setup
bash setup.sh  # Creates venv, installs deps, initializes configs

# 3. Configure
cp ops/secrets.env.template ops/secrets.env
# Edit with OANDA credentials

# 4. Verify
python verify_system_ready.py  # Should show all ✓

# 5. Run
python -u oanda_trading_engine.py
```

---

## Architecture for AI Comprehension

### File Structure (What Does What)

```
Core Entry Points:
  - oanda_trading_engine.py         ← Main trading loop
  - headless_runtime.py             ← Supervisor mode
  - scripts/oanda_paper.py           ← Paper trading launcher

Configuration:
  - configs/runtime_mode.json       ← Mode switcher (PAPER/LIVE)
  - ops/secrets.env                 ← Credentials (GITIGNORE)
  - foundation/rick_charter.py      ← Hard limits enforcement

Signal Generation (7 Strategies):
  - strategies/bullish_wolf.py       ← Example strategy
  - strategies/bearish_wolf.py
  - strategies/liquidity_sweep.py
  - strategies/fib_confluence_breakout.py
  - [+ 3 more in same directory]
  - systems/multi_signal_engine.py   ← Aggregates all signals

Risk Management:
  - risk/dynamic_sizing.py           ← Kelly-criterion position sizing
  - risk/momentum_adaptive_sl.py      ← Stop loss calculation
  - risk/risk_control_center.py      ← Gate enforcement
  - risk/oco_validator.py            ← Order validation

Brokers:
  - brokers/oanda_connector.py       ← Main implementation
  - brokers/oanda_connector_enhanced.py
  - brokers/coinbase_connector.py    ← Alt broker
  - brokers/ib_connector.py          ← Alt broker

AI & Learning:
  - hive/rick_hive_mind.py           ← AI agent integration
  - hive/hive_llm_orchestrator.py    ← LLM routing
  - hive/adaptive_rick.py            ← Adaptive behavior
  - swarm/orchestrator.py            ← Multi-agent voting
  - ml_learning/regime_detector.py   ← Market detection

Monitoring & Logging:
  - util/narration_logger.py         ← Event logging (JSONL)
  - util/mode_manager.py             ← Mode switching
  - util/positions_registry.py       ← Position tracking
  - util/parameter_manager.py        ← Parameter tuning

Dashboards:
  - dashboard/app_enhanced.py        ← Streamlit web UI
  - dashboard/websocket_server.py    ← Real-time feed
  - .vscode/tasks.json               ← 33 automation tasks

Backtesting:
  - backtest/runner.py               ← Backtest executor
  - backtest/analyzer.py             ← Results analyzer
  - backtest/narrator.py             ← Event narration

Testing & Verification:
  - verify_system_ready.py           ← Quick checks (2s)
  - verify_system.py                 ← Deep checks (130+)
  - run_diagnostics.py               ← Health report
  - system_audit.sh                  ← Compliance audit
```

---

## Data Flow for AI Understanding

### 1-Second Trading Cycle

```
Second 1:
  [Market Data Arrives] → oanda_trading_engine.py
                       → multi_signal_engine.scan_all_symbols()
                       → For each symbol:
                           - Run strategy.scan(candles) [7 strategies]
                           - momentum_signals.aggregate([results])
                           - Get signal: (LONG/SHORT/NEUTRAL, confidence)
                       → rick_charter.validate_trade()
                           - Check notional >= $15k
                           - Check margin >= 18.3%
                           - Check correlation < 0.75
                           - Check max trades < 3
                       → IF valid: dynamic_sizing.calculate_position_size()
                           - Get historical win rate
                           - Apply Kelly criterion
                           - Calculate lot size
                       → oanda_connector.place_order()
                           - Place market order with SL/TP
                       → narration_logger.log()
                           - Write event to narration.jsonl (repo root)
                       → [Loop back to start of second]
```

### From Market Data to Narration Event

```json
[Input: EUR_USD 4H candle close]
  ↓ (oanda_trading_engine.py)
[7 strategies analyze last 100 candles]
  ↓ (strategies/*.py)
[Signals: bull=80%, bear=20%, etc]
  ↓ (systems/multi_signal_engine.py)
[Aggregated signal: BUY, conf=73%]
  ↓ (condition: confidence > 70)
[Validate charter rules]
  ↓ (foundation/rick_charter.py)
[Calculate position size]
  ↓ (risk/dynamic_sizing.py)
[Place order on OANDA]
  ↓ (brokers/oanda_connector.py)
[Log to narration.jsonl]
  ↓ (util/narration_logger.py)
{
  "timestamp": "2026-03-01T14:23:45Z",
  "event_type": "TRADE_OPENED",
  "symbol": "EUR_USD",
  "details": {
    "direction": "LONG",
    "entry": 1.0852,
    "lot_size": 0.5
  }
}
```

---

## Key Concepts for AI

### 1. Mode System (PAPER vs LIVE)

**How it works:**
- `configs/runtime_mode.json` stores current mode
- At startup, engine reads mode and connects to appropriate broker
- Mode switching requires **pin=841921** for LIVE

**How to switch:**
```python
# In any script
from util.mode_manager import switch_mode
switch_mode('LIVE', pin=841921)  # PIN from env var RICK_PIN
```

### 2. Charter Compliance (Hard Limits)

**What it does:**
Prevents trades that violate hard limits:

```python
class RickCharter:
    MIN_NOTIONAL = 15000        # Min trade size in USD
    MIN_MARGIN_PERCENT = 0.183  # Min 18.3% margin available
    CORRELATION_THRESHOLD = 0.75
    MAX_CONCURRENT_TRADES = 3
    
    def validate_trade(self, symbol, direction, account):
        # Returns: (is_valid: bool, reason: str)
```

**AI Understanding:**
- These are HARD STOPS (no exceptions)
- If any gate fails, trade is SKIPPED
- Logged as "REJECTION" in narration

### 3. Win Rate Tracking

**How it's calculated:**
```python
# From narration.jsonl (repo root)
closed_trades = [t for t in trades if t['event_type'] == 'TRADE_CLOSED']
wins = sum(1 for t in closed_trades if t['details']['pnl_usd'] > 0)
win_rate = wins / len(closed_trades)  # Target: > 0.55
```

**Per-Symbol Tracking:**
```python
by_symbol = {}
for trade in closed_trades:
    symbol = trade['symbol']
    if symbol not in by_symbol:
        by_symbol[symbol] = {'wins': 0, 'losses': 0}
    if trade['details']['pnl_usd'] > 0:
        by_symbol[symbol]['wins'] += 1
    else:
        by_symbol[symbol]['losses'] += 1
```

### 4. Position Sizing (Kelly Criterion)

**Formula:**
```
f* = (win% × avg_win - loss% × avg_loss) / avg_win
f_conservative = f* × 0.25  # 25% Kelly (safer)
lot_size = (f_conservative × account_equity) / risk_per_lot
```

**AI Task:** If win rate is low, Kelly will reduce lot size. This is correct behavior.

### 5. Strategy Framework

**Every strategy must:**
```python
from strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    def scan(self, candles):
        """
        Input: List of Candle objects (last 100)
        Output: (signal_direction, confidence, details)
        
        signal_direction: 'LONG' | 'SHORT' | 'NEUTRAL'
        confidence: 0-100 (0=no signal, 100=max strength)
        """
        # Calculate your indicator
        # Return your signal
        return 'LONG', 78, {'reason': 'Bullish wolf pack detected'}
```

**How to add a new strategy:**
1. Create `strategies/my_strategy.py`
2. Inherit from `BaseStrategy`
3. Implement `scan(candles)` method
4. Register in `strategies/registry.py`
5. It automatically participates in voting

### 6. Narration Logging (Event Trail)

**Format:** One JSON object per line

```json
{"timestamp": "2026-03-01T14:23:45Z", "event_type": "TRADE_OPENED", ...}
{"timestamp": "2026-03-01T14:25:30Z", "event_type": "TRADE_CLOSED", ...}
```

**Event Types:**
- `SCAN`: Signal scan result (may or may not lead to trade)
- `TRADE_OPENED`: Order placed successfully
- `TRADE_UPDATE`: SL moved, TP adjusted, or scale-out
- `TRADE_CLOSED`: Trade exited (SL/TP hit)
- `REJECTION`: Signal rejected by charter

**AI Task:** To analyze performance, parse this file and calculate stats.

---

## AI Development Tasks

### Task 1: Add a New Strategy

**Requirement:** Create a strategy based on moving average crossover

```python
# Create strategies/ma_crossover.py

from strategies.base import BaseStrategy
import numpy as np

class MAcrossover(BaseStrategy):
    def __init__(self, fast_period=5, slow_period=20):
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def scan(self, candles):
        closes = np.array([c.close for c in candles])
        
        fast_ma = np.mean(closes[-self.fast_period:])
        slow_ma = np.mean(closes[-self.slow_period:])
        
        if fast_ma > slow_ma:
            confidence = min(100, (fast_ma - slow_ma) / slow_ma * 1000)
            return 'LONG', confidence, {'fast': fast_ma, 'slow': slow_ma}
        elif fast_ma < slow_ma:
            confidence = min(100, (slow_ma - fast_ma) / slow_ma * 1000)
            return 'SHORT', confidence, {'fast': fast_ma, 'slow': slow_ma}
        else:
            return 'NEUTRAL', 0, {}
```

Then register in `strategies/registry.py`:
```python
from strategies.ma_crossover import MAcrossover

def load_strategies():
    return {
        'ma_crossover': MAcrossover(),
        # ... others
    }
```

### Task 2: Increase/Decrease Leverage

**Current:** MAX Leverage = 3.0x (from RICK_AGGRESSIVE_LEVERAGE)

**To change:**
1. Edit `.env`: RICK_AGGRESSIVE_LEVERAGE=5.0
2. Or edit code: `risk/dynamic_sizing.py` line with leverage multiplier
3. Backtest immediately to verify new P&L behavior

### Task 3: Switch Brokers (OANDA to Coinbase)

**Option 1: Runtime Switch**
```python
# In oanda_trading_engine.py
if BROKER == 'coinbase':
    from brokers.coinbase_connector import CoinbaseConnector
    connector = CoinbaseConnector(api_key, secret)
else:
    from brokers.oanda_connector import OandaConnector
    connector = OandaConnector(token, account_id)
```

**Option 2: Config-based**
Edit `configs/runtime_mode.json`:
```json
{
  "brokers": {
    "oanda": {"enabled": false},
    "coinbase": {"enabled": true}
  }
}
```

### Task 4: Enable Hive Mind AI Integration

**Current Status:** Optional (can run without)

**To enable:**
```python
# In oanda_trading_engine.py
from hive.rick_hive_mind import RickHiveMind

if HIVE_MIND_ENABLED:
    hive = RickHiveMind(llm_provider='openai')  # or 'claude', 'local'
    ai_assessment = hive.assess_trade(symbol, signal, confidence)
    confidence = confidence * ai_assessment['modifier']  # Adjust confidence
```

**AI Models Supported:**
- OpenAI (GPT-4)
- Anthropic (Claude)
- Local (Ollama)

### Task 5: Debug Performance Issue

**Scenario:** Win rate below 55%

**Diagnostic Steps:**

```bash
# 1. Identify weak symbol
python << 'EOF'
import json
from pathlib import Path
narration = Path('narration.jsonl')  # repo root
by_symbol = {}
with open(narration) as f:
    for line in f:
        t = json.loads(line)
        if t['event_type'] == 'TRADE_CLOSED':
            s = t['symbol']
            if s not in by_symbol: by_symbol[s] = {'w': 0, 'l': 0}
            if t['details']['pnl_usd'] > 0: by_symbol[s]['w'] += 1
            else: by_symbol[s]['l'] += 1

for s in by_symbol:
    total = by_symbol[s]['w'] + by_symbol[s]['l']
    wr = by_symbol[s]['w'] / total
    print(f"{s}: {wr:.1%} ({by_symbol[s]['w']}/{total})")
EOF

# 2. Test that symbol in isolation
python << 'EOF'
from systems.multi_signal_engine import MultiSignalEngine
from brokers.oanda_connector import OandaConnector

engine = MultiSignalEngine()
connector = OandaConnector(...)

symbol = 'GBP_USD'  # Weak symbol
candles = connector.get_candles(symbol, 'H4', 100)

signal, conf, _ = engine.scan_symbol(symbol, candles)
print(f"{symbol}: {signal} (confidence={conf})")

# Check which strategies agree
for strategy_name, result in engine.get_strategy_votes(symbol, candles).items():
    print(f"  {strategy_name}: {result['direction']} ({result['confidence']}%)")
EOF

# 3. Backtest that symbol with different parameters
python backtest/runner.py --symbol GBP_USD --tuning-mode

# 4. If still bad: disable strategy or increase SL
# Option A: Disable strategy
# Edit strategies/registry.py - remove weak strategy
# Option B: Increase SL distance
# Edit risk/momentum_adaptive_sl.py - increase ATR multiplier
```

### Task 6: Deploy to Cloud (AWS/GCP)

**For high availability:**

```dockerfile
# Dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
ENV OANDA_PRACTICE_TOKEN=secret
CMD ["python", "-u", "oanda_trading_engine.py"]
```

```bash
# Build & push
docker build -t rbotzilla:latest .
docker tag rbotzilla:latest gcr.io/PROJECT_ID/rbotzilla:latest
docker push gcr.io/PROJECT_ID/rbotzilla:latest

# Deploy to Cloud Run/GKE
gcloud run deploy rbotzilla --image gcr.io/PROJECT_ID/rbotzilla:latest \
  --set-env-vars OANDA_PRACTICE_TOKEN=secret
```

---

## Testing for AI

### Write a Test

```python
# tests/test_bullish_wolf.py
import pytest
from strategies.bullish_wolf import BullishWolf

def test_bullish_wolf_signal():
    strat = BullishWolf()
    
    # Create mock candles (uptrend then consolidation)
    candles = [...]  # Your test data
    
    signal, conf, details = strat.scan(candles)
    
    assert signal == 'LONG'
    assert conf > 60
    assert 'trap_high' in details

# Run test
# pytest tests/test_bullish_wolf.py -v
```

### Backtest a Strategy Change

```bash
python backtest/runner.py --symbol EUR_USD --strategy bullish_wolf

# Results show:
# - Win rate
# - P&L
# - Max drawdown
# - Sharpe ratio
```

---

## Common Mistakes for AI to Avoid

❌ **Don't:**
- Violate charter limits (code will reject)
- Change PIN without updating env var
- Commit secrets.env to git (use .gitignore)
- Modify lot size higher than Kelly permits
- Add strategy without registering in registry
- Change narration format (breaks analysis)

✅ **Do:**
- Test on paper before going live
- Backtest any strategy changes
- Monitor margin constantly
- Keep git history clean
- Log all decisions to narration
- Version bumps on deployments

---

## Extending for AI

### Scale to More Symbols

Currently: EUR_USD, GBP_USD, USD_JPY

To add YEN pairs:
1. Add to scanner loop: `for symbol in ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CAD']:`
2. Verify each symbol has enough history for strategies
3. Test charter limits for more concurrent trades
4. Backtest entire system with new symbol

### Multi-Timeframe Trading

Currently: Mostly 4-hour timeframe

To add multi-timeframe:
```python
# Scan multiple timeframes
for tf in ['1H', '4H', '1D']:
    for symbol in symbols:
        signal = scan_symbol(symbol, tf)  # Modified scan
        # Use timeframe as additional factor in voting
```

### Live Trading Automation

Currently: Requires manual PIN to switch to LIVE

To auto-switch after validation:
```python
if PERFORMANCE.win_rate > 0.55 and PERFORMANCE.days >= 7:
    auto_switch_to_live()  # After validation
```

---

## Resources for AI

| Resource | Location | Use Case |
|----------|----------|----------|
| README.md | / | System overview |
| DEPLOYMENT.md | / | Setup & rebuild |
| ARCHITECTURE.md | / | System design |
| WORKFLOWS.md | / | Operations |
| MEGA_PROMPT.md | / | This file |
| API_CHEATSHEET.md | / | API quick ref |
| Code | / | Implementation |
| Logs | narration.jsonl (root) | Event analysis |
| Tests | tests/ | Unit tests |

---

## Final Checklist for AI Rebuild

- [ ] Clone repo
- [ ] Run setup.sh
- [ ] Add credentials to ops/secrets.env
- [ ] Run verify_system_ready.py (all ✓)
- [ ] Run oanda_trading_engine.py
- [ ] Verify signals in /tmp/rbz.log
- [ ] Check narration.jsonl for events
- [ ] Run "📈 Performance Analysis" task
- [ ] If paper testing good: backtest new feature
- [ ] Deploy to live if >55% win rate
- [ ] Commit to git with descriptive message

---

**This MEGA_PROMPT enables any AI agent to understand, rebuild, and extend RBOTZILLA PHOENIX.**

**Last Updated:** March 3, 2026
