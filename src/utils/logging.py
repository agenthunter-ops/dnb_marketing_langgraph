"""Shared logging utilities."""

from __future__ import annotations

import logging
from typing import Iterable

from config.settings import get_settings


def configure_logging(extra_handlers: Iterable[logging.Handler] | None = None) -> None:
    """Configure application-wide logging.

    Parameters
    ----------
    extra_handlers:
        Optional iterable of additional handlers to attach to the root logger.
    """

    settings = get_settings()

    level = logging.DEBUG if settings.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    root_logger = logging.getLogger()
    if extra_handlers:
        for handler in extra_handlers:
            root_logger.addHandler(handler)


__all__ = ["configure_logging"]

