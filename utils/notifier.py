"""
Telegram notifier untuk trade signals & alerts.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Bot

from config import settings
from utils.logger import logger

if TYPE_CHECKING:
    pass


class Notifier:
    """Send notifications via Telegram bot."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.admin_ids = settings.telegram.admin_ids

    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send message to all admins."""
        if not settings.notifications.enabled:
            return False
        success = True
        for admin_id in self.admin_ids:
            try:
                await self.bot.send_message(admin_id, text, parse_mode=parse_mode)
            except Exception as e:
                logger.warning(f"Notify failed for {admin_id}: {e}")
                success = False
        return success

    async def notify_trade_opened(self, trade: dict, signal: dict) -> None:
        """Notify trade opened."""
        if not settings.notifications.on_trade:
            return
        text = (
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  🚀 <b>NEW TRADE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 Side: <b>{trade['side'].upper()}</b>\n"
            f"💰 Entry: <code>{trade['entry_price']:.2f}</code>\n"
            f"📦 Size: <code>{trade['amount']:.6f}</code>\n"
            f"⚡ Leverage: <b>{trade.get('leverage', 5)}x</b>\n\n"
            f"🛡 SL: <code>{trade['stop_loss']:.2f}</code>\n"
            f"🎯 TP: <code>{trade['take_profit']:.2f}</code>\n\n"
            f"💪 Strength: <code>{signal.get('strength', 0):.0%}</code>\n"
            f"🧠 Confidence: <code>{signal.get('confidence', 0):.0%}</code>\n"
            f"🤖 AI: <code>{settings.ai.effective_mode}</code>"
        )
        await self.send_message(text)

    async def notify_trade_closed(self, trade: dict, reason: str) -> None:
        """Notify trade closed."""
        if not settings.notifications.on_trade:
            return
        pnl = trade.get('pnl', 0)
        pnl_pct = trade.get('pnl_pct', 0)
        emoji = "✅" if pnl >= 0 else "❌"
        sign = "+" if pnl >= 0 else ""

        text = (
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  {emoji} <b>POSITION CLOSED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 Side: <b>{trade['side'].upper()}</b>\n"
            f"💰 Entry: <code>{trade['entry_price']:.2f}</code>\n"
            f"💵 Exit: <code>{trade.get('exit_price', 0):.2f}</code>\n\n"
            f"💰 PnL: <code>{sign}{pnl:.2f} USDT</code>\n"
            f"📈 PnL %: <code>{sign}{pnl_pct:.2f}%</code>\n\n"
            f"🎯 Reason: <b>{reason}</b>"
        )
        await self.send_message(text)

    async def notify_error(self, error_msg: str) -> None:
        """Notify error."""
        if not settings.notifications.on_error:
            return
        text = (
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  🚨 <b>ERROR</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<code>{error_msg[:500]}</code>"
        )
        await self.send_message(text)

    async def notify_risk_alert(self, alert_type: str, details: str) -> None:
        """Notify risk alert."""
        text = (
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  ⚠️ <b>RISK ALERT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>{alert_type}</b>\n\n"
            f"{details}"
        )
        await self.send_message(text)

    async def notify_daily_summary(self, stats: dict) -> None:
        """Send daily summary."""
        if not settings.notifications.on_daily_summary:
            return
        sign = "+" if stats.get('total_pnl', 0) >= 0 else ""
        text = (
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  📊 <b>DAILY REPORT</b>\n"
            f"  📅 {stats.get('date', 'Today')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📈 Trades: <b>{stats.get('total_trades', 0)}</b>\n"
            f"✅ Winners: <b>{stats.get('wins', 0)}</b>\n"
            f"❌ Losers: <b>{stats.get('losses', 0)}</b>\n\n"
            f"💰 Total PnL: <code>{sign}{stats.get('total_pnl', 0):.2f} USDT</code>\n"
            f"📈 PnL %: <code>{sign}{stats.get('total_pnl_pct', 0):.2f}%</code>\n\n"
            f"🏆 Best: <code>+{stats.get('best_trade', 0):.2f}</code>\n"
            f"📉 Worst: <code>{stats.get('worst_trade', 0):.2f}</code>"
        )
        await self.send_message(text)
