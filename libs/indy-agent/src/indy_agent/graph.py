"""The standalone three-node script-refactoring LangGraph workflow."""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from indy_agent.edits import EditApplicationError, apply_edits
from indy_agent.models import RefactorError, RefactorState, RefactorStatus
from indy_agent.proposer import request_proposal
from indy_agent.validation import SourceValidationError, validate_refactored_script


def _error(status: RefactorStatus, stage: str, message: str, details: dict | None = None) -> dict:
    return {
        "status": status,
        "error": RefactorError(stage=stage, message=message, details=details or {}),
    }


def propose_edits(state: RefactorState) -> dict:
    try:
        proposal = request_proposal(state["source_script"])
    except (ValidationError, ValueError, TypeError) as error:
        return _error(
            RefactorStatus.INVALID_AGENT_RESPONSE,
            "propose_edits",
            "The model response did not match the proposal schema.",
            {"reason": str(error)},
        )
    except Exception as error:  # Network and model service errors are terminal but recoverable.
        return _error(
            RefactorStatus.AGENT_FAILURE,
            "propose_edits",
            "The Ollama proposal request failed.",
            {"reason": str(error)},
        )

    if not proposal.artifacts:
        if proposal.edits:
            return _error(
                RefactorStatus.INVALID_AGENT_RESPONSE,
                "propose_edits",
                "A proposal without artifacts must not include edits.",
            )
        return {
            "proposal": proposal,
            "status": RefactorStatus.NO_ARTIFACTS_FOUND,
            "error": None,
        }
    if not proposal.edits:
        return _error(
            RefactorStatus.INVALID_AGENT_RESPONSE,
            "propose_edits",
            "A proposal with artifacts must include at least one edit.",
        )
    return {
        "proposal": proposal,
        "status": RefactorStatus.PENDING,
        "error": None,
    }


def apply_proposed_edits(state: RefactorState) -> dict:
    proposal = state["proposal"]
    assert proposal is not None
    try:
        refactored_script, diff = apply_edits(state["source_script"], proposal.edits)
    except EditApplicationError as error:
        return _error(RefactorStatus.EDIT_FAILURE, "apply_edits", error.message, error.details)
    return {
        "refactored_script": refactored_script,
        "diff": diff,
        "status": RefactorStatus.PENDING,
        "error": None,
    }


def validate_result(state: RefactorState) -> dict:
    refactored_script = state["refactored_script"]
    assert refactored_script is not None
    proposal = state["proposal"]
    assert proposal is not None
    try:
        validate_refactored_script(refactored_script, proposal.artifacts)
    except SourceValidationError as error:
        return {
            **_error(
                RefactorStatus.INVALID_CODE if error.invalid_code else RefactorStatus.INVALID_CONTRACT,
                "validate_result",
                error.message,
                error.details,
            ),
            "refactored_script": None,
        }
    return {"status": RefactorStatus.SUCCESS, "error": None}


def _after_proposal(state: RefactorState) -> Literal["apply_edits", "end"]:
    return "apply_edits" if state["status"] == RefactorStatus.PENDING else "end"


def _after_application(state: RefactorState) -> Literal["validate_result", "end"]:
    return "validate_result" if state["status"] == RefactorStatus.PENDING else "end"


builder = StateGraph(RefactorState)
builder.add_node("propose_edits", propose_edits)
builder.add_node("apply_edits", apply_proposed_edits)
builder.add_node("validate_result", validate_result)
builder.add_edge(START, "propose_edits")
builder.add_conditional_edges("propose_edits", _after_proposal, {"apply_edits": "apply_edits", "end": END})
builder.add_conditional_edges("apply_edits", _after_application, {"validate_result": "validate_result", "end": END})
builder.add_edge("validate_result", END)

graph = builder.compile()
