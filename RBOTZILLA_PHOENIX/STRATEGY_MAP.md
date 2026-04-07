# STRATEGY_MAP.md — Phase 1
# RBOTZILLA_OANDA_CLEAN

Generated: 2026-03-17

Detectors firing in runtime (from narration.jsonl pasted evidence):
- ema_stack — fired in 100% of passing scans this session
- fibonacci — fired in 100% of passing scans this session
- ema_scalper_200 — fired in most passing scans
- fvg (Fair Value Gap) — fired in some scans
- liq_sweep (Liquidity Sweep) — fired on GBP_NZD
- trap_reversal — fired on GBP_NZD
- rsi_extreme — fired on GBP_NZD

---

## Strategy Detectors (from systems/multi_signal_engine.py)

All detectors live inside `scan_symbol()` in `systems/multi_signal_engine.py`.
They are not standalone files — they are internal scoring functions.

| Detector | Runtime evidence | Judgment | Carry to clean repo? |
|---|---|---|---|
| ema_stack | Fires constantly, 3-4 votes | KEEP — core signal | YES |
| fibonacci | Fires constantly, always present | KEEP — core signal | YES |
| ema_scalper_200 | Fires frequently | KEEP | YES |
| fvg (Fair Value Gap) | Fires on AUD pairs | KEEP | YES |
| liq_sweep | Fires on GBP exotics | KEEP — but pair quality matters | YES |
| trap_reversal | Fires with liq_sweep | KEEP | YES |
| rsi_extreme | Fires with liq_sweep | KEEP | YES |

---

## Strategy Files (strategies/ folder)

These are file-based strategy classes loaded via registry.py.
NOT confirmed as detectors in multi_signal_engine — may be separate execution strategies.

| File | Judgment | Notes |
|---|---|---|
| `strategies/liquidity_sweep.py` | KEEP | Maps to liq_sweep detector |
| `strategies/trap_reversal_scalper.py` | KEEP | Maps to trap_reversal detector |
| `strategies/fib_confluence_breakout.py` | KEEP | Maps to fibonacci detector |
| `strategies/institutional_sd.py` | MAYBE KEEP | Supply/demand — inspect before porting |
| `strategies/price_action_holy_grail.py` | MAYBE KEEP | Inspect quality before porting |
| `strategies/bullish_wolf.py` | MAYBE KEEP | Wolf pattern — worked historically |
| `strategies/bearish_wolf.py` | MAYBE KEEP | Wolf pattern — worked historically |
| `strategies/sideways_wolf.py` | DISCARD | Ranging market signal — too noisy |
| `strategies/crypto_breakout.py` | DISCARD | Crypto-specific |
| `strategies/base.py` | KEEP | Required base class |
| `strategies/registry.py` | KEEP | Loader needed |

---

## Hive Mind (rick_hive_mind.py)

- In the live scan (08:47:29), Hive rejected EUR_USD (77%), GBP_USD (76%), AUD_USD (76%) via `hive_conflict`
- This is a significant filter — blocks high-confidence signals when Hive disagrees
- The Hive calls `delegate_analysis()` which returns a `consensus_signal`
- UNVERIFIED what the Hive consensus is based on (likely LLM or internal rules)
- Judgment: MAYBE KEEP — needs inspection. If it's LLM-dependent, it is unreliable for production.

---

## Session Bias (multi_signal_engine.py lines 106-151)

- Pure UTC clock math. No broker check.
- Multiplier: 1.0 for prime session, 0.90 off-session
- "london", "new_york", "tokyo", "overlap" are just UTC hour ranges
- Judgment: KEEP but label clearly as metadata-only. Do NOT use as market-open gate.

---

## Signal Confidence Thresholds

| Parameter | Current value | Source |
|---|---|---|
| min_signal_confidence | 0.68 (env) / 0.70 (hardcoded) | RUNTIME_VERIFIED — narration shows 0.68 gate |
| min_votes | 3 | CODE_VERIFIED (line 3697 Phoenix) |
| max_positions | 12 (env) | RUNTIME_VERIFIED — open_slots: 10/12 observed |
| max_new_trades_per_cycle | 6 | CODE_VERIFIED |
| scan_fast_seconds | 60 | RUNTIME_VERIFIED — 66-71s gaps observed |
| scan_slow_seconds | 300 | CODE_VERIFIED |
