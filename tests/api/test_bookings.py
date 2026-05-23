from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app


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


def test_list_upcoming_returns_sorted_results() -> None:
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


def test_list_upcoming_rejects_invalid_limit() -> None:
    response = client.get(
        "/api/bookings/upcoming",
        params={"from_ts": datetime(2026, 1, 2, 8, 0).isoformat(), "limit": 0, "offset": 0},
    )

    assert response.status_code == 422
