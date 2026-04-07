#!/usr/bin/env python3
"""
trade_engine.py
RBOTZILLA_OANDA_CLEAN — Phase 7
Label: NEW_CLEAN_REWRITE

OANDA Practice-Only Trade Engine.
No Phoenix path assumptions. No ML. No Coinbase. No live mode.

Execution flow per cycle:
    1.  Load env + initialize connector
    2.  Startup verification (account, endpoint, open trades)
    3.  Scan each configured pair → fetch M15 candles
    4.  Run scan_symbol() → optional AggregatedSignal
    5.  Dedup: skip if symbol already active this cycle or in broker
    6.  Log CANDIDATE_FOUND
    7.  Call check_broker_tradability() → may block here
    8.  Log gate result (ORDER_SUBMIT_ALLOWED or a *_BLOCK)
    9.  If allowed: log "→ Placing", place via OCO, confirm trade_id
    10. Log TRADE_OPENED only on confirmed broker trade_id
    11. Sleep scan_fast_seconds, loop
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, Set

# Ensure repo root is on sys.path (engine/ lives one level below)
_repo_root = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, _repo_root)

from config.profile_manager import load_engine_profile
load_engine_profile(_repo_root)

# ── Local imports (no Phoenix paths) ──────────────────────────────────────────
from brokers.coinbase_connector import get_coinbase_connector
from strategies.multi_signal_engine import scan_symbol, AggregatedSignal
from engine.broker_tradability_gate import (
    check_broker_tradability, validate_oco_payload,
    check_submit_response,
    set_cooldown,
)
from engine.trade_manager import TradeManager
from engine.pre_market_scanner import PreMarketScanner
from engine.capital_router import CapitalRouter, compute_compounded_units, compute_watermark_compounded_units
# regime_detector intentionally not imported — vote+confidence gate is the quality filter
from engine.mean_reversion_scanner import scan_sideways_symbol
from engine.strategy_pipelines import (
    run_momentum_pipeline,
    run_reversal_pipeline,
    run_meanrev_pipeline,
    run_scalp_pipeline,
)
from foundation.rick_charter import RickCharter
from util.narration_logger import (
    log_event, log_trade_opened, log_gate_block, log_narration,
    CANDIDATE_FOUND, ORDER_SUBMIT_ALLOWED, SYMBOL_ALREADY_ACTIVE_BLOCK,
    TRADE_OPENED, TRADE_OPEN_FAILED, ENGINE_STARTED, ENGINE_STOPPED,
    SIGNAL_SCAN_COMPLETE, OCO_VALIDATION_BLOCK, ORDER_SUBMIT_BLOCK,
    MARGIN_GATE_BLOCKED, ATTACH_ONLY_BLOCK,
    CAPITAL_REALLOC_DECIDED, CAPITAL_REALLOC_FAILED,
)

# ── Env-driven config ──────────────────────────────────────────────────────────
MAX_POSITIONS          = int(os.getenv("RBOT_MAX_POSITIONS",           "12"))
MAX_NEW_PER_CYCLE      = int(os.getenv("RBOT_MAX_NEW_TRADES_PER_CYCLE", "4"))
SCAN_FAST_SECONDS      = int(os.getenv("RBOT_SCAN_FAST_SECONDS",       "60"))
SCAN_SLOW_SECONDS      = int(os.getenv("RBOT_SCAN_SLOW_SECONDS",       "300"))
MIN_CONFIDENCE         = float(os.getenv("RBOT_MIN_SIGNAL_CONFIDENCE", "0.75"))  # raised 0.70→0.75: Phoenix production standard  # PATCH#1
MIN_VOTES              = int(os.getenv("RBOT_MIN_VOTES",               "3"))
CANDLE_COUNT           = int(os.getenv("RBOT_CANDLE_COUNT",            "250"))
CANDLE_GRANULARITY     = os.getenv("RBOT_CANDLE_GRANULARITY",          "M15")
MIN_FREE_MARGIN_PCT    = float(os.getenv("RBOT_MIN_FREE_MARGIN_PCT",   "0.20"))  # block if <20% margin free
CHARTER_MIN_NOTIONAL_USD = float(os.getenv("RBOT_CHARTER_MIN_NOTIONAL_USD", "15000"))
CHARTER_TARGET_NOTIONAL_USD = float(os.getenv("RBOT_CHARTER_TARGET_NOTIONAL_USD", "17500"))
CHARTER_MIN_RR = float(os.getenv("RBOT_CHARTER_MIN_RR", "3.26"))

# ── Safety mode flags ─────────────────────────────────────────────────────────
# Both default to False so existing deployments are unaffected without .env change.
# Set ATTACH_ONLY=true when Phoenix is the active opener to prevent dual-placement.
ATTACH_ONLY          = os.getenv("ATTACH_ONLY",          "false").strip().lower() == "true"
DISABLE_NEW_ENTRIES  = os.getenv("DISABLE_NEW_ENTRIES",  "false").strip().lower() == "true"
PAIR_REENTRY_COOLDOWN_MINUTES = int(os.getenv("RBOT_PAIR_REENTRY_COOLDOWN_MINUTES", "60"))  # PATCH#3

# ── Signal Quality Gates ──────────────────────────────────────────────────────
VOLUME_GATE_ENABLED = os.getenv("RBOT_VOLUME_GATE_ENABLED", "true").strip().lower() == "true"
VOLUME_GATE_MULT    = float(os.getenv("RBOT_VOLUME_GATE_MULT", "1.2"))
RSI_GATE_ENABLED    = os.getenv("RBOT_RSI_GATE_ENABLED", "true").strip().lower() == "true"
RSI_OB_LEVEL        = float(os.getenv("RBOT_RSI_OB_LEVEL", "75"))
RSI_OS_LEVEL        = float(os.getenv("RBOT_RSI_OS_LEVEL", "25"))

_DEFAULT_COINBASE_PAIRS = (
    "BTC-USD,ETH-USD,ADA-USD,XRP-USD,DOT-USD,LINK-USD,LTC-USD,BCH-USD,"
    "XLM-USD,EOS-USD,TRX-USD,VET-USD,ALGO-USD,ATOM-USD,AVAX-USD,POL-USD,"
    "SOL-USD,UNI-USD"
)
TRADING_PAIRS = [
    p.strip().upper() for p in os.getenv("COINBASE_INSTRUMENTS", _DEFAULT_COINBASE_PAIRS).split(",")
    if p.strip()
]


class TradeEngine:
    """
    Practice-only OANDA trade engine.
    Single async loop: scan → gate → place → sleep.
    """

    def __init__(self):
        # Charter compliance validation
        if hasattr(RickCharter, 'validate_pin'):
            if not RickCharter.validate_pin(841921):
                raise PermissionError("Invalid Charter PIN — cannot initialize trading engine")

        self.connector        = get_coinbase_connector()
        self.active_positions: Dict[str, dict] = {}   # trade_id → position dict
        self.manager          = TradeManager(self.connector)
        self.is_running       = False
        self._pair_last_trade_ts: Dict[str, float] = {}
        self._pair_last_side: Dict[str, str] = {}
        self._cooldown_persist_path = Path("/tmp/rbotz_clean_cooldowns.json")
        self._load_cooldown_state()  # restore cooldowns saved by last run

        # ── Pre-market scanner (fires once per session boundary) ───────────────
        self.pre_scanner      = PreMarketScanner(self.connector)
        self._session_playbook = []   # ranked list from last pre-market scan

        # ── Capital router (snowball reallocation) — init_nav resolved at start ─
        self._initial_nav     = 0.0   # set in run() after first account query
        self._watermark_nav   = 0.0   # highest observed NAV since engine start
        self._router: Optional[CapitalRouter] = None

        print("  ✅ Foundation/Charter imported and validated")
        print(f"  ✅ TradeManager initialized (hard_stop=${self.manager._hard_stop_usd:.0f})")
        print("  ✅ PreMarketScanner initialized")
        print("  ✅ CapitalRouter ready (activates after first NAV read)")

        # ── Phoenix-mode: fixed SL/TP pips (0 = use signal's computed values) ──
        self._sl_pips = int(os.getenv("RBOT_SL_PIPS", "0"))
        self._tp_pips = int(os.getenv("RBOT_TP_PIPS", "0"))

        # ── Chop Mode Config ────────────────────────────────────────────────
        self._chop_enabled = os.getenv("RBOT_CHOP_MODE_ENABLED", "false").lower() == "true"
        self._chop_units   = int(os.getenv("RBOT_CHOP_UNITS", "14000"))
        self._chop_max_pos = int(os.getenv("RBOT_CHOP_MAX_POSITIONS", "3"))
        self.current_max_positions = int(os.getenv("RBOT_MAX_POSITIONS", "3"))
        self.is_chop_mode_active = False

        # Hedge Engine entirely amputated for Coinbase API (per user directive)
        self._hedge_engine = None

    # ── Regime Monitor ───────────────────────────────────────────────────────
    
    def _update_regime_state(self) -> None:
        """Dynamically toggles Chop Mode based on BTC-USD volatility instead of clocks."""
        if not self._chop_enabled:
            self.is_chop_mode_active = False
            self.current_max_positions = int(os.getenv("RBOT_MAX_POSITIONS", "3"))
            return
            
        try:
            # Query the king of crypto to determine global market state
            candles = self.connector.get_historical_data("BTC-USD", count=50, granularity="15")
            if not candles or len(candles) < 50:
                return  # fail open
            
            closes = [float(c.get("mid", {}).get("c", 0)) for c in candles]
            from engine.regime_detector import detect_market_regime
            r_data = detect_market_regime(closes, "BTC-USD")
            
            # If BTC is in Chop/Sideways/Triage, compress the entire engine
            if r_data.get('regime').upper() in ('SIDEWAYS', 'TRIAGE'):
                self.is_chop_mode_active = True
                self.current_max_positions = self._chop_max_pos
            else:
                self.is_chop_mode_active = False
                self.current_max_positions = int(os.getenv("RBOT_MAX_POSITIONS", "3"))
                
        except Exception as _btc_err:
            pass  # fail open, maintain current state

    # ── Startup verification ─────────────────────────────────────────────────

    def print_startup_banner(self) -> None:
        """Print verified broker state at startup. Does NOT use cached values."""
        print("\n" + "=" * 60)
        print("  RBOTZILLA COINBASE CRYPTO — LIVE ENGINE")
        print("=" * 60)
        try:
            info = self.connector.get_account_info()
            trades = self.connector.get_trades()
            print(f"  Environment   : {os.getenv('OANDA_ENVIRONMENT', 'practice')}")
            print(f"  Endpoint      : {self.connector.api_base}")
            print(f"  Account ID    : {self.connector.account_id}")
            print(f"  Balance       : ${info.balance:,.2f}")
            print(f"  Margin Used   : ${info.margin_used:,.2f}")
            print(f"  Broker Trades : {len(trades)}")
            print(f"  OCO Enforced  : YES (SL+TP+TS mandatory on all orders)")
            print(f"  Pairs Scanning: {len(TRADING_PAIRS)}")
            print(f"  Max Positions : {MAX_POSITIONS}")
            print(f"  Min Confidence: {MIN_CONFIDENCE:.0%}")
        except Exception as e:
            print(f"  WARNING: startup broker query failed: {e}")
        print("=" * 60 + "\n")

        log_event(ENGINE_STARTED, symbol="SYSTEM", venue="startup", details={
            "account_id":   self.connector.account_id,
            "endpoint":     self.connector.api_base,
            "pairs_count":  len(TRADING_PAIRS),
            "max_positions": MAX_POSITIONS,
        })

    # ── Broker dedup ─────────────────────────────────────────────────────────

    def _symbol_is_active(self, symbol: str) -> bool:
        """Return True if symbol already has an open position (local or broker)."""
        for pos in self.active_positions.values():
            if pos.get("symbol") == symbol:
                return True
        try:
            for t in (self.connector.get_trades() or []):
                if t.get("instrument") == symbol:
                    return True
        except Exception:
            pass
        return False

    # ── Single scan cycle ────────────────────────────────────────────────────

    async def _run_scan_cycle(self) -> int:
        """
        One full scan cycle.
        Returns: number of trades successfully placed.
        """
        # ── Live broker position count + full sync to active_positions ─────────
        try:
            broker_trades = self.connector.get_trades() or []
            broker_open   = len(broker_trades)
            # Rebuild broker truth: {trade_id: instrument}
            broker_by_id  = {t.get("id", t.get("tradeID", "")): t.get("instrument", "") for t in broker_trades}
            broker_symbols = set(broker_by_id.values())

            # Remove local positions no longer in broker
            stale = [tid for tid in list(self.active_positions) if tid not in broker_by_id]
            for tid in stale:
                self.active_positions.pop(tid, None)

            # Add broker positions not yet tracked locally
            for tid, instrument in broker_by_id.items():
                if tid and tid not in self.active_positions:
                    self.active_positions[tid] = {"symbol": instrument, "synced_from_broker": True}
        except Exception:
            broker_open   = len(self.active_positions)
            broker_symbols = set()

        slots_left  = max(0, self.current_max_positions - broker_open)
        cycle_limit = min(slots_left, MAX_NEW_PER_CYCLE)

        _mode_str = "[CHOP MODE]" if getattr(self, "is_chop_mode_active", False) else "[SNIPER MODE]"

        if cycle_limit == 0:
            # ── Positions full: show managed trade summary instead of bare line ──
            managed_summary = []
            for t in broker_trades:
                _tid = str(t.get("id") or t.get("tradeID") or "")
                _inst = str(t.get("instrument") or "")
                _units = float(t.get("currentUnits") or t.get("initialUnits") or 0)
                _dir = "LONG" if _units > 0 else "SHORT"
                _upnl = float(t.get("unrealizedPL") or 0)
                managed_summary.append(f"{_inst} {_dir} ${_upnl:+.2f}")
            _summary_str = " | ".join(managed_summary) if managed_summary else "syncing..."
            print(f"\n  {_mode_str} Positions full ({broker_open}/{self.current_max_positions}) — managing active trades")
            print(f"  📊 {_summary_str}")
            return 0

        # Slots available — print scan header
        print(f"\n{_mode_str} Slots open ({slots_left}/{self.current_max_positions}) — scanning {len(TRADING_PAIRS)} pairs...")

        # ── ATTACH_ONLY hard block ─────────────────────────────────────────────
        if ATTACH_ONLY or DISABLE_NEW_ENTRIES:
            log_event(
                ATTACH_ONLY_BLOCK, symbol="SYSTEM", venue="engine",
                details={
                    "reason":               "ATTACH_ONLY mode active — new trade entries disabled",
                    "attach_only_flag":     ATTACH_ONLY,
                    "disable_entries_flag": DISABLE_NEW_ENTRIES,
                    "broker_open":          broker_open,
                    "slots_left":           slots_left,
                },
            )
            print(f"  [ATTACH_ONLY]  broker_open={broker_open}  no new entries this cycle")
            return 0

        # ── Live account for margin gate ──────────────────────────────────────
        try:
            acct         = self.connector.get_account_info()
            nav          = acct.balance + acct.unrealized_pl
            margin_used  = acct.margin_used
            free_margin  = nav - margin_used
            free_margin_pct = free_margin / nav if nav > 0 else 0.0
        except Exception:
            nav = free_margin_pct = 1.0   # fail-open on NAV query only

        # Collect qualifying signals
        # ── Gap 2 fix: honour pre-market playbook ordering ─────────────────────
        # Non-vetoed playbook symbols are moved to the front of the scan list so
        # the highest-conviction session setups are evaluated first when slots are
        # limited. Symbols not in the playbook remain after, in their default order.
        if self._session_playbook:
            pb_symbols = [
                e.symbol for e in self._session_playbook
                if not e.vetoed and e.symbol in set(TRADING_PAIRS)
            ]
            pb_set = set(pb_symbols)
            scan_order = pb_symbols + [s for s in TRADING_PAIRS if s not in pb_set]
        else:
            scan_order = list(TRADING_PAIRS)

        qualified = []
        for symbol in scan_order:
            try:
                candles = self.connector.get_historical_data(
                    symbol, count=CANDLE_COUNT, granularity=CANDLE_GRANULARITY
                )
                if not candles or len(candles) < 50:
                    continue

                # ── Phase 9: Multi-Strategy Pipeline Scanner ───────────────────
                candidates = []

                # ─ Pipeline 1: Momentum (SMA + EMA + Fib, 2-of-3, H4-confirmed) ─
                mom = run_momentum_pipeline(symbol, candles, min_confidence=MIN_CONFIDENCE)
                if mom and getattr(mom, 'signal_type', '') == 'trend':
                    try:
                        candles_h4 = self.connector.get_historical_data(symbol, count=100, granularity="H4")
                        closes_h4 = [float(c.get("mid", {}).get("c", 0)) for c in candles_h4]
                        if len(closes_h4) >= 55:
                            k = 2.0 / (56.0)
                            ema_h4 = sum(closes_h4[:55]) / 55.0
                            for px in closes_h4[55:]:
                                ema_h4 = (px - ema_h4) * k + ema_h4
                            price_h4 = closes_h4[-1]
                            if mom.direction == "BUY" and price_h4 < ema_h4:
                                mom.confidence -= 0.15
                                print(f"  [MTF_SNIPER] {symbol} MOMENTUM BUY scored -15% — H4 BEARISH")
                            elif mom.direction == "SELL" and price_h4 > ema_h4:
                                mom.confidence -= 0.15
                                print(f"  [MTF_SNIPER] {symbol} MOMENTUM SELL scored -15% — H4 BULLISH")
                            if mom:
                                mom._timeframe = "M15+H4"
                    except Exception:
                        pass
                if mom:
                    candidates.append(mom)

                # ─ Pipeline 2: Reversal (Trap + LiqSweep + RSI, 1-of-3) ────────
                rev = run_reversal_pipeline(symbol, candles)
                if rev:
                    candidates.append(rev)

                # ─ Pipeline 3: Mean Reversion (BB + S&D + RSI, 1-of-3) ─────────
                mr = run_meanrev_pipeline(symbol, candles)
                if mr:
                    candidates.append(mr)

                # ─ Pipeline 4: FVG Scalp (FVG + OrderBlock, 1-of-2) ───────────
                sc = run_scalp_pipeline(symbol, candles)
                if sc:
                    candidates.append(sc)

                # ── Volume Confirmation Gate ─────────────────────────────────
                if VOLUME_GATE_ENABLED and candidates:
                    try:
                        _vols = [float(c.get("volume", 0)) for c in candles[-20:]]
                        if len(_vols) >= 20 and _vols[-1] > 0:
                            _avg_vol = sum(_vols[:-1]) / len(_vols[:-1])
                            if _avg_vol > 0 and _vols[-1] < _avg_vol * VOLUME_GATE_MULT:
                                for _cs in candidates:
                                    _cs.confidence -= 0.10
                                    print(f"  [VOL_GATE] {symbol} {_cs.direction} penalizing confidence -10% — vol {_vols[-1]:.0f} < {_avg_vol * VOLUME_GATE_MULT:.0f} (1.2x avg)")
                    except Exception:
                        pass

                # ── RSI Overbought/Oversold Gate ──────────────────────────────
                if RSI_GATE_ENABLED and candidates:
                    _cls_rsi = [float(c.get("mid", {}).get("c", 0)) for c in candles[-15:]]
                    if len(_cls_rsi) >= 15:
                        _gains = [max(_cls_rsi[i] - _cls_rsi[i-1], 0) for i in range(1, len(_cls_rsi))]
                        _losses = [max(_cls_rsi[i-1] - _cls_rsi[i], 0) for i in range(1, len(_cls_rsi))]
                        _avg_gain = sum(_gains) / 14.0
                        _avg_loss = sum(_losses) / 14.0
                        if _avg_loss > 0:
                            _rs = _avg_gain / _avg_loss
                            _rsi_val = 100.0 - (100.0 / (1.0 + _rs))
                        else:
                            _rsi_val = 100.0
                        for _cs in candidates:
                            if _rsi_val >= RSI_OB_LEVEL and _cs.direction == "BUY":
                                _cs.confidence -= 0.20
                                print(f"  [RSI_GATE] {symbol} {_cs.direction} penalizing confidence -20% — RSI overbought/oversold")
                            elif _rsi_val <= RSI_OS_LEVEL and _cs.direction == "SELL":
                                _cs.confidence -= 0.20
                                print(f"  [RSI_GATE] {symbol} {_cs.direction} penalizing confidence -20% — RSI overbought/oversold")

                # ── Penalty cap: max -20% total ──────────────────────────────
                if candidates:
                    for _cs in candidates:
                        _start_conf = getattr(_cs, '_pre_penalty_conf', _cs.confidence)
                        if not hasattr(_cs, '_pre_penalty_conf'):
                            _cs._pre_penalty_conf = _cs.confidence

                # ─ Pick best signal for this pair ─────────────────────────────
                if candidates:
                    candidates = [c for c in candidates if c.confidence >= MIN_CONFIDENCE]
                    if candidates:
                        best = max(candidates, key=lambda s: s.confidence)
                        if not hasattr(best, '_timeframe'):
                            best._timeframe = "M15"
                        if not hasattr(best, '_strategy'):
                            best._strategy = getattr(best, 'signal_type', 'trend')
                        qualified.append(best)

                # ─ Per-pair scan diagnostic line (matches OANDA output) ────────
                def _pfmt(sig, label):
                    if sig is None:
                        return f"{label}=✗"
                    return f"{label}={sig.confidence:.0%}✓"

                tag = ""
                plain = ""
                if candidates:
                    best_sig = max(candidates, key=lambda s: s.confidence)
                    best_strat = getattr(best_sig, '_strategy', '?')
                    dir_word = best_sig.direction
                    strat_desc = {
                        "momentum":       "Strong trend detected",
                        "reversal":       "Reversal pattern spotted",
                        "mean_reversion": "Price stretched, snap-back expected",
                        "scalp":          "Quick entry opportunity found",
                    }.get(best_strat.lower(), "Signal detected")
                    tag   = f"  → QUEUED [{best_strat.upper()}]"
                    plain = f"  💬 {symbol}: {strat_desc} ({best_sig.confidence:.0%} confident) — queuing a {dir_word}"
                print(
                    f"  [SCAN] {symbol:<10}"
                    f"  MOM={_pfmt(mom, 'MOM')[4:]}"
                    f"  REV={_pfmt(rev, 'REV')[4:]}"
                    f"  MR={_pfmt(mr, 'MR')[3:]}"
                    f"  SC={_pfmt(sc, 'SC')[3:]}"
                    f"{tag}"
                )
                if plain:
                    print(plain)

            except Exception as _scan_err:
                import traceback
                print(f"  [SCAN_ERR] {symbol}: {_scan_err}")
                traceback.print_exc()
                continue  # Never let a single pair crash the scan loop

        qualified.sort(key=lambda s: s.confidence, reverse=True)

        log_event(SIGNAL_SCAN_COMPLETE, symbol="SYSTEM", venue="signal_scan", details={
            "pairs_scanned":    len(TRADING_PAIRS),
            "candidates_found": len(qualified),
            "cycle_limit":      cycle_limit,
            "open_slots":       slots_left,
        })

        # ── Placement loop ────────────────────────────────────────────────────
        placed_this_cycle: set = set()
        placed_count = 0

        for sig in qualified[:cycle_limit]:
            symbol = sig.symbol

            # ── LONG_ONLY_MODE Switch (Spot Protection) ────────────────────
            # Prevents Spot trades from executing Shorts which would sell user held funds.
            # Futures contracts ('-PERP' or '-FUT') are exempt and naturally allow shorting.
            if os.getenv("LONG_ONLY_MODE", "True").lower() in ("true", "1", "yes"):
                is_futures = "-PERP" in symbol.upper() or "-FUT" in symbol.upper()
                if sig.direction == "SELL" and not is_futures:
                    print(f"  BLOCKED    {symbol} — LONG_ONLY_MODE (Shorting disabled for Spot)")
                    continue

            # ── Dedup: broker symbols + local + this cycle ─────────────────
            if (symbol.upper() in placed_this_cycle
                    or symbol in broker_symbols
                    or self._symbol_is_active(symbol)):

                log_gate_block(symbol, SYMBOL_ALREADY_ACTIVE_BLOCK, {"symbol": symbol})
                continue

            # ── Margin gate (live NAV) ──────────────────────────────────────
            if free_margin_pct < MIN_FREE_MARGIN_PCT:
                log_gate_block(symbol, MARGIN_GATE_BLOCKED, {
                    "free_margin_pct": round(free_margin_pct, 3),
                    "min_required":    MIN_FREE_MARGIN_PCT,
                })
                print(f"  BLOCKED    {symbol} — MARGIN_GATE_BLOCKED free={free_margin_pct:.1%}")
                continue   # margin tight for this symbol — try next

            # ── Correlation gate: no same-currency same-direction double-up ──
            if self._would_create_correlated_exposure(symbol, sig.direction):
                print(
                    f"  BLOCKED    {symbol} — CORRELATION_GATE "
                    f"({sig.direction} on same currency already open)"
                )
                continue

            # ── Phase 1: CANDIDATE_FOUND ───────────────────────────────────
            log_event(CANDIDATE_FOUND, symbol=symbol, venue="signal_scan", details={
                "symbol":     symbol,
                "direction":  sig.direction,
                "confidence": round(sig.confidence, 4),
                "votes":      sig.votes,
                "detectors":  sig.detectors_fired,
                "session":    sig.session,
            })
            print(
                f"  CANDIDATE  {symbol} {sig.direction} "
                f"conf={sig.confidence:.1%} ({sig.votes}v)"
            )

            # ── Phase 2: broker tradability gate ──────────────────────────
            gate = check_broker_tradability(
                self.connector, symbol,
                placed_this_cycle=placed_this_cycle,
            )
            if not gate["allowed"]:
                log_gate_block(symbol, gate["event"], gate["detail"])
                print(f"  BLOCKED    {symbol} — {gate['event']} {gate['detail']}")
                continue

            # Live mid-price from gate — used as entry_price for notional calc
            # (MARKET orders have no submitted price; Charter needs a real number)
            live_mid = (gate.get("live_price") or {}).get("mid") or 0.0

            # ── Anti-churn gate: no immediate same-pair re-entry / flip ──────
            churn_reason = self._pair_cooldown_reason(symbol, sig.direction)
            if churn_reason:
                print(f"  BLOCKED    {symbol} — {churn_reason}")
                continue

            sig = self._enforce_rr_buffer(symbol, sig, live_mid)

            # ── Phase 3: ORDER_SUBMIT_ALLOWED ─────────────────────────────
            log_event(ORDER_SUBMIT_ALLOWED, symbol=symbol, venue="tradability_gate", details={
                "symbol":     symbol,
                "direction":  sig.direction,
                "confidence": round(sig.confidence, 4),
            })
            print(f"  → Placing  {symbol} {sig.direction} conf={sig.confidence:.1%}")

            # ── Phoenix-mode: fixed pip SL/TP override ──────────────────────────
            # Replaces signal's variable SL/TP with exact pip-equivalent values.
            # Crypto adaptation: pip = 0.1% of price (not fixed forex pip).
            if self._sl_pips > 0 and live_mid:
                _strategy  = getattr(sig, '_strategy',  getattr(sig, 'signal_type', 'trend')).lower()
                
                # Default to env-based sizing
                _trade_sl_pips = self._sl_pips
                _trade_tp_pips = self._tp_pips
                
                if any(x in _strategy for x in ["reversal", "mean_rev", "scalp", "yt_macd"]):
                    _trade_sl_pips = 12
                    _trade_tp_pips = 24
                    print(f"  [STRATEGY EXIT] {_strategy} detected — using tighter {_trade_sl_pips}/{_trade_tp_pips} exits")
                else:
                    print(f"  [STRATEGY EXIT] {_strategy} detected — using standard {_trade_sl_pips}/{_trade_tp_pips} exits")

                _pip = live_mid * 0.001   # crypto: 0.1% of price per pip-equiv
                _sl_dist = _trade_sl_pips * _pip
                _tp_dist = _trade_tp_pips * _pip
                if sig.direction == "BUY":
                    sig.sl = round(live_mid - _sl_dist, 5)
                    sig.tp = round(live_mid + _tp_dist, 5)
                else:
                    sig.sl = round(live_mid + _sl_dist, 5)
                    sig.tp = round(live_mid - _tp_dist, 5)

            # ── Phase 4: OCO payload validation ───────────────────────────
            units = self._compute_units(symbol, sig, nav)
            # Convert USD-based base_units to fractional crypto quantity
            if live_mid > 0.0:
                units = units / live_mid
            units = self._apply_min_notional_floor(symbol, units, live_mid)
            oco_check = validate_oco_payload(
                symbol=symbol,
                direction=sig.direction,
                entry_price=live_mid,
                stop_loss=sig.sl,
                take_profit=sig.tp,
                units=units,
            )
            if not oco_check["valid"]:
                log_gate_block(symbol, OCO_VALIDATION_BLOCK, oco_check)
                print(f"  BLOCKED    {symbol} — OCO_VALIDATION_BLOCK {oco_check['reason']}")
                set_cooldown(symbol)  # avoid retrying a structurally failing pair every cycle
                continue

            # ── Phase 5: place OCO order ───────────────────────────────────
            try:
                # Trailing stop distance: floor at 0.5% of price, buffer at 2x
                # to prevent rejection from distances too close to current price.
                min_ts_dist = live_mid * 0.005
                raw_sl_dist = abs(live_mid - sig.sl)
                ts_dist = max(raw_sl_dist, min_ts_dist * 2)

                result = self.connector.place_oco_order(
                    instrument=symbol,
                    entry_price=live_mid,
                    stop_loss=sig.sl,
                    take_profit=sig.tp,
                    units=units,
                    order_type="MARKET",
                    trailing_stop_distance=ts_dist,
                )

                # ── Phase 6: verify broker response ───────────────────────
                confirm = check_submit_response(result, symbol)
                
                # Fallback: If broker said success=True but parsing failed to find trade_id
                if not confirm.get("confirmed") and result.get("success") and (result.get("live_api") or result.get("visible_in_oanda", True)):
                    import time
                    for _ in range(4):
                        time.sleep(1.0)  # Wait for LIMIT order cross
                        try:
                            trades = self.connector.get_trades()
                            matching = [t for t in trades if t.get("instrument") == symbol]
                            if matching:
                                newest = max(matching, key=lambda x: int(x.get("id", 0)))
                                confirm["confirmed"] = True
                                confirm["trade_id"] = str(newest.get("id"))
                                break
                        except Exception:
                            pass

                if not confirm.get("confirmed"):
                    log_event(ORDER_SUBMIT_BLOCK, symbol=symbol, venue="coinbase", details={
                        "symbol": symbol, "error": confirm.get("error", "unknown")
                    })
                    print(f"  ✗ REJECTED {symbol} — {confirm.get('error', 'unknown')}")
                    continue

                trade_id = confirm["trade_id"]
                set_cooldown(symbol)
                placed_this_cycle.add(symbol.upper())
                self.active_positions[trade_id] = {
                    "symbol":      symbol,
                    "direction":   sig.direction,
                    "stop_loss":   sig.sl,
                    "take_profit": sig.tp,
                    "confidence":  sig.confidence,
                    "session":     sig.session,
                    "opened_at":   datetime.now(timezone.utc).isoformat(),
                    "stale_cycles": 0,  # stagnation counter
                }
                log_trade_opened(
                    symbol=symbol, direction=sig.direction, trade_id=trade_id,
                    entry=result.get("entry_price", live_mid),
                    stop_loss=sig.sl, take_profit=sig.tp,
                    size=units,
                    confidence=sig.confidence, votes=sig.votes,
                    detectors=sig.detectors_fired, session=sig.session,
                )
                placed_count += 1
                self._mark_pair_trade(symbol, sig.direction)
                print(f"  ✓ OPENED   {symbol} trade_id={trade_id}")

                # ── Hedge counter-trade deleted (Crypto pairs are highly correlated) ────

            except Exception as e:
                log_event(TRADE_OPEN_FAILED, symbol=symbol, venue="coinbase", details={
                    "symbol": symbol, "error": str(e)
                })
                print(f"  ✗ ERROR    {symbol} — {e}")

        # ── Gap 1 fix: CapitalRouter reallocation ──────────────────────────────
        # Runs ONLY when all position slots are full AND a candidate is genuinely
        # stronger than the weakest open position (controlled by UPGRADE_THRESHOLD).
        # One reallocation max per cycle. Passes through full OCO validation gate.
        if (
            self._router
            and qualified
            and not ATTACH_ONLY
            and not DISABLE_NEW_ENTRIES
        ):
            self._router.reset_cycle()
            try:
                acct_info = {"NAV": nav, "balance": nav}
                realloc = self._router.evaluate(
                    open_positions=self.active_positions,
                    candidates=qualified,
                    account_info=acct_info,
                )
            except Exception as _re:
                realloc = None
                print(f"  [ROUTER] evaluate() error: {_re}")

            if realloc:
                _rs = realloc.close_symbol
                _rt = realloc.close_trade_id
                log_event(CAPITAL_REALLOC_DECIDED, symbol=_rs, venue="capital_router",
                          details=realloc.as_dict())
                print(
                    f"  [ROUTER] REALLOC  close {_rs}({_rt[:6]}) "
                    f"→ open {realloc.open_symbol} {realloc.open_direction} "
                    f"({realloc.improvement_pct:.1%} improvement)"
                )

                # Step A: close the weak position
                try:
                    self.connector.close_trade(_rt)
                    self.active_positions.pop(_rt, None)
                except Exception as _ce:
                    log_event(CAPITAL_REALLOC_FAILED, symbol=_rs, venue="capital_router",
                              details={"step": "close", "error": str(_ce)})
                    print(f"  [ROUTER] ⚠️  Close failed for {_rs}: {_ce}")
                    realloc = None  # abort — do not open without closing

            if realloc:
                # Step B: find the matching signal from this cycle's qualified list
                _open_sig = next(
                    (s for s in qualified
                     if s.symbol == realloc.open_symbol
                     and s.direction == realloc.open_direction),
                    None,
                )
                if _open_sig and _open_sig.symbol not in placed_this_cycle:
                    _open_sym = _open_sig.symbol
                    # Re-run margin gate with fresh account state
                    if free_margin_pct < MIN_FREE_MARGIN_PCT:
                        log_event(CAPITAL_REALLOC_FAILED, symbol=_open_sym,
                                  venue="capital_router",
                                  details={"step": "open", "reason": "margin_gate"})
                        print(f"  [ROUTER] ⚠️  Realloc blocked — margin gate")
                    else:
                        # OCO validation — fresh gate on the replacement symbol
                        _realloc_gate = check_broker_tradability(
                            self.connector, _open_sym,
                            placed_this_cycle=placed_this_cycle,
                        )
                        _live_mid = (_realloc_gate.get("live_price") or {}).get("mid") or 0.0
                        _oco_check = validate_oco_payload(
                            symbol=_open_sym,
                            direction=_open_sig.direction,
                            entry_price=_live_mid,
                            stop_loss=_open_sig.sl,
                            take_profit=_open_sig.tp,
                            units=self._compute_units(_open_sym, _open_sig, nav),
                        )
                        if not _realloc_gate["allowed"] or not _oco_check["valid"]:
                            _reason = (
                                _realloc_gate.get("event", "gate_block")
                                if not _realloc_gate["allowed"]
                                else _oco_check.get("reason", "oco_invalid")
                            )
                            log_event(CAPITAL_REALLOC_FAILED, symbol=_open_sym,
                                      venue="capital_router",
                                      details={"step": "open", "reason": _reason})
                            print(f"  [ROUTER] ⚠️  Realloc open blocked: {_reason}")
                        else:
                            try:
                                _open_sig = self._enforce_rr_buffer(_open_sym, _open_sig, _live_mid)
                                _units = self._compute_units(_open_sym, _open_sig, nav)
                                _units = self._apply_min_notional_floor(_open_sym, _units, _live_mid)
                                _min_ts = _live_mid * 0.005
                                _ts_dist = max(abs(_live_mid - _open_sig.sl), _min_ts * 2)
                                _res = self.connector.place_oco_order(
                                    instrument=_open_sym,
                                    entry_price=_live_mid,
                                    stop_loss=_open_sig.sl,
                                    take_profit=_open_sig.tp,
                                    units=_units,
                                    order_type="MARKET",
                                    trailing_stop_distance=_ts_dist,
                                )
                                _conf = check_submit_response(_res, _open_sym)
                                if _conf.get("confirmed"):
                                    _tid = _conf["trade_id"]
                                    set_cooldown(_open_sym)
                                    placed_this_cycle.add(_open_sym.upper())
                                    self.active_positions[_tid] = {
                                        "symbol":      _open_sym,
                                        "direction":   _open_sig.direction,
                                        "stop_loss":   _open_sig.sl,
                                        "take_profit": _open_sig.tp,
                                        "confidence":  _open_sig.confidence,
                                        "session":     _open_sig.session,
                                        "opened_at":   datetime.now(timezone.utc).isoformat(),
                                        "stale_cycles": 0,
                                    }
                                    log_trade_opened(
                                        symbol=_open_sym, direction=_open_sig.direction,
                                        trade_id=_tid,
                                        entry=_res.get("entry_price", _live_mid),
                                        stop_loss=_open_sig.sl, take_profit=_open_sig.tp,
                                        size=_units, confidence=_open_sig.confidence,
                                        votes=_open_sig.votes,
                                        detectors=_open_sig.detectors_fired,
                                        session=_open_sig.session,
                                    )
                                    placed_count += 1
                                    self._mark_pair_trade(_open_sym, _open_sig.direction)
                                    print(f"  [ROUTER] ✓ REALLOC OPENED {_open_sym} id={_tid}")
                                else:
                                    log_event(CAPITAL_REALLOC_FAILED, symbol=_open_sym,
                                              venue="capital_router",
                                              details={"step": "open",
                                                       "error": _conf.get("error", "unknown")})
                                    print(f"  [ROUTER] ✗ Realloc open rejected: {_conf.get('error')}")
                            except Exception as _oe:
                                log_event(CAPITAL_REALLOC_FAILED, symbol=_open_sym,
                                          venue="capital_router",
                                          details={"step": "open", "error": str(_oe)})
                                print(f"  [ROUTER] ✗ Realloc open error: {_oe}")

        return placed_count

    def _pair_cooldown_reason(self, symbol: str, direction: str) -> Optional[str]:
        now = datetime.now(timezone.utc).timestamp()
        last_ts = self._pair_last_trade_ts.get(symbol)
        last_side = self._pair_last_side.get(symbol)
        if last_ts is not None:
            elapsed = now - last_ts
            cooldown = PAIR_REENTRY_COOLDOWN_MINUTES * 60
            if elapsed < cooldown:
                remain_sec = cooldown - elapsed
                remain_min = remain_sec / 60.0
                pct_hour = (remain_min / 60.0) * 100.0
                return f"PAIR_COOLDOWN_ACTIVE last_side={last_side} wait={remain_min:.1f}m ({pct_hour:.0f}% of hour)"

        for pos in self.active_positions.values():
            if str(pos.get("symbol", "")).upper() == symbol.upper():
                open_side = str(pos.get("direction", ""))
                return f"PAIR_ALREADY_OPEN open_side={open_side}"

        try:
            broker_trades = self.connector.get_trades() or []
            for t in broker_trades:
                inst = str(t.get("instrument") or "")
                units = float(t.get("currentUnits") or t.get("initialUnits") or 0)
                side = "BUY" if units > 0 else "SELL" if units < 0 else ""
                if inst.upper() == symbol.upper() and side:
                    return f"PAIR_ALREADY_OPEN open_side={side}"
        except Exception:
            pass

        return None

    def _load_cooldown_state(self) -> None:
        """Restore pair cooldown timestamps from disk (survives restarts)."""
        import json
        try:
            if self._cooldown_persist_path.exists():
                raw = json.loads(self._cooldown_persist_path.read_text())
                ts_map  = raw.get("ts", {})
                side_map = raw.get("side", {})
                self._pair_last_trade_ts.update({k: float(v) for k, v in ts_map.items()})
                self._pair_last_side.update(side_map)
                print(f"  ✅ Cooldown state restored ({len(ts_map)} pairs) from {self._cooldown_persist_path}")
        except Exception as _e:
            print(f"  ⚠️  Cooldown restore failed (starting fresh): {_e}")

    def _save_cooldown_state(self) -> None:
        """Persist pair cooldown timestamps to disk so restarts honour existing cooldowns."""
        import json
        try:
            payload = {
                "ts":   {k: v for k, v in self._pair_last_trade_ts.items()},
                "side": {k: v for k, v in self._pair_last_side.items()},
            }
            self._cooldown_persist_path.write_text(json.dumps(payload, indent=2))
        except Exception as _e:
            print(f"  ⚠️  Cooldown save failed: {_e}")

    def _mark_pair_trade(self, symbol: str, direction: str) -> None:
        self._pair_last_trade_ts[symbol] = datetime.now(timezone.utc).timestamp()
        self._pair_last_side[symbol] = direction
        self._save_cooldown_state()  # persist so restarts honour this cooldown

    def _would_create_correlated_exposure(self, symbol: str, direction: str) -> bool:
        """
        Return True if opening symbol+direction would double up on the same
        BASE currency in the same direction as an existing open position.
        For crypto (all XXX-USD), only base overlap matters — quote is always USD.
        """
        if "-" not in symbol:
            return False
        new_base = symbol.split("-")[0]
        for pos in self.active_positions.values():
            s = pos.get("symbol", "")
            d = pos.get("direction", "")
            if "-" not in s or d != direction:
                continue
            b = s.split("-")[0]
            if b == new_base:
                return True
        return False

    def _apply_min_notional_floor(self, symbol: str, units: float, live_mid: float) -> float:
        """
        Enforce buffered Charter notional using broker USD-notional math.
        Crypto version: Uses pure float math, never casts to int.
        """
        try:
            px = float(live_mid or 0.0)
        except Exception:
            px = 0.0
        if px <= 0:
            return float(units)

        side = 1.0 if float(units) >= 0 else -1.0
        # For cross-margin scaling, don't use max(1). Use actual fractional crypto limits if needed.
        abs_units = abs(float(units))
        target = float(CHARTER_TARGET_NOTIONAL_USD)

        def usd_notional_for(test_units: float) -> float:
            try:
                if hasattr(self.connector, "get_usd_notional"):
                    return float(self.connector.get_usd_notional(test_units, symbol, px))
            except Exception:
                pass
            try:
                from brokers.coinbase_connector import CoinbaseConnector
                return float(abs(test_units) * px)
            except Exception:
                pass
            base = (symbol or "").split("-")[0].upper()
            if base == "USD":
                return float(abs(test_units))
            return float(abs(test_units) * px)
            
        # Target sizing by dollar value directly since px is accurate
        required_units = float(target / px) if px > 0 else abs_units
        cur = max(abs_units, required_units)
        
        # Round to 5 decimal places for typical crypto precision
        return round(cur * side, 5)

    def _enforce_rr_buffer(self, symbol: str, sig, entry_price: float):
        """
        Push TP slightly farther so broker-side / Charter-side rounding cannot reject
        an exactly-3.20 setup. Keeps SL unchanged, only widens TP modestly.
        """
        try:
            entry = float(entry_price or 0.0)
            sl = float(sig.sl or 0.0)
            tp = float(sig.tp or 0.0)
        except Exception:
            return sig
        if entry <= 0 or sl <= 0 or tp <= 0:
            return sig

        side = str(sig.direction).upper()
        if side == "BUY":
            risk = entry - sl
            if risk > 0:
                min_tp = entry + (risk * CHARTER_MIN_RR)
                if tp < min_tp:
                    sig.tp = round(min_tp, 5)
        elif side == "SELL":
            risk = sl - entry
            if risk > 0:
                min_tp = entry - (risk * CHARTER_MIN_RR)
                if tp > min_tp:
                    sig.tp = round(min_tp, 5)
        return sig


    def _compute_units(self, symbol: str, sig: AggregatedSignal, nav: float = 0.0) -> float:
        """
        Sizing stack:
        1) start from RBOT_BASE_UNITS
        2) apply watermark-based compounding
        3) enforce Charter notional floor with broker USD-notional math
        """
        base_units = float(os.getenv("RBOT_BASE_UNITS", "2.0"))
        if getattr(self, "is_chop_mode_active", False):
            base_units = float(getattr(self, "_chop_units", base_units))
        growth_exponent = float(os.getenv("RBOT_COMPOUND_GROWTH_EXPONENT", "1.15"))
        drawdown_floor_ratio = float(os.getenv("RBOT_COMPOUND_DRAWDOWN_FLOOR_RATIO", "1.00"))
        max_growth_multiple = float(os.getenv("RBOT_COMPOUND_MAX_GROWTH_MULTIPLE", "3.00"))

        scaled = base_units
        if nav > 0 and self._initial_nav > 0:
            scaled = compute_watermark_compounded_units(
                base_units=base_units,
                current_nav=nav,
                initial_nav=self._initial_nav,
                watermark_nav=(self._watermark_nav or self._initial_nav),
                growth_exponent=growth_exponent,
                drawdown_floor_ratio=drawdown_floor_ratio,
                max_growth_multiple=max_growth_multiple,
            )

        signed_units = scaled if sig.direction == "BUY" else -scaled

        # Price division + notional floor now handled in placement loop
        # using the gate's trusted live_mid (avoids silent 0-price from rate limits)

        # ── Apply Configured Leverage Scaling ──────────────────────────────
        # Only scales units if it's a futures contract (PERP/FUT). Spot is un-leveraged.
        is_futures = "-PERP" in symbol.upper() or "-FUT" in symbol.upper()
        
        if is_futures:
            if hasattr(sig, 'meta') and sig.meta.get("is_golden_turnaround"):
                leverage = float(os.getenv("CRYPTO_MAX_LEVERAGE_MULTIPLIER", os.getenv("CRYPTO_LEVERAGE_MULTIPLIER", "10.0")))
                print(f"  [GOLDEN TURNAROUND] 🎯 {symbol} — Max Leverage Applied: {leverage}x")
            else:
                leverage = float(os.getenv("CRYPTO_LEVERAGE_MULTIPLIER", "1.0"))
                
            if leverage > 1.0:
                signed_units = signed_units * leverage
            
        return float(signed_units)

    # ── Main loop ────────────────────────────────────────────────────────────

    async def run(self) -> None:
        self.is_running = True
        self.print_startup_banner()

        # Activate TradeManager after is_running = True
        self.manager.activate()

        # ── Capture initial NAV for compound unit scaling ──────────────────────
        try:
            _acct = self.connector.get_account_info()
            self._initial_nav = _acct.balance + _acct.unrealized_pl
            self._watermark_nav = self._initial_nav
            self._router = CapitalRouter(self.connector, initial_nav=self._initial_nav)
            print(f"  ✅ CapitalRouter ACTIVE  initial_nav=${self._initial_nav:,.2f}  watermark=${self._watermark_nav:,.2f}")
        except Exception as _nav_err:
            print(f"  ⚠️  CapitalRouter NAV init failed: {_nav_err} — compound scaling disabled")

        while self.is_running:
            try:
                # ── Pre-market session scan ────────────────────────────────────
                if self.pre_scanner.should_run_now():
                    self._session_playbook = self.pre_scanner.run_scan()
                    if self._session_playbook:
                        active_pb = [e for e in self._session_playbook if not e.vetoed]
                        print(f"  [PLAYBOOK] {len(active_pb)} active setups for upcoming session")

                try:
                    _acct_live = self.connector.get_account_info()
                    _nav_live = _acct_live.balance + _acct_live.unrealized_pl
                    if _nav_live > self._watermark_nav:
                        self._watermark_nav = _nav_live
                except Exception:
                    pass
                    
                self._update_regime_state()

                placed = await self._run_scan_cycle()
                # ── Trail management: runs every cycle regardless of ATTACH_ONLY ─
                await self.manager.tick(engine_positions=self.active_positions)

                open_now = len(self.active_positions)

                if open_now >= MAX_POSITIONS:
                    print(f"  Positions full ({open_now}/{MAX_POSITIONS}) — waiting {SCAN_SLOW_SECONDS}s")
                    await asyncio.sleep(SCAN_SLOW_SECONDS)
                else:
                    print(f"  Slots open ({open_now}/{MAX_POSITIONS}) — rescanning in {SCAN_FAST_SECONDS}s")
                    await asyncio.sleep(SCAN_FAST_SECONDS)

            except KeyboardInterrupt:
                print("\n  Stopping engine…")
                self.is_running = False
                self.manager.deactivate()
                log_event(ENGINE_STOPPED, symbol="SYSTEM", venue="engine", details={
                    "reason": "keyboard_interrupt"
                })
            except Exception as e:
                print(f"  Engine cycle error: {e}")
                await asyncio.sleep(30)


def main():
    engine = TradeEngine()
    try:
        asyncio.run(engine.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
