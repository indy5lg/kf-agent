import os
import uuid
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Any, Protocol


class Stage(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class StageReport:
    name: Stage
    result: Any | None = None
    error: str | None = None


class KubeflowClient(Protocol):
    def submit(self, pipeline_inputs: dict) -> uuid.UUID: ...
    def get_stage(self, run_id: uuid.UUID) -> StageReport: ...


@dataclass
class _RunRecord:
    calls: int = 0


class FakeKubeflowClient:
    """In-memory test double. `steps_to_terminal` controls how many
    `get_stage()` calls a run stays at `running` before reporting terminal,
    so tests can exercise both the in-progress and terminal paths."""

    def __init__(self, steps_to_terminal: int = 2, simulate_failure: bool = False) -> None:
        self._steps_to_terminal = steps_to_terminal
        self._simulate_failure = simulate_failure
        self._runs: dict[uuid.UUID, _RunRecord] = {}

    def submit(self, pipeline_inputs: dict) -> uuid.UUID:
        run_id = uuid.uuid4()
        self._runs[run_id] = _RunRecord()
        return run_id

    def get_stage(self, run_id: uuid.UUID) -> StageReport:
        record = self._runs[run_id]
        record.calls += 1
        if record.calls < self._steps_to_terminal:
            return StageReport(name=Stage.RUNNING)
        if self._simulate_failure:
            return StageReport(name=Stage.FAILED, error="simulated pipeline failure")
        return StageReport(name=Stage.SUCCEEDED, result={"status": "ok"})


class RealKubeflowClient:
    def __init__(self, host: str) -> None:
        self._host = host
        self._client = None

    def _kfp_client(self):
        if self._client is None:
            import kfp

            self._client = kfp.Client(host=self._host)
        return self._client

    def submit(self, pipeline_inputs: dict) -> uuid.UUID:
        run = self._kfp_client().create_run_from_pipeline_func(
            pipeline_inputs["pipeline_func"],
            arguments=pipeline_inputs.get("arguments", {}),
        )
        return uuid.UUID(run.run_id)

    def get_stage(self, run_id: uuid.UUID) -> StageReport:
        run_detail = self._kfp_client().get_run(str(run_id))
        status = run_detail.state
        if status in ("SUCCEEDED",):
            return StageReport(name=Stage.SUCCEEDED, result=run_detail)
        if status in ("FAILED", "ERROR"):
            return StageReport(name=Stage.FAILED, error=str(run_detail))
        return StageReport(name=Stage.RUNNING)


@lru_cache
def get_kubeflow_client() -> KubeflowClient:
    mode = os.environ.get("KUBEFLOW_CLIENT", "fake")
    if mode == "fake":
        return FakeKubeflowClient()
    if mode == "real":
        return RealKubeflowClient(os.environ["KUBEFLOW_HOST"])
    raise ValueError(f"Unknown KUBEFLOW_CLIENT: {mode!r}")
