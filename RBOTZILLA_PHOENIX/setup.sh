#!/bin/bash

# RBOTZILLA PHOENIX Automated Setup Script
# Purpose: Complete system initialization from GitHub clone
# Usage: bash setup.sh

set -e  # Exit on error

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🤖 RBOTZILLA PHOENIX - Automated Setup${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo ""

# 1. Check Python version
echo -e "${YELLOW}[1/8] Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"
if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    echo -e "${GREEN}✓ Python version OK${NC}"
else
    echo -e "${RED}✗ Python 3.8+ required${NC}"
    exit 1
fi
echo ""

# 2. Create virtual environment
echo -e "${YELLOW}[2/8] Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi
source venv/bin/activate
echo ""

# 3. Upgrade pip
echo -e "${YELLOW}[3/8] Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo -e "${GREEN}✓ Pip upgraded${NC}"
echo ""

# 4. Install dependencies
echo -e "${YELLOW}[4/8] Installing dependencies from requirements.txt...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}✗ requirements.txt not found${NC}"
    exit 1
fi
echo ""

# 5. Create log directories
echo -e "${YELLOW}[5/8] Creating log directories...${NC}"
mkdir -p logs audit_logs audit_reports backups backtest/results
chmod 755 logs audit_logs audit_reports backups
echo -e "${GREEN}✓ Log directories created${NC}"
echo ""

# 6. Initialize runtime mode config
echo -e "${YELLOW}[6/8] Initializing configuration files...${NC}"
if [ ! -f "configs/runtime_mode.json" ]; then
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
    echo -e "${GREEN}✓ Runtime mode initialized (default: PAPER)${NC}"
else
    echo "Runtime mode config already exists, skipping..."
fi
echo ""

# 7. Create secrets template
echo -e "${YELLOW}[7/8] Creating secrets template...${NC}"
if [ ! -f "ops/secrets.env" ]; then
    if [ ! -f "ops/secrets.env.template" ]; then
        cat > ops/secrets.env << 'EOF'
# OANDA Practice Account (for testing)
OANDA_PRACTICE_ACCOUNT_ID=your_practice_account_id
OANDA_PRACTICE_TOKEN=your_practice_token

# OANDA Live Account (requires PIN to activate)
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
        chmod 600 ops/secrets.env
        echo -e "${YELLOW}⚠️  Created ops/secrets.env - EDIT WITH YOUR CREDENTIALS${NC}"
    else
        cp ops/secrets.env.template ops/secrets.env
        chmod 600 ops/secrets.env
        echo -e "${YELLOW}⚠️  Created ops/secrets.env from template${NC}"
    fi
else
    echo "Secrets file already exists, skipping..."
fi
echo ""

# 8. Fix script permissions
echo -e "${YELLOW}[8/8] Setting up script permissions...${NC}"
find . -name "*.sh" -type f -exec chmod +x {} \;
echo -e "${GREEN}✓ Scripts are executable${NC}"
echo ""

# Verification
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit ops/secrets.env with your OANDA credentials"
echo "     nano ops/secrets.env"
echo ""
echo "  2. Verify system readiness (2 seconds)"
echo "     python verify_system_ready.py"
echo ""
echo "  3. Start the bot (via VS Code or command line)"
echo "     python -u oanda_trading_engine.py"
echo ""
echo "  4. Monitor performance"
echo "     Ctrl+Shift+P → Run Task → 📈 Performance Analysis"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo "  - DO NOT commit ops/secrets.env to git (contains credentials)"
echo "  - Use .gitignore to protect secrets"
echo "  - Keep ops/secrets.env secure (chmod 600)"
echo ""
echo "Documentation:"
echo "  - README.md              - Quick start & features"
echo "  - DEPLOYMENT.md          - Detailed setup guide"
echo "  - ARCHITECTURE.md        - System design"
echo "  - WORKFLOWS.md           - Daily operations"
echo "  - MEGA_PROMPT.md         - AI agent capabilities"
echo ""
