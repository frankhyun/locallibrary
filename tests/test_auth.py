from ninja.testing import TestClient

from accounts.tokens import create_token
from taskflow.api import api


client = TestClient(api)


def test_obtain_token(alice):
    response = client.post("/auth/token", json={"username": "alice", "password": "wonderland-42"})
    assert response.status_code == 200
    assert set(response.json()) == {"access", "refresh"}


def test_wrong_password(alice):
    assert client.post("/auth/token", json={"username": "alice", "password": "nope"}).status_code == 401


def test_missing_token():
    assert client.get("/projects/").status_code == 401


def test_expired_token(alice):
    token = create_token(alice.id, "access", lifetime=-1)
    assert client.get("/projects/", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_refresh_token_is_not_an_access_token(alice):
    refresh = client.post(
        "/auth/token", json={"username": "alice", "password": "wonderland-42"}
    ).json()["refresh"]
    assert client.get("/projects/", headers={"Authorization": f"Bearer {refresh}"}).status_code == 401
