# ENGINE_COMPONENT_MAP.md — Phase 1
# RBOTZILLA_OANDA_CLEAN

Generated: 2026-03-17
Ranking: A=best verified | B=good, unverified | C=needs rewrite | D=discard

---

## A. Best Market Data Code

**Source:** `brokers/oanda_connector.py` — `get_historical_data()`
**Method:** `GET /v3/instruments/{instrument}/candles`
**Label:** RUNTIME_VERIFIED
**Rating:** A
**Carry:** YES — extract as-is, minimal cleanup
**Notes:** Returns list of M15 OHLCV dicts. Used in every scan cycle. Confirmed working.

---

## B. Best OANDA Connector Code

**Source:** `brokers/oanda_connector.py` (Phoenix)
**Label:** RUNTIME_VERIFIED
**Rating:** A
**Key methods confirmed working:**
- `_make_request()` — all API calls route through here. Returns `{success, data}` dict.
- `get_account_info()` → returns `OandaAccount` dataclass (balance, margin_used, margin_available, unrealized_pl)
- `get_trades()` → list of trade dicts with instrument, id, currentUnits, unrealizedPL, stopLossOrder, takeProfitOrder
- `get_historical_data()` → M15 candles
- `_make_request("GET", "/v3/accounts/{id}/pricing")` → returns prices[0] with `tradeable`, `time`, `bids`, `asks`
- `set_trade_stop()` → PATCHED this session to check response
- `place_oco_order()` → places SL+TP at entry
**Carry:** YES — this is the foundation. Copy directly.

**Comparison — rick_clean_live connector:**
**Label:** UNVERIFIED
Not tested. May predate the practice-endpoint enforcement. Do not use as primary.

---

## C. Best Order Placement Code

**Source:** `oanda_trading_engine.py` → `place_trade()` (line 1349)
**Label:** CODE_VERIFIED (runtime placing confirmed, internal logic unverified)
**Rating:** B
**Notes:**
- Calls `place_oco_order()` from connector
- Applies Charter compliance pre-checks
- OCO places SL+TP atomically
- Entry price from live bid/ask at placement time (line 1450)
**Carry:** Extract `place_trade()` logic — do not carry the entire 4250-line engine file

---

## D. Best OCO Enforcement Code

**Source:** `risk/oco_validator.py` (Phoenix) + `brokers/oanda_connector.py::place_oco_order()`
**Label:** UNVERIFIED (oco_validator), RUNTIME_VERIFIED (place_oco_order)
**Rating:** B
**Notes:**
- `place_oco_order()` at connector level enforces SL+TP at placement
- `oco_validator.py` adds payload validation before the call
- Charter enforces min 1:3 R:R
**Carry:** Both files. Validate oco_validator before use.

---

## E. Best Active-Position Sync Code

**Source:** `oanda_trading_engine.py` → `_sync_open_positions()` (line ~2420)
**Label:** CODE_VERIFIED
**Rating:** B
**Notes:**
- Pulls open trades from OANDA and reconciles against `active_positions` dict
- Removes stale local positions whose trade IDs are gone from broker
**Carry:** Extract method. The reconcile VS Code task also exists for manual sync.

---

## F. Best Trade Manager Code

**Source:** `oanda_trading_engine.py` → `trade_manager_loop()` 
**Label:** CODE_VERIFIED (trail SL patch applied this session)
**Rating:** B
**Notes:**
- Monitors open positions, applies trailing SL when 2R reached
- PATCHED: now checks `set_trade_stop()` response before logging success
- UNVERIFIED at runtime (no TRAIL_SL_REJECTED seen yet — no trade reached trail point this session)
**Carry:** Extract as standalone class in clean repo.

---

## G. Best Narration/Logging Code

**Source:** `oanda_trading_engine.py` → `log_narration()` call pattern + `narration.jsonl`
**Label:** RUNTIME_VERIFIED (event format confirmed)
**Rating:** A
**JSONL schema (runtime confirmed):**
```json
{
  "timestamp": "ISO8601+UTC",
  "event_type": "CANDIDATE_FOUND|ORDER_SUBMIT_ALLOWED|SPREAD_TOO_WIDE_BLOCK|...",
  "symbol": "EUR_USD",
  "venue": "signal_scan|tradability_gate|oanda|trading_loop",
  "details": {}
}
```
**Carry:** YES. Extract `log_narration()` as standalone util. Keep event_type naming convention.

---

## H. Best Startup Verification Code

**Source:** `startup_sequence.py` (Phoenix, patched this session)
**Label:** RUNTIME_VERIFIED
**Rating:** A
**Output confirmed:** Environment, Endpoint, Account ID, Broker Open Trades, Synced Symbols, OCO Enforcement
**Carry:** YES. Use as template for clean repo startup block.

---

## I. Best Spread/Session/Market-Open Gating Code

**Source:** `oanda_trading_engine.py` → `_check_broker_tradability()` (new method, this session)
**Label:** RUNTIME_VERIFIED
**Rating:** A
**Checks:**
1. Live quote fetch via `/pricing` endpoint
2. `tradeable` boolean field
3. Quote timestamp freshness (default 120s)
4. Spread > MAX_SPREAD_PIPS (default 8.0, env-overridable)
**Carry:** YES. This is the cleanest gate added this session. Copy directly.

**Session labels:** `session_bias()` in `systems/multi_signal_engine.py`
**Rating:** C — metadata only, not a market-open gate. Must be clearly labeled in clean repo.

---

## J. Best Strategy Modules for High-Quality Trades

**Best performing today (runtime evidence):**
1. `ema_stack + fibonacci + ema_scalper_200` — fired on EUR_USD, GBP_USD, GBP_CAD, EUR_CAD at 73-80% confidence
2. `fvg + fibonacci + ema_scalper_200` — fired on AUD_USD, AUD_CAD at 74-78% confidence (4 votes on AUD_USD)
3. `liq_sweep + trap_reversal + rsi_extreme` — fired on GBP_NZD at 74% confidence (BLOCKED by spread — signal quality is real, pair is wrong)

**Strategy rating for clean repo:**
- ema_stack, fibonacci, ema_scalper_200, fvg: **KEEP** — they produce consistent 3-4 vote signals at 73-80% confidence
- liq_sweep, trap_reversal, rsi_extreme: **KEEP** — real signal, apply to better spreads-pairs only
