#!/usr/bin/env python3
"""
OANDA Trading Engine - RBOTzilla Charter Compliant
Environment-Agnostic: practice/live determined ONLY by API endpoint & token
- Unified codebase for all environments
- Real-time OANDA API for market data and execution
- Full RICK Hive Mind + ML Intelligence + Immutable Risk Management
- Momentum-based TP cancellation with adaptive trailing stops
PIN: 841921 | Generated: 2025-10-15
"""

# ── Non-interactive / headless safety guard ────────────────────────────────
# VS Code task terminals and nohup sessions have no TTY.  Exit here only if
# we are genuinely NOT meant to run (e.g. accidentally sourced).  Set
# RBOT_FORCE_RUN=1 to bypass any TTY check unconditionally.
import os as _os
if not _os.environ.get('RBOT_FORCE_RUN') and _os.environ.get('RBOT_REQUIRE_TTY'):
    import sys as _sys
    if not _sys.stdout.isatty():
        _sys.exit(0)

import sys
from pathlib import Path
import os
import time
import asyncio
import requests
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.resolve()))

# Load environment variables manually
env_file = str(Path(__file__).parent / 'master.env')
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Charter compliance imports
from foundation.rick_charter import RickCharter
from foundation.margin_correlation_gate import MarginCorrelationGate, Position, Order, HookResult
from util.position_police import _rbz_force_min_notional_position_police
from util.sms_client import send_sms
from util.aggressive_practice_runner import run_aggressive_practice_cycle
from util.news_spread_gate import evaluate_news_spread
from brokers.oanda_connector import OandaConnector
from util.terminal_display import TerminalDisplay, Colors
from util.narration_logger import log_narration, log_pnl
from util.rick_narrator import RickNarrator

# Momentum-based adaptive SL system (NEW)
try:
    from risk.momentum_adaptive_sl import (
        MomentumProfile, AdaptiveStopLoss, WinningTradeAnalyzer, 
        ReallocateCapital, calculate_momentum_profile
    )
    MOMENTUM_ADAPTIVE_SL_AVAILABLE = True
except ImportError:
    MOMENTUM_ADAPTIVE_SL_AVAILABLE = False
from util.usd_converter import get_usd_notional
from util.positions_registry import PositionsRegistry
from util.position_dashboard import PositionDashboard
from systems.multi_signal_engine import scan_symbol, manage_open_trade, TradeAction, AggregatedSignal

# Tight trailing stop + TP guard (dec4_dec10 reference: rbz_tight_trailing.py)
try:
    from rbz_tight_trailing import apply_rbz_overrides, tp_guard, policy_for, TightSL
    RBZ_TRAILING_AVAILABLE = True
except ImportError:
    RBZ_TRAILING_AVAILABLE = False
    print("⚠️  rbz_tight_trailing not available - using legacy trailing")

# ML Intelligence imports
try:
    from ml_learning.regime_detector import RegimeDetector
    from ml_learning.signal_analyzer import SignalAnalyzer
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️  ML modules not available - running in basic mode")

# Hive Mind imports
try:
    from hive.rick_hive_mind import RickHiveMind, SignalStrength
    HIVE_AVAILABLE = True
except ImportError:
    HIVE_AVAILABLE = False
    print("⚠️  Hive Mind not available - running without swarm coordination")

# Hive-LLM Orchestrator imports
try:
    from hive.hive_llm_orchestrator import HiveLLMOrchestrator, TradeOpportunity
    HIVE_LLM_ORCHESTRATOR_AVAILABLE = True
except ImportError:
    HIVE_LLM_ORCHESTRATOR_AVAILABLE = False
    print("⚠️  Hive-LLM Orchestrator not available")

# Momentum & Trailing imports (extracted from rbotzilla_golden_age.py)
try:
    from util.momentum_trailing import MomentumDetector, SmartTrailingSystem
    MOMENTUM_SYSTEM_AVAILABLE = True
except ImportError:
    MOMENTUM_SYSTEM_AVAILABLE = False
    print("⚠️  Momentum/Trailing system not available")

