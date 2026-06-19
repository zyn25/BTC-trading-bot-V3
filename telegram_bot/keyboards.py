"""
Reply & Inline keyboards.
"""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton,
)


def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Status"), KeyboardButton(text="💰 Balance")],
            [KeyboardButton(text="📈 Positions"), KeyboardButton(text="📜 History")],
            [KeyboardButton(text="⏸️ Pause"), KeyboardButton(text="▶️ Resume")],
            [KeyboardButton(text="🔄 Scan"), KeyboardButton(text="🤖 AI")],
            [KeyboardButton(text="🆘 Emergency"), KeyboardButton(text="⚙️ Settings")],
        ],
        resize_keyboard=True,
    )


def get_inline_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏸️ Pause", callback_data="inline_pause"),
            InlineKeyboardButton(text="📊 Scan", callback_data="inline_scan"),
        ],
        [
            InlineKeyboardButton(text="📈 Positions", callback_data="inline_positions"),
            InlineKeyboardButton(text="📜 History", callback_data="inline_history"),
        ],
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="inline_refresh"),
        ],
        [
            InlineKeyboardButton(text="🆘 Emergency", callback_data="inline_emergency"),
        ],
    ])


def get_inline_positions(trades: list) -> InlineKeyboardMarkup:
    buttons = []
    for t in trades:
        buttons.append([
            InlineKeyboardButton(
                text=f"❌ Close #{t['id']}",
                callback_data=f"inline_close:{t['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔄 Refresh", callback_data="inline_refresh")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_inline_settings() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Risk 1%", callback_data="inline_risk:1"),
            InlineKeyboardButton(text="Risk 2%", callback_data="inline_risk:2"),
            InlineKeyboardButton(text="Risk 3%", callback_data="inline_risk:3"),
        ],
        [
            InlineKeyboardButton(text="Lev 3x", callback_data="inline_lev:3"),
            InlineKeyboardButton(text="Lev 5x", callback_data="inline_lev:5"),
            InlineKeyboardButton(text="Lev 10x", callback_data="inline_lev:10"),
        ],
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="inline_refresh"),
        ],
    ])


def get_confirmation(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm", callback_data=f"inline_confirm:{action}"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="inline_cancel"),
        ]
    ])


def get_buy_sell_confirm(amount: float, side: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"✅ Confirm {side.upper()} {amount}",
                callback_data=f"inline_{side}:{amount}"
            ),
            InlineKeyboardButton(text="❌ Cancel", callback_data="inline_cancel"),
        ]
    ])
