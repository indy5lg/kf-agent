import pytest
from indy_kf_utils import get_seaweedfs_client


def test_returns_upload_url_pointing_at_api(authenticated_client):
    response = authenticated_client.post("/uploads", json={"project": "proj1"})

    assert response.status_code == 200
    assert response.json()["upload_url"] == "http://localhost:8000/uploads/proj1"


def test_same_project_returns_same_url(authenticated_client):
    first = authenticated_client.post("/uploads", json={"project": "proj1"})
    second = authenticated_client.post("/uploads", json={"project": "proj1"})

    assert first.json()["upload_url"] == second.json()["upload_url"]


def test_rejects_without_a_session(client):
    assert client.post("/uploads", json={"project": "proj1"}).status_code == 401


@pytest.mark.parametrize("bad", ["../etc", "a/b", "", ".hidden", "x" * 65])
def test_rejects_unsafe_project_names(authenticated_client, bad):
    response = authenticated_client.post("/uploads", json={"project": bad})

    assert response.status_code == 422


def test_put_stores_file_under_the_session_user(authenticated_client):
    response = authenticated_client.put("/uploads/proj1", content=b"print('hi')")

    assert response.status_code == 200
    assert get_seaweedfs_client().fetch_script("alice", "proj1") == b"print('hi')"


def test_put_ignores_a_username_in_the_path_or_body(authenticated_client):
    authenticated_client.put("/uploads/proj1", content=b"mine")

    assert get_seaweedfs_client().fetch_script("alice", "proj1") == b"mine"


def test_put_requires_a_session(client):
    assert client.put("/uploads/proj1", content=b"x").status_code == 401


def test_put_rejects_empty_body(authenticated_client):
    assert authenticated_client.put("/uploads/proj1", content=b"").status_code == 400


def test_put_rejects_oversized_body(authenticated_client):
    response = authenticated_client.put(
        "/uploads/proj1", content=b"x" * (5 * 1024 * 1024 + 1)
    )

    assert response.status_code == 413


def test_put_rejects_unsafe_project_name(authenticated_client):
    assert authenticated_client.put("/uploads/bad.name", content=b"x").status_code == 422


def test_fake_storage_endpoint_is_gone(client):
    assert client.put("/fake-storage/alice/proj1", content=b"x").status_code == 404


def test_storage_failure_is_not_swallowed(authenticated_client, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("seaweedfs down")

    monkeypatch.setattr(get_seaweedfs_client(), "upload", boom)

    with pytest.raises(RuntimeError, match="seaweedfs down"):
        authenticated_client.put("/uploads/proj1", content=b"x")


def test_runs_rejects_unsafe_project_name(authenticated_client):
    response = authenticated_client.post(
        "/runs", json={"project": "../x", "preset_prompt": "Explain this pipeline"}
    )

    assert response.status_code == 422
