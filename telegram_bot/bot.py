"""
Telegram bot orchestrator.
"""
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from telegram_bot.handlers import register_handlers
from telegram_bot.inline import register_inline_handlers
from telegram_bot.middlewares import AdminMiddleware, ThrottlingMiddleware
from utils.logger import logger


class TelegramBot:
    """Telegram bot controller."""

    def __init__(self, strategy, executor, positions, db, ai_orchestrator):
        self.bot = Bot(
            token=settings.telegram.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        self.dp = Dispatcher(storage=MemoryStorage())

        # Middlewares
        self.dp.message.middleware(AdminMiddleware(settings.telegram.admin_ids))
        self.dp.callback_query.middleware(AdminMiddleware(settings.telegram.admin_ids))
        self.dp.inline_query.middleware(AdminMiddleware(settings.telegram.admin_ids))
        self.dp.message.middleware(ThrottlingMiddleware(1.0))

        # Handlers
        register_handlers(self.dp, strategy, executor, positions, db, ai_orchestrator)
        register_inline_handlers(self.dp, self.bot, strategy, executor, positions, db, ai_orchestrator)

        self.strategy = strategy
        self.executor = executor

    async def start(self):
        logger.info("📱 Starting Telegram bot...")
        try:
            await self.bot.delete_webhook(drop_pending_updates=True)
            await self.dp.start_polling(
                self.bot,
                allowed_updates=["message", "callback_query", "inline_query", "chosen_inline_result"],
            )
        except Exception as e:
            logger.exception(f"Telegram error: {e}")

    async def stop(self):
        try:
            await self.bot.session.close()
        except Exception:
            pass
