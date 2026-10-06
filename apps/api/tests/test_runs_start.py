from indy_kf_utils import get_seaweedfs_client

VALID_SCRIPT = b"""
from kfp import dsl

@dsl.component
def say_hi() -> str:
    return "hi"

@dsl.pipeline
def my_pipeline():
    say_hi()
"""


def _seed_upload(username: str, project: str, script_bytes: bytes = VALID_SCRIPT) -> None:
    get_seaweedfs_client().upload(username, project, script_bytes)


def test_returns_run_id_immediately_for_completed_upload(authenticated_client):
    _seed_upload("alice", "proj1")

    response = authenticated_client.post(
        "/runs",
        json={"project": "proj1", "preset_prompt": "Explain this pipeline"},
    )

    assert response.status_code == 202
    assert "run_id" in response.json()


def test_rejects_run_start_with_no_matching_upload(authenticated_client):
    response = authenticated_client.post(
        "/runs",
        json={"project": "proj-no-upload", "preset_prompt": "Explain this pipeline"},
    )

    assert response.status_code >= 400
    assert "run_id" not in response.json()


def test_rejects_prompt_outside_fixed_set(authenticated_client):
    _seed_upload("alice", "proj2")

    response = authenticated_client.post(
        "/runs",
        json={"project": "proj2", "preset_prompt": "do whatever you want"},
    )

    assert response.status_code == 422


def test_rejects_without_a_session(client):
    _seed_upload("alice", "proj3")

    response = client.post(
        "/runs",
        json={"project": "proj3", "preset_prompt": "Explain this pipeline"},
    )

    assert response.status_code == 401
