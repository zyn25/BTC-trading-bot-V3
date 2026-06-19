"""
Middlewares - Admin check + throttling.
"""
from __future__ import annotations

import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineQuery, TelegramObject
from cachetools import TTLCache

from utils.logger import logger


class AdminMiddleware(BaseMiddleware):
    """Whitelist middleware."""

    def __init__(self, admin_ids: list):
        self.admin_ids = set(admin_ids)

    async def __call__(self, handler, event: TelegramObject, data: Dict) -> Any:
        user = None
        if isinstance(event, (Message, CallbackQuery, InlineQuery)):
            user = event.from_user

        if not user:
            return None

        if user.id not in self.admin_ids:
            logger.warning(f"⛔ Unauthorized: {user.id}")
            if isinstance(event, Message):
                await event.answer("⛔ Unauthorized")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Unauthorized", show_alert=True)
            elif isinstance(event, InlineQuery):
                await event.answer([], cache_time=60)
            return None

        data["user"] = user
        return await handler(event, data)


class ThrottlingMiddleware(BaseMiddleware):
    """Rate limiting."""

    def __init__(self, rate: float = 1.0):
        self.rate = rate
        self.cache = TTLCache(maxsize=1000, ttl=rate * 2)

    async def __call__(self, handler, event: TelegramObject, data: Dict) -> Any:
        user = data.get("user")
        if not user:
            return await handler(event, data)

        now = time.monotonic()
        last = self.cache.get(user.id, 0)
        if now - last < self.rate:
            return None

        self.cache[user.id] = now
        return await handler(event, data)
