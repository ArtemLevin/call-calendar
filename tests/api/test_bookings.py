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
