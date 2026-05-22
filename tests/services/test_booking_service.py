"""Unit tests for BookingService with SQLAlchemy session."""

from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import Base
from app.exceptions import BookingNotFoundError, SlotNotAvailableError
from app.schemas.booking import BookingCreate
from app.services.booking_service import BookingService

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
async def test_create_booking_success(db_session: AsyncSession) -> None:
    service = BookingService(db_session)
    payload = BookingCreate(
        slot_start=datetime(2026, 1, 1, 10, 0),
        customer_name="Alice",
        customer_email="alice@example.com",
    )

    booking = await service.create_booking(payload)

    assert booking.id >= 1
    assert booking.customer_name == "Alice"


@pytest.mark.asyncio
async def test_create_booking_conflict(db_session: AsyncSession) -> None:
    service = BookingService(db_session)
    payload = BookingCreate(
        slot_start=datetime(2026, 1, 1, 10, 0),
        customer_name="Alice",
        customer_email="alice@example.com",
    )

    await service.create_booking(payload)

    with pytest.raises(SlotNotAvailableError):
        await service.create_booking(payload)


@pytest.mark.asyncio
async def test_get_booking_not_found(db_session: AsyncSession) -> None:
    service = BookingService(db_session)

    with pytest.raises(BookingNotFoundError):
        await service.get_by_id(999)
