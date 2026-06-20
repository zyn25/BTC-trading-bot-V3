"""
Load historical data dari exchange atau CSV.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

from core.exchange import ExchangeManager
from config import settings
from utils.logger import logger


class DataLoader:
    """Load OHLCV data untuk backtesting."""

    def __init__(self, exchange: ExchangeManager):
        self.exchange = exchange

    async def fetch_historical(self, symbol: str = None, timeframe: str = None,
                                days: int = 365) -> pd.DataFrame:
        """
        Fetch historical OHLCV data.
        Default: 1 tahun data 15m BTC/USDT.
        """
        symbol = symbol or settings.trading.symbol
        timeframe = timeframe or settings.trading.timeframe

        logger.info(f"📊 Fetching {days} days of {symbol} {timeframe} data...")

        # Calculate limit based on timeframe
        timeframe_minutes = {
            "1m": 1, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "4h": 240, "1d": 1440,
        }
        minutes = timeframe_minutes.get(timeframe, 15)
        candles_per_day = (24 * 60) // minutes
        total_candles = days * candles_per_day

        # CCXT has limit per request (usually 1000-1500)
        # Need to fetch in batches
        all_ohlcv = []
        batch_size = 1000
        batches = (total_candles // batch_size) + 1

        for i in range(batches):
            try:
                ohlcv = await self.exchange.exchange.fetch_ohlcv(
                    symbol, timeframe, limit=batch_size
                )
                if not ohlcv:
                    break
                all_ohlcv = ohlcv + all_ohlcv  # prepend (older data)
                logger.info(f"  Batch {i+1}/{batches}: {len(ohlcv)} candles")
                
                # Set end time untuk batch berikutnya
                oldest_ts = ohlcv[0][0]
                await self.exchange.exchange.sleep(100)  # Rate limit
            except Exception as e:
                logger.warning(f"Batch {i+1} error: {e}")
                break

        if not all_ohlcv:
            raise ValueError("No data fetched")

        df = pd.DataFrame(all_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)

        logger.info(f"✅ Loaded {len(df)} candles from {df.index[0]} to {df.index[-1]}")
        return df

    def load_from_csv(self, filepath: str) -> pd.DataFrame:
        """Load dari CSV file (format: timestamp,open,high,low,close,volume)."""
        df = pd.read_csv(filepath)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        logger.info(f"✅ Loaded {len(df)} candles from CSV")
        return df

    def save_to_csv(self, df: pd.DataFrame, filepath: str):
        """Save ke CSV untuk reuse."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(filepath)
        logger.info(f"💾 Saved to {filepath}")
