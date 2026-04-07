#!/bin/bash
#
# RBOTZILLA PHOENIX — ONE-SHOT NATIVE VALIDATION PACKAGE
# Run this from ~/RBOTZILLA_PHOENIX in your real terminal.
# PRACTICE ACCOUNT ONLY. NO LIVE FUNDS.
#
# Usage:
#   cd ~/RBOTZILLA_PHOENIX
#   chmod +x run_validation.sh
#   ./run_validation.sh
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

EVIDENCE_LOG="$SCRIPT_DIR/LIVE_RUNTIME_EVIDENCE.md"

echo ""
echo "================================================================="
echo -e "${CYAN}  RBOTZILLA PHOENIX — NATIVE VALIDATION SUITE${NC}"
echo -e "${YELLOW}  Practice Account Only | No Live Funds${NC}"
echo "================================================================="
echo ""

# Activate venv if present
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
else
    echo -e "${YELLOW}⚠️  No venv found, using system python3${NC}"
fi

# ── PHASE 1: Environment Confirmation ──
echo ""
echo "================================================================="
echo -e "${CYAN}  PHASE 1: ENVIRONMENT CONFIRMATION${NC}"
echo "================================================================="
echo ""

echo "Working directory: $(pwd)"
echo "Python binary: $(which python3)"
echo "Python version: $(python3 --version)"
echo ""

echo "Git status:"
git status --short 2>/dev/null || echo "(not a git repo)"
echo ""

echo "OANDA environment variables:"
env | grep -i oanda 2>/dev/null || echo "(none found — check .env)"
echo ""

# ── PHASE 2: Repo Check ──
echo "================================================================="
echo -e "${CYAN}  PHASE 2: CRITICAL CODE VERIFICATION${NC}"
echo "================================================================="
echo ""

echo "--- grep: _manage_trade in engine ---"
grep -n "def _manage_trade" oanda_trading_engine.py 2>/dev/null || echo "(not found — expected if using trade_manager_loop)"

echo ""
echo "--- grep: tight_step2 in trailing ---"
grep -n "tight_step2" rbz_tight_trailing.py

echo ""
echo "--- grep: def info in terminal_display ---"
grep -n "def info" util/terminal_display.py

echo ""
echo "--- grep: 127.0.0.1 in dashboards ---"
grep -n "127.0.0.1" dashboard/app_enhanced.py dashboard/websocket_server.py

echo ""
echo "--- grep: signal_type in engine ---"
grep -n "signal_type" oanda_trading_engine.py | head -5

echo ""

# ── PHASE 3: Trailing Stop Behavioral Proof ──
echo "================================================================="
echo -e "${CYAN}  PHASE 3: TRAILING STOP BEHAVIORAL PROOF${NC}"
echo "================================================================="
echo ""

TRAILING_EXIT=0
python3 verification_harness/validate_trailing.py || TRAILING_EXIT=$?

if [ $TRAILING_EXIT -eq 0 ]; then
    echo -e "\n${GREEN}✅ TRAILING TESTS: ALL PASSED${NC}"
    TRAILING_RESULT="PASS"
else
    echo -e "\n${RED}❌ TRAILING TESTS: $TRAILING_EXIT FAILURES${NC}"
    TRAILING_RESULT="FAIL"
fi

echo ""

# ── PHASE 4: Lifecycle Smoke Test ──
echo "================================================================="
echo -e "${CYAN}  PHASE 4: LIFECYCLE SMOKE TEST${NC}"
echo "================================================================="
echo ""

LIFECYCLE_EXIT=0
python3 verification_harness/validate_lifecycle_smoke.py || LIFECYCLE_EXIT=$?

if [ $LIFECYCLE_EXIT -eq 0 ]; then
    echo -e "\n${GREEN}✅ LIFECYCLE TESTS: ALL PASSED${NC}"
    LIFECYCLE_RESULT="PASS"
else
    echo -e "\n${RED}❌ LIFECYCLE TESTS: $LIFECYCLE_EXIT FAILURES${NC}"
    LIFECYCLE_RESULT="FAIL"
fi

echo ""

# ── PHASE 5: Native OANDA Practice Boot (30-second capture) ──
echo "================================================================="
echo -e "${CYAN}  PHASE 5: NATIVE OANDA PRACTICE BOOT (30s capture)${NC}"
echo "================================================================="
echo ""
echo -e "${YELLOW}Starting engine in PRACTICE mode for 30 seconds...${NC}"
echo -e "${YELLOW}This will connect to OANDA with fake money only.${NC}"
echo ""

BOOT_LOG="$SCRIPT_DIR/logs/native_boot_capture.log"
mkdir -p "$SCRIPT_DIR/logs"

# Run the engine for 30 seconds, capture stdout+stderr
timeout 30 python3 -u oanda_trading_engine.py --env practice > "$BOOT_LOG" 2>&1 || true

