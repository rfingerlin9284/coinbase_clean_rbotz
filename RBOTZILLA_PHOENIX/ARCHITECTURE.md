# 🏗️ RBOTZILLA ARCHITECTURE DOCUMENTATION

## System Design Overview

RBOTZILLA PHOENIX is built on a modular, multi-agent architecture designed for:
- **Robustness**: Multiple redundant signal sources
- **Scalability**: Easy to add strategies, brokers, agents
- **Safety**: Hard compliance gates prevent over-leveraging
- **Observability**: Comprehensive logging & dashboards

---

## 1. Entry Points & Boot Sequence

### Primary Entry Point: `oanda_trading_engine.py`

```python
# Boot sequence:
1. Load environment (credentials, mode)
2. Initialize OANDA connector
3. Load charter (compliance rules)
4. Start market data stream
5. Begin SCAN cycle:
   a. For each symbol (EUR_USD, GBP_USD, USD_JPY):
      - Fetch latest candles
      - Run through all 7 strategies
      - Aggregate signals
   b. Check compliance gates
   c. If signal passes, calculate position size
   d. Place order if conditions met
   e. Manage existing trades
   f. Log event to narration.jsonl
6. Sleep 1 second, loop to step 5
```

### Alternative Entry Points

```bash
# Headless (supervisor mode)
python headless_runtime.py --broker oanda

# Paper mode direct
python scripts/oanda_paper.py

# Coinbase engine
python scripts/coinbase_headless.py --env sandbox

# Dashboard only
streamlit run dashboard/app_enhanced.py

# WebSocket data feed
python dashboard/websocket_server.py
```

---

## 2. Core Modules & Their Interactions

### A. Signal Generation Pipeline

```
Market Data Stream (WebSocket)
    ↓ (1Hz polling)
CandleBuffer (keeps last 100 candles per symbol)
    ↓
7 Strategy Detectors (parallel scan):
    ├─ momentum_sma.py (SMA moving average)
    ├─ ema_stack.py (EMA confirmation)
    ├─ fvg.py (Fair value gap detection)
    ├─ fibonacci.py (Fib confluence)
    ├─ liquidity_sweep.py (Smart money logic)
    ├─ trap_reversal.py (Trap entry detection)
    └─ rsi_extreme.py (RSI extremes)
    ↓
Signal Aggregator (momentum_signals.py):
    - Weighted vote from each strategy
    - Confidence scoring (0-100)
    - Direction: BUY/SELL/NEUTRAL
    ↓
Multi-Signal Engine (multi_signal_engine.py):
    - Combines all symbols
    - Ranks signals by strength
    - Returns top trade candidates
    ↓
Optional Hive Mind AI:
    - Narrative analysis (rick_hive_mind.py)
    - Market regime assessment
    - Adaptive parameter adjustment
```

**Key File:** `systems/multi_signal_engine.py`
```python
def scan_symbol(self, symbol, candles):
    """
    Scan single symbol through all strategies.
    Returns: (signal_type, confidence, details)
    """
    signals = {
        'momentum_sma': strategy_momentum_sma(candles),
        'ema_stack': strategy_ema_stack(candles),
        # ... 5 more
    }
    # Weighted average
    confidence = sum(w * s['confidence'] for w, s in signals.items())
    direction = 'BUY' if confidence > 50 else 'SELL' if confidence < -50 else 'NEUTRAL'
    return (direction, abs(confidence), details)
```

---

### B. Compliance & Risk Gates

