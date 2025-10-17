"""Helper utilities for working with configuration objects."""

from __future__ import annotations

from functools import lru_cache

from config.settings import Settings, get_settings


@lru_cache(maxsize=1)
def settings_dict() -> dict[str, object]:
    """Return the cached settings as a plain dictionary."""

    return get_settings().as_dict()


__all__ = ["Settings", "get_settings", "settings_dict"]

