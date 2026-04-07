# 🚀 DEPLOYMENT & REBUILD GUIDE

## Complete Setup from Zero

### Prerequisites
- Linux/macOS with bash
- Python 3.8+
- pip & virtualenv
- OANDA account (practice & live)
- 2GB disk space

### 1. Clone Repository
```bash
git clone https://github.com/rfingerlin9284/rbotzilla_pheonix.git
cd rbotzilla_pheonix
```

### 2. Automated Setup (Recommended)
```bash
bash setup.sh
```

This script:
- Creates Python 3.9 virtual environment
- Installs all dependencies from requirements.txt
- Creates logs/ directory structure
- Initializes configs/runtime_mode.json
- Generates ops/secrets.env (secrets template)
- Sets up .vscode/tasks.json if in VS Code

### 3. Manual Setup (If setup.sh fails)

**Create Virtual Environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Install Dependencies:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Create Directory Structure:**
```bash
mkdir -p logs audit_logs audit_reports backups backtest/results
chmod 755 scripts/*.sh
```

**Initialize Configuration:**
```bash
cat > configs/runtime_mode.json << 'EOF'
{
  "mode": "PAPER",
  "headless": true,
  "dashboard_enabled": false,
  "brokers": {
    "oanda": {"enabled": true},
    "coinbase": {"enabled": false}
  },
  "last_updated": "2026-03-03T00:00:00Z",
  "history": []
}
EOF
```

**Create Secrets File:**
```bash
cat > ops/secrets.env << 'EOF'
# OANDA Practice Account (for testing)
OANDA_PRACTICE_ACCOUNT_ID=your_practice_account_id
OANDA_PRACTICE_TOKEN=your_practice_token

# OANDA Live Account (requires PIN to switch)
OANDA_LIVE_ACCOUNT_ID=your_live_account_id
OANDA_LIVE_TOKEN=your_live_token

# Bot Configuration
BOT_MAX_TRADES=3
RICK_PIN=841921
RICK_DEV_MODE=1
RICK_AGGRESSIVE_LEVERAGE=3
ENABLE_DASHBOARD=0
ENABLE_OANDA=1
ENABLE_COINBASE=0
EOF
chmod 600 ops/secrets.env  # Restrict permissions
```

---

## 4. Credentials Setup

### Get OANDA Credentials
1. Log into OANDA account
2. Go to Settings → Account → API Access
3. Generate v3 REST API token (practice)
4. Generate v3 REST API token (live) if going live
5. Copy account ID and token

### Update ops/secrets.env
```bash
nano ops/secrets.env
# Add your credentials
source ops/secrets.env
```

### Verify Credentials
```bash
python << 'EOF'
import os
from oandapyV20 import API
token = os.environ.get('OANDA_PRACTICE_TOKEN')
account_id = os.environ.get('OANDA_PRACTICE_ACCOUNT_ID')
api = API(access_token=token, environment='practice')
print("✅ OANDA credentials valid") if api else print("❌ Invalid")
EOF
```

---

## 5. Verification Checklist

```bash
# Quick checks before first run
python verify_system_ready.py          # ~2 seconds
python verify_system.py                # ~10 seconds (130+ checks)
python run_diagnostics.py --json       # Full system health

# Should all show ✅ for main components
```

---

## 6. First Run (Paper Mode)

```bash
# Option A: Direct command
python -u oanda_trading_engine.py

# Option B: Headless (no TTY required)
python headless_runtime.py --broker oanda

# Option C: Via VS Code
# Press Ctrl+Shift+B (or Ctrl+Shift+P → "Start Bot")
```

**Expected Output:**
```
════════════════════════════════════════════════════
🤖 RBOTZILLA TRADING ENGINE
════════════════════════════════════════════════════
Mode: PAPER
Charter: Active (notional limit $15k)
Strategies: 7 detectors ready
Broker: OANDA (practice)
════════════════════════════════════════════════════
[14:23:45] SCAN: EUR_USD conf=0.73, signal=BUY
[14:23:46] Placing: 0.5 lot EUR_USD LONG @ 1.0854
[14:23:47] TRADE_OPENED: EUR_USD ID=12345
════════════════════════════════════════════════════
```

---

## 7. Monitoring Setup

### Terminal 1: Real-time Logs
```bash
tail -f /tmp/rbz.log | grep -E "SCAN:|Placing|TRADE_|BREAKEVEN"
```

### Terminal 2: Performance Metrics
```bash
while true; do
  python -c "from backtest.analyzer import analyze_narration; analyze_narration('logs/narration.jsonl')"
  sleep 300  # Update every 5 minutes
done
```

