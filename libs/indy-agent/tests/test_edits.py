import pytest

from indy_agent.edits import EditApplicationError, apply_edits
from indy_agent.models import Edit


def test_apply_edits_returns_transformed_source_and_diff() -> None:
    result, diff = apply_edits("path = 'data'\n", [Edit(old_text="'data'", new_text="args.dataset_path", expected_matches=1, purpose="parameterize")])
    assert result == "path = args.dataset_path\n"
    assert "-path = 'data'" in diff
    assert "+path = args.dataset_path" in diff


@pytest.mark.parametrize("expected_matches", [1, 3])
def test_apply_edits_rejects_incorrect_match_count(expected_matches: int) -> None:
    with pytest.raises(EditApplicationError):
        apply_edits("value = 'data'\nvalue = 'data'\n", [Edit(old_text="'data'", new_text="args.path", expected_matches=expected_matches, purpose="parameterize")])


def test_apply_edits_rejects_overlapping_anchors_without_partial_result() -> None:
    edits = [
        Edit(old_text="value = 'data'", new_text="value = args.path", expected_matches=1, purpose="first"),
        Edit(old_text="'data'", new_text="args.path", expected_matches=1, purpose="second"),
    ]
    with pytest.raises(EditApplicationError, match="overlapping"):
        apply_edits("value = 'data'\n", edits)


def test_apply_edits_rejects_a_missing_anchor() -> None:
    with pytest.raises(EditApplicationError) as error:
        apply_edits("value = 'data'\n", [Edit(old_text="missing", new_text="replacement", expected_matches=1, purpose="missing")])
    assert error.value.details["actual_matches"] == 0


def test_apply_edits_matches_single_line_import_not_longer_import_prefixes() -> None:
    source = (
        "import torch\n"
        "import torch.nn as nn\n"
        "import torch.optim as optim\n"
        "import torchvision\n"
        "import torchvision.transforms as transforms\n"
    )
    result, _ = apply_edits(
        source,
        [
            Edit(
                old_text="import torch",
                new_text="import torch\nimport argparse",
                expected_matches=1,
                purpose="add argparse import",
            )
        ],
    )
    assert result == (
        "import torch\n"
        "import argparse\n"
        "import torch.nn as nn\n"
        "import torch.optim as optim\n"
        "import torchvision\n"
        "import torchvision.transforms as transforms\n"
    )
