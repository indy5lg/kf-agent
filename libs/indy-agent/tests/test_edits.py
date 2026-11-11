import pytest

from indy_agent.edits import EditApplicationError, apply_edits
from indy_agent.models import Edit


def test_apply_edits_returns_transformed_source_and_diff() -> None:
    result, diff = apply_edits("path = 'data'\n", [Edit(old_text="'data'", new_text="args.dataset_path", expected_matches=1, purpose="parameterize")])
    assert result == "path = args.dataset_path\n"
    assert "-path = 'data'" in diff
    assert "+path = args.dataset_path" in diff


@pytest.mark.parametrize(
    "source,edit,expected_details",
    [
        (
            "value = 'data'\nvalue = 'data'\n",
            Edit(old_text="'data'", new_text="args.path", expected_matches=1, purpose="parameterize"),
            {"edit_index": 0, "expected_matches": 1, "actual_matches": 2},
        ),
        (
            "value = 'data'\nvalue = 'data'\n",
            Edit(old_text="'data'", new_text="args.path", expected_matches=3, purpose="parameterize"),
            {"edit_index": 0, "expected_matches": 3, "actual_matches": 2},
        ),
        (
            "value = 'data'\n",
            Edit(old_text="missing", new_text="replacement", expected_matches=1, purpose="missing"),
            {"edit_index": 0, "expected_matches": 1, "actual_matches": 0},
        ),
    ],
)
def test_apply_edits_reports_each_anchor_match_mismatch(
    source: str, edit: Edit, expected_details: dict[str, int]
) -> None:
    with pytest.raises(EditApplicationError) as error:
        apply_edits(source, [edit])
    assert error.value.details == expected_details


def test_apply_edits_rejects_overlapping_anchors_without_partial_result() -> None:
    edits = [
        Edit(old_text="value = 'data'", new_text="value = args.path", expected_matches=1, purpose="first"),
        Edit(old_text="'data'", new_text="args.path", expected_matches=1, purpose="second"),
    ]
    with pytest.raises(EditApplicationError, match="overlapping"):
        apply_edits("value = 'data'\n", edits)


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
