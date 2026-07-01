# Prisma
> Production LLM Engineering Platform

Prisma is a local-first engineering platform for building production-grade LLM systems.

The repository is currently at Phase 6: observability and runtime metrics. It can turn a committed sample corpus into a searchable local vector index, route a query through deterministic workflow steps, return cited answers with workflow and runtime metadata through a minimal FastAPI endpoint, run a local deterministic evaluation harness against committed golden cases, compare prompt-driven behavior against the committed Phase 4 baseline, and inspect generated request-local runtime artifacts.

## Quick Start

Prerequisite: Python 3.11 or newer. The examples below use `python3.11`; replace it with the Python 3.11+ executable available on your machine.

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
python -m app.retrieval.index
python -m evals.runner
python -m evals.regression
python -m app.observability.inspect
```

Generated index files, the manifest, routine evaluation scorecards, prompt-regression reports, and runtime request artifacts are written under `.local/prisma/` and are not committed.

Run the API locally:

```sh
uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

Query the API:

```sh
curl -s \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"question":"What does Prisma mean by provider boundaries?","top_k":4}' \
  http://127.0.0.1:8000/query
```

## Local Checks

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

Tests are correctness tests for ingestion, indexing, retrieval, workflow routing, context assembly, local grounded generation, API schemas, structured errors, the evaluation harness, prompt-regression code, and local runtime observability. Evaluation, regression, and runtime inspection remain local-only; they are not CI gates or hosted telemetry.

## Evaluation Harness

Run the local eval smoke path:

```sh
python -m app.retrieval.index
python -m evals.runner
```

The runner loads `evals/golden/cases.jsonl`, exercises `POST /query` through FastAPI `TestClient`, computes deterministic metrics, and writes `.local/prisma/evals/scorecard.json`.

Baseline policy:

- Committed golden data: `evals/golden/cases.jsonl`
- Committed Phase 4 baseline summary: `evals/baselines/phase4-baseline.json`
- Generated routine scorecard: `.local/prisma/evals/scorecard.json`

Phase 4 does not add LLM-as-judge, semantic similarity, RAGAS, PromptFoo, dashboards, hosted services, or CI gates.

## Prompt Regression

Run the local prompt-regression smoke path:

```sh
python -m evals.runner
python -m evals.regression
```

The regression runner fingerprints the configured prompt, runs the Phase 4 evaluation harness, compares the generated scorecard with `evals/baselines/phase4-baseline.json`, and writes `.local/prisma/evals/regression.json`.

Regression policy:

- Committed eval baseline: `evals/baselines/phase4-baseline.json`
- Committed prompt snapshot: `evals/baselines/phase4-prompt-snapshot.json`
- Generated regression report: `.local/prisma/evals/regression.json`

Prompt regression is informational in Phase 5. It does not add prompt optimization, prompt generation, prompt registries, LLM-as-judge, PromptFoo, dashboards, hosted services, or CI gates.

## Runtime Observability

By default, successful `POST /query` responses include an additive top-level `runtime` block with request id, stage latencies, retrieval attempts, and citation count. When `[observability].enabled = false`, the response keeps the field as `runtime: null`.

Full request-local runtime artifacts are generated at:

- `.local/prisma/runtime/latest-request.json`
- `.local/prisma/runtime/requests/<request_id>.json`

Inspect the latest artifact after a query or eval run:

```sh
python -m app.observability.inspect
```

Runtime artifacts are local generated state. They contain stage events, deterministic counts, source paths, workflow route, and neutral generation backend/model ids; they do not contain question text, prompt text, answer text, provider usage, costs, telemetry exports, dashboards, or external endpoints.

## Documentation

- [Project plan](docs/PRISMA_PROJECT_PLAN_v0.1.md)
- [Repository architecture](docs/PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md)
- [Phase 0 repository skeleton plan](docs/PRISMA_PHASE_0_REPOSITORY_SKELETON_PLAN_v0.1.md)
- [Phase 1 ingestion and indexing plan](docs/PRISMA_PHASE_1_INGESTION_INDEXING_PLAN_v0.1.md)
- [Phase 2 baseline RAG API plan](docs/PRISMA_PHASE_2_BASELINE_RAG_API_PLAN_v0.1.md)
- [Phase 3 agent workflow plan](docs/PRISMA_PHASE_3_AGENT_WORKFLOW_PLAN_v0.1.md)
- [Phase 4 evaluation harness plan](docs/PRISMA_PHASE_4_EVALUATION_HARNESS_PLAN_v0.1.md)
- [Phase 5 prompt regression plan](docs/PRISMA_PHASE_5_PROMPT_REGRESSION_PLAN_v0.1.md)
- [Phase 6 observability runtime metrics plan](docs/PRISMA_PHASE_6_OBSERVABILITY_RUNTIME_METRICS_PLAN_v0.1.md)
- [Development guide](docs/DEVELOPMENT.md)
