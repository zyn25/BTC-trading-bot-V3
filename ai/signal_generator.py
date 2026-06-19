"""
Technical Signal Generator (Layer 1).
"""
from __future__ import annotations

from typing import Dict

import pandas as pd

from ai.trend_detector import TrendDetector, ti
from config import settings
from utils.indicators import TechnicalIndicators
from utils.logger import logger


class SignalGenerator:
    """Generate trading signals dari technical analysis."""

    def __init__(self):
        self.trend_detector = TrendDetector()

    async def generate_signal(self, df: pd.DataFrame, sentiment: Dict) -> Dict:
        """Generate signal dari OHLCV + sentiment."""
        if df is None or len(df) < 50:
            return {"type": "neutral", "should_trade": False}

        # Trend
        trend_data = await self.trend_detector.detect_trend(df)

        # Technical confluence
        tech = self._technical_confluence(df)

        # Volume
        volume_sig = self._volume_analysis(df)

        # Combine scores
        long_score = 0.0
        short_score = 0.0

        # Trend weight: 40%
        if trend_data["trend"] == "bullish":
            long_score += 0.40 * trend_data["strength"]
        elif trend_data["trend"] == "bearish":
            short_score += 0.40 * trend_data["strength"]

        # Sentiment: 15%
        sent_val = sentiment.get("composite_score", 0)
        if sent_val < -50:
            short_score += 0.15
        elif sent_val < -20:
            short_score += 0.10
        elif sent_val > 50:
            long_score += 0.15
        elif sent_val > 20:
            long_score += 0.10

        # Technical: 30%
        long_score += 0.30 * tech["bullish"]
        short_score += 0.30 * tech["bearish"]

        # Volume: 15%
        if volume_sig["confirming"]:
            if volume_sig["direction"] == "bullish":
                long_score += 0.15
            else:
                short_score += 0.15

        # Determine signal
        if long_score > short_score and long_score >= settings.ai.min_signal_strength:
            signal_type = "long"
            strength = long_score
        elif short_score > long_score and short_score >= settings.ai.min_signal_strength:
            signal_type = "short"
            strength = short_score
        else:
            signal_type = "neutral"
            strength = max(long_score, short_score)

        confidence = min((strength + (1 - abs(long_score - short_score))) / 2, 1.0)

        # Entry, SL, TP
        current_price = df["close"].iloc[-1]
        atr_val = ti.atr(df["high"], df["low"], df["close"], 14)
        atr_now = atr_val.iloc[-1] if not atr_val.empty else current_price * 0.01

        if signal_type == "long":
            entry = current_price
            sl = entry - (atr_now * settings.trading.stop_loss_atr_mult)
            tp1 = entry + (atr_now * settings.trading.take_profit_atr_mult)
            tp2 = entry + (atr_now * settings.trading.take_profit_atr_mult * 1.5)
        elif signal_type == "short":
            entry = current_price
            sl = entry + (atr_now * settings.trading.stop_loss_atr_mult)
            tp1 = entry - (atr_now * settings.trading.take_profit_atr_mult)
            tp2 = entry - (atr_now * settings.trading.take_profit_atr_mult * 1.5)
        else:
            entry = sl = tp1 = tp2 = current_price

        risk = abs(entry - sl)
        reward = abs(tp1 - entry)
        rr = reward / risk if risk > 0 else 0

        return {
            "type": signal_type,
            "strength": strength,
            "confidence": confidence,
            "entry": entry,
            "stop_loss": sl,
            "take_profit_1": tp1,
            "take_profit_2": tp2,
            "atr": atr_now,
            "risk_reward": rr,
            "trend": trend_data,
            "sentiment": sentiment,
            "should_trade": (
                signal_type != "neutral"
                and confidence >= settings.ai.confidence_threshold
                and strength >= settings.ai.min_signal_strength
                and rr >= settings.trading.min_risk_reward
            ),
        }

    def _technical_confluence(self, df: pd.DataFrame) -> Dict:
        close = df["close"]
        high = df["high"]
        low = df["low"]
        bullish = 0.0
        bearish = 0.0

        try:
            ema9 = ti.ema(close, 9)
            ema21 = ti.ema(close, 21)
            if ema9.iloc[-1] > ema21.iloc[-1]:
                bullish += 0.20
            else:
                bearish += 0.20

            rsi = ti.rsi(close, 14)
            rsi_val = rsi.iloc[-1]
            if 40 < rsi_val < 65:
                bullish += 0.15
            elif 35 < rsi_val < 60:
                bearish += 0.15

            _, _, hist = ti.macd(close)
            if hist.iloc[-1] > 0:
                bullish += 0.20
            else:
                bearish += 0.20

            upper, middle, lower = ti.bollinger_bands(close)
            if close.iloc[-1] < lower.iloc[-1]:
                bullish += 0.15
            elif close.iloc[-1] > upper.iloc[-1]:
                bearish += 0.15
            elif close.iloc[-1] > middle.iloc[-1]:
                bullish += 0.05
            else:
                bearish += 0.05

            adx = ti.adx(high, low, close, 14)
            if not adx.empty and adx.iloc[-1] > 25:
                ema50 = ti.ema(close, 50)
                if close.iloc[-1] > ema50.iloc[-1]:
                    bullish += 0.15
                else:
                    bearish += 0.15

            stoch_k, stoch_d = ti.stochastic(high, low, close)
            if not stoch_k.empty and stoch_k.iloc[-1] < 20 and stoch_k.iloc[-1] > stoch_d.iloc[-1]:
                bullish += 0.15
            elif not stoch_k.empty and stoch_k.iloc[-1] > 80 and stoch_k.iloc[-1] < stoch_d.iloc[-1]:
                bearish += 0.15
        except Exception as e:
            logger.warning(f"Technical confluence error: {e}")

        return {"bullish": bullish, "bearish": bearish}

    def _volume_analysis(self, df: pd.DataFrame) -> Dict:
        try:
            current_vol = df["volume"].iloc[-1]
            avg_vol = df["volume"].rolling(20).mean().iloc[-1]
            vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1.0
            price_change = df["close"].iloc[-1] - df["close"].iloc[-2]

            if vol_ratio > 1.3 and price_change > 0:
                return {"confirming": True, "direction": "bullish", "ratio": vol_ratio}
            elif vol_ratio > 1.3 and price_change < 0:
                return {"confirming": True, "direction": "bearish", "ratio": vol_ratio}
        except Exception:
            pass
        return {"confirming": False, "direction": "neutral", "ratio": 1.0}