```
Signal (Direction + Confidence)
    ↓
Charter System (foundation/rick_charter.py):
    ├─ Rule 1: Notional limit ($15k min per trade)
    │  └─ Check: (lot_size * pip_value * distance_to_sl) >= $15k
    │
    ├─ Rule 2: Margin gate (18.3% minimum)
    │  └─ Check: available_margin / account_nav >= 0.183
    │
    ├─ Rule 3: Pair correlation (max 0.75)
    │  └─ Check: No 3 correlated pairs open simultaneously
    │
    ├─ Rule 4: Max concurrent trades (3)
    │  └─ Check: open_trade_count < 3
    │
    └─ Rule 5: Time-based (market hours only)
       └─ Check: Current time in active trading window
    ↓
  ✅ ALL GATES PASS → Proceed to sizing
  ❌ ANY GATE FAILS → SKIP trade, log rejection
```

**Key File:** `foundation/rick_charter.py`
```python
class RickCharter:
    MIN_NOTIONAL = 15000  # Hard minimum
    MIN_MARGIN_PERCENT = 0.183
    CORRELATION_THRESHOLD = 0.75
    MAX_CONCURRENT_TRADES = 3
    
    def validate_trade(self, symbol, direction, account):
        """Returns (is_valid, reason_if_invalid)"""
        if account['margin'] < self.MIN_MARGIN_PERCENT * account['nav']:
            return False, "Margin too low"
        # ... more checks
        return True, None
```

---

### C. Position Sizing

```
Signal passes charter ✅
    ↓
Risk Manager (risk/dynamic_sizing.py):
    ├─ Input: Historical win rate, P&L stats
    ├─ Calculate Kelly fraction:
    │  f* = (win% * avg_win - loss% * avg_loss) / avg_win
    │  Conservative: f = f* * 0.25  (25% Kelly)
    │
    ├─ Determine lot size:
    │  lots = (f * account_equity) / risk_per_lot
    │
    └─ Output: Position size (0.1 - 2.0 lots)
    ↓
Momentum Adaptive SL (risk/momentum_adaptive_sl.py):
    ├─ Calculate dynamic stop loss based on:
    │  - Current volatility (ATR)
    │  - Momentum profile
    │  - Support/resistance levels
    │
    └─ Output: SL distance (15-100 pips)
    ↓
OCO Validator (risk/oco_validator.py):
    ├─ One-Cancels-Other order setup:
    │  - Buy limit/stop
    │  - SL stop-loss
    │  - TP take-profit
    │
    └─ Verify order validity
```

**Key File:** `risk/dynamic_sizing.py`
```python
def calculate_kelly_lot_size(self, symbol, account_equity, risk_per_lot=50):
    """
    Kelly Criterion position sizing.
    Returns: (lot_size, confidence)
    """
    # Fetch performance stats
    stats = performance_analyzer.get_symbol_stats(symbol)
    win_rate = stats['win_rate']  # e.g., 0.55
    avg_win = stats['avg_win']    # e.g., $125
    avg_loss = stats['avg_loss']  # e.g., $75
    
    # Kelly formula
    f_opt = (win_rate * avg_win - (1-win_rate) * avg_loss) / avg_win
    f_conservative = f_opt * 0.25  # 25% Kelly (safer)
    
    # Lot size from Kelly
    lot_size = (f_conservative * account_equity) / risk_per_lot
    return min(lot_size, 2.0), f_conservative  # Cap at 2.0 lots
```

---

### D. Order Execution & Management

```
Position Size + Entry Signal
    ↓
OANDA Connector (brokers/oanda_connector.py):
    ├─ Place order (BUY/SELL)
    ├─ Set SL (tight)
    ├─ Set TP (optional)
    └─ Return trade ID
    ↓
Trade Management Loop:
    ├─ Monitor trade P&L every 1 second
    ├─ Tight Two-Step SL:
    │  Step 1: ATR-based initial SL
    │  Step 2: Scale to breakeven after X pips profit
    │
    ├─ Aggressive Trailing:
    │  - As trade goes +50% of target range, tighten SL
    │  - Move SL up by 70% of profit gained
    │
    ├─ TP Guard:
    │  - Don't close early if momentum strong
    │  - TP only closes if signal flips
    │
    └─ Scale-Out:
       - At +50% of risk: close 50% position
       - At +100% of risk: close 25% more
    ↓
Trade Closes (SL or TP hit)
    ↓
Narration Logger:
    └─ Log event: {timestamp, symbol, pnl, rr_ratio, duration}
```

