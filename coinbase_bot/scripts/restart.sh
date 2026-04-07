#!/usr/bin/env bash
# restart.sh — RBOTZILLA_COINBASE_CLEAN
# Label: COINBASE_CRYPTO_ENGINE
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$SCRIPT_DIR/stop.sh"
sleep 1
bash "$SCRIPT_DIR/start.sh"
echo "OK: RBOTZILLA_COINBASE_CLEAN engine restarted"
