#!/bin/bash
# ==============================================================================
# RBOTZILLA PHOENIX - MASTER TURN ON SCRIPT
# ==============================================================================
# Starts the autonomous trading bot AND opens the live monitoring dashboard.
#
# USAGE: ./turn_on.sh
# ==============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

SESSION_NAME="rbot_engine"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}           RBOTZILLA PHOENIX — STARTING UP                     ${NC}"
echo -e "${CYAN}================================================================${NC}"

# Check virtual environment
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Error: 'venv' folder not found. Please run ./setup.sh first.${NC}"
    exit 1
fi

# Check tmux is installed
if ! command -v tmux &> /dev/null; then
    echo -e "${RED}❌ Error: 'tmux' is not installed. Run: sudo apt install tmux${NC}"
    exit 1
fi

# Check if bot is already running
if pgrep -f "orchestrator_start.py" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  The bot is already running!${NC}"
    echo ""
    echo -e "${CYAN}Opening the live dashboard...${NC}"
    # Just attach to existing session if it exists; otherwise open a new terminal
    if tmux has-session -t $SESSION_NAME 2>/dev/null; then
        tmux attach -t $SESSION_NAME
    fi
    exit 0
fi

echo -e "${YELLOW}Step 1/3 — Starting the trading engine in the background...${NC}"

# ── WINDOW 0: Trading Engine (runs silently in background) ──────────────────
tmux new-session -d -s $SESSION_NAME -x 220 -y 50 \
    "source venv/bin/activate && python3 orchestrator_start.py --auto"

sleep 1

echo -e "${YELLOW}Step 2/3 — Starting the live monitoring dashboard...${NC}"

# ── WINDOW 1: Live Dashboard (opens in foreground pane) ─────────────────────
tmux new-window -t $SESSION_NAME -n "dashboard" \
    "source venv/bin/activate && python3 dashboard.py; read -p 'Dashboard closed. Press Enter to exit.'"

sleep 1

echo -e "${YELLOW}Step 3/3 — All systems up! Opening your dashboard now...${NC}"
echo ""
echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}  ✅  RBOTZILLA IS LIVE — Dashboard launching in 3 seconds...  ${NC}"
echo -e "${GREEN}================================================================${NC}"
echo ""
echo -e "  📺 ${YELLOW}The live dashboard will open automatically.${NC}"
echo -e "  🔴 ${YELLOW}To stop the bot:${NC}     ./turn_off.sh"
echo -e "  🔄 ${YELLOW}To restart/update:${NC}  ./refresh.sh"
echo ""

sleep 3

# Attach directly to the dashboard window so the user sees it immediately
tmux select-window -t $SESSION_NAME:dashboard
tmux attach -t $SESSION_NAME
