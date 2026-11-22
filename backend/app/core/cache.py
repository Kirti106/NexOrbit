import hashlib
import json
import time
from threading import RLock
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response


class TTLCache:
    def __init__(self) -> None:
        self._values: dict[str, tuple[float, Any]] = {}
        self._lock = RLock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._values.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at <= time.monotonic():
                self._values.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        with self._lock:
            self._values[key] = (time.monotonic() + ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._values.clear()


cache = TTLCache()


def apply_etag(
    request: Request,
    response: Response,
    data: Any,
    ttl: int,
) -> Response | None:
    body = json.dumps(
        jsonable_encoder(data),
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    etag = f'W/"{hashlib.sha256(body).hexdigest()}"'
    headers = {
        "ETag": etag,
        "Cache-Control": f"public, max-age={ttl}",
    }
    response.headers.update(headers)
    candidates = {
        value.strip()
        for value in request.headers.get("If-None-Match", "").split(",")
    }
    if "*" in candidates or etag in candidates or etag[2:] in candidates:
        return Response(status_code=304, headers=headers)
    return None
