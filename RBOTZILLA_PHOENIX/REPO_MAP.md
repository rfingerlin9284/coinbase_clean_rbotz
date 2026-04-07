# REPO_MAP.md — Phase 1 Inventory
# RBOTZILLA_OANDA_CLEAN

Generated: 2026-03-17
Label convention: RUNTIME_VERIFIED | CODE_VERIFIED | UNVERIFIED | DISCARD

---

## SOURCE A: /home/rfing/RBOTZILLA_PHOENIX

### Core Engine
| File | Lines | Label | Notes |
|---|---|---|---|
| `oanda_trading_engine.py` | ~4250 | RUNTIME_VERIFIED | Main engine — heavily patched this session. Too monolithic to carry wholesale. Extract logic only. |
| `startup_sequence.py` | 440 | CODE_VERIFIED | Patched to show live broker state. Extractable. |

### Broker Layer
| File | Lines | Label | Notes |
|---|---|---|---|
| `brokers/oanda_connector.py` | 1019 | RUNTIME_VERIFIED | 25 public methods. place_oco_order, get_account_info, set_trade_stop, get_trades, get_historical_data, pricing endpoint all runtime-confirmed |
| `brokers/oanda_connector_enhanced.py` | ? | UNVERIFIED | Enhanced variant — not tested this session |

### Signal / Strategy Layer
| File | Lines | Label | Notes |
|---|---|---|---|
| `systems/multi_signal_engine.py` | 1186 | RUNTIME_VERIFIED | scan_symbol(), session_bias(), AggregatedSignal. Produces real candidates. |
| `strategies/registry.py` | ? | UNVERIFIED | Strategy loader |
| `strategies/base.py` | ? | UNVERIFIED | Base class |
| `strategies/liquidity_sweep.py` | ? | UNVERIFIED | Detector used in runtime |
| `strategies/trap_reversal_scalper.py` | ? | UNVERIFIED | Detector used in runtime |
| `strategies/fib_confluence_breakout.py` | ? | UNVERIFIED | Detector used in runtime |
| `strategies/institutional_sd.py` | ? | UNVERIFIED | |
| `strategies/bullish_wolf.py` | ? | UNVERIFIED | Wolf pack pattern |
| `strategies/bearish_wolf.py` | ? | UNVERIFIED | Wolf pack pattern |
| `strategies/price_action_holy_grail.py` | ? | UNVERIFIED | |
| `strategies/sideways_wolf.py` | ? | UNVERIFIED | |
| `strategies/crypto_breakout.py` | ? | DISCARD | Crypto-specific, not needed for OANDA-only |

### Risk Layer
| File | Lines | Label | Notes |
|---|---|---|---|
| `foundation/margin_correlation_gate.py` | 506 | CODE_VERIFIED | pre_trade_gate(), margin_gate(). Default NAV bug patched. |
| `risk/oco_validator.py` | 468 | UNVERIFIED | OCO payload validation |
| `risk/dynamic_sizing.py` | 500 | UNVERIFIED | Position sizing |
| `risk/momentum_adaptive_sl.py` | ? | UNVERIFIED | Adaptive SL |
| `foundation/rick_charter.py` | ? | UNVERIFIED | Charter rules |

### Narration / Logging
| File | Lines | Label | Notes |
|---|---|---|---|
| `scripts/narration_live.py` | ? | UNVERIFIED | Live JSONL tail viewer |
| narration.jsonl (runtime) | runtime | RUNTIME_VERIFIED | Fields: timestamp, event_type, symbol, venue, details |

### Scripts (shell)
| File | Label | Notes |
|---|---|---|
| `scripts/task_restart_practice.sh` | RUNTIME_VERIFIED | stop + start — works |
| `scripts/task_start_practice.sh` | RUNTIME_VERIFIED | Starts engine under nohup |
| `scripts/task_stop_practice.sh` | RUNTIME_VERIFIED | Kills engine cleanly |
| `scripts/task_tail_engine.sh` | UNVERIFIED | |
| `scripts/task_tail_narration.sh` | UNVERIFIED | |
| `scripts/task_broker_isolation_check.sh` | UNVERIFIED | |
| `scripts/task_trade_health_check.sh` | UNVERIFIED | |
| `scripts/rbot_ctl.sh` | UNVERIFIED | |

### DISCARD (Phoenix)
| File | Reason |
|---|---|
| `dec4_dec10/` | Old patch proposals |
| `fix_oanda.py`, `test_der.py`, `test_margin.py` | One-off debug |
| `hive/browser_ai_connector.py`, `hive/rick_hive_browser.py` | Browser automation |
| `ml_learning/` | Not available at runtime ("basic mode") |
| `hedge_fund_orchestrator.py`, `orchestrator_start.py` | Multi-broker, not needed |
| `util/news_spread_gate.py` | Uses fake simulation (line 3757 Phoenix) |
| `brokers/alpaca_connector.py`, `brokers/ib_connector.py`, `brokers/coinbase_*.py` | Not OANDA |
| `maintenance_agent.py`, `audit_self_optimization.py` | Agent scaffolding |
| `autonomous_boot.py` | Not needed in clean repo |
| `dashboard/`, `dashboard_supervisor.py` | Optional — defer to Phase 2 |
| `strategies/crypto_breakout.py` | Crypto-specific |

---

## SOURCE B: /home/rfing/RBOTZILLA_PHOENIX/_source_repos/rick_clean_live

### Broker Layer
| File | Label | Notes |
|---|---|---|
| `brokers/oanda_connector.py` | UNVERIFIED | May be older version. Not tested. |
| `brokers/oanda_connector_enhanced.py` | UNVERIFIED | Enhanced variant |
| `bridges/oanda_charter_bridge.py` | UNVERIFIED | Charter-aware bridge |
| `RICK_LIVE_PROTOTYPE/brokers/oanda_connector.py` | UNVERIFIED | Prototype variant |

### Risk
| File | Label | Notes |
|---|---|---|
| `risk/oco_validator.py` | UNVERIFIED | May be cleaner than Phoenix version |
| `risk/dynamic_sizing.py` | UNVERIFIED | |

### Narration
| File | Label | Notes |
|---|---|---|
| `RICK_LIVE_PROTOTYPE/util/narration_logger.py` | UNVERIFIED | Standalone narration — likely cleaner |

### DISCARD (rick_clean_live)
| Path | Reason |
|---|---|
| `_archive_scripts/` | Archived — not production |
| `canary_trading_engine_OLD_DEPRECATED.py` | Explicitly deprecated |
| `ROLLBACK_SNAPSHOTS/` | Snapshot only |
| `connectors/futures/` | Futures, not forex |
| `connectors/yahoo_cryptopanic_connector.py` | Not needed |
| `swarm/`, `wolf_packs/` | Prototype patterns |
| `RICK_LIVE_PROTOTYPE/ghost_trading_engine.py` | Ghost/simulation |
| `RICK_LIVE_PROTOTYPE/live_ghost_engine.py` | Ghost/simulation |
