"""
Groq LLM Analyzer (Layer 2 - Optional).
Provides AI reasoning & news sentiment.
"""
from __future__ import annotations

import json
import time
from typing import Dict, Optional

from cachetools import TTLCache

from config import settings
from utils.logger import logger
from utils.news_fetcher import NewsFetcher


class GroqAnalyzer:
    """
    Groq LLM analyzer untuk news sentiment & market reasoning.
    Graceful fallback jika tidak ada API key atau error.
    """

    def __init__(self):
        self.enabled = settings.ai.has_groq
        self.client = None
        self.news_fetcher = NewsFetcher()
        self.cache: TTLCache = TTLCache(maxsize=100, ttl=settings.ai.groq_cache_ttl)
        self.last_call_time = 0
        self.min_interval = 2.0  # seconds between calls (rate limit safety)
        self.calls_today = 0
        self.errors_today = 0

        if self.enabled:
            self._init_client()

    def _init_client(self):
        """Initialize Groq client."""
        try:
            from groq import AsyncGroq
            self.client = AsyncGroq(api_key=settings.ai.groq_api_key, timeout=settings.ai.groq_timeout)
            logger.info(f"✅ Groq client initialized (model: {settings.ai.groq_model})")
        except ImportError:
            logger.warning("⚠️ groq package not installed. Run: pip install groq")
            self.enabled = False
        except Exception as e:
            logger.warning(f"⚠️ Groq init failed: {e}")
            self.enabled = False

    async def close(self):
        await self.news_fetcher.close()
        if self.client:
            try:
                await self.client.close()
            except Exception:
                pass

    async def analyze_news_sentiment(self, symbol: str = "BTC") -> Dict:
        """
        Analyze recent news sentiment via Groq.
        Returns dict with score (-100 to +100) and reasoning.
        """
        if not self.enabled:
            return {"enabled": False, "score": 0, "reasoning": "Groq not enabled"}

        # Rate limiting
        now = time.monotonic()
        if now - self.last_call_time < self.min_interval:
            await self._wait(self.min_interval - (now - self.last_call_time))

        # Check cache
        cache_key = f"news_{symbol}"
        if cache_key in self.cache:
            logger.debug("📦 Using cached Groq result")
            return self.cache[cache_key]

        # Fetch news
        headlines = await self.news_fetcher.fetch_headlines(symbol, limit=10)
        if not headlines:
            return {"enabled": True, "score": 0, "reasoning": "No news available"}

        # Build prompt
        headlines_text = "\n".join(f"- {h}" for h in headlines)
        prompt = f"""Analyze these recent {symbol} crypto news headlines for trading sentiment:

{headlines_text}

Provide a JSON response:
{{
  "score": <number from -100 (very bearish) to +100 (very bullish)>,
  "reasoning": "<1-2 sentence explanation>",
  "key_events": ["<event1>", "<event2>"]
}}

Consider: market impact, regulatory news, adoption, technology, whale activity.
Respond ONLY with valid JSON, no markdown."""

        try:
            self.last_call_time = time.monotonic()
            response = await self.client.chat.completions.create(
                model=settings.ai.groq_model,
                messages=[
                    {"role": "system", "content": "You are a crypto market analyst. Respond only with valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=300,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            result_out = {
                "enabled": True,
                "score": max(-100, min(100, result.get("score", 0))),
                "reasoning": result.get("reasoning", ""),
                "key_events": result.get("key_events", []),
                "source": "groq",
            }

            self.cache[cache_key] = result_out
            self.calls_today += 1
            logger.info(f"🧠 Groq sentiment: {result_out['score']} ({result_out['reasoning'][:50]})")
            return result_out

        except Exception as e:
            self.errors_today += 1
            logger.warning(f"⚠️ Groq analysis error: {e}")
            return {"enabled": True, "score": 0, "reasoning": f"Error: {str(e)[:50]}", "error": True}

    async def enhance_signal(self, signal: Dict, symbol: str = "BTC") -> Dict:
        """
        Enhance technical signal dengan Groq reasoning.
        Returns signal dengan AI reasoning tambahan.
        """
        if not self.enabled or signal["type"] == "neutral":
            signal["ai_reasoning"] = "Technical only" if not self.enabled else "Neutral signal"
            return signal

        news_sentiment = await self.analyze_news_sentiment(symbol)

        # Adjust confidence based on news
        original_confidence = signal["confidence"]
        news_score = news_sentiment.get("score", 0)
        news_normalized = news_score / 100  # -1 to +1

        # If news aligns with signal, boost confidence
        if signal["type"] == "long" and news_normalized > 0.2:
            signal["confidence"] = min(signal["confidence"] + 0.05, 1.0)
        elif signal["type"] == "short" and news_normalized < -0.2:
            signal["confidence"] = min(signal["confidence"] + 0.05, 1.0)
        # If news conflicts, reduce confidence
        elif signal["type"] == "long" and news_normalized < -0.3:
            signal["confidence"] = max(signal["confidence"] - 0.10, 0.0)
        elif signal["type"] == "short" and news_normalized > 0.3:
            signal["confidence"] = max(signal["confidence"] - 0.10, 0.0)

        signal["ai_reasoning"] = news_sentiment.get("reasoning", "")
        signal["ai_mode"] = "hybrid"
        signal["news_score"] = news_normalized
        signal["original_confidence"] = original_confidence

        return signal

    async def _wait(self, seconds: float):
        """Async sleep."""
        import asyncio
        await asyncio.sleep(seconds)

    def get_stats(self) -> Dict:
        """Get usage stats."""
        return {
            "enabled": self.enabled,
            "model": settings.ai.groq_model if self.enabled else "N/A",
            "calls_today": self.calls_today,
            "errors_today": self.errors_today,
            "cache_size": len(self.cache),
        }
