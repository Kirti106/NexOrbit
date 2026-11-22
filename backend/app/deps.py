from fastapi import Depends
from sqlalchemy.orm import Session

from .core.config import Settings, get_settings
from .db.session import get_db


def settings_dependency() -> Settings:
    return get_settings()


__all__ = ["Depends", "Session", "Settings", "get_db", "settings_dependency"]
