import time
from collections import deque
from threading import Lock


class InMemoryRateLimiter:
    def __init__(self, requests_per_minute: int) -> None:
        self.requests_per_minute = requests_per_minute
        self._requests: dict[str, deque[float]] = {}
        self._lock = Lock()

    def allow(self, client_ip: str) -> bool:
        now = time.monotonic()
        cutoff = now - 60
        with self._lock:
            requests = self._requests.setdefault(client_ip, deque())
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if len(requests) >= self.requests_per_minute:
                return False
            requests.append(now)
            return True
