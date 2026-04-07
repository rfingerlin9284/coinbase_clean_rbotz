# 🤖 RBOTZILLA PHOENIX - Autonomous Trading Bot System

**Status:** Production-Ready Prototype | **Mode:** Paper Trading | **Date:** March 2026

---

## 🎯 Executive Summary

**RBOTZILLA PHOENIX** is a comprehensive, multi-agent automated trading system that trades forex pairs (EUR_USD, GBP_USD, USD_JPY) on OANDA. The system combines:

- **Multi-Strategy Engine**: 10+ technical analysis strategies with AI-powered signal aggregation
- **Risk Management Charter**: Hard stops on notional exposure, margin, pair correlation
- **Hive Mind AI Integration**: OpenAI/Claude agents for narrative analysis & adaptive trading
- **Swarm Agent Architecture**: Specialized agents (technical, risk, audit) voting on trades
- **Real-time Monitoring**: Live dashboard, narration logs, performance analytics
- **VS Code Integration**: 33 automation tasks for complete workflow management

**Target Metrics:**
- Win Rate: 55%+ (tracked per-symbol)
- Risk/Reward Ratio: 2:1+
- Capital Allocation: Dynamic position sizing based on regime

---

## 🚀 Quick Start (5 Minutes)

### 1. Clone & Setup
```bash
git clone https://github.com/rfingerlin9284/rbotzilla_pheonix.git
cd rbotzilla_pheonix
bash setup.sh
```

### 2. Configure Credentials
```bash
cp ops/secrets.env.template ops/secrets.env
# Edit ops/secrets.env with your OANDA credentials:
# OANDA_PRACTICE_ACCOUNT_ID=<your_account_id>
# OANDA_PRACTICE_TOKEN=<your_practice_token>
```

### 3. Start Bot
```bash
# Option A: Command line
python -u oanda_trading_engine.py

# Option B: VS Code (recommended for monitoring)
# Press Ctrl+Shift+B (or Ctrl+Shift+P → Run Task → Start Bot)
```

### 4. Monitor Performance
```bash
# Terminal 1: Real-time scan log
Ctrl+Shift+P → 📡 Scan Log (live tail)

# Terminal 2: Performance metrics
Ctrl+Shift+P → 📈 Performance Analysis

# Terminal 3: Event stream
Ctrl+Shift+P → 📜 Narration Log (live tail)
```

---

## 📋 System Architecture

### Core Components

```
RBOTZILLA_PHOENIX/
├── oanda_trading_engine.py          # 🎯 Main bot entrypoint
├── configs/runtime_mode.json        # PAPER/LIVE mode switcher
├── requirements.txt                 # All dependencies
│
├── brokers/                         # Exchange connectors
│   ├── oanda_connector.py
│   ├── oanda_connector_enhanced.py
│   ├── coinbase_connector.py
│   └── ib_connector.py
│
├── strategies/                      # 10+ trading strategies
│   ├── bullish_wolf.py
│   ├── bearish_wolf.py
│   ├── fib_confluence_breakout.py
│   ├── liquidity_sweep.py
│   ├── institutional_sd.py
│   └── [6 more...]
│
├── systems/                         # Signal aggregation & execution
│   ├── multi_signal_engine.py       # Combines all signals
│   ├── momentum_signals.py
│   └── [execution layer]
│
├── risk/                            # Risk control & position sizing
│   ├── dynamic_sizing.py            # Kelly-based position sizing
│   ├── momentum_adaptive_sl.py       # Stop loss management
│   ├── risk_control_center.py
│   ├── oco_validator.py             # One-Cancels-Other validation
│   └── backtest/risk/               # Backtest risk gates
│
├── hive/                            # AI agent integration
│   ├── rick_hive_mind.py            # OpenAI orchestration
│   ├── hive_mind_processor.py       # Event processing
│   ├── hive_llm_orchestrator.py     # LLM coordination
│   ├── adaptive_rick.py             # Adaptive behavior
│   └── guardian_gates.py            # Safety gates
│
├── swarm/                           # Multi-agent voting system
│   ├── swarm_bot.py
│   ├── orchestrator.py
│   └── agents/
│       ├── base_agent.py
│       ├── alpha_technical.py
│       ├── risk_agent.py
│       └── audit_agent.py
│
├── foundation/                      # Core compliance
│   ├── rick_charter.py              # Hard position limits
│   └── margin_correlation_gate.py   # Margin & correlation checks
│
├── ml_learning/                     # Machine learning components
│   ├── regime_detector.py           # Market regime classification
│   ├── signal_analyzer.py           # Signal strength scoring
│   ├── pattern_learner.py
│   └── optimizer.py
│
├── dashboard/                       # Web visualization
│   ├── app_enhanced.py              # Streamlit dashboard
│   ├── websocket_server.py          # Real-time feed
│   └── live_dashboard.html
│
├── backtest/                        # Historical analysis
│   ├── runner.py                    # Backtest execution
│   ├── analyzer.py                  # Results aggregation
│   ├── narrator.py                  # Event narration
│   ├── data_loader.py
│   └── venue_params.py
│
├── util/                            # Utilities
│   ├── narration_logger.py          # Event logging (JSONL)
│   ├── mode_manager.py              # PAPER/LIVE switching
│   ├── positions_registry.py        # Position tracking
│   ├── parameter_manager.py
│   ├── timezone_manager.py
│   └── [10+ more utilities]
│
├── scripts/                         # Executable scripts
│   ├── check_positions.py           # OANDA position snapshot
│   ├── oanda_paper.py               # Paper mode launcher
│   ├── coinbase_headless.py         # Coinbase headless
│   ├── rbot_ctl.sh                  # CLI control wrapper
│   └── start_headless.sh
│
├── logs/                            # Runtime logs
│   ├── narration.jsonl              # All trade events (JSONL)
│   ├── parameter_changes.log        # Audit trail
│   └── strict_runtime_*.txt         # Compliance logs
│
├── audit_logs/                      # Compliance & security
├── audit_reports/                   # Generated audit reports
├── backups/                         # Configuration backups
├── .vscode/tasks.json               # ⭐ 33 automation tasks
│
└── [Documentation files]
    ├── README.md                    # This file
    ├── DEPLOYMENT.md                # Deployment & rebuild guide
    ├── ARCHITECTURE.md              # Detailed system design
    ├── WORKFLOWS.md                 # Operational procedures
    ├── MEGA_PROMPT.md               # AI agent capabilities
    └── API_CHEATSHEET.md            # Quick API reference
```

