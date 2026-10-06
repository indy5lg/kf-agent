import pytest

from indy_agent import InvalidScript, compile_script

VALID_SCRIPT = b"""
from kfp import dsl

@dsl.component
def say_hi() -> str:
    return "hi"

@dsl.pipeline
def my_pipeline():
    say_hi()
"""

SYNTAX_ERROR_SCRIPT = b"""
from kfp import dsl

@dsl.pipeline
def broken_pipeline(
    pass
"""

NO_PIPELINE_SCRIPT = b"""
from kfp import dsl

@dsl.component
def say_hi() -> str:
    return "hi"
"""

MULTIPLE_PIPELINES_SCRIPT = b"""
from kfp import dsl

@dsl.pipeline
def pipeline_one():
    pass

@dsl.pipeline
def pipeline_two():
    pass
"""


def test_valid_script_compiles_successfully():
    inputs = compile_script(VALID_SCRIPT, preset_prompt="Explain this pipeline")

    assert inputs.preset_prompt == "Explain this pipeline"
    assert inputs.pipeline_func is not None


def test_syntax_error_raises_invalid_script():
    with pytest.raises(InvalidScript):
        compile_script(SYNTAX_ERROR_SCRIPT, preset_prompt="Explain this pipeline")


def test_no_decorated_function_raises_invalid_script():
    with pytest.raises(InvalidScript):
        compile_script(NO_PIPELINE_SCRIPT, preset_prompt="Explain this pipeline")


def test_multiple_decorated_functions_raises_invalid_script():
    with pytest.raises(InvalidScript):
        compile_script(MULTIPLE_PIPELINES_SCRIPT, preset_prompt="Explain this pipeline")
