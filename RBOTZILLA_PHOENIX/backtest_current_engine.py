#!/usr/bin/env python3
"""
RBOTZILLA PHOENIX — Current Engine Backtest
============================================
Tests the LIVE multi_signal_engine.py (with all current settings) against
real OANDA M15 candle history pulled from the practice API.

What it measures:
  • Signal quality at current thresholds (0.68 conf, 3-vote min)
  • Per-strategy win rate, profit factor, max drawdown
  • Expected value per trade (basis for forward projections)
  • Comparison: old settings (0.62, 2-vote) vs new (0.68, 3-vote)

Run:
  python backtest_current_engine.py

Output:
  backtest_results_YYYYMMDD_HHMMSS.json  + printed summary
"""

import os, sys, json, time, math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple

# ── Load env ────────────────────────────────────────────────────────────────
def _load_env(path=".env"):
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
_load_env()

# ── OANDA candle fetcher ─────────────────────────────────────────────────────
import requests

API_TOKEN = os.getenv("OANDA_API_TOKEN") or os.getenv("OANDA_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")
API_BASE   = os.getenv("OANDA_API_BASE", "https://api-fxpractice.oanda.com")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type":  "application/json",
}

def fetch_candles(symbol: str, count: int = 500, granularity: str = "M15") -> List[dict]:
    """Fetch historical candles from OANDA practice API."""
    try:
        resp = requests.get(
            f"{API_BASE}/v3/instruments/{symbol}/candles",
            headers=HEADERS,
            params={"count": count, "granularity": granularity, "price": "M"},
            timeout=15,
        )
        if resp.status_code != 200:
            print(f"  ⚠  {symbol}: HTTP {resp.status_code}")
            return []
        data = resp.json().get("candles", [])
        # Filter to complete candles only
        return [c for c in data if c.get("complete", False)]
    except Exception as e:
        print(f"  ⚠  {symbol} candle fetch error: {e}")
        return []

# ── Import signal engine ─────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from systems.multi_signal_engine import scan_symbol, AggregatedSignal

# ── Backtest config ──────────────────────────────────────────────────────────
PAIRS = [
    "EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF", "AUD_USD",
    "NZD_USD", "USD_CAD", "EUR_GBP", "EUR_JPY", "GBP_JPY",
    "AUD_JPY", "EUR_AUD", "GBP_AUD", "AUD_CHF", "NZD_CHF",
]

CANDLE_COUNT   = 500           # ~5 days of M15 candles per pair
GRANULARITY    = "M15"
RR_RATIO       = 3.20          # Charter minimum 3.2:1
SPREAD_PIPS    = 1.5           # Conservative spread assumption
STARTING_CAP   = 7600.0        # Current account approximate NAV
RISK_PCT       = 0.015         # 1.5% risk per trade

# Settings comparison: old vs new
CONFIGS = {
    "OLD_0.62_2votes": {"min_confidence": 0.62, "min_votes": 2},
    "NEW_0.68_3votes": {"min_confidence": 0.68, "min_votes": 3},
}

# ── Trade simulator ──────────────────────────────────────────────────────────
def pip_size(symbol: str) -> float:
    return 0.01 if "JPY" in symbol else 0.0001

