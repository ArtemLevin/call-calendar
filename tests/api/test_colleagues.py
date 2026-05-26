from collections.abc import AsyncGenerator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.main import app


@pytest.fixture
def client(db_session: AsyncSession) -> TestClient:
    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_list_colleagues_returns_default_seed(client: TestClient) -> None:
    response = client.get("/api/colleagues/")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == 1
    assert payload[0]["name"] == "Kirill Mokevnin"
    assert payload[0]["default_meeting_provider"] == "google_meet"


def test_get_colleague_availability_contract(client: TestClient) -> None:
    response = client.get(
        "/api/colleagues/1/availability",
        params={
            "from_ts": datetime(2026, 1, 1, 0, 0).isoformat(),
            "to_ts": datetime(2026, 1, 2, 0, 0).isoformat(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["colleague_id"] == 1
    assert isinstance(payload["slots"], list)


def test_get_colleague_availability_rejects_invalid_range(client: TestClient) -> None:
    response = client.get(
        "/api/colleagues/1/availability",
        params={
            "from_ts": datetime(2026, 1, 2, 0, 0).isoformat(),
            "to_ts": datetime(2026, 1, 1, 0, 0).isoformat(),
        },
    )

    assert response.status_code == 422


def test_list_colleagues_supports_empty_page_with_offset(client: TestClient) -> None:
    response = client.get("/api/colleagues/", params={"limit": 50, "offset": 999})

    assert response.status_code == 200
    assert response.json() == []


def test_list_colleagues_rejects_invalid_limit(client: TestClient) -> None:
    response = client.get("/api/colleagues/", params={"limit": 0, "offset": 0})

    assert response.status_code == 422


def test_get_colleague_availability_returns_404_for_unknown_colleague(client: TestClient) -> None:
    response = client.get(
        "/api/colleagues/999/availability",
        params={
            "from_ts": datetime(2026, 1, 1, 0, 0).isoformat(),
            "to_ts": datetime(2026, 1, 2, 0, 0).isoformat(),
        },
    )

    assert response.status_code == 404


def test_get_colleague_availability_can_return_empty_slots(client: TestClient) -> None:
    response = client.get(
        "/api/colleagues/1/availability",
        params={
            "from_ts": datetime(2026, 1, 3, 0, 0).isoformat(),
            "to_ts": datetime(2026, 1, 4, 0, 0).isoformat(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["colleague_id"] == 1
    assert payload["slots"] == []
