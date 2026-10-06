import time

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

CANONICAL_STAGE_ORDER = ["queued", "validating", "running", "finalizing", "succeeded", "failed"]


def _poll_until_terminal(client, run_id: str, timeout_seconds: float = 3.0) -> list[str]:
    observed: list[str] = []
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        response = client.get(f"/runs/{run_id}/status")
        assert response.status_code == 200
        body = response.json()
        stage = body["stage"]
        if not observed or observed[-1] != stage:
            observed.append(stage)
        if stage in ("succeeded", "failed"):
            return observed, body
        time.sleep(0.005)
    raise AssertionError(f"run did not reach a terminal stage within {timeout_seconds}s: {observed}")


def _assert_in_canonical_order(observed: list[str]) -> None:
    indices = [CANONICAL_STAGE_ORDER.index(stage) for stage in observed]
    assert indices == sorted(indices), f"stages observed out of order: {observed}"


def test_full_loop_for_a_valid_script_reaches_succeeded(authenticated_client):
    upload_response = authenticated_client.post("/uploads", json={"project": "e2e-valid"})
    assert upload_response.status_code == 200

    # Simulates the browser's direct PUT to Seaweedfs, which this fake client
    # never performs over real HTTP (see FakeSeaweedfsClient docstring).
    get_seaweedfs_client().upload("alice", "e2e-valid", VALID_SCRIPT)

    run_response = authenticated_client.post(
        "/runs",
        json={"project": "e2e-valid", "preset_prompt": "Explain this pipeline"},
    )
    assert run_response.status_code == 202
    run_id = run_response.json()["run_id"]

    observed, final_body = _poll_until_terminal(authenticated_client, run_id)

    _assert_in_canonical_order(observed)
    assert observed[-1] == "succeeded"
    assert final_body["result"] is not None
    assert final_body["error"] is None


def test_full_loop_for_an_invalid_script_reaches_failed(authenticated_client):
    upload_response = authenticated_client.post("/uploads", json={"project": "e2e-invalid"})
    assert upload_response.status_code == 200

    get_seaweedfs_client().upload("alice", "e2e-invalid", INVALID_SCRIPT)

    run_response = authenticated_client.post(
        "/runs",
        json={"project": "e2e-invalid", "preset_prompt": "Explain this pipeline"},
    )
    assert run_response.status_code == 202
    run_id = run_response.json()["run_id"]

    observed, final_body = _poll_until_terminal(authenticated_client, run_id)

    _assert_in_canonical_order(observed)
    assert observed[-1] == "failed"
    assert "running" not in observed
    assert "finalizing" not in observed
    assert final_body["error"] is not None
    assert final_body["result"] is None
