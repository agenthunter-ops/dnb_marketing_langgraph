"""Application configuration management."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


@dataclass
class Settings:
    """Strongly-typed view of runtime configuration."""

    environment: str = "development"
    debug: bool = False
    azure_storage_account_url: Optional[str] = None
    azure_blob_container: Optional[str] = None

    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8000

    streamlit_port: int = 8501

    def as_dict(self) -> dict[str, object]:
        """Return a dictionary representation of the settings."""

        return {
            "environment": self.environment,
            "debug": self.debug,
            "azure_storage_account_url": self.azure_storage_account_url,
            "azure_blob_container": self.azure_blob_container,
            "fastapi_host": self.fastapi_host,
            "fastapi_port": self.fastapi_port,
            "streamlit_port": self.streamlit_port,
        }


def _str_to_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings from environment variables with sensible defaults."""

    return Settings(
        environment=os.getenv("APP_ENV", "development"),
        debug=_str_to_bool(os.getenv("APP_DEBUG")),
        azure_storage_account_url=os.getenv("AZURE_STORAGE_ACCOUNT_URL"),
        azure_blob_container=os.getenv("AZURE_BLOB_CONTAINER"),
        fastapi_host=os.getenv("FASTAPI_HOST", "0.0.0.0"),
        fastapi_port=int(os.getenv("FASTAPI_PORT", "8000")),
        streamlit_port=int(os.getenv("STREAMLIT_PORT", "8501")),
    )


__all__ = ["Settings", "get_settings"]

