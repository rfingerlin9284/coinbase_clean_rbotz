#!/usr/bin/env bash
# QUICK REFERENCE CARD - Capital Preservation System Commands

echo "
╔════════════════════════════════════════════════════════════════════════╗
║                    RBOTZILLA - QUICK REFERENCE CARD                   ║
╚════════════════════════════════════════════════════════════════════════╝

📊 MONITORING COMMANDS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  status          Full portfolio report + capital efficiency
  summary         Quick summary of open positions
  positions       List all open positions with P&L
  manual          List manual (LLM-created) positions only

🔐 CAPITAL PRESERVATION COMMANDS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  oco_status      Check all OCO (SL/TP) orders
  oco_verify      Verify and fix broken OCO orders
  red_positions   Show all floating red positions
  prune_analysis  Analyze what will be pruned
  prune_execute   Close stagnant/losing positions
  efficiency      Capital efficiency score (0-100+)

🎮 TRADING COMMANDS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  buy SYMBOL PRICE SL TP SIZE
    Example: buy EUR_USD 1.0950 1.0940 1.0975 1.0
    → Buy 1.0 lot EUR/USD at 1.0950, SL 1.0940, TP 1.0975
    → OCO created, red alert monitoring ON, efficiency tracked

  sell SYMBOL PRICE SL TP SIZE
    Example: sell GBP_USD 1.2500 1.2530 1.2450 0.5
    → Sell 0.5 lot GBP/USD (SHORT), SL 1.2530, TP 1.2450

  close POSITION_ID
    → Close specific position immediately

  auto POSITION_ID
    → Enable auto-management for manual position

⚙️  CONFIGURATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  config          Current operating configuration
  info            System information
  sync            Manually trigger cross-repo sync
  sync_status     Check repo synchronization status

⏹️  CONTROL:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  stop            Stop trading operations safely
  exit            Exit program (stops system)

╔════════════════════════════════════════════════════════════════════════╗
║                             SYSTEM BEHAVIOR                            ║
╚════════════════════════════════════════════════════════════════════════╝

EVERY 5 SECONDS:
  ✓ Check all positions for RED ALERT (-0.2% loss)
  ✓ Close positions that hit SL or TP
  ✓ Monitor floating losses in real-time

EVERY 30 SECONDS:
  ✓ Verify all OCO orders exist and working
  ✓ Recreate broken orders automatically
  ✓ Ensure NO orphaned positions

EVERY 60 SECONDS:
  ✓ Identify stagnant positions (10+ min, <0.3% move)
  ✓ Identify poor performers (low momentum)
  ✓ Close HIGH severity pruning candidates

EVERY 120 SECONDS:
  ✓ Identify winners (>$50 profit)
  ✓ Identify losers (<-$100 loss)
  ✓ Scale winners +20%, close losers

EVERY 300 SECONDS:
  ✓ Print full portfolio status
  ✓ Update capital efficiency score
  ✓ Report statistics

╔════════════════════════════════════════════════════════════════════════╗
║                           KEY THRESHOLDS                               ║
╚════════════════════════════════════════════════════════════════════════╝

RED ALERT CLOSE:          -0.2% loss
STAGNANT DETECTION:       10+ minutes open, <0.3% move
POOR MOMENTUM:            <0.4 confidence score
BAD RISK/REWARD:          >0.7x ratio (more risk than reward)
MIN PROFIT FOR SCALE:     >$50 profit
MAX LOSS FOR CLOSE:       <-$100 loss
MARGIN PER SYMBOL:        5-10% (vs 1.5% default)
OCO VERIFICATION:         Every 30 seconds

╔════════════════════════════════════════════════════════════════════════╗
║                         TYPICAL SESSION                                ║
╚════════════════════════════════════════════════════════════════════════╝

1. START:
   python3 orchestrator_start.py

2. VIEW STATUS:
   > status
   (See portfolio + all systems running)

3. OPEN POSITION:
   > buy EUR_USD 1.0950 1.0940 1.0975 1.0
   (System creates OCO, starts monitoring)

4. MONITOR RUNNING:
   > efficiency
   (Check capital efficiency)

5. MANAGE OPEN:
   > red_positions
   (See any floating losses)

6. CLOSE IF NEEDED:
   > close abc123def456
   (Manual close, OCO also closes)

7. STOP WHEN DONE:
   > stop
   (Graceful shutdown)

╔════════════════════════════════════════════════════════════════════════╗
║                        EXAMPLE SCENARIOS                               ║
╚════════════════════════════════════════════════════════════════════════╝

Scenario 1: Winning Trade
─────────────────────────────────────────────────────────────────────────
1. Buy EUR_USD @ 1.0950 with SL 1.0940, TP 1.0975
2. Price moves to 1.0960 (+10 pips)
3. System tightens SL to 1.0945 (profit protection)
4. Price hits TP @ 1.0975
5. OCO closes position automatically
6. System reallocates capital to next winner
Result: +$250 profit captured ✅

Scenario 2: Losing Trade
─────────────────────────────────────────────────────────────────────────
1. Buy GBP_USD @ 1.2500 with SL 1.2480, TP 1.2550
2. Price drops to 1.2485 (-1.2%)
3. RED ALERT threshold hit (-0.2%)
4. System closes immediately @ 1.2485
5. Loss locked at -$50 (not -$500)
6. Capital reallocated to winners
Result: Fast loss, capital preserved ✅

Scenario 3: Stagnant Position
─────────────────────────────────────────────────────────────────────────
1. Open USD_JPY @ 105.50
2. 10 minutes pass, price barely moves
3. Pruning engine detects stagnant
4. Position size reduced by 50%
5. Capital freed and reallocated
Result: Zombie capital eliminated ✅

╔════════════════════════════════════════════════════════════════════════╗
║                        CAPITAL FLAGS                                   ║
╚════════════════════════════════════════════════════════════════════════╝

🟢 GREEN  → Position is profitable
🔴 RED    → Position is losing
⚠️  YELLOW → Position is stagnant or risky
🚨 ALERT  → Red alert triggered (closing NOW)
✅ LOCKED → OCO order verified and active
❌ BROKEN → OCO order missing (auto-recreating)
🔄 REALLOCATING → Capital moving from losers to winners

═══════════════════════════════════════════════════════════════════════════╝
"
