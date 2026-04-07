#!/usr/bin/env python3
"""
Stochastic Regime Detector - RBOTzilla COINBASE CLEAN
Market regime classification using volatility and trend analysis.
Calibrated for M15 crypto candle data from Coinbase Advanced Trade API.
PIN: 841921 | Ported from OANDA CLEAN: 2026-03-29

Crypto adaptation:
  - Annualization uses 365*96 = 35040 (24/7 market, no closed days)
  - Volatility scoring thresholds scaled ~5x upward to account for
    crypto's inherently higher baseline vol vs forex
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone

class MarketRegime(Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    CRASH = "crash"
    TRIAGE = "triage"

@dataclass
class RegimeData:
    regime: MarketRegime
    confidence: float
    volatility: float
    trend_strength: float
    regime_probabilities: Dict[str, float]

class StochasticRegimeDetector:
    """
    Classifies market regime from a price series.

    All internal scaling assumes M15 crypto candles:
      - Volatility annualized via sqrt(35040)  [365 days * 96 bars/day]
      - Trend slope normalized and scaled by 2000x so softmax scores
        land in a readable 0.5-10.0 range for typical crypto moves.

    Regime scoring:
      BULL      — positive trend, controlled volatility
      BEAR      — negative trend
      SIDEWAYS  — negligible trend, low volatility
      CRASH     — strong negative trend AND elevated volatility
      TRIAGE    — low-confidence catch-all baseline (score 0.3)
    """

    # M15 crypto: 365 trading days * 96 candles/day = 35040 periods/year
    _M15_ANNUALIZATION = np.sqrt(35040)

    # Structural slope normalized by mean price — same scale factor works for crypto
    _TREND_SCALE = 2000.0

    def __init__(self, pin: int = None):
        if pin and pin != 841921:
            raise PermissionError("Invalid PIN")
        self.lookback_period = 50

    # ── Volatility ────────────────────────────────────────────────────────────

    def _calculate_volatility(self, prices: np.ndarray) -> float:
        """Annualized volatility from M15 log-return std."""
        if len(prices) < 2:
            return 0.0
        returns = np.diff(prices) / prices[:-1]
        return float(np.std(returns) * self._M15_ANNUALIZATION)

    # ── Trend ─────────────────────────────────────────────────────────────────

    def _calculate_trend_strength(self, prices: np.ndarray) -> float:
        """Normalized linear-regression slope, scaled for softmax scoring."""
        if len(prices) < 2:
            return 0.0
        x = np.arange(len(prices))
        slope, _ = np.polyfit(x, prices, 1)
        return float((slope / np.mean(prices)) * self._TREND_SCALE)

    # ── Regime probabilities ──────────────────────────────────────────────────

    def _calculate_regime_probabilities(self, vol: float, trend: float) -> Dict[str, float]:
        """
        Score each regime, apply stochastic noise, then softmax.

        Inputs are ALREADY scaled by the calculate methods above.
        Volatility multipliers scaled down ~5x vs forex to compensate
        for crypto's ~5x higher baseline annualized vol.
        """
        scores = {}

        # Bull: positive trend, penalized by high volatility
        scores[MarketRegime.BULL.value] = max(0, trend * 10) * max(0.1, 1.0 - vol * 0.1)

        # Bear: negative trend, boosted slightly by volatility
        scores[MarketRegime.BEAR.value] = max(0, -trend * 10) * min(2.0, 1.0 + vol * 0.1)

        # Sideways: near-zero trend, low volatility
        # Crypto vol baseline is 0.5-2.0 — use 0.1x multiplier so normal ranging isn't crushed
        scores[MarketRegime.SIDEWAYS.value] = max(0, 1.0 - abs(trend) * 10) * max(0.1, 1.0 - vol * 0.1)

        # Crash: requires BOTH strong negative trend AND EXTREME volatility
        # Crypto baseline vol is 0.5-2.0, so only trigger crash above 2.5
        if trend < -1.5 and vol > 2.5:
            scores[MarketRegime.CRASH.value] = (-trend * 10) * (vol * 0.5)
        else:
            scores[MarketRegime.CRASH.value] = 0.05

        # Triage: low-confidence catch-all. Must be easy for real regimes to beat.
        scores[MarketRegime.TRIAGE.value] = 0.3
        if vol > 3.0:
            scores[MarketRegime.TRIAGE.value] *= 1.5

        # Stochastic noise (time-seeded so consecutive calls vary)
        np.random.seed(int(datetime.now(timezone.utc).timestamp() * 1000) % 2**32)
        noise = np.random.normal(0, 0.05, len(scores))

        # Sharpen scores before softmax to produce readable confidence (60-99%)
        score_values = (np.array(list(scores.values())) + noise) * 3.0

        # Softmax
        exp_scores = np.exp(score_values - np.max(score_values))
        probabilities = exp_scores / np.sum(exp_scores)

        regime_names = list(scores.keys())
        return {regime_names[i]: float(probabilities[i]) for i in range(len(regime_names))}

    # ── Main detection ────────────────────────────────────────────────────────

    def detect_regime(self, prices: List[float], symbol: str = "UNKNOWN") -> RegimeData:
        """Classify market regime from a price series."""
        price_array = np.array(prices, dtype=float)

        if len(price_array) < 10:
            return RegimeData(
                regime=MarketRegime.TRIAGE,
                confidence=0.3,
                volatility=0.0,
                trend_strength=0.0,
                regime_probabilities={r.value: 0.2 for r in MarketRegime}
            )

        analysis_prices = price_array[-self.lookback_period:] if len(price_array) > self.lookback_period else price_array

        volatility = self._calculate_volatility(analysis_prices)
        trend_strength = self._calculate_trend_strength(analysis_prices)

        regime_probs = self._calculate_regime_probabilities(volatility, trend_strength)

        best_regime_name = max(regime_probs.keys(), key=lambda k: regime_probs[k])
        best_regime = MarketRegime(best_regime_name)
        confidence = regime_probs[best_regime_name]

        return RegimeData(
            regime=best_regime,
            confidence=confidence,
            volatility=volatility,
            trend_strength=trend_strength,
            regime_probabilities=regime_probs
        )


# ── Convenience function (called by trade_engine.py) ─────────────────────────

def detect_market_regime(prices: List[float], symbol: str = "UNKNOWN") -> Dict[str, Any]:
    """Returns dict with keys: regime, confidence, vol, trend."""
    detector = StochasticRegimeDetector(pin=841921)
    result = detector.detect_regime(prices, symbol)
    return {
        'regime': result.regime.value,
        'confidence': result.confidence,
        'vol': result.volatility,
        'trend': result.trend_strength
    }


# ── Self-test (crypto-realistic M15 data) ─────────────────────────────────────

if __name__ == "__main__":
    print("StochasticRegimeDetector self-test starting...\n")
    np.random.seed(42)

    # ── Realistic M15 crypto scenarios ──────────────────────────────────────
    # BTC-USD ~ $65,000

    # Bull: BTC trending up ~$500 over 50 M15 bars
    bull_prices = [65000 + i * 10 + np.random.normal(0, 30) for i in range(50)]

    # Bear: BTC trending down ~$500 over 50 M15 bars
    bear_prices = [65500 - i * 10 + np.random.normal(0, 30) for i in range(50)]

    # Sideways: BTC flat with tiny noise
    sideways_prices = [65000 + np.random.normal(0, 8) for i in range(50)]

    # Crash: BTC plunging ~$2000 with high volatility
    crash_prices = [66000 - i * 40 + np.random.normal(0, 120) for i in range(50)]

    # Triage: BTC minimal data (short series)
    triage_prices = [65000 + np.random.normal(0, 20) for i in range(8)]

    detector = StochasticRegimeDetector(pin=841921)

    test_cases = [
        ("Bull (BTC-USD +$500)",          bull_prices,     "bull"),
        ("Bear (BTC-USD -$500)",          bear_prices,     "bear"),
        ("Sideways (BTC-USD flat)",        sideways_prices, "sideways"),
        ("Crash (BTC-USD -$2000 HV)",     crash_prices,    "crash"),
        ("Triage (insufficient data)",     triage_prices,   "triage"),
    ]

    print("Regime Detection Results:")
    print("=" * 60)

    passed = 0
    failed = 0
    for name, prices, expected in test_cases:
        result = detector.detect_regime(prices, name)
        match = "✅" if result.regime.value == expected else "❌"
        if result.regime.value == expected:
            passed += 1
        else:
            failed += 1

        print(f"\n  {name}:")
        print(f"    Regime:     {result.regime.value}  {match}  (expected: {expected})")
        print(f"    Confidence: {result.confidence:.2%}")
        print(f"    Volatility: {result.volatility:.4f}")
        print(f"    Trend:      {result.trend_strength:.4f}")

    print("\n" + "=" * 60)
    print(f"  Results: {passed}/{passed+failed} passed")
    if failed == 0:
        print("  ✅ All regimes classified correctly")
        print("  ✅ StochasticRegimeDetector self-test PASSED")
        print("  🔐 REGIME LOGIC ACTIVE — COINBASE CLEAN")
    else:
        print(f"  ⚠️  {failed} test(s) did not match expected regime")
        print("  ⚠️  Review scoring thresholds")
