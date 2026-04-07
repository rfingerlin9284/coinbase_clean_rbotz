# LIVE RUNTIME EVIDENCE

Generated: 2026-03-14T11:38:15-04:00

## Environment
- Working directory: /home/rfing/RBOTZILLA_PHOENIX
- Python: /home/rfing/RBOTZILLA_PHOENIX/venv/bin/python3 (Python 3.12.3)
- Git status: 621ce77

## Phase 3: Trailing Stop Behavioral Proof
- Result: **PASS**

## Phase 4: Lifecycle Smoke Test
- Result: **FAIL**

## Phase 5: Native OANDA Practice Boot (30s)
- Result: **PASS**
- Position sync markers found: 0
- Trade manager markers found: 2
- Crash/error markers found: 0
- Trailing wire markers found: 1
- Full boot log: logs/native_boot_capture.log

## Dashboard Binding
dashboard/app_enhanced.py:242:    socketio.run(app, host=os.getenv('RBZ_DASH_HOST', '127.0.0.1'), port=8080, debug=False, allow_unsafe_werkzeug=True)
dashboard/websocket_server.py:132:    socketio.run(app, host='127.0.0.1', port=5001, debug=False)

## Signal Type Pass-through
126:        # signal_type  = pos.get('signal_type', 'trend')
1305:                   signal_type: str = 'trend'):
1309:            # 🛡️ FIX #6: TP COOLDOWN — per symbol AND per signal_type
1312:            # Key format:  "SYMBOL:signal_type"  e.g. "GBP_USD:trend"
1313:            # Fallback (no signal_type known): "SYMBOL:any" — blocks all types.
