import pytest

from indy_agent.models import Artifact, ValidationViolationCode
from indy_agent.validation import SourceValidationError, validate_refactored_script


ARTIFACTS = [Artifact(name="dataset", direction="input", kind="dataset", cli_argument="--dataset-path")]


def test_validation_accepts_matching_argparse_contract() -> None:
    validate_refactored_script(
        "import argparse\nparser = argparse.ArgumentParser()\nparser.add_argument('--dataset-path')\nargs = parser.parse_args()\nprint(args.dataset_path)\n",
        ARTIFACTS,
    )


def test_validation_rejects_invalid_python_without_execution() -> None:
    with pytest.raises(SourceValidationError) as error:
        validate_refactored_script("if True print('never execute')\n", ARTIFACTS)
    assert error.value.invalid_code
    assert error.value.details["line"] == 1
    assert "violations" not in error.value.details


@pytest.mark.parametrize(
    "source,expected_violation",
    [
        (
            "parser = object()\nparser.add_argument('--dataset-path')\nargs = parser.parse_args()\nprint(args.dataset_path)\n",
            {"code": ValidationViolationCode.MISSING_ARGPARSE_IMPORT},
        ),
        (
            "import argparse\nparser = argparse.ArgumentParser()\nparser.add_argument('--dataset-path')\nprint(args.dataset_path)\n",
            {"code": ValidationViolationCode.MISSING_PARSE_ARGS},
        ),
        (
            "import argparse\nparser = argparse.ArgumentParser()\nargs = parser.parse_args()\nprint(args.dataset_path)\n",
            {
                "code": ValidationViolationCode.MISSING_CLI_ARGUMENT,
                "artifact": "dataset",
                "expected_cli_argument": "--dataset-path",
            },
        ),
        (
            "import argparse\nparser = argparse.ArgumentParser()\nparser.add_argument('--dataset-path')\nargs = parser.parse_args()\n",
            {
                "code": ValidationViolationCode.MISSING_ARGUMENT_DESTINATION,
                "artifact": "dataset",
                "expected_destination": "args.dataset_path",
            },
        ),
    ],
)
def test_validation_reports_an_isolated_contract_violation(
    source: str, expected_violation: dict[str, object]
) -> None:
    with pytest.raises(SourceValidationError) as error:
        validate_refactored_script(source, ARTIFACTS)
    assert not error.value.invalid_code
    assert error.value.details == {"violations": [expected_violation]}


def test_validation_collects_every_artifact_violation_in_proposal_order() -> None:
    artifacts = [
        Artifact(name="dataset", direction="input", kind="dataset", cli_argument="--dataset-path"),
        Artifact(name="model", direction="output", kind="model", cli_argument="--model-path"),
    ]
    source = "import argparse\nparser = argparse.ArgumentParser()\nargs = parser.parse_args()\n"
    with pytest.raises(SourceValidationError) as error:
        validate_refactored_script(source, artifacts)

    assert error.value.details == {
        "violations": [
            {"code": "missing_cli_argument", "artifact": "dataset", "expected_cli_argument": "--dataset-path"},
            {"code": "missing_argument_destination", "artifact": "dataset", "expected_destination": "args.dataset_path"},
            {"code": "missing_cli_argument", "artifact": "model", "expected_cli_argument": "--model-path"},
            {"code": "missing_argument_destination", "artifact": "model", "expected_destination": "args.model_path"},
        ]
    }


def test_validation_orders_global_violations_before_artifact_violations() -> None:
    with pytest.raises(SourceValidationError) as error:
        validate_refactored_script("args = object()\n", ARTIFACTS)

    assert error.value.details == {
        "violations": [
            {"code": "missing_argparse_import"},
            {"code": "missing_parse_args"},
            {"code": "missing_cli_argument", "artifact": "dataset", "expected_cli_argument": "--dataset-path"},
            {"code": "missing_argument_destination", "artifact": "dataset", "expected_destination": "args.dataset_path"},
        ]
    }
