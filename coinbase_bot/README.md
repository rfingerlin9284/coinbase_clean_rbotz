# RBOTZILLA: COINBASE 24/7 HARVESTER UPGRADE PLAN

This repository is currently transitioning from the legacy structure to the brand new **`Rbot_v_24.7_brain`** architecture that we just fully realized on the OANDA engine.

Because Crypto operates under completely different physics than Forex, we cannot simply "copy-paste" the code. If we do, the massive 50,000-unit lot sizes and pip-math will instantly fail against the Coinbase API (or blow up the margin). 

This README outlines the exact step-by-step master plan to rebuild the Coinbase engine using the new Dual-Regime logic.

---

## 🏗️ Phase 1: Overwrite and Core Severing
We will clone the massive structural wins from OANDA while safely disconnecting the Forex specifics.
1. **Clone the Brain:** We will manually copy `engine/trade_engine.py`, `engine/capital_router.py`, and `engine/strategy_pipelines.py` from the OANDA repo to this repo.
2. **Sever OANDA:** We will completely strip out `get_oanda_connector.py` and replace it with `brokers/coinbase_cdp_connector.py`.
3. **Re-Wire the Pipes:** We will update all import paths in the engine so they naturally speak directly to the Coinbase Advanced Trade API.

## 🧮 Phase 2: The Math Overhaul (Fractional Sizing vs Pips)
This is the most dangerous phase. Crypto sizing works completely differently than Forex.
1. **Pip Annihilation:** OANDA relies on `0.0001` pip math to calculate stop-losses. We must rewrite the stop-loss generator inside `trade_engine.py` to use **Basis Points (BPS)** or raw percentages (e.g., `-1.5%` vs `20 pips`).
2. **Fractional Sizing:** We will completely rewrite `CapitalRouter` so that instead of scaling blocks of `14,000` units, it scales in dollar-costs and converts to strict crypto fractional limits (e.g., `0.0125 BTC`).

## 🕰️ Phase 3: Volatility Regimes (Killing The Clock)
The OANDA system uses the Eastern Standard Time clock (3 AM London, 12 PM NY) to toggle between Chop Mode and Sniper Mode. Crypto never sleeps; there is no "London Open."
1. **VIX for Crypto:** Instead of checking the physical time `_now_et.hour`, we will rewrite `_update_regime_state()` to read the **Average True Range (ATR)** of Bitcoin.
2. **Dynamic Triggers:**
   - If BTC ATR is low/suppressed ➔ Engine dynamically shifts into **CHOP MODE** (small sizes, hedging active).
   - If BTC ATR violently spikes ➔ Engine dynamically shifts into **SNIPER MODE** (heavy capital deployed, hedging disabled).

## 🛡️ Phase 4: Porting the Quant Hedge Engine
Crypto hedging is notoriously difficult because almost all altcoins are perfectly positively correlated to Bitcoin. 
1. **Inverse Map:** We will rewrite the `util/quant_hedge_engine.py` map. Instead of hedging EUR/USD with USD/CAD, we must map Bitcoin exposure to either mathematically inverse tokens or stablecoin yields. 
2. **Fix the Minus Bug:** We will ensure the `abs(position_size)` fix we applied in OANDA is fully present here so short trades don't crash the hedge ratio.

---

### How to Begin
When you are ready to start this build, simply open a new conversation with Antigravity inside this workspace and paste:
> *"Initiate Phase 1 of the Coinbase 24/7 Harvester upgrade as per the README."*
