# RBOTZILLA AUDIT LEDGER

Last updated: 2026-03-17

---

## ENFORCED WORKSPACE RULES

1. I cannot see your terminal unless you paste output.
2. I cannot execute code in your terminal. I can only propose commands.
3. I cannot see the OANDA web UI.
4. Nothing is called VERIFIED unless your pasted terminal output proves it.
5. Labels used throughout this ledger:
   - `RUNTIME_VERIFIED` — you pasted proof
   - `CODE_VERIFIED` — confirmed in production file, not runtime-tested
   - `UNVERIFIED` — not yet proven by either method
   - `INFERRED` — logically concluded, not directly observed
6. If sandbox/tool limits prevent verification, it will be stated plainly.
7. One copy-paste terminal block only when terminal action is needed.
8. No scope creep. No silent file changes.

---

## WHAT IS PROVEN (RUNTIME_VERIFIED)

| Fix | Evidence |
|---|---|
| CANDIDATE_FOUND fires before broker gate | Narration output 2026-03-17T08:18:20-28 pasted |
| SPREAD_TOO_WIDE_BLOCK fires, not Placing | Same output: GBP_NZD 9.1–9.4 pips blocked |
| → Placing never prints for blocked pair | Confirmed absent from pasted output |
| OANDA pricing API field names confirmed | `/pricing` response pasted: `tradeable`, `time`, `bids[0].price` as string |
| Spread math correct for non-JPY | EUR_USD: (1.14856 - 1.14840) × 10000 = 1.6 pips |
| Startup broker state block fires | grep -A 8 SECTION 7 confirmed account ID 101-001-31210531-001, 1 open trade |
| Account is PRACTICE only | `PRACTICE endpoints` confirmed in all outputs |

---

## WHAT IS CODE_VERIFIED (not runtime re-proven after last changes)

| Fix | File | Lines |
|---|---|---|
| Trail SL now checks set_trade_stop response | `oanda_trading_engine.py` | ~3030-3065 |
| Margin gate uses live NAV + margin_used | `oanda_trading_engine.py` | ~1426-1473 |
| _check_broker_tradability method added | `oanda_trading_engine.py` | ~2313-2420 |
| Symbol dedup _placed_this_cycle fix | `oanda_trading_engine.py` | ~3976-4097 |
| asyncio.sleep(3) → scan_fast_seconds | `oanda_trading_engine.py` | 4151 |
| GBP_NZD removed from trading_pairs | `oanda_trading_engine.py` | 264 |
| startup_sequence.py Section 7 live broker query | `startup_sequence.py` | ~291-340 |
| tasks.json 9 plain-English tasks | `.vscode/tasks.json` | all |

---

## WHAT REMAINS UNVERIFIED

| Item | Why unverified |
|---|---|
| 60-second rescan timing after last restart | Need one scan cycle pasted after most recent restart |
| GBP_NZD absent from next scan log | Need narration.jsonl after latest restart |
| tradeable=false behavior (market closed) | No closed-market response observed yet |
| Duplicate trade fix (_placed_this_cycle) | Need a scan cycle with a qualifying signal to confirm |
| Trail SL response check runtime behavior | No TRAIL_SL_REJECTED narration observed yet |

---

## KNOWN BUGS FIXED THIS SESSION

| Bug | Impact | Fix Applied |
|---|---|---|
| 10 identical AUD_CAD trades in 76s | Lost ~$4k practice money | _placed_this_cycle dedup |
| asyncio.sleep(3) hardcoded scan bomb | Trades placed every 3s instead of 60s | Fixed to scan_fast_seconds |
| Ghost trailing SL (set_trade_stop response unchecked) | SL appeared set but wasn't | Response check added |
| Stale NAV ($1,970) in margin gate | False margin_cap_would_exceed blocks | Live NAV refresh per trade |
| →Placing printed before broker approval | No gate between candidate and order | CANDIDATE_FOUND/ALLOWED split |
| Startup showed no broker state | Operator had no visibility at start | 7-field live confirmation block |

---

## WHAT IS INFERRED (not directly observed)

- December performance gains were likely from tighter scan cadence and fewer duplicate trades, not a different confidence algorithm — INFERRED from code comparison
- GBP_NZD spread is structurally wide, not a transient condition — INFERRED from 10 consecutive readings 9.1–9.4 pips

---

## NEXT ACTION

Run verification block below, paste results, then proceed to RBOTZILLA_OANDA_CLEAN.
