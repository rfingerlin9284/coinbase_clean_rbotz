# 🚨 AGENT RECOVERY MANIFEST & INSTRUCTION PROTOCOL 🚨

## To Any Future AI Agent or Operator:
You have been provided with this ZIP archive containing the verified, stable snapshot of **RBOTZILLA_OANDA_CLEAN** as of March 26, 2026. 

This snapshot was taken explicitly BEFORE any experimental time-based scheduling logic was added to the `.env` or Python runtime. 

### What This Snapshot Represents:
1. **The 15-Minute Cooldown Patch:** The engine is permanently hardened against micro-trading. The `RBOT_PAIR_REENTRY_COOLDOWN_MINUTES=15` lock is natively injected into `.env`.
2. **The 75% Confidence Benchmark:** The signal threshold was raised to 0.75 out-of-the-box in `trade_engine.py` to match Phoenix profitability.
3. **Advanced Telemetry:** `script/human_tail.py` and `trade_manager.py` are natively synced to output dynamic R:R tracking, SL distances, and PNL percentages.
4. **Live Trading Defenses:** `QuantHedgeEngine` is disabled (`RBOT_HEDGE_ENABLED=false`), and OCO stops are strictly enforced.

### How To Reconstruct from this Backup:
If the LIVE working directory is corrupted, you, the Agent, must do the following:

1. **Purge the old live state:** 
   `rm -rf /home/rfing/RBOTZILLA_OANDA_CLEAN/*`
2. **Unzip this archive directly into the working directory:**
   `unzip RBOTZILLA_OANDA_CLEAN_SNAPSHOT_BACKUP.zip -d /home/rfing/RBOTZILLA_OANDA_CLEAN/`
3. **Restore file locks:** Ensure all python engine scripts and shell scripts are locked securely to prevent unauthorized overwrite.
   `chmod 444 /home/rfing/RBOTZILLA_OANDA_CLEAN/engine/*.py`
   `chmod 444 /home/rfing/RBOTZILLA_OANDA_CLEAN/scripts/*.sh`
   `chmod 444 /home/rfing/RBOTZILLA_OANDA_CLEAN/.env`
4. **Validate the reconstruction:**
   Boot `bash scripts/restart.sh` and verify the Live Tail telemetry prints the proper "World State" boot block.

**DO NOT DEVIATE.** This snapshot is the exact verified state of the engine capturing trend continuations with institutional gates.
