"""
Technical trend detection (Layer 1 AI).
"""
from __future__ import annotations

from typing import Dict

import pandas as pd

from config import settings
from utils.indicators import TechnicalIndicators
from utils.logger import logger

ti = TechnicalIndicators()


class TrendDetector:
    """Multi-method trend detection."""

    async def detect_trend(self, df: pd.DataFrame) -> Dict:
        """Detect trend dari OHLCV data."""
        if df is None or len(df) < 50:
            return {
                "trend": "neutral",
                "strength": 0.0,
                "confidence": 0.0,
                "bullish_score": 0.0,
                "bearish_score": 0.0,
            }

        tech = self._technical_trend(df)
        structure = self._market_structure(df)
        momentum = self._momentum_analysis(df)

        weights = [0.4, 0.35, 0.25]
        bullish = sum(t["bullish"] * w for t, w in zip([tech, structure, momentum], weights))
        bearish = sum(t["bearish"] * w for t, w in zip([tech, structure, momentum], weights))

        if bullish > bearish + 0.15:
            trend = "bullish"
            strength = min(bullish, 1.0)
        elif bearish > bullish + 0.15:
            trend = "bearish"
            strength = min(bearish, 1.0)
        else:
            trend = "neutral"
            strength = max(bullish, bearish)

        confidence = 1.0 - abs(bullish - bearish)

        return {
            "trend": trend,
            "strength": strength,
            "confidence": confidence,
            "bullish_score": bullish,
            "bearish_score": bearish,
        }

    def _technical_trend(self, df: pd.DataFrame) -> Dict:
        close = df["close"]
        ema9 = ti.ema(close, 9)
        ema21 = ti.ema(close, 21)
        ema50 = ti.ema(close, 50)
        ema200 = ti.ema(close, 200)

        current = close.iloc[-1]
        bullish = 0.0
        bearish = 0.0

        if not ema200.empty and current > ema9.iloc[-1] > ema21.iloc[-1] > ema50.iloc[-1]:
            bullish += 0.4
        elif not ema200.empty and current < ema9.iloc[-1] < ema21.iloc[-1] < ema50.iloc[-1]:
            bearish += 0.4

        if not ema200.empty:
            if current > ema200.iloc[-1]:
                bullish += 0.3
            else:
                bearish += 0.3

        # Crossover
        if len(ema9) > 1 and len(ema21) > 1:
            if ema9.iloc[-1] > ema21.iloc[-1] and ema9.iloc[-2] <= ema21.iloc[-2]:
                bullish += 0.3
            elif ema9.iloc[-1] < ema21.iloc[-1] and ema9.iloc[-2] >= ema21.iloc[-2]:
                bearish += 0.3

        return {"bullish": bullish, "bearish": bearish}

    def _market_structure(self, df: pd.DataFrame) -> Dict:
        bullish = 0.0
        bearish = 0.0
        try:
            highs = df["high"].rolling(5).max()
            lows = df["low"].rolling(5).min()
            recent_h = highs.iloc[-20:].dropna()
            recent_l = lows.iloc[-20:].dropna()

            if len(recent_h) >= 3:
                if recent_h.iloc[-1] > recent_h.iloc[-3]:
                    bullish += 0.5
                elif recent_h.iloc[-1] < recent_h.iloc[-3]:
                    bearish += 0.5
            if len(recent_l) >= 3:
                if recent_l.iloc[-1] > recent_l.iloc[-3]:
                    bullish += 0.5
                elif recent_l.iloc[-1] < recent_l.iloc[-3]:
                    bearish += 0.5
        except Exception:
            pass
        return {"bullish": bullish, "bearish": bearish}

    def _momentum_analysis(self, df: pd.DataFrame) -> Dict:
        close = df["close"]
        bullish = 0.0
        bearish = 0.0
        try:
            rsi = ti.rsi(close, 14)
            macd_line, signal_line, hist = ti.macd(close)
            stoch_k, stoch_d = ti.stochastic(df["high"], df["low"], close)

            rsi_val = rsi.iloc[-1] if not rsi.empty else 50
            if 40 < rsi_val < 70:
                bullish += 0.3
            elif rsi_val > 70:
                bearish += 0.2
            elif 30 < rsi_val < 60:
                bearish += 0.3
            elif rsi_val < 30:
                bullish += 0.2

            if not hist.empty and hist.iloc[-1] > 0:
                bullish += 0.4
            elif not hist.empty:
                bearish += 0.4

            if not stoch_k.empty and not stoch_d.empty:
                if stoch_k.iloc[-1] < 20 and stoch_k.iloc[-1] > stoch_d.iloc[-1]:
                    bullish += 0.3
                elif stoch_k.iloc[-1] > 80 and stoch_k.iloc[-1] < stoch_d.iloc[-1]:
                    bearish += 0.3
        except Exception as e:
            logger.warning(f"Momentum analysis error: {e}")

        return {"bullish": bullish, "bearish": bearish}
