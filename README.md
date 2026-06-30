# Prisma
> Production LLM Engineering Platform

Prisma is a local-first engineering platform for building production-grade LLM systems.

The repository is currently at Phase 4: evaluation harness. It can turn a committed sample corpus into a searchable local vector index, route a query through deterministic workflow steps, return cited answers with workflow metadata through a minimal FastAPI endpoint, and run a local deterministic evaluation harness against committed golden cases.

## Quick Start

Prerequisite: Python 3.11 or newer. The examples below use `python3.11`; replace it with the Python 3.11+ executable available on your machine.

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
python -m app.retrieval.index
python -m evals.runner
```

Generated index files, the manifest, and routine evaluation scorecards are written under `.local/prisma/` and are not committed.

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
```

Tests are correctness tests for ingestion, indexing, retrieval, workflow routing, context assembly, local grounded generation, API schemas, structured errors, and the evaluation harness code. The evaluation runner measures end-to-end behavior and writes a generated scorecard; it is not a CI gate.

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

Phase 4 does not add LLM-as-judge, semantic similarity, RAGAS, PromptFoo, prompt regression, dashboards, hosted services, or CI gates.

## Documentation

- [Project plan](docs/PRISMA_PROJECT_PLAN_v0.1.md)
- [Repository architecture](docs/PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md)
- [Phase 0 repository skeleton plan](docs/PRISMA_PHASE_0_REPOSITORY_SKELETON_PLAN_v0.1.md)
- [Phase 1 ingestion and indexing plan](docs/PRISMA_PHASE_1_INGESTION_INDEXING_PLAN_v0.1.md)
- [Phase 2 baseline RAG API plan](docs/PRISMA_PHASE_2_BASELINE_RAG_API_PLAN_v0.1.md)
- [Phase 3 agent workflow plan](docs/PRISMA_PHASE_3_AGENT_WORKFLOW_PLAN_v0.1.md)
- [Phase 4 evaluation harness plan](docs/PRISMA_PHASE_4_EVALUATION_HARNESS_PLAN_v0.1.md)
- [Development guide](docs/DEVELOPMENT.md)