**Key File:** `brokers/oanda_connector_enhanced.py`
```python
def place_trade(self, symbol, direction, lot_size, stop_loss_pips, take_profit_pips):
    """
    Place OCO order on OANDA.
    Returns: trade_id
    """
    order_data = {
        "orders": [{
            "type": "MARKET",
            "instrument": symbol,
            "units": int(lot_size * 100000),  # Convert lots to units
            "takeProfitOnFill": {"price": tp_price},
            "stopLossOnFill": {"price": sl_price}
        }]
    }
    # Submit via OANDA API v3
    response = self.api.request(OrderCreate(self.account_id, order_data))
    return response['orderFillTransaction']['id']
```

---

## 3. Mode System (PAPER vs LIVE)

```
configs/runtime_mode.json:
{
  "mode": "PAPER",  // or "LIVE"
  "headless": true,
  "brokers": {"oanda": {"enabled": true}}
}
    ↓
Mode Manager (util/mode_manager.py):
    ├─ Switching logic (requires PIN for LIVE)
    ├─ Persists mode to config file
    ├─ Triggers broker reconnection
    └─ Logs mode changes
    ↓
Engine detects mode at startup:
    PAPER:
      ├─ Connection string: practice.oanda.com
      ├─ Simulated fills
      └─ No real P&L
    │
    LIVE:
      ├─ Connection string: stream-fxpractice.oanda.com (LIVE)
      ├─ Real money trades
      ├─ Real P&L
      └─ Requires PIN confirmation
```

**Key File:** `util/mode_manager.py`
```python
def switch_mode(new_mode, pin=None):
    """Switch between PAPER and LIVE modes."""
    if new_mode == 'LIVE' and pin != os.environ.get('RICK_PIN'):
        raise Exception("Invalid PIN for LIVE mode")
    
    config = json.load(open('configs/runtime_mode.json'))
    config['mode'] = new_mode
    json.dump(config, open('configs/runtime_mode.json', 'w'))
    # Reconnect broker
    restart_broker_connection()
```

---

## 4. Hive Mind AI System (Optional)

```
Market Event
    ↓
Hive Mind Processor (hive/hive_mind_processor.py):
    ├─ Extract narrative context
    ├─ Format as LLM prompt
    └─ Send to orchestrator
    ↓
LLM Orchestrator (hive/hive_llm_orchestrator.py):
    ├─ Router to LLM provider:
    │  ├─ OpenAI (GPT-4)
    │  ├─ Anthropic (Claude)
    │  └─ Local (Ollama)
    │
    ├─ Prompt: "EUR_USD forming bullish pattern. Current signal: BUY, conf=78%"
    │           "What is your assessment? Agree/Disagree/Wait?"
    │
    └─ Parse response → confidence adjustment
    ↓
Rick Hive Mind (hive/rick_hive_mind.py):
    ├─ Adaptive behavior based on AI consensus
    ├─ May adjust:
    │  - Position size (increase if AI agrees)
    │  - Stop loss (tighten if AI warns)
    │  - Target symbols (focus on strong agrees)
    │
    └─ Log all AI decisions to audit trail
    ↓
Guardian Gates (hive/guardian_gates.py):
    ├─ Verify AI recommendations don't violate charter
    ├─ Hard stops remain: no mode it can override
    └─ AI can only adjust non-critical parameters
```

---

## 5. Swarm Agent System (Multi-Vote Trading)