echo "--- Engine output (first 100 lines): ---"
head -100 "$BOOT_LOG"
echo ""
echo "--- Engine output (last 50 lines): ---"
tail -50 "$BOOT_LOG"
echo ""

# Check for critical markers in the boot log
SYNC_FOUND=$(grep -cEi "sync_open_positions|sync.*position|Syncing.*trade|Re-imported|Synced existing" "$BOOT_LOG" 2>/dev/null || true)
SYNC_FOUND=${SYNC_FOUND:-0}
MANAGER_FOUND=$(grep -cEi "trade_manager|TRADE MANAGER|management.*loop|Managing.*trade" "$BOOT_LOG" 2>/dev/null || true)
MANAGER_FOUND=${MANAGER_FOUND:-0}
CRASH_FOUND=$(grep -cE "TypeError|AttributeError|Traceback|CRITICAL" "$BOOT_LOG" 2>/dev/null || true)
CRASH_FOUND=${CRASH_FOUND:-0}
TRAILING_WIRE=$(grep -cEi "tight_sl|TightSL|trailing.*wire|_apply_tight" "$BOOT_LOG" 2>/dev/null || true)
TRAILING_WIRE=${TRAILING_WIRE:-0}

echo "--- Boot Evidence Summary ---"
echo "  Position sync markers: $SYNC_FOUND"
echo "  Trade manager markers: $MANAGER_FOUND"
echo "  Crash/error markers:   $CRASH_FOUND"
echo "  Trailing wire markers: $TRAILING_WIRE"
echo ""

if [ "$CRASH_FOUND" -eq 0 ]; then
    echo -e "${GREEN}✅ BOOT TEST: NO CRASHES DETECTED${NC}"
    BOOT_RESULT="PASS"
else
    echo -e "${RED}❌ BOOT TEST: $CRASH_FOUND CRASH MARKERS FOUND${NC}"
    BOOT_RESULT="FAIL"
fi

echo ""

# ── PHASE 6: Generate Evidence Report ──
echo "================================================================="
echo -e "${CYAN}  PHASE 6: GENERATING EVIDENCE REPORT${NC}"
echo "================================================================="
echo ""

cat > "$EVIDENCE_LOG" << EVIDENCE_EOF
# LIVE RUNTIME EVIDENCE

Generated: $(date -Iseconds)

## Environment
- Working directory: $(pwd)
- Python: $(which python3) ($(python3 --version 2>&1))
- Git status: $(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

## Phase 3: Trailing Stop Behavioral Proof
- Result: **$TRAILING_RESULT**

## Phase 4: Lifecycle Smoke Test
- Result: **$LIFECYCLE_RESULT**

## Phase 5: Native OANDA Practice Boot (30s)
- Result: **$BOOT_RESULT**
- Position sync markers found: $SYNC_FOUND
- Trade manager markers found: $MANAGER_FOUND
- Crash/error markers found: $CRASH_FOUND
- Trailing wire markers found: $TRAILING_WIRE
- Full boot log: logs/native_boot_capture.log

## Dashboard Binding
$(grep -n "host=" dashboard/app_enhanced.py dashboard/websocket_server.py 2>/dev/null)

## Signal Type Pass-through
$(grep -n "signal_type" oanda_trading_engine.py 2>/dev/null | head -5)
EVIDENCE_EOF

echo -e "${GREEN}✅ Evidence written to: $EVIDENCE_LOG${NC}"

# ── FINAL VERDICT ──
echo ""
echo "================================================================="
echo -e "${CYAN}  FINAL VERDICT${NC}"
echo "================================================================="
echo ""

ALL_PASS=true
[ "$TRAILING_RESULT" != "PASS" ] && ALL_PASS=false
[ "$LIFECYCLE_RESULT" != "PASS" ] && ALL_PASS=false
[ "$BOOT_RESULT" != "PASS" ] && ALL_PASS=false

echo "  Trailing logic:      $TRAILING_RESULT"
echo "  Lifecycle tests:     $LIFECYCLE_RESULT"
echo "  Native boot:         $BOOT_RESULT"
echo ""

if [ "$ALL_PASS" = true ]; then
    echo -e "${GREEN}██████████████████████████████████████████████████████████████${NC}"
    echo -e "${GREEN}  ✅ ALL VALIDATION PHASES PASSED — SYSTEM IS GO FOR DEMO    ${NC}"
    echo -e "${GREEN}██████████████████████████████████████████████████████████████${NC}"
else
    echo -e "${RED}██████████████████████████████████████████████████████████████${NC}"
    echo -e "${RED}  ❌ VALIDATION FAILED — REVIEW ABOVE OUTPUT AND FIX          ${NC}"
    echo -e "${RED}██████████████████████████████████████████████████████████████${NC}"
fi

echo ""
echo "Full boot log: logs/native_boot_capture.log"
echo "Evidence report: LIVE_RUNTIME_EVIDENCE.md"
echo ""
echo "Done. Paste this terminal output back to Anti-Gravity for final decision."
