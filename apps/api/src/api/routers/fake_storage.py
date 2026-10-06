from fastapi import APIRouter, Request
from indy_kf_utils import get_seaweedfs_client

router = APIRouter()


@router.put("/fake-storage/{username}/{project}")
async def store_fake_upload(username: str, project: str, request: Request) -> dict[str, bool]:
    body = await request.body()
    get_seaweedfs_client().upload(username, project, body)
    return {"ok": True}
