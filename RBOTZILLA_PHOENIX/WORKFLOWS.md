# 📖 OPERATIONAL WORKFLOWS

## Daily Trading Workflow

### Pre-Market (30 minutes before market open)

**Terminal 1: Pre-flight Checks**
```bash
cd /home/rfing/RBOTZILLA_PHOENIX
source venv/bin/activate

# 1. Quick system check (2 seconds)
python verify_system_ready.py

# Expected output:
# ✓ Core Dependencies OK
# ✓ RICK Core Modules OK
# ✓ Trading Engine OK
```

**Terminal 2: Full Diagnostics (5 seconds)**
```bash
python run_diagnostics.py --json
# Outputs to /tmp/rbotzilla_diagnostics.json
```

**Terminal 3: Check Previous Day's Performance**
```bash
# Via VS Code task:
# Ctrl+Shift+P → "📈 Performance Analysis"

# Or command line:
python << 'EOF'
import json
from pathlib import Path

narration_file = Path('narration.jsonl')
if narration_file.exists():
    trades = [json.loads(line) for line in narration_file.readlines()]
    closed = [t for t in trades if t.get('event_type') == 'TRADE_CLOSED']
    if closed:
        pnl = sum(t['details']['pnl_usd'] for t in closed[-100:])
        win_rate = sum(1 for t in closed[-100:] if t['details']['pnl_usd'] > 0) / len(closed[-100:])
        print(f"Last 100 trades: {win_rate:.1%} win rate | P&L: ${pnl:+.2f}")
EOF
```

**Terminal 4: Open Market Monitoring (4 terminals)**
```bash
# Live scanning (shows real-time trades)
tail -f /tmp/rbz.log | grep -E "SCAN:|Placing"

# Event stream (narration.jsonl is at repo root)
tail -f narration.jsonl | python -m json.tool

# Account balance updates
watch -n 10 'python scripts/check_positions.py'

# Dashboard (optional — Flask-SocketIO, not Streamlit)
python dashboard/app_enhanced.py
```

### Market Open

**Start Bot**
```bash
# Via VS Code (recommended):
Ctrl+Shift+B  # Runs "▶ Start Bot (Paper)"

# Or command line:
python -u oanda_trading_engine.py

# Or headless:
python headless_runtime.py --broker oanda &
```

**Monitor First Hour**
- Check logs for errors
- Verify signals are being generated
- Confirm trades are executing (if conditions met)
- Monitor P&L updates in real-time

### During Market Hours (Every 30 minutes)

**Check Performance Metrics**
```bash
# Via VS Code:
Ctrl+Shift+P → "📈 Performance Analysis"

# Look for:
# - Win Rate: Should be ≥55%
# - Per-symbol stats: Identify weak symbols
# - Last 15 trades: Recent trend
```

**Review Recent Trades**
```bash
# Last 5 trades
tail -5 narration.jsonl | python -m json.tool

# Analyze:
# - Was entry price good?
# - Was SL appropriate?
# - Did TP make sense?
# - Any patterns in losses?
```

**Check Margin & Risk**
```bash
# Via VS Code:
Ctrl+Shift+P → "💰 Get Account Balance"

# Verify:
# - Margin available > 20%
# - No trades at risk limit
# - Balance is reasonable
```

### Mid-Day Review (Lunch)

```bash
# Export diagnostics
python run_diagnostics.py --json

# Analyze:
jq '.systems | keys[]' /tmp/rbotzilla_diagnostics.json

# Check for warnings
grep -i "warn" /tmp/rbz.log | tail -10
```

### Market Close (30 minutes before)

**Prepare for Close**
```bash
# Check if any trades should close early
tail -20 narration.jsonl | grep TRADE_CLOSED

# Review day's P&L
python << 'EOF'
import json
from datetime import datetime, timedelta
from pathlib import Path

narration_file = Path('narration.jsonl')
today_start = datetime.now().replace(hour=0, minute=0, second=0)

with open(narration_file) as f:
    today_closed = []
    for line in f:
        trade = json.loads(line)
        if trade.get('event_type') == 'TRADE_CLOSED':
            ts = datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00'))
            if ts > today_start:
                today_closed.append(trade)

pnl = sum(t['details']['pnl_usd'] for t in today_closed)
wins = sum(1 for t in today_closed if t['details']['pnl_usd'] > 0)
print(f"Today: {len(today_closed)} trades | {wins} wins | ${pnl:+.2f} P&L")
EOF
```

### End-of-Day Shutdown

**1. Stop Bot (Gracefully)**
```bash
# Via VS Code:
Ctrl+Shift+P → "⏹ Stop Bot"

# Or command line:
pkill -f oanda_trading_engine.py

# Bot will:
# - Close remaining positions
# - Write final trade events
# - Exit cleanly
```

