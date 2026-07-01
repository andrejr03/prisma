from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from app.config import PrismaSettings, load_settings
from app.observability.inspect import load_runtime_artifact, main, render_summary
from app.observability.models import RuntimeEvent, RuntimeMetrics

_REQUEST_ID = "a" * 32


def test_inspect_reads_latest_artifact_and_prints_summary(
    tmp_path: Path,
    capsys,
) -> None:
    settings = _settings(tmp_path)
    latest_path = _write_artifact(settings)
    before = latest_path.read_text(encoding="utf-8")

    exit_code = main([], settings=settings)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Prisma runtime request" in captured.out
    assert f"Request ID: {_REQUEST_ID}" in captured.out
    assert "Status: completed" in captured.out
    assert "Retrieval attempts: 1" in captured.out
    assert "Workflow route: validate_query -> retrieve_context -> finalize_response" in captured.out
    assert latest_path.read_text(encoding="utf-8") == before


def test_inspect_reads_specific_request_id(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_artifact(settings)

    events, metrics, path = load_runtime_artifact(settings=settings, request_id=_REQUEST_ID)
    summary = render_summary(events=events, metrics=metrics, path=path)

    assert metrics.request_id == _REQUEST_ID
    assert path.name == f"{_REQUEST_ID}.json"
    assert "Generation backend: local-grounded" in summary


def test_inspect_returns_clear_error_when_no_artifact_exists(
    tmp_path: Path,
    capsys,
) -> None:
    settings = _settings(tmp_path)

    exit_code = main([], settings=settings)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "no runtime artifact found; issue a request first" in captured.err


def _settings(repo_root: Path) -> PrismaSettings:
    settings = load_settings()
    return replace(
        settings,
        repo_root=repo_root,
        observability=replace(
            settings.observability,
            runtime_dir=".local/prisma/runtime",
        ),
    )


def _write_artifact(settings: PrismaSettings) -> Path:
    runtime_dir = settings.repo_root / settings.observability.runtime_dir
    latest_path = runtime_dir / "latest-request.json"
    request_path = runtime_dir / "requests" / f"{_REQUEST_ID}.json"
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.parent.mkdir(parents=True, exist_ok=True)

    events = [
        RuntimeEvent(
            request_id=_REQUEST_ID,
            sequence=0,
            timestamp="2026-07-01T00:00:00Z",
            stage="request",
            status="started",
        )
    ]
    metrics = RuntimeMetrics(
        request_id=_REQUEST_ID,
        total_latency_ms=10.0,
        retrieval_latency_ms=2.0,
        context_assembly_latency_ms=1.0,
        generation_latency_ms=3.0,
        validation_latency_ms=1.0,
        retrieval_attempts=1,
        retrieved_context_count=2,
        retrieved_source_paths=["datasets/sample_corpus/provider-boundaries.md"],
        citation_count=1,
        answer_char_count=32,
        generated_answer_sentence_count=2,
        context_char_count=120,
        prompt_char_count=80,
        workflow_route=["validate_query", "retrieve_context", "finalize_response"],
        generation_backend="local-grounded",
        generation_model_id="local-grounded-v1",
        status="completed",
    )
    payload = {
        "events": [event.model_dump(mode="json") for event in events],
        "metrics": metrics.model_dump(mode="json"),
    }
    rendered = json.dumps(payload, indent=2) + "\n"
    latest_path.write_text(rendered, encoding="utf-8")
    request_path.write_text(rendered, encoding="utf-8")
    return latest_path
