# Development

This repository is in Phase 4. It contains the repository skeleton, local ingestion and indexing for the committed sample corpus, a baseline RAG API over the local index, a bounded workflow that validates, retrieves, optionally rewrites once, generates, and validates citations, and a deterministic local evaluation harness.

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

Successful responses include the existing answer, citation, context, and metadata fields plus a `workflow` object with the terminal status, route, retrieval attempt count, retry limit, rewritten query, and context sufficiency flag.

## Checks

```sh
python -m ruff check .
python -m ruff format --check .
python -m mypy app evals
python -m pytest
python -m app.retrieval.index
python -m evals.runner
```

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

The tests are code correctness tests for the application and evaluation harness. The eval runner measures behavior through the public API boundary and produces a scorecard; it does not enforce a CI gate in Phase 4.

## Evaluation Assets

Phase 4 keeps evaluation data and generated artifacts separate:

- Golden cases are committed at `evals/golden/cases.jsonl`.
- The promoted Phase 4 baseline summary is committed at `evals/baselines/phase4-baseline.json`.
- Routine scorecards are generated at `.local/prisma/evals/scorecard.json` and remain ignored by git.

Do not overwrite the committed baseline during routine eval runs. Promote a new baseline only as an explicit reviewed change.

## Contribution Boundaries

Follow the approved plans and repository architecture:

- Keep existing Phase 3 workflow behavior unchanged unless a later approved plan says otherwise.
- Keep Phase 4 focused on deterministic local evaluation through the public API boundary.
- Do not create deferred directories before their phase needs them.
- Do not add open-ended agents, autonomous tool use, multi-agent systems, chat memory, CI, Docker, hosted services, dashboards, LLM-as-judge metrics, RAGAS, PromptFoo, provider comparisons, UI, provider-specific model APIs, or secrets.
- Keep prompts as data assets under `prompts/`; do not add prompt registries or versioning systems in Phase 4.
- Keep dependencies declared in `pyproject.toml`; do not add `requirements.txt`.
- Keep secrets and local runtime state out of version control.
