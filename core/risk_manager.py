"""
Risk Management - Critical untuk capital preservation.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict

from config import TradingSettings, settings
from database.db_manager import DatabaseManager
from utils.logger import logger


class RiskManager:
    """Comprehensive risk management."""

    def __init__(self, config: TradingSettings, db: DatabaseManager):
        self.config = config
        self.db = db
        self._lock = asyncio.Lock()
        self._daily_trades = 0
        self._last_reset = datetime.utcnow().date()

    def _reset_if_new_day(self):
        today = datetime.utcnow().date()
        if today > self._last_reset:
            self._daily_trades = 0
            self._last_reset = today

    def calculate_position_size(self, balance: float, entry: float, sl: float) -> float:
        """Calculate position size berdasarkan risk."""
        if entry == sl or sl == 0:
            return 0.0
        risk_amount = balance * self.config.risk_per_trade
        price_diff = abs(entry - sl)
        position_value = (risk_amount / price_diff) * entry
        size = position_value / entry
        max_size = (balance * self.config.max_position_pct) / entry
        return min(size, max_size)

    async def can_open_trade(self, balance: float) -> Dict:
        """Check semua risk constraints."""
        async with self._lock:
            self._reset_if_new_day()
            checks = {
                "balance_ok": balance >= 100,
                "daily_loss_ok": await self._check_daily_loss(),
                "max_trades_ok": await self._check_max_trades(),
                "daily_trades_ok": self._daily_trades < self.config.max_daily_trades,
            }
            allowed = all(checks.values())
            if not allowed:
                failed = [k for k, v in checks.items() if not v]
                logger.warning(f"⚠️ Risk check failed: {failed}")
            return {"allowed": allowed, "checks": checks}

    async def record_trade(self):
        self._daily_trades += 1

    async def _check_daily_loss(self) -> bool:
        daily_pnl = await self.db.get_daily_pnl()
        return daily_pnl > -self.config.max_daily_loss_pct * 100

    async def _check_max_trades(self) -> bool:
        open_trades = await self.db.get_open_trades()
        return len(open_trades) < self.config.max_open_trades
