from threading import RLock
from time import monotonic
from typing import Any


class TTLCache:
    def __init__(self) -> None:
        self._values: dict[str, tuple[float, Any]] = {}
        self._lock = RLock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._values.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at <= monotonic():
                del self._values[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        with self._lock:
            self._values[key] = (monotonic() + ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._values.clear()


cache = TTLCache()
