"""
Helper functions.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pytz


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def format_price(price: float, decimals: int = 2) -> str:
    """Format price dengan separator."""
    return f"{price:,.{decimals}f}"


def format_pct(pct: float, decimals: int = 2) -> str:
    """Format percentage dengan sign."""
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.{decimals}f}%"


def format_duration(seconds: int) -> str:
    """Format duration ke human-readable."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    elif seconds < 86400:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}m"
    else:
        d = seconds // 86400
        h = (seconds % 86400) // 3600
        return f"{d}d {h}h"


def safe_float(value, default: float = 0.0) -> float:
    """Safely convert to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(value, max_val))
