import hmac
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import Depends, Header, HTTPException, Request, status

from .config import get_settings

_requests: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def require_admin_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = get_settings().admin_api_key
    if not expected or not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def limit_admin_requests(request: Request, _: None = Depends(require_admin_key)) -> None:
    key = request.client.host if request.client else "unknown"
    now = monotonic()
    with _lock:
        window = _requests[key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= 10:
            raise HTTPException(status_code=429, detail="Admin rate limit exceeded")
        window.append(now)
