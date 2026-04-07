# RBOTZILLA PHOENIX - Backup Copies

## 📦 Contents

This folder contains **read-only backup copies** of the RBOTZILLA_PHOENIX automated trading bot system.

### Files Included

- **rbtz_pheonix_1.tar.gz** (5.6 MB) - Pure clone from GitHub repository #1
- **rbtz_pheonix_2.tar.gz** (5.6 MB) - Pure clone from GitHub repository #2

### 🔒 Read-Only Status

All files in this directory are **read-only** for data integrity protection.

## 🚀 Quick Start - Extract & Use

### On Linux/macOS:
```bash
tar -xzf rbtz_pheonix_1.tar.gz
cd rbtz_pheonix_1
./setup.sh
# Configure ops/secrets.env with OANDA credentials
python oanda_trading_engine.py
```

### On Windows (WSL):
```bash
# Extract in WSL
tar -xzf rbtz_pheonix_1.tar.gz
cd rbtz_pheonix_1
bash setup.sh
# Configure ops/secrets.env with OANDA credentials
python oanda_trading_engine.py
```

## 📋 What is RBOTZILLA PHOENIX?

**RBOTZILLA PHOENIX** is an autonomous multi-strategy forex trading bot with:
- 7+ technical indicator strategies (Bullish Wolf, Liquidity Sweep, Fib Confluence, etc.)
- Multi-broker support (OANDA, Coinbase, Interactive Brokers)
- Advanced risk management with charter compliance gates
- AI Hive Mind integration (optional LLM-based decision making)
- Swarm agent voting system (Technical, Risk, Audit agents)
- Paper + Live trading modes with PIN-protected live switching
- Comprehensive 33-task VS Code automation for monitoring
- Streamlit dashboard for real-time performance tracking

## 📚 Documentation

After extraction, refer to:
- **README.md** - System overview and quick start
- **DEPLOYMENT.md** - Complete setup from zero
- **ARCHITECTURE.md** - Deep technical design
- **WORKFLOWS.md** - Operational procedures
- **MEGA_PROMPT.md** - AI agent rebuild instructions

## ✅ System Requirements

- Python 3.8+
- OANDA or other broker account
- Linux/macOS/WSL (Windows Subsystem for Linux)
- 4GB RAM minimum, 8GB recommended
- Stable internet connection (24/7 connectivity for live trading)

## 🔐 Security Notes

- **Clone from GitHub**: These are pure clones without any credentials
- **Configure Credentials**: You MUST add `ops/secrets.env` with your broker API tokens
- **Never Commit Secrets**: The .gitignore protects against accidental credential leaks
- **PIN Protection**: Live mode requires a PIN code for security

## 📊 Version Information

- **Baseline**: GitHub master branch (commit d315a10)
- **Date Created**: March 3, 2026
- **Documentation Level**: Comprehensive (4000+ lines)
- **Status**: Production-ready

## 🆘 Support

### Quick Diagnostics:
```bash
cd rbtz_pheonix_1
source venv/bin/activate
python run_diagnostics.py
```

### Check System Health:
```bash
./verify_system_ready.py
```

### Verify Broker Connection:
```bash
python verify_live_safety.sh
```

## 🔄 Using Both Clones

- **Clone #1**: Development/Testing environment
- **Clone #2**: Backup/Production environment

Keep both synchronized with GitHub for consistency.

## 📝 Notes

- These are **clean baseline copies** from GitHub
- No runtime data, logs, or temporary files included
- Perfect for fresh deployments or disaster recovery
- All documentation included automatically on extraction

---

**Created**: March 3, 2026  
**System**: RBOTZILLA PHOENIX v3.3.2026  
**Repository**: https://github.com/rfingerlin9284/rbotzilla_pheonix
