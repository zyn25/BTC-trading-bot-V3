"""
Position manager - monitor & trailing stop.
"""
from __future__ import annotations

import asyncio
from typing import Dict, List

from core.exchange import ExchangeManager
from database.db_manager import DatabaseManager
from config import settings
from utils.logger import logger


class PositionManager:
    """Monitor active positions."""

    def __init__(self, exchange: ExchangeManager, db: DatabaseManager):
        self.exchange = exchange
        self.db = db
        self.monitoring = False
        self._unrealized: Dict[int, Dict] = {}

    async def monitor_positions(self):
        """Main monitoring loop."""
        self.monitoring = True
        logger.info("👁️ Position monitor started")
        while self.monitoring:
            try:
                await self._check_all()
                await asyncio.sleep(settings.monitoring.position_check)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(30)
        logger.info("👁️ Position monitor stopped")

    async def _check_all(self):
        """Check all open positions."""
        trades = await self.db.get_open_trades()
        for trade in trades:
            try:
                ticker = await self.exchange.get_ticker(trade["symbol"])
                current_price = ticker["last"]
                self._update_pnl(trade, current_price)
                await self._check_trailing(trade, current_price)
            except Exception as e:
                logger.error(f"Check trade {trade['id']}: {e}")

    def _update_pnl(self, trade: Dict, current_price: float):
        if trade["side"] == "long":
            pnl_pct = ((current_price - trade["entry_price"]) / trade["entry_price"]) * 100
        else:
            pnl_pct = ((trade["entry_price"] - current_price) / trade["entry_price"]) * 100
        pnl = pnl_pct * trade["amount"] * trade.get("leverage", 5) * trade["entry_price"] / 100
        self._unrealized[trade["id"]] = {
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "current_price": current_price,
        }

    async def _check_trailing(self, trade: Dict, current_price: float):
        """Check trailing stop."""
        activation = settings.trading.trailing_activation_pct
        trailing = settings.trading.trailing_stop_pct

        if trade["side"] == "long":
            profit_pct = (current_price - trade["entry_price"]) / trade["entry_price"]
            if profit_pct > activation:
                new_sl = current_price * (1 - trailing)
                if trade["stop_loss"] < new_sl:
                    await self._move_sl(trade, new_sl)
        else:
            profit_pct = (trade["entry_price"] - current_price) / trade["entry_price"]
            if profit_pct > activation:
                new_sl = current_price * (1 + trailing)
                if trade["stop_loss"] > new_sl:
                    await self._move_sl(trade, new_sl)

    async def _move_sl(self, trade: Dict, new_sl: float):
        """Move stop loss."""
        try:
            # Cancel old, create new (simplified)
            await self.db.update_trade(trade["id"], {"stop_loss": new_sl})
            logger.info(f"📈 Trailing SL moved: {new_sl:.2f}")
        except Exception as e:
            logger.warning(f"Move SL failed: {e}")

    def get_unrealized_pnl(self, trade_id: int) -> Dict:
        return self._unrealized.get(trade_id, {"pnl": 0, "pnl_pct": 0, "current_price": 0})

    def get_total_unrealized_pnl(self) -> float:
        return sum(u["pnl"] for u in self._unrealized.values())

    async def get_open_positions_count(self) -> int:
        trades = await self.db.get_open_trades()
        return len(trades)

    def stop(self):
        self.monitoring = False
