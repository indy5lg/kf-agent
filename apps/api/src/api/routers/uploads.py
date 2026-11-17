import os

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from indy_db import User
from indy_kf_utils import get_seaweedfs_client

from api.dependencies import get_current_user
from api.schemas import PROJECT_NAME_PATTERN, UploadRequest, UploadResponse, storage_username

router = APIRouter()

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def _public_api_base_url() -> str:
    return os.environ.get("API_PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")


@router.post("/uploads", response_model=UploadResponse)
def request_upload_url(
    body: UploadRequest, current_user: User = Depends(get_current_user)
) -> UploadResponse:
    # The browser PUTs the file back to this API (cookie-authenticated), and the
    # API writes it to SeaweedFS. SeaweedFS credentials never reach the browser.
    return UploadResponse(upload_url=f"{_public_api_base_url()}/uploads/{body.project}")


@router.put("/uploads/{project}")
async def upload_script(
    request: Request,
    project: str = Path(pattern=PROJECT_NAME_PATTERN),
    current_user: User = Depends(get_current_user),
) -> dict[str, bool]:
    data = await request.body()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Uploaded file is too large")
    get_seaweedfs_client().upload(storage_username(current_user), project, data)
    return {"ok": True}
