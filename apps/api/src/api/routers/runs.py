import uuid

from fastapi import APIRouter, Depends, HTTPException
from indy_db import User
from indy_kf_utils import ScriptNotUploaded

from api.dependencies import get_current_user
from api.runs import run_store, start_run
from api.schemas import RunStatusResponse, StartRunRequest

router = APIRouter()


@router.post("/runs", status_code=202)
def create_run(
    body: StartRunRequest, current_user: User = Depends(get_current_user)
) -> dict[str, str]:
    username = current_user.email.split("@")[0]
    try:
        run_id = start_run(username, body.project, body.preset_prompt)
    except ScriptNotUploaded as exc:
        raise HTTPException(
            status_code=400, detail=f"no uploaded script found for {exc}"
        ) from exc
    return {"run_id": str(run_id)}


@router.get("/runs/{run_id}/status", response_model=RunStatusResponse)
def get_run_status(
    run_id: uuid.UUID, current_user: User = Depends(get_current_user)
) -> RunStatusResponse:
    state = run_store.get(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail="run not found")
    stage, result, error = state.snapshot()
    return RunStatusResponse(stage=stage, result=result, error=error)
