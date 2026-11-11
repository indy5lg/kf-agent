# indy-agent

Standalone LangGraph workflow for converting hardcoded ML-script artifact paths into
an inspectable argparse contract for later Kubeflow Pipelines work.

## Setup

From the repository root, install the uv-managed workspace environment:

```bash
uv sync
```

Copy `.env.example` to `.env` inside this directory and configure an Ollama endpoint
when it is not available at `http://localhost:11434`:

```dotenv
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:e4b
```

LangSmith is optional. The graph runs without LangSmith credentials; add the normal
LangSmith environment variables only when tracing is desired.

## Run tests

```bash
uv run --project libs/indy-agent pytest libs/indy-agent/tests
```

The quick baseline Ollama smoke test is skipped unless explicitly requested. It
also skips if the configured endpoint or model is unavailable:

```bash
RUN_OLLAMA_INTEGRATION=1 uv run --project libs/indy-agent pytest libs/indy-agent/tests -m integration
```

To test the baseline script plus both whitespace-only spacing variants, run the
separate comprehensive check:

```bash
RUN_OLLAMA_INTEGRATION=1 uv run --project libs/indy-agent pytest libs/indy-agent/tests -m comprehensive_integration
```

## Run the local agent server

```bash
uv run --project libs/indy-agent langgraph dev --config libs/indy-agent/langgraph.json
```

### Compare Ollama requests from Studio and pytest

For local debugging, set `OLLAMA_DEBUG_CAPTURE_DIR` before starting the server
or running pytest. Each model call writes a JSON file containing the complete
prompt, structured-output schema, Ollama request options, and parsed proposal.
The captured script may contain sensitive code, so use a local directory that
is not committed to Git.

```bash
OLLAMA_DEBUG_CAPTURE_DIR=/tmp/indy-agent-ollama-captures \
OLLAMA_DEBUG_CAPTURE_LABEL=studio \
uv run --project libs/indy-agent langgraph dev --config libs/indy-agent/langgraph.json
```

In another terminal, run the integration test with a different label:

```bash
RUN_OLLAMA_INTEGRATION=1 \
OLLAMA_DEBUG_CAPTURE_DIR=/tmp/indy-agent-ollama-captures \
OLLAMA_DEBUG_CAPTURE_LABEL=pytest \
uv run --project libs/indy-agent pytest libs/indy-agent/tests -m integration -v
```

Compare the resulting `ollama-request-*.json` files. The `ollama_request`
object is the complete request assembled by LangChain immediately before the
Ollama client sends it.

The published graph is `script_refactoring`. Invoke it with raw Python source:

```json
{
  "source_script": "import torch\\n..."
}
```

The result includes a terminal `status`, structured errors when applicable, and
the latest in-memory `working_script`. Only `status: success` marks that script
as usable. `diff` always compares the immutable source with the latest working
script; `diff_trace` records the bounded initial proposal and optional repair
patch outcomes. Its `proposal` contains the complete artifact contract at
`proposal.artifacts`, using `dataset`, `model`, `metrics`, or `artifact`; there
are no top-level `artifacts` or `changes` result fields.

Successful results also include `dependency_analysis`, generated
deterministically from the final `working_script`. Its `requirements` list and
`requirements_text` provide sorted, unpinned requirements content for a later
container build; `unresolved_modules` identifies non-standard imports that are
not in the agent's explicit import-to-PyPI mapping. The first version does not
infer dynamic imports, versions, extras, package indexes, CUDA variants, or
local project packages.

When deterministic proposal, edit, syntax, or artifact-contract validation
fails, the graph may request up to three repair proposals. The repair receives the
original source as reference, the current working script as its only edit
target, the current artifact contract, and the structured failure. Ollama
service failures and `no_artifacts_found` are terminal and are not retried.