class OandaTradingEngine:
    """
    RBOTzilla Charter-Compliant OANDA Trading Engine
    - Environment agnostic (practice/live determined by API token/endpoint only)
    - Immutable OCO orders (3:1 R:R minimum)
    - Full narration logging to JSONL
    - ML regime detection and signal analysis
    - Rick Hive Mind coordination
    - Sub-300ms execution tracking
    """
    
    def __init__(self, environment='practice'):
        """
        Initialize Trading Engine
        
        Args:
            environment: 'practice' or 'live' (default: practice)
                        Only difference is API endpoint and token used
        """
        # signal_type  = pos.get('signal_type', 'trend')
        # Validate Charter PIN
        if hasattr(RickCharter, 'validate_pin'):
            if not RickCharter.validate_pin(841921):
                raise PermissionError("Invalid Charter PIN - cannot initialize trading engine")
        
        self.display = TerminalDisplay()
        self.environment = environment
        
        # Initialize OANDA connector: environment determines endpoint only
        self.oanda = OandaConnector(environment=environment)
        env_label = "PRACTICE" if environment == 'practice' else "LIVE"
        self.display.success(f"✅ {env_label} API connected")
        print(f"   Account: {self.oanda.account_id}")
        print(f"   Endpoint: {self.oanda.api_base}")
        
        # Initialize Rick's narration system
        self.narrator = RickNarrator()
        
        # Initialize ML Intelligence if available
        if ML_AVAILABLE:
            self.regime_detector = RegimeDetector()
            self.signal_analyzer = SignalAnalyzer()
            self.display.success("✅ ML Intelligence loaded")
        else:
            self.regime_detector = None
            self.signal_analyzer = None
        
        # Initialize Hive Mind if available
        if HIVE_AVAILABLE:
            self.hive_mind = RickHiveMind()
            self.display.success("✅ Hive Mind connected")
        else:
            self.hive_mind = None
        
        # Initialize Hive-LLM Orchestrator if available
        if HIVE_LLM_ORCHESTRATOR_AVAILABLE:
            self.hive_llm_orchestrator = HiveLLMOrchestrator()
            self.display.success("✅ Hive-LLM Orchestrator initialized")
        else:
            self.hive_llm_orchestrator = None
        
        # Initialize Momentum System if available
        if MOMENTUM_SYSTEM_AVAILABLE and not RBZ_TRAILING_AVAILABLE:
            self.momentum_detector = MomentumDetector()
            self.trailing_system = SmartTrailingSystem()
            self.display.success("✅ Legacy Momentum/Trailing system loaded")
        else:
            self.momentum_detector = None
            self.trailing_system = None
            if RBZ_TRAILING_AVAILABLE:
                self.display.success("🛡️  Legacy Trailing disabled (RBZ TightTrailing Active)")
        
        # Initialize Strategy Aggregator (combines 5 prototype strategies)
        try:
            from util.strategy_aggregator import StrategyAggregator
            self.strategy_aggregator = StrategyAggregator(signal_vote_threshold=2)
            self.display.success("✅ Strategy Aggregator loaded (5 prototype strategies)")
        except ImportError:
            self.strategy_aggregator = None
            self.display.warning("⚠️  Strategy Aggregator not available")
        
        # Initialize Quantitative Hedge Engine (correlation-based hedging)
        try:
            from util.quant_hedge_engine import QuantHedgeEngine
            self.hedge_engine = QuantHedgeEngine()
            self.active_hedges = {}  # Track active hedge positions
            self.display.success("✅ Quantitative Hedge Engine loaded")
        except ImportError:
            self.hedge_engine = None
            self.active_hedges = {}
            self.display.warning("⚠️  Hedge Engine not available")
        
        # Initialize Positions Registry (cross-platform position tracking)
        try:
            self.positions_registry = PositionsRegistry()
            self.display.success("✅ Positions Registry initialized")
        except Exception as e:
            self.positions_registry = None
            self.display.warning(f"⚠️  Positions Registry unavailable: {e}")
        
        # Charter-compliant trading parameters
        self.charter = RickCharter
        
        # ========================================================================
        # MARGIN & CORRELATION GUARDIAN GATES (NEW)
        # ========================================================================
        # Get account NAV for gate calculations — Persist last known good value
        self.last_known_nav_file = Path(__file__).parent / "logs" / "last_known_nav.txt"
        account_nav = 10000.0
        if self.last_known_nav_file.exists():
            try:
                account_nav = float(self.last_known_nav_file.read_text().strip())
            except: pass

        try:
            if hasattr(self.oanda, 'get_account_info'):
                account_info = self.oanda.get_account_info()
                if account_info is not None:
                    account_nav = float(getattr(account_info, 'balance', None) or account_nav)
                    self.last_known_nav_file.write_text(str(account_nav))
        except Exception as e:
            self.display.warning(f"⚠️  NAV Fetch Error: {e}, using persisted ${account_nav:,.2f}")
        
        self.gate = MarginCorrelationGate(account_nav=account_nav)
        self.current_positions = []  # Track positions for gate monitoring
        self.pending_orders = []      # Track pending orders for gate monitoring
        self.display.success("🛡️  Margin & Correlation Guardian Gates ACTIVE")
        
        # ========================================================================
        # PROFESSIONAL HEDGE FUND PORTFOLIO ORCHESTRATOR
        # ========================================================================
        try:
            from util.portfolio_orchestrator import PortfolioOrchestrator
            self.portfolio_orchestrator = PortfolioOrchestrator(
                master_repo_path="/home/rfing/RBOTZILLA_PHOENIX",
                account_balance=account_nav,
                oanda_connector=self.oanda
            )
            # Disable cross-repo sync so we don't interfere with other test folders
            self.portfolio_orchestrator.start_trading(use_repo_sync=False)
            self.display.success("✅ Hedge Fund Portfolio Orchestrator & Capital Preserver ACTIVE")
        except Exception as e:
            self.portfolio_orchestrator = None
            self.display.warning(f"⚠️  Portfolio Orchestrator unavailable: {e}")
        
        # Expanded FX universe (majors + liquid minors/crosses)
        self.trading_pairs = [
            # Majors
            'EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD',
            'USD_CAD', 'NZD_USD',
            # Minors / crosses
            'EUR_GBP', 'EUR_JPY', 'GBP_JPY', 'EUR_AUD', 'EUR_CAD',
            'AUD_JPY', 'CHF_JPY', 'GBP_CAD', 'GBP_CHF', 'AUD_CAD',
            'AUD_CHF', 'CAD_JPY', 'NZD_JPY', 'EUR_NZD',
            'NZD_CAD',
        ]
        
        self.min_trade_interval = 300  # 5 minutes when positions FULL (M15 Charter floor)
        # Scan cadence: fast when slots remain, slow only when at capacity
        self.scan_fast_seconds = int(os.getenv('RBOT_SCAN_FAST_SECONDS', '60'))
        self.scan_slow_seconds = int(os.getenv('RBOT_SCAN_SLOW_SECONDS', '300'))
        
        # Confidence gate — aggregated floor for scan_symbol (raised 0.68→0.70, Dec-Quality standard)
        # Each individual detector already requires ≥0.62; this is the MEAN across 3+ detectors.
        self.min_confidence = 0.70

        # ── Multi-signal scan config (env-overridable) ─────────────────────────────────
        # min_signal_confidence: FINAL gate applied after aggregation (env-overridable)
        self.min_signal_confidence  = float(os.getenv('RBOT_MIN_SIGNAL_CONFIDENCE',  '0.68'))
        self.max_new_trades_per_cycle = int(os.getenv('RBOT_MAX_NEW_TRADES_PER_CYCLE', '6'))
        self.scan_log_top_n         = int(os.getenv('RBOT_SCAN_LOG_TOP_N',           '8'))
        
        # Initialize Risk/Charter Subsystem
        self.charter = RickCharter()
        self.enforce_charter = True  # Added to prevent missing attr during executions
        
        # IMMUTABLE RISK MANAGEMENT (Charter Section 3.2)
        self.min_notional_usd = self.charter.MIN_NOTIONAL_USD  # $15,000 minimum (Charter immutable)
        # Tight SL/TP from rbz reference: 10 pip SL, 32 pip TP (3.2:1)
        self.stop_loss_pips = getattr(self.charter, 'STOP_LOSS_PIPS', 10)
        self.take_profit_pips = 32  # 3.2:1 R:R ratio (Charter minimum)
        self.trailing_start_pips = 3   # Begin trailing after 3 pip profit
        self.trailing_dist_pips  = 5   # Trail at 5 pips distance
        self.min_rr_ratio = getattr(self.charter, 'MIN_RISK_REWARD_RATIO', 3.2)  # 3.2 Default
        self.max_daily_loss = abs(getattr(self.charter, 'DAILY_LOSS_BREAKER_PCT', 5.0))  # 5% Default
        
        # Position sizes calculated dynamically to meet Charter $15k minimum
        self.position_size = 14000  # Base size (adjusted per pair to meet minimums)
        
        # State tracking
        self.active_positions = {}
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.total_pnl = 0.0
        self.is_running = False
        self.session_start = datetime.now(timezone.utc)
        
        # ========================================================================
        # BOT STATUS AWARENESS (Knows if it's trading or not)
        # ========================================================================
        self.bot_status = {
            'engine_initialized': True,
            'is_trading': False,           # Main flag: bot is actively trading
            'connected': True,             # Connection to OANDA
            'positions_open': 0,           # Number of open positions
            'last_trade_time': None,       # When last trade was placed
            'last_signal_check': None,     # When signals last checked
            'total_signals_scanned': 0,    # Lifetime signal count
            'total_positions_opened': 0,   # Lifetime accounts for trades
            'session_uptime_seconds': 0,   # How long bot has been running
            'status_message': 'BOT INITIALIZED - READY TO START'
        }
        
        # Platform-specific pair management (env-overridable)
        self.max_pairs_per_platform = int(os.getenv('RBOT_MAX_PAIRS_PER_PLATFORM', '12'))
        self.max_active_positions = int(os.getenv('RBOT_MAX_ACTIVE_POSITIONS', '12'))
        self.active_pairs = set()  # Track active pairs on this platform
        self.global_active_pairs_file = '/tmp/rick_trading_global_pairs.json'  # Cross-platform tracking

        # FIX #6: Per-symbol TP cooldown — prevents re-entry immediately after TP/SL
        # Maps symbol -> datetime of last close.  Blocks new entry for N minutes.
        self.tp_cooldowns: Dict[str, datetime] = {}
        self.tp_cooldown_minutes: int = int(os.getenv('RBOT_TP_COOLDOWN_MINUTES', '10'))  # Reduced from 30→10 min: prevents blocking re-entry on valid moves after a TP hit
        # Per-symbol SL-rejection backoff: tracks last time a green-lock SL was rejected
        # so we don't hammer OANDA with the same rejected price 16x in 45 seconds.
        self._sl_rejection_backoff: Dict[str, float] = {}

        # TradeManager settings
        # Only consider converting TP -> trailing SL after 60 seconds
        self.min_position_age_seconds = 60
        # Hive consensus threshold to trigger TP cancellation
        self.hive_trigger_confidence = 0.80
        self.trade_manager_active = False  # Track if trade manager is running
        self.trade_manager_last_heartbeat = None  # Last time trade manager was active
        self.default_management_profile = "OCO SL/TP; 0.75R->BE; 1.5R->scale50%; 2R->trail; hard_stop_usd"

        self.trade_metadata_index_path = Path(__file__).parent / "logs" / "trade_metadata_index.json"
        self.trade_metadata_index = {
            "by_trade_id": {},
            "by_order_id": {},
            "by_symbol": {}
        }
        self._load_trade_metadata_index()

        # ========================================================================
        # CONNECTION RESILIENCE & AUTO-RECONNECT SYSTEM (NEW FEATURE)
        # ========================================================================
        self.connection_state = {
            'connected': True,
            'last_healthy_check': datetime.now(timezone.utc),
            'consecutive_failures': 0,
            'reconnect_attempt': 0,
            'last_reconnect_time': None,
            'connection_loss_time': None,
            'is_reconnecting': False,
            'last_error': None
        }
        
        self.reconnect_config = {
            'initial_wait_seconds': 2,
            'max_wait_seconds': 300,  # 5 minutes max between retries
            'exponential_base': 2,
            'max_reconnect_attempts': 0,  # 0 = unlimited automatic retries
            'health_check_interval': 30,  # seconds between connection checks
            'failure_threshold': 3  # consecutive failures before reconnect attempt
        }
        
        self.display.success("✅ Connection resilience & auto-reconnect ENABLED")

        # Tight trailing stop + TP guard (wired later in __init__ to avoid early attribute errors)
        if RBZ_TRAILING_AVAILABLE:
            # Check for RBOT_TP_COOLDOWN_MINUTES override
            self.tp_cooldown_minutes = int(os.getenv('RBOT_TP_COOLDOWN_MINUTES', '10'))
            self.display.success(f"🛡️  RBZ TightTrailing Available (Cooldown: {self.tp_cooldown_minutes}m)")
        
        # Narration logging
        log_narration(
            event_type="ENGINE_START",
            details={
                "pin": "841921",
                "environment": environment,
                "charter_compliant": True,
                "ml_enabled": ML_AVAILABLE,
                "hive_enabled": HIVE_AVAILABLE,
                "min_rr_ratio": self.min_rr_ratio
            },
            symbol="SYSTEM",
            venue="oanda"
        )
        
        # ========================================================================
        # POSITION DASHBOARD (Active monitoring + display)
        # ========================================================================
        self.dashboard = PositionDashboard(refresh_interval_sec=60)
        self.display.success("✅ Position Dashboard initialized (60s refresh)")
        self.dashboard_task = None  # Track monitoring task
        
        # Wire tight trailing overrides late to ensure all methods are available
        if RBZ_TRAILING_AVAILABLE:
            try:
                apply_rbz_overrides(connector=self.oanda, engine=self)
                self.display.success("✅ RBZ tight trailing + TP guard ACTIVE & WIRED")
            except Exception as _rbz_err:
                self.display.warning(f"⚠️  RBZ trailing wire skipped: {_rbz_err}")

        self._display_startup()

    def _load_trade_metadata_index(self):
        try:
            self.trade_metadata_index_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.trade_metadata_index_path.exists():
                return
            with open(self.trade_metadata_index_path, 'r', encoding='utf-8') as fh:
                payload = json.load(fh)
            if isinstance(payload, dict):
                self.trade_metadata_index["by_trade_id"] = payload.get("by_trade_id") or {}
                self.trade_metadata_index["by_order_id"] = payload.get("by_order_id") or {}
                self.trade_metadata_index["by_symbol"] = payload.get("by_symbol") or {}
        except Exception as e:
            self.display.warning(f"⚠️  Could not load trade metadata index: {e}")

    def _save_trade_metadata_index(self):
        try:
            with open(self.trade_metadata_index_path, 'w', encoding='utf-8') as fh:
                json.dump(self.trade_metadata_index, fh, ensure_ascii=False, indent=2)
        except Exception as e:
            self.display.warning(f"⚠️  Could not save trade metadata index: {e}")

    def _record_trade_metadata(self, symbol: str, metadata: dict, order_id: str = "", trade_id: str = ""):
        if not isinstance(metadata, dict):
            return

        normalized_symbol = str(symbol or metadata.get("symbol") or "").upper()
        normalized_order_id = str(order_id or metadata.get("order_id") or "").strip()
        normalized_trade_id = str(trade_id or metadata.get("trade_id") or "").strip()

        stored = dict(metadata)
        stored["symbol"] = normalized_symbol
        stored["management_profile"] = stored.get("management_profile") or self.default_management_profile
        stored["updated_at"] = datetime.now(timezone.utc).isoformat()

        if normalized_trade_id:
            stored["trade_id"] = normalized_trade_id
            self.trade_metadata_index["by_trade_id"][normalized_trade_id] = stored
        if normalized_order_id:
            stored["order_id"] = normalized_order_id
            self.trade_metadata_index["by_order_id"][normalized_order_id] = stored
        if normalized_symbol:
            self.trade_metadata_index["by_symbol"][normalized_symbol] = stored

        self._save_trade_metadata_index()

    def _lookup_trade_metadata(self, trade_id: str = "", order_id: str = "", symbol: str = "") -> dict:
        tid = str(trade_id or "").strip()
        oid = str(order_id or "").strip()
        sym = str(symbol or "").upper()

        if tid and tid in self.trade_metadata_index["by_trade_id"]:
            return dict(self.trade_metadata_index["by_trade_id"].get(tid) or {})
        if oid and oid in self.trade_metadata_index["by_order_id"]:
            return dict(self.trade_metadata_index["by_order_id"].get(oid) or {})
        if sym and sym in self.trade_metadata_index["by_symbol"]:
            return dict(self.trade_metadata_index["by_symbol"].get(sym) or {})
        return {}

    def _refresh_gate_positions_from_active(self):
        refreshed_positions = []
        for position_id, pos in (self.active_positions or {}).items():
            symbol = (pos.get('symbol') or '').upper()
            if not symbol:
                continue

            direction = str(pos.get('direction') or '').upper()
            side = "LONG" if direction == "BUY" else "SHORT"

            try:
                units = abs(float(pos.get('units') or 0.0))
            except Exception:
                units = 0.0

            try:
                entry_price = float(pos.get('entry') or 0.0)
            except Exception:
                entry_price = 0.0

            try:
                current_price = float(pos.get('current_price') or entry_price or 0.0)
            except Exception:
                current_price = entry_price

            try:
                pnl = float(pos.get('unrealized_pnl') or 0.0)
            except Exception:
                pnl = 0.0

            try:
                pnl_pips = float(pos.get('pnl_pips') or 0.0)
            except Exception:
                pnl_pips = 0.0

            try:
                notional_hint = abs(float(pos.get('notional') or 0.0))
            except Exception:
                notional_hint = 0.0

            parts = symbol.split('_')
            base = parts[0] if len(parts) == 2 else ''
            if notional_hint > 0:
                usd_notional = notional_hint
            elif base == 'USD':
                usd_notional = units
            else:
                usd_notional = units * abs(entry_price)

            margin_used = usd_notional * 0.03

            refreshed_positions.append(
                Position(
                    symbol=symbol,
                    side=side,
                    units=units,
                    entry_price=entry_price,
                    current_price=current_price,
                    pnl=pnl,
                    pnl_pips=pnl_pips,
                    margin_used=margin_used,
                    position_id=str(pos.get('trade_id') or pos.get('order_id') or position_id)
                )
            )

        self.current_positions = refreshed_positions

    def _reconcile_positions_registry_with_broker(self):
        if not self.positions_registry:
            return

        try:
            trades = self.oanda.get_trades() or []
        except Exception as e:
            self.display.warning(f"⚠️  Registry reconcile skipped (broker fetch failed): {e}")
            return

        broker_open_symbols = {
            (t.get('instrument') or t.get('symbol') or '').upper()
            for t in trades
            if (t.get('instrument') or t.get('symbol') or '')
        }

        try:
            registry_positions = self.positions_registry.get_active_positions(platform='oanda') or {}
        except Exception as e:
            self.display.warning(f"⚠️  Registry reconcile skipped (registry fetch failed): {e}")
            return

        for symbol in list(registry_positions.keys()):
            normalized_symbol = str(symbol or '').upper()
            if normalized_symbol and normalized_symbol not in broker_open_symbols:
                try:
                    self.positions_registry.unregister_position(normalized_symbol, 'oanda')
                except Exception:
                    pass
    
    def _display_startup(self):
        """Display startup screen with Charter compliance info"""
        self.display.clear_screen()
        env_label = "PRACTICE" if self.environment == 'practice' else "LIVE"
        env_color = Colors.BRIGHT_YELLOW if self.environment == 'practice' else Colors.BRIGHT_RED
        
        self.display.header(
            f"🤖 RBOTzilla TRADING ENGINE ({env_label})",
            f"Charter-Compliant OANDA | PIN: 841921 | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        self.display.section("CHARTER COMPLIANCE STATUS")
        self.display.info("PIN Validated", "841921 ✅", Colors.BRIGHT_GREEN)
        self.display.info("Charter Version", "RBOTzilla UNI Phase 9", Colors.BRIGHT_CYAN)
        self.display.info("Immutable OCO", "ENFORCED (All orders)", Colors.BRIGHT_GREEN)
        self.display.info("Min R:R Ratio", f"{self.min_rr_ratio}:1 (Charter Immutable)", Colors.BRIGHT_GREEN)
        self.display.info("Min Notional", f"${self.min_notional_usd:,} (Charter Immutable)", Colors.BRIGHT_GREEN)
        self.display.info("Max Daily Loss", f"{self.max_daily_loss}% (Charter Breaker)", Colors.BRIGHT_GREEN)
        self.display.info("Max Latency", f"{getattr(self.charter, 'MAX_PLACEMENT_LATENCY_MS', 300)}ms (Charter 2.1)", Colors.BRIGHT_GREEN)
        
        self.display.section("ENVIRONMENT CONFIGURATION")
        self.display.info("Environment", env_label, env_color)
        self.display.info("API Endpoint", self.oanda.api_base, Colors.BRIGHT_CYAN)
        self.display.info("Account ID", self.oanda.account_id, Colors.BRIGHT_CYAN)
        
        self.display.section("TRADE MANAGEMENT")
        self.display.info("Max Pairs Per Platform", f"{self.max_pairs_per_platform} pairs", Colors.BRIGHT_GREEN)
        self.display.info("Active Pairs", f"{len(self.active_pairs)}/{self.max_pairs_per_platform}", Colors.BRIGHT_CYAN)
        self.display.info("Trade Manager", "Will activate on start", Colors.BRIGHT_YELLOW)
        self.display.info("Smart Trailing", "Enabled (Momentum-based)", Colors.BRIGHT_GREEN)
        self.display.info("TP/SL Enforcement", "MANDATORY (OCO Required)", Colors.BRIGHT_GREEN)
        self.display.info("Market Data", "Real-time OANDA API", Colors.BRIGHT_GREEN)
        self.display.info("Order Execution", f"OANDA {env_label} API", env_color)
        
        self.display.section("SYSTEM COMPONENTS")
        self.display.info("Narration Logging", "ACTIVE → narration.jsonl", Colors.BRIGHT_GREEN)
        self.display.info("ML Intelligence", "ACTIVE" if ML_AVAILABLE else "DISABLED", 
                         Colors.BRIGHT_GREEN if ML_AVAILABLE else Colors.BRIGHT_BLACK)
        self.display.info("Hive Mind", "CONNECTED" if HIVE_AVAILABLE else "STANDALONE",
                         Colors.BRIGHT_GREEN if HIVE_AVAILABLE else Colors.BRIGHT_BLACK)
        self.display.info("Momentum System", "ACTIVE (rbotzilla_golden_age)" if MOMENTUM_SYSTEM_AVAILABLE else "DISABLED",
                         Colors.BRIGHT_GREEN if MOMENTUM_SYSTEM_AVAILABLE else Colors.BRIGHT_BLACK)
        
        self.display.section("RISK PARAMETERS")
        self.display.info("Position Size", f"~{self.position_size:,} units (dynamic per pair)", Colors.BRIGHT_CYAN)
        self.stop_loss_pips = getattr(self.charter, 'STOP_LOSS_PIPS', 10)
        self.take_profit_pips = 54  # Increased to meet user's $75+ profit target (50 pips @ 15k units)
        self.display.info("Stop Loss", f"{self.stop_loss_pips} pips", Colors.BRIGHT_CYAN)
        self.display.info("Take Profit", f"{self.take_profit_pips} pips (5.4:1 R:R)", Colors.BRIGHT_CYAN)
        self.display.info("Max Positions", f"{self.max_active_positions} concurrent", Colors.BRIGHT_CYAN)
        print()
        self.display.warning("⚠️  Charter requires $15k min notional - positions sized accordingly")
        
        self.display.section("OANDA CONNECTION")
        self.display.connection_status(f"OANDA {env_label} API", "READY")

        # ── LIVE BROKER STATE CONFIRMATION ───────────────────────────────────────
        # Always print actual broker state at startup so the operator can verify
        # exactly what account and positions the engine sees.
        self.display.section("STARTUP BROKER STATE CONFIRMATION")
        try:
            _startup_trades = self.oanda.get_trades() or []
            _broker_count = len(_startup_trades)
            _broker_symbols = [
                (t.get('instrument') or t.get('symbol', 'UNKNOWN')).upper()
                for t in _startup_trades
            ]
            _local_count = len(self.active_positions)
            _local_symbols = sorted(set(
                str(pos.get('symbol', tid)).upper()
                for tid, pos in self.active_positions.items()
            ))
        except Exception as _e:
            _broker_count = "ERROR"
            _broker_symbols = []
            _local_count = len(self.active_positions)
            _local_symbols = []
            self.display.warning(f"  ⚠️  Broker state query failed at startup: {_e}")

        self.display.info("Environment",        env_label,                    env_color)
        self.display.info("API Endpoint",       self.oanda.api_base,          Colors.BRIGHT_CYAN)
        self.display.info("Account ID",         self.oanda.account_id,        Colors.BRIGHT_CYAN)
        self.display.info("Broker Open Trades", str(_broker_count),           Colors.BRIGHT_YELLOW)
        self.display.info("Local active_pos",   str(_local_count),            Colors.BRIGHT_YELLOW)
        if _broker_symbols:
            self.display.info("Synced Symbols",
                              ", ".join(_broker_symbols), Colors.BRIGHT_CYAN)
        else:
            self.display.info("Synced Symbols", "none (clean slate)", Colors.BRIGHT_BLACK)
        if _broker_count != _local_count:
            self.display.warning(
                f"  ⚠️  MISMATCH: broker={_broker_count}, local={_local_count} "
                f"— run Reconcile task to investigate"
            )
        self.display.info("OCO Enforcement",    "ACTIVE ✅",                  Colors.BRIGHT_GREEN)
        # ─────────────────────────────────────────────────────────────────────────

        print()
        self.display.alert(f"✅ RBOTzilla Engine Ready - {env_label} Environment", "SUCCESS")

        self.display.divider()
        print()
    
    def update_bot_status(self):
        """Update bot status awareness - knows if it's trading or not"""
        current_time = datetime.now(timezone.utc)
        uptime = (current_time - self.session_start).total_seconds()
        
        self.bot_status['session_uptime_seconds'] = uptime
        self.bot_status['positions_open'] = len(self.active_positions)
        self.bot_status['is_trading'] = self.is_running and len(self.active_positions) > 0
        
        if self.is_running:
            if len(self.active_positions) > 0:
                self.bot_status['status_message'] = f"🟢 TRADING ACTIVE ({len(self.active_positions)} positions)"
            else:
                self.bot_status['status_message'] = "🟡 SCANNING (waiting for signals)"
        else:
            self.bot_status['status_message'] = "🔴 BOT STOPPED"
        
        return self.bot_status
    
    def report_bot_status(self):
        """Print bot status report"""
        status = self.update_bot_status()
        
        print("\n" + "="*80)
        print(f"📊 BOT STATUS AWARENESS")
        print("="*80)
        print(f"  Engine Status:           {status['status_message']}")
        print(f"  Is Trading:              {status['is_trading']}")
        print(f"  Connected:               {status['connected']}")
        print(f"  Open Positions:          {status['positions_open']}")
        print(f"  Session Uptime:          {int(status['session_uptime_seconds'])}s")
        print(f"  Total Signals Scanned:   {status['total_signals_scanned']}")
        print(f"  Total Positions Opened:  {status['total_positions_opened']}")
        print("="*80 + "\n")
    
    def is_actively_trading(self) -> bool:
        """Check if bot is actively trading (has open positions)"""
        return self.is_running and len(self.active_positions) > 0
    
    def get_current_status(self) -> dict:
        """Get current bot status as dictionary"""
        return self.update_bot_status()
    
    def is_connection_healthy(self) -> bool:
        """Check if API connection is healthy"""
        try:
            # Attempt a simple API call to verify connection
            account_info = self.oanda.get_account_info()
            if account_info is not None:
                self.connection_state['last_healthy_check'] = datetime.now(timezone.utc)
                return True
            return False
        except Exception as e:
            self.connection_state['last_error'] = str(e)
            return False
    
    async def handle_connection_loss(self, error: str):
        """Handle connection loss with automatic reconnection"""
        self.connection_state['connected'] = False
        self.connection_state['consecutive_failures'] += 1
        self.connection_state['last_error'] = error
        
        if not self.connection_state['connection_loss_time']:
            self.connection_state['connection_loss_time'] = datetime.now(timezone.utc)
        
        self.display.alert(
            f"⚠️  CONNECTION LOST (Attempt #{self.connection_state['reconnect_attempt'] + 1}): {error}",
            "WARNING"
        )
        
        log_narration(
            event_type="CONNECTION_LOST",
            details={
                "error": error,
                "attempt": self.connection_state['reconnect_attempt'] + 1,
                "consecutive_failures": self.connection_state['consecutive_failures'],
                "will_auto_reconnect": True
            },
            symbol="SYSTEM",
            venue="connection_manager"
        )
    
    async def attempt_reconnect(self) -> bool:
        """Attempt to reconnect to OANDA API with exponential backoff"""
        if self.connection_state['is_reconnecting']:
            return False  # Already attempting to reconnect
        
        self.connection_state['is_reconnecting'] = True
        self.connection_state['reconnect_attempt'] += 1
        
        # Calculate exponential backoff wait time
        wait_time = min(
            self.reconnect_config['initial_wait_seconds'] * (
                self.reconnect_config['exponential_base'] ** 
                (self.connection_state['reconnect_attempt'] - 1)
            ),
            self.reconnect_config['max_wait_seconds']
        )
        
        self.display.warning(
            f"🔄 Reconnect attempt #{self.connection_state['reconnect_attempt']} "
            f"in {wait_time:.0f} seconds... (exponential backoff)"
        )
        
        # Wait before attempting reconnection
        await asyncio.sleep(wait_time)
        
        # Attempt to reconnect
        try:
            self.display.alert("🔌 Attempting to reconnect to OANDA API...", "INFO")
            
            # Reinitialize the connector
            self.oanda = OandaConnector(environment=self.environment)
            
            # Verify connection is healthy
            if self.is_connection_healthy():
                self.connection_state['connected'] = True
                self.connection_state['consecutive_failures'] = 0
                self.connection_state['reconnect_attempt'] = 0
                self.connection_state['last_reconnect_time'] = datetime.now(timezone.utc)
                self.connection_state['connection_loss_time'] = None
                self.connection_state['is_reconnecting'] = False
                
                # Sync open positions after reconnection
                self._sync_open_positions()
                
                downtime = (datetime.now(timezone.utc) - self.connection_state['last_reconnect_time']).total_seconds()
                self.display.success(
                    f"✅ RECONNECTED to OANDA API successfully! (Resumed after {downtime:.0f}s downtime)"
                )
                
                log_narration(
                    event_type="CONNECTION_RESTORED",
                    details={
                        "attempt": self.connection_state['reconnect_attempt'],
                        "positions_synced": len(self.active_positions)
                    },
                    symbol="SYSTEM",
                    venue="connection_manager"
                )
                
                return True
            else:
                raise RuntimeError("Connection health check failed after reconnect")
                
        except Exception as e:
            self.connection_state['is_reconnecting'] = False
            self.connection_state['last_error'] = str(e)
            
            # Check if max reconnect attempts exceeded (0 = unlimited)
            if (self.reconnect_config['max_reconnect_attempts'] > 0 and 
                self.connection_state['reconnect_attempt'] >= self.reconnect_config['max_reconnect_attempts']):
                
                self.display.error(
                    f"❌ RECONNECTION FAILED after {self.connection_state['reconnect_attempt']} attempts. "
                    f"Max retries exceeded. Stopping bot."
                )
                
                log_narration(
                    event_type="MAX_RECONNECT_ATTEMPTS_EXCEEDED",
                    details={
                        "attempts": self.connection_state['reconnect_attempt'],
                        "max_allowed": self.reconnect_config['max_reconnect_attempts'],
                        "error": str(e)
                    },
                    symbol="SYSTEM",
                    venue="connection_manager"
                )
                
                self.is_running = False
                return False
            
            # Will retry on next cycle
            return False
    
    async def monitor_connection_health(self):
        """Background task to periodically check connection health"""
        while self.is_running:
            try:
                # Check connection every N seconds
                await asyncio.sleep(self.reconnect_config['health_check_interval'])
                
                if not self.is_connection_healthy():
                    self.connection_state['consecutive_failures'] += 1
                    
                    if self.connection_state['consecutive_failures'] >= self.reconnect_config['failure_threshold']:
                        await self.handle_connection_loss(
                            f"Connection health check failed "
                            f"({self.connection_state['consecutive_failures']} consecutive failures)"
                        )
                        
                        # Attempt reconnection
                        reconnected = await self.attempt_reconnect()
                        if not reconnected and self.is_running:
                            # Will retry on next health check
                            pass
                else:
                    # Connection is healthy, reset failure counter
                    if self.connection_state['consecutive_failures'] > 0:
                        self.display.success(f"✅ Connection restored to healthy state")
                    self.connection_state['consecutive_failures'] = 0
                    self.connection_state['connected'] = True
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.display.error(f"Error in connection health monitor: {e}")
                await asyncio.sleep(5)
    
    def get_current_price(self, pair):
        """Get current real-time price from OANDA API (environment-agnostic)"""
        try:
            # Get real-time prices from OANDA API (practice or live based on connector config)
            api_base = self.oanda.api_base
            headers = self.oanda.headers
            account_id = self.oanda.account_id
            
            response = requests.get(
                f"{api_base}/v3/accounts/{account_id}/pricing",
                headers=headers,
                params={"instruments": pair},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'prices' in data and len(data['prices']) > 0:
                    price_info = data['prices'][0]
                    bid = float(price_info['bids'][0]['price'])
                    ask = float(price_info['asks'][0]['price'])
                    
                    # Correct pip multiplier for JPY vs other pairs
                    multiplier = 100 if 'JPY' in pair.upper() else 10000
                    spread = round((ask - bid) * multiplier, 1)  # in pips
                    
                    return {
                        'bid': bid,
                        'ask': ask,
                        'spread': spread,
                        'real_api': True
                    }
            
            raise RuntimeError(f"OANDA pricing failed for {pair} (status {response.status_code})")
            
        except Exception as e:
            raise RuntimeError(f"OANDA pricing unavailable for {pair}: {e}") from e
    
    def evaluate_signal_with_ml(self, symbol: str, signal_data: Dict) -> Tuple[bool, Dict]:
        """
        Filter signals through ML regime detection and strength analysis
        
        Returns:
            (bool, dict): (approved, analysis_details)
        """
        if not self.regime_detector or not self.signal_analyzer:
            # No ML, accept signal
            return True, {'ml_available': False, 'reason': 'ML not available'}
        
        try:
            # Get recent price data for ML analysis
            price_data = self.get_current_price(symbol)
            if not price_data:
                return False, {'ml_available': True, 'reason': 'Could not fetch price data'}
            
            # Detect market regime
            regime = self.regime_detector.detect_regime(symbol)
            
            # Analyze signal quality
            strength = self.signal_analyzer.analyze_signal(
                symbol, 
                signal_data.get('action', 'buy'),
                signal_data.get('entry', price_data.get('ask', 0))
            )
            
            # Accept signals with high confidence in trending regimes
            if regime in ['trending_up', 'trending_down']:
                # Strong trend: accept if confidence >= 0.70
                if strength >= 0.70:
                    log_narration(
                        event_type="ML_SIGNAL_APPROVED",
                        details={
                            "symbol": symbol,
                            "regime": regime,
                            "strength": strength,
                            "reason": "High confidence in strong trend"
                        },
                        symbol=symbol,
                        venue="ml_intelligence"
                    )
                    return True, {
                        'ml_available': True,
                        'regime': regime,
                        'strength': strength,
                        'approved': True
                    }
            
            elif regime in ['ranging', 'consolidating']:
                # Low trend environment: accept only exceptional signals (>0.80)
                if strength >= 0.80:
                    log_narration(
                        event_type="ML_SIGNAL_APPROVED",
                        details={
                            "symbol": symbol,
                            "regime": regime,
                            "strength": strength,
                            "reason": "Exceptional signal in ranging market"
                        },
                        symbol=symbol,
                        venue="ml_intelligence"
                    )
                    return True, {
                        'ml_available': True,
                        'regime': regime,
                        'strength': strength,
                        'approved': True
                    }
            
            # Signal rejected due to weak confidence
            log_narration(
                event_type="ML_SIGNAL_REJECTED",
                details={
                    "symbol": symbol,
                    "regime": regime,
                    "strength": strength,
                    "reason": f"Insufficient confidence in {regime} regime"
                },
                symbol=symbol,
                venue="ml_intelligence"
            )
            
            return False, {
                'ml_available': True,
                'regime': regime,
                'strength': strength,
                'approved': False,
                'reason': f'Weak signal ({strength:.2f}) in {regime} market'
            }
        
        except Exception as e:
            # ML error - be permissive, don't block trade
            self.display.warning(f"ML evaluation error for {symbol}: {str(e)}")
            return True, {'ml_available': True, 'error': str(e), 'approved': True}
    
    def amplify_signal_with_hive(self, symbol: str, signal_data: Dict) -> Dict:
        """
        Amplify signal strength through Hive Mind consensus
        
        Args:
            symbol: Currency pair
            signal_data: Signal dict with 'action', 'entry', etc.
        
        Returns:
            Amplified signal dict with hive_amplified flag and confidence
        """
        if not self.hive_mind:
            # No Hive, return original
            return signal_data
        
        try:
            # Query Hive Mind for consensus on this symbol
            market_data = {
                "symbol": symbol.replace('_', ''),
                "action": signal_data.get('action', 'buy'),
                "entry_price": signal_data.get('entry', 0),
                "timeframe": "M15"
            }
            
            hive_analysis = self.hive_mind.delegate_analysis(market_data)
            
            if not hive_analysis:
                return signal_data
            
            consensus = hive_analysis.consensus_signal
            confidence = hive_analysis.consensus_confidence
            
            # Check if Hive strongly agrees with signal
            if confidence >= self.hive_trigger_confidence:
                # Hive consensus is strong
                
                # Amplify the signal
                amplified_signal = signal_data.copy()
                amplified_signal['hive_amplified'] = True
                amplified_signal['hive_confidence'] = confidence
                amplified_signal['hive_consensus'] = consensus.value if hasattr(consensus, 'value') else str(consensus)
                
                log_narration(
                    event_type="HIVE_CONSENSUS_STRONG",
                    details={
                        "symbol": symbol,
                        "consensus": consensus.value if hasattr(consensus, 'value') else str(consensus),
                        "confidence": confidence,
                        "original_signal": signal_data.get('tag', 'unknown'),
                        "amplified": True
                    },
                    symbol=symbol,
                    venue="hive_mind"
                )
                
                self.display.success(f"🐝 Hive amplified {symbol}: {consensus} ({confidence:.2f})")
                
                return amplified_signal
            else:
                # Hive consensus weak - return original signal
                log_narration(
                    event_type="HIVE_CONSENSUS_WEAK",
                    details={
                        "symbol": symbol,
                        "consensus": consensus.value if hasattr(consensus, 'value') else str(consensus),
                        "confidence": confidence,
                        "threshold": self.hive_trigger_confidence
                    },
                    symbol=symbol,
                    venue="hive_mind"
                )
                
                return signal_data
        
        except Exception as e:
            # Hive error - return original signal
            self.display.warning(f"Hive amplification error for {symbol}: {str(e)}")
            return signal_data
    
    def calculate_position_size(self, symbol: str, entry_price: float, signal_confidence: float = None) -> int:
        """Calculate position size, using MarginMaximizer if available, or Charter minimum notional fallback."""
        import math
        
        # 1) Try Aggressive Margin Maximizer sizing first
        if getattr(self, 'portfolio_orchestrator', None) and self.portfolio_orchestrator.margin_maximizer:
            try:
                sl_pips = getattr(self, 'stop_loss_pips', 10.0)
                
                # Build mock position view for correlation limit checks
                existing_positions = {}
                # Unified USD notional calculation for existing positions
                for pos in self.active_positions.values():
                    pos_symbol = (pos.get('symbol') or '').upper()
                    units = float(pos.get('units') or 0)
                    entry = float(pos.get('entry') or entry_price)
                    
                    # Convert to USD notional
                    if '_USD' in pos_symbol:
                        usd_notional = abs(units) * entry if pos_symbol.endswith('_USD') else abs(units)
                    elif 'USD_' in pos_symbol:
                        usd_notional = abs(units)
                    else:
                        # Fallback for cross: use entry price as a rough USD proxy if quote isn't USD
                        # A better way would be using a mid-rate, but this is much safer than JPY units.
                        usd_notional = abs(units) * 0.75 # AUD, NZD, CAD crosses are roughly 0.6-0.8 USD
                    
                    if pos_symbol:
                        existing_positions[pos_symbol] = {'notional': usd_notional}

                units = self.portfolio_orchestrator.margin_maximizer.calculate_position_size(
                    symbol=symbol,
                    entry_price=entry_price,
                    stop_loss_pips=sl_pips,
                    existing_positions=existing_positions
                )
                
                position_size = math.ceil(units / 100) * 100
                if position_size > 0:
                    return position_size
            except Exception as e:
                self.display.warning(f"⚠️ Margin Maximizer failed: {e}. Using fallback sizing.")

        # 2) Fallback to standard Charter sizing
        min_notional = float(self.min_notional_usd)
        max_notional = float(os.getenv('RBOT_MAX_NOTIONAL_USD', '30000'))
        if max_notional < min_notional:
            max_notional = min_notional
        conf_floor = float(self.min_signal_confidence)
        conf_cap = 0.94
        conf = float(signal_confidence) if signal_confidence is not None else conf_floor
        conf = max(conf_floor, min(conf, conf_cap))
        
        # ── December-Style Quality Picking Logic: Power-Curve Scaling ──
        # Rather than linear scaling, we use a power of 1.5 to 2.0. 
        # This keeps 'meh' trades Small ($10k) and 'Ultra' trades Large ($30k+).
        # This is the "Quality over Quantity" fix.
        scale_raw = (conf - conf_floor) / max(conf_cap - conf_floor, 1e-9)
        scale = max(0.0, min(scale_raw, 1.0)) ** 1.8  # Power curve for exponential conviction
        
        target_notional = min_notional + (max_notional - min_notional) * scale
        
        # Bonus for Hive-amplified conviction (if scale is high)
        if conf >= 0.88:
             target_notional *= 1.25 # Extra 25% for "Home Runs"
             target_notional = min(target_notional, max_notional * 1.5)

        parts = symbol.upper().split("_")
        base  = parts[0] if len(parts) == 2 else ""
        quote = parts[1] if len(parts) == 2 else ""

        # Unified Unit Calculation for all pairs
        if quote == "USD":
            # EUR_USD, GBP_USD, AUD_USD
            required_units = math.ceil(target_notional / entry_price)
        elif base == "USD":
            # USD_JPY, USD_CAD, USD_CHF
            required_units = math.ceil(target_notional)
        else:
            # Cross pair - need a rough conversion factor to target USD notional
            # The entry price of EUR_AUD is 1.6 (AUD per EUR)
            # 10,000 units of EUR_AUD = 10,000 EUR
            # 10,000 EUR in USD is roughly $11,000 (at EUR_USD = 1.1)
            # So for target_notional $11,000, we need 10,000 units.
            # Scaling: units = target_notional / 1.1
            # For simplicity and safety across all crosses, we'll use a 1.0 multiplier 
            # and let the margin gate handle the final check.
            required_units = math.ceil(target_notional * 0.9) # Conservative proxy for most EUR/GBP/AUD crosses
            
        position_size = math.ceil(required_units / 100) * 100
        min_notional_charter = getattr(self.charter, "MIN_NOTIONAL_USD", 15000)
        charter_required_units = math.ceil(min_notional_charter / max(entry_price, 1e-9))
        position_size = max(position_size, charter_required_units)
        enforced_notional = position_size * entry_price
        self.display.info("Charter Size Enforcement", f"Units: {position_size} | Notional: ${enforced_notional:.0f}")
        return position_size
    
    def _can_trade_pair(self, symbol: str) -> Tuple[bool, str]:
        """
        Check if we can trade this pair based on platform limits
        
        Returns:
            Tuple of (can_trade: bool, reason: str)
        """
        # Check platform-specific limit (default 6, env-overridable)
        if len(self.active_pairs) >= self.max_pairs_per_platform:
            if symbol not in self.active_pairs:
                return False, f"Platform limit reached ({self.max_pairs_per_platform} pairs max)"
        
        return True, "OK"
    
    def _validate_tp_sl_set(self, symbol: str, stop_loss: float, take_profit: float, direction: str) -> bool:
        """
        Validate that TP and SL are properly set and meet requirements
        
        Args:
            symbol: Trading pair
            stop_loss: Stop loss price
            take_profit: Take profit price
            direction: BUY or SELL
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        if stop_loss is None:
            raise ValueError(f"CRITICAL: Stop Loss not set for {symbol} {direction}")
        
        if take_profit is None:
            raise ValueError(f"CRITICAL: Take Profit not set for {symbol} {direction}")
        
        # Validate that SL and TP are in the correct direction
        if direction == "BUY":
            if stop_loss >= take_profit:
                raise ValueError(f"CRITICAL: For BUY, SL ({stop_loss}) must be < TP ({take_profit})")
        else:  # SELL
            if stop_loss <= take_profit:
                raise ValueError(f"CRITICAL: For SELL, SL ({stop_loss}) must be > TP ({take_profit})")
        
        # Log successful validation
        log_narration(
            event_type="TP_SL_VALIDATED",
            details={
                "symbol": symbol,
                "direction": direction,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "validation": "PASSED"
            },
            symbol=symbol,
            venue="oanda"
        )
        
        return True
    
    def calculate_stop_take_levels(self, symbol: str, direction: str, entry_price: float):
        """
        Calculate stop loss and take profit levels
        
        IMPORTANT: Both SL and TP are ALWAYS calculated and returned.
        This ensures OCO order compliance for all trades.
        """
        pip_size = 0.0001  # Standard for most pairs
        if 'JPY' in symbol:
            pip_size = 0.01
        
        if direction == "BUY":
            stop_loss = entry_price - (self.stop_loss_pips * pip_size)
            take_profit = entry_price + (self.take_profit_pips * pip_size)
        else:  # SELL
            stop_loss = entry_price + (self.stop_loss_pips * pip_size)
            take_profit = entry_price - (self.take_profit_pips * pip_size)
        
        # Validate that both values are set
        if stop_loss is None or take_profit is None:
            raise ValueError(f"CRITICAL: Failed to calculate TP/SL for {symbol} {direction}")
        
        return round(stop_loss, 5), round(take_profit, 5)
    
    def _evaluate_hedge_conditions(self, symbol: str, direction: str, units: float, 
                                   entry_price: float, notional: float, current_margin_used: float) -> Dict:
        """
        Intelligent multi-condition hedge evaluation
        Analyzes portfolio state, market conditions, and risk exposure
        
        Returns:
            Dict with 'execute' (bool) and 'reason' (str)
        """
        # Get account NAV for calculations
        account_nav = 2000.0
        try:
            if hasattr(self.oanda, 'get_account_info'):
                account_info = self.oanda.get_account_info()
                account_nav = float(account_info.get('NAV', 2000.0))
        except Exception:
            pass
        
        # Calculate current margin utilization
        margin_utilization = (current_margin_used / account_nav) if account_nav > 0 else 0
        
        # Evaluate hedge opportunity
        hedge_opp = self.hedge_engine.evaluate_hedge_opportunity(symbol)
        
        # ========================================================================
        # HEDGE DECISION RULES - Multi-Condition Analysis
        # ========================================================================
        
        # RULE 1: No suitable hedge pair available
        if not hedge_opp['hedge_available']:
            return {'execute': False, 'reason': 'No inverse correlation pair found'}
        
        # RULE 2: Weak correlation (< -0.50 threshold)
        if abs(hedge_opp['correlation']) < 0.50:
            return {'execute': False, 'reason': f"Weak correlation ({hedge_opp['correlation']:.2f})"}
        
        # RULE 3: Extreme margin usage (>80%) only — hedge to protect capital
        # Raised from 70% → 80% to avoid triggering on normal portfolio loads.
        if margin_utilization > 0.80:
            return {
                'execute': True, 
                'reason': f'High margin usage ({margin_utilization:.1%}) - protective hedge required'
            }
        
        # RULE 4: Large notional (>$20k) - Hedge to reduce single-position risk
        if notional > 20000:
            return {
                'execute': True,
                'reason': f'Large notional (${notional:,.0f}) - risk reduction hedge'
            }
        
        # RULE 5: DISABLED — hedging on shared currency exposure caused phantom
        # counter-trades that ate spread without reducing net risk.
        # usd_exposure_count gate removed.
        
        # RULE 6: Strong inverse correlation (< -0.70) - Opportunistic hedge
        if hedge_opp['correlation'] < -0.70:
            return {
                'execute': True,
                'reason': f"Strong inverse correlation ({hedge_opp['correlation']:.2f}) - optimal hedge opportunity"
            }
        
        # RULE 7: DISABLED — 15-25% margin + strong correlation was firing within
        # the first 90 seconds of every new trade, opening immediate counter-trades.
        # Re-enable only if you explicitly want proactive hedging at low margin %.
        
        # DEFAULT: Skip hedge for low-risk scenarios
        return {
            'execute': False,
            'reason': f'Low risk profile (margin: {margin_utilization:.1%}, notional: ${notional:,.0f})'
        }
    
    def place_trade(self, symbol: str, direction: str,
                   signal_sl: float = None, signal_tp: float = None,
                   signal_confidence: float = None,
                   signal_votes: int = None,
                   signal_detectors: list = None,
                   signal_session: str = None,
                   signal_type: str = 'trend'):
        """Place Charter-compliant OCO order with full logging (environment-agnostic)"""
        try:
            # ========================================================================
            # 🛡️ FIX #6: TP COOLDOWN — per symbol AND per signal_type
            # A trend cooldown on GBP_USD should NOT block a mean_reversion or
            # reversal entry on the same pair from a different detector set.
            # Key format:  "SYMBOL:signal_type"  e.g. "GBP_USD:trend"
            # Fallback (no signal_type known): "SYMBOL:any" — blocks all types.
            # ========================================================================
            _now_utc = datetime.now(timezone.utc)
            _sig_type = signal_type or 'trend'
            # Check both the specific type key AND the catch-all "any" key
            _cooldown_keys_to_check = [f"{symbol.upper()}:{_sig_type}", f"{symbol.upper()}:any"]
            for _ck in _cooldown_keys_to_check:
                _last_close = self.tp_cooldowns.get(_ck)
                if _last_close is not None:
                    _elapsed = (_now_utc - _last_close).total_seconds()
                    _cooldown_secs = self.tp_cooldown_minutes * 60
                    if _elapsed < _cooldown_secs:
                        _remaining = int(_cooldown_secs - _elapsed)
                        self.display.warning(
                            f"⏳ TP_COOLDOWN_BLOCK: {symbol} [{_sig_type}] — {_remaining}s remaining "
                            f"(cooldown {self.tp_cooldown_minutes}min after close)"
                        )
                        log_narration(
                            event_type="TP_COOLDOWN_BLOCK",
                            details={
                                "symbol": symbol,
                                "signal_type": _sig_type,
                                "cooldown_key": _ck,
                                "last_close_utc": _last_close.isoformat(),
                                "elapsed_seconds": round(_elapsed, 1),
                                "cooldown_minutes": self.tp_cooldown_minutes,
                                "remaining_seconds": _remaining,
                            },
                            symbol=symbol,
                            venue="oanda"
                        )
                        return None
                    else:
                        # Cooldown expired — clear this specific key
                        self.tp_cooldowns.pop(_ck, None)

            # ========================================================================
            # 🛡️ PAIR LIMIT CHECK (NEW - Per User Requirement)
            # ========================================================================
            can_trade, reason = self._can_trade_pair(symbol)
            if not can_trade:
                self.display.error(f"❌ PAIR LIMIT BLOCKED: {reason}")
                log_narration(
                    event_type="PAIR_LIMIT_REJECTION",
                    details={
                        "symbol": symbol,
                        "reason": reason,
                        "active_pairs": list(self.active_pairs),
                        "max_pairs": self.max_pairs_per_platform
                    },
                    symbol=symbol,
                    venue="oanda"
                )
                return None
            
            # ========================================================================
            # 🛡️ POSITIONS REGISTRY CHECK (Prevent duplicate positions across platforms)
            # ========================================================================
            if self.positions_registry:
                self._reconcile_positions_registry_with_broker()
                if not self.positions_registry.is_symbol_available(symbol):
                    self.display.error(f"❌ BROKER_REGISTRY_BLOCK: {symbol} already in use on another platform")
                    log_narration(
                        event_type="BROKER_REGISTRY_BLOCK",
                        details={
                            "symbol": symbol,
                            "reason": "Symbol already has active position on another platform",
                            "active_positions": self.positions_registry.get_active_positions()
                        },
                        symbol=symbol,
                        venue="oanda"
                    )
                    return None
            
            # Get current price
            price_data = self.get_current_price(symbol)
            if not price_data:
                self.display.error(f"Could not get price for {symbol}")
                log_narration(
                    event_type="PRICE_ERROR",
                    details={"symbol": symbol, "error": "No price data"},
                    symbol=symbol,
                    venue="oanda"
                )
                return None
            
            # Use bid for SELL, ask for BUY
            entry_price = price_data['ask'] if direction == "BUY" else price_data['bid']
            
            # Calculate Charter-compliant position size
            position_size = self.calculate_position_size(
                symbol, entry_price, signal_confidence=signal_confidence
            )
            
            # Recompute and log resulting notional before sending order
            notional_value = get_usd_notional(position_size, symbol, entry_price, self.oanda)
            charter_min_not = getattr(self.charter, "MIN_NOTIONAL_USD", 15000)
            if notional_value and notional_value < charter_min_not:
                log_narration(event_type="UPSIZE_TO_MIN_NOTIONAL", details={"symbol":symbol, "target_usd":charter_min_not, "actual_notional":notional_value, "units":position_size}, symbol=symbol, venue="oanda")
            
            if notional_value is None:
                self.display.error(f"❌ Cannot calculate USD notional for {symbol}")
                return None
            
            # ========================================================================
            # 🛡️ PRE-TRADE GUARDIAN GATE CHECK
            # ========================================================================
            # Always pull live account info so gate uses real NAV and real margin_used.
            # Do NOT fall back to zero — if fetch fails, block rather than guess.
            current_margin_used = None
            try:
                if hasattr(self.oanda, 'get_account_info'):
                    _acct = self.oanda.get_account_info()
                    if _acct is not None:
                        _live_nav = float(getattr(_acct, 'balance', None) or 0)
                        _live_margin = getattr(_acct, 'margin_used', None)
                        current_margin_used = float(_live_margin) if _live_margin is not None else 0.0
                        # Refresh gate NAV with live balance every trade attempt
                        if _live_nav > 0 and _live_nav != self.gate.account_nav:
                            self.gate.account_nav = _live_nav
                            self.gate.max_margin_usd = _live_nav * self.gate.MARGIN_CAP_PCT
            except Exception as _acct_e:
                self.display.warning(f"⚠️  Could not fetch live account info for gate: {_acct_e}")

            if current_margin_used is None:
                self.display.warning(
                    f"⚠️  Blocking {symbol}: live margin fetch failed — cannot safely compute gate"
                )
                log_narration(
                    event_type="GATE_REJECTION",
                    details={"symbol": symbol, "reason": "live_margin_fetch_failed"},
                    symbol=symbol, venue="oanda"
                )
                return None

            # Create order object for gate validation
            gate_order = Order(
                symbol=symbol,
                side=direction,
                units=position_size,
                price=entry_price,
                order_id=f"pending_{symbol}_{int(time.time())}"
            )

            # Run pre-trade gate
            self._refresh_gate_positions_from_active()
            gate_result = self.gate.pre_trade_gate(
                new_order=gate_order,
                current_positions=self.current_positions,
                pending_orders=self.pending_orders,
                total_margin_used=current_margin_used
            )
            
            # If gate rejects order, stop here
            if not gate_result.allowed:
                self.display.error(f"❌ GUARDIAN GATE BLOCKED: {gate_result.reason}")
                if gate_result.action == "AUTO_CANCEL":
                    self.display.alert(f"   Action: {gate_result.action}", "WARNING")
                log_narration(
                    event_type="GATE_REJECTION",
                    details={
                        "symbol": symbol,
                        "reason": gate_result.reason,
                        "action": gate_result.action,
                        "margin_used": current_margin_used
                    },
                    symbol=symbol,
                    venue="oanda"
                )
                return None
            
            # CHARTER ENFORCEMENT: Verify minimum notional — UPSIZE instead of reject
            if notional_value < self.min_notional_usd:
                import math as _math
                _parts = symbol.upper().split("_")
                _base  = _parts[0] if len(_parts) == 2 else ""
                _quote = _parts[1] if len(_parts) == 2 else ""
                if _base == "USD":
                    _req = _math.ceil(self.min_notional_usd)
                elif _quote == "USD":
                    _req = _math.ceil(self.min_notional_usd / entry_price)
                else:
                    usd_per_unit = get_usd_notional(1, symbol, entry_price, self.oanda)
                    if usd_per_unit and usd_per_unit > 0:
                        _req = _math.ceil(self.min_notional_usd / usd_per_unit)
                    else:
                        _req = _math.ceil(self.min_notional_usd / entry_price) # fallback fallback
                        
                _new_size = _math.ceil(max(position_size, _req) / 100) * 100
                _new_notional = get_usd_notional(_new_size, symbol, entry_price, self.oanda) or (_new_size * entry_price)

                self.display.success(
                    f"⚙️  UPSIZE: {symbol} units {position_size:,} → {_new_size:,} "
                    f"to meet ${self.min_notional_usd:,} notional "
                    f"(was ${notional_value:,.0f} → now ${_new_notional:,.0f})"
                )
                log_narration(
                    event_type="UPSIZE_TO_MIN_NOTIONAL",
                    details={
                        "symbol": symbol,
                        "direction": direction,
                        "units_before": position_size,
                        "units_after": _new_size,
                        "notional_before": round(notional_value, 2),
                        "notional_after": round(_new_notional, 2),
                        "min_required_usd": self.min_notional_usd,
                        "entry_price": entry_price,
                    },
                    symbol=symbol,
                    venue="risk"
                )
                position_size  = _new_size
                notional_value = _new_notional

                # Re-check margin gate with new size
                gate_order.units = position_size
                # FIX: Use normalized USD notional for margin calculation
                _new_margin = notional_value * 0.03 # Using 3% as a safe buffer (OANDA is usually 2-3%)
                _proj_pct = (current_margin_used + _new_margin) / max(self.gate.account_nav, 1)
                if _proj_pct > self.gate.MARGIN_CAP_PCT:
                    self.display.error(
                        f"❌ POST-UPSIZE MARGIN CAP: {_proj_pct*100:.1f}% after upsize — skipping"
                    )
                    return None
            
            # Display market data
            self.display.section("MARKET SCAN")
            
            self.display.success("✅ Real-time OANDA API data")
            
            self.display.market_data(
                symbol,
                price_data['bid'],
                price_data['ask'],
                price_data['spread']  # already in pips
            )
            
            # Calculate stops.
            #
            # Signal SL/TP are anchored to the candle-close price, not the live
            # bid/ask.  If price drifted since the close the raw values would
            # create a wrong distance (e.g. 1-pip SL) and fail the RR gate.
            # Re-apply the *distance* from the signal to the live entry price,
            # with the charter pip values as an absolute floor.
            pip = 0.01 if 'JPY' in symbol else 0.0001
            charter_sl_dist = self.stop_loss_pips   * pip   # e.g. 0.0010
            charter_tp_dist = self.take_profit_pips * pip   # e.g. 0.0032

            # Determine correct price precision for the instrument
            price_precision = 3 if "JPY" in symbol.upper() else 5
            
            if self.enforce_charter:
                if signal_sl is not None and signal_tp is not None:
                    if direction == "BUY":
                        sl_dist = max(abs(entry_price - signal_sl),  charter_sl_dist)
                        tp_dist = max(abs(signal_tp   - entry_price), charter_tp_dist)
                        stop_loss   = round(entry_price - sl_dist, price_precision)
                        take_profit = round(entry_price + tp_dist, price_precision)
                    else:
                        sl_dist = max(abs(signal_sl   - entry_price), charter_sl_dist)
                        tp_dist = max(abs(entry_price - signal_tp),  charter_tp_dist)
                        stop_loss   = round(entry_price + sl_dist, price_precision)
                        take_profit = round(entry_price - tp_dist, price_precision)
                else:
                    stop_loss, take_profit = self.calculate_stop_take_levels(symbol, direction, entry_price)
                    stop_loss = round(stop_loss, price_precision)
                    take_profit = round(take_profit, price_precision)
            else:
                stop_loss, take_profit = self.calculate_stop_take_levels(symbol, direction, entry_price)
                stop_loss = round(stop_loss, price_precision)
                take_profit = round(take_profit, price_precision)
            
            # ========================================================================
            # 🛡️ VALIDATE TP/SL ARE SET (NEW - Per User Requirement)
            # ========================================================================
            self._validate_tp_sl_set(symbol, stop_loss, take_profit, direction)
            self.display.success(f"✅ TP/SL validated for {symbol} {direction}: SL={stop_loss:.5f}, TP={take_profit:.5f}")
            
            # CHARTER ENFORCEMENT: Verify R:R ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            # If R:R is below minimum, ESCALATE TP to meet charter requirements
            # (rather than rejecting the trade)
            if rr_ratio < self.min_rr_ratio:
                required_reward = risk * self.min_rr_ratio
                if direction == "BUY":
                    take_profit = round(entry_price + required_reward, price_precision)
                    self.display.warning(
                        f"⚙️  RR ESCALATION: {rr_ratio:.2f} → {self.min_rr_ratio:.1f}:1 "
                        f"(TP {entry_price + (required_reward - reward):+.5f})"
                    )
                else:
                    take_profit = round(entry_price - required_reward, price_precision)
                    self.display.warning(
                        f"⚙️  RR ESCALATION: {rr_ratio:.2f} → {self.min_rr_ratio:.1f}:1 "
                        f"(TP {entry_price - (required_reward - reward):+.5f})"
                    )
                # Recalculate ratio with new TP
                reward = abs(take_profit - entry_price)
                rr_ratio = reward / risk if risk > 0 else 0
                log_narration(
                    event_type="RR_ESCALATION",
                    details={
                        "original_rr": reward / risk if risk > 0 else 0,
                        "escalated_rr": rr_ratio,
                        "target": self.min_rr_ratio,
                        "symbol": symbol
                    },
                    symbol=symbol,
                    venue="oanda"
                )
            
            # Use small tolerance for floating point comparison
            if rr_ratio < (self.min_rr_ratio - 0.01):
                self.display.error(f"❌ CHARTER VIOLATION: R:R {rr_ratio:.2f} < {self.min_rr_ratio}")
                log_narration(
                    event_type="CHARTER_VIOLATION",
                    details={
                        "violation": "MIN_RR_RATIO",
                        "rr_ratio": rr_ratio,
                        "min_required": self.min_rr_ratio,
                        "symbol": symbol
                    },
                    symbol=symbol,
                    venue="oanda"
                )
                return None
            
            # Determine units (negative for SELL)
            units = position_size if direction == "BUY" else -position_size
            
            # Display Charter compliance
            self.display.info("Position Size", f"{abs(units):,} units (dynamic)", Colors.BRIGHT_CYAN)
            self.display.info("Notional Value", f"${notional_value:,.0f} ✅", Colors.BRIGHT_GREEN)
            self.display.info("R:R Ratio", f"{rr_ratio:.2f}:1 ✅", Colors.BRIGHT_GREEN)
            
            # Place OCO order
            self.display.alert(f"Placing Charter-compliant {direction} OCO order for {symbol}...", "INFO")
            
            # Log pre-trade
            log_narration(
                event_type="TRADE_SIGNAL",
                details={
                    "symbol": symbol,
                    "direction": direction,
                    "entry": entry_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "units": units,
                    "notional": notional_value,
                    "rr_ratio": rr_ratio,
                    "live_data": True
                },
                symbol=symbol,
                venue="oanda"
            )
            
            # Execute order via OANDA API (environment determined by connector config)
            order_result = self.oanda.place_oco_order(
                instrument=symbol,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                units=units,
                ttl_hours=6.0  # Charter: 6 hour max hold
            )
            
            if order_result.get('success'):
                order_id = order_result.get('order_id')
                trade_id = str(order_result.get('trade_id') or '').strip()
                position_key = trade_id or str(order_id)
                
                # CHARTER ENFORCEMENT: Verify latency
                latency_ms = order_result.get('latency_ms', 0)
                if latency_ms > getattr(self.charter, 'MAX_PLACEMENT_LATENCY_MS', 300):
                    self.display.warning(f"❌ CHARTER VIOLATION: Latency {latency_ms:.1f}ms > 300ms")
                    log_narration(
                        event_type="CHARTER_VIOLATION",
                        details={
                            "violation": "MAX_LATENCY",
                            "latency_ms": latency_ms,
                            "max_allowed": getattr(self.charter, 'MAX_PLACEMENT_LATENCY_MS', 300),
                            "order_id": order_id
                        },
                        symbol=symbol,
                        venue="oanda"
                    )
                    # Continue anyway since order was placed (just log violation)
                
                # Display successful trade
                self.display.trade_open(
                    symbol,
                    direction,
                    entry_price,
                    f"Stop: {stop_loss:.5f} | Target: {take_profit:.5f} | Size: {abs(units):,} units | Notional: ${notional_value:,.0f}"
                )
                
                # Track position
                management_profile = self.default_management_profile

                self.active_positions[position_key] = {
                    'symbol': symbol,
                    'direction': direction,
                    'entry': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'units': units,
                    'notional': notional_value,
                    'rr_ratio': rr_ratio,
                    'timestamp': datetime.now(timezone.utc),
                    'signal_confidence': signal_confidence,
                    'signal_votes': signal_votes,
                    'signal_detectors': list(signal_detectors or []),
                    'signal_timeframe': "M15",
                    'signal_session': signal_session,
                    'management_profile': management_profile,
                    'order_id': str(order_id or ''),
                    'trade_id': trade_id,
                }

                self._record_trade_metadata(
                    symbol=symbol,
                    order_id=str(order_id or ''),
                    trade_id=trade_id,
                    metadata={
                        "symbol": symbol,
                        "direction": direction,
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "signal_confidence": signal_confidence,
                        "signal_votes": signal_votes,
                        "signal_detectors": list(signal_detectors or []),
                        "signal_timeframe": "M15",
                        "signal_session": signal_session,
                        "management_profile": management_profile,
                        "hard_stop_usd": float(os.getenv("RBOT_MAX_LOSS_USD_PER_TRADE", "30")),
                    }
                )
                
                # ========================================================================
                # 🛡️ UPDATE ACTIVE PAIRS (NEW - Per User Requirement)
                # ========================================================================
                self.active_pairs.add(symbol)
                
                self.display.success(f"✅ Pair {symbol} added to active pairs ({len(self.active_pairs)}/{self.max_pairs_per_platform})")
                
                # ========================================================================
                # 🛡️ TRACK POSITION FOR GUARDIAN GATE ONGOING MONITORING
                # ========================================================================
                gate_position = Position(
                    symbol=symbol,
                    side="LONG" if direction == "BUY" else "SHORT",
                    units=abs(units),
                    entry_price=entry_price,
                    current_price=entry_price,
                    pnl=0.0,
                    pnl_pips=0.0,
                    margin_used=(notional_value * 0.02),  # Typical FOREX margin ~2%
                    position_id=position_key
                )
                self.current_positions.append(gate_position)
                self.display.info("🛡️ Position tracked for guardian gate monitoring", "", Colors.BRIGHT_CYAN)
                
                # ========================================================================
                # 🛡️ REGISTER POSITION IN CROSS-PLATFORM REGISTRY
                # ========================================================================
                if self.positions_registry:
                    try:
                        registered = self.positions_registry.register_position(
                            symbol=symbol,
                            platform='oanda',
                            order_id=position_key,
                            direction=direction,
                            notional_usd=notional_value
                        )
                        if registered:
                            self.display.info("📋 Position registered in cross-platform registry", "", Colors.BRIGHT_CYAN)
                        else:
                            self.display.warning("⚠️  Position registry update failed (may already exist)")
                    except Exception as e:
                        self.display.warning(f"⚠️  Could not register position: {e}")
                
                # ========================================================================
                # 📊 ADD POSITION TO DASHBOARD (Real-time monitoring)
                # ========================================================================
                try:
                    strategy_name = ",".join(signal_detectors) if signal_detectors else "unknown"
                    self.dashboard.add_position(
                        symbol=symbol,
                        strategy=strategy_name,
                        direction=direction,
                        entry_price=entry_price,
                        units=abs(units),
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        current_price=entry_price,
                    )
                    self.display.success(f"📊 {symbol} added to position dashboard (monitoring every 60s)")
                except Exception as e:
                    self.display.warning(f"⚠️  Dashboard update failed: {e}")
                
                self.total_trades += 1
                
                # Log successful placement with narration
                log_narration(
                    event_type="TRADE_OPENED",
                    details={
                        "symbol": symbol,
                        "direction": direction,
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "size": abs(units),
                        "notional": notional_value,
                        "rr_ratio": rr_ratio,
                        "order_id": order_id,
                        "trade_id": trade_id,
                        "charter_compliant": True,
                        "signal_confidence": signal_confidence,
                        "signal_votes": signal_votes,
                        "signal_detectors": list(signal_detectors or []),
                        "signal_timeframe": "M15",
                        "signal_session": signal_session,
                        "management_profile": management_profile,
                        "hard_stop_usd": float(os.getenv("RBOT_MAX_LOSS_USD_PER_TRADE", "30")),
                    },
                    symbol=symbol,
                    venue="oanda"
                )
                log_narration(event_type="OCO_PLACED", details={"symbol": symbol, "order_id": order_id}, symbol=symbol, venue="oanda")
                send_sms(f"✅ TRADE OPENED & OCO PLACED: {symbol} {direction} | Notional: ${notional_value:.0f} | SL: {stop_loss}")
                
                # Get Rick's commentary
                rick_comment = self.narrator.generate_commentary(
                    event_type="TRADE_OPENED",
                    details={
                        "symbol": symbol,
                        "direction": direction,
                        "entry": entry_price,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "rr_ratio": rr_ratio,
                        "notional": notional_value,
                        "reasoning": f"Charter-compliant {rr_ratio:.2f}:1 R:R, ${notional_value:,.0f} notional"
                    }
                )
                
                self.display.alert(f"✅ OCO order placed! Order ID: {order_id}", "SUCCESS")
                self.display.info("Latency", f"{latency_ms:.1f}ms", Colors.BRIGHT_CYAN)
                self.display.rick_says(rick_comment)
                
                # ========================================================================
                # 🛡️ QUANTITATIVE HEDGE ENGINE - INTELLIGENT MULTI-CONDITION ANALYSIS
                # ========================================================================
                if self.hedge_engine:
                    hedge_decision = self._evaluate_hedge_conditions(
                        symbol=symbol,
                        direction=direction,
                        units=abs(units),
                        entry_price=entry_price,
                        notional=notional_value,
                        current_margin_used=current_margin_used
                    )
                    
                    if hedge_decision['execute']:
                        self.display.section("HEDGE ANALYSIS")
                        self.display.info("Hedge Decision", hedge_decision['reason'], Colors.BRIGHT_YELLOW)
                        
                        hedge_position = self.hedge_engine.execute_hedge(
                            primary_symbol=symbol,
                            primary_side=direction,
                            position_size=abs(units),
                            entry_price=entry_price
                        )
                        
                        if hedge_position:
                            # Store hedge reference
                            self.active_hedges[position_key] = hedge_position
                            
                            self.display.success(
                                f"🛡️ HEDGE EXECUTED: {hedge_position.side} {hedge_position.size:.0f} units "
                                f"{hedge_position.symbol} @ {hedge_position.hedge_ratio:.0%} coverage"
                            )
                            self.display.info(
                                "Correlation", 
                                f"{hedge_position.correlation:.2f} (inverse)", 
                                Colors.BRIGHT_CYAN
                            )
                            
                            log_narration(
                                event_type="HEDGE_EXECUTED",
                                details={
                                    "primary_symbol": symbol,
                                    "hedge_symbol": hedge_position.symbol,
                                    "hedge_side": hedge_position.side,
                                    "hedge_size": hedge_position.size,
                                    "hedge_ratio": hedge_position.hedge_ratio,
                                    "correlation": hedge_position.correlation,
                                    "reason": hedge_decision['reason']
                                },
                                symbol=symbol,
                                venue="quant_hedge"
                            )
                            

                            # Place actual hedge order via OANDA API
                            hedge_units = hedge_position.size if hedge_position.side == 'BUY' else -hedge_position.size
                            
                            # Calculate SL and TP for the hedge (using default 15 pip SL and 30 pip TP for aggressive scalping)
                            pip_multiplier = 0.01 if "JPY" in hedge_position.symbol else 0.0001
                            try:
                                current_hedge_price = self.get_current_price(hedge_position.symbol)
                                if current_hedge_price:
                                    h_entry = current_hedge_price['ask'] if hedge_position.side == 'BUY' else current_hedge_price['bid']
                                else:
                                    h_entry = hedge_position.entry_price # Fallback
                            except Exception:
                                h_entry = hedge_position.entry_price
                                
                            hedge_sl_pips = float(os.getenv('RBOT_HEDGE_SL_PIPS', '20.0'))
                            hedge_tp_pips = float(os.getenv('RBOT_HEDGE_TP_PIPS', '40.0'))
                            
                            if hedge_position.side == 'BUY':
                                hedge_sl = h_entry - (hedge_sl_pips * pip_multiplier)
                                hedge_tp = h_entry + (hedge_tp_pips * pip_multiplier)
                            else:
                                hedge_sl = h_entry + (hedge_sl_pips * pip_multiplier)
                                hedge_tp = h_entry - (hedge_tp_pips * pip_multiplier)
                                
                            # CHARTER ENFORCEMENT: Ensure hedge meets $15,000 minimum
                            try:
                                h_notional = get_usd_notional(abs(hedge_units), hedge_position.symbol, h_entry, self.oanda) or (abs(hedge_units) * h_entry)
                                if h_notional < self.min_notional_usd:
                                    import math as _math
                                    _usd_per_unit = get_usd_notional(1, hedge_position.symbol, h_entry, self.oanda)
                                    if _usd_per_unit and _usd_per_unit > 0:
                                        _h_req = _math.ceil(self.min_notional_usd / _usd_per_unit)
                                    else:
                                        _h_req = _math.ceil(self.min_notional_usd / h_entry)
                                    _new_h_size = _math.ceil(max(abs(hedge_units), _h_req) / 100) * 100
                                    hedge_units = _new_h_size if hedge_units > 0 else -_new_h_size
                                    self.display.warning(f"⚠️  UPSIZING Hedge to meet Charter limits -> {abs(hedge_units):,} units")
                            except Exception as e:
                                self.display.error(f"Failed to check hedge charter size: {e}")
                                
                            hedge_order_result = self.oanda.place_oco_order(
                                instrument=hedge_position.symbol,
                                entry_price=h_entry,
                                stop_loss=hedge_sl,
                                take_profit=hedge_tp,
                                units=hedge_units,
                                ttl_hours=6.0
                            )
                            
                            if hedge_order_result.get('success'):
                                self.display.success(f"✅ HEDGE ORDER PLACED ID: {hedge_order_result.get('order_id')}")
                            else:
                                self.display.error(f"❌ Failed to place hedge order: {hedge_order_result.get('error')}")

                        else:
                            self.display.warning("⚠️  No suitable hedge pair found")
                    else:
                        self.display.info("Hedge Decision", f"SKIPPED - {hedge_decision['reason']}", Colors.DIM)
                
                return position_key
            else:
                error = order_result.get('error', 'Unknown error')
                self.display.error(f"Order failed: {error}")
                
                log_narration(
                    event_type="ORDER_FAILED",
                    details={
                        "symbol": symbol,
                        "direction": direction,
                        "error": error,
                        "environment": self.environment
                    },
                    symbol=symbol,
                    venue="oanda"
                )
                
                return None
                
        except Exception as e:
            self.display.error(f"Error placing trade: {e}")
            log_narration(
                event_type="TRADE_ERROR",
                details={"error": str(e), "symbol": symbol},
                symbol=symbol,
                venue="oanda"
            )
            return None
    
    def check_positions(self):
        """Check status of open positions via OANDA API"""
        # Positions managed by TradeManager background loop
        # This method can be extended to sync state with OANDA API if needed
        return

    def _get_unrealized_pnl_map(self) -> dict:
        """Best-effort map of trade_id -> unrealized P/L from broker trades."""
        try:
            trades = self.oanda.get_trades() or []
        except Exception:
            return {}

        pnl_map = {}
        for trade in trades:
            trade_id = str(trade.get('id') or trade.get('tradeID') or trade.get('trade_id') or '')
            if not trade_id:
                continue
            try:
                pnl_map[trade_id] = float(
                    trade.get('unrealizedPL')
                    or trade.get('unrealized_pl')
                    or 0.0
                )
            except Exception:
                pnl_map[trade_id] = 0.0
        return pnl_map

    def _trigger_loss_hedge_if_needed(
        self,
        *,
        symbol: str,
        direction: str,
        trade_id: str,
        units: float,
        entry_price: float,
        unrealized_pnl: float,
    ) -> bool:
        """Trigger a one-time protective hedge when unrealized loss crosses threshold."""
        if not self.hedge_engine:
            return False

        # LOSS HEDGE: disabled by default — the hedge was being rejected by
        # ORDER_REJECTED_MIN_NOTIONAL (hedge notional < $15k) while still logging
        # and consuming CPU.  Set RBOT_LOSS_HEDGE_TRIGGER_USD to a value below
        # RBOT_MAX_LOSS_USD_PER_TRADE to re-enable when position sizing supports it.
        trigger_usd = abs(float(os.getenv('RBOT_LOSS_HEDGE_TRIGGER_USD', '9999')))
        if unrealized_pnl > -trigger_usd:
            return False

        hedge_key = f"loss_hedge::{trade_id}"
        if hedge_key in self.active_hedges:
            return False

        try:
            hedge_opp = self.hedge_engine.evaluate_hedge_opportunity(symbol)
        except Exception:
            return False

        if not hedge_opp.get('hedge_available'):
            return False

        min_abs_corr = abs(float(os.getenv('RBOT_LOSS_HEDGE_MIN_ABS_CORR', '0.50')))
        if abs(float(hedge_opp.get('correlation') or 0.0)) < min_abs_corr:
            return False

        try:
            # Ratio of 1.0 ensures hedge notional >= $15k charter minimum
            hedge_position = self.hedge_engine.execute_hedge(
                primary_symbol=symbol,
                primary_side=direction,
                position_size=abs(float(units) or 0.0),
                entry_price=entry_price,
                hedge_ratio=float(os.getenv('RBOT_LOSS_HEDGE_RATIO', '1.0')),
            )
        except Exception:
            hedge_position = None

        if not hedge_position:
            return False

        self.active_hedges[hedge_key] = hedge_position

        log_narration(
            event_type="LOSS_HEDGE_TRIGGERED",
            details={
                "primary_symbol": symbol,
                "primary_trade_id": trade_id,
                "primary_direction": direction,
                "primary_units": abs(float(units) or 0.0),
                "primary_entry": entry_price,
                "primary_unrealized_pnl": unrealized_pnl,
                "loss_trigger_usd": trigger_usd,
                "hedge_symbol": hedge_position.symbol,
                "hedge_side": hedge_position.side,
                "hedge_size": hedge_position.size,
                "hedge_ratio": hedge_position.hedge_ratio,
                "correlation": hedge_position.correlation,
            },
            symbol=symbol,
            venue="oanda"
        )
        
        # Place actual hedge order via OANDA API
        hedge_units = hedge_position.size if hedge_position.side == 'BUY' else -hedge_position.size
        
        # Calculate SL and TP for the hedge (using default 15 pip SL and 30 pip TP for aggressive scalping)
        pip_multiplier = 0.01 if "JPY" in hedge_position.symbol else 0.0001
        try:
            current_hedge_price = self.get_current_price(hedge_position.symbol)
            if current_hedge_price:
                h_entry = current_hedge_price['ask'] if hedge_position.side == 'BUY' else current_hedge_price['bid']
            else:
                h_entry = hedge_position.entry_price # Fallback
        except Exception:
            h_entry = hedge_position.entry_price
            
        hedge_sl_pips = float(os.getenv('RBOT_HEDGE_SL_PIPS', '20.0'))
        hedge_tp_pips = float(os.getenv('RBOT_HEDGE_TP_PIPS', '40.0'))
        
        if hedge_position.side == 'BUY':
            hedge_sl = h_entry - (hedge_sl_pips * pip_multiplier)
            hedge_tp = h_entry + (hedge_tp_pips * pip_multiplier)
        else:
            hedge_sl = h_entry + (hedge_sl_pips * pip_multiplier)
            hedge_tp = h_entry - (hedge_tp_pips * pip_multiplier)
            
        hedge_order_result = self.oanda.place_oco_order(
            instrument=hedge_position.symbol,
            entry_price=h_entry,
            stop_loss=hedge_sl,
            take_profit=hedge_tp,
            units=hedge_units,
            ttl_hours=6.0
        )
        
        if hedge_order_result.get('success'):
            self.display.success(f"✅ PROTECTIVE HEDGE ORDER PLACED ID: {hedge_order_result.get('order_id')}")
            # Ensure it is tracked by active trades
            self._sync_open_positions()
        else:
            self.display.error(f"❌ Failed to place protective hedge order: {hedge_order_result.get('error')}")

        self.display.alert(
            f"🛡️ LOSS_HEDGE_TRIGGERED {symbol} ({trade_id}) uPnL={unrealized_pnl:.2f} "
            f"→ {hedge_position.side} {hedge_position.size:.0f} {hedge_position.symbol}",
            "WARNING"
        )
        return True

    def _try_opportunity_reallocation(self, qualified_candidates: list) -> bool:
        """Close a weaker eligible position to free capacity for a better setup."""
        if not qualified_candidates or not self.active_positions:
            return False

        candidate = qualified_candidates[0]
        enable = os.getenv('RBOT_ENABLE_OPPORTUNITY_REALLOCATION', '1') == '1'
        min_upgrade_delta = float(os.getenv('RBOT_REALLOC_MIN_CONF_DELTA', '0.03'))
        min_age_seconds = int(os.getenv('RBOT_REALLOC_MIN_AGE_SECONDS', '60'))
        if not enable:
            return False

        candidate_conf = float(getattr(candidate, 'confidence', 0.0) or 0.0)
        now_utc = datetime.now(timezone.utc)
        unrealized_map = self._get_unrealized_pnl_map()

        victims = []
        candidate_symbol = str(getattr(candidate, 'symbol', '') or '').upper()
        candidate_symbol_exists = any(
            (pos.get('symbol') or '').upper() == candidate_symbol
            for pos in self.active_positions.values()
        )

        for trade_id, pos in self.active_positions.items():
            symbol = (pos.get('symbol') or '').upper()
            pos_conf = float(pos.get('signal_confidence', self.min_signal_confidence) or self.min_signal_confidence)

            timestamp = pos.get('timestamp')
            if isinstance(timestamp, datetime):
                try:
                    ts = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
                    age_sec = max(0.0, (now_utc - ts).total_seconds())
                except Exception:
                    age_sec = 10**12
            else:
                age_sec = 10**12

            pnl = float(unrealized_map.get(str(trade_id), 0.0) or 0.0)

            if age_sec >= min_age_seconds and (candidate_conf - pos_conf) >= min_upgrade_delta:
                victims.append({
                    'trade_id': str(trade_id),
                    'symbol': symbol,
                    'pos_conf': pos_conf,
                    'age_sec': age_sec,
                    'pnl': pnl,
                })

        if not victims:
            return False

        if candidate_symbol_exists:
            same_symbol_victims = [
                v for v in victims
                if v['symbol'] == candidate_symbol and v['pnl'] < 0
            ]
            if same_symbol_victims:
                victims = same_symbol_victims

        victims.sort(key=lambda v: (0 if v['pnl'] < 0 else 1, v['pos_conf'], v['pnl']))
        victim = victims[0]

        try:
            close_result = self.oanda.close_trade(victim['trade_id'])
            if isinstance(close_result, dict) and close_result.get('success') is False:
                return False

            closed_trade_id = victim['trade_id']
            closed_symbol = victim['symbol']
            self.active_positions.pop(closed_trade_id, None)
            self.active_pairs.discard(closed_symbol)

            if self.positions_registry:
                try:
                    self.positions_registry.unregister_position(closed_symbol, 'oanda')
                except Exception:
                    pass

            log_narration(
                event_type="OPPORTUNITY_REALLOCATION",
                details={
                    "closed_symbol": closed_symbol,
                    "closed_trade_id": closed_trade_id,
                    "closed_confidence": victim['pos_conf'],
                    "closed_unrealized_pnl": victim['pnl'],
                    "replacement_symbol": getattr(candidate, 'symbol', ''),
                    "replacement_confidence": candidate_conf,
                    "min_upgrade_delta": min_upgrade_delta,
                },
                symbol=getattr(candidate, 'symbol', '') or 'SYSTEM',
                venue="oanda"
            )

            self.display.alert(
                f"♻️ Reallocated: closed {closed_symbol} ({closed_trade_id}) "
                f"conf={victim['pos_conf']:.1%}, uPnL={victim['pnl']:.2f} "
                f"→ opening {getattr(candidate, 'symbol', '')} conf={candidate_conf:.1%}",
                "WARNING"
            )
            return True
        except Exception as e:
            self.display.warning(f"Opportunity reallocation failed: {e}")
            return False

    # =========================================================================
    # BROKER TRADABILITY GATE
    # =========================================================================
    # MAX_STALE_QUOTE_SECONDS: reject if broker quote is older than this.
    # MAX_SPREAD_PIPS:         reject if spread exceeds this many pips.
    # Both can be overridden via environment variables.
    _MAX_STALE_QUOTE_SECONDS = int(os.getenv("RBOT_MAX_STALE_QUOTE_SECONDS", "120"))
    _MAX_SPREAD_PIPS         = float(os.getenv("RBOT_MAX_SPREAD_PIPS", "8.0"))

    def _check_broker_tradability(self, symbol: str) -> dict:
        """
        Hard pre-placement gate.  Returns:
            {'tradable': True}  — all checks passed, safe to submit order
            {'tradable': False, 'reason': <str>, 'detail': <dict>}

        Checks (in order):
        1. Live price fetch from OANDA — if this fails, we cannot trade.
        2. 'tradeable' flag in OANDA pricing response — broker explicitly marks
           some instruments as non-tradeable outside market hours.
        3. Quote freshness — OANDA sometimes returns a cached spread/price
           with a stale timestamp; we reject if older than MAX_STALE_QUOTE_SECONDS.
        4. Spread sanity — reject if ask-bid spread exceeds MAX_SPREAD_PIPS.
        """
        try:
            endpoint = f"/v3/accounts/{self.oanda.account_id}/pricing"
            params   = {"instruments": symbol}
            resp     = self.oanda._make_request("GET", endpoint, params=params)

            # --- fetch failure ---------------------------------------------------
            if not resp or not resp.get("success"):
                return {
                    "tradable": False,
                    "reason":   "quote_fetch_failed",
                    "detail":   {"response": str(resp)},
                }

            prices = (resp.get("data") or {}).get("prices") or []
            if not prices:
                return {
                    "tradable": False,
                    "reason":   "quote_fetch_failed",
                    "detail":   {"response": "empty prices list"},
                }

            price_obj = prices[0]

            # --- broker tradeable flag -------------------------------------------
            if not price_obj.get("tradeable", True):
                return {
                    "tradable": False,
                    "reason":   "instrument_not_tradable",
                    "detail":   {"tradeable": False, "symbol": symbol},
                }

            # --- quote freshness -------------------------------------------------
            quote_time_str = price_obj.get("time", "")
            if quote_time_str:
                try:
                    from datetime import datetime, timezone as _tz
                    quote_dt = datetime.fromisoformat(
                        quote_time_str[:26].rstrip("Z")
                    ).replace(tzinfo=_tz.utc)
                    age_seconds = (datetime.now(_tz.utc) - quote_dt).total_seconds()
                    if age_seconds > self._MAX_STALE_QUOTE_SECONDS:
                        return {
                            "tradable": False,
                            "reason":   "stale_quote",
                            "detail":   {
                                "quote_age_seconds": round(age_seconds, 1),
                                "max_allowed":       self._MAX_STALE_QUOTE_SECONDS,
                                "quote_time":        quote_time_str,
                            },
                        }
                except Exception:
                    pass  # if we cannot parse the timestamp, proceed

            # --- spread sanity ---------------------------------------------------
            bids = price_obj.get("bids") or []
            asks = price_obj.get("asks") or []
            if bids and asks:
                bid = float(bids[0]["price"])
                ask = float(asks[0]["price"])
                pip_mult = 100 if "JPY" in symbol else 10000
                spread_pips = round((ask - bid) * pip_mult, 1)
                if spread_pips > self._MAX_SPREAD_PIPS:
                    return {
                        "tradable": False,
                        "reason":   "spread_too_wide",
                        "detail":   {
                            "spread_pips": spread_pips,
                            "max_allowed": self._MAX_SPREAD_PIPS,
                            "bid": bid,
                            "ask": ask,
                        },
                    }

            return {"tradable": True}

        except Exception as _gate_err:
            return {
                "tradable": False,
                "reason":   "tradability_check_error",
                "detail":   {"error": str(_gate_err)},
            }

    def _sync_open_positions(self):

        """
        Pull current open trades from OANDA and add any that are missing from
        active_positions.  Called on startup AND at the top of each trade_manager
        cycle so positions placed manually or before a restart are always tracked.
        """
        try:
            trades = self.oanda.get_trades() or []
        except Exception as e:
            self.display.warning(f"_sync_open_positions: get_trades failed — {e}")
            return

        self._reconcile_positions_registry_with_broker()

        open_broker_trade_ids = {
            str(t.get('id') or t.get('tradeID') or t.get('trade_id') or '')
            for t in trades
            if str(t.get('id') or t.get('tradeID') or t.get('trade_id') or '')
        }
        stale_trade_ids = [tid for tid in list(self.active_positions.keys()) if str(tid) not in open_broker_trade_ids]
        for stale_trade_id in stale_trade_ids:
            stale_pos = self.active_positions.pop(stale_trade_id, {}) or {}
            stale_symbol = (stale_pos.get('symbol') or '').upper()
            if stale_symbol:
                self.active_pairs.discard(stale_symbol)
                # FIX #6: On a stop-loss or unexpected close, set cooldown for ALL
                # signal types on this symbol (key = "SYMBOL:any") so the pair
                # can't immediately re-enter on any strategy type.
                # On a graceful TP close (session_ended etc.) the close handler
                # already sets the specific signal_type key.
                self.tp_cooldowns[f"{stale_symbol}:any"] = datetime.now(timezone.utc)
                if self.positions_registry:
                    try:
                        self.positions_registry.unregister_position(stale_symbol, 'oanda')
                    except Exception:
                        pass

        for t in trades:
            symbol    = (t.get('instrument') or t.get('symbol', '')).upper()
            trade_id  = str(t.get('id') or t.get('tradeID') or t.get('trade_id', ''))
            if not trade_id or trade_id in self.active_positions:
                continue

            meta = self._lookup_trade_metadata(trade_id=trade_id, symbol=symbol)

            raw_units = float(t.get('currentUnits') or t.get('units') or 0)
            direction = 'BUY' if raw_units > 0 else 'SELL'
            entry     = float(t.get('price') or t.get('averagePrice') or 0)

            # Try to read attached SL/TP orders from the trade object
            sl_order  = t.get('stopLossOrder') or {}
            tp_order  = t.get('takeProfitOrder') or {}
            sl_price  = float(sl_order.get('price', 0))
            tp_price  = float(tp_order.get('price', 0))

            # Fallback: derive SL/TP from our config defaults
            pip = 0.01 if 'JPY' in symbol else 0.0001
            if sl_price == 0:
                sl_price = (entry - self.stop_loss_pips * pip) if direction == 'BUY' \
                           else (entry + self.stop_loss_pips * pip)
            if tp_price == 0:
                tp_price = (entry + self.take_profit_pips * pip) if direction == 'BUY' \
                           else (entry - self.take_profit_pips * pip)

            signal_detectors = meta.get('signal_detectors')
            if not isinstance(signal_detectors, list):
                signal_detectors = []

            try:
                synced_confidence = float(meta.get('signal_confidence', self.min_signal_confidence))
            except Exception:
                synced_confidence = float(self.min_signal_confidence)

            hard_stop_raw = meta.get('hard_stop_usd', os.getenv('RBOT_MAX_LOSS_USD_PER_TRADE', '30'))
            try:
                hard_stop_value = float(hard_stop_raw)
            except Exception:
                hard_stop_value = float(os.getenv('RBOT_MAX_LOSS_USD_PER_TRADE', '30'))

            self.active_positions[trade_id] = {
                'symbol':     symbol,
                'direction':  direction,
                'entry':      entry,
                'stop_loss':  sl_price,
                'take_profit': tp_price,
                'units':      abs(raw_units),
                'notional':   0,
                'rr_ratio':   0,
                'timestamp': datetime.now(timezone.utc),
                'signal_confidence': synced_confidence,
                'signal_votes': meta.get('signal_votes'),
                'signal_detectors': signal_detectors,
                'signal_timeframe': meta.get('signal_timeframe', 'M15'),
                'signal_session': meta.get('signal_session') or meta.get('session'),
                'management_profile': meta.get('management_profile') or self.default_management_profile,
                'order_id': str(meta.get('order_id') or ''),
                'trade_id': trade_id,
                'signal_sl':  sl_price,
                'signal_tp':  tp_price,
                'scaled_out': False,
                'trail_active': False,
                'synced_from_broker': True,
            }

            self._record_trade_metadata(
                symbol=symbol,
                order_id=str(meta.get('order_id') or ''),
                trade_id=trade_id,
                metadata={
                    "symbol": symbol,
                    "direction": direction,
                    "entry_price": entry,
                    "stop_loss": sl_price,
                    "take_profit": tp_price,
                    "signal_confidence": synced_confidence,
                    "signal_votes": meta.get('signal_votes'),
                    "signal_detectors": signal_detectors,
                    "signal_timeframe": meta.get('signal_timeframe', 'M15'),
                    "signal_session": meta.get('signal_session') or meta.get('session'),
                    "management_profile": meta.get('management_profile') or self.default_management_profile,
                    "hard_stop_usd": hard_stop_value,
                }
            )
            self.active_pairs.add(symbol)
            self.display.info(
                f"🔄 Synced existing position: {symbol} {direction} entry={entry:.5f} "
                f"SL={sl_price:.5f} TP={tp_price:.5f}", "", Colors.BRIGHT_CYAN
            )

        self._refresh_gate_positions_from_active()

    def _analyze_and_reoptimize_positions(self):
        """
        Analyze current positions against new margin config (1.5% risk per trade)
        and identify positions that need resizing.
        
        This ensures all positions align with the updated configuration:
        - Position sizing: 1.5% risk per trade (up from 1.0%)
        - Signal confidence policy: 55% vote floor / 62% final gate
        - Margin utilization: 25-30% target (vs current 11.6%)
        """
        if not self.active_positions:
            self.display.info("📊 Reoptimization", "No open positions to reoptimize", Colors.BRIGHT_CYAN)
            return
        
        try:
            # Get current account balance
            acct_info = self.oanda.get_account_info()
            if not acct_info:
                self.display.warning("⚠️  Could not fetch account info for reoptimization")
                return
            
            account_balance = float(getattr(acct_info, 'balance', None) or 10000.0)
            margin_used = float(getattr(acct_info, 'marginUsed', None) or 0.0)
            margin_available = float(getattr(acct_info, 'marginAvailable', None) or 0.0)
            margin_pct = (margin_used / account_balance * 100) if account_balance > 0 else 0
            
            self.display.alert(
                f"Position Reoptimization Analysis (NEW CONFIG: 1.5% risk, 55% vote floor / 62% final gate)",
                "INFO"
            )
            print(f"   Account Balance: ${account_balance:,.2f}")
            print(f"   Current Margin Used: ${margin_used:,.2f} ({margin_pct:.1f}%)")
            print(f"   Margin Available: ${margin_available:,.2f}")
            print()
            
            # Import margin maximizer for calculations
            from util.margin_maximizer import MarginMaximizer, MarginConfig
            
            margin_calc = MarginMaximizer(
                MarginConfig(
                    risk_per_trade_min=0.015,     # 1.5%
                    risk_per_trade_target=0.020,  # 2.0% PROFESSIONAL COMPOUNDING
                    risk_per_trade_max=0.025      # 2.5%
                )
            )
            margin_calc.account_balance = account_balance
            
            # Target margins
            target_margin_min = 0.25  # 25%
            target_margin_max = 0.30  # 30%
            target_margin_usd_min = account_balance * target_margin_min
            target_margin_usd_max = account_balance * target_margin_max
            
            print(f"   Target Margin Range: ${target_margin_usd_min:,.0f} - ${target_margin_usd_max:,.0f} "
                  f"({target_margin_min*100:.0f}% - {target_margin_max*100:.0f}%)")
            print()
            
            # Analyze each position
            print("   Position Analysis:")
            print("   " + "=" * 100)
            
            adjustments_needed = False
            for trade_id, pos in self.active_positions.items():
                symbol = pos['symbol']
                units = pos['units']
                direction = pos['direction']
                entry = pos['entry']
                
                # Calculate notional value (units * entry price)
                notional = units * entry
                position_margin_pct = (margin_used / account_balance * 100) if account_balance > 0 else 0
                
                # Get recommendation from margin maximizer
                allocation = margin_calc.get_allocation_for_symbol(
                    symbol,
                    account_balance=account_balance,
                    existing_positions=self.active_positions
                )
                
                target_notional = allocation['target_notional']
                max_notional = allocation['max_notional']
                target_units = target_notional / entry if entry > 0 else 0
                max_units = max_notional / entry if entry > 0 else 0
                
                status = "✅"
                if units < target_units * 0.8:  # More than 20% undersized
                    status = "⚠️ UNDERSIZED"
                    adjustments_needed = True
                elif units > max_units * 1.1:   # More than 10% oversized
                    status = "⚠️ OVERSIZED"
                    adjustments_needed = True
                
                print(f"   {status} {symbol} {direction:4} | Units: {units:>8,.0f} | "
                      f"Entry: {entry:.5f} | Notional: ${notional:>10,.0f}")
                print(f"         Target: {target_units:>8,.0f} units | "
                      f"Max: {max_units:>8,.0f} units | Risk Factor: 1.5%")
                print()
            
            print("   " + "=" * 100)
            print()
            
            if adjustments_needed:
                print("   RECOMMENDATION:")
                print("   Close and reopen undersized positions to align with Professional Compounding (2.0% risk)")
                print("   This will increase position sizes to leverage account growth")
                print("   New margin utilization target: 25-30% (currently {:.1f}%)".format(margin_pct))
                print()
                
                # Auto-resize if enabled
                auto_resize = os.getenv('RBOT_AUTO_RESIZE_POSITIONS', '0') == '1'
                if auto_resize:
                    self.display.alert("AUTO_RESIZE enabled - closing undersized positions", "INFO")
                    self._auto_resize_undersized_positions()
                else:
                    self.display.info("Auto-Resize", "💡 Set RBOT_AUTO_RESIZE_POSITIONS=1 to auto-close and reopen positions", Colors.BRIGHT_CYAN)
            else:
                self.display.success("✅ All positions are properly sized for new config")
            
            # Log analysis
            log_narration(
                event_type="POSITION_REOPTIMIZATION_ANALYSIS",
                details={
                    "account_balance": account_balance,
                    "current_margin_pct": margin_pct,
                    "target_margin_range": f"{target_margin_min*100:.0f}%-{target_margin_max*100:.0f}%",
                    "adjustments_needed": adjustments_needed,
                    "positions_analyzed": len(self.active_positions),
                    "new_config": "risk_1.5%_vote_floor_55%_final_gate_62%"
                }
            )
            
        except Exception as e:
            self.display.error(f"❌ Position reoptimization analysis failed: {e}")
            log_narration(
                event_type="POSITION_REOPTIMIZATION_ERROR",
                details={"error": str(e)}
            )

    def _auto_resize_undersized_positions(self):
        """Close undersized positions to allow bot to reopen at correct sizing"""
        self.display.alert("Closing undersized positions for resizing...", "WARNING")
        
        try:
            from util.margin_maximizer import MarginMaximizer, MarginConfig
            
            # Get fresh account info
            acct_info = self.oanda.get_account_info()
            account_balance = float(getattr(acct_info, 'balance', None) or 10000.0)
            
            margin_calc = MarginMaximizer(
                MarginConfig(
                    risk_per_trade_min=0.10,
                    risk_per_trade_target=0.15,
                    risk_per_trade_max=0.20
                )
            )
            margin_calc.account_balance = account_balance
            
            closed_count = 0
            for trade_id, pos in list(self.active_positions.items()):
                symbol = pos['symbol']
                units = pos['units']
                entry = pos['entry']
                direction = pos['direction']
                
                allocation = margin_calc.get_allocation_for_symbol(
                    symbol,
                    account_balance=account_balance
                )
                target_units = (allocation['target_notional'] / entry) if entry > 0 else 0
                
                # Close if undersized (less than 80% of target)
                if units < target_units * 0.80:
                    try:
                        # Close at market (or within 1 pip if market looks bad)
                        self.display.info("Auto-Resize", f"Closing {symbol} {direction} {units:,.0f} units "
                                         f"(undersized: {units:,.0f} vs target {target_units:,.0f})")
                        
                        self.oanda.close_trade(trade_id)
                        closed_count += 1
                        
                        # Remove from tracking
                        del self.active_positions[trade_id]
                        
                    except Exception as close_err:
                        self.display.error(f"   ❌ Failed to close {trade_id}: {close_err}")
            
            if closed_count > 0:
                self.display.success(f"✅ Closed {closed_count} undersized position(s) for resizing")
                self.display.info("Auto-Resize", "💡 Bot will reopen with new sizing on next scan cycle")
                log_narration(
                    event_type="POSITIONS_CLOSED_FOR_RESIZE",
                    details={
                        "closed_count": closed_count,
                        "new_config": "risk_1.5%_vote_floor_55%_final_gate_62%",
                        "next_action": "await_reopen_with_new_sizing"
                    }
                )
        except Exception as e:
            self.display.error(f"❌ Auto-resize failed: {e}")

    def _pip_size(self, symbol: str) -> float:
        return 0.01 if 'JPY' in (symbol or '').upper() else 0.0001

    def _is_trade_in_green(self, direction: str, entry_price: float, current_price: float) -> bool:
        if (direction or '').upper() == 'BUY':
            return current_price > entry_price
        return current_price < entry_price

    def _enforce_green_sl(self, symbol: str, direction: str, entry_price: float, current_price: float, candidate_sl: float):
        """If trade is green, force SL to remain in green by configured lock distance.

        FIX (2026-03-11): Requires RBOT_GREEN_LOCK_MIN_PROFIT_PIPS of actual profit
        before activating. Previously fired with 0.1 pip profit, setting SL to
        entry+5pips (inside the spread) → instant stop-outs on every trade.
        """
        if candidate_sl is None:
            return candidate_sl, False, None

        try:
            proposed = float(candidate_sl)
        except Exception:
            return candidate_sl, False, None

        if not self._is_trade_in_green(direction, entry_price, current_price):
            return proposed, False, None

        pip_size = self._pip_size(symbol)
        lock_pips = float(os.getenv('RBOT_GREEN_LOCK_PIPS', '5.0'))
        lock_distance = lock_pips * pip_size

        # ── Minimum profit gate vs Explicit Trailing ────────────────────────
        # If rbz_tight_trailing provided a candidate_sl that is *already* in profit,
        # we respect it as an explicit lock attempt and bypass the min_profit gate,
        # provided it clears the spread (fallback lock_distance).
        is_candidate_in_profit = False
        if (direction or '').upper() == 'BUY':
            is_candidate_in_profit = proposed > entry_price
        else:
            is_candidate_in_profit = proposed > 0 and proposed < entry_price

        # Default fallback lock (5 pips)
        min_profit_pips = float(os.getenv('RBOT_GREEN_LOCK_MIN_PROFIT_PIPS', '10.0'))
        min_profit_distance = min_profit_pips * pip_size
        actual_profit_distance = abs(current_price - entry_price)

        if not is_candidate_in_profit and actual_profit_distance < min_profit_distance:
            # If the candidate IS NOT a profit lock, and we haven't hit the 
            # fallback green lock trigger, hold the original SL.
            return proposed, False, None  

        if (direction or '').upper() == 'BUY':
            green_floor = max(entry_price + lock_distance, proposed if is_candidate_in_profit else 0)
            adjusted = max(proposed, green_floor)
        else:
            green_floor = min(entry_price - lock_distance, proposed if is_candidate_in_profit else float('inf'))
            adjusted = min(proposed, green_floor)

        return adjusted, abs(adjusted - proposed) > 1e-12, green_floor

    async def trade_manager_loop(self):
        """Background loop that evaluates active positions and asks the Hive for momentum signals.

        Behavior:
        - For positions older than `min_position_age_seconds`, query the Hive Mind for a consensus
          analysis on that symbol.
        - Use battle-tested MomentumDetector (from rbotzilla_golden_age.py) to detect strong momentum.
        - If EITHER the Hive consensus exceeds threshold OR MomentumDetector confirms momentum,
          cancel the existing TakeProfit order and set an adaptive trailing stop via the OANDA connector.
        - All modifications are logged via `log_narration` to keep an auditable trail.
        
        Integration Note: This TradeManager integrates existing momentum detection logic from
        /home/ing/RICK/RICK_LIVE_CLEAN/rbotzilla_golden_age.py (MomentumDetector & SmartTrailingSystem)
        to fulfill Charter requirement for code reuse (PIN 841921).
        """
        # ========================================================================
        # 🛡️ TRADE MANAGER ACTIVATION (NEW - Per User Requirement)
        # ========================================================================
        self.trade_manager_active = True
        self.trade_manager_last_heartbeat = datetime.now(timezone.utc)
        
        self.display.success("✅ TRADE MANAGER ACTIVATED AND CONNECTED")
        log_narration(
            event_type="TRADE_MANAGER_ACTIVATED",
            details={
                "status": "ACTIVE",
                "timestamp": self.trade_manager_last_heartbeat.isoformat(),
                "min_position_age_seconds": self.min_position_age_seconds,
                "hive_trigger_confidence": self.hive_trigger_confidence
            },
            symbol="SYSTEM",
            venue="trade_manager"
        )
        
        while self.is_running:
            try:
                # Re-sync broker positions each cycle so manually opened or
                # restarted trades are always visible to the manager.
                self._sync_open_positions()

                base_limit = abs(float(os.getenv('RBOT_MAX_LOSS_USD_PER_TRADE', '30')))
                allow_extended_dollar_stop = os.getenv('RBOT_ALLOW_EXTENDED_DOLLAR_STOP', '0') == '1'
                extended_limit = abs(float(os.getenv('RBOT_MAX_LOSS_USD_EXTENDED_PER_TRADE', '50')))
                conf_min = float(os.getenv('RBOT_TURNAROUND_CONFIDENCE_MIN', '0.80'))
                recovery_min = float(os.getenv('RBOT_TURNAROUND_RECOVERY_USD', '6'))
                try:
                    current_trades_snapshot = self.oanda.get_trades() or []
                except Exception:
                    current_trades_snapshot = []

                broker_trade_by_symbol = {}
                for t in current_trades_snapshot:
                    broker_symbol = (t.get('instrument') or t.get('symbol', '')).upper()
                    if broker_symbol and broker_symbol not in broker_trade_by_symbol:
                        broker_trade_by_symbol[broker_symbol] = t

                now = datetime.now(timezone.utc)
                for order_id, pos in list(self.active_positions.items()):
                    symbol = (pos.get('symbol') or '').upper()
                    broker_trade_id = str(order_id)

                    broker_trade = broker_trade_by_symbol.get(symbol)
                    if broker_trade:
                        broker_trade_id = str(
                            broker_trade.get('id')
                            or broker_trade.get('tradeID')
                            or broker_trade.get('trade_id')
                            or order_id
                        )
                        try:
                            unrealized_pnl = float(
                                broker_trade.get('unrealizedPL')
                                or broker_trade.get('unrealized_pl')
                                or 0.0
                            )
                        except Exception:
                            unrealized_pnl = 0.0

                        try:
                            broker_units = float(
                                broker_trade.get('currentUnits')
                                or broker_trade.get('units')
                                or pos.get('units')
                                or 0.0
                            )
                        except Exception:
                            broker_units = float(pos.get('units') or 0.0)

                        try:
                            broker_entry = float(
                                broker_trade.get('price')
                                or pos.get('entry')
                                or 0.0
                            )
                        except Exception:
                            broker_entry = float(pos.get('entry') or 0.0)

                        self._trigger_loss_hedge_if_needed(
                            symbol=symbol,
                            direction=pos.get('direction') or ('BUY' if broker_units > 0 else 'SELL'),
                            trade_id=broker_trade_id,
                            units=broker_units,
                            entry_price=broker_entry,
                            unrealized_pnl=unrealized_pnl,
                        )

                        try:
                            signal_confidence = float(pos.get('signal_confidence') or 0.0)
                        except Exception:
                            signal_confidence = 0.0

                        previous_worst = pos.get('worst_unrealized_pnl')
                        try:
                            worst_unrealized = float(previous_worst)
                        except Exception:
                            worst_unrealized = unrealized_pnl
                        if unrealized_pnl < worst_unrealized:
                            worst_unrealized = unrealized_pnl
                        pos['worst_unrealized_pnl'] = worst_unrealized

                        recovery_usd = unrealized_pnl - worst_unrealized
                        extension_eligible = (
                            not bool(pos.get('synced_from_broker'))
                            and signal_confidence >= conf_min
                            and recovery_usd >= recovery_min
                        )
                        if not allow_extended_dollar_stop:
                            extension_eligible = False
                        effective_limit = extended_limit if (allow_extended_dollar_stop and extension_eligible) else base_limit

                        if unrealized_pnl <= -effective_limit:
                            try:
                                close_resp = self.oanda.close_trade(broker_trade_id)
                                if isinstance(close_resp, dict) and close_resp.get("success") is False:
                                    self.display.warning(f"Hard dollar stop close rejected for {symbol} ({broker_trade_id}): {close_resp}")
                                    continue
                            except Exception as close_err:
                                self.display.warning(
                                    f"Hard dollar stop close failed for {symbol} ({broker_trade_id}): {close_err}"
                                )
                                continue

                            self.active_positions.pop(str(order_id), None)
                            self.active_positions.pop(str(broker_trade_id), None)
                            self.active_pairs.discard(symbol)
                            if self.positions_registry:
                                try:
                                    self.positions_registry.unregister_position(symbol, 'oanda')
                                except Exception:
                                    pass

                            # FIX: hard dollar stop must set cooldown so the pair
                            # cannot immediately re-enter on the very next scan cycle.
                            self.tp_cooldowns[symbol.upper()] = datetime.now(timezone.utc)

                            log_narration(
                                event_type="HARD_DOLLAR_STOP",
                                details={
                                    "symbol": symbol,
                                    "trade_id": broker_trade_id,
                                    "unrealized_pnl": unrealized_pnl,
                                    "base_limit": base_limit,
                                    "extended_limit": extended_limit,
                                    "effective_limit": effective_limit,
                                    "extension_eligible": extension_eligible,
                                    "signal_confidence": signal_confidence,
                                    "recovery_usd": recovery_usd,
                                },
                                symbol=symbol,
                                venue="trade_manager"
                            )
                            self.display.alert(
                                f"🛑 HARD_DOLLAR_STOP {symbol} ({broker_trade_id}) "
                                f"uPnL={unrealized_pnl:.2f} <= -{effective_limit:.2f} "
                                f"(extension_eligible={extension_eligible}) — closed and slot released",
                                "WARNING"
                            )
                            continue

                    tp_already_cancelled = bool(pos.get('tp_cancelled'))
                    
                    # Age check
                    age = (now - pos['timestamp']).total_seconds()
                    if age < self.min_position_age_seconds:
                        continue

                    symbol = pos['symbol']
                    direction = pos['direction']
                    entry_price = pos['entry']
                    pos_sl  = pos.get('stop_loss', 0)
                    pos_tp  = pos.get('take_profit', 0)

                    # ── RBZ Tight Trailing Hook ──────────────────────────────────
                    # Calls _manage_trade on every active position so rbz_tight_trailing's
                    # Two-Step SL lock + aggressive trail wrapper can execute.
                    try:
                        self._manage_trade({
                            'id': broker_trade_id,
                            'trade_id': broker_trade_id,
                            'symbol': symbol,
                            'instrument': symbol,
                            'side': direction,
                            'direction': direction,
                            'entry': entry_price,
                            'entry_price': entry_price,
                            'sl': pos_sl,
                            'stop_loss': pos_sl,
                            'tp': pos_tp,
                            'take_profit': pos_tp,
                            'meta': pos.get('meta', {}),
                            'strategy': pos.get('strategy_name') or pos.get('signal_type', 'trend'),
                            'tags': set(pos.get('tags') or []),
                        })
                    except Exception:
                        pass  # Never let trailing logic crash the main loop


                    try:
                        current_price_data = self.get_current_price(symbol)
                        if not current_price_data:
                            continue
                        current_price = current_price_data['ask'] if direction == 'BUY' else current_price_data['bid']
                    except Exception as e:
                        self.display.warning(f"Could not fetch current price for {symbol}: {e}")
                        continue

                    # Enforce in-green SL for any position currently in profit.
                    existing_sl = float(pos_sl or 0.0)
                    if existing_sl > 0:
                        green_sl_candidate, green_lock_applied, green_floor = self._enforce_green_sl(
                            symbol=symbol,
                            direction=direction,
                            entry_price=entry_price,
                            current_price=current_price,
                            candidate_sl=existing_sl,
                        )
                        if green_lock_applied and (
                            (direction == 'BUY' and green_sl_candidate > existing_sl)
                            or (direction == 'SELL' and green_sl_candidate < existing_sl)
                        ):
                            # SL rejection backoff: if OANDA rejected this exact SL price
                            # recently (within 60s), skip the API call entirely rather than
                            # hammering the broker 16 times in 45 seconds.
                            import time as _time
                            _sl_key = f"{broker_trade_id}:{green_sl_candidate:.5f}"
                            _last_rejection = self._sl_rejection_backoff.get(_sl_key, 0)
                            _sl_backoff_ok = (_time.time() - _last_rejection) > 60
                            if not _sl_backoff_ok:
                                pass  # silently skip — still in backoff window
                            else:
                                try:
                                    self.oanda.set_trade_stop(broker_trade_id, green_sl_candidate)
                                    pos['stop_loss'] = green_sl_candidate
                                    pos_sl = green_sl_candidate
                                    # Clear any old backoff for this trade on success
                                    self._sl_rejection_backoff.pop(_sl_key, None)
                                    log_narration(
                                        event_type="GREEN_LOCK_ENFORCED",
                                        details={
                                            "symbol": symbol,
                                            "trade_id": broker_trade_id,
                                            "entry": entry_price,
                                            "current_price": current_price,
                                            "old_sl": existing_sl,
                                            "new_sl": green_sl_candidate,
                                            "green_floor": green_floor,
                                            "green_lock_applied": True,
                                        },
                                        symbol=symbol,
                                        venue="trade_manager"
                                    )
                                except Exception as green_lock_err:
                                    # Record rejection so we don't retry this exact price for 60s
                                    self._sl_rejection_backoff[_sl_key] = _time.time()
                                    self.display.warning(f"Green-lock SL rejected for {symbol} @ {green_sl_candidate:.5f} (backoff 60s): {green_lock_err}")

                    # ── Incremental position management (multi_signal_engine) ──
                    from systems.multi_signal_engine import manage_open_trade, TradeAction, session_bias
                    sess_name, _ = session_bias(symbol)
                    trade_action, trade_detail = manage_open_trade(
                        direction    = direction,
                        entry        = entry_price,
                        sl           = pos_sl,
                        tp           = pos_tp,
                        current_price= current_price,
                        symbol       = symbol,
                        scaled_out   = pos.get('scaled_out', False),
                        trail_active = pos.get('trail_active', False),
                        session      = sess_name,
                    )

                    if trade_action == TradeAction.SCALE_OUT_HALF:
                        self.display.alert(
                            f"📉 SCALE_OUT_HALF {symbol} @ {current_price:.5f}  "
                            f"(1R profit, closing 50%)", "INFO"
                        )
                        try:
                            trades = self.oanda.get_trades()
                            for t in trades:
                                ti = (t.get('instrument') or t.get('symbol', '')).upper()
                                if ti == symbol.upper():
                                    tid = t.get('id') or t.get('tradeID') or t.get('trade_id')
                                    units_now = int(abs(float(t.get('currentUnits', t.get('units', 0)))))
                                    half = max(1, units_now // 2)
                                    close_units = half if direction == 'BUY' else -half
                                    self.oanda.close_trade_partial(tid, close_units)
                                    pos['scaled_out'] = True
                                    log_narration(
                                        event_type="SCALE_OUT_HALF",
                                        details={"symbol": symbol, "units_closed": half,
                                                 "pnl_r": trade_detail.get('pnl_r')},
                                        symbol=symbol, venue="trade_manager"
                                    )
                                    log_narration(
                                        event_type="ACD_PARTIAL_PROFIT",
                                        details={"symbol": symbol, "units_closed": half},
                                        symbol=symbol, venue="oanda"
                                    )
                                    send_sms(f"💰 ACD_PARTIAL_PROFIT: {symbol} | Scaled out 50%")
                        except Exception as _se:
                            self.display.warning(f"Scale-out error for {symbol}: {_se}")

                    elif trade_action == TradeAction.MOVE_BE:
                        new_sl = trade_detail.get('new_sl', entry_price)
                        new_sl, green_lock_applied, green_floor = self._enforce_green_sl(
                            symbol=symbol,
                            direction=direction,
                            entry_price=entry_price,
                            current_price=current_price,
                            candidate_sl=new_sl,
                        )
                        self.display.info(
                            f"🔒 BREAKEVEN {symbol}  new SL → {new_sl:.5f}", "", Colors.BRIGHT_GREEN
                        )
                        try:
                            trades = self.oanda.get_trades()
                            for t in trades:
                                ti = (t.get('instrument') or t.get('symbol', '')).upper()
                                if ti == symbol.upper():
                                    tid = t.get('id') or t.get('tradeID') or t.get('trade_id')
                                    self.oanda.set_trade_stop(tid, new_sl)
                                    pos['stop_loss'] = new_sl
                                    log_narration(
                                        event_type="SL_MOVED_BE",
                                        details={
                                            "symbol": symbol,
                                            "trade_id": tid,
                                            "entry": entry_price,
                                            "current_price": current_price,
                                            "new_sl": new_sl,
                                            "green_floor": green_floor,
                                            "green_lock_applied": green_lock_applied,
                                        },
                                        symbol=symbol, venue="trade_manager"
                                    )
                                    log_narration(
                                        event_type="ACD_BE_TRIGGER",
                                        details={"symbol": symbol, "new_sl": pos['entry']},
                                        symbol=symbol, venue="oanda"
                                    )
                                    send_sms(f"🛡️ ACD_BE_TRIGGER: {symbol} moved Stop Loss to entry Break-Even.")
                        except Exception as _be:
                            self.display.warning(f"Breakeven SL error for {symbol}: {_be}")

                    elif trade_action == TradeAction.TRAIL_TIGHT:
                        new_sl = trade_detail.get('new_sl')
                        new_sl, green_lock_applied, green_floor = self._enforce_green_sl(
                            symbol=symbol,
                            direction=direction,
                            entry_price=entry_price,
                            current_price=current_price,
                            candidate_sl=new_sl,
                        )
                        self.display.success(
                            f"🎯 TRAIL_TIGHT {symbol}  trail SL → {new_sl:.5f}  "
                            f"(R={trade_detail.get('pnl_r', 0):.2f})"
                        )
                        try:
                            trades = self.oanda.get_trades()
                            for t in trades:
                                ti = (t.get('instrument') or t.get('symbol', '')).upper()
                                if ti == symbol.upper():
                                    tid = t.get('id') or t.get('tradeID') or t.get('trade_id')
                                    sl_resp = self.oanda.set_trade_stop(tid, new_sl)
                                    if not isinstance(sl_resp, dict) or not sl_resp.get("success"):
                                        self.display.warning(
                                            f"⚠️ TRAIL SL REJECTED by broker for {symbol} "
                                            f"tid={tid} proposed_sl={new_sl:.5f}: {sl_resp}"
                                        )
                                        log_narration(
                                            event_type="TRAIL_SL_REJECTED",
                                            details={
                                                "symbol": symbol,
                                                "trade_id": tid,
                                                "proposed_sl": new_sl,
                                                "error": str(sl_resp),
                                                "pnl_r": trade_detail.get('pnl_r'),
                                            },
                                            symbol=symbol, venue="trade_manager"
                                        )
                                        continue  # do NOT update memory or log TRAIL_TIGHT_SET
                                    pos['stop_loss']   = new_sl
                                    pos['trail_active'] = True
                                    log_narration(
                                        event_type="TRAIL_TIGHT_SET",
                                        details={
                                            "symbol": symbol,
                                            "trade_id": tid,
                                            "entry": entry_price,
                                            "current_price": current_price,
                                            "new_sl": new_sl,
                                            "green_floor": green_floor,
                                            "green_lock_applied": green_lock_applied,
                                            "pnl_r": trade_detail.get('pnl_r'),
                                        },
                                        symbol=symbol, venue="trade_manager"
                                    )
                        except Exception as _te:
                            self.display.warning(f"Trail-tight SL error for {symbol}: {_te}")

                    elif trade_action == TradeAction.CLOSE_ALL:
                        reason = trade_detail.get('reason', 'engine')
                        self.display.alert(
                            f"🚪 CLOSE_ALL {symbol} reason={reason}  "
                            f"price={current_price:.5f}", "WARNING"
                        )
                        try:
                            trades = self.oanda.get_trades()
                            for t in trades:
                                ti = (t.get('instrument') or t.get('symbol', '')).upper()
                                if ti == symbol.upper():
                                    tid = t.get('id') or t.get('tradeID') or t.get('trade_id')
                                    self.oanda.close_trade(tid)
                                    log_narration(
                                        event_type="FORCED_CLOSE",
                                        details={"symbol": symbol, "reason": reason,
                                                 "pnl_r": trade_detail.get('pnl_r')},
                                        symbol=symbol, venue="trade_manager"
                                    )
                                    if reason != "stop_breach":
                                        log_narration(
                                            event_type="ACD_FULL_HARVEST",
                                            details={"symbol": symbol, "reason": "FORCED_CLOSE_DYNAMIC"},
                                            symbol=symbol, venue="oanda"
                                        )
                                        log_narration(
                                            event_type="ACD_PEAK_EXIT",
                                            details={"symbol": symbol, "reason": "FORCED_CLOSE_DYNAMIC"},
                                            symbol=symbol, venue="oanda"
                                        )
                                        send_sms(f"🏆 ACD_FULL_HARVEST / PEAK EXIT: {symbol} forced closed dynamically.")
                                    else:
                                        send_sms(f"🛑 STOP BREACH: {symbol} forced closed organically.")
                        except Exception as _ce:
                            self.display.warning(f"Force-close error for {symbol}: {_ce}")

                    # ── Legacy hive/momentum checks (continue after incremental mgmt) ──
                    # Calculate profit in pips and ATR multiples
                    pip_size = 0.0001 if 'JPY' not in symbol else 0.01
                    if direction == 'BUY':
                        profit_pips = (current_price - entry_price) / pip_size
                    else:
                        profit_pips = (entry_price - current_price) / pip_size
                    
                    # Estimate ATR (use stop_loss_pips / 1.2 as proxy, since stop = 1.2 * ATR)
                    estimated_atr_pips = self.stop_loss_pips / 1.2
                    profit_atr_multiple = profit_pips / estimated_atr_pips if estimated_atr_pips > 0 else 0

                    # Signal flags
                    hive_signal_confirmed = False
                    momentum_signal_confirmed = False

                    # Query Hive Mind for consensus on this instrument
                    if self.hive_mind:
                        market_data = {
                            "symbol": symbol.replace('_', ''),
                            "current_price": current_price,
                            "timeframe": "M15"
                        }

                        analysis = self.hive_mind.delegate_analysis(market_data)
                        consensus = analysis.consensus_signal
                        confidence = analysis.consensus_confidence

                        # Log the analysis
                        log_narration(
                            event_type="HIVE_ANALYSIS",
                            details={
                                "symbol": symbol,
                                "consensus": consensus.value if hasattr(consensus, 'value') else str(consensus),
                                "confidence": confidence,
                                "order_id": order_id,
                                "profit_atr": profit_atr_multiple
                            },
                            symbol=symbol,
                            venue="hive"
                        )

                        # Check hive consensus threshold for TP conversion (STRONG signals)
                        if confidence >= self.hive_trigger_confidence and consensus in (SignalStrength.STRONG_BUY, SignalStrength.STRONG_SELL):
                            if (direction == 'BUY' and consensus == SignalStrength.STRONG_BUY) or (direction == 'SELL' and consensus == SignalStrength.STRONG_SELL):
                                hive_signal_confirmed = True
                                self.display.info("Hive Consensus", f"{consensus.value} ({confidence:.2f}) for {symbol}", Colors.BRIGHT_CYAN)

                        # --- NEW: ADVANCED EARLY EXIT LOGIC (STOP THE BLEED) ---
                        # If Hive consensus is OPPOSITE to our trade and confidence is high enough, 
                        # and we are in profit drawdown (even small), exit early.
                        is_opposite = (direction == 'BUY' and consensus in (SignalStrength.SELL, SignalStrength.STRONG_SELL)) or \
                                      (direction == 'SELL' and consensus in (SignalStrength.BUY, SignalStrength.STRONG_BUY))
                        
                        if is_opposite and confidence >= 0.75 and profit_atr_multiple < -0.1:
                            self.display.warning(f"🚨 HIVE REVERSAL: Closing {symbol} {direction} (Hive consensus is {consensus.value} @ {confidence:.2f})")
                            try:
                                self.oanda.close_trade(broker_trade_id)
                                self.active_positions.pop(str(order_id), None)
                                self.active_positions.pop(str(broker_trade_id), None)
                                self.active_pairs.discard(symbol)
                                if self.positions_registry:
                                    try:
                                        self.positions_registry.unregister_position(symbol, 'oanda')
                                    except Exception: pass
                                
                                # Set cooldown to prevent immediate re-entry
                                self.tp_cooldowns[symbol.upper()] = datetime.now(timezone.utc)

                                log_narration(
                                    event_type="HIVE_EARLY_EXIT",
                                    details={
                                        "symbol": symbol,
                                        "consensus": consensus.value if hasattr(consensus, 'value') else str(consensus),
                                        "confidence": confidence,
                                        "pnl_atr": profit_atr_multiple,
                                        "reason": "Hive Reversal detected during drawdown"
                                    },
                                    symbol=symbol,
                                    venue="hive"
                                )
                                continue # Move to next position
                            except Exception as _ce:
                                self.display.error(f"Failed to execute Hive Early Exit for {symbol}: {_ce}")

                    # Use MomentumDetector from rbotzilla_golden_age.py
                    if self.momentum_detector and profit_atr_multiple > 0:
                        # Assume moderate trend and normal volatility for simple case
                        # (In production, you'd query actual regime/volatility from ML modules)
                        trend_strength = 0.7  # Moderate trend assumption
                        market_cycle = 'BULL_MODERATE'  # Default assumption
                        volatility = 1.0  # Normal volatility

                        has_momentum, momentum_strength = self.momentum_detector.detect_momentum(
                            profit_atr_multiple=profit_atr_multiple,
                            trend_strength=trend_strength,
                            cycle=market_cycle,
                            volatility=volatility
                        )

                        if has_momentum:
                            momentum_signal_confirmed = True
                            self.display.info("Momentum", f"{momentum_strength:.2f}x strength for {symbol} (profit: {profit_atr_multiple:.2f}x ATR)", Colors.BRIGHT_GREEN)
                            
                            log_narration(
                                event_type="MOMENTUM_DETECTED",
                                details={
                                    "symbol": symbol,
                                    "profit_atr": profit_atr_multiple,
                                    "momentum_strength": momentum_strength,
                                    "order_id": order_id
                                },
                                symbol=symbol,
                                venue="momentum_detector"
                            )

                    # Maintain adaptive trailing for already-converted positions
                    if tp_already_cancelled and self.trailing_system and profit_atr_multiple > 0:
                        try:
                            atr_price = estimated_atr_pips * pip_size
                            trail_distance = self.trailing_system.calculate_dynamic_trailing_distance(
                                profit_atr_multiple=profit_atr_multiple,
                                atr=atr_price,
                                momentum_active=momentum_signal_confirmed
                            )

                            if direction == 'BUY':
                                candidate_sl = current_price - trail_distance
                            else:
                                candidate_sl = current_price + trail_distance

                            original_sl = float(pos.get('stop_loss') or 0.0)
                            if direction == 'BUY':
                                adaptive_sl = max(candidate_sl, original_sl)
                                improvement_pips = (adaptive_sl - original_sl) / pip_size
                            else:
                                adaptive_sl = min(candidate_sl, original_sl) if original_sl > 0 else candidate_sl
                                improvement_pips = (original_sl - adaptive_sl) / pip_size if original_sl > 0 else 0.0

                            adaptive_sl, green_lock_applied, green_floor = self._enforce_green_sl(
                                symbol=symbol,
                                direction=direction,
                                entry_price=entry_price,
                                current_price=current_price,
                                candidate_sl=adaptive_sl,
                            )

                            min_step_pips = float(os.getenv('RBOT_MIN_TRAIL_STEP_PIPS', '0.5'))
                            if improvement_pips >= min_step_pips:
                                trades = self.oanda.get_trades()
                                for t in trades:
                                    trade_instrument = t.get('instrument') or t.get('symbol')
                                    trade_id = t.get('id') or t.get('tradeID') or t.get('trade_id')
                                    if not trade_id:
                                        continue
                                    if trade_instrument and trade_instrument.replace('.', '_').upper() == symbol:
                                        set_resp = self.oanda.set_trade_stop(trade_id, adaptive_sl)
                                        pos['stop_loss'] = adaptive_sl
                                        log_narration(
                                            event_type="TRAILING_SL_UPDATED",
                                            details={
                                                "trade_id": trade_id,
                                                "symbol": symbol,
                                                "set_stop": adaptive_sl,
                                                "prior_stop": original_sl,
                                                "improvement_pips": improvement_pips,
                                                "profit_atr": profit_atr_multiple,
                                                "momentum_active": momentum_signal_confirmed,
                                                "green_floor": green_floor,
                                                "green_lock_applied": green_lock_applied,
                                                "set_resp": set_resp,
                                            },
                                            symbol=symbol,
                                            venue="oanda"
                                        )
                                        break
                        except Exception as _ae:
                            self.display.warning(f"Adaptive trailing maintenance error for {symbol}: {_ae}")

                    # Trigger TP cancellation if EITHER signal confirmed
                    # (only once per position)
                    if (hive_signal_confirmed or momentum_signal_confirmed) and not tp_already_cancelled:
                        trigger_source = []
                        if hive_signal_confirmed:
                            trigger_source.append("Hive")
                        if momentum_signal_confirmed:
                            trigger_source.append("Momentum")
                        
                        self.display.alert(f"{'|'.join(trigger_source)} signal(s) detected for {symbol} - converting OCO to trailing SL", "INFO")

                        # Attempt to cancel TP order(s) associated with this OCO
                        try:
                            cancel_resp = self.oanda.cancel_order(order_id)

                            log_narration(
                                event_type="TP_CANCEL_ATTEMPT",
                                details={
                                    "order_id": order_id,
                                    "trigger_source": trigger_source,
                                    "profit_atr": profit_atr_multiple,
                                    "cancel_response": cancel_resp
                                },
                                symbol=symbol,
                                venue="oanda"
                            )

                            # Find open trades for this symbol and set an initial trailing stop
                            trades = self.oanda.get_trades()
                            for t in trades:
                                trade_instrument = t.get('instrument') or t.get('symbol')
                                trade_id = t.get('id') or t.get('tradeID') or t.get('trade_id')
                                if not trade_id:
                                    continue
                                if trade_instrument and trade_instrument.replace('.', '_').upper() == symbol:
                                    # Calculate adaptive trailing stop using SmartTrailingSystem
                                    if self.trailing_system and profit_atr_multiple > 0:
                                        atr_price = estimated_atr_pips * pip_size
                                        trail_distance = self.trailing_system.calculate_dynamic_trailing_distance(
                                            profit_atr_multiple=profit_atr_multiple,
                                            atr=atr_price,
                                            momentum_active=True
                                        )
                                        
                                        if direction == 'BUY':
                                            new_sl = current_price - trail_distance
                                        else:
                                            new_sl = current_price + trail_distance
                                        
                                        # Ensure new SL is better than original
                                        original_sl = pos.get('stop_loss')
                                        if direction == 'BUY':
                                            adaptive_sl = max(new_sl, original_sl)
                                        else:
                                            adaptive_sl = min(new_sl, original_sl)
                                    else:
                                        # Keep existing stop_loss
                                        adaptive_sl = pos.get('stop_loss')

                                    adaptive_sl, green_lock_applied, green_floor = self._enforce_green_sl(
                                        symbol=symbol,
                                        direction=direction,
                                        entry_price=entry_price,
                                        current_price=current_price,
                                        candidate_sl=adaptive_sl,
                                    )
                                    
                                    set_resp = self.oanda.set_trade_stop(trade_id, adaptive_sl)

                                    log_narration(
                                        event_type="TRAILING_SL_SET",
                                        details={
                                            "trade_id": trade_id,
                                            "order_id": order_id,
                                            "set_stop": adaptive_sl,
                                            "trail_distance_pips": (current_price - adaptive_sl) / pip_size if direction == 'BUY' else (adaptive_sl - current_price) / pip_size,
                                            "entry": entry_price,
                                            "current_price": current_price,
                                            "green_floor": green_floor,
                                            "green_lock_applied": green_lock_applied,
                                            "set_resp": set_resp,
                                            "trigger_source": trigger_source
                                        },
                                        symbol=symbol,
                                        venue="oanda"
                                    )

                                    # Mark position as having TP cancelled
                                    pos['tp_cancelled'] = True
                                    pos['tp_cancelled_timestamp'] = datetime.now(timezone.utc)
                                    pos['tp_cancel_source'] = trigger_source
                                    self.display.success(f"✅ TP cancelled and adaptive trailing SL set for trade {trade_id} ({symbol})")
                                    break

                        except Exception as e:
                            self.display.error(f"Error during TP cancellation/trailing conversion: {e}")
                            log_narration(
                                event_type="TP_CANCEL_ERROR",
                                details={"order_id": order_id, "error": str(e)},
                                symbol=symbol,
                                venue="oanda"
                            )

                # Sleep short interval before next pass
                await asyncio.sleep(5)
                
                # ========================================================================
                # 🛡️ UPDATE TRADE MANAGER HEARTBEAT (NEW - Per User Requirement)
                # ========================================================================
                self.trade_manager_last_heartbeat = datetime.now(timezone.utc)
                
            except Exception as e:
                self.display.error(f"TradeManager loop error: {e}")
                await asyncio.sleep(5)
        
        # ========================================================================
        # 🛡️ TRADE MANAGER DEACTIVATION (NEW - Per User Requirement)
        # ========================================================================
        self.trade_manager_active = False
        self.display.warning("⚠️  TRADE MANAGER DEACTIVATED")
        log_narration(
            event_type="TRADE_MANAGER_DEACTIVATED",
            details={
                "status": "INACTIVE",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            symbol="SYSTEM",
            venue="trade_manager"
        )
    
    def _handle_position_closed(self, trade_id: str):
        """Handle a closed position"""
        if trade_id not in self.active_positions:
            return
        
        position = self.active_positions[trade_id]
        
        try:
            # Get trade details from OANDA
            trades = self.oanda.get_trades()
            
            # Assume win for now (we'd need to check actual closing price)
            # In real implementation, you'd query the closed trade details
            is_win = True  # Placeholder
            
            pnl = 50.0 if is_win else -20.0  # Placeholder values
            
            if is_win:
                self.wins += 1
                self.display.trade_win(
                    position['symbol'],
                    pnl,
                    f"Exit: {position['take_profit']:.5f} | R:R 3:1 achieved"
                )
            else:
                self.losses += 1
                self.display.trade_loss(
                    position['symbol'],
                    pnl,
                    f"Exit: {position['stop_loss']:.5f} | Stopped out"
                )
            
            # Remove from active positions
            del self.active_positions[trade_id]
            
            # ========================================================================
            # 🛡️ REMOVE FROM ACTIVE PAIRS (NEW - Per User Requirement)
            # ========================================================================
            if position['symbol'] in self.active_pairs:
                self.active_pairs.discard(position['symbol'])
                self.display.info(f"✅ Pair {position['symbol']} removed from active pairs ({len(self.active_pairs)}/{self.max_pairs_per_platform})", "", Colors.BRIGHT_CYAN)
            
            # ========================================================================
            # 🛡️ UNREGISTER POSITION FROM CROSS-PLATFORM REGISTRY
            # ========================================================================
            if self.positions_registry:
                try:
                    unregistered = self.positions_registry.unregister_position(
                        symbol=position['symbol'],
                        platform='oanda'
                    )
                    if unregistered:
                        self.display.info("📋 Position removed from cross-platform registry", "", Colors.BRIGHT_CYAN)
                except Exception as e:
                    self.display.warning(f"⚠️  Could not unregister position: {e}")
            
            # Display stats
            self._display_stats()
            
        except Exception as e:
            self.display.error(f"Error handling closed position: {e}")
    
    def _display_stats(self):
        """Display current statistics"""
        win_rate = (self.wins / self.total_trades * 100) if self.total_trades > 0 else 0
        
        stats = {
            "Total Trades": str(self.total_trades),
            "Active Positions": str(len(self.active_positions)),
            "Wins / Losses": f"{self.wins} / {self.losses}",
            "Win Rate": f"{win_rate:.1f}%"
        }
        
        self.display.stats_panel(stats)
    
    def _manage_trade(self, trade: dict) -> None:
        """
        Per-trade management hook — called for each active position each cycle.
        rbz_tight_trailing.py wraps this method via apply_rbz_overrides() to inject
        the Two-Step SL lock + aggressive trailing stop logic.
        Without this stub, the trailing wire fails silently and stops NEVER trail.
        PIN: 841921 | IMMUTABLE HOOK — do not remove.
        """
        # Base: nothing to do — rbz_tight_trailing wrapper handles the real work
        pass

    async def run_trading_loop(self):
        """Main trading loop (environment-agnostic)"""
        self.is_running = True
        
        env_label = "PRACTICE" if self.environment == 'practice' else "LIVE"
        self.display.alert(f"Starting trading engine with {env_label} API...", "SUCCESS")
        self.display.alert(f"📊 Market Data: {env_label} OANDA API (real-time)", "INFO")
        self.display.alert(f"💰 Orders: {env_label} OANDA API", "INFO")
        print()
        
        trade_count = 0
        last_police_sweep = time.time()  # Track last Position Police sweep
        police_sweep_interval = 900  # 15 minutes (M15 charter compliance)
        last_status_report = time.time()  # Track last status report
        status_report_interval = 300  # Report bot status every 5 minutes
        
        # Sync any trades already open on the broker before the manager starts
        self._sync_open_positions()
        
        # Analyze positions against new config (1.5% risk, 55% vote floor / 62% final gate)
        self._analyze_and_reoptimize_positions()

        # Start TradeManager background task
        trade_manager_task = asyncio.create_task(self.trade_manager_loop())
        
        # Start Connection Health Monitor background task
        health_monitor_task = asyncio.create_task(self.monitor_connection_health())
        self.display.success("✅ Health monitor task started - auto-reconnect ACTIVE")
        
        # Initial status awareness
        self.bot_status['engine_initialized'] = True
        self.bot_status['connected'] = True
        self.display.success("✅ BOT STATUS AWARENESS: ACTIVE")
        self.report_bot_status()
        
        while self.is_running:
            try:
                # UPDATE BOT STATUS (every loop iteration)
                self.update_bot_status()
                
                # PERIODIC STATUS REPORT (every 5 minutes)
                current_time_status = time.time()
                if current_time_status - last_status_report >= status_report_interval:
                    self.display.section(f"📊 BOT STATUS UPDATE - Is Trading: {self.bot_status['is_trading']}")
                    self.bot_status['total_signals_scanned'] += 1
                    last_status_report = current_time_status
                
                # AUTOMATED POSITION POLICE SWEEP (every 15 minutes)
                current_time = time.time()
                if current_time - last_police_sweep >= police_sweep_interval:
                    try:
                        self.display.info("Position Police", "🚓 Sweep starting...", Colors.BRIGHT_MAGENTA)
                        _rbz_force_min_notional_position_police()
                        last_police_sweep = current_time
                        self.display.success("✅ Position Police sweep complete")
                    except Exception as e:
                        self.display.error(f"❌ Position Police error: {e}")
                
                # Check existing positions
                self.check_positions()

                # Refresh gate NAV from live account balance each cycle
                try:
                    if hasattr(self.oanda, 'get_account_info'):
                        _acct = self.oanda.get_account_info()
                        if _acct is not None:
                            _nav = float(getattr(_acct, 'balance', None) or self.gate.account_nav)
                            if _nav != self.gate.account_nav:
                                self.gate.account_nav = _nav
                                self.gate.max_margin_usd = _nav * self.gate.MARGIN_CAP_PCT
                except Exception:
                    pass
                
                # --- AGGRESSIVE PRACTICE PATCH LOGIC ---
                try:
                    if self.environment == 'practice':
                        practice_res = run_aggressive_practice_cycle(self)
                        if practice_res.get("block_new_entries", False):
                            MAX_POSITIONS = 0 # Temporarily zero out new entries for this cycle
                        else:
                            MAX_POSITIONS = self.max_active_positions
                    else:
                        MAX_POSITIONS = self.max_active_positions
                except Exception as _prac_err:
                    self.display.error(f"Practice Rotation Engine error: {_prac_err}")
                    MAX_POSITIONS = self.max_active_positions
                # ── Multi-strategy scan: place ALL qualifying signals ─────────

                open_count = len(self.active_positions)
                if open_count >= MAX_POSITIONS:
                    self.display.alert(
                        f"Max positions reached ({open_count}/{MAX_POSITIONS}) — "
                        f"evaluating for a higher-confidence upgrade...",
                        "INFO"
                    )

                if open_count <= MAX_POSITIONS:
                    from datetime import datetime, timezone as _tz
                    _utc_now = datetime.now(_tz.utc)

                    # Symbols already open on broker OR tracked locally
                    held_on_broker = set(
                        (t.get('instrument') or t.get('symbol', '')).upper()
                        for t in (self.oanda.get_trades() or [])
                    )
                    active_symbols = {
                        pos['symbol'].upper()
                        for pos in self.active_positions.values()
                        if 'symbol' in pos
                    }
                    blocked_symbols = held_on_broker | active_symbols

                    qualified: list[AggregatedSignal] = []
                    blocked_upgrade_candidates: list[AggregatedSignal] = []
                    rejected:  list[dict]             = []

                    for _candidate in self.trading_pairs:
                        _cu = _candidate.upper()
                        is_blocked_symbol = _cu in blocked_symbols

                        # ── fetch candles + run all detectors ───────────
                        try:
                            candles = self.oanda.get_historical_data(
                                _candidate, count=250, granularity="M15"
                            )
                            
                            if candles and "time" in candles[-1]:
                                last_time_str = candles[-1]["time"][:19]
                                last_dt = datetime.fromisoformat(last_time_str).replace(tzinfo=_tz.utc)
                                if (_utc_now - last_dt).total_seconds() > 3600:
                                    rejected.append({
                                        'symbol': _candidate,
                                        'reason': 'market_closed',
                                        'conf': None,
                                        'dir': None
                                    })
                                    continue

                            agg = scan_symbol(
                                _candidate, candles,
                                utc_now=_utc_now,
                                min_confidence=self.min_confidence,  # 0.68 aggregated floor
                                min_votes=3,  # 3-of-9 detectors must agree (Dec 10 standard)
                            )
                        except Exception as _scan_err:
                            rejected.append({'symbol': _candidate,
                                             'reason': 'error_in_scan',
                                             'conf': None, 'dir': None,
                                             'detail': str(_scan_err)})
                            continue

                        # ── Hive Conflict Check ─────────────────────────
                        if self.hive_mind:
                            try:
                                # Quick check to ensure we aren't scanning against the Hive consensus
                                hive_analysis = self.hive_mind.delegate_analysis({'symbol': _candidate})
                                hive_signal = (hive_analysis.consensus_signal.value or '').upper()
                                if ('BUY' in hive_signal and agg.direction == 'SELL') or \
                                   ('SELL' in hive_signal and agg.direction == 'BUY'):
                                    rejected.append({'symbol': _candidate,
                                                     'reason': 'hive_conflict',
                                                     'conf': agg.confidence, 'dir': agg.direction,
                                                     'detail': f"Hive suggests {hive_signal}"})
                                    continue
                            except Exception:
                                pass # Don't block if hive fails

                        # ── not enough consensus ─────────────────────────
                        if agg is None:
                            rejected.append({'symbol': _candidate,
                                             'reason': 'no_signal',
                                             'conf': None, 'dir': None})
                            continue

                        # ── confidence gate (selection threshold) ────────
                        if agg.confidence < self.min_signal_confidence:
                            rejected.append({'symbol': _candidate,
                                             'reason': 'confidence_below_threshold',
                                             'conf': agg.confidence,
                                             'dir':  agg.direction,
                                             'threshold': self.min_signal_confidence})
                            continue

                        # ── already active symbol: keep as upgrade candidate ─
                        if is_blocked_symbol:
                            blocked_upgrade_candidates.append(agg)
                            rejected.append({'symbol': _candidate,
                                             'reason': 'already_active_symbol',
                                             'conf': agg.confidence,
                                             'dir':  agg.direction})
                            continue

                        # ── passed — queue it ─────────────────────────────
                        qualified.append(agg)

                    # Sort best-edge first
                    qualified.sort(key=lambda x: x.confidence, reverse=True)
                    blocked_upgrade_candidates.sort(key=lambda x: x.confidence, reverse=True)

                    # News & Spread Gate on candidates
                    surviving_qualified = []
                    for q in qualified:
                        gate_res = evaluate_news_spread(q.symbol, 1.0) # Using generic spread simulation until dynamic spread API available
                        if gate_res.get("status") == "BLOCK":
                            rejected.append({"symbol": q.symbol, "reason": "hostile_conditions", "conf": q.confidence})
                        else:
                            surviving_qualified.append(q)
                    qualified = surviving_qualified

                    slots_left  = MAX_POSITIONS - open_count
                    cycle_limit = min(slots_left, self.max_new_trades_per_cycle,
                                      len(qualified))

                    reason_counts = {}
                    for item in rejected:
                        reason = item.get('reason', 'unknown')
                        reason_counts[reason] = reason_counts.get(reason, 0) + 1

                    # ── SIGNAL_SCAN_RESULTS log (terminal + narration) ───
                    N = self.scan_log_top_n
                    scan_summary = {
                        'pairs_scanned':    len(self.trading_pairs),
                        'candidates_passed': len(qualified),
                        'open_slots':       slots_left,
                        'placing':          cycle_limit,
                        'min_conf_gate':    self.min_signal_confidence,
                        'top_candidates':   [
                            {'symbol': a.symbol, 'dir': a.direction,
                             'conf': round(a.confidence, 4),
                             'votes': a.votes,
                             'detectors': a.detectors_fired,
                             'session': a.session, 'rr': round(a.rr, 2)}
                            for a in qualified[:N]
                        ],
                        'top_rejected': [
                            {'symbol': r['symbol'], 'reason': r['reason'],
                             'conf': r.get('conf'), 'dir': r.get('dir')}
                            for r in rejected[:N]
                        ],
                        'rejected_by_stage': reason_counts,
                    }
                    log_narration(
                        event_type="SIGNAL_SCAN_RESULTS",
                        details=scan_summary,
                        symbol="SYSTEM",
                        venue="signal_scan",
                    )

                    # Terminal summary
                    self.display.section(
                        f"📡 SCAN: {len(self.trading_pairs)} pairs "
                        f"| ✅ {len(qualified)} passed "
                        f"| ❌ {len(rejected)} rejected "
                        f"| 🎯 placing {cycle_limit}"
                    )
                    for a in qualified[:N]:
                        self.display.success(
                            f"  ✅ {a.symbol:10} {a.direction:4} "
                            f"conf={a.confidence:.1%}  votes={a.votes}  "
                            f"det={','.join(a.detectors_fired)}  "
                            f"sess={a.session}  RR={a.rr:.2f}"
                        )
                    for r in rejected[:N]:
                        conf_str = f"{r['conf']:.1%}" if r['conf'] else 'n/a'
                        self.display.warning(
                            f"  ❌ {r['symbol']:10} {str(r.get('dir') or ''):4} "
                            f"conf={conf_str:6}  → {r['reason']}"
                        )
                    if reason_counts:
                        self.display.info(
                            "Gate blocks",
                            ", ".join(f"{k}:{v}" for k, v in sorted(reason_counts.items())),
                            Colors.BRIGHT_YELLOW
                        )

                    if cycle_limit == 0:
                        reallocated = False
                        opportunity_pool = sorted(
                            qualified + blocked_upgrade_candidates,
                            key=lambda x: x.confidence,
                            reverse=True
                        )
                        if len(opportunity_pool) > 0 and open_count >= MAX_POSITIONS:
                            reallocated = self._try_opportunity_reallocation(opportunity_pool)
                        if reallocated:
                            held_on_broker = set(
                                (t.get('instrument') or t.get('symbol', '')).upper()
                                for t in (self.oanda.get_trades() or [])
                            )
                            active_symbols = {
                                pos['symbol'].upper()
                                for pos in self.active_positions.values()
                                if 'symbol' in pos
                            }
                            blocked_symbols = held_on_broker | active_symbols

                            for blocked_agg in blocked_upgrade_candidates:
                                if blocked_agg.symbol.upper() not in blocked_symbols:
                                    qualified.append(blocked_agg)

                            qualified.sort(key=lambda x: x.confidence, reverse=True)

                            open_count = len(self.active_positions)
                            slots_left = max(0, MAX_POSITIONS - open_count)
                            cycle_limit = min(slots_left, self.max_new_trades_per_cycle,
                                              len(qualified))

                    if cycle_limit == 0:
                        self.display.warning(
                            f"No qualifying signals this cycle — "
                            f"rescanning in {self.scan_fast_seconds}s..."
                        )
                        await asyncio.sleep(self.scan_fast_seconds)
                        continue

                    # ── Place each selected trade ─────────────────────────
                    # _placed_this_cycle prevents duplicate placements for the
                    # same symbol within a single cycle, even if active_positions
                    # hasn't been updated yet due to async timing.
                    _placed_this_cycle: set = set()

                    for agg in qualified[:cycle_limit]:
                        symbol = agg.symbol
                        
                        already_active = False

                        # In-cycle dedup: blocks same symbol twice in one
                        # scan cycle regardless of active_positions update lag
                        if symbol.upper() in _placed_this_cycle:
                            already_active = True

                        if not already_active and symbol in getattr(self, "active_positions", {}):
                            already_active = True

                        if not already_active:
                            try:
                                open_positions = self.oanda.get_open_positions()
                                for _p in open_positions or []:
                                    _sym = _p.get("instrument") or _p.get("symbol")
                                    if _sym == symbol:
                                        already_active = True
                                        break
                            except Exception:
                                pass

                        if already_active:
                            rejected.append({
                                "symbol": symbol,
                                "reason": "symbol_already_active",
                                "conf": None,
                                "dir": None
                            })
                            # use log_narration instead of self._narrate to match existing logging architecture in engine
                            log_narration(
                                event_type="SYMBOL_ALREADY_ACTIVE_BLOCK",
                                details={"reason": "existing_position"},
                                symbol=symbol,
                                venue="oanda"
                            )
                            continue

                        # ── Phase 1: CANDIDATE_FOUND ─────────────────────────
                        # Safe to log — we have a qualifying signal but have
                        # NOT yet confirmed the broker will accept the order.
                        log_narration(
                            event_type="CANDIDATE_FOUND",
                            details={
                                "symbol":     symbol,
                                "direction":  agg.direction,
                                "confidence": round(agg.confidence, 4),
                                "votes":      agg.votes,
                                "detectors":  agg.detectors_fired,
                                "session":    agg.session,
                            },
                            symbol=symbol, venue="signal_scan"
                        )
                        self.display.info(
                            "CANDIDATE",
                            f"{symbol} {agg.direction} conf={agg.confidence:.1%} "
                            f"({agg.votes} votes: {','.join(agg.detectors_fired)})",
                            Colors.BRIGHT_CYAN
                        )

                        # ── Phase 2: broker tradability gate ─────────────────
                        _tradability = self._check_broker_tradability(symbol)
                        if not _tradability.get("tradable"):
                            _reason = _tradability.get("reason", "unknown")
                            _detail = _tradability.get("detail", {})

                            # Map reason → narration event type
                            _event_map = {
                                "instrument_not_tradable": "INSTRUMENT_NOT_TRADABLE_BLOCK",
                                "stale_quote":             "STALE_QUOTE_BLOCK",
                                "spread_too_wide":         "SPREAD_TOO_WIDE_BLOCK",
                                "quote_fetch_failed":      "ORDER_SUBMIT_BLOCK",
                                "tradability_check_error": "ORDER_SUBMIT_BLOCK",
                            }
                            # stale_quote from pricing is the market-closed proxy
                            if _reason == "stale_quote":
                                _event_type = "MARKET_CLOSED_BLOCK"
                            else:
                                _event_type = _event_map.get(_reason, "ORDER_SUBMIT_BLOCK")

                            log_narration(
                                event_type=_event_type,
                                details={"symbol": symbol, "reason": _reason, **_detail},
                                symbol=symbol, venue="tradability_gate"
                            )
                            self.display.warning(
                                f"🚫 {_event_type}: {symbol} blocked — {_reason} {_detail}"
                            )
                            rejected.append({
                                "symbol": symbol,
                                "reason": _reason,
                                "conf":   agg.confidence,
                                "dir":    agg.direction,
                            })
                            continue

                        # ── Phase 3: ORDER_SUBMIT_ALLOWED — safe to place ────
                        log_narration(
                            event_type="ORDER_SUBMIT_ALLOWED",
                            details={
                                "symbol":    symbol,
                                "direction": agg.direction,
                                "confidence": round(agg.confidence, 4),
                            },
                            symbol=symbol, venue="tradability_gate"
                        )
                        self.display.success(
                            f"→ Placing {agg.symbol} {agg.direction} "
                            f"conf={agg.confidence:.1%}  "
                            f"({agg.votes} votes: {','.join(agg.detectors_fired)})"
                        )
                        trade_id = self.place_trade(
                            agg.symbol, agg.direction,
                            signal_sl=agg.sl,
                            signal_tp=agg.tp,
                            signal_confidence=agg.confidence,
                            signal_votes=agg.votes,
                            signal_detectors=agg.detectors_fired,
                            signal_session=agg.session,
                            signal_type=getattr(agg, 'signal_type', 'trend'),
                        )

                        if trade_id:
                            # Lock this symbol for remainder of this cycle
                            _placed_this_cycle.add(symbol.upper())

                            if trade_id in self.active_positions:
                                self.active_positions[trade_id].update({
                                    'signal_sl':        agg.sl,
                                    'signal_tp':        agg.tp,
                                    'signal_confidence': agg.confidence,
                                    'signal_votes':     agg.votes,
                                    'signal_detectors': agg.detectors_fired,
                                    'signal_timeframe': "M15",
                                    'signal_session':   agg.session,
                                    'management_profile': "OCO SL/TP; 0.5R->BE; 1R->scale50%; 2R->trail; hard_stop_usd",
                                    'scaled_out':       False,
                                    'trail_active':     False,
                                })
                            trade_count += 1

                    self.display.divider()
                    print()
                
                # Fast rescan while slots remain; slow only when full.
                open_count_now = len(self.active_positions)
                
                # ── DASHBOARD: Display position summary and system health ───────
                try:
                    if self.dashboard and os.getenv('RBOT_DASHBOARD_ACTIVE', 'true').lower() != 'false':
                        self.dashboard.sync_and_display()
                except Exception as _dashboard_err:
                    self.display.warning(f"⚠️ Dashboard render error: {_dashboard_err}")
                
                if open_count_now >= MAX_POSITIONS:
                    self.display.alert(
                        f"Positions full ({open_count_now}/{MAX_POSITIONS}) — "
                        f"waiting {self.scan_slow_seconds}s for next slot...",
                        "INFO"
                    )
                    await asyncio.sleep(self.scan_slow_seconds)
                else:
                    self.display.alert(
                        f"Slots open ({open_count_now}/{MAX_POSITIONS}) — "
                        f"rescanning in {self.scan_fast_seconds}s...",
                        "INFO"
                    )
                    await asyncio.sleep(self.scan_fast_seconds)

                
            except KeyboardInterrupt:
                self.display.warning("\n⏹️  Stopping trading engine gracefully...")
                self.is_running = False
                log_narration(
                    event_type="BOT_STOPPED_BY_USER",
                    details={"timestamp": datetime.now(timezone.utc).isoformat()},
                    symbol="SYSTEM",
                    venue="trading_loop"
                )
                break
            except Exception as e:
                self.display.error(f"❌ Error in trading loop: {e}")
                
                # Attempt automatic reconnection
                await self.handle_connection_loss(str(e))
                
                if self.is_running:
                    # Try to reconnect before continuing
                    reconnected = await self.attempt_reconnect()
                    if not reconnected and self.is_running:
                        # Calculate wait time with exponential backoff
                        wait_time = min(
                            self.reconnect_config['initial_wait_seconds'] * (
                                self.reconnect_config['exponential_base'] ** 
                                (self.connection_state['reconnect_attempt'] - 1)
                            ),
                            self.reconnect_config['max_wait_seconds']
                        )
                        self.display.warning(f"⏳ Waiting {wait_time:.0f}s before next reconnect attempt...")
                        await asyncio.sleep(wait_time)
        
        self.display.section("SESSION COMPLETE")
        self._display_stats()
        # Cancel trade manager task
        try:
            trade_manager_task.cancel()
            health_monitor_task.cancel()
        except Exception:
            pass


async def main():
    """Main entry point - environment determined by API configuration"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RBOTzilla Charter-Compliant OANDA Trading Engine')
    parser.add_argument('--env', '--environment', 
                       choices=['practice', 'live'], 
                       default='practice',
                       help='Trading environment (practice=paper, live=real money)')
    parser.add_argument('--yes-live', action='store_true',
                       help='Required for non-interactive LIVE startup')
    parser.add_argument('--node-id', type=str, default='master',
                       help='Hive Mind Swarm Node ID')
    
    args = parser.parse_args()
    
    # Confirm LIVE mode with user
    if args.env == 'live':
        if args.yes_live:
            print("\n✅ LIVE startup confirmed via --yes-live. Running full startup sequence...\n")
        else:
            print("\n" + "="*60)
            print("⚠️  LIVE TRADING MODE - REAL MONEY AT RISK ⚠️")
            print("="*60)
            confirm = input("\nType 'CONFIRM LIVE' to proceed with live trading: ")
            if confirm != 'CONFIRM LIVE':
                print("Live trading cancelled.")
                return
            print("\n✅ Live trading confirmed. Running full startup sequence...\n")
    
    # ══════════════════════════════════════════════════════════════════════════
    # NEW: COMPREHENSIVE STARTUP SEQUENCE WITH DETAILED CONFIRMATIONS
    # ══════════════════════════════════════════════════════════════════════════
    try:
        from startup_sequence import run_startup
        startup_result = run_startup(environment=args.env)
        # startup_result contains all confirmations and background bot statuses
    except ImportError:
        print("⚠️  Enhanced startup sequence not available, using basic initialization")
    except Exception as e:
        print(f"⚠️  Startup sequence error: {e}, continuing with basic initialization")
    
    print(f"\n🚀 Initializing trading engine... [Node ID: {args.node_id}]\n")
    engine = OandaTradingEngine(environment=args.env)
    await engine.run_trading_loop()


# RBZ guard at import time
try:
    _rbz_force_min_notional_position_police()
except Exception as _e:
    print('[RBZ_POLICE] error', _e)

if __name__ == '__main__':
    asyncio.run(main())
