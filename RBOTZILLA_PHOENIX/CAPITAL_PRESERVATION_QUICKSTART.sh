#!/usr/bin/env bash
# Quick-start guide for RBOTZILLA PHOENIX with Capital Preservation System

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║         🏢 RBOTZILLA PHOENIX - CAPITAL PRESERVATION & GROWTH SYSTEM           ║
║                      Professional Hedge Fund Trading                           ║
║                                                                                ║
║           Your capital ALWAYS works toward NET POSITIVE P&L 24/7              ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝

📊 WHAT THIS SYSTEM DOES:

  ✅ Tracks ALL positions (autonomous + manual LLM commands)
  ✅ Monitors every position EVERY 5 SECONDS for red alerts
  ✅ Closes losing positions IMMEDIATELY (-0.2% loss threshold)
  ✅ Weeds out stagnant positions automatically (60s interval)
  ✅ Verifies hardened OCO orders (SL/TP) every 30 seconds
  ✅ Reallocates capital FROM losers TO winners continuously
  ✅ Uses 5-10% margin per symbol (NOT 1.5%)
  ✅ Syncs positions across all cloned repositories
  ✅ Supports manual trading via LLM commands

═══════════════════════════════════════════════════════════════════════════════

🚀 QUICK START (5 minutes):

## Step 1: Initialize the system
python3 orchestrator_start.py

## Step 2: View available commands
Type 'help' in the interactive menu

## Step 3: Start autonomous trading
The system automatically:
  • Monitors positions every 5 seconds
  • Verifies OCO orders every 30 seconds
  • Prunes stagnant positions every 60 seconds
  • Reallocates capital every 120 seconds
  • Reports status every 5 minutes

═══════════════════════════════════════════════════════════════════════════════

🎮 INTERACTIVE MODE (use these commands):

📊 Portfolio Monitoring:
  status         → Full portfolio status with efficiency report
  summary        → Quick summary of open positions
  positions      → List all open positions
  manual         → List manual positions (LLM commands)

🤖 Trading:
  buy SYMBOL PRICE SL TP SIZE      → Open long position
    Example: buy EUR_USD 1.0950 1.0940 1.0975 1.0
  
  sell SYMBOL PRICE SL TP SIZE     → Open short position
  close POSITION_ID                → Close specific position
  auto POSITION_ID                 → Enable auto-management

🔐 Capital Preservation:
  oco_status     → Check all OCO orders (hardened SL/TP)
  oco_verify     → Verify and recreate broken OCOs
  red_positions  → Show positions floating in red
  prune_analysis → Analyze what gets pruned
  prune_execute  → Execute capital pruning
  efficiency     → Show capital efficiency score

═══════════════════════════════════════════════════════════════════════════════

💡 THE 5 SYSTEMS WORKING TOGETHER:

1. OCO ORDER MANAGER (30s verification):
   └─ Ensures SL/TP orders hardened at broker level
   └─ If order breaks → Auto-recreates
   └─ Result: NEVER an orphaned position

2. AGGRESSIVE PORTFOLIO MONITOR (5s checks):
   └─ Watches ALL positions constantly
   └─ RED ALERT: Lose >-0.2% → CLOSE IMMEDIATELY
   └─ Result: Fast loss management, prevents bleeding

3. CAPITAL PRUNING ENGINE (60s interval):
   └─ Identifies stagnant/poor performing positions
   └─ High severity → Auto-close (red losers)
   └─ Medium severity → Reduce size or flag
   └─ Result: Zombie capital eliminated

4. NET POSITIVE CAPITAL ENGINE (Orchestrator):
   └─ Runs all 4 systems in parallel
   └─ Reallocates capital from losers → winners
   └─ Calculates efficiency score (0-100+)
   └─ Reports every 5 minutes
   └─ Result: 100% capital ALWAYS moving toward profit

5. MARGIN MAXIMIZER (Real-time sizing):
   └─ Sizes positions at 5-10% per symbol (vs 1.5%)
   └─ Respects correlation/drawdown limits
   └─ Result: More capital deployment = more returns

═══════════════════════════════════════════════════════════════════════════════

🎯 REAL-TIME EXAMPLE:

[14:32:15] Portfolio Monitor Check:
  ✅ EUR_USD position +$125 profit → SL tightened to breakeven
  🔴 GBP_USD position -$50 loss → Approaching SL
  🚨 USD_JPY position -0.25% loss → RED ALERT → CLOSING NOW
     Prevented loss: $500 (market closed at -1.2%)

