import os
from functools import lru_cache
from typing import Protocol


class ScriptNotUploaded(Exception):
    pass


class SeaweedfsClient(Protocol):
    def build_upload_url(self, username: str, project: str) -> str: ...
    def fetch_script(self, username: str, project: str) -> bytes: ...


class FakeSeaweedfsClient:
    """In-memory test double. `upload()` is a test seam only — production
    code never calls it, since the real upload happens via a direct browser
    PUT to the URL `build_upload_url()` returns, bypassing this client."""

    def __init__(self) -> None:
        self._storage: dict[tuple[str, str], bytes] = {}

    def build_upload_url(self, username: str, project: str) -> str:
        base_url = os.environ.get("FAKE_SEAWEEDFS_UPLOAD_BASE_URL", "http://localhost:8000")
        return f"{base_url.rstrip('/')}/fake-storage/{username}/{project}"

    def upload(self, username: str, project: str, data: bytes) -> None:
        self._storage[(username, project)] = data

    def fetch_script(self, username: str, project: str) -> bytes:
        try:
            return self._storage[(username, project)]
        except KeyError:
            raise ScriptNotUploaded(f"{username}/{project}") from None


class RealSeaweedfsClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def build_upload_url(self, username: str, project: str) -> str:
        return f"{self._base_url}/{username}/{project}/script.py"

    def fetch_script(self, username: str, project: str) -> bytes:
        import httpx

        url = self.build_upload_url(username, project)
        response = httpx.get(url)
        if response.status_code == 404:
            raise ScriptNotUploaded(f"{username}/{project}")
        response.raise_for_status()
        return response.content


@lru_cache
def get_seaweedfs_client() -> SeaweedfsClient:
    mode = os.environ.get("SEAWEEDFS_CLIENT", "fake")
    if mode == "fake":
        return FakeSeaweedfsClient()
    if mode == "real":
        return RealSeaweedfsClient(os.environ["SEAWEEDFS_BASE_URL"])
    raise ValueError(f"Unknown SEAWEEDFS_CLIENT: {mode!r}")
