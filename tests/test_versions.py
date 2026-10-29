from ninja.testing import TestClient

from taskflow.api import api
from taskflow.api_v2 import api_v2


def test_v2_token_response(alice):
    response = TestClient(api_v2).post(
        "/auth/token", json={"username": "alice", "password": "wonderland-42"}
    )
    assert response.status_code == 200
    assert set(response.json()) == {
        "access_token", "refresh_token", "token_type", "expires_in"
    }


def test_v1_auth_is_deprecated():
    schema = TestClient(api).get("/openapi.json").json()
    assert schema["paths"]["/taskflow/api/auth/token"]["post"]["deprecated"] is True


def test_health_is_public_and_hidden():
    client = TestClient(api)
    assert client.get("/health").json() == {"status": "ok"}
    assert "/health" not in client.get("/openapi.json").json()["paths"]
