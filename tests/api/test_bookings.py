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
        # Why: API tests must use the same isolated test session as repository/service tests
        # so endpoint behavior stays deterministic and independent of local runtime DB state.
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_create_booking_success(client: TestClient) -> None:
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
    assert set(body.keys()) == {
        "id",
        "slot_start",
        "customer_name",
        "customer_email",
        "status",
    }
    assert "created_at" not in body


def test_create_booking_conflict(client: TestClient) -> None:
    payload = {
        "slot_start": datetime(2026, 1, 1, 11, 0).isoformat(),
        "customer_name": "Bob",
        "customer_email": "bob@example.com",
    }
    first = client.post("/api/bookings/", json=payload)
    second = client.post("/api/bookings/", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert isinstance(second.json()["detail"], str)


def test_get_booking_not_found(client: TestClient) -> None:
    response = client.get("/api/bookings/999999")
    assert response.status_code == 404
    assert isinstance(response.json()["detail"], str)


def test_list_upcoming_returns_sorted_results(client: TestClient) -> None:
    client.post(
        "/api/bookings/",
        json={
            "slot_start": datetime(2026, 1, 2, 12, 0).isoformat(),
            "customer_name": "Later",
            "customer_email": "later@example.com",
        },
    )
    client.post(
        "/api/bookings/",
        json={
            "slot_start": datetime(2026, 1, 2, 9, 0).isoformat(),
            "customer_name": "Earlier",
            "customer_email": "earlier@example.com",
        },
    )

    response = client.get(
        "/api/bookings/upcoming",
        params={"from_ts": datetime(2026, 1, 2, 8, 0).isoformat(), "limit": 10, "offset": 0},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 2
    assert body[0]["customer_name"] == "Earlier"


def test_list_upcoming_rejects_invalid_limit(client: TestClient) -> None:
    response = client.get(
        "/api/bookings/upcoming",
        params={"from_ts": datetime(2026, 1, 2, 8, 0).isoformat(), "limit": 0, "offset": 0},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert len(detail) >= 1
    first_error = detail[0]
    assert first_error["loc"][-1] == "limit"
    assert first_error["type"] == "greater_than_equal"


def test_create_booking_accepts_timezone_aware_slot_start(client: TestClient) -> None:
    response = client.post(
        "/api/bookings/",
        json={
            "slot_start": "2026-01-01T10:00:00+00:00",
            "customer_name": "Aware",
            "customer_email": "aware@example.com",
        },
    )

    assert response.status_code == 201


def test_create_booking_rejects_non_30_minute_slot(client: TestClient) -> None:
    response = client.post(
        "/api/bookings/",
        json={
            "slot_start": datetime(2026, 1, 1, 10, 15).isoformat(),
            "customer_name": "Invalid Slot",
            "customer_email": "invalid-slot@example.com",
        },
    )

    assert response.status_code == 422
    assert "30-minute" in response.json()["detail"]


def test_upcoming_contains_booked_slots_not_free_slots(client: TestClient) -> None:
    payload = {
        "slot_start": datetime(2026, 1, 3, 10, 0).isoformat(),
        "customer_name": "Booked",
        "customer_email": "booked@example.com",
    }
    created = client.post("/api/bookings/", json=payload)
    assert created.status_code == 201

    upcoming = client.get(
        "/api/bookings/upcoming",
        params={"from_ts": datetime(2026, 1, 3, 0, 0).isoformat(), "limit": 10, "offset": 0},
    )
    assert upcoming.status_code == 200
    first_slot = upcoming.json()[0]["slot_start"]

    conflict = client.post(
        "/api/bookings/",
        json={
            "slot_start": first_slot,
            "customer_name": "Duplicate",
            "customer_email": "duplicate@example.com",
        },
    )
    assert conflict.status_code == 409


def test_update_booking_status_success(client: TestClient) -> None:
    created = client.post(
        "/api/bookings/",
        json={
            "slot_start": datetime(2026, 1, 4, 10, 0).isoformat(),
            "customer_name": "Status Owner",
            "customer_email": "status-owner@example.com",
        },
    )
    assert created.status_code == 201
    booking_id = created.json()["id"]

    updated = client.patch(
        f"/api/bookings/{booking_id}/status",
        json={"status": "confirmed"},
    )

    assert updated.status_code == 200
    assert updated.json()["status"] == "confirmed"


def test_update_booking_status_rejects_invalid_transition(client: TestClient) -> None:
    created = client.post(
        "/api/bookings/",
        json={
            "slot_start": datetime(2026, 1, 4, 10, 30).isoformat(),
            "customer_name": "Status Owner",
            "customer_email": "status-owner-2@example.com",
        },
    )
    booking_id = created.json()["id"]
    confirmed = client.patch(f"/api/bookings/{booking_id}/status", json={"status": "confirmed"})
    assert confirmed.status_code == 200
    completed = client.patch(f"/api/bookings/{booking_id}/status", json={"status": "completed"})
    assert completed.status_code == 200

    invalid = client.patch(f"/api/bookings/{booking_id}/status", json={"status": "pending"})
    assert invalid.status_code == 409
    assert "Cannot transition" in invalid.json()["detail"]


def test_update_booking_status_is_idempotent_for_same_status(client: TestClient) -> None:
    created = client.post(
        "/api/bookings/",
        json={
            "slot_start": datetime(2026, 1, 4, 11, 0).isoformat(),
            "customer_name": "Idempotent Owner",
            "customer_email": "idempotent-owner@example.com",
        },
    )
    assert created.status_code == 201
    booking_id = created.json()["id"]

    unchanged = client.patch(f"/api/bookings/{booking_id}/status", json={"status": "pending"})

    assert unchanged.status_code == 200
    body = unchanged.json()
    assert body["id"] == booking_id
    assert body["status"] == "pending"


def test_update_booking_status_returns_404_for_missing_booking(client: TestClient) -> None:
    response = client.patch("/api/bookings/999999/status", json={"status": "confirmed"})

    assert response.status_code == 404
    assert isinstance(response.json()["detail"], str)


def test_update_booking_status_rejects_invalid_status_payload(client: TestClient) -> None:
    created = client.post(
        "/api/bookings/",
        json={
            "slot_start": datetime(2026, 1, 4, 11, 30).isoformat(),
            "customer_name": "Invalid Enum Owner",
            "customer_email": "invalid-enum-owner@example.com",
        },
    )
    assert created.status_code == 201
    booking_id = created.json()["id"]

    response = client.patch(f"/api/bookings/{booking_id}/status", json={"status": "archived"})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert len(detail) >= 1