def simulate_trades(
    symbol: str,
    candles: List[dict],
    min_confidence: float,
    min_votes: int,
) -> List[dict]:
    """
    Walk-forward simulation: for each candle window, run scan_symbol,
    then forward-simulate the trade outcome using subsequent candles.
    Skips overlapping trade windows (one trade per symbol at a time).
    """
    trades = []
    n = len(candles)
    pip = pip_size(symbol)
    in_trade_until = 0  # candle index after which we can re-enter

    # Need at least 120 candles for the EMA/Fibonacci detectors
    for i in range(120, n - 10):
        if i < in_trade_until:
            continue

        window = candles[:i+1]
        try:
            sig = scan_symbol(
                symbol, window,
                min_confidence=min_confidence,
                min_votes=min_votes,
            )
        except Exception:
            continue

        if sig is None:
            continue

        # Entry price (next candle open approximation)
        entry_candle = candles[i+1] if i+1 < n else None
        if not entry_candle:
            continue

        entry_mid = entry_candle.get("mid", {})
        entry_price = float(entry_mid.get("o") or entry_mid.get("c") or sig.entry)

        # Apply spread
        spread = SPREAD_PIPS * pip
        if sig.direction == "BUY":
            entry_price += spread / 2
            sl = entry_price - sig.risk_dist
            tp = entry_price + sig.reward_dist
        else:
            entry_price -= spread / 2
            sl = entry_price + sig.risk_dist
            tp = entry_price - sig.reward_dist

        # Risk $ amount
        risk_usd = STARTING_CAP * RISK_PCT

        # Forward simulate up to 40 candles (~10 hours M15)
        outcome = None
        exit_candle_idx = None
        for j in range(i+1, min(i+41, n)):
            c = candles[j]
            c_mid = c.get("mid", {})
            c_high = float(c_mid.get("h") or 0)
            c_low  = float(c_mid.get("l") or 0)
            if not c_high or not c_low:
                continue

            if sig.direction == "BUY":
                if c_low <= sl:
                    outcome = "LOSS"; exit_candle_idx = j; break
                if c_high >= tp:
                    outcome = "WIN";  exit_candle_idx = j; break
            else:
                if c_high >= sl:
                    outcome = "LOSS"; exit_candle_idx = j; break
                if c_low <= tp:
                    outcome = "WIN";  exit_candle_idx = j; break

        if outcome is None:
            outcome = "TIMEOUT"  # neither hit — neutral, count as scratch
            exit_candle_idx = min(i+40, n-1)

        pnl_usd = (risk_usd * RR_RATIO) if outcome == "WIN" else (-risk_usd if outcome == "LOSS" else 0.0)

        trades.append({
            "symbol":      symbol,
            "direction":   sig.direction,
            "confidence":  round(sig.confidence, 4),
            "votes":       sig.votes,
            "detectors":   sig.detectors_fired,
            "signal_type": sig.signal_type,
            "session":     sig.session,
            "entry":       round(entry_price, 5),
            "sl":          round(sl, 5),
            "tp":          round(tp, 5),
            "rr":          round(sig.rr, 2),
            "outcome":     outcome,
            "pnl_usd":     round(pnl_usd, 2),
            "candle_idx":  i,
        })

        in_trade_until = (exit_candle_idx or i) + 1  # no overlap

    return trades

