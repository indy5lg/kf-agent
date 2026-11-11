"""Deterministic third-party dependency analysis for Python source."""

from __future__ import annotations

import ast
import sys

from indy_agent.models import DependencyAnalysis


IMPORT_TO_PYPI: dict[str, str] = {
    "PIL": "Pillow",
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "datasets": "datasets",
    "joblib": "joblib",
    "keras": "keras",
    "lightgbm": "lightgbm",
    "matplotlib": "matplotlib",
    "mlflow": "mlflow",
    "numpy": "numpy",
    "pandas": "pandas",
    "requests": "requests",
    "scipy": "scipy",
    "seaborn": "seaborn",
    "sklearn": "scikit-learn",
    "tensorflow": "tensorflow",
    "torch": "torch",
    "torchaudio": "torchaudio",
    "torchvision": "torchvision",
    "tqdm": "tqdm",
    "transformers": "transformers",
    "wandb": "wandb",
    "xgboost": "xgboost",
    "yaml": "PyYAML",
}

STANDARD_LIBRARY_MODULES = frozenset({*sys.stdlib_module_names, *sys.builtin_module_names, "__future__"})


def collect_import_roots(source_script: str) -> list[str]:
    """Collect sorted top-level roots from absolute static imports only."""
    roots: set[str] = set()
    for node in ast.walk(ast.parse(source_script)):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".", 1)[0])
    return sorted(roots)


def analyze_dependencies(source_script: str) -> DependencyAnalysis:
    """Return stable requirements and unresolved roots without executing code."""
    imported_modules = collect_import_roots(source_script)
    standard_library_modules = sorted(set(imported_modules) & STANDARD_LIBRARY_MODULES)
    candidates = set(imported_modules) - STANDARD_LIBRARY_MODULES
    requirements = sorted({IMPORT_TO_PYPI[root] for root in candidates if root in IMPORT_TO_PYPI})
    unresolved_modules = sorted(root for root in candidates if root not in IMPORT_TO_PYPI)
    return DependencyAnalysis(
        imported_modules=imported_modules,
        standard_library_modules=standard_library_modules,
        requirements=requirements,
        requirements_text="".join(f"{requirement}\n" for requirement in requirements),
        unresolved_modules=unresolved_modules,
    )
