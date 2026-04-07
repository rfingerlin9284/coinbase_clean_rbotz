#!/bin/bash
#
# RBOTZILLA PHOENIX - Smart Startup Script
# Automatically runs comprehensive initialization sequence
# Shows all systems coming online with detailed confirmations
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Determine script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo -e "${CYAN}Run: ./setup.sh${NC}"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Get environment (default: practice)
ENV="${1:-practice}"

# Validate environment
if [ "$ENV" != "practice" ] && [ "$ENV" != "live" ]; then
    echo -e "${RED}❌ Invalid environment: $ENV${NC}"
    echo -e "${CYAN}Usage: ./start_trading.sh [practice|live]${NC}"
    exit 1
fi

# LIVE warning
if [ "$ENV" = "live" ]; then
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}⚠️  LIVE TRADING MODE INITIALIZATION ⚠️${NC}"
    echo -e "${YELLOW}   - OANDA: Locked to PRACTICE/PAPER tokens${NC}"
    echo -e "${YELLOW}   - COINBASE: Live Capital (if configured)${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    read -p "Type 'CONFIRM LIVE' to proceed: " CONFIRM
    if [ "$CONFIRM" != "CONFIRM LIVE" ]; then
        echo -e "${YELLOW}Live trading cancelled.${NC}"
        exit 0
    fi
fi

# Clear screen for clean startup
clear

# Start the engine with startup sequence
echo -e "${CYAN}Starting RBOTZILLA PHOENIX (OANDA Hybrid Paper Mode)...${NC}\n"
echo "Initializing comprehensive startup sequence..."
echo ""

# Run trading engine with startup sequence
if [ "$ENV" = "live" ]; then
    python -u oanda_trading_engine.py --env live --yes-live
else
    python -u oanda_trading_engine.py --env practice
fi
