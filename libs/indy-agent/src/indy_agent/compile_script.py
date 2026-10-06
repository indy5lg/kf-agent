import importlib.util
import inspect
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from kfp.dsl.graph_component import GraphComponent


class InvalidScript(Exception):
    pass


@dataclass
class PipelineInputs:
    pipeline_func: GraphComponent
    preset_prompt: str


def compile_script(script_bytes: bytes, preset_prompt: str) -> PipelineInputs:
    module = _import_script(script_bytes)
    pipeline_funcs = [
        obj for _, obj in inspect.getmembers(module) if isinstance(obj, GraphComponent)
    ]

    if len(pipeline_funcs) == 0:
        raise InvalidScript("script defines no @dsl.pipeline-decorated function")
    if len(pipeline_funcs) > 1:
        raise InvalidScript(
            f"script defines {len(pipeline_funcs)} @dsl.pipeline-decorated functions, expected exactly 1"
        )

    return PipelineInputs(pipeline_func=pipeline_funcs[0], preset_prompt=preset_prompt)


def _import_script(script_bytes: bytes):
    try:
        source = script_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InvalidScript("script is not valid UTF-8 text") from exc

    with tempfile.TemporaryDirectory() as tmp_dir:
        module_name = f"uploaded_script_{uuid.uuid4().hex}"
        script_path = Path(tmp_dir) / f"{module_name}.py"
        script_path.write_text(source)

        spec = importlib.util.spec_from_file_location(module_name, script_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            raise InvalidScript(f"script could not be parsed/run: {exc}") from exc
        finally:
            sys.modules.pop(module_name, None)

        return module
