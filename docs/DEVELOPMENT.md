# Development

This repository is in Phase 1. It contains the repository skeleton plus local ingestion and indexing for the committed sample corpus.

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

Run the same command again to verify idempotency. The second run should report that the index is already up to date.

Generated artifacts are written under `.local/prisma/`, which is ignored by git.

## Checks

```sh
python -m ruff check .
python -m ruff format --check .
python -m mypy app
python -m pytest
python -m app.retrieval.index
python -m app.retrieval.index
```

The tests are code correctness tests for Phase 1. They are not evaluation scorecards and do not create an evaluation harness.

## Contribution Boundaries

Follow the Phase 0 skeleton plan and repository architecture:

- Keep Phase 1 focused on ingestion and indexing.
- Do not create deferred directories before their phase needs them.
- Do not add answer generation, chat, prompts, agents, evals, CI, Docker, hosted services, or secrets.
- Keep dependencies declared in `pyproject.toml`; do not add `requirements.txt`.
- Keep secrets and local runtime state out of version control.
