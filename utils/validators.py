"""
Input validation utilities.
"""
from __future__ import annotations

from typing import Tuple


def validate_amount(amount_str: str, balance: float, price: float) -> Tuple[bool, float, str]:
    """Validate trade amount. Returns (is_valid, amount, error_msg)."""
    try:
        amount = float(amount_str)
    except (ValueError, TypeError):
        return False, 0.0, "Invalid amount format"

    if amount <= 0:
        return False, 0.0, "Amount must be > 0"

    max_amount = (balance * 0.5) / price  # Max 50% balance
    if amount > max_amount:
        return False, 0.0, f"Amount too large (max: {max_amount:.6f})"

    return True, amount, ""


def validate_risk_pct(risk_str: str) -> Tuple[bool, float, str]:
    """Validate risk percentage."""
    try:
        pct = float(risk_str)
    except (ValueError, TypeError):
        return False, 0.0, "Invalid risk format"

    if not 0.5 <= pct <= 5.0:
        return False, 0.0, "Risk must be between 0.5% and 5%"

    return True, pct / 100, ""


def validate_leverage(lev_str: str) -> Tuple[bool, int, str]:
    """Validate leverage value."""
    try:
        lev = int(lev_str)
    except (ValueError, TypeError):
        return False, 0, "Invalid leverage format"

    if not 1 <= lev <= 20:
        return False, 0, "Leverage must be between 1x and 20x"

    return True, lev, ""


def validate_position_id(id_str: str) -> Tuple[bool, int, str]:
    """Validate position ID."""
    try:
        pos_id = int(id_str)
    except (ValueError, TypeError):
        return False, 0, "Invalid position ID"

    if pos_id <= 0:
        return False, 0, "Position ID must be positive"

    return True, pos_id, ""
