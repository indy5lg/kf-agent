import pytest

from indy_agent.models import Artifact
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


def test_validation_rejects_invalid_indentation() -> None:
    with pytest.raises(SourceValidationError) as error:
        validate_refactored_script("if True:\nprint('bad')\n", ARTIFACTS)
    assert error.value.invalid_code


@pytest.mark.parametrize(
    "source,reason",
    [
        ("args = object()\nprint(args.dataset_path)\n", "does not import argparse"),
        ("import argparse\nparser = argparse.ArgumentParser()\nargs = parser.parse_args()\n", "not defined by argparse"),
        ("import argparse\nparser = argparse.ArgumentParser()\nparser.add_argument('--dataset-path')\nargs = parser.parse_args()\n", "not used through args"),
    ],
)
def test_validation_rejects_mismatched_contract(source: str, reason: str) -> None:
    with pytest.raises(SourceValidationError, match=reason) as error:
        validate_refactored_script(source, ARTIFACTS)
    assert not error.value.invalid_code
