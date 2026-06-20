"""
Test AI strategy di historical data.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict, List

import pandas as pd

from ai.ai_orchestrator import AIOrchestrator
from ai.trend_detector import ti
from config import settings
from utils.logger import logger


class StrategyTester:
    """Test strategy di historical data dengan simulasi real trading."""

    def __init__(self, initial_balance: float = 10000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.trades: List[Dict] = []
        self.equity_curve: List[float] = []
        self.positions: Dict = {}  # {symbol: {side, entry, amount, sl, tp, ...}}
        self.ai = AIOrchestrator()

    async def run(self, df: pd.DataFrame, symbol: str = "BTC/USDT",
                  show_progress: bool = True) -> Dict:
        """
        Run backtest pada historical data.
        Simulasi real-time trading dengan AI signals.
        """
        await self.ai.initialize()
        logger.info(f"🚀 Starting backtest | Balance: ${self.initial_balance:,.2f}")
        logger.info(f"📊 Data: {len(df)} candles | Period: {df.index[0]} → {df.index[-1]}")

        # Warmup period (first 200 candles untuk indicators)
        warmup = 200
        if len(df) < warmup + 100:
            raise ValueError(f"Data terlalu sedikit. Minimal {warmup + 100} candles.")

        # Process each candle
        total = len(df) - warmup
        for i in range(warmup, len(df)):
            # Slice data sampai candle ini (simulasi real-time)
            current_df = df.iloc[:i+1].copy()
            current_price = current_df["close"].iloc[-1]
            current_time = current_df.index[-1]

            # Progress
            if show_progress and i % 100 == 0:
                pct = ((i - warmup) / total) * 100
                logger.info(f"  Progress: {pct:.1f}% | Trades: {len(self.trades)} | Balance: ${self.balance:,.2f}")

            # Check existing positions (SL/TP/Trailing)
            await self._check_positions(current_price, current_time)

            # Generate signal (every 15 candles = ~15 menit di TF 15m)
            if i % 15 == 0 and not self.positions:
                try:
                    signal = await self.ai.analyze(current_df, exchange=None, symbol=symbol)
                    if signal.get("should_trade"):
                        await self._execute_trade(signal, current_price, current_time)
                except Exception as e:
                    logger.debug(f"Signal error at {current_time}: {e}")

            # Track equity
            unrealized = self._calc_unrealized_pnl(current_price)
            self.equity_curve.append(self.balance + unrealized)

        # Close remaining positions
        if self.positions:
            for pos_id in list(self.positions.keys()):
                await self._close_position(pos_id, df["close"].iloc[-1], 
                                            df.index[-1], "end_of_test")

        await self.ai.close()

        return self._generate_report()

    async def _execute_trade(self, signal: Dict, price: float, timestamp):
        """Execute trade (simulasi)."""
        # Risk check
        risk_amount = self.balance * settings.trading.risk_per_trade
        sl_distance = abs(signal["entry"] - signal["stop_loss"])
        
        if sl_distance == 0:
            return

        position_size = (risk_amount / sl_distance) * signal["entry"] / signal["entry"]
        position_value = position_size * price

        # Max position check
        if position_value > self.balance * settings.trading.max_position_pct:
            position_size = (self.balance * settings.trading.max_position_pct) / price

        if position_size <= 0 or position_value > self.balance:
            return

        # Simulate execution (with slippage)
        slippage = 0.0005  # 0.05%
        if signal["type"] == "long":
            entry_price = price * (1 + slippage)
        else:
            entry_price = price * (1 - slippage)

        position = {
            "id": len(self.trades) + 1,
            "symbol": settings.trading.symbol,
            "side": signal["type"],
            "entry_price": entry_price,
            "entry_time": timestamp,
            "amount": position_size,
            "leverage": settings.trading.leverage,
            "stop_loss": signal["stop_loss"],
            "take_profit_1": signal["take_profit_1"],
            "take_profit_2": signal["take_profit_2"],
            "trailing_stop": signal["stop_loss"],
            "signal_strength": signal["strength"],
            "ai_confidence": signal["confidence"],
        }

        self.positions[position["id"]] = position
        self.balance -= position_value / settings.trading.leverage  # Margin

        logger.debug(
            f"📈 OPEN {position['side'].upper()} @ {entry_price:.2f} | "
            f"Size: {position_size:.6f} | Time: {timestamp}"
        )

    async def _check_positions(self, current_price: float, timestamp):
        """Check SL/TP/Trailing untuk semua posisi."""
        for pos_id in list(self.positions.keys()):
            pos = self.positions[pos_id]
            
            # Calculate current PnL
            if pos["side"] == "long":
                pnl_pct = (current_price - pos["entry_price"]) / pos["entry_price"]
            else:
                pnl_pct = (pos["entry_price"] - current_price) / pos["entry_price"]

            # Trailing stop update
            activation = settings.trading.trailing_activation_pct
            trailing = settings.trading.trailing_stop_pct
            
            if pnl_pct > activation:
                if pos["side"] == "long":
                    new_sl = current_price * (1 - trailing)
                    if new_sl > pos["trailing_stop"]:
                        pos["trailing_stop"] = new_sl
                else:
                    new_sl = current_price * (1 + trailing)
                    if new_sl < pos["trailing_stop"]:
                        pos["trailing_stop"] = new_sl

            # Check SL hit
            active_sl = pos["trailing_stop"]
            if pos["side"] == "long" and current_price <= active_sl:
                await self._close_position(pos_id, active_sl, timestamp, "stop_loss")
            elif pos["side"] == "short" and current_price >= active_sl:
                await self._close_position(pos_id, active_sl, timestamp, "stop_loss")

            # Check TP hit
            elif pos["side"] == "long" and current_price >= pos["take_profit_2"]:
                await self._close_position(pos_id, pos["take_profit_2"], timestamp, "take_profit")
            elif pos["side"] == "short" and current_price <= pos["take_profit_2"]:
                await self._close_position(pos_id, pos["take_profit_2"], timestamp, "take_profit")

    async def _close_position(self, pos_id: int, exit_price: float, 
                                timestamp, reason: str):
        """Close position dan catat trade."""
        pos = self.positions[pos_id]
        
        # Calculate PnL
        if pos["side"] == "long":
            pnl_pct = (exit_price - pos["entry_price"]) / pos["entry_price"]
        else:
            pnl_pct = (pos["entry_price"] - exit_price) / pos["entry_price"]

        pnl = pnl_pct * pos["amount"] * pos["entry_price"] * pos["leverage"]
        pnl -= abs(pnl) * 0.0004 * 2  # Fee (0.04% each side)

        # Update balance
        position_value = pos["amount"] * pos["entry_price"]
        self.balance += (position_value / pos["leverage"]) + pnl

        # Record trade
        trade = {
            **pos,
            "exit_price": exit_price,
            "exit_time": timestamp,
            "pnl": pnl,
            "pnl_pct": pnl_pct * 100,
            "exit_reason": reason,
        }
        self.trades.append(trade)

        del self.positions[pos_id]

        emoji = "✅" if pnl > 0 else "❌"
        logger.debug(
            f"{emoji} CLOSE {pos['side'].upper()} @ {exit_price:.2f} | "
            f"PnL: {pnl:+.2f} USDT ({pnl_pct*100:+.2f}%) | {reason}"
        )

    def _calc_unrealized_pnl(self, current_price: float) -> float:
        """Calculate total unrealized PnL."""
        total = 0
        for pos in self.positions.values():
            if pos["side"] == "long":
                pnl_pct = (current_price - pos["entry_price"]) / pos["entry_price"]
            else:
                pnl_pct = (pos["entry_price"] - current_price) / pos["entry_price"]
            total += pnl_pct * pos["amount"] * pos["entry_price"] * pos["leverage"]
        return total

    def _generate_report(self) -> Dict:
        """Generate backtest report."""
        from .metrics import calculate_metrics
        from .report import generate_report

        if not self.trades:
            return {"error": "No trades executed"}

        metrics = calculate_metrics(self.trades, self.initial_balance, self.balance)
        report = generate_report(metrics, self.trades, self.initial_balance, self.balance, 
                                  self.equity_curve)

        return {
            "metrics": metrics,
            "report": report,
            "trades": self.trades,
            "equity_curve": self.equity_curve,
        }
