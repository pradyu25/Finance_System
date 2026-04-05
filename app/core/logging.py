"""
Structured logging setup
=========================
Uses `loguru` to provide human-readable console output during development
and JSON-formatted records suitable for log aggregators in production.
"""

import sys
from app.core.config import settings
from loguru import logger


def setup_logging() -> None:
    """Configure the global loguru logger."""
    logger.remove()  # Remove the default handler

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
        "<level>{message}</level>"
    )

    # Console handler
    logger.add(
        sys.stderr,
        format=log_format,
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True,
    )

    # File handler (rotated daily, kept for 7 days)
    logger.add(
        "logs/finance_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="INFO",
        rotation="1 day",
        retention="7 days",
        compression="zip",
        enqueue=True,   # Thread-safe async logging
    )
