import time
from threading import Lock

from fastapi import Depends, HTTPException, Request, status

from .config import Settings, get_settings
from .core.security import verify_admin_key
from .db.session import get_db

_rate_lock = Lock()
_admin_requests: dict[str, list[float]] = {}


def settings_dependency(request: Request) -> Settings:
    settings = getattr(request.app.state, "settings", None)
    return settings if settings is not None else get_settings()


def ml_http_dependency(request: Request):
    return request.app.state.ml_http


def require_admin(request: Request, settings: Settings = Depends(settings_dependency)) -> None:
    verify_admin_key(request, settings)
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with _rate_lock:
        recent = [item for item in _admin_requests.get(client_ip, []) if now - item < 60]
        if len(recent) >= 10:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "rate_limited", "message": "Admin rate limit exceeded"},
            )
        recent.append(now)
        _admin_requests[client_ip] = recent


__all__ = ["get_db", "require_admin", "settings_dependency"]
