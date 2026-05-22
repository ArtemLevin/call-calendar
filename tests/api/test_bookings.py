"""Integration tests for booking API with SQLite database.

Tests use a test-specific database that is created and dropped for each test.
"""

from datetime import datetime

import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import Base, get_db_session
from app.main import app

# Test database URL - in-memory SQLite for isolation
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def override_get_db_session() -> AsyncSession:
    """Override dependency to use test database session."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_database() -> None:
    """Create tables before test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    yield
    
    # Cleanup
    app.dependency_overrides.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


client = TestClient(app)


def test_create_booking_success() -> None:
    response = client.post(
        "/api/bookings/",
        json={
            "slot_start": datetime(2026, 1, 1, 10, 0).isoformat(),
            "customer_name": "Alice",
            "customer_email": "alice@example.com",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] >= 1
    assert body["status"] == "pending"


def test_create_booking_conflict() -> None:
    payload = {
        "slot_start": datetime(2026, 1, 1, 11, 0).isoformat(),
        "customer_name": "Bob",
        "customer_email": "bob@example.com",
    }
    first = client.post("/api/bookings/", json=payload)
    second = client.post("/api/bookings/", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_get_booking_not_found() -> None:
    response = client.get("/api/bookings/999999")
    assert response.status_code == 404
