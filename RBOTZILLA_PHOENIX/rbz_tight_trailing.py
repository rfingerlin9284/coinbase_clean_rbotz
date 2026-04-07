
# ============================================================
# file: rbz_tight_trailing.py   (DROP-IN, CLEAN OVERWRITE)
# Purpose: Tight Two-Step Stop + Aggressive Trailing + TP Guard
# ============================================================
from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Any, Dict, Optional, Callable, Set

# ---------------------------
# Charter override (keeps min-notional; disables TP-PnL gating)
# ---------------------------
@dataclass
class CharterConfig:
    min_notional_usd: float = 10_000.0
    enforce_min_expected_pnl: bool = False
    min_expected_pnl_usd: float = 35.0

def _notional(price: float, units: float) -> float:
    return abs(float(price) * float(units))

def charter_validate_override(
    *, symbol: str, side: str, price: float, sl: Optional[float],
    tp: Optional[float], units: float, cfg: CharterConfig,
    log: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    def _log(msg: str) -> None:
        if log:
            try: log(msg)
            except Exception: pass
    nom = _notional(price, units)
    if nom < cfg.min_notional_usd:
        _log(f"❌ ORDER REJECTED: Charter requires ≥ ${cfg.min_notional_usd:,.0f} notional (got ${nom:,.2f})")
        return {"allowed": False, "reason": "NOTIONAL_BELOW_MIN", "notional": nom, "min_notional": cfg.min_notional_usd}
    if cfg.enforce_min_expected_pnl and tp is not None:
        exp = (float(tp) - float(price)) * (1 if side.upper()=="BUY" else -1) * float(units)
        if exp < cfg.min_expected_pnl_usd:
            _log(f"WARNING: Expected PnL ${exp:.2f} < min ${cfg.min_expected_pnl_usd:.2f}")
            return {"allowed": False, "reason": "EXPECTED_PNL_BELOW_MIN", "expected_pnl": exp}
    return {"allowed": True, "reason": "OK"}

# ---------------------------
# Pair-aware tight Two-Step SL + trail
# ---------------------------
@dataclass
class TightSL:
    step1_trigger_pct: float = 0.0020
    step1_lock_pct:    float = -0.0003
    step2_trigger_pct: float = 0.0040
    trail_trigger_pct: float = 0.0070
    trail_pct:         float = 0.0020

PAIR_CLASS = {
    "EUR_USD":"major","GBP_USD":"major","USD_JPY":"major","USD_CHF":"major",
    "USD_CAD":"major","AUD_USD":"major","NZD_USD":"major",
    "EUR_GBP":"minor","EUR_JPY":"minor","GBP_JPY":"minor","AUD_JPY":"minor","CAD_JPY":"minor",
    "EUR_AUD":"minor","EUR_NZD":"minor","EUR_CAD":"minor","GBP_AUD":"minor","GBP_NZD":"minor",
    "AUD_NZD":"minor","AUD_CAD":"minor","AUD_CHF":"minor","NZD_JPY":"minor","CAD_CHF":"minor",
}
DEFAULTS = {
    # Step1 Trig, Step1 Lock, Step2 Trig, Trail Trig, Trail Pct
    "major":  TightSL(0.0006, 0.00010, 0.0012, 0.0018, 0.0008), # Step1: 6 pips, Step2: 12 pips, Trail: 18 pips
    "minor":  TightSL(0.0008, 0.00015, 0.0015, 0.0022, 0.0010), # Step1: 8 pips, Step2: 15 pips, Trail: 22 pips
    "exotic": TightSL(0.0012, 0.00015, 0.0020, 0.0030, 0.0015), # Step1: 12 pips
}
SCALP_TAGS = {"scalp","micro","hf","intraday_fast"}
SWING_TAGS = {"swing","position","carry","condor","range_swing"}

@dataclass
class StrategyPolicy:
    is_swing: bool
    allow_tp: bool
    mult_step1_trig: float = 1.0
    mult_step1_lock: float = 1.0
    mult_step2_trig: float = 1.0
    mult_trail_trig: float = 1.0
    mult_trail_pct:  float = 1.0

STRATEGY_OVERRIDES = {
    "trap_reversal_scalper": StrategyPolicy(False, False, 0.8, 1.0, 0.9, 0.9, 0.8),
    "liquidity_sweep_scalp": StrategyPolicy(False, False, 0.9, 1.0, 0.9, 0.9, 0.9),
    "wolfpack_ema_trend_scalp": StrategyPolicy(False, False, 1.0, 1.0, 1.0, 0.9, 0.9),
    "fvg_breakout_scalp": StrategyPolicy(False, False, 0.9, 1.0, 0.9, 0.9, 0.9),
    "price_action_holy_grail_scalp": StrategyPolicy(False, False, 0.9, 1.0, 0.9, 0.9, 0.8),

    "holy_grail_swing": StrategyPolicy(True, True, 1.2, 1.0, 1.2, 1.2, 1.3),
    "fvg_breakout_swing": StrategyPolicy(True, True, 1.2, 1.0, 1.2, 1.2, 1.3),
    "institutional_sd_swing": StrategyPolicy(True, True, 1.3, 1.0, 1.3, 1.3, 1.4),
    "iron_condor": StrategyPolicy(True, True, 2.0, 1.0, 2.0, 2.0, 2.0),
}

def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()

def _pair_class(symbol: str) -> str:
    return PAIR_CLASS.get((symbol or "").upper(), "exotic")

def strategy_policy(strategy_name: Optional[str], tags: Optional[Set[str]]) -> StrategyPolicy:
    n = _norm(strategy_name)
    if n in STRATEGY_OVERRIDES:
        return STRATEGY_OVERRIDES[n]
    t = set(_norm(x) for x in (tags or set()))
    if t & SWING_TAGS:
        return StrategyPolicy(True, True)
    if t & SCALP_TAGS:
        return StrategyPolicy(False, False)
    return StrategyPolicy(False, False)

class _T:
    def __init__(self, symbol: str, strategy_name: Optional[str], tags: Optional[Set[str]]):
        self.symbol = symbol; self.strategy_name = strategy_name; self.tags = tags or set()

def policy_for(symbol: str, strategy_name: Optional[str] = None, tags: Optional[Set[str]] = None) -> TightSL:
    base = DEFAULTS[_pair_class(symbol)]
    sp = strategy_policy(strategy_name, tags)
    return TightSL(
        step1_trigger_pct = base.step1_trigger_pct * sp.mult_step1_trig,
        step1_lock_pct    = base.step1_lock_pct    * sp.mult_step1_lock,
        step2_trigger_pct = base.step2_trigger_pct * sp.mult_step2_trig,
        trail_trigger_pct = base.trail_trigger_pct * sp.mult_trail_trig,
        trail_pct         = base.trail_pct         * sp.mult_trail_pct,
    )

def should_allow_tp(strategy_name: Optional[str], tags: Optional[Set[str]] = None) -> bool:
    return bool(strategy_policy(strategy_name, tags).allow_tp)

def tp_guard(strategy_name: Optional[str], tags: Optional[Set[str]] = None, proposed_tp: Optional[float] = None) -> Optional[float]:
    return proposed_tp if should_allow_tp(strategy_name, tags) else None

def _apply_tight_sl(
    *, policy: TightSL, trade: Dict[str, Any], price: float,
    adjust_stop_cb, log
) -> None:
    side   = (trade.get("side") or trade.get("direction") or "").upper()
    symbol = trade.get("symbol") or trade.get("instrument") or "UNKNOWN"
    entry  = float(trade.get("entry") or trade.get("entry_price") or 0.0)
    sl     = float(trade.get("sl") or trade.get("stop_loss") or 0.0)
    meta   = dict(trade.get("meta") or {})
    trade_id = str(trade.get("id") or trade.get("trade_id") or "")

    if not trade_id or not entry or not price:
        return

    changed = False

    if not meta.get("tight_step1", False):
        tgt = entry * (1.0 + policy.step1_trigger_pct) if side=="BUY" else entry * (1.0 - policy.step1_trigger_pct)
        if (side=="BUY" and price >= tgt) or (side=="SELL" and price <= tgt):
            # Ensure Step 1 lock clears spread (minimum 3 pips)
            min_lock_pips = 0.0003 if 'JPY' not in symbol else 0.03
            if side == "BUY":
                new_sl = max(entry * (1.0 + policy.step1_lock_pct), entry + min_lock_pips)
                if new_sl > sl:
                    adjust_stop_cb(trade_id, new_sl); meta["tight_step1"] = True; changed = True
                    log(f"[TightSL] {symbol} STEP1 lock → SL {new_sl:.5f}")
            else:
                new_sl = min(entry * (1.0 - abs(policy.step1_lock_pct)), entry - min_lock_pips)
                if sl == 0.0 or new_sl < sl:
                    adjust_stop_cb(trade_id, new_sl); meta["tight_step1"] = True; changed = True
                    log(f"[TightSL] {symbol} STEP1 lock → SL {new_sl:.5f}")

    if meta.get("tight_step1", False) and not meta.get("tight_step2", False):
        tgt = entry * (1.0 + policy.step2_trigger_pct) if side=="BUY" else entry * (1.0 - policy.step2_trigger_pct)
        if (side=="BUY" and price >= tgt) or (side=="SELL" and price <= tgt):
            lock2_pct = policy.step2_trigger_pct * 0.50
            if side == "BUY":
                new_sl = max(sl, entry * (1.0 + lock2_pct))
            else:
                new_sl = min(sl if sl>0 else entry, entry * (1.0 - lock2_pct))
            
            if (side=="BUY" and new_sl > sl) or (side=="SELL" and (sl == 0.0 or new_sl < sl)):
                adjust_stop_cb(trade_id, new_sl)
                log(f"[TightSL] {symbol} STEP2 breakeven → SL {new_sl:.5f}")
            meta["tight_step2"] = True; changed = True

    if meta.get("tight_step2", False):
        tgt = entry * (1.0 + policy.trail_trigger_pct) if side=="BUY" else entry * (1.0 - policy.trail_trigger_pct)
        if (side=="BUY" and price >= tgt) or (side=="SELL" and price <= tgt):
            if side == "BUY":
                new_sl = max(sl, price * (1.0 - policy.trail_pct))
                if new_sl > sl:
                    adjust_stop_cb(trade_id, new_sl); changed = True
                    log(f"[TightSL] {symbol} TRAIL → SL {new_sl:.5f}")
            else:
                new_sl = min(sl if sl>0 else price, price * (1.0 + policy.trail_pct))
                if sl == 0.0 or new_sl < sl:
                    adjust_stop_cb(trade_id, new_sl); changed = True
                    log(f"[TightSL] {symbol} TRAIL → SL {new_sl:.5f}")

    if changed:
        trade["meta"] = meta

def calibrate_from_atr(policy: TightSL, atr_pct_of_price: float) -> TightSL:
    k = max(0.75, min(1.5, atr_pct_of_price / 0.003))
    return replace(policy,
                   step1_trigger_pct = policy.step1_trigger_pct * k,
                   step2_trigger_pct = policy.step2_trigger_pct * k,
                   trail_trigger_pct = policy.trail_trigger_pct * k,
                   trail_pct         = policy.trail_pct * max(0.8, min(1.2, 1.0 / k)))

def print_policy(symbol: str, strategy_name: Optional[str] = None) -> str:
    pol = policy_for(symbol, strategy_name, None)
    cls = _pair_class(symbol)
    s = (
        f"Policy for {symbol} [{cls}]{' + ' + (strategy_name or '') if strategy_name else ''}\n"
        f"  step1_trigger : {pol.step1_trigger_pct*100:.2f}%\n"
        f"  step1_lock    : {pol.step1_lock_pct*100:.2f}%\n"
        f"  step2_trigger : {pol.step2_trigger_pct*100:.2f}%\n"
        f"  trail_trigger : {pol.trail_trigger_pct*100:.2f}%\n"
        f"  trail_pct     : {pol.trail_pct*100:.2f}%"
    )
    try: print(s)
    except Exception: pass
    return s

def add_console_command(engine: Any) -> None:
    def cmd(argline: str) -> None:
        parts = (argline or "").split()
        if not parts:
            out = "Usage: /policy SYMBOL [STRATEGY_NAME]"
        else:
            sym = parts[0]; strat = " ".join(parts[1:]) if len(parts)>1 else None
            out = print_policy(sym, strat)
        try: engine.display.info("Policy", out)
        except Exception:
            try: print(out)
            except Exception: pass
    for name in ("register_command","add_command","on_command"):
        fn = getattr(engine, name, None)
        if callable(fn):
            try:
                fn("/policy", cmd)
                return
            except Exception:
                continue
    setattr(engine, "cmd_policy", cmd)

def _bind_charter(connector: Any, cfg: CharterConfig) -> None:
    def _log(msg: str) -> None:
        for attr in ("log","info","warning"):
            fn = getattr(connector, attr, None)
            if callable(fn):
                try: fn(msg); return
                except Exception: pass
        try: print(msg)
        except Exception: pass

    def _proxy(*, symbol: str, side: str, price: float, sl: float|None, tp: float|None, units: float) -> Dict[str, Any]:
        return charter_validate_override(symbol=symbol, side=side, price=price, sl=sl, tp=tp, units=units, cfg=cfg, log=_log)
    setattr(connector, "charter_validate", _proxy)

def _wrap_manage(engine: Any) -> None:
    original = getattr(engine, "_manage_trade", None)
    if original is None:
        raise AttributeError("Engine has no _manage_trade to wrap")

    def _log(msg: str) -> None:
        try: engine.display.info("TightSL", msg); return
        except Exception: pass
        try: engine.oanda.log(msg); return
        except Exception: pass
        try: print(msg)
        except Exception: pass

    def _adjust_stop(trade_id: str, new_sl: float) -> None:
        for obj, meth in ((engine.oanda, "adjust_stop"), (engine.connector, "adjust_stop")):
            try:
                fn = getattr(obj, meth, None)
                if callable(fn):
                    fn(trade_id, new_sl)
                    return
            except Exception:
                continue
        _log(f"[TightSL] adjust_stop failed for {trade_id}")

    def wrapper(trade: Dict[str, Any]) -> None:
        try: original(trade)
        except Exception as e: _log(f"[TightSL] legacy _manage_trade error: {e}")

        symbol  = trade.get("symbol") or trade.get("instrument") or "UNKNOWN"
        strat   = trade.get("strategy") or trade.get("strategy_name")
        tags    = set(trade.get("tags") or [])
        policy  = policy_for(symbol, strat, tags)

        try: price = float(engine.oanda.get_price(symbol))
        except Exception:
            price = float(trade.get("price") or trade.get("current") or trade.get("mark") or 0.0)

        try:
            _apply_tight_sl(policy=policy, trade=trade, price=price, adjust_stop_cb=_adjust_stop, log=_log)
        except Exception as e:
            _log(f"[TightSL] enforce error: {e}")

    setattr(engine, "_manage_trade", wrapper)
    add_console_command(engine)

def apply_rbz_overrides(*, connector: Any, engine: Any, charter_cfg: Optional[CharterConfig] = None) -> None:
    _bind_charter(connector, charter_cfg or CharterConfig())
    _wrap_manage(engine)
