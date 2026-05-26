from fastapi.testclient import TestClient

from app.main import app


def test_root_serves_frontend_entrypoint() -> None:
    client = TestClient(app)

    response = client.get('/')

    assert response.status_code == 200
    assert 'text/html' in response.headers['content-type']
    assert 'Call Calendar' in response.text
    assert 'class="booking-card"' in response.text
    assert 'id="calendar-grid"' in response.text
    assert 'id="slot-list"' in response.text
    assert 'id="booking-form"' in response.text
    assert 'id="settings-button"' in response.text
    assert 'id="meeting-duration-select"' in response.text
    assert 'id="meeting-provider-select"' in response.text
    assert 'id="meeting-timezone-select"' in response.text
    assert 'Kirill Mokevnin' in response.text


def test_web_assets_are_served() -> None:
    client = TestClient(app)

    response = client.get('/web/app.js')

    assert response.status_code == 200
    assert 'javascript' in response.headers['content-type']
    assert "fetch(`${config.API_BASE_URL}/meeting-metadata/options`)" in response.text
    assert "fetch(`${config.API_BASE_URL}/meeting-settings`)" in response.text
    assert "meetingProviderSelect?.addEventListener('change'" in response.text
