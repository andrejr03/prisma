# Prisma
> Production LLM Engineering Platform

Prisma is a local-first engineering platform for building production-grade LLM systems.

The repository is currently at Phase 1: ingestion and indexing. It can turn a committed sample corpus into a searchable local vector index with deterministic chunking, stable ids, local embeddings, and a generated manifest.

## Quick Start

Prerequisite: Python 3.11 or newer. The examples below use `python3.11`; replace it with the Python 3.11+ executable available on your machine.

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
python -m app.retrieval.index
python -m app.retrieval.index
```

The second indexing run should report that the index is already up to date. Generated index files and the manifest are written under `.local/prisma/` and are not committed.

## Local Checks

```sh
python -m ruff check .
python -m ruff format --check .
python -m mypy app
python -m pytest
python -m app.retrieval.index
```

Phase 1 tests are correctness tests for ingestion, chunking, identifiers, local embeddings, vector persistence, and idempotent indexing. They are not an evaluation harness.

## Documentation

- [Project plan](docs/PRISMA_PROJECT_PLAN_v0.1.md)
- [Repository architecture](docs/PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md)
- [Phase 0 repository skeleton plan](docs/PRISMA_PHASE_0_REPOSITORY_SKELETON_PLAN_v0.1.md)
- [Phase 1 ingestion and indexing plan](docs/PRISMA_PHASE_1_INGESTION_INDEXING_PLAN_v0.1.md)
- [Development guide](docs/DEVELOPMENT.md)
