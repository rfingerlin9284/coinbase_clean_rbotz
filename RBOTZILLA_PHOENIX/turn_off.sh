#!/bin/bash
# ==============================================================================
# RBOTZILLA PHOENIX - MASTER TURN OFF SCRIPT
# ==============================================================================
# This tightly shuts down all ongoing trading processes and the background
# tmux session.
#
# RUNNING: ./turn_off.sh
# ==============================================================================

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SESSION_NAME="rbot_engine"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}                RBOTZILLA MASTER TURN OFF                       ${NC}"
echo -e "${CYAN}================================================================${NC}"

echo -e "${YELLOW}Initiating graceful shutdown sequence...${NC}"

# 1. Kill the orchestrator
if pgrep -f "orchestrator_start.py" > /dev/null 2>&1; then
    echo "Stopping orchestrator..."
    pkill -f "orchestrator_start.py"
    sleep 1
fi

# 2. Kill the oanda engine if it's running directly
if pgrep -f "oanda_trading_engine.py" > /dev/null 2>&1; then
    echo "Stopping OANDA trading engine..."
    pkill -f "oanda_trading_engine.py"
    sleep 1
fi

# 3. Kill the tmux session if it exists
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "Closing background terminal session..."
    tmux kill-session -t $SESSION_NAME
fi

# 4. Final verification
if pgrep -f "orchestrator_start.py" > /dev/null 2>&1 || pgrep -f "oanda_trading_engine.py" > /dev/null 2>&1; then
    echo -e "${RED}⚠️ Warning: Some processes took too long to stop or required a hard reset.${NC}"
    echo "Force killing remaining systems..."
    pkill -9 -f "orchestrator_start.py" 2>/dev/null || true
    pkill -9 -f "oanda_trading_engine.py" 2>/dev/null || true
fi

echo -e ""
echo -e "${GREEN}✅ SUCCESS: The bot has been safely turned OFF.${NC}"
echo -e "Remember: Your OCO safety nets on existing trades are still alive at the broker."
echo -e "${CYAN}================================================================${NC}"
