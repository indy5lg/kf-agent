import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from indy_agent import InvalidScript, compile_script
from indy_kf_utils import Stage, get_kubeflow_client, get_seaweedfs_client

POLL_INTERVAL_SECONDS = 0.02


@dataclass
class RunState:
    stage: str = "queued"
    result: Any | None = None
    error: str | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)

    def set(self, stage: str, *, result: Any | None = None, error: str | None = None) -> None:
        with self.lock:
            self.stage = stage
            self.result = result
            self.error = error

    def snapshot(self) -> tuple[str, Any | None, str | None]:
        with self.lock:
            return self.stage, self.result, self.error


class RunStore:
    def __init__(self) -> None:
        self._runs: dict[uuid.UUID, RunState] = {}
        self._lock = threading.Lock()

    def create(self) -> tuple[uuid.UUID, RunState]:
        run_id = uuid.uuid4()
        state = RunState()
        with self._lock:
            self._runs[run_id] = state
        return run_id, state

    def get(self, run_id: uuid.UUID) -> RunState | None:
        with self._lock:
            return self._runs.get(run_id)

    def clear(self) -> None:
        with self._lock:
            self._runs.clear()


run_store = RunStore()


def start_run(username: str, project: str, preset_prompt: str) -> uuid.UUID:
    script_bytes = get_seaweedfs_client().fetch_script(username, project)

    run_id, state = run_store.create()
    thread = threading.Thread(
        target=_process_run, args=(state, script_bytes, preset_prompt), daemon=True
    )
    thread.start()
    return run_id


def _process_run(state: RunState, script_bytes: bytes, preset_prompt: str) -> None:
    state.set("validating")
    try:
        pipeline_inputs = compile_script(script_bytes, preset_prompt)
    except InvalidScript as exc:
        state.set("failed", error=str(exc))
        return

    kf_client = get_kubeflow_client()
    run_id = kf_client.submit(
        {"pipeline_func": pipeline_inputs.pipeline_func, "preset_prompt": preset_prompt}
    )
    state.set("running")

    while True:
        report = kf_client.get_stage(run_id)
        if report.name == Stage.RUNNING:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        if report.name == Stage.SUCCEEDED:
            state.set("finalizing")
            time.sleep(POLL_INTERVAL_SECONDS)
            state.set("succeeded", result=report.result)
        else:
            state.set("failed", error=report.error)
        return
