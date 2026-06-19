"""
Main entry point dengan graceful shutdown.
"""
from __future__ import annotations

import asyncio
import signal
import sys
from pathlib import Path

from config import settings
from utils.logger import logger

# Ensure directories
Path("data").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)

from ai.ai_orchestrator import AIOrchestrator
from core.exchange import ExchangeManager
from core.market_analyzer import MarketAnalyzer
from core.order_executor import OrderExecutor
from core.position_manager import PositionManager
from core.risk_manager import RiskManager
from core.strategy import StrategyEngine
from database.db_manager import DatabaseManager
from telegram_bot.bot import TelegramBot
from utils.notifier import Notifier


class TradingBotApp:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.tasks = []
        self.db = None
        self.exchange = None
        self.ai = None
        self.notifier = None

    async def setup(self):
        logger.info("=" * 60)
        logger.info(f"🚀 BTC Trading Bot v3.0 | {settings.env.upper()}")
        logger.info(f"📊 {settings.trading.symbol} | {settings.trading.timeframe}")
        logger.info(f"🤖 AI: {settings.ai.effective_mode}")
        logger.info("=" * 60)

        try:
            settings.validate_for_production()
        except ValueError as e:
            logger.warning(f"Config warning: {e}")

        # Initialize
        self.db = DatabaseManager()
        await self.db.init_db()

        self.exchange = ExchangeManager()
        await self.exchange.connect()
        await self.exchange.set_leverage(settings.trading.leverage, settings.trading.symbol)

        self.ai = AIOrchestrator()
        await self.ai.initialize()

        self.notifier = Notifier(bot=None)  # Will set bot later

        risk = RiskManager(settings.trading, self.db)
        market = MarketAnalyzer(self.exchange, self.ai)
        await market.warmup()

        positions = PositionManager(self.exchange, self.db)
        executor = OrderExecutor(self.exchange, risk, positions, self.db, self.notifier)
        strategy = StrategyEngine(market, self.ai, executor, risk, self.notifier)

        # Telegram
        telegram = TelegramBot(strategy, executor, positions, self.db, self.ai)
        self.notifier.bot = telegram.bot  # Inject bot

        self._tasks = [
            ("strategy", strategy.run_loop),
            ("positions", positions.monitor_positions),
            ("telegram", telegram.start),
        ]
        return telegram

    async def run(self):
        telegram = await self.setup()
        self.tasks = [asyncio.create_task(fn(), name=name) for name, fn in self._tasks]

        # Handle signals
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self.shutdown_event.set)

        logger.info("✅ All systems running")

        # Wait for shutdown
        await self.shutdown_event.wait()
        await self.shutdown(telegram)

    async def shutdown(self, telegram):
        logger.info("🛑 Shutting down...")
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        try:
            await telegram.stop()
        except Exception:
            pass
        if self.ai:
            await self.ai.close()
        if self.exchange:
            await self.exchange.close()
        if self.db:
            await self.db.close()
        logger.info("✅ Shutdown complete")


async def main():
    app = TradingBotApp()
    try:
        await app.run()
    except KeyboardInterrupt:
        logger.info("Interrupted")
    except Exception as e:
        logger.exception(f"Fatal: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
