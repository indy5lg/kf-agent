"""Bounded LangGraph workflow for ML-script artifact refactoring."""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph
from langchain_core.exceptions import OutputParserException
from pydantic import ValidationError

from indy_agent.edits import EditApplicationError, apply_edits, create_diff
from indy_agent.models import (
    AttemptKind,
    DiffTraceEntry,
    RefactorError,
    RefactorState,
    RefactorStatus,
)
from indy_agent.proposer import request_proposal, request_repair
from indy_agent.validation import SourceValidationError, validate_refactored_script

MAX_PROPOSAL_ATTEMPTS = 2
RETRYABLE_STATUSES = {
    RefactorStatus.INVALID_AGENT_RESPONSE,
    RefactorStatus.EDIT_FAILURE,
    RefactorStatus.INVALID_CODE,
    RefactorStatus.INVALID_CONTRACT,
}


def _error(status: RefactorStatus, stage: str, message: str, details: dict | None = None) -> dict:
    return {
        "status": status,
        "error": RefactorError(stage=stage, message=message, details=details or {}),
    }


def _append_trace(
    state: RefactorState,
    *,
    proposal=None,
    feedback: RefactorError | None = None,
    patch_diff: str | None = None,
    outcome: RefactorStatus,
    error: RefactorError | None = None,
) -> list[DiffTraceEntry]:
    return [
        *state.get("diff_trace", []),
        DiffTraceEntry(
            attempt_number=state["attempt_count"],
            kind=state["attempt_kind"],
            proposal=proposal,
            feedback=feedback,
            patch_diff=patch_diff,
            outcome=outcome,
            error=error,
        ),
    ]


def _replace_last_trace(state: RefactorState, *, outcome: RefactorStatus, error: RefactorError | None) -> list[DiffTraceEntry]:
    trace = list(state.get("diff_trace", []))
    if trace:
        trace[-1] = trace[-1].model_copy(update={"outcome": outcome, "error": error})
    return trace


def initialize_working_script(state: RefactorState) -> dict:
    """Establish the immutable-source/current-candidate invariant."""
    return {
        "working_script": state["source_script"],
        "proposal": None,
        "diff": "",
        "diff_trace": [],
        "attempt_count": 0,
        "repair_feedback": None,
        "status": RefactorStatus.PENDING,
        "error": None,
    }


def _propose(state: RefactorState, *, kind: AttemptKind) -> dict:
    feedback = state.get("error") if kind == AttemptKind.REPAIR else None
    count = state["attempt_count"] + 1
    trace_state = {**state, "attempt_count": count, "attempt_kind": kind}
    try:
        if kind == AttemptKind.INITIAL:
            proposal = request_proposal(state["source_script"])
        else:
            prior = state.get("proposal")
            proposal = request_repair(
                source_script=state["source_script"],
                working_script=state["working_script"],
                artifacts=[] if prior is None else prior.artifacts,
                error=feedback,
            )
    except (OutputParserException, ValidationError, ValueError, TypeError) as error:
        result = _error(
            RefactorStatus.INVALID_AGENT_RESPONSE,
            "repair_proposal" if kind == AttemptKind.REPAIR else "propose_edits",
            "The model response did not match the proposal schema.",
            {"reason": str(error)},
        )
        return {
            **result,
            "attempt_count": count,
            "attempt_kind": kind,
            "diff_trace": _append_trace(trace_state, feedback=feedback, outcome=result["status"], error=result["error"]),
        }
    except Exception as error:
        result = _error(
            RefactorStatus.AGENT_FAILURE,
            "repair_proposal" if kind == AttemptKind.REPAIR else "propose_edits",
            "The Ollama proposal request failed.",
            {"reason": str(error)},
        )
        return {
            **result,
            "attempt_count": count,
            "attempt_kind": kind,
            "diff_trace": _append_trace(trace_state, feedback=feedback, outcome=result["status"], error=result["error"]),
        }

    common = {
        "proposal": proposal,
        "attempt_count": count,
        "attempt_kind": kind,
        "repair_feedback": feedback,
        "error": None,
    }
    if not proposal.artifacts:
        if proposal.edits:
            result = _error(
                RefactorStatus.INVALID_AGENT_RESPONSE,
                "repair_proposal" if kind == AttemptKind.REPAIR else "propose_edits",
                "A proposal without artifacts must not include edits.",
            )
            return {
                **common,
                **result,
                "diff_trace": _append_trace(trace_state, proposal=proposal, feedback=feedback, outcome=result["status"], error=result["error"]),
            }
        return {
            **common,
            "status": RefactorStatus.NO_ARTIFACTS_FOUND,
            "diff_trace": _append_trace(trace_state, proposal=proposal, feedback=feedback, outcome=RefactorStatus.NO_ARTIFACTS_FOUND),
        }
    if not proposal.edits:
        result = _error(
            RefactorStatus.INVALID_AGENT_RESPONSE,
            "repair_proposal" if kind == AttemptKind.REPAIR else "propose_edits",
            "A proposal with artifacts must include at least one edit.",
        )
        return {
            **common,
            **result,
            "diff_trace": _append_trace(trace_state, proposal=proposal, feedback=feedback, outcome=result["status"], error=result["error"]),
        }
    return {**common, "status": RefactorStatus.PENDING}


