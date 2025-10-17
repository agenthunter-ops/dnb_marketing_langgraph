"""Client utilities for interacting with the Brand Centre service."""
from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

import httpx
from azure.identity import ClientSecretCredential, DefaultAzureCredential, TokenCredential

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BrandAsset:
    """Represents an asset stored in Brand Centre."""

    asset_id: str
    brand: str
    title: str
    locale: Optional[str]
    compliance_tags: List[str]
    content_url: str
    updated_at: dt.datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class BrandCenterClient:
    """Client to authenticate against Brand Centre and fetch documents/assets.

    The client wraps the authentication flow using Azure AD credentials and exposes
    helper methods for fetching metadata and asset content. All HTTP interactions
    are performed with ``httpx`` which keeps the implementation fast and testable.
    """

    def __init__(
        self,
        base_url: str,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        scope: Optional[str] = None,
        *,
        timeout: float = 30.0,
        credential: Optional[TokenCredential] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._scope = scope or f"{self._base_url}/.default"
        self._timeout = timeout
        self._credential = credential or self._build_credential(
            tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
        )
        self._client = httpx.Client(timeout=self._timeout)
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0

    @staticmethod
    def _build_credential(
        *, tenant_id: Optional[str], client_id: Optional[str], client_secret: Optional[str]
    ) -> TokenCredential:
        if tenant_id and client_id and client_secret:
            logger.debug("Using ClientSecretCredential for Brand Centre authentication")
            return ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
        logger.debug("Using DefaultAzureCredential for Brand Centre authentication")
        return DefaultAzureCredential()

    def _get_access_token(self) -> str:
        now = dt.datetime.utcnow().timestamp()
        if self._token and now < self._token_expiry - 60:
            return self._token
        token = self._credential.get_token(self._scope)
        self._token = token.token
        try:
            self._token_expiry = float(token.expires_on)
        except (TypeError, ValueError):
            self._token_expiry = now + 3600
        logger.debug("Obtained new Brand Centre access token expiring at %s", self._token_expiry)
        return self._token

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        headers = {"Authorization": f"Bearer {self._get_access_token()}"}
        if not url.startswith("http"):
            url = f"{self._base_url}{url}"
        response = self._client.request(method, url, params=params, json=json, headers=headers)
        response.raise_for_status()
        return response

    def list_assets(
        self,
        *,
        brand: str,
        locale: Optional[str] = None,
        modified_since: Optional[dt.datetime] = None,
        page_size: int = 100,
    ) -> List[BrandAsset]:
        params: Dict[str, Any] = {"brand": brand, "page_size": page_size}
        if locale:
            params["locale"] = locale
        if modified_since:
            timestamp = (
                modified_since.replace(tzinfo=dt.timezone.utc)
                if modified_since.tzinfo is None
                else modified_since.astimezone(dt.timezone.utc)
            )
            params["modified_since"] = timestamp.isoformat()

        assets: List[BrandAsset] = []
        next_page: Optional[str] = "/api/assets"
        while next_page:
            response = self._request("GET", next_page, params=params)
            payload = response.json()
            for item in payload.get("items", []):
                assets.append(self._deserialize_asset(item))
            next_page = payload.get("next")
            params = {}
        logger.info("Fetched %s assets for brand %s", len(assets), brand)
        return assets

    def stream_assets(
        self,
        *,
        brand: str,
        locale: Optional[str] = None,
        modified_since: Optional[dt.datetime] = None,
        page_size: int = 100,
    ) -> Iterable[BrandAsset]:
        params: Dict[str, Any] = {"brand": brand, "page_size": page_size}
        if locale:
            params["locale"] = locale
        if modified_since:
            timestamp = (
                modified_since.replace(tzinfo=dt.timezone.utc)
                if modified_since.tzinfo is None
                else modified_since.astimezone(dt.timezone.utc)
            )
            params["modified_since"] = timestamp.isoformat()

        next_page: Optional[str] = "/api/assets"
        while next_page:
            response = self._request("GET", next_page, params=params)
            payload = response.json()
            for item in payload.get("items", []):
                yield self._deserialize_asset(item)
            next_page = payload.get("next")
            params = {}

    def download_asset_text(self, asset: BrandAsset) -> str:
        response = self._request("GET", asset.content_url)
        if "application/json" in response.headers.get("content-type", ""):
            payload = response.json()
            return payload.get("content", "")
        return response.text

    @staticmethod
    def _deserialize_asset(payload: Dict[str, Any]) -> BrandAsset:
        updated_raw = payload.get("updated_at")
        if isinstance(updated_raw, str):
            updated_raw = updated_raw.replace("Z", "+00:00")
        updated_at = dt.datetime.fromisoformat(updated_raw) if updated_raw else dt.datetime.utcnow()

        return BrandAsset(
            asset_id=str(payload["id"]),
            brand=payload.get("brand", ""),
            title=payload.get("title", ""),
            locale=payload.get("locale"),
            compliance_tags=payload.get("compliance_tags", []),
            content_url=payload.get("content_url", ""),
            updated_at=updated_at,
            metadata={k: v for k, v in payload.items() if k not in {
                "id",
                "brand",
                "title",
                "locale",
                "compliance_tags",
                "content_url",
                "updated_at",
            }},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BrandCenterClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
