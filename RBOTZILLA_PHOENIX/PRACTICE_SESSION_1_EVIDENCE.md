# PRACTICE SESSION 1 EVIDENCE

- Collected: 2026-03-14T14:18:35-04:00
- Runtime log: /home/rfing/RBOTZILLA_PHOENIX/logs/native_boot_capture.log
- Narration log: /home/rfing/RBOTZILLA_PHOENIX/narration.jsonl

## Startup Proof
```text
     🤖 RBOTZILLA PHOENIX - SYSTEM INITIALIZATION
⏰ Startup initiated: 2026-03-14 11:37:46 UTC
[1m[92m🟢 RBOTZILLA PHOENIX - FULLY OPERATIONAL[0m
```

## Practice Mode Proof
```text
WARNING:brokers.oanda_connector:USER OVERRIDE: OANDA is strictly locked to PRACTICE endpoints to prevent real money loss.
[92m✅ ✅ PRACTICE API connected[0m
   Endpoint: https://api-fxpractice.oanda.com
[1m[96m                     🤖 RBOTzilla TRADING ENGINE (PRACTICE)                      [0m
[90m  • [0m[37mEnvironment:[0m [93mPRACTICE[0m
[90m  • [0m[37mAPI Endpoint:[0m [96mhttps://api-fxpractice.oanda.com[0m
[90m  • [0m[37mOrder Execution:[0m [93mOANDA PRACTICE API[0m
  🔴 [37mOANDA PRACTICE API  [0m [91mREADY[0m
[92m✅ ✅ RBOTzilla Engine Ready - PRACTICE Environment[0m
[92m✅ Starting trading engine with PRACTICE API...[0m
[96mℹ️ 📊 Market Data: PRACTICE OANDA API (real-time)[0m
[96mℹ️ 💰 Orders: PRACTICE OANDA API[0m
```

## Trade Placement Proof
```text
[96mℹ️ Placing Charter-compliant SELL OCO order for EUR_JPY...[0m
[44m[37m OPEN [0m [91m[1mEUR_JPY SELL[0m [36m@ 182.33600[0m 📉
[92m✅ 📍 Position opened: EUR_JPY SELL @ 182.33600[0m
[95m💬 Rick:[0m [3m[37m📌 TRADE_OPENED: Event logged[0m
[96mℹ️ Placing Charter-compliant BUY OCO order for EUR_NZD...[0m
[44m[37m OPEN [0m [92m[1mEUR_NZD BUY[0m [36m@ 1.97791[0m 📈
[92m✅ 📍 Position opened: EUR_NZD BUY @ 1.97791[0m
[95m💬 Rick:[0m [3m[37m📌 TRADE_OPENED: Event logged[0m
```

## OCO Proof
```text
✅ [92m[1mSYSTEM ON[0m → OCO (One-Cancels-Other) Order Validator
  ✅ OCO Order Manager (hardened exits)
  ✅ OCO Verification (30s interval)
   • OCO orders verified every 30 seconds (hardened exits)
[90m  • [0m[37mImmutable OCO:[0m [92mENFORCED (All orders)[0m
[90m  • [0m[37mTP/SL Enforcement:[0m [92mMANDATORY (OCO Required)[0m
[92m✅ ✅ TP/SL validated for EUR_JPY SELL: SL=182.47800, TP=181.79600[0m
[96mℹ️ Placing Charter-compliant SELL OCO order for EUR_JPY...[0m
[92m✅ ✅ OCO order placed! Order ID: 41039[0m
[92m✅ ✅ TP/SL validated for EUR_NZD BUY: SL=1.97512, TP=1.98453[0m
[96mℹ️ Placing Charter-compliant BUY OCO order for EUR_NZD...[0m
[92m✅ ✅ OCO order placed! Order ID: 41040[0m
```

## Trade Manager Proof
```text
🤖 [92mBACKGROUND BOT [1mACTIVE[0m → 🛡️  Risk Management Agent
[1m[96m▶ SECTION 6: ADVANCED RISK MANAGEMENT SYSTEMS[0m
WARNING:root:Selenium not available. Install with: pip install selenium webdriver-manager
WARNING:root:Selenium not available. Install with: pip install selenium webdriver-manager
  ✅ OCO Order Manager (hardened exits)
[1m[93m▶ TRADE MANAGEMENT[0m
[90m  • [0m[37mTrade Manager:[0m [93mWill activate on start[0m
[92m✅ ✅ TRADE MANAGER ACTIVATED AND CONNECTED[0m
```

