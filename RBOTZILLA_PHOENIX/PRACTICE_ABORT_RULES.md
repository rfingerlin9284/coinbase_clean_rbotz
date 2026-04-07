# PRACTICE ABORT RULES

Primary stop command:
```bash
cd ~/RBOTZILLA_PHOENIX
bash scripts/stop_practice_session.sh
```

Fallback:

```bash
cd ~/RBOTZILLA_PHOENIX
bash turn_off.sh || true
pkill -9 -f "oanda_trading_engine.py|headless_runtime.py|orchestrator_start.py" || true
```

| Trigger                    | What to look for                                                  |
| -------------------------- | ----------------------------------------------------------------- |
| Any traceback              | `Traceback (most recent call last):`                              |
| Live-account indicator     | `LIVE`, missing `PAPER TRADING`, unexpected `--yes-live` behavior |
| Repeated crash loop        | Same error 3+ times in 5 minutes                                  |
| Missing OCO                | A trade is placed, but the `hedge_fund_orchestrator` fails to log OCO creation |
| Runaway trade count        | abnormal rapid position growth                                    |
| Suspicious exposure        | huge notional / margin alarm / repeated guard breaches            |
| Dashboard exposure wrong   | dashboard starts on non-local bind when not intended              |
| TypeError / AttributeError | any old crash marker returns                                      |
