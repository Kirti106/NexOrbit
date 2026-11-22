"""Compatibility exports for database dependencies used by the routers."""

from .db.base import Base
from .db.session import SessionLocal, engine, get_db

__all__ = ["Base", "SessionLocal", "engine", "get_db"]