### Data Flow Architecture

```
Market Data (OANDA WebSocket)
    ↓
Multi-Strategy Scanner (7 detectors)
    ↓
Signal Aggregator (momentum_signals.py)
    ↓
Hive Mind AI (rick_hive_mind.py) → Optional narrative analysis
    ↓
Charter Compliance (rick_charter.py) → Hard gates
    ├─ Notional limit check
    ├─ Margin availability check
    └─ Pair correlation check
    ↓
Risk Sizing (dynamic_sizing.py) → Position size calculation
    ↓
Order Placement (oanda_connector.py)
    ↓
Trade Management
    ├─ Tight two-step SL (rbz_tight_trailing.py)
    ├─ Aggressive trailing on winners
    ├─ TP guard to prevent early closes
    └─ Scale-out on momentum
    ↓
Narration Logger (narration_logger.py)
    ↓
Performance Analytics (Performance Analysis task)
```

---

## ⚙️ Configuration

### Runtime Mode
```bash
# View current mode
cat configs/runtime_mode.json

# Switch to PAPER (safe testing)
python -c "from util.mode_manager import switch_mode; switch_mode('PAPER', pin=841921)"

# Switch to LIVE (requires PIN)
python -c "from util.mode_manager import switch_mode; switch_mode('LIVE', pin=841921)"

# Or use VS Code task: Ctrl+Shift+P → "Mode → Paper"
```

### Environment Variables
```bash
# ops/secrets.env (create from template)
ENABLE_DASHBOARD=0
ENABLE_OANDA=1
ENABLE_COINBASE=0

OANDA_PRACTICE_ACCOUNT_ID=xxxxx
OANDA_PRACTICE_TOKEN=xxxxx
OANDA_LIVE_ACCOUNT_ID=xxxxx
OANDA_LIVE_TOKEN=xxxxx

BOT_MAX_TRADES=3          # Max concurrent trades
RICK_PIN=841921           # Master PIN for mode switching
RICK_DEV_MODE=1           # Development mode flag
RICK_AGGRESSIVE_LEVERAGE=3
```

### Charter Compliance Settings
(From foundation/rick_charter.py)
```python
MIN_NOTIONAL = 15000      # Min per-trade notional
MIN_MARGIN = 18.3%        # Min margin % before stopping
STRATEGIES_ENABLED = 7    # Signal detectors active
MAX_PAIRS_CORRELATED = 0.75  # Correlation threshold
```

---

## 🎮 Control & Monitoring

### VS Code Tasks (Keyboard Shortcuts)
```
Ctrl+Shift+B               ▶ Start Bot (Paper)
Ctrl+Shift+P → "Stop"      ⏹ Stop Bot
Ctrl+Shift+P → "Restart"   🔄 Restart Bot
Ctrl+Shift+P → "Verify"    ✅ Quick System Check
Ctrl+Shift+P → "Diag"      🔍 Full Diagnostics
Ctrl+Shift+P → "Perf"      📈 Performance Analysis
```

### Command Line
```bash
# Start bot
python -u oanda_trading_engine.py --env practice

# Start headless (no TTY required)
python headless_runtime.py --broker oanda

# Check positions
python scripts/check_positions.py

# View logs
tail -f /tmp/rbz.log
tail -f logs/narration.jsonl

# System audit
bash system_audit.sh

# Run diagnostics
python run_diagnostics.py --json

# Verify system ready
python verify_system_ready.py

# Comprehensive feature test (130+ checks)
python verify_system.py
```

