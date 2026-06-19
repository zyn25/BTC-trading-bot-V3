"""
Technical indicators menggunakan pandas-ta.
"""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
import pandas_ta as ta


class TechnicalIndicators:
    """Kumpulan technical indicators profesional."""

    @staticmethod
    def ema(series: pd.Series, period: int) -> pd.Series:
        return ta.ema(series, length=period)

    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series:
        return ta.sma(series, length=period)

    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        return ta.rsi(series, length=period)

    @staticmethod
    def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        macd_df = ta.macd(series, fast=fast, slow=slow, signal=signal)
        if macd_df is None or macd_df.empty:
            return pd.Series(dtype=float), pd.Series(dtype=float), pd.Series(dtype=float)
        cols = macd_df.columns.tolist()
        return macd_df[cols[0]], macd_df[cols[1]], macd_df[cols[2]]

    @staticmethod
    def bollinger_bands(series: pd.Series, period: int = 20, std: float = 2.0):
        bb = ta.bbands(series, length=period, std=std)
        if bb is None or bb.empty:
            empty = pd.Series(dtype=float)
            return empty, empty, empty
        cols = bb.columns.tolist()
        return bb[cols[0]], bb[cols[1]], bb[cols[2]]

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        result = ta.atr(high, low, close, length=period)
        if result is None:
            return pd.Series(dtype=float)
        return result

    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        result = ta.adx(high, low, close, length=period)
        if result is None or result.empty:
            return pd.Series(dtype=float)
        return result.iloc[:, 0]  # ADX column

    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                   k: int = 14, d: int = 3, smooth_k: int = 3):
        stoch = ta.stoch(high, low, close, k=k, d=d, smooth_k=smooth_k)
        if stoch is None or stoch.empty:
            empty = pd.Series(dtype=float)
            return empty, empty
        cols = stoch.columns.tolist()
        return stoch[cols[0]], stoch[cols[1]]

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        result = ta.obv(close, volume)
        if result is None:
            return pd.Series(dtype=float)
        return result

    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        typical = (high + low + close) / 3
        cumvol = volume.cumsum()
        return (typical * volume).cumsum() / cumvol.replace(0, np.nan)
