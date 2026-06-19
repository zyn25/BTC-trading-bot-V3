"""
Command handlers.
"""
from __future__ import annotations

from aiogram import Dispatcher, types, F
from aiogram.filters import Command

from config import settings
from telegram_bot.formatters import MessageFormatter
from telegram_bot.keyboards import (
    get_main_keyboard, get_inline_positions, get_inline_settings, get_confirmation
)
from utils.logger import logger

fmt = MessageFormatter()


def register_handlers(dp: Dispatcher, strategy, executor, positions, db, ai):
    """Register command handlers."""

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        await message.answer(
            "🤖 <b>BTC Trading Bot v3.0</b>\n\n"
            "Welcome! Bot siap digunakan.\n"
            "Mode: <code>{}</code>".format(settings.ai.effective_mode),
            reply_markup=get_main_keyboard(),
        )

    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        await message.answer(
            "📖 <b>COMMANDS</b>\n\n"
            "/status - Bot status\n"
            "/balance - Saldo\n"
            "/positions - Posisi terbuka\n"
            "/history - Trade history\n"
            "/stats - Statistics\n"
            "/scan - Market scan\n"
            "/ai - AI info\n"
            "/pause - Pause trading\n"
            "/resume - Resume trading\n"
            "/emergency - Emergency close all\n"
            "/settings - Settings"
        )

    @dp.message(F.text == "📊 Status")
    @dp.message(Command("status"))
    async def cmd_status(message: types.Message):
        try:
            balance = await executor.exchange.get_balance()
            daily_pnl = await db.get_daily_pnl()
            winrate = await db.get_winrate(30)
            open_count = await positions.get_open_positions_count()
            text = fmt.status(
                strategy.running, balance, daily_pnl, open_count, winrate,
                settings.ai.effective_mode
            )
            await message.answer(text, reply_markup=get_inline_positions([]))
        except Exception as e:
            await message.answer(f"❌ Error: {e}")

    @dp.message(F.text == "💰 Balance")
    @dp.message(Command("balance"))
    async def cmd_balance(message: types.Message):
        try:
            balance = await executor.exchange.get_balance()
            await message.answer(fmt.balance(balance))
        except Exception as e:
            await message.answer(f"❌ Error: {e}")

    @dp.message(F.text == "📈 Positions")
    @dp.message(Command("positions"))
    async def cmd_positions(message: types.Message):
        trades = await db.get_open_trades()
        await message.answer(fmt.positions(trades), reply_markup=get_inline_positions(trades))

    @dp.message(F.text == "📜 History")
    @dp.message(Command("history"))
    async def cmd_history(message: types.Message):
        trades = await db.get_recent_trades(20)
        await message.answer(fmt.history(trades))

    @dp.message(F.text == "⏸️ Pause")
    @dp.message(Command("pause"))
    async def cmd_pause(message: types.Message):
        strategy.running = False
        await message.answer("⏸️ <b>Trading PAUSED</b>")

    @dp.message(F.text == "▶️ Resume")
    @dp.message(Command("resume"))
    async def cmd_resume(message: types.Message):
        strategy.running = True
        await message.answer("▶️ <b>Trading RESUMED</b>")

    @dp.message(F.text == "🔄 Scan")
    @dp.message(Command("scan"))
    async def cmd_scan(message: types.Message):
        msg = await message.answer("🔄 <i>Scanning...</i>")
        try:
            signal = await strategy.manual_scan()
            await msg.edit_text(fmt.signal(signal))
        except Exception as e:
            await msg.edit_text(f"❌ Scan error: {e}")

    @dp.message(F.text == "🤖 AI")
    @dp.message(Command("ai"))
    async def cmd_ai(message: types.Message):
        try:
            stats = await db.get_today_groq_usage()
            await message.answer(fmt.ai_info(settings.ai.effective_mode, settings.ai.has_groq, stats))
        except Exception as e:
            await message.answer(fmt.ai_info(settings.ai.effective_mode, settings.ai.has_groq))

    @dp.message(F.text == "🆘 Emergency")
    @dp.message(Command("emergency"))
    async def cmd_emergency(message: types.Message):
        await message.answer(
            "⚠️ <b>EMERGENCY STOP</b>\n\nClose SEMUA posisi?",
            reply_markup=get_confirmation("emergency"),
        )

    @dp.message(F.text == "⚙️ Settings")
    @dp.message(Command("settings"))
    async def cmd_settings(message: types.Message):
        await message.answer(
            "⚙️ <b>SETTINGS</b>",
            reply_markup=get_inline_settings(),
        )

    @dp.message(Command("stats"))
    async def cmd_stats(message: types.Message):
        wr = await db.get_winrate(30)
        pnl = await db.get_daily_pnl()
        await message.answer(
            f"📊 <b>STATS</b>\n\n"
            f"Win Rate (30d): <b>{wr:.1f}%</b>\n"
            f"Today PnL: <code>{pnl:+.2f}%</code>"
        )

    # Callback handlers
    @dp.callback_query(F.data.startswith("inline_close:"))
    async def cb_close(callback: types.CallbackQuery):
        trade_id = int(callback.data.split(":")[1])
        trades = await db.get_open_trades()
        trade = next((t for t in trades if t["id"] == trade_id), None)
        if trade:
            success = await executor.close_position(trade, "manual")
            if success:
                await callback.message.edit_text(f"✅ Position #{trade_id} closed")
            else:
                await callback.message.edit_text(f"❌ Failed to close #{trade_id}")
        await callback.answer()

    @dp.callback_query(F.data == "inline_emergency")
    async def cb_emergency(callback: types.CallbackQuery):
        await callback.message.edit_text(
            "⚠️ <b>CONFIRM EMERGENCY</b>\n\nClose ALL positions?",
            reply_markup=get_confirmation("emergency"),
        )

    @dp.callback_query(F.data.startswith("inline_confirm:"))
    async def cb_confirm(callback: types.CallbackQuery):
        action = callback.data.split(":", 1)[1]
        if action == "emergency":
            trades = await db.get_open_trades()
            count = 0
            for t in trades:
                if await executor.close_position(t, "emergency"):
                    count += 1
            await callback.message.edit_text(f"🚨 Emergency closed {count} positions")
        await callback.answer()

    @dp.callback_query(F.data == "inline_cancel")
    async def cb_cancel(callback: types.CallbackQuery):
        await callback.message.edit_text("❌ <b>Cancelled</b>")
        await callback.answer()

    @dp.callback_query(F.data == "inline_pause")
    async def cb_pause(callback: types.CallbackQuery):
        strategy.running = False
        await callback.message.edit_text("⏸️ <b>Trading PAUSED</b>")
        await callback.answer()

    @dp.callback_query(F.data == "inline_resume")
    async def cb_resume(callback: types.CallbackQuery):
        strategy.running = True
        await callback.message.edit_text("▶️ <b>Trading RESUMED</b>")
        await callback.answer()

    @dp.callback_query(F.data == "inline_scan")
    async def cb_scan(callback: types.CallbackQuery):
        await callback.answer("Scanning...")
        signal = await strategy.manual_scan()
        await callback.message.edit_text(fmt.signal(signal))

    @dp.callback_query(F.data == "inline_refresh")
    async def cb_refresh(callback: types.CallbackQuery):
        await callback.answer("Refreshing...")
        await cmd_status(callback.message)

    @dp.callback_query(F.data.startswith("inline_risk:"))
    async def cb_risk(callback: types.CallbackQuery):
        pct = int(callback.data.split(":")[1])
        # In production: update config
        await callback.message.edit_text(f"✅ Risk set to {pct}%")
        await callback.answer()

    @dp.callback_query(F.data.startswith("inline_lev:"))
    async def cb_lev(callback: types.CallbackQuery):
        lev = int(callback.data.split(":")[1])
        await callback.message.edit_text(f"✅ Leverage set to {lev}x")
        await callback.answer()
