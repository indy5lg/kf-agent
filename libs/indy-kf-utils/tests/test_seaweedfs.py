import boto3
import pytest
from moto import mock_aws

from indy_kf_utils.seaweedfs import (
    FakeSeaweedfsClient,
    S3SeaweedfsClient,
    ScriptNotUploaded,
    object_key,
)

BUCKET = "kubie-bridge-storage"


def test_fake_fetch_script_raises_when_nothing_uploaded():
    with pytest.raises(ScriptNotUploaded):
        FakeSeaweedfsClient().fetch_script("alice", "proj1")


def test_fake_fetch_script_returns_uploaded_bytes():
    client = FakeSeaweedfsClient()
    client.upload("alice", "proj1", b"print('hello')")

    assert client.fetch_script("alice", "proj1") == b"print('hello')"


def test_object_key_is_scoped_to_user_and_project():
    assert object_key("alice", "proj1") == "alice/proj1/script.py"


@pytest.fixture
def s3():
    with mock_aws():
        yield boto3.client("s3", region_name="us-east-1")


def _client(s3):
    return S3SeaweedfsClient("http://unused", "key", "secret", BUCKET, s3=s3)


def test_s3_upload_creates_missing_bucket_and_stores_under_user_project_key(s3):
    _client(s3).upload("alice", "proj1", b"print('hi')")

    obj = s3.get_object(Bucket=BUCKET, Key="alice/proj1/script.py")
    assert obj["Body"].read() == b"print('hi')"


def test_s3_upload_into_existing_bucket(s3):
    s3.create_bucket(Bucket=BUCKET)

    _client(s3).upload("alice", "proj1", b"x")

    assert s3.get_object(Bucket=BUCKET, Key="alice/proj1/script.py")["Body"].read() == b"x"


def test_s3_reupload_replaces_previous_script(s3):
    client = _client(s3)
    client.upload("alice", "proj1", b"v1")
    client.upload("alice", "proj1", b"v2")

    assert client.fetch_script("alice", "proj1") == b"v2"


def test_s3_fetch_missing_key_raises_script_not_uploaded(s3):
    s3.create_bucket(Bucket=BUCKET)

    with pytest.raises(ScriptNotUploaded):
        _client(s3).fetch_script("alice", "nope")


def test_s3_fetch_missing_bucket_raises_script_not_uploaded(s3):
    with pytest.raises(ScriptNotUploaded):
        _client(s3).fetch_script("alice", "proj1")


def test_s3_users_are_isolated(s3):
    client = _client(s3)
    client.upload("alice", "proj1", b"alice's")

    with pytest.raises(ScriptNotUploaded):
        client.fetch_script("bob", "proj1")
