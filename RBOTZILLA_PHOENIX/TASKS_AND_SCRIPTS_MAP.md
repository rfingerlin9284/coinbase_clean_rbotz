# TASKS_AND_SCRIPTS_MAP.md — Phase 1
# RBOTZILLA_OANDA_CLEAN

Generated: 2026-03-17

---

## Shell Scripts — Phoenix (RUNTIME_VERIFIED)

| Script | What it does | Carry? |
|---|---|---|
| `task_restart_practice.sh` | stop + start | YES — copy directly |
| `task_start_practice.sh` | nohup engine → logs/practice_session.log | YES |
| `task_stop_practice.sh` | pkill or pid-file kill | YES |
| `task_tail_engine.sh` | tail -f logs/practice_session.log | YES |
| `task_tail_narration.sh` | tail narration.jsonl with pretty print | YES |
| `task_broker_isolation_check.sh` | checks broker endpoint is practice | YES |
| `task_trade_health_check.sh` | checks open trades vs local positions | YES |
| `rbot_ctl.sh` | general control script | MAYBE — inspect first |
| `validate_practice_stack.sh` | preflight check | MAYBE |
| `narration_live.py` | Python narration tail viewer | YES |

---

## VS Code Tasks — Phoenix (.vscode/tasks.json — patched this session)

9 tasks confirmed written:
1. Start RBOTzilla Practice Engine
2. Stop RBOTzilla Practice Engine
3. Restart RBOTzilla Practice Engine
4. Broker Isolation Check
5. Trade Health Check
6. Tail Engine Log
7. Tail Narration Log
8. Show Current OANDA Config
9. Reconcile Broker vs Local Positions

**Carry to clean repo:** YES — these are the target task set. Rebuild with updated paths.

---

## VS Code Tasks — Target for RBOTZILLA_OANDA_CLEAN

| Task | Command |
|---|---|
| Start Clean Practice Engine | `bash scripts/start.sh` |
| Stop Clean Practice Engine | `bash scripts/stop.sh` |
| Restart Clean Practice Engine | `bash scripts/restart.sh` |
| Tail Engine Log | `tail -f logs/engine.log` |
| Tail Narration Log | Python pretty-printer on narration.jsonl |
| Show OANDA Account | inline Python: balance, margin, trades |
| Reconcile Broker vs Local | inline Python: broker trades vs engine state |
| Trade Health Check | `bash scripts/health_check.sh` |
| Broker Tradability Check | inline Python: call /pricing, show tradeable + spread |

---

## Discarded Scripts

| Script | Reason |
|---|---|
| `coinbase_headless.py` | Coinbase — not needed |
| `train_initial_ml_model.py` | ML not available at runtime |
| `audit_today_trades_et.py` | ET timezone — not portable |
| `edge_kpi_report_et.py` | ET timezone — not portable |
| `build_prototype_backup.sh` | Repo management — not engine |
| `collect_practice_session_evidence.sh` | Ad-hoc utility |
| `preflight_practice_session.sh` | Phoenix-specific paths |
| `run_practice_wsl.sh` | WSL-specific |
| `start_headless.sh` | Headless mode — defer |
| `watch_practice_session.sh` | Ad-hoc watcher |
