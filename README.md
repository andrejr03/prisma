# Prisma
> Production LLM Engineering Platform

Prisma is a local-first engineering platform for building production-grade LLM systems.

The repository is currently at Phase 0: a minimal skeleton with project tooling, configuration defaults, and documentation only. No application features are implemented in this phase.

## Quick Start

Prerequisite: Python 3.11 or newer. The examples below use `python3.11`; replace it with the Python 3.11+ executable available on your machine.

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
python -c "import app; print(app.__name__)"
```

## Local Checks

```sh
python -m ruff check .
python -m ruff format --check .
python -m mypy app
python -m pytest || test $? -eq 5
```

Phase 0 intentionally does not include tests yet, so the test runner is configured before the first test suite is introduced.

## Documentation

- [Project plan](docs/PRISMA_PROJECT_PLAN_v0.1.md)
- [Repository architecture](docs/PRISMA_REPOSITORY_ARCHITECTURE_v0.1.md)
- [Phase 0 repository skeleton plan](docs/PRISMA_PHASE_0_REPOSITORY_SKELETON_PLAN_v0.1.md)
- [Development guide](docs/DEVELOPMENT.md)