```
Trade Signal Generated
    ↓
Swarm Orchestrator (swarm/orchestrator.py):
    ├─ Create voting session
    └─ Send signal to all agents
    ↓
Swarm Agents Vote (parallel):
    ├─ Technical Agent (swarm/agents/alpha_technical.py)
    │  └─ Analyzes: momentum, confluence, setups
    │     Vote: +1 (AGREE), 0 (NEUTRAL), -1 (DISAGREE)
    │
    ├─ Risk Agent (swarm/agents/risk_agent.py)
    │  └─ Analyzes: position size, margin, correlation
    │     Vote: ±1 based on risk assessment
    │
    ├─ Audit Agent (swarm/agents/audit_agent.py)
    │  └─ Analyzes: compliance, charter adherence
    │     Vote: ±1 based on rule violations
    │
    └─ Master Agent decides:
       ├─ Tally votes → confidence score
       ├─ If net positive → EXECUTE
       └─ If net negative → SKIP with reason
```

---

## 6. Logging & Events (Narration System)

```
Every trade event:
    ↓
Narration Logger (util/narration_logger.py):
    ├─ Event types:
    │  ├─ TRADE_OPENED: signal place + price
    │  ├─ TRADE_UPDATE: SL moved, TP adjusted
    │  ├─ SCALE_OUT: partial close
    │  ├─ TRADE_CLOSED: final P&L
    │  └─ REJECTION: why trade skipped
    │
    └─ Format: JSONL (one JSON object per line)
    ↓
logs/narration.jsonl:
{
  "timestamp": "2026-03-01T14:23:45.123Z",
  "event_type": "TRADE_CLOSED",
  "symbol": "EUR_USD",
  "trade_id": "12345",
  "details": {
    "direction": "LONG",
    "entry_price": 1.0852,
    "exit_price": 1.0878,
    "pnl_usd": 65.00,
    "pnl_pips": 26,
    "rr_executed": 2.3,
    "duration_minutes": 23,
    "sl": 1.0825,
    "tp": 1.0900,
    "confidence": 0.78
  }
}
```

---

## 7. Performance Analytics

```
Trade Closes
    ↓
Performance Analyzer (backtest/analyzer.py):
    ├─ Parse narration.jsonl
    ├─ Calculate:
    │  ├─ Win rate % (target: 55%+)
    │  ├─ Total P&L
    │  ├─ Avg win / Avg loss
    │  ├─ R:R ratio (target: 2:1+)
    │  ├─ Max drawdown
    │  ├─ Sharpe ratio
    │  ├─ Per-symbol stats
    │  └─ Last 15 trades
    │
    └─ Export: JSON or display
    ↓
VS Code Task: "📈 Performance Analysis"
    └─ Shows: Win rate %, P&L, last 15 trades
```

---

## 8. Strategy Framework

```
Base Strategy (strategies/base.py):
    ├─ Interface: scan(candles: List[Candle]) → Signal
    ├─ Parameters: (inputs, weights, thresholds)
    └─ Returns: (direction: LONG/SHORT/NEUTRAL, confidence: 0-100)

Example: Bullish Wolf Pack (strategies/bullish_wolf.py):
    ├─ Input: 100 candles
    ├─ Logic:
    │  1. Find consolidation zone
    │  2. Detect bullish trap (lower low)
    │  3. Entry on breakout above trap high
    │  4. SL below trap low
    │
    ├─ Confidence: Based on:
    │  - Distance from zone
    │  - Volume confirmation
    │  - Momentum alignment
    │
    └─ Return: (BUY, 78) or (NEUTRAL, 0)

Registry (strategies/registry.py):
    ├─ Register all 10 strategies
    ├─ Auto-load on engine start
    └─ Each strategy gets equal weight in voting
```

---

## 9. Broker Abstraction Layer

