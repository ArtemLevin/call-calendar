from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Booking, Colleague, MeetingSettings
from app.db.session import Base
from app.schemas.booking import MeetingDurationMinutes, MeetingProvider, MeetingTimezone


@pytest.fixture(scope="session")
def test_db_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    # Why: file-backed SQLite keeps schema state visible across async connections,
    # which avoids false negatives from isolated per-connection in-memory databases.
    db_dir = tmp_path_factory.mktemp("db")
    return f"sqlite+aiosqlite:///{Path(db_dir) / 'test_call_calendar.db'}"


@pytest_asyncio.fixture(scope="session")
async def test_engine(test_db_url: str) -> AsyncGenerator[AsyncEngine, None]:
    # Why: explicit async fixture semantics guarantee create_all runs before tests,
    # preventing race conditions where repository queries hit missing tables.
    engine = create_async_engine(test_db_url, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False, autoflush=False)
    async with session_factory() as session:
        # Why: cleaning mutable rows between tests keeps conflict/pagination checks
        # deterministic and eliminates hidden coupling through persistent state.
        await session.execute(MeetingSettings.__table__.delete())
        await session.execute(Booking.__table__.delete())
        await session.execute(Colleague.__table__.delete())
        session.add(
            Colleague(
                id=1,
                name="Kirill Mokevnin",
                default_meeting_provider=MeetingProvider.GOOGLE_MEET,
                timezone=MeetingTimezone.ASIA_YEKATERINBURG,
                meeting_duration_minutes=MeetingDurationMinutes.THIRTY,
            )
        )
        await session.commit()
        yield session
