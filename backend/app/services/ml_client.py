"""Thin async client for the ML API. The backend never recomputes ML output."""
from typing import Any

import httpx
from fastapi import HTTPException

from ..config import ML_API_TIMEOUT, ML_API_URL

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=ML_API_URL,
            timeout=ML_API_TIMEOUT,
            headers={"User-Agent": "NexOrbit-backend/1.0"},
        )
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def ml_get(path: str, params: dict[str, Any] | None = None) -> Any:
    """GET from the ML API and return its JSON unchanged.

    Upstream 4xx errors are passed through (404 unknown satellite, 422 bad
    input). Connection problems become 502, timeouts become 504.
    """
    clean = {k: v for k, v in (params or {}).items() if v is not None}
    try:
        response = await get_client().get(path, params=clean)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="ML API timed out") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"ML API unreachable at {ML_API_URL}. Is the ml_api service running?",
        ) from exc

    if 400 <= response.status_code < 500:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise HTTPException(status_code=response.status_code, detail=detail)
    if response.status_code >= 500:
        raise HTTPException(status_code=502, detail="ML API returned an error")
    return response.json()
