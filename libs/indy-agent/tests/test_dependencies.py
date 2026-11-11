from indy_agent.dependencies import analyze_dependencies, collect_import_roots


def test_collect_import_roots_handles_aliases_nested_imports_and_relative_imports() -> None:
    source = """import torch.nn as nn
from sklearn.metrics import accuracy_score
if True:
    import torchvision.transforms
from .helpers import train
from ..local import settings
"""
    assert collect_import_roots(source) == ["sklearn", "torch", "torchvision"]


def test_analyze_dependencies_excludes_standard_library_and_renders_sorted_requirements() -> None:
    analysis = analyze_dependencies("import pathlib\nimport argparse\nimport torch.nn\nimport torchvision.transforms\n")
    assert analysis.imported_modules == ["argparse", "pathlib", "torch", "torchvision"]
    assert analysis.standard_library_modules == ["argparse", "pathlib"]
    assert analysis.requirements == ["torch", "torchvision"]
    assert analysis.requirements_text == "torch\ntorchvision\n"
    assert analysis.unresolved_modules == []


def test_analyze_dependencies_maps_known_aliases_and_reports_unknown_roots() -> None:
    analysis = analyze_dependencies("import yaml\nfrom PIL import Image\nimport custom_training_helpers\n")
    assert analysis.requirements == ["Pillow", "PyYAML"]
    assert analysis.unresolved_modules == ["custom_training_helpers"]


def test_analyze_dependencies_returns_empty_output_for_standard_library_only_source() -> None:
    analysis = analyze_dependencies("import json\nfrom pathlib import Path\n")
    assert analysis.requirements == []
    assert analysis.requirements_text == ""
    assert analysis.unresolved_modules == []
