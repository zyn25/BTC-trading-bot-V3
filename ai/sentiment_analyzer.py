"""
Sentiment analyzer (FNG + Funding Rate).
"""
from __future__ import annotations

from typing import Dict, Optional

import aiohttp

from config import settings
from utils.logger import logger


class SentimentAnalyzer:
    """Multi-source sentiment analyzer."""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def init(self):
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def get_fear_greed_index(self) -> Dict:
        """Fear & Greed Index dari Alternative.me (FREE)."""
        if not settings.ai.use_sentiment_fng:
            return {"value": 50, "classification": "Neutral", "sentiment": "neutral", "weight": 0}

        await self.init()
        try:
            url = f"{settings.ai.fng_api_url}?limit=1"
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("data"):
                        value = int(data["data"][0]["value"])
                        return {
                            "value": value,
                            "classification": data["data"][0]["value_classification"],
                            "sentiment": self._classify_fng(value),
                            "weight": 0.15,
                        }
        except Exception as e:
            logger.warning(f"F&G Index error: {e}")
        return {"value": 50, "classification": "Neutral", "sentiment": "neutral", "weight": 0}

    async def get_funding_sentiment(self, exchange, symbol: str) -> Dict:
        """Funding rate sentiment."""
        if not settings.ai.use_sentiment_funding:
            return {"rate": 0, "sentiment": "neutral", "weight": 0}
        try:
            funding = await exchange.exchange.fetch_funding_rate(symbol)
            rate = float(funding.get("fundingRate", 0)) * 100

            if rate > 0.05:
                sentiment, score = "overheated_bearish", -30
            elif rate > 0.02:
                sentiment, score = "mildly_bullish", -10
            elif rate < -0.05:
                sentiment, score = "oversold_bullish", 30
            elif rate < -0.02:
                sentiment, score = "mildly_bearish", 10
            else:
                sentiment, score = "neutral", 0

            return {"rate": rate, "sentiment": sentiment, "score": score, "weight": 0.10}
        except Exception as e:
            logger.warning(f"Funding error: {e}")
        return {"rate": 0, "sentiment": "neutral", "weight": 0}

    async def get_overall_sentiment(self, exchange=None, symbol: str = "BTC/USDT") -> Dict:
        """Aggregate sentiment."""
        await self.init()
        components = []
        scores = []
        weights = []

        fng = await self.get_fear_greed_index()
        components.append(fng)
        scores.append((fng["value"] - 50) * 2)  # normalize to -100..+100
        weights.append(fng.get("weight", 0.15))

        if exchange:
            funding = await self.get_funding_sentiment(exchange, symbol)
            components.append(funding)
            if "score" in funding:
                scores.append(funding["score"])
                weights.append(funding.get("weight", 0.10))

        if weights and sum(weights) > 0:
            composite = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        else:
            composite = 0

        return {
            "composite_score": composite,
            "classification": self._classify_score(composite),
            "components": components,
        }

    def _classify_fng(self, value: int) -> str:
        if value >= 75:
            return "extreme_greed"
        if value >= 55:
            return "greed"
        if value >= 45:
            return "neutral"
        if value >= 25:
            return "fear"
        return "extreme_fear"

    def _classify_score(self, score: float) -> str:
        if score >= 50:
            return "very_bullish"
        if score >= 20:
            return "bullish"
        if score >= -20:
            return "neutral"
        if score >= -50:
            return "bearish"
        return "very_bearish"
