import secrets

from fastapi import HTTPException, Request, status

from .config import Settings


def verify_admin_key(request: Request, settings: Settings) -> None:
    supplied = request.headers.get("X-API-Key", "")
    if not settings.admin_api_key or not secrets.compare_digest(
        supplied, settings.admin_api_key
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "A valid X-API-Key is required"},
        )
