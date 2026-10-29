import pytest
from django.contrib.auth.models import User
from ninja.testing import TestClient

from taskflow.api import api


@pytest.fixture
def api_client():
    return TestClient(api)


@pytest.fixture
def user(db):
    return User.objects.create_user("pytest-user", password="StrongPass123!")


def test_auth_endpoint_issues_tokens(api_client, user):
    response = api_client.post(
        "/auth/token",
        json={"username": "pytest-user", "password": "StrongPass123!"},
    )
    assert response.status_code == 200
    assert set(response.json()) == {"access", "refresh"}


def test_projects_require_a_valid_access_token(api_client):
    assert api_client.get("/projects/").status_code == 401