```
Connector Interface:
    ├─ get_account()
    ├─ get_positions()
    ├─ place_market_order(symbol, direction, size)
    ├─ get_candles(symbol, timeframe, count)
    └─ stream_prices(symbols)

OANDA Implementation (brokers/oanda_connector.py):
    ├─ Uses oandapyV20 library
    ├─ v3 REST API endpoints
    ├─ Streaming WebSocket for prices
    └─ Full OCO order support

Coinbase Implementation (brokers/coinbase_connector.py):
    ├─ Uses coinbase-advanced-py library
    ├─ Advanced Trades API
    └─ Spot trading only

Interactive Brokers (brokers/ib_connector.py):
    ├─ Uses ib_insync library
    ├─ Futures & options support
    └─ High-frequency capable
```

---

## 10. Directory Dependency Map

```
oanda_trading_engine.py
    ├─ Imports: foundation/rick_charter.py
    ├─ Imports: brokers/oanda_connector.py
    ├─ Imports: systems/multi_signal_engine.py
    │   ├─ Imports: strategies/* (10 strategy files)
    │   ├─ Imports: systems/momentum_signals.py
    │   └─ Imports: risk/dynamic_sizing.py
    │       └─ Imports: backtest/analyzer.py
    ├─ Imports: hive/rick_hive_mind.py (optional)
    │   └─ Imports: hive/hive_llm_orchestrator.py
    ├─ Imports: swarm/orchestrator.py (optional)
    │   └─ Imports: swarm/agents/*.py
    ├─ Imports: util/* (narration_logger, mode_manager, etc.)
    ├─ Imports: ml_learning/regime_detector.py (optional)
    └─ Imports: dashboard/websocket_server.py (optional)
```

---

## 11. Configuration & Environment

```
Three-level config hierarchy:

Level 1: Environment Variables (ops/secrets.env)
    ├─ OANDA_PRACTICE_TOKEN
    ├─ BOT_MAX_TRADES
    ├─ RICK_PIN
    └─ RICK_DEV_MODE

Level 2: Config Files (configs/runtime_mode.json)
    ├─ mode: "PAPER" | "LIVE"
    ├─ headless: true | false
    ├─ brokers: {...}
    └─ history: [...]

Level 3: Code Defaults (foundation/rick_charter.py)
    ├─ MIN_NOTIONAL = 15000
    ├─ MIN_MARGIN = 0.183
    ├─ STRATEGIES_ENABLED = 7
    └─ CORRELATION_THRESHOLD = 0.75

Priority: Environment > Config File > Code Defaults
```

---

## 12. Performance & Optimization

### Bottlenecks & Solutions

| Bottleneck | Current | Optimization |
|-----------|---------|--------------|
| Market data polling | 1Hz | Async WebSocket (sub-ms) |
| Strategy scanning | 7 sequential | Parallel threads |
| OANDA API calls | Synchronous | Async aiohttp |
| Narration writes | Unbuffered | Write buffer (100 events) |
| Dashboard updates | 1s | Push via WebSocket |

### Threading Model
```
Main Thread:
    └─ Market data loop (1Hz)
        └─ Strategy scanning
        └─ Charter validation
        └─ Order execution

Background Threads:
    ├─ Narration writer (async batch)
    ├─ WebSocket server (async)
    ├─ Dashboard updater (async)
    ├─ Hive Mind AI (async, if enabled)
    └─ Monitor/logging (async)
```

---

## 13. Testing & Quality Assurance

### Test Pyramid
```
Unit Tests (strategies/)
    ├─ Test each strategy in isolation
    ├─ Mock OANDA connection
    └─ Verify confidence scores

Integration Tests (systems/)
    ├─ Test multi_signal_engine
    ├─ Test charter validation
    ├─ Test risk sizing
    └─ Against historical data

E2E Tests (backtest/)
    ├─ Full system on historical data
    ├─ Verify P&L calculation
    ├─ Verify trade management
    └─ Generate performance report

Property-Based Tests
    ├─ Invariants: margin never <0
    ├─ Invariants: notional always >= MIN
    ├─ Invariants: P&L = entry - exit
    └─ Fuzz testing with random data
```

---

**Last Updated:** March 3, 2026