**2. Save Checkpoint**
```bash
# Via VS Code:
Ctrl+Shift+P → "💾 Git Save"

# Or command line:
cd /home/rfing/RBOTZILLA_PHOENIX
git add -A
git commit -m "EOD checkpoint: $(date '+%Y-%m-%d %H:%M')"
```

**3. Daily Report**
```bash
python << 'EOF'
import json
from datetime import datetime
from pathlib import Path

narration = Path('narration.jsonl')
report = {
    'date': datetime.now().isoformat(),
    'total_trades': 0,
    'wins': 0,
    'losses': 0,
    'pnl': 0,
    'by_symbol': {}
}

with open(narration) as f:
    for line in f:
        trade = json.loads(line)
        if trade['event_type'] == 'TRADE_CLOSED':
            symbol = trade['symbol']
            pnl = trade['details']['pnl_usd']
            
            report['total_trades'] += 1
            report['pnl'] += pnl
            if pnl > 0:
                report['wins'] += 1
            else:
                report['losses'] += 1
            
            if symbol not in report['by_symbol']:
                report['by_symbol'][symbol] = {'wins': 0, 'losses': 0, 'pnl': 0}
            report['by_symbol'][symbol]['pnl'] += pnl
            if pnl > 0:
                report['by_symbol'][symbol]['wins'] += 1
            else:
                report['by_symbol'][symbol]['losses'] += 1

# Print report
print(json.dumps(report, indent=2))

# Save to file
with open(f"daily_reports/{datetime.now().strftime('%Y%m%d')}_report.json", 'w') as f:
    json.dump(report, f, indent=2)
EOF
```

---

## Weekly Review Workflow

**Every Friday (After Market Close)**

```bash
# 1. Comprehensive diagnostics
python verify_system.py  # 130+ checks

# 2. Full backtest analysis
python backtest/analyzer.py --export-json backtest/results/weekly_summary.json

# 3. Review performance trends
python << 'EOF'
import json
from pathlib import Path

narration = Path('narration.jsonl')
by_day = {}

with open(narration) as f:
    for line in f:
        trade = json.loads(line)
        if trade['event_type'] == 'TRADE_CLOSED':
            date = trade['timestamp'][:10]  # YYYY-MM-DD
            pnl = trade['details']['pnl_usd']
            
            if date not in by_day:
                by_day[date] = {'trades': 0, 'pnl': 0, 'wins': 0}
            by_day[date]['trades'] += 1
            by_day[date]['pnl'] += pnl
            if pnl > 0:
                by_day[date]['wins'] += 1

# Show weekly trend
for date in sorted(by_day.keys())[-5:]:
    stats = by_day[date]
    win_rate = stats['wins'] / stats['trades'] if stats['trades'] > 0 else 0
    print(f"{date}: {stats['trades']:2} trades | {win_rate:5.1%} | ${stats['pnl']:+7.2f}")
EOF

# 4. Identify weak symbols (below 55% win rate)
python << 'EOF'
import json
from pathlib import Path

narration = Path('narration.jsonl')
by_symbol = {}

with open(narration) as f:
    for line in f:
        trade = json.loads(line)
        if trade['event_type'] == 'TRADE_CLOSED':
            symbol = trade['symbol']
            if symbol not in by_symbol:
                by_symbol[symbol] = []
            by_symbol[symbol].append(trade)

for symbol in ['EUR_USD', 'GBP_USD', 'USD_JPY']:
    trades = by_symbol.get(symbol, [])
    if not trades:
        continue
    wins = sum(1 for t in trades if t['details']['pnl_usd'] > 0)
    win_rate = wins / len(trades)
    pnl = sum(t['details']['pnl_usd'] for t in trades)
    
    status = "✅" if win_rate >= 0.55 else "⚠️"
    print(f"{status} {symbol}: {win_rate:.1%} ({wins}/{len(trades)}) | ${pnl:+.2f}")
EOF

# 5. Review charter violations
grep "Charter violation" logs/parameter_changes.log | tail -20

# 6. Check for memory leaks or crashes
dmesg | tail -20
grep -i "error\|exception" /tmp/rbz.log | tail -10
```

**Decisions to Make:**
- Symbol underperforming? Disable in strategy registry
- Win rate below 55%? Increase SL distance or reduce lot size
- High drawdown? Reduce leverage or enable Hive Mind AI
- Good results? Consider going live (if paper trading)

---

## Mode Switching Workflow (PAPER → LIVE)

### Pre-Live Checklist

```bash
# 1. Win rate verification (must be >55% for 24+ hours)
# Run "📈 Performance Analysis" task daily for 1 week

# 2. Verify all safety checks pass
bash verify_live_safety.sh

# 3. Test with small capital
# Switch to LIVE, trade with minimal lot size (0.1 lots)

# 4. Run full diagnostics
python run_diagnostics.py

# 5. Backup all configs
cp -r configs/ backups/configs.$(date +%s)/
cp ops/secrets.env backups/secrets.env.$(date +%s)

# 6. Final confirmation
echo "Ready for LIVE? (type YES): "
read confirm
if [[ "$confirm" != "YES" ]]; then
    echo "Cancelled"
    exit 1
fi
```

