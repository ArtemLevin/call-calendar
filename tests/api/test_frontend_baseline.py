from fastapi.testclient import TestClient

from app.main import app


def test_root_serves_frontend_entrypoint() -> None:
    client = TestClient(app)

    response = client.get('/')

    assert response.status_code == 200
    assert 'text/html' in response.headers['content-type']
    assert 'Call Calendar' in response.text
    assert 'id="booking-form"' in response.text
    assert 'id="page-size"' in response.text


def test_web_assets_are_served() -> None:
    client = TestClient(app)

    response = client.get('/web/app.js')

    assert response.status_code == 200
    assert 'javascript' in response.headers['content-type']
