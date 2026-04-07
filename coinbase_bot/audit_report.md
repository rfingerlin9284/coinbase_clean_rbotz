# RBOTZILLA AUDIT & HANDOFF REPORT

## Problem Statement
The user reported that the trading engine is successfully identifying algorithmic entries (Momentum pipelines), but progress is being destroyed by the stop loss mechanism:
> *"these stop loss maxs are killing progress... find out why im not capturing profits likte i am losses and again how did this happen"*

## Root Cause Analysis
The mathematical structure of the current exit geometry is actively choking the trading edge. The bot is being chopped up by standard market noise before the trades can mature.

1. **Massive Position Sizing (`RBOT_BASE_UNITS=50000`)**
   - At 50,000 units on pairs like EUR/USD, each pip of movement is worth ~$5.00.
2. **Suffocating Tight Stop Loss limit (`RBOT_MAX_LOSS_USD_PER_TRADE=75`)**
   - Because of the $75 hard loss cap, the bot mathematically cannot survive more than a **15-pip drawdown** ($5.00 x 15 = $75).
   - *The Reality:* A 15-pip stop loss in modern FX markets is near-impossible to trade with standard momentum breakouts. The average daily range of EUR/USD is 60+ pips. USD/JPY routinely moves 150+ pips. 
   - *The Result:* Every time the bot enters a valid setup, normal 10-20 pip market "breathing" or retracements instantly clip the trade out at a loss before the actual move occurs.
3. **Mismatched Execution Strategy**
   - The bot currently plays **Momentum Breakouts**. By definition, buying a breakout occurs at high/extended prices, which makes the position vulnerable to a short-term pullback (mean reversion). 
   - A 15-pip stop *requires* sniper precision (Liquidity Sweeps, Order Blocks, and pullback entries), but the engine is firing on fast momentum expansions.

## Summary of Active Interventions Already Applied Today
1. **Disabled `_try_scale_out_1r`**: The engine previously sold 50% of the position upon reaching 15 pips of profit. This was disastrous for the Risk/Reward math. It has been stripped.
2. **Disabled `apply_tight_sl` (Counter-Trend Trail)**: The engine previously clamped a fast trailing stop on runners, choking out winning trades at $10-$20. It has been stripped.
3. **Results:** The bot is now a pure "Naked OCO". It holds full size to either the stop loss or the take profit. 

## Structural Recommendations for the Next AI
To restore consistent profitability and give the edge room to work, the next Agent MUST redesign the sizing/geometry:

> [!CAUTION]
> **Do not attempt to 'fix' this by just tightening the stop loss further.** 

**Option A: Halve the Size, Double the Stop**
- Change `RBOT_BASE_UNITS` from `50000` to `25000`.
- This reduces cost-per-pip to ~$2.50.
- Change `RBOT_SL_PIPS` from `15` to `30`.
- Change `RBOT_TP_PIPS` from `30` to `60`.
- *Why:* Keeps max real-dollar risk at roughly $75, but gives the trade double the physical room on the chart to survive whipsaws and noise.

**Option B: Reprogram the Entry Edge to "Sniper/Pullbacks"**
- The new TurboScribe transcripts contain detailed workflows (`/liquidity-sweep-entry.md` and `/order-block-sniper.md`). 
- If keeping the 15-pip stop loss, the bot *must* stop buying momentum breakouts and only buy on deep retracements into Order Blocks / Fair Value Gaps where risk is structurally smaller than 15 pips.

---

### System Environment State for Context
**`/home/rfing/RBOTZILLA_OANDA_CLEAN/.env` (Current Exit Config)**
```ini
RBOT_SL_PIPS=15
RBOT_TP_PIPS=30
RBOT_TS_PIPS=100
RBOT_TS_ATR_MULT=0
RBOT_CHOP_TARGET_RR=1.5
RBOT_MAX_LOSS_USD_PER_TRADE=75
RBOT_PROFIT_TARGET_PCT=100
RBOT_GREEN_LOCK_PIPS=3.0
RBOT_GREEN_LOCK_MIN_PROFIT_PIPS=999.0
RBOT_STAGNATION_CYCLES=20
RBOT_MAX_NEW_TRADES_PER_CYCLE=2
RBOT_SCAN_FAST_SECONDS=15
RBOT_SCAN_SLOW_SECONDS=30
```
