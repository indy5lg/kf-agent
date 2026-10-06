from fastapi import APIRouter, Depends
from indy_db import User
from indy_kf_utils import get_seaweedfs_client

from api.dependencies import get_current_user
from api.schemas import UploadRequest, UploadResponse

router = APIRouter()


@router.post("/uploads", response_model=UploadResponse)
def request_upload_url(
    body: UploadRequest, current_user: User = Depends(get_current_user)
) -> UploadResponse:
    username = current_user.email.split("@")[0]
    upload_url = get_seaweedfs_client().build_upload_url(username, body.project)
    return UploadResponse(upload_url=upload_url)
