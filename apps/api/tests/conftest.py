import os

os.environ.setdefault("SEAWEEDFS_CLIENT", "fake")
os.environ.setdefault("KUBEFLOW_CLIENT", "fake")
# indy_db.config reads DATABASE_URL eagerly at import time, even though these
# tests never touch the DB (only construct a plain in-memory User object).
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://unused:unused@localhost/unused")

import pytest
from fastapi.testclient import TestClient
from indy_db import User
from indy_kf_utils import get_kubeflow_client, get_seaweedfs_client

from api.dependencies import get_current_user
from api.main import app
from api.runs import run_store

FAKE_USER_EMAIL = "alice@example.com"


@pytest.fixture
def client():
    # Plain TestClient (no `with` block) intentionally skips app lifespan,
    # so startup never tries to reach Postgres - these routes don't use the DB.
    get_seaweedfs_client.cache_clear()
    get_kubeflow_client.cache_clear()
    run_store.clear()
    app.dependency_overrides.pop(get_current_user, None)
    return TestClient(app)


@pytest.fixture
def authenticated_client(client):
    # Overrides get_current_user with a plain in-memory User rather than
    # registering/logging in through indy_db - these routes' tests stay
    # independent of a live Postgres, same as the unauthenticated client.
    app.dependency_overrides[get_current_user] = lambda: User(
        email=FAKE_USER_EMAIL, password="unused"
    )
    yield client
    app.dependency_overrides.pop(get_current_user, None)