[14:32:45] OCO Verification:
  ✅ 47 OCO orders verified active
  🔴 1 broken OCO found → Recreating...
  ✅ OCO recreated successfully

[14:33:45] Capital Pruning:
  🔍 Scanning for stagnant positions...
  📈 EUR_USD: Open 15 min, +0.5% → HOLD
  ⏱️  AUD_USD: Open 18 min, <0.1% move → STAGNANT
  ✂️  Reducing AUD_USD by 50%, reallocating capital

[14:34:45] Capital Reallocation:
  💰 Identified 3 winning positions
  💰 Identified 2 losing positions
  📈 Scaling winners +20%
  📉 Closing losers
  🎯 Capital moved: $500 winners, $300 losers → winner+$500

[14:35:00] Status Report:
  💪 Capital Efficiency: 127/100 (STRONG)
  📊 Open Positions: 5 (4 green, 1 red)
  💰 Total P&L: +$325 (+2.6%)
  🎯 Notional: $12,500
  ✅ Capital Preserved: $18,750 (losses prevented this session)

═══════════════════════════════════════════════════════════════════════════════

📈 KEY METRICS TO WATCH:

Capital Efficiency Score (0-100+):
  0-50: Capital not working well (losses)
  50-100: Capital at breakeven/slow growth
  100-150: Capital growing steadily (good)
  150+: Capital growing strong (very good)

P&L Per Notional:
  This shows return per dollar deployed
  Example: 2% P&L / $12,500 notional = 2% efficiency

Red Positions Count:
  0 = Perfect (no losers)
  1-2 = Acceptable (will be pruned or hit SL)
  3+ = Too many, portfolio being pruned aggressively

═══════════════════════════════════════════════════════════════════════════════

🔧 ADVANCED: Running in Background

## Autonomous mode (no interactive menu):
python3 orchestrator_start.py --auto

## Manual trading only:
python3 orchestrator_start.py --manual

## Custom account balance:
python3 orchestrator_start.py --account 50000

## Custom repo path:
python3 orchestrator_start.py --repo /path/to/repo

═══════════════════════════════════════════════════════════════════════════════

📚 DOCUMENTATION:

Read these files to understand the system:
  CAPITAL_PRESERVATION_SYSTEM.md  ← Complete system guide
  util/oco_order_manager.py       ← OCO verification logic
  util/aggressive_portfolio_monitor.py  ← Red alert system
  util/capital_pruning_engine.py  ← Pruning algorithms
  util/net_positive_capital_engine.py   ← Main orchestrator
  util/portfolio_orchestrator.py  ← User-facing API

═══════════════════════════════════════════════════════════════════════════════

❓ FAQ:

Q: What happens if I manually set a position?
A: It registers in the universal registry as MANUAL_PROMPT source
   System still monitors it, returns red-alerts, but won't auto-prune

Q: Can OCO orders be broken?
A: They CAN break (network issue, broker issue), but OCO Manager
   verifies every 30 seconds and RECREATES broken ones automatically

Q: How often is capital reallocated?
A: Every 120 seconds (2 minutes). Winners scale +20%, losers scale -50%

Q: What's the red alert threshold?
A: -0.2% loss triggers IMMEDIATE closure (very aggressive)
   This is tunable in AggressivePortfolioMonitor class

Q: Do I need to do anything?
A: NO! System runs 100% autonomously. You can:
   • Monitor status anytime
   • Open/close positions manually via 'buy'/'sell' commands
   • Check capital efficiency with 'efficiency' command

═══════════════════════════════════════════════════════════════════════════════

✅ WHAT'S PROTECTED:

  ✅ No orphaned positions (OCO verified constantly)
  ✅ No floating losses >0.5% (red alert closes immediately)
  ✅ No stagnant capital (zombie positions pruned)
  ✅ No over-leverage (margin limits enforced)
  ✅ No broken exits (OCO recreated automatically)
  ✅ No idle capital (reallocated to winners)

═══════════════════════════════════════════════════════════════════════════════

🚀 START NOW:

  python3 orchestrator_start.py

═══════════════════════════════════════════════════════════════════════════════

Version: 2.0 - Capital Preservation System
Status: Production Ready
Mission: Keep 100% capital moving toward NET POSITIVE P&L 24/7

EOF
