"""
Async database manager.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
)

from config import settings
from database.models import Base, Trade, Signal, DailyStats, AIUsage
from utils.logger import logger


class DatabaseManager:
    """Async DB manager untuk semua operasi persistence."""

    def __init__(self, url: str = None):
        self.url = url or settings.database.url
        self.engine = create_async_engine(self.url, echo=settings.database.echo)
        self.session_factory = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def init_db(self):
        """Create all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database initialized")

    async def close(self):
        await self.engine.dispose()

    # ============ TRADES ============

    async def save_trade(self, trade_data: dict) -> int:
        async with self.session_factory() as session:
            trade = Trade(**trade_data)
            session.add(trade)
            await session.commit()
            await session.refresh(trade)
            return trade.id

    async def update_trade(self, trade_id: int, updates: dict) -> bool:
        async with self.session_factory() as session:
            trade = await session.get(Trade, trade_id)
            if not trade:
                return False
            for k, v in updates.items():
                setattr(trade, k, v)
            await session.commit()
            return True

    async def get_open_trades(self, symbol: Optional[str] = None) -> List[dict]:
        async with self.session_factory() as session:
            stmt = select(Trade).where(Trade.status == "open")
            if symbol:
                stmt = stmt.where(Trade.symbol == symbol)
            result = await session.execute(stmt)
            trades = result.scalars().all()
            return [t.to_dict() for t in trades]

    async def get_recent_trades(self, limit: int = 20) -> List[dict]:
        async with self.session_factory() as session:
            stmt = (
                select(Trade)
                .where(Trade.status == "closed")
                .order_by(Trade.exit_time.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [t.to_dict() for t in result.scalars().all()]

    async def get_daily_pnl(self) -> float:
        """Get today's PnL percentage."""
        async with self.session_factory() as session:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            stmt = (
                select(func.sum(Trade.pnl_pct))
                .where(and_(Trade.status == "closed", Trade.exit_time >= today_start))
            )
            result = await session.execute(stmt)
            return result.scalar() or 0.0

    async def get_winrate(self, days: int = 30) -> float:
        async with self.session_factory() as session:
            start = datetime.utcnow() - timedelta(days=days)
            total_stmt = (
                select(func.count(Trade.id))
                .where(and_(Trade.status == "closed", Trade.exit_time >= start))
            )
            total = (await session.execute(total_stmt)).scalar() or 0
            if total == 0:
                return 0.0
            wins_stmt = (
                select(func.count(Trade.id))
                .where(and_(Trade.status == "closed", Trade.exit_time >= start, Trade.pnl > 0))
            )
            wins = (await session.execute(wins_stmt)).scalar() or 0
            return (wins / total) * 100

    # ============ SIGNALS ============

    async def save_signal(self, signal_data: dict) -> int:
        async with self.session_factory() as session:
            sig = Signal(**signal_data)
            session.add(sig)
            await session.commit()
            await session.refresh(sig)
            return sig.id

    # ============ AI USAGE ============

    async def log_groq_usage(self, tokens: int = 0, error: bool = False, cache_hit: bool = False):
        async with self.session_factory() as session:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            stmt = select(AIUsage).where(AIUsage.date >= today)
            result = await session.execute(stmt)
            usage = result.scalar_one_or_none()
            if not usage:
                usage = AIUsage(date=today)
                session.add(usage)
            if not error and not cache_hit:
                usage.groq_calls += 1
                usage.groq_tokens += tokens
            if error:
                usage.groq_errors += 1
            if cache_hit:
                usage.cache_hits += 1
            await session.commit()

    async def get_today_groq_usage(self) -> dict:
        async with self.session_factory() as session:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            stmt = select(AIUsage).where(AIUsage.date >= today)
            result = await session.execute(stmt)
            usage = result.scalar_one_or_none()
            if usage:
                return {
                    "calls": usage.groq_calls,
                    "tokens": usage.groq_tokens,
                    "errors": usage.groq_errors,
                    "cache_hits": usage.cache_hits,
                }
            return {"calls": 0, "tokens": 0, "errors": 0, "cache_hits": 0}