## Sync Recovery Proof
NOT OBSERVED YET

## Trailing Management Proof
```text
   └─ [96mReal-time momentum scanning | Trailing SL adjusts with price action[0m
[92m✅ 🛡️  Legacy Trailing disabled (RBZ TightTrailing Active)[0m
[92m✅ 🛡️  RBZ TightTrailing Available (Cooldown: 10m)[0m
[92m✅ ✅ RBZ tight trailing + TP guard ACTIVE & WIRED[0m
[90m  • [0m[37mSmart Trailing:[0m [92mEnabled (Momentum-based)[0m
```

## Signal Type Proof
NOT OBSERVED YET

## Errors Found
NOT OBSERVED YET

## Narration Tail
```text
{"timestamp": "2026-03-14T17:59:05.177761+00:00", "event_type": "GATE_REJECTION", "symbol": "AUD_CHF", "venue": "oanda", "details": {"symbol": "AUD_CHF", "reason": "margin_cap_would_exceed: 110.4% after order", "action": "AUTO_CANCEL", "margin_used": 0.0}}
{"timestamp": "2026-03-14T17:59:05.178475+00:00", "event_type": "TP_COOLDOWN_BLOCK", "symbol": "CHF_JPY", "venue": "oanda", "details": {"symbol": "CHF_JPY", "signal_type": "trend", "cooldown_key": "CHF_JPY:any", "last_close_utc": "2026-03-14T17:55:46.919249+00:00", "elapsed_seconds": 198.3, "cooldown_minutes": 10, "remaining_seconds": 401}}
{"timestamp": "2026-03-14T17:59:05.596555+00:00", "event_type": "GATE_REJECTION", "symbol": "EUR_USD", "venue": "oanda", "details": {"symbol": "EUR_USD", "reason": "margin_cap_would_exceed: 97.7% after order", "action": "AUTO_CANCEL", "margin_used": 0.0}}
{"timestamp": "2026-03-14T18:00:10.353909+00:00", "event_type": "SIGNAL_SCAN_RESULTS", "symbol": "SYSTEM", "venue": "signal_scan", "details": {"pairs_scanned": 23, "candidates_passed": 5, "open_slots": 12, "placing": 5, "min_conf_gate": 0.68, "top_candidates": [{"symbol": "GBP_USD", "dir": "SELL", "conf": 0.7967, "votes": 3, "detectors": ["ema_stack", "fibonacci", "ema_scalper_200"], "session": "new_york", "rr": 3.46}, {"symbol": "CHF_JPY", "dir": "SELL", "conf": 0.7882, "votes": 4, "detectors": ["ema_stack", "fibonacci", "liq_sweep", "ema_scalper_200"], "session": "new_york", "rr": 4.0}, {"symbol": "AUD_JPY", "dir": "SELL", "conf": 0.7673, "votes": 3, "detectors": ["ema_stack", "fibonacci", "ema_scalper_200"], "session": "new_york", "rr": 3.85}, {"symbol": "NZD_CAD", "dir": "SELL", "conf": 0.7604, "votes": 3, "detectors": ["ema_stack", "fibonacci", "ema_scalper_200"], "session": "new_york", "rr": 3.29}, {"symbol": "EUR_JPY", "dir": "SELL", "conf": 0.7298, "votes": 3, "detectors": ["ema_stack", "fibonacci", "ema_scalper_200"], "session": "new_york", "rr": 3.32}], "top_rejected": [{"symbol": "EUR_USD", "reason": "hive_conflict", "conf": 0.7881, "dir": "SELL"}, {"symbol": "USD_JPY", "reason": "no_signal", "conf": null, "dir": null}, {"symbol": "USD_CHF", "reason": "hive_conflict", "conf": 0.786, "dir": "BUY"}, {"symbol": "AUD_USD", "reason": "no_signal", "conf": null, "dir": null}, {"symbol": "USD_CAD", "reason": "no_signal", "conf": null, "dir": null}, {"symbol": "NZD_USD", "reason": "no_signal", "conf": null, "dir": null}, {"symbol": "EUR_GBP", "reason": "no_signal", "conf": null, "dir": null}, {"symbol": "GBP_JPY", "reason": "no_signal", "conf": null, "dir": null}], "rejected_by_stage": {"hive_conflict": 9, "no_signal": 9}}}
{"timestamp": "2026-03-14T18:00:10.729973+00:00", "event_type": "GATE_REJECTION", "symbol": "GBP_USD", "venue": "oanda", "details": {"symbol": "GBP_USD", "reason": "margin_cap_would_exceed: 97.7% after order", "action": "AUTO_CANCEL", "margin_used": 0.0}}
{"timestamp": "2026-03-14T18:00:10.730679+00:00", "event_type": "TP_COOLDOWN_BLOCK", "symbol": "CHF_JPY", "venue": "oanda", "details": {"symbol": "CHF_JPY", "signal_type": "trend", "cooldown_key": "CHF_JPY:any", "last_close_utc": "2026-03-14T17:55:46.919249+00:00", "elapsed_seconds": 263.8, "cooldown_minutes": 10, "remaining_seconds": 336}}
{"timestamp": "2026-03-14T18:00:11.206493+00:00", "event_type": "UPSIZE_TO_MIN_NOTIONAL", "symbol": "AUD_JPY", "venue": "risk", "details": {"symbol": "AUD_JPY", "direction": "SELL", "units_before": 1800, "units_after": 20100, "notional_before": 1344.51, "notional_after": 15013.68, "min_required_usd": 15000, "entry_price": 111.485}}
{"timestamp": "2026-03-14T18:00:11.207652+00:00", "event_type": "TP_SL_VALIDATED", "symbol": "AUD_JPY", "venue": "oanda", "details": {"symbol": "AUD_JPY", "direction": "SELL", "stop_loss": 111.63, "take_profit": 110.945, "validation": "PASSED"}}
{"timestamp": "2026-03-14T18:00:11.207869+00:00", "event_type": "TRADE_SIGNAL", "symbol": "AUD_JPY", "venue": "oanda", "details": {"symbol": "AUD_JPY", "direction": "SELL", "entry": 111.485, "stop_loss": 111.63, "take_profit": 110.945, "units": -20100, "notional": 15013.68495, "rr_ratio": 3.724137931034628, "live_data": true}}
{"timestamp": "2026-03-14T18:00:11.375899+00:00", "event_type": "OCO_PLACED", "symbol": "AUD_JPY", "venue": "oanda", "details": {"order_id": "41081", "trade_id": "", "entry_price": 111.485, "stop_loss": 111.63, "take_profit": 110.945, "units": -20100, "latency_ms": 166.5823459625244, "environment": "PRACTICE", "live_api": true, "visible_in_oanda": true}}
{"timestamp": "2026-03-14T18:00:11.451019+00:00", "event_type": "TRADE_OPENED", "symbol": "AUD_JPY", "venue": "oanda", "details": {"symbol": "AUD_JPY", "direction": "SELL", "entry_price": 111.485, "stop_loss": 111.63, "take_profit": 110.945, "size": 20100, "notional": 15013.68495, "rr_ratio": 3.724137931034628, "order_id": "41081", "trade_id": "", "charter_compliant": true, "signal_confidence": 0.7673, "signal_votes": 3, "signal_detectors": ["ema_stack", "fibonacci", "ema_scalper_200"], "signal_timeframe": "M15", "signal_session": "new_york", "management_profile": "OCO SL/TP; 0.75R->BE; 1.5R->scale50%; 2R->trail; hard_stop_usd", "hard_stop_usd": 30.0}}
{"timestamp": "2026-03-14T18:00:11.982529+00:00", "event_type": "TP_SL_VALIDATED", "symbol": "NZD_CAD", "venue": "oanda", "details": {"symbol": "NZD_CAD", "direction": "SELL", "stop_loss": 0.79352, "take_profit": 0.78644, "validation": "PASSED"}}
{"timestamp": "2026-03-14T18:00:11.983628+00:00", "event_type": "TRADE_SIGNAL", "symbol": "NZD_CAD", "venue": "oanda", "details": {"symbol": "NZD_CAD", "direction": "SELL", "entry": 0.79184, "stop_loss": 0.79352, "take_profit": 0.78644, "units": -252600, "notional": 144013.52448, "rr_ratio": 3.2142857142856625, "live_data": true}}
{"timestamp": "2026-03-14T18:00:12.156628+00:00", "event_type": "OCO_PLACED", "symbol": "NZD_CAD", "venue": "oanda", "details": {"order_id": "41082", "trade_id": "", "entry_price": 0.79184, "stop_loss": 0.79352, "take_profit": 0.78644, "units": -252600, "latency_ms": 171.59080505371094, "environment": "PRACTICE", "live_api": true, "visible_in_oanda": true}}
{"timestamp": "2026-03-14T18:00:12.192320+00:00", "event_type": "TRADE_OPENED", "symbol": "NZD_CAD", "venue": "oanda", "details": {"symbol": "NZD_CAD", "direction": "SELL", "entry_price": 0.79184, "stop_loss": 0.79352, "take_profit": 0.78644, "size": 252600, "notional": 144013.52448, "rr_ratio": 3.2142857142856625, "order_id": "41082", "trade_id": "", "charter_compliant": true, "signal_confidence": 0.7604, "signal_votes": 3, "signal_detectors": ["ema_stack", "fibonacci", "ema_scalper_200"], "signal_timeframe": "M15", "signal_session": "new_york", "management_profile": "OCO SL/TP; 0.75R->BE; 1.5R->scale50%; 2R->trail; hard_stop_usd", "hard_stop_usd": 30.0}}
{"timestamp": "2026-03-14T18:00:12.757862+00:00", "event_type": "UPSIZE_TO_MIN_NOTIONAL", "symbol": "EUR_JPY", "venue": "risk", "details": {"symbol": "EUR_JPY", "direction": "SELL", "units_before": 1100, "units_after": 12300, "notional_before": 1343.82, "notional_after": 15026.31, "min_required_usd": 15000, "entry_price": 182.336}}
{"timestamp": "2026-03-14T18:00:12.758978+00:00", "event_type": "TP_SL_VALIDATED", "symbol": "EUR_JPY", "venue": "oanda", "details": {"symbol": "EUR_JPY", "direction": "SELL", "stop_loss": 182.478, "take_profit": 181.796, "validation": "PASSED"}}
{"timestamp": "2026-03-14T18:00:12.759139+00:00", "event_type": "TRADE_SIGNAL", "symbol": "EUR_JPY", "venue": "oanda", "details": {"symbol": "EUR_JPY", "direction": "SELL", "entry": 182.336, "stop_loss": 182.478, "take_profit": 181.796, "units": -12300, "notional": 15026.309760000002, "rr_ratio": 3.8028169014087045, "live_data": true}}
{"timestamp": "2026-03-14T18:00:12.906436+00:00", "event_type": "OCO_PLACED", "symbol": "EUR_JPY", "venue": "oanda", "details": {"order_id": "41083", "trade_id": "", "entry_price": 182.336, "stop_loss": 182.478, "take_profit": 181.796, "units": -12300, "latency_ms": 146.010160446167, "environment": "PRACTICE", "live_api": true, "visible_in_oanda": true}}
{"timestamp": "2026-03-14T18:00:12.950535+00:00", "event_type": "TRADE_OPENED", "symbol": "EUR_JPY", "venue": "oanda", "details": {"symbol": "EUR_JPY", "direction": "SELL", "entry_price": 182.336, "stop_loss": 182.478, "take_profit": 181.796, "size": 12300, "notional": 15026.309760000002, "rr_ratio": 3.8028169014087045, "order_id": "41083", "trade_id": "", "charter_compliant": true, "signal_confidence": 0.7298, "signal_votes": 3, "signal_detectors": ["ema_stack", "fibonacci", "ema_scalper_200"], "signal_timeframe": "M15", "signal_session": "new_york", "management_profile": "OCO SL/TP; 0.75R->BE; 1.5R->scale50%; 2R->trail; hard_stop_usd", "hard_stop_usd": 30.0}}
```

## SUMMARY

### OBSERVED
- startup
- practice mode
- trade placement
- OCO
- trade manager
- trailing evidence

### NOT OBSERVED
- _manage_trade runtime marker
- signal_type runtime marker

### NEEDS MORE RUNTIME
- cooldown expiry and re-entry
- full trade lifecycle close -> re-manage -> re-enter
