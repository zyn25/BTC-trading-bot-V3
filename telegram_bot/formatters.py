"""
Message formatters - futuristic style.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List


class MessageFormatter:
    """Format messages dengan style futuristik."""

    @staticmethod
    def status(running: bool, balance: Dict, daily_pnl: float,
               open_count: int, winrate: float, ai_mode: str = "technical") -> str:
        status_emoji = "🟢" if running else "🔴"
        pnl_emoji = "📈" if daily_pnl >= 0 else "📉"
        return (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  {status_emoji} <b>BOT STATUS</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚡ Trading: <b>{'ACTIVE' if running else 'PAUSED'}</b>\n"
            f"💰 Balance: <code>{balance['total']:,.2f} USDT</code>\n"
            f"💵 Free: <code>{balance['free']:,.2f} USDT</code>\n"
            f"{pnl_emoji} Daily PnL: <code>{daily_pnl:+.2f}%</code>\n"
            f"📊 Open: <b>{open_count}/{settings.trading.max_open_trades if False else 2}</b>\n"
            f"🎯 Win Rate: <b>{winrate:.1f}%</b>\n"
            f"🤖 AI: <code>{ai_mode}</code>\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )

    @staticmethod
    def positions(trades: List[Dict]) -> str:
        if not trades:
            return "📭 <b>Tidak ada posisi terbuka</b>"
        text = "━━━━━━━━━━━━━━━━━━━━━━\n  📊 <b>OPEN POSITIONS</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for t in trades:
            side_emoji = "🟢" if t["side"] == "long" else "🔴"
            text += (
                f"{side_emoji} <b>#{t['id']} {t['side'].upper()}</b>\n"
                f"   Entry: <code>{t['entry_price']:.2f}</code>\n"
                f"   Size: <code>{t['amount']:.6f}</code>\n"
                f"   SL: <code>{t.get('stop_loss', 0):.2f}</code>\n"
                f"   TP: <code>{t.get('take_profit', 0):.2f}</code>\n\n"
            )
        text += "━━━━━━━━━━━━━━━━━━━━━━"
        return text

    @staticmethod
    def history(trades: List[Dict]) -> str:
        if not trades:
            return "📜 <b>Belum ada history</b>"
        wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        wr = (wins / len(trades)) * 100
        sign = "+" if total_pnl >= 0 else ""
        text = (
            f"━━━━━━━━━━━━━━━━━━━━━━\n  📜 <b>HISTORY</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 {len(trades)} trades | WR: {wr:.1f}%\n"
            f"💰 Total: <code>{sign}{total_pnl:.2f} USDT</code>\n\n"
        )
        for t in trades[:10]:
            emoji = "✅" if t.get("pnl", 0) > 0 else "❌"
            side_e = "🟢" if t["side"] == "long" else "🔴"
            text += (
                f"{emoji} {side_e} #{t['id']} "
                f"<code>{t['entry_price']:.0f}</code>→<code>{t.get('exit_price', 0):.0f}</code> "
                f"<code>{t.get('pnl', 0):+.2f}</code>\n"
            )
        text += "━━━━━━━━━━━━━━━━━━━━━━"
        return text

    @staticmethod
    def signal(signal: Dict) -> str:
        if signal["type"] == "neutral":
            return "🔍 <b>No tradeable signal</b>\n\nMarket dalam kondisi netral."
        emoji = "🚀" if signal["type"] == "long" else "🔻"
        return (
            f"━━━━━━━━━━━━━━━━━━━━━━\n  {emoji} <b>SIGNAL</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 Type: <b>{signal['type'].upper()}</b>\n"
            f"💪 Strength: <code>{signal['strength']:.0%}</code>\n"
            f"🧠 Confidence: <code>{signal['confidence']:.0%}</code>\n"
            f"🤖 AI: <code>{signal.get('ai_mode', 'technical')}</code>\n\n"
            f"💰 Entry: <code>${signal['entry']:.2f}</code>\n"
            f"🛡 SL: <code>${signal['stop_loss']:.2f}</code>\n"
            f"🎯 TP1: <code>${signal['take_profit_1']:.2f}</code>\n"
            f"🎯 TP2: <code>${signal['take_profit_2']:.2f}</code>\n"
            f"📈 R:R: <b>1:{signal['risk_reward']:.1f}</b>\n\n"
            f"💭 {signal.get('ai_reasoning', 'Technical analysis')[:200]}\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )

    @staticmethod
    def balance(balance: Dict) -> str:
        return (
            f"💰 <b>BALANCE</b>\n\n"
            f"Total: <code>{balance['total']:,.2f} USDT</code>\n"
            f"Free: <code>{balance['free']:,.2f} USDT</code>\n"
            f"Margin: <code>{balance['used']:,.2f} USDT</code>"
        )

    @staticmethod
    def ai_info(ai_mode: str, has_groq: bool, stats: Dict = None) -> str:
        text = (
            f"━━━━━━━━━━━━━━━━━━━━━━\n  🤖 <b>AI STATUS</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Mode: <code>{ai_mode}</code>\n"
            f"Groq: <b>{'✅ Active' if has_groq else '❌ Disabled'}</b>\n"
        )
        if stats and has_groq:
            text += (
                f"\n📊 Today's Usage:\n"
                f"  Calls: <code>{stats.get('calls', 0)}</code>\n"
                f"  Tokens: <code>{stats.get('tokens', 0):,}</code>\n"
                f"  Errors: <code>{stats.get('errors', 0)}</code>\n"
                f"  Cache hits: <code>{stats.get('cache_hits', 0)}</code>\n"
            )
        text += "━━━━━━━━━━━━━━━━━━━━━━"
        return text