### Mode Switch Command

**Warning: Requires PIN (841921 by default)**

```bash
# Via Python
python << 'EOF'
from util.mode_manager import switch_mode
switch_mode('LIVE', pin=841921)  # Pin stored in env
print("✅ Mode switched to LIVE")
print("⚠️ Real money trades will now execute!")
EOF

# Verify mode changed
cat configs/runtime_mode.json | grep mode
```

### Post-Switch Monitoring

**First Hour (Critical):**
- Watch `/tmp/rbz.log` closely
- Monitor account balance
- Verify trades execute with real money filled
- Check P&L updates happen correctly

**First Day:**
- Run "💰 Get Account Balance" every 30 min
- Monitor margin carefully (must stay >20%)
- Set mental/email alerts for large losses
- Be ready to manually close positions if needed

**First Week:**
- Limit max trades per day manually
- Review every trade in detail
- Have emergency close script ready
- Don't change any parameters

---

## Emergency Procedures

### Emergency Close All Positions

```bash
# Via VS Code:
Ctrl+Shift+P → "🔌 Close All Positions"
# (requires YES confirmation)

# Or command line:
python << 'EOF'
from brokers.oanda_connector import OandaConnector

connector = OandaConnector(
    account_id=os.environ['OANDA_PRACTICE_ACCOUNT_ID'],
    access_token=os.environ['OANDA_PRACTICE_TOKEN'],
    environment='practice'
)

# Close each symbol
for symbol in ['EUR_USD', 'GBP_USD', 'USD_JPY']:
    connector.close_position(symbol)
    print(f"✅ Closed {symbol}")
EOF
```

### Kill Bot Immediately

```bash
# Hard kill (not recommended, but works)
pkill -9 -f oanda_trading_engine.py

# OANDA will close positions server-side
# But may result in slippage

# Better: Use graceful stop
pkill -f oanda_trading_engine.py  # Gives 5 sec to close
```

### Rollback to Previous Config

```bash
# If bad config deployed:
ls -la backups/configs.*

# Restore
cp backups/configs.1672531200/* configs/

# Restart bot
```

---

## Troubleshooting Workflow

### Bot Starts but Doesn't Generate Signals

```bash
# 1. Check if market data is flowing
tail -20 /tmp/rbz.log

# 2. Verify strategies are loaded
python << 'EOF'
from strategies.registry import load_strategies
strats = load_strategies()
print(f"Loaded {len(strats)} strategies: {list(strats.keys())}")
EOF

# 3. Test signal generation manually
python << 'EOF'
from systems.multi_signal_engine import MultiSignalEngine
engine = MultiSignalEngine()
signal, conf, details = engine.scan_symbol('EUR_USD', candles)
print(f"Signal: {signal}, Confidence: {conf}")
EOF
```

### OANDA Connection Fails

```bash
# 1. Verify credentials
python scripts/check_positions.py

# 2. Test API connectivity
python << 'EOF'
from oandapyV20 import API
api = API(access_token=os.environ['OANDA_PRACTICE_TOKEN'], environment='practice')
print("✅ OANDA API connected") if api else print("❌ Failed")
EOF

# 3. Check network
ping oanda.com
```

### Memory Usage Growing

```bash
# Check memory
ps aux | grep oanda_trading_engine

# If growing: likely memory leak in strategy
# Add memory profiling:
pip install memory-profiler
python -m memory_profiler oanda_trading_engine.py

# Identify which strategy/component is leaking
# Restart bot daily or weekly as temporary fix
```

### Strange P&L not matching

```bash
# 1. Verify all trades logged
grep TRADE_CLOSED narration.jsonl | wc -l

# 2. Manually calculate
python << 'EOF'
import json
with open('narration.jsonl') as f:
    trades = [json.loads(line) for line in f if 'TRADE_CLOSED' in line]
    manual_pnl = sum(t['details']['pnl_usd'] for t in trades)
    print(f"Manual calculation: ${manual_pnl:.2f}")

# Compare with OANDA account balance change
EOF
```

---

## Maintenance Workflow (Weekly)

```bash
# 1. Update code
git fetch origin
git merge origin/main

# 2. Reinstall dependencies
pip install --upgrade -r requirements.txt

# 3. Run full test suite
pytest tests/ -v

# 4. Backup data
tar -czf backups/backup_$(date +%Y%m%d).tar.gz logs/ configs/

# 5. Check disk usage
du -sh .
du -sh logs/  # Should stay <1GB (rotate old logs)

# 6. Verify all safety systems
python verify_system.py
bash verify_live_safety.sh
```

---

**Last Updated:** March 3, 2026
