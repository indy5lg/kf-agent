def test_returns_upload_url(authenticated_client):
    response = authenticated_client.post("/uploads", json={"project": "proj1"})

    assert response.status_code == 200
    assert "upload_url" in response.json()


def test_same_project_returns_same_url(authenticated_client):
    first = authenticated_client.post("/uploads", json={"project": "proj1"})
    second = authenticated_client.post("/uploads", json={"project": "proj1"})

    assert first.json()["upload_url"] == second.json()["upload_url"]


def test_rejects_without_a_session(client):
    response = client.post("/uploads", json={"project": "proj1"})

    assert response.status_code == 401


def test_upload_url_uses_derived_username(authenticated_client):
    response = authenticated_client.post("/uploads", json={"project": "proj1"})

    assert response.status_code == 200
    assert "alice" in response.json()["upload_url"]


def test_does_not_accept_a_username_field(authenticated_client):
    response = authenticated_client.post(
        "/uploads", json={"project": "proj1", "username": "someone-else"}
    )

    assert response.status_code == 200
    assert "someone-else" not in response.json()["upload_url"]
    assert "alice" in response.json()["upload_url"]
