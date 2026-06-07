"""Structured logging. No verbose logging in production by default."""
import logging
import sys

from app.core.config import get_settings


def setup_logger(name: str) -> logging.Logger:
    """Return a logger with level from settings."""
    settings = get_settings()
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    return logger
