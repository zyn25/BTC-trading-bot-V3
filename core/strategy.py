"""
Strategy orchestrator.
"""
from __future__ import annotations

import asyncio
from typing import Dict, Optional

from ai.ai_orchestrator import AIOrchestrator
from config import settings
from core.market_analyzer import MarketAnalyzer
from core.order_executor import OrderExecutor
from core.risk_manager import RiskManager
from utils.logger import logger
from utils.notifier import Notifier


class StrategyEngine:
    """Main strategy orchestrator."""

    def __init__(self, analyzer: MarketAnalyzer, ai: AIOrchestrator,
                 executor: OrderExecutor, risk: RiskManager, notifier: Notifier):
        self.analyzer = analyzer
        self.ai = ai
        self.executor = executor
        self.risk = risk
        self.notifier = notifier
        self.running = False

    async def run_loop(self):
        """Main loop."""
        self.running = True
        logger.info("🎯 Strategy started")
        while self.running:
            try:
                await self._cycle()
                await asyncio.sleep(settings.monitoring.scan)
            except Exception as e:
                logger.exception(f"Strategy error: {e}")
                await asyncio.sleep(30)

    async def _cycle(self):
        """Single cycle."""
        signal = await self.analyzer.get_current_analysis()
        if not signal.get("should_trade"):
            return

        balance_info = await self.executor.exchange.get_balance()
        balance = balance_info["free"]

        if balance < 100:
            logger.warning("⚠️ Balance too low")
            return

        await self.executor.execute_signal(signal, balance)

    async def manual_scan(self) -> Dict:
        """Manual market scan."""
        return await self.analyzer.get_current_analysis()

    def stop(self):
        self.running = False
