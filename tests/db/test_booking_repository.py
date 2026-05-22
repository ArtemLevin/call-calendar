"""Unit tests for BookingRepository with SQLAlchemy session."""

from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.repositories.booking_repository import BookingRepository
from app.db.session import Base
from app.schemas.booking import BookingCreate

# Test database URL - in-memory SQLite for isolation
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_database() -> None:
    """Create tables before test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Provide a test database session."""
    async with TestSessionLocal() as session:
        yield session


@pytest.mark.asyncio
async def test_repository_create_and_get(db_session: AsyncSession) -> None:
    repo = BookingRepository(db_session)
    data = BookingCreate(
        slot_start=datetime(2026, 1, 1, 9, 0),
        customer_name="Repo User",
        customer_email="repo@example.com",
    )

    created = await repo.create(data)
    fetched = await repo.get_by_id(created.id)

    assert fetched is not None
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_repository_slot_availability_changes_after_create(db_session: AsyncSession) -> None:
    repo = BookingRepository(db_session)
    slot = datetime(2026, 1, 1, 9, 30)
    data = BookingCreate(
        slot_start=slot,
        customer_name="Repo User",
        customer_email="repo@example.com",
    )

    assert await repo.is_slot_available(str(slot))
    await repo.create(data)
    assert not await repo.is_slot_available(str(slot))
