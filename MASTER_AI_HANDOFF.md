# RBOTZILLA MASTER AUDIT & HANDOFF REPORT

## 1. Problem Statement
The user reported that the trading engine is making valid directional calls, but progress is being destroyed by the mathematical configuration of the stop loss:
> *"these stop loss maxs are killing progress... find out why im not capturing profits like i am losses... what about the entire new workflow and stop loss logic?"*

---

## 2. Root Cause Analysis (The Math Failure)
The current exit geometry structurally forces a toxic Risk/Reward scenario. 

1. **Massive Position Sizing (`RBOT_BASE_UNITS=50000`)**
   - At 50k units on EUR/USD, 1 pip = ~$5.00.
2. **Suffocating Tight Stop Loss limit (`RBOT_MAX_LOSS_USD_PER_TRADE=75`)**
   - This hard cap dictates a strictly enforced **15-pip stop loss** ($5.00 x 15 = $75).
   - *The Reality:* A 15-pip stop loss is near-impossible to survive using the engine's current **Momentum Breakout** logic. Breakouts inherently buy the top/sell the bottom and rely on continuation, suffering deep pullbacks beforehand. 10-20 pip whip-saws are standard market noise.
3. **Mismatched Exit Geometry (Now Patched)**
   - Prior to this audit, the manager would sell 50% of the trade at +15 pips (1R) and then tighten the stop loss via a counter-trend wrapper, choking runners at +$10-$20. 
   - You were risking roughly 100% of the size for -$75, but only capturing 50% size for +$15. This structurally ruined the Edge. The scale-out and tight trails **have been stripped**, returning the engine to a Naked OCO.

---

## 3. The Target Blueprint: New Workflow Architecture
The user has recently ingested 13 advanced trading transcript files into the `.agents/workflows/` directory. The engine MUST be retrofitted to abandon its old generic momentum code and adopt this multi-layer structure.

### The 6-Layer Execution Pipeline (`workflow-router.md`)
1. **MTF Top-Down:** H4/Daily trend determines the strictly enforced directional bias.
2. **Session Killzones:** Trading occurs ONLY during A/B volume windows (e.g., NY/London overlap).
3. **Regime Detection:** 
   - Trending → Fire *Order Block Sniper* or *Liquidity Sweep Entry*.
   - Sideways → Fire *Range Bounce/Breakout* or *VWAP Mean Reversion*.
   - Triage → Disengage entirely.
4. **Compound Gate:** Require 4 out of 6 confidence boosters (+20% for unmitigated OBs, +15% for VWAP crosses, +25% for HTF alignment).
5. **Scalp Math Rules:** Ensure the strategy guarantees >70% win-rate to justify tight scalp sizing.
6. **Position Sizing Engine:** Dynamically scale `RBOT_BASE_UNITS` using Fractional Kelly based on the compound confidence score.

---

## 4. Target Entry Strategy: Strategy Rework
To survive the 15-pip stop loss, the bot CANNOT buy momentum expansions. It must be converted to the **Order Block Sniper** (`order-block-sniper.md`) logic:

- **H4/H1 Phase:** Detect the structural shift (BOS) and identify the "Origin Order Block" (institutional imbalance before the impulsive move).
- **Wait Phase:** Do NOTHING during the impulse. 
- **Sniper Entry (M15/M5):** Execute limit orders ONLY when price fully retraces into the unmitigated OB zone.
- **Why this works:** Buying a deep institutional retracement drops the structural risk to 5-10 pips, easily surviving the $75 limit while keeping the 30+ pip upside intact.

---

## 5. Target Exit/Stop-Loss Strategy (`scalp-math-rules.md`)
The new Scalp Math workflow dictates specific structural rules:
1. **Trader's Equation:** Scalping structurally forces a 1:2 R:R *against* the trader (risk 2, make 1). To counteract this, the entry edge (Order Blocks + Regime gating) MUST mathematically exceed an 80% win rate.
2. **Stop Types:** Bots must use strict Stop or Limit orders ONLY. No scaling-in (martingale) for bots.
3. **Jackrabbit Trap:** All signals must be evaluated strictly on CANDLE CLOSE to prevent fake-outs in the final seconds of M5 bars.

---

## 6. Structural Task List for the Next Agent AI
To fully align this repo with the requested workflows, the next AI must:

1. **Re-size or Re-stop:** Either halve `RBOT_BASE_UNITS` to `25000` (allowing a 30-pip stop loss under the $75 cap), OR implement the Order Block Sniper limit-entry logic to ensure entries only occur at extremes where a 15-pip stop is structurally valid.
2. **Implement MTF Filter:** Update `trade_engine.py` to fetch H4 candles and strictly block any signals that oppose the H4 bias.
3. **Migrate to Pullbacks:** De-weight "Momentum Breakout" pipelines and prioritize the algorithmic detection of Fair Value Gaps and Order Blocks for limit entries.

---

### System Environment State for Context
**`/home/rfing/RBOTZILLA_OANDA_CLEAN/.env` (Current Exit Config)**
```ini
RBOT_SL_PIPS=15
RBOT_TP_PIPS=30
RBOT_TS_PIPS=100              # Effectively disables trail to hit full TP
RBOT_TS_ATR_MULT=0
RBOT_CHOP_TARGET_RR=1.5
RBOT_MAX_LOSS_USD_PER_TRADE=75
RBOT_PROFIT_TARGET_PCT=100
RBOT_GREEN_LOCK_PIPS=3.0      # Scale-outs manually disabled in trade_manager.py
RBOT_MAX_NEW_TRADES_PER_CYCLE=2
RBOT_SCAN_FAST_SECONDS=15
RBOT_SCAN_SLOW_SECONDS=30     # Fixed from 300 to aggressively protect stops
```