### Web Dashboard
```bash
# Start Streamlit dashboard
streamlit run dashboard/app_enhanced.py

# Start WebSocket server (real-time updates)
python dashboard/websocket_server.py

# Access at http://localhost:8501
```

---

## 📊 Performance Tracking

### Performance Analysis Task
Run `Ctrl+Shift+P → 📈 Performance Analysis` to see:
- **Win Rate %** (target: 55%+)
- **Total P&L** in USD
- **Avg Win / Avg Loss** amounts
- **R:R Ratio** (reward/risk; target: 2:1+)
- **Per-Symbol Stats** (EUR_USD, GBP_USD, USD_JPY)
- **Last 15 Trades** with timestamps and outcomes

### Narration Log (JSONL Format)
```bash
tail -f logs/narration.jsonl | python -m json.tool
```

Format:
```json
{
  "timestamp": "2026-03-01T14:23:45Z",
  "event_type": "TRADE_CLOSED",
  "symbol": "EUR_USD",
  "details": {
    "direction": "LONG",
    "pnl_usd": 45.50,
    "rr_executed": 2.3,
    "duration_minutes": 15
  }
}
```

---

## 🔧 Development & Customization

### Adding a New Strategy
1. Create `strategies/my_strategy.py` inheriting from `strategy/base.py`
2. Implement `scan(candles) → signal` method
3. Register in `strategies/registry.py`
4. Signal automatically integrated into multi_signal_engine

### Modifying Charter Limits
Edit `foundation/rick_charter.py`:
```python
class RickCharter:
    MIN_NOTIONAL = 15000      # Change this
    MIN_MARGIN_PERCENT = 18.3  # Or this
    CORRELATION_THRESHOLD = 0.75  # Or this
```

### Tuning Position Sizing
Edit `risk/dynamic_sizing.py`:
```python
# Kelly Criterion for position sizing
f_kelly = calculate_kelly_fraction(
    win_rate=0.55,  # Adjust based on performance
    avg_win=avg_win,
    avg_loss=avg_loss,
    kelly_fraction=0.25  # Adjust risk (0.25 = conservative)
)
```

### AI Integration
Edit `hive/rick_hive_mind.py` to:
- Change LLM provider (OpenAI → Claude → DeepSeek)
- Modify narrative analysis prompts
- Enable/disable adaptive positioning

---

## 🧪 Testing & Backtesting

### Quick Backtest
```bash
# Run historical test
python backtest/runner.py

# Analyze results
python backtest/analyzer.py

# Generate report
python backtest/analyzer.py --export-json backtest/results/summary.json
```

### Unit Tests
```bash
pytest tests/ -v --cov=. --cov-report=html
```

---

## 📚 Documentation Structure

| Document | Purpose | Audience |
|----------|---------|----------|
| **README.md** (this file) | System overview & quick start | Everyone |
| **DEPLOYMENT.md** | Installation, rebuild, upgrade | DevOps, Deployment |
| **ARCHITECTURE.md** | Detailed system design & modules | Engineers, Integrators |
| **WORKFLOWS.md** | Daily operations & procedures | Traders, Operators |
| **MEGA_PROMPT.md** | AI agent capabilities & mega command | Developers, AI Teams |
| **API_CHEATSHEET.md** | OANDA & broker APIs quick ref | Developers |

---

## 🔐 Security & Compliance

- **Live Mode PIN**: 841921 (stored in env vars)
- **Notional Limits**: Hard stops prevent over-leveraging
- **Margin Gates**: System stops trading if margin drops below 18.3%
- **Correlation Checks**: Prevents high correlation position stacking
- **Audit Trail**: All trades logged in narration.jsonl with timestamps
- **Compliance Reports**: Generated logs in audit_reports/

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot won't start | Run `Ctrl+Shift+P → ✅ Verify System` |
| OANDA API errors | Check credentials in ops/secrets.env |
| Low win rate | Run `Ctrl+Shift+P → 📈 Performance Analysis` to identify weak symbols |
| Memory leak | Check logs with `📡 View Headless Logs` task |
| Dashboard offline | Restart with `streamlit run dashboard/app_enhanced.py` |

---

## 📞 Support & Development

- **Logs**: `/tmp/rbz.log` (real-time), `logs/narration.jsonl` (events)
- **Diagnostics**: `python run_diagnostics.py --json`
- **Audit**: `bash system_audit.sh`
- **Feature Check**: `python verify_system.py` (130+ checks)

---

## 📝 License

MIT - See LICENSE file

---

## 🎖️ Version History

| Version | Date | Notes |
|---------|------|-------|
| 1.0.0 | Mar 2026 | Initial production release |
| 0.9.0 | Feb 2026 | Beta with 33 VS Code tasks |
| 0.8.0 | Jan 2026 | Multi-agent system complete |

---

**Last Updated:** March 3, 2026  
**Maintainer:** Trading Bot Team  
**Repository:** https://github.com/rfingerlin9284/rbotzilla_pheonix
