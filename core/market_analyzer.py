"""
Market analyzer dengan multi-timeframe.
"""
from __future__ import annotations

from typing import Dict

import pandas as pd

from ai.ai_orchestrator import AIOrchestrator
from core.exchange import ExchangeManager
from config import settings
from utils.logger import logger


class MarketAnalyzer:
    """Multi-TF market analyzer."""

    def __init__(self, exchange: ExchangeManager, ai: AIOrchestrator):
        self.exchange = exchange
        self.ai = ai

    async def warmup(self):
        """Pre-load data."""
        try:
            await self.exchange.get_ohlcv(settings.trading.symbol, settings.trading.timeframe, 200)
            logger.info("✅ Market analyzer warmed up")
        except Exception as e:
            logger.warning(f"Warmup warning: {e}")

    async def get_current_analysis(self) -> Dict:
        """Full market analysis."""
        try:
            # Primary TF
            df = await self.exchange.get_ohlcv(
                settings.trading.symbol, settings.trading.timeframe, 200
            )

            # AI analysis
            signal = await self.ai.analyze(df, self.exchange, settings.trading.symbol)

            # HTF confirmation
            if settings.ai.htf_alignment_required and signal["type"] != "neutral":
                htf_aligned = await self._check_htf_alignment(signal["type"])
                signal["htf_aligned"] = htf_aligned
                if not htf_aligned:
                    signal["should_trade"] = False
                    signal["filter_reason"] = "HTF not aligned"

            return signal

        except Exception as e:
            logger.exception(f"Analysis error: {e}")
            return {"type": "neutral", "should_trade": False, "error": str(e)}

    async def _check_htf_alignment(self, signal_type: str) -> bool:
        """Check higher timeframe trend alignment."""
        from ai.trend_detector import TrendDetector
        detector = TrendDetector()
        try:
            for htf in settings.trading.timeframes_higher:
                df = await self.exchange.get_ohlcv(settings.trading.symbol, htf, 100)
                trend = await detector.detect_trend(df)
                if signal_type == "long" and trend["trend"] != "bullish":
                    return False
                if signal_type == "short" and trend["trend"] != "bearish":
                    return False
            return True
        except Exception as e:
            logger.warning(f"HTF check error: {e}")
            return True  # fail-safe
