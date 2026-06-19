"""
News fetcher untuk Groq analysis.
"""
from __future__ import annotations

from typing import List, Optional

import aiohttp

from config import settings
from utils.logger import logger


class NewsFetcher:
    """Fetch crypto news dari multiple sources."""

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

    async def fetch_headlines(self, symbol: str = "BTC", limit: int = 10) -> List[str]:
        """Fetch recent headlines untuk symbol."""
        await self.init()

        # Try CryptoPanic first
        if settings.ai.cryptopanic_api_key and settings.ai.use_news_api:
            headlines = await self._fetch_cryptopanic(symbol, limit)
            if headlines:
                return headlines

        # Fallback: return empty (bot still works with technical only)
        logger.debug("No news source configured")
        return []

    async def _fetch_cryptopanic(self, symbol: str, limit: int) -> List[str]:
        """Fetch from CryptoPanic API."""
        try:
            url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                "auth_token": settings.ai.cryptopanic_api_key,
                "currencies": symbol,
                "filter": "hot",
                "kind": "news",
            }
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("results", [])[:limit]
                    return [r.get("title", "") for r in results if r.get("title")]
        except Exception as e:
            logger.warning(f"CryptoPanic fetch error: {e}")
        return []
