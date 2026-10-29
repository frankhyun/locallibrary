import pytest
from django.contrib.auth.models import User
from ninja.testing import TestClient

from accounts.tokens import create_token_pair
from projects.models import Membership, Project
from taskflow.api import api


@pytest.fixture(autouse=True)
def fast_test_settings(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def alice(db):
    return User.objects.create_user("alice", password="wonderland-42")


@pytest.fixture
def bob(db):
    return User.objects.create_user("bob", password="wonderland-42")


@pytest.fixture
def carol(db):
    return User.objects.create_user("carol", password="wonderland-42")


@pytest.fixture
def project(alice, bob):
    project = Project.objects.create(name="Website redesign", description="New site")
    project.memberships.create(user=alice, role=Membership.Role.OWNER)
    project.memberships.create(user=bob, role=Membership.Role.MEMBER)
    return project


@pytest.fixture
def client_for():
    def make_client(user):
        token = create_token_pair(user.id)["access"]
        return TestClient(api, headers={"Authorization": f"Bearer {token}"})

    return make_client
