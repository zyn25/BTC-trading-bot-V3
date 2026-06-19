"""
CCXT async exchange wrapper dengan retry logic.
"""
from __future__ import annotations

import asyncio
from typing import Dict, List, Optional

import ccxt.async_support as ccxt
import pandas as pd

from config import ExchangeSettings, settings
from utils.logger import logger


class ExchangeManager:
    """Async exchange manager dengan auto-retry."""

    def __init__(self, config: ExchangeSettings = None):
        self.config = config or settings.exchange
        self.exchange: Optional[ccxt.Exchange] = None

    async def connect(self):
        try:
            exchange_class = getattr(ccxt, self.config.name)
            options = {
                "apiKey": self.config.api_key,
                "secret": self.config.secret,
                "enableRateLimit": True,
                "timeout": self.config.timeout,
                "options": {"defaultType": "future", "adjustForTimeDifference": True},
            }
            if self.config.passphrase:
                options["password"] = self.config.passphrase

            self.exchange = exchange_class(options)
            if self.config.testnet:
                self.exchange.set_sandbox_mode(True)
                logger.info("🧪 Testnet mode")
            await self.exchange.load_markets()
            logger.info(f"✅ Connected to {self.config.name}")
        except Exception as e:
            logger.exception(f"❌ Exchange connection failed: {e}")
            raise

    async def close(self):
        if self.exchange:
            await self.exchange.close()

    async def _retry(self, func, *args, max_retries: int = 3, **kwargs):
        """Execute dengan exponential backoff retry."""
        last_error = None
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait}s: {e}")
                    await asyncio.sleep(wait)
        raise last_error

    async def set_leverage(self, leverage: int, symbol: str):
        try:
            await self.exchange.set_leverage(leverage, symbol)
            logger.info(f"⚙️ Leverage {leverage}x for {symbol}")
        except Exception as e:
            logger.warning(f"Set leverage warning: {e}")

    async def get_balance(self) -> Dict:
        balance = await self._retry(self.exchange.fetch_balance)
        return {
            "total": float(balance.get("total", {}).get("USDT", 0) or 0),
            "free": float(balance.get("free", {}).get("USDT", 0) or 0),
            "used": float(balance.get("used", {}).get("USDT", 0) or 0),
        }

    async def get_ticker(self, symbol: str) -> Dict:
        ticker = await self._retry(self.exchange.fetch_ticker, symbol)
        return {
            "symbol": symbol,
            "last": float(ticker["last"]),
            "bid": float(ticker.get("bid", 0) or 0),
            "ask": float(ticker.get("ask", 0) or 0),
            "volume": float(ticker.get("quoteVolume", 0) or 0),
            "change_pct": float(ticker.get("percentage", 0) or 0),
            "high": float(ticker.get("high", 0) or 0),
            "low": float(ticker.get("low", 0) or 0),
        }

    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
        ohlcv = await self._retry(self.exchange.fetch_ohlcv, symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        return df

    async def create_order(self, symbol: str, side: str, amount: float,
                            order_type: str = "market", price: Optional[float] = None,
                            params: Optional[Dict] = None) -> Dict:
        params = params or {}
        order = await self._retry(
            self.exchange.create_order, symbol, order_type, side, amount, price, params
        )
        logger.info(f"📝 Order: {side} {amount} {symbol} @ {price or 'market'}")
        return order

    async def create_stop_loss(self, symbol: str, side: str, amount: float, stop_price: float) -> Dict:
        params = {"stopPrice": stop_price, "reduceOnly": True}
        opposite = "sell" if side == "buy" else "buy"
        return await self.create_order(symbol, opposite, amount, "stop_market", None, params)

    async def create_take_profit(self, symbol: str, side: str, amount: float, tp_price: float) -> Dict:
        params = {"stopPrice": tp_price, "reduceOnly": True}
        opposite = "sell" if side == "buy" else "buy"
        return await self.create_order(symbol, opposite, amount, "take_profit_market", None, params)

    async def cancel_order(self, order_id: str, symbol: str):
        try:
            await self.exchange.cancel_order(order_id, symbol)
            logger.info(f"🚫 Cancelled: {order_id}")
        except Exception as e:
            logger.warning(f"Cancel error: {e}")

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        return await self._retry(self.exchange.fetch_open_orders, symbol)
