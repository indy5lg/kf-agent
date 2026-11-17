import os
from functools import lru_cache
from typing import Protocol

SCRIPT_FILENAME = "script.py"

# S3 error codes that mean "the object (or its bucket) isn't there".
_MISSING_CODES = ("NoSuchKey", "NoSuchBucket", "404", "NotFound")


class ScriptNotUploaded(Exception):
    pass


class SeaweedfsClient(Protocol):
    def upload(self, username: str, project: str, data: bytes) -> None: ...
    def fetch_script(self, username: str, project: str) -> bytes: ...


def object_key(username: str, project: str) -> str:
    return f"{username}/{project}/{SCRIPT_FILENAME}"


class FakeSeaweedfsClient:
    """In-memory test double used when SEAWEEDFS_CLIENT=fake (the default)."""

    def __init__(self) -> None:
        self._storage: dict[tuple[str, str], bytes] = {}

    def upload(self, username: str, project: str, data: bytes) -> None:
        self._storage[(username, project)] = data

    def fetch_script(self, username: str, project: str) -> bytes:
        try:
            return self._storage[(username, project)]
        except KeyError:
            raise ScriptNotUploaded(f"{username}/{project}") from None


class S3SeaweedfsClient:
    """Talks to the SeaweedFS S3 gateway. Only the API server holds the
    credentials; browsers upload through the API, never to SeaweedFS directly."""

    def __init__(
        self, endpoint_url: str, access_key: str, secret_key: str, bucket: str, s3=None
    ) -> None:
        self._bucket = bucket
        if s3 is None:
            import boto3
            from botocore.client import Config

            s3 = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                # SeaweedFS has no real region; boto3 just needs one to sign with.
                region_name="us-east-1",
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path"},
                    connect_timeout=5,
                    read_timeout=30,
                ),
            )
        self._s3 = s3
        self._bucket_ready = False

    def _ensure_bucket(self) -> None:
        if self._bucket_ready:
            return
        from botocore.exceptions import ClientError

        try:
            self._s3.head_bucket(Bucket=self._bucket)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") not in _MISSING_CODES:
                raise
            self._s3.create_bucket(Bucket=self._bucket)
        self._bucket_ready = True

    def upload(self, username: str, project: str, data: bytes) -> None:
        self._ensure_bucket()
        self._s3.put_object(
            Bucket=self._bucket,
            Key=object_key(username, project),
            Body=data,
            ContentType="text/x-python",
        )

    def fetch_script(self, username: str, project: str) -> bytes:
        from botocore.exceptions import ClientError

        try:
            response = self._s3.get_object(
                Bucket=self._bucket, Key=object_key(username, project)
            )
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in _MISSING_CODES:
                raise ScriptNotUploaded(f"{username}/{project}") from exc
            raise
        return response["Body"].read()


@lru_cache
def get_seaweedfs_client() -> SeaweedfsClient:
    mode = os.environ.get("SEAWEEDFS_CLIENT", "fake")
    if mode == "fake":
        return FakeSeaweedfsClient()
    if mode == "s3":
        return S3SeaweedfsClient(
            endpoint_url=os.environ["SEAWEEDFS_S3_ENDPOINT"],
            access_key=os.environ["SEAWEEDFS_ACCESS_KEY"],
            secret_key=os.environ["SEAWEEDFS_SECRET_KEY"],
            bucket=os.environ["SEAWEEDFS_BUCKET"],
        )
    raise ValueError(f"Unknown SEAWEEDFS_CLIENT: {mode!r} (expected 'fake' or 's3')")