### Terminal 3: Dashboard (Optional)
```bash
streamlit run dashboard/app_enhanced.py
# Opens http://localhost:8501
```

---

## 8. Switching to Live Mode

**⚠️ CRITICAL: Only after extensive paper testing (24+ hours)**

```bash
# Verify live safety checks pass
bash verify_live_safety.sh

# Switch mode to LIVE (requires PIN)
python << 'EOF'
from util.mode_manager import switch_mode
switch_mode('LIVE', pin=841921)  # PIN from env var
EOF

# Or use VS Code task (not available for LIVE due to confirmation requirements)

# Verify mode switched
cat configs/runtime_mode.json
```

**Before Going Live:**
- [ ] Win rate > 55% in paper mode (24+ hours data)
- [ ] R:R ratio > 2:1
- [ ] Verified on all three symbols
- [ ] Tested overnight/weekend scenarios
- [ ] Run verify_live_safety.sh passes
- [ ] Risk limits are appropriate

---

## 9. Upgrades & Updates

### Pulling Latest Code
```bash
git fetch origin
git merge origin/main  # Assuming main branch
```

### Updating Dependencies
```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
python run_diagnostics.py  # Verify no breaks
```

### Backing Up Configuration
```bash
cp configs/runtime_mode.json backups/runtime_mode.json.$(date +%s)
cp ops/secrets.env backups/secrets.env.$(date +%s)
```

---

## 10. Docker Deployment (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
ENV OANDA_PRACTICE_TOKEN=xxxx
ENV OANDA_PRACTICE_ACCOUNT_ID=xxxx
CMD ["python", "-u", "oanda_trading_engine.py"]
```

Build & Run:
```bash
docker build -t rbotzilla:latest .
docker run -e OANDA_PRACTICE_TOKEN=xxxx \
           -e OANDA_PRACTICE_ACCOUNT_ID=xxxx \
           -v $(pwd)/logs:/app/logs \
           rbotzilla:latest
```

---

## 11. Troubleshooting Deployment

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Or check for missing modules
python -c "import oandapyV20; import pandas; import numpy"
```

### OANDA Connection Fails
```bash
# Verify credentials
echo $OANDA_PRACTICE_TOKEN
echo $OANDA_PRACTICE_ACCOUNT_ID

# Test API directly
python scripts/check_positions.py
```

### Virtual Environment Issues
```bash
# Deactivate & recreate
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Permission Errors
```bash
# Fix script permissions
chmod +x scripts/*.sh
chmod +x *.sh

# Fix log directory
chmod 755 logs audit_logs audit_reports
```

---

## 12. Production Checklist

- [ ] All credentials in ops/secrets.env (never commit)
- [ ] .gitignore covers secrets + logs + venv
- [ ] Verified bot runs >24 hours on paper
- [ ] Performance tracking enabled (Performance Analysis task)
- [ ] Backup strategy defined (configs backed up)
- [ ] Monitoring dashboard running
- [ ] Win rate > 55% on all symbols
- [ ] System audit passing (bash system_audit.sh)
- [ ] Git repo clean & up to date
- [ ] README documentation reviewed

---

## 13. Backup & Recovery

### Automatic Backups
```bash
# Backup configs every 6 hours
(crontab -l; echo "0 */6 * * * cp /home/rfing/RBOTZILLA_PHOENIX/configs/* /home/rfing/RBOTZILLA_PHOENIX/backups/") | crontab -
```

### Manual Backup
```bash
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  configs/ logs/narration.jsonl ops/ .vscode/
```

### Recovery
```bash
# Restore from backup
tar -xzf backup_20260303_000000.tar.gz -C /home/rfing/RBOTZILLA_PHOENIX/
```

---

## 14. System Resource Requirements

| Component | Min | Recommended |
|-----------|-----|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 512MB | 2GB+ |
| Disk | 1GB | 5GB+ |
| Network | 1 Mbps | 10+ Mbps |
| Uptime | 95% | 99%+ |

---

## 15. Support Resources

| Resource | Location | Purpose |
|----------|----------|---------|
| Logs | `/tmp/rbz.log` | Real-time engine logs |
| Events | `logs/narration.jsonl` | All trade events |
| Diagnostics | `python run_diagnostics.py` | System health |
| Audit | `bash system_audit.sh` | Security check |
| Compliance | `audit_reports/` | Trade audit logs |

---

**Last Updated:** March 3, 2026