# ── Stats ────────────────────────────────────────────────────────────────────
def compute_stats(trades: List[dict]) -> dict:
    if not trades:
        return {"trades": 0}

    wins    = [t for t in trades if t["outcome"] == "WIN"]
    losses  = [t for t in trades if t["outcome"] == "LOSS"]
    timeout = [t for t in trades if t["outcome"] == "TIMEOUT"]
    closed  = wins + losses

    win_rate   = len(wins)   / len(closed) if closed else 0
    total_pnl  = sum(t["pnl_usd"] for t in trades)
    gross_win  = sum(t["pnl_usd"] for t in wins)
    gross_loss = abs(sum(t["pnl_usd"] for t in losses))
    pf         = gross_win / gross_loss if gross_loss > 0 else float("inf")
    avg_conf   = sum(t["confidence"] for t in trades) / len(trades)
    avg_votes  = sum(t["votes"]      for t in trades) / len(trades)
    ev_per_trade = total_pnl / len(trades) if trades else 0

    # Max drawdown
    equity = STARTING_CAP
    peak   = equity
    max_dd = 0.0
    for t in trades:
        equity += t["pnl_usd"]
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100
        if dd > max_dd:
            max_dd = dd

    return {
        "trades":       len(trades),
        "wins":         len(wins),
        "losses":       len(losses),
        "timeouts":     len(timeout),
        "win_rate":     round(win_rate * 100, 1),
        "total_pnl":    round(total_pnl, 2),
        "profit_factor":round(pf, 2),
        "ev_per_trade": round(ev_per_trade, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "avg_confidence": round(avg_conf, 3),
        "avg_votes":    round(avg_votes, 1),
        "final_equity": round(STARTING_CAP + total_pnl, 2),
    }

def monthly_projection(stats: dict, trades_per_day: float = 2.0) -> dict:
    """Project monthly P&L assuming similar signal frequency."""
    if stats.get("trades", 0) == 0:
        return {}
    ev   = stats["ev_per_trade"]
    daily_pnl  = ev * trades_per_day
    return {
        "est_daily_pnl":   round(daily_pnl, 2),
        "est_weekly_pnl":  round(daily_pnl * 5, 2),
        "est_monthly_pnl": round(daily_pnl * 21, 2),
    }

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*70)
    print("  RBOTZILLA PHOENIX — CURRENT ENGINE BACKTEST")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  {GRANULARITY}  |  {CANDLE_COUNT} candles/pair")
    print("="*70)

    if not API_TOKEN:
        print("❌ No OANDA_API_TOKEN found in .env — cannot fetch candles")
        sys.exit(1)

    all_results = {}

    for config_name, cfg in CONFIGS.items():
        print(f"\n{'─'*70}")
        print(f"  CONFIG: {config_name}  (min_conf={cfg['min_confidence']}, min_votes={cfg['min_votes']})")
        print(f"{'─'*70}")

        all_trades = []
        pair_stats = {}

        for symbol in PAIRS:
            print(f"  Fetching {symbol}...", end=" ", flush=True)
            candles = fetch_candles(symbol, count=CANDLE_COUNT, granularity=GRANULARITY)
            if len(candles) < 130:
                print(f"not enough candles ({len(candles)}) — skip")
                continue
            print(f"{len(candles)} candles — simulating...", end=" ", flush=True)

            trades = simulate_trades(symbol, candles, cfg["min_confidence"], cfg["min_votes"])
            stats  = compute_stats(trades)
            pair_stats[symbol] = stats
            all_trades.extend(trades)

            t_cnt  = stats.get("trades", 0)
            wr     = stats.get("win_rate", 0)
            pnl    = stats.get("total_pnl", 0)
            pf     = stats.get("profit_factor", 0)
            print(f"{t_cnt} signals | WR={wr:.0f}% | PnL=${pnl:+.2f} | PF={pf:.2f}")

        print(f"\n  ── AGGREGATE RESULTS: {config_name} ──")
        agg_stats = compute_stats(all_trades)
        proj      = monthly_projection(agg_stats, trades_per_day=len(PAIRS) * 0.15)
        for k, v in agg_stats.items():
            print(f"    {k:<25} {v}")
        print()
        for k, v in proj.items():
            print(f"    {k:<25} ${v:+.2f}")

        all_results[config_name] = {
            "config":      cfg,
            "aggregate":   agg_stats,
            "projection":  proj,
            "by_pair":     pair_stats,
        }

    # ── Head-to-head comparison ──────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("  OLD vs NEW — HEAD TO HEAD")
    print(f"{'='*70}")
    old = all_results.get("OLD_0.62_2votes", {}).get("aggregate", {})
    new = all_results.get("NEW_0.68_3votes", {}).get("aggregate", {})
    metrics = ["trades", "win_rate", "total_pnl", "profit_factor", "ev_per_trade", "max_drawdown_pct"]
    print(f"  {'Metric':<25} {'OLD (0.62/2v)':<18} {'NEW (0.68/3v)':<18}  Delta")
    print(f"  {'─'*25} {'─'*18} {'─'*18}  {'─'*10}")
    for m in metrics:
        ov = old.get(m, "n/a")
        nv = new.get(m, "n/a")
        try:
            delta = f"{nv - ov:+.2f}" if isinstance(ov, (int, float)) and isinstance(nv, (int, float)) else "─"
        except Exception:
            delta = "─"
        print(f"  {m:<25} {str(ov):<18} {str(nv):<18}  {delta}")

    # ── Save JSON ────────────────────────────────────────────────────────────
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"backtest_results_{ts}.json"
    with open(fname, "w") as f:
        json.dump({
            "run_at":        datetime.now().isoformat(),
            "granularity":   GRANULARITY,
            "candle_count":  CANDLE_COUNT,
            "pairs_tested":  PAIRS,
            "starting_cap":  STARTING_CAP,
            "risk_pct":      RISK_PCT,
            "rr_ratio":      RR_RATIO,
            "results":       all_results,
        }, f, indent=2)
    print(f"\n  Results saved → {fname}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