def propose_edits(state: RefactorState) -> dict:
    return _propose(state, kind=AttemptKind.INITIAL)


def repair_proposal(state: RefactorState) -> dict:
    return _propose(state, kind=AttemptKind.REPAIR)


def apply_proposed_edits(state: RefactorState) -> dict:
    proposal = state["proposal"]
    assert proposal is not None
    try:
        working_script, patch_diff = apply_edits(state["working_script"], proposal.edits)
    except EditApplicationError as error:
        result = _error(RefactorStatus.EDIT_FAILURE, "apply_edits", error.message, error.details)
        return {
            **result,
            "diff_trace": _append_trace(
                state,
                proposal=proposal,
                feedback=state.get("repair_feedback"),
                outcome=result["status"],
                error=result["error"],
            ),
        }
    return {
        "working_script": working_script,
        "diff": create_diff(state["source_script"], working_script),
        "diff_trace": _append_trace(
            state,
            proposal=proposal,
            feedback=state.get("repair_feedback"),
            patch_diff=patch_diff,
            outcome=RefactorStatus.PENDING,
        ),
        "status": RefactorStatus.PENDING,
        "error": None,
    }


def validate_result(state: RefactorState) -> dict:
    proposal = state["proposal"]
    assert proposal is not None
    try:
        validate_refactored_script(state["working_script"], proposal.artifacts)
    except SourceValidationError as error:
        status = RefactorStatus.INVALID_CODE if error.invalid_code else RefactorStatus.INVALID_CONTRACT
        result = _error(status, "validate_result", error.message, error.details)
        return {**result, "diff_trace": _replace_last_trace(state, outcome=status, error=result["error"])}
    return {
        "status": RefactorStatus.SUCCESS,
        "error": None,
        "diff_trace": _replace_last_trace(state, outcome=RefactorStatus.SUCCESS, error=None),
    }


def _should_repair(state: RefactorState) -> bool:
    return state["status"] in RETRYABLE_STATUSES and state["attempt_count"] < MAX_PROPOSAL_ATTEMPTS


def _after_attempt(state: RefactorState) -> Literal["apply_edits", "repair_proposal", "end"]:
    if state["status"] == RefactorStatus.PENDING:
        return "apply_edits"
    return "repair_proposal" if _should_repair(state) else "end"


def _after_application(state: RefactorState) -> Literal["validate_result", "repair_proposal", "end"]:
    if state["status"] == RefactorStatus.PENDING:
        return "validate_result"
    return "repair_proposal" if _should_repair(state) else "end"


def _after_validation(state: RefactorState) -> Literal["repair_proposal", "end"]:
    return "repair_proposal" if _should_repair(state) else "end"


builder = StateGraph(RefactorState)
builder.add_node("initialize_working_script", initialize_working_script)
builder.add_node("propose_edits", propose_edits)
builder.add_node("repair_proposal", repair_proposal)
builder.add_node("apply_edits", apply_proposed_edits)
builder.add_node("validate_result", validate_result)
builder.add_edge(START, "initialize_working_script")
builder.add_edge("initialize_working_script", "propose_edits")
builder.add_conditional_edges("propose_edits", _after_attempt, {"apply_edits": "apply_edits", "repair_proposal": "repair_proposal", "end": END})
builder.add_conditional_edges("repair_proposal", _after_attempt, {"apply_edits": "apply_edits", "repair_proposal": "repair_proposal", "end": END})
builder.add_conditional_edges("apply_edits", _after_application, {"validate_result": "validate_result", "repair_proposal": "repair_proposal", "end": END})
builder.add_conditional_edges("validate_result", _after_validation, {"repair_proposal": "repair_proposal", "end": END})

graph = builder.compile()
