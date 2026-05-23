from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Booking
from app.db.session import Base


@pytest.fixture(scope="session")
def test_db_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    # Why: file-backed SQLite keeps the same schema visible across connections,
    # which avoids flaky behavior that in-memory SQLite shows with pooled async sessions.
    db_dir = tmp_path_factory.mktemp("db")
    return f"sqlite+aiosqlite:///{Path(db_dir) / 'test_call_calendar.db'}"


@pytest.fixture(scope="session")
async def test_engine(test_db_url: str):
    # Why: dedicated test engine isolates persistence side effects from developer
    # machines and CI shared state, so repository tests stay deterministic.
    engine = create_async_engine(test_db_url, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False, autoflush=False)
    async with session_factory() as session:
        # Why: truncating mutable tables before each test prevents cross-test data
        # coupling, which is essential for trustworthy conflict/pagination assertions.
        await session.execute(Booking.__table__.delete())
        await session.commit()
        yield session
