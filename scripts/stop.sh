#!/usr/bin/env bash
# stop.sh — RBOTZILLA_OANDA_CLEAN
# Label: NEW_CLEAN_REWRITE
set -euo pipefail

pkill -f "RBOTZILLA_COINBASE_CLEAN.*trade_engine|trade_engine.py" >/dev/null 2>&1 && echo "OK: RBOTZILLA_COINBASE_CLEAN engine stopped" || echo "OK: engine was not running"
