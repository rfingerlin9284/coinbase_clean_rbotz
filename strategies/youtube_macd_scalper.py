from typing import Any, Dict, Optional, Literal
from .base import BaseStrategy, ProposedTrade, StrategyContext, StrategyMetadata

class YoutubeMacdScalper(BaseStrategy):
    """
    Transcribed from 'Best Crypto Scalping Strategy for the 5 Minute Time Frame'
    - Uses EMA 50, EMA 200, and MACD.
    - Long when EMA 50 > EMA 200, MACD histogram is negative but trending up (pullback).
    - Exits at exactly +0.50% profit target, -0.40% stop loss.
    """
    def __init__(self) -> None:
        super().__init__(
            metadata=StrategyMetadata(
                name="Youtube MACD 5m Scalper",
                code="YT_MACD_SCALP",
                priority="bronze",
                markets=["CRYPTO"],
                base_timeframes=["M5"],
                max_hold_minutes=120,   # Scalping, quick exits
                target_rr=1.25,         # 0.5% / 0.4% = 1.25
                est_win_rate=0.60
            )
        )

    def decide_entry(self, ctx: StrategyContext) -> Optional[ProposedTrade]:
        if len(ctx.candles) < 200:
            return None

        # These indicators are expected to be computed by the engine and passed in ctx.indicators
        # Fallback to simple calculation if not provided yet.
        ema50 = ctx.indicators.get("EMA_50", 0)
        ema200 = ctx.indicators.get("EMA_200", 0)
        macd = ctx.indicators.get("MACD_hist", 0)
        
        current_price = ctx.candles[-1].get("c", 0.0)
        if current_price == 0.0:
            return None

        # Long condition: EMA 50 > EMA 200 (uptrend) and MACD histogram shows pullback
        if ema50 > ema200 and macd < 0:
            # We want to buy at market immediately
            return ProposedTrade(
                strategy_code=self.metadata.code,
                symbol=ctx.symbol,
                direction="BUY",
                entry_type="market",
                entry_price=current_price,
                stop_loss_price=current_price * 0.996,  # -0.4%
                take_profit_price=current_price * 1.005, # +0.5%
                target_rr=1.25,
                confidence=0.75,
                notes={"reason": "EMA50>200 uptrend with MACD pullback bounds (0.5% TP / 0.4% SL)"}
            )
            
        # Short condition: EMA 50 < EMA 200 (downtrend) and MACD histogram shows bounce
        elif ema50 < ema200 and macd > 0:
            return ProposedTrade(
                strategy_code=self.metadata.code,
                symbol=ctx.symbol,
                direction="SELL",
                entry_type="market",
                entry_price=current_price,
                stop_loss_price=current_price * 1.004,  # +0.4%
                take_profit_price=current_price * 0.995, # -0.5%
                target_rr=1.25,
                confidence=0.75,
                notes={"reason": "EMA50<200 downtrend with MACD bounce bounds (0.5% TP / 0.4% SL)"}
            )

        return None
