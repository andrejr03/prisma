# Development

This repository has Phases 0-7 complete. It contains the repository skeleton, local ingestion and indexing for the committed sample corpus, a baseline RAG API over the local index, a bounded workflow that validates, retrieves, optionally rewrites once, generates, and validates citations, a deterministic local evaluation harness, an informational prompt-regression runner, local request-runtime observability, and a GitHub Actions CI/CD evaluation gate.

## Setup

Use Python 3.11 or newer. The examples below use `python3.11`; replace it with the Python 3.11+ executable available on your machine.

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## Run

Build the local vector index:

```sh
python -m app.retrieval.index
```

Generated artifacts are written under `.local/prisma/`, which is ignored by git.

Run the evaluation harness:

```sh
python -m evals.runner
```

The runner verifies or builds the local index if needed, loads `evals/golden/cases.jsonl`, exercises `POST /query` through FastAPI `TestClient`, writes `.local/prisma/evals/scorecard.json`, and prints a concise summary.

Run prompt regression:

```sh
python -m evals.regression
```

The regression runner fingerprints the configured prompt, runs the evaluation harness, compares the generated scorecard with the committed Phase 4 baseline, writes `.local/prisma/evals/regression.json`, and prints a concise summary. Regression remains informational in Phase 7; CI fails only if the command crashes.

Run the baseline API:

```sh
uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

Send a local query:

```sh
curl -s \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"question":"What does Prisma mean by provider boundaries?","top_k":4}' \
  http://127.0.0.1:8000/query
```

If the index is missing, `POST /query` returns a structured `503` error with code `index_not_ready`.

Successful responses include the existing answer, citation, context, and metadata fields plus a `workflow` object with the terminal status, route, retrieval attempt count, retry limit, rewritten query, and context sufficiency flag. They also include an additive `runtime` object when observability is enabled. When observability is disabled, the response keeps `runtime: null`.

Inspect the latest runtime artifact:

```sh
python -m app.observability.inspect
```

The inspection command only reads local JSON artifacts. It does not issue requests, mutate files, access the network, or upload telemetry.
Runtime metrics remain informational in Phase 7; CI fails only if inspection crashes.

## Checks

The local command sequence mirrors CI:

```sh
python -m ruff check .
python -m ruff format --check .
python -m mypy app evals
python -m pytest
python -m app.retrieval.index
python -m evals.runner
python -m evals.regression
python -m app.observability.inspect
```

GitHub Actions runs these commands in the same order on push and pull requests to `main`. CI also reads `.local/prisma/evals/scorecard.json` after `python -m evals.runner` and fails when `aggregate.pass_rate` is below `aggregate.minimum_pass_rate` or either field is missing. Regression and runtime metrics remain informational; only command crashes fail CI for those steps.

API smoke check:

```sh
python - <<'PY'
from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)
response = client.post(
    "/query",
    json={"question": "What does Prisma mean by provider boundaries?", "top_k": 4},
)
assert response.status_code == 200, response.text
body = response.json()
assert body["answer"]
assert body["citations"]
assert body["citations"][0]["source_path"] == "datasets/sample_corpus/provider-boundaries.md"
assert body["citations"][0]["chunk_id"]
print(body["answer"])
PY
```

Workflow smoke check:

```sh
python - <<'PY'
from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)
response = client.post(
    "/query",
    json={"question": "What does Prisma mean by provider boundaries?", "top_k": 4},
)
assert response.status_code == 200, response.text
workflow = response.json()["workflow"]
assert workflow["status"] == "completed"
assert 1 <= workflow["retrieval_attempts"] <= 2
assert workflow["max_retrieval_attempts"] == 2
assert workflow["route"][0] == "validate_query"
assert "finalize_response" in workflow["route"]
print(workflow)
PY
```

Evaluation smoke check:

```sh
python -m evals.runner
test -f .local/prisma/evals/scorecard.json
```

Prompt-regression smoke check:

```sh
python -m evals.regression
test -f .local/prisma/evals/regression.json
```

Runtime observability smoke check:

```sh
python -m app.observability.inspect
test -f .local/prisma/runtime/latest-request.json
```

The tests are code correctness tests for the application, evaluation harness, prompt-regression harness, and runtime observability. The eval and regression runners measure behavior through the public API boundary and produce generated artifacts. Local reports remain under `.local/`; CI uploads the scorecard, regression report, and latest runtime artifact as GitHub Actions artifacts instead of committing them.

## Evaluation Assets

Phase 4 through Phase 7 keep evaluation data, prompt snapshot metadata, runtime metadata, and generated artifacts separate:

- Golden cases are committed at `evals/golden/cases.jsonl`.
- The promoted Phase 4 baseline summary is committed at `evals/baselines/phase4-baseline.json`.
- The Phase 4 prompt snapshot is committed at `evals/baselines/phase4-prompt-snapshot.json`.
- Routine scorecards are generated at `.local/prisma/evals/scorecard.json` and remain ignored by git.
- Routine prompt-regression reports are generated at `.local/prisma/evals/regression.json` and remain ignored by git.
- Runtime request artifacts are generated at `.local/prisma/runtime/latest-request.json` and `.local/prisma/runtime/requests/<request_id>.json` and remain ignored by git.
- CI uploads generated scorecards, regression reports, and latest runtime artifacts as ephemeral workflow artifacts.

Do not overwrite committed baselines or prompt snapshots during routine eval or regression runs. Do not commit runtime artifacts. Promote a new baseline only as an explicit reviewed change.

## Contribution Boundaries

Follow the approved plans and repository architecture:

- Keep existing Phase 3 workflow behavior unchanged unless a later approved plan says otherwise.
- Keep Phase 4 focused on deterministic local evaluation through the public API boundary.
- Keep Phase 5 focused on deterministic, informational prompt regression.
- Keep Phase 6 focused on local request-runtime metrics and generated `.local/prisma/runtime/` artifacts.
- Keep Phase 7 focused on the approved GitHub Actions workflow, local validation sequence, CI-side scorecard assertion, and artifact upload.
- Do not create deferred directories before their phase needs them.
- Do not add open-ended agents, autonomous tool use, multi-agent systems, chat memory, Docker, hosted services, dashboards, LLM-as-judge metrics, RAGAS, PromptFoo, provider comparisons, UI, provider-specific model APIs, real token billing, cost billing integrations, telemetry upload, external monitoring, or secrets.
- Keep prompts as data assets under `prompts/`; do not add prompt registries, prompt generation, prompt optimization, or prompt tuning in Phase 5.
- Keep dependencies declared in `pyproject.toml`; do not add `requirements.txt`.
- Keep secrets and local runtime state out of version control.
