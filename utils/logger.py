"""
Loguru-based logger setup dengan rotation dan colored output.
"""
from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger as _logger


def setup_logger(name: str = "bot", level: str = "INFO") -> "logger":
    """Setup logger dengan console + file output."""
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)

    # Remove default handler
    _logger.remove()

    # Console handler (colored)
    _logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level:<8}</level> | "
            "<cyan>{name:<15}</cyan> | "
            "<level>{message}</level>"
        ),
        level=level,
        colorize=True,
    )

    # File handler (rotated)
    _logger.add(
        "logs/bot_{time:YYYY-MM-DD}.log",
        rotation="100 MB",
        retention="7 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name:<15} | {message}",
        level=level,
    )

    # Error file (separate)
    _logger.add(
        "logs/errors_{time:YYYY-MM-DD}.log",
        rotation="50 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name:<15} | {message}",
        level="ERROR",
    )

    return _logger


# Global logger
logger = setup_logger()
