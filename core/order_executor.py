"""
Order executor dengan safety checks.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict, Optional

from core.exchange import ExchangeManager
from core.risk_manager import RiskManager
from core.position_manager import PositionManager
from database.db_manager import DatabaseManager
from config import settings
from utils.logger import logger
from utils.notifier import Notifier


class OrderExecutor:
    """Handle order execution dengan risk integration."""

    def __init__(self, exchange: ExchangeManager, risk: RiskManager,
                 position_manager: PositionManager, db: DatabaseManager,
                 notifier: Notifier):
        self.exchange = exchange
        self.risk = risk
        self.positions = position_manager
        self.db = db
        self.notifier = notifier
        self._lock = asyncio.Lock()

    async def execute_signal(self, signal: Dict, balance: float) -> Optional[Dict]:
        """Execute trade signal."""
        if signal["type"] == "neutral":
            return None

        async with self._lock:
            # Risk check
            risk_check = await self.risk.can_open_trade(balance)
            if not risk_check["allowed"]:
                logger.warning("⚠️ Trade rejected by risk manager")
                return None

            # Position size
            size = self.risk.calculate_position_size(
                balance, signal["entry"], signal["stop_loss"]
            )
            if size <= 0:
                return None

            side = "buy" if signal["type"] == "long" else "sell"
            symbol = settings.trading.symbol

            try:
                # Entry order
                order = await self.exchange.create_order(symbol, side, size, "market")
                entry_price = float(order.get("average") or order.get("price") or signal["entry"])

                # Save trade
                trade_data = {
                    "symbol": symbol,
                    "side": signal["type"],
                    "entry_price": entry_price,
                    "amount": size,
                    "leverage": settings.trading.leverage,
                    "stop_loss": signal["stop_loss"],
                    "take_profit": signal["take_profit_2"],
                    "strategy": "ai_combo",
                    "signal_strength": signal["strength"],
                    "ai_confidence": signal["confidence"],
                    "ai_mode": signal.get("ai_mode", "technical"),
                    "ai_reasoning": signal.get("ai_reasoning", ""),
                    "status": "open",
                }
                trade_id = await self.db.save_trade(trade_data)

                # SL + TP
                try:
                    await self.exchange.create_stop_loss(symbol, side, size, signal["stop_loss"])
                    await self.exchange.create_take_profit(symbol, side, size, signal["take_profit_2"])
                except Exception as e:
                    logger.warning(f"SL/TP order warning: {e}")

                await self.risk.record_trade()

                trade_record = {**trade_data, "id": trade_id}
                logger.info(f"✅ Trade #{trade_id} executed: {signal['type'].upper()} @ {entry_price}")

                # Notify
                await self.notifier.notify_trade_opened(trade_record, signal)

                return trade_record

            except Exception as e:
                logger.exception(f"❌ Order execution failed: {e}")
                await self.notifier.notify_error(f"Order failed: {e}")
                return None

    async def close_position(self, trade: Dict, reason: str = "manual") -> bool:
        """Close existing position."""
        async with self._lock:
            try:
                symbol = trade["symbol"]
                side = "sell" if trade["side"] == "long" else "buy"
                amount = trade["amount"]

                # Cancel SL/TP
                try:
                    orders = await self.exchange.get_open_orders(symbol)
                    for o in orders:
                        await self.exchange.cancel_order(o["id"], symbol)
                except Exception:
                    pass

                # Close
                order = await self.exchange.create_order(
                    symbol, side, amount, "market", params={"reduceOnly": True}
                )
                exit_price = float(order.get("average") or order.get("price") or 0)

                # PnL
                if trade["side"] == "long":
                    pnl_pct = ((exit_price - trade["entry_price"]) / trade["entry_price"]) * 100
                else:
                    pnl_pct = ((trade["entry_price"] - exit_price) / trade["entry_price"]) * 100
                pnl = (exit_price - trade["entry_price"]) * amount * (1 if trade["side"] == "long" else -1)

                # Update DB
                await self.db.update_trade(trade["id"], {
                    "exit_price": exit_price,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "status": "closed",
                    "exit_time": datetime.utcnow(),
                    "exit_reason": reason,
                })

                trade["exit_price"] = exit_price
                trade["pnl"] = pnl
                trade["pnl_pct"] = pnl_pct

                logger.info(f"🏁 Closed #{trade['id']}: PnL {pnl:+.2f} ({pnl_pct:+.2f}%)")
                await self.notifier.notify_trade_closed(trade, reason)
                return True

            except Exception as e:
                logger.exception(f"❌ Close failed: {e}")
                await self.notifier.notify_error(f"Close failed: {e}")
                return False
