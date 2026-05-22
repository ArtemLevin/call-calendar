"""Database session configuration and FastAPI dependency providers."""

from collections.abc import AsyncGenerator
from typing import Any
import os

DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///./call_calendar.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


class Base:
    """Fallback base used until SQLAlchemy-backed persistence is fully wired."""


engine: Any = None
AsyncSessionLocal: Any = None


async def get_db_session() -> AsyncGenerator[Any, None]:
    """Yield a DB session when SQLAlchemy stack is available."""
    raise RuntimeError(
        "Database session is not configured yet. Complete Alembic/Repository integration first."
    )
    yield
