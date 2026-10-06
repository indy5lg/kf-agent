import pytest

from indy_kf_utils.seaweedfs import FakeSeaweedfsClient, ScriptNotUploaded


def test_build_upload_url_scoped_to_username_and_project():
    client = FakeSeaweedfsClient()

    url = client.build_upload_url("alice", "proj1")

    assert "alice" in url
    assert "proj1" in url


def test_build_upload_url_stable_across_repeated_calls():
    client = FakeSeaweedfsClient()

    first = client.build_upload_url("alice", "proj1")
    second = client.build_upload_url("alice", "proj1")

    assert first == second


def test_fetch_script_raises_when_nothing_uploaded():
    client = FakeSeaweedfsClient()

    with pytest.raises(ScriptNotUploaded):
        client.fetch_script("alice", "proj1")


def test_fetch_script_returns_uploaded_bytes():
    client = FakeSeaweedfsClient()
    script_bytes = b"print('hello')"
    client.upload("alice", "proj1", script_bytes)

    fetched = client.fetch_script("alice", "proj1")

    assert fetched == script_bytes
