#!/bin/bash
# ==============================================================================
# RBOTZILLA PHOENIX - MASTER REFRESH SCRIPT
# ==============================================================================
# Safely powers off the bot, updates everything, and powers it back on.
#
# RUNNING: ./refresh.sh
# ==============================================================================

set -e

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}                RBOTZILLA SYSTEM REFRESH                        ${NC}"
echo -e "${CYAN}================================================================${NC}"

# STEP 1: Power down
echo -e "\n[1/3] Powering down current systems..."
if [ -f "./turn_off.sh" ]; then
    ./turn_off.sh
else
    bash "./turn_off.sh" || true
fi

# STEP 2: Update environment
# (Optional: If you use git pull, uncomment the line below)
# git pull origin main

echo -e "\n[2/3] Checking for dependency updates..."
source venv/bin/activate
pip install -r requirements.txt --upgrade --quiet

# STEP 3: Power up
echo -e "\n[3/3] Powering systems back up..."
if [ -f "./turn_on.sh" ]; then
    ./turn_on.sh
else
    bash "./turn_on.sh"
fi

echo -e ""
echo -e "${GREEN}✅ REFRESH COMPLETE: The bot is back online and running the latest code!${NC}"
echo -e "${CYAN}================================================================${NC}"
