# NATIVE EVIDENCE LEDGER

Last updated: 2026-03-14 (Practice Session 1)

## VERIFIED BY NATIVE OUTPUT
- Engine startup & Practice Mode confirmed (`api-fxpractice.oanda.com`)
- Trade placement & upsizing successful (`EUR_JPY units 1,100 → 12,300 to meet $15,000`)
- OCO placement successful & latency tracked (`Order ID: 41083 | Latency: 146ms`)
- Guardian Gate Blocks functioning (`margin_cap_would_exceed`, `hive_conflict`)
- Trade manager activation confirmed (`TRADE MANAGER ACTIVATED AND CONNECTED`)
- TP Cooldown logic functioning (`TP_COOLDOWN_BLOCK: 270s remaining`)
- Signal type routing passed to JSONL (`"signal_type": "trend"`)
- Narration JSONL successfully writing telemetry

## STATIC CODE VERIFIED ONLY
- Dashboard localhost default (code grep + runtime expectation)

## NOT VERIFIED YET
- `_manage_trade` runtime hit on real trade (requires open market price action)
- `_apply_tight_sl` runtime hit on real trade (requires open market price action)
- Sync/recovery of orphaned open positions
- Full autonomous practice cycle end-to-end (close -> re-manage -> re-enter)
