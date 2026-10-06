import time
import uuid

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

INVALID_SCRIPT = b"not a valid pipeline script at all"


def _seed_upload(username: str, project: str, script_bytes: bytes) -> None:
    get_seaweedfs_client().upload(username, project, script_bytes)


def _start_run(client, project: str) -> str:
    response = client.post(
        "/runs",
        json={"project": project, "preset_prompt": "Explain this pipeline"},
    )
    assert response.status_code == 202
    return response.json()["run_id"]


def _poll_until_terminal(client, run_id: str, timeout_seconds: float = 3.0) -> list[str]:
    observed: list[str] = []
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        response = client.get(f"/runs/{run_id}/status")
        assert response.status_code == 200
        stage = response.json()["stage"]
        if not observed or observed[-1] != stage:
            observed.append(stage)
        if stage in ("succeeded", "failed"):
            return observed
        time.sleep(0.01)
    raise AssertionError(f"run did not reach a terminal stage within {timeout_seconds}s: {observed}")


def test_unknown_run_id_returns_404(authenticated_client):
    response = authenticated_client.get(f"/runs/{uuid.uuid4()}/status")

    assert response.status_code == 404


def test_rejects_without_a_session(client):
    response = client.get(f"/runs/{uuid.uuid4()}/status")

    assert response.status_code == 401


def test_valid_script_progresses_to_succeeded_with_result(authenticated_client):
    _seed_upload("alice", "proj1", VALID_SCRIPT)
    run_id = _start_run(authenticated_client, "proj1")

    observed = _poll_until_terminal(authenticated_client, run_id)

    canonical_order = ["queued", "validating", "running", "finalizing", "succeeded"]
    assert observed == [s for s in canonical_order if s in observed]
    assert observed[-1] == "succeeded"
    final = authenticated_client.get(f"/runs/{run_id}/status").json()
    assert final["result"] is not None


def test_invalid_script_reaches_failed_skipping_running_and_finalizing(authenticated_client):
    _seed_upload("alice", "proj2", INVALID_SCRIPT)
    run_id = _start_run(authenticated_client, "proj2")

    observed = _poll_until_terminal(authenticated_client, run_id)

    assert "running" not in observed
    assert "finalizing" not in observed
    assert observed[-1] == "failed"
    final = authenticated_client.get(f"/runs/{run_id}/status").json()
    assert final["error"] is not None
