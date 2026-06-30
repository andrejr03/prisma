# Development

This repository is in Phase 0. It contains repository skeleton, tooling, and documentation only.

## Setup

Use Python 3.11 or newer. The examples below use `python3.11`; replace it with the Python 3.11+ executable available on your machine.

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## Run

Phase 0 has no application entry point. Verify the package root is importable:

```sh
python -c "import app; print(app.__name__)"
```

## Checks

```sh
python -m ruff check .
python -m ruff format --check .
python -m mypy app
python -m pytest || test $? -eq 5
```

The test runner is configured in `pyproject.toml`, but Phase 0 intentionally does not create a test suite. Tests start when application code is introduced.

## Contribution Boundaries

Follow the Phase 0 skeleton plan and repository architecture:

- Do not add application logic in Phase 0.
- Do not create deferred directories before their phase needs them.
- Keep dependencies declared in `pyproject.toml`; do not add `requirements.txt`.
- Keep secrets and local runtime state out of version control.
