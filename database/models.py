"""
SQLAlchemy 2.0 async models.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    side: Mapped[str] = mapped_column(String(10))
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float] = mapped_column(Float, nullable=True)
    amount: Mapped[float] = mapped_column(Float)
    leverage: Mapped[int] = mapped_column(Integer, default=5)
    stop_loss: Mapped[float] = mapped_column(Float, nullable=True)
    take_profit: Mapped[float] = mapped_column(Float, nullable=True)
    pnl: Mapped[float] = mapped_column(Float, default=0.0)
    pnl_pct: Mapped[float] = mapped_column(Float, default=0.0)
    fee: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    strategy: Mapped[str] = mapped_column(String(50), nullable=True)
    signal_strength: Mapped[float] = mapped_column(Float, nullable=True)
    ai_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    ai_mode: Mapped[str] = mapped_column(String(20), nullable=True)
    ai_reasoning: Mapped[str] = mapped_column(Text, nullable=True)
    entry_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    exit_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    exit_reason: Mapped[str] = mapped_column(String(50), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "amount": self.amount,
            "leverage": self.leverage,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
            "status": self.status,
            "strategy": self.strategy,
            "signal_strength": self.signal_strength,
            "ai_confidence": self.ai_confidence,
            "ai_mode": self.ai_mode,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "exit_reason": self.exit_reason,
        }


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20))
    signal_type: Mapped[str] = mapped_column(String(20))
    strength: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    trend: Mapped[str] = mapped_column(String(20), nullable=True)
    sentiment: Mapped[str] = mapped_column(String(20), nullable=True)
    ai_mode: Mapped[str] = mapped_column(String(20), nullable=True)
    ai_reasoning: Mapped[str] = mapped_column(Text, nullable=True)
    indicators_json: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    executed: Mapped[bool] = mapped_column(Boolean, default=False)


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, unique=True, index=True)
    total_trades: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    total_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    total_pnl_pct: Mapped[float] = mapped_column(Float, default=0.0)
    max_drawdown: Mapped[float] = mapped_column(Float, default=0.0)
    best_trade: Mapped[float] = mapped_column(Float, default=0.0)
    worst_trade: Mapped[float] = mapped_column(Float, default=0.0)


class AIUsage(Base):
    """Track Groq API usage."""
    __tablename__ = "ai_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    groq_calls: Mapped[int] = mapped_column(Integer, default=0)
    groq_tokens: Mapped[int] = mapped_column(Integer, default=0)
    groq_errors: Mapped[int] = mapped_column(Integer, default=0)
    cache_hits: Mapped[int] = mapped_column(Integer, default=0)
