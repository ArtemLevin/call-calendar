from collections.abc import AsyncGenerator

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


def test_get_meeting_metadata_options_returns_expected_enums(client: TestClient) -> None:
    response = client.get("/api/meeting-metadata/options")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "meeting_provider_options": ["google_meet", "zoom", "phone"],
        "meeting_timezone_options": [
            "Asia/Yekaterinburg",
            "UTC",
            "Europe/Berlin",
            "America/New_York",
        ],
        "meeting_duration_minutes_options": [30],
    }


def test_get_meeting_settings_returns_defaults(client: TestClient) -> None:
    response = client.get("/api/meeting-settings")
    assert response.status_code == 200
    assert response.json() == {
        "meeting_provider": "google_meet",
        "meeting_timezone": "Asia/Yekaterinburg",
        "meeting_duration_minutes": 30,
    }


def test_patch_meeting_settings_updates_values(client: TestClient) -> None:
    patched = client.patch(
        "/api/meeting-settings",
        json={
            "meeting_provider": "zoom",
            "meeting_timezone": "UTC",
            "meeting_duration_minutes": 30,
        },
    )
    assert patched.status_code == 200
    assert patched.json() == {
        "meeting_provider": "zoom",
        "meeting_timezone": "UTC",
        "meeting_duration_minutes": 30,
    }

    fetched = client.get("/api/meeting-settings")
    assert fetched.status_code == 200
    assert fetched.json() == patched.json()


def test_patch_meeting_settings_rejects_invalid_timezone_422(client: TestClient) -> None:
    response = client.patch(
        "/api/meeting-settings",
        json={
            "meeting_provider": "zoom",
            "meeting_timezone": "Mars/Olympus",
            "meeting_duration_minutes": 30,
        },
    )
    assert response.status_code == 422
