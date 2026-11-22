import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class MLUnavailable(RuntimeError):
    pass


class MLClient:
    def __init__(self, base_url: str, client: httpx.AsyncClient | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client

    async def open(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(8.0, connect=2.0),
            )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get_json(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self._client is None:
            await self.open()
        assert self._client is not None
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = await self._client.get(path, params=params)
                if response.status_code >= 500:
                    response.raise_for_status()
                if response.is_error:
                    raise MLUnavailable(
                        f"ML service rejected the request ({response.status_code})"
                    )
                return response.json()
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code < 500:
                    break
                if attempt < 2:
                    await asyncio.sleep(0.1 * (attempt + 1))
        logger.warning("ML service request failed for %s: %s", path, last_error)
        raise MLUnavailable("ML service is unavailable") from last_error
