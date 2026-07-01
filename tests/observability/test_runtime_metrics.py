from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from app.config import PrismaSettings, load_settings
from app.models.rag import (
    Citation,
    QueryResponse,
    ResponseMetadata,
    RetrievedContextItem,
    WorkflowMetadata,
)
from app.observability.models import RuntimeEvent, RuntimeMetrics
from app.observability.runtime import RuntimeRecorder, is_safe_request_id


def test_runtime_request_ids_are_unique_and_filename_safe(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    first = RuntimeRecorder.from_settings(settings)
    second = RuntimeRecorder.from_settings(settings)

    assert first.request_id != second.request_id
    assert is_safe_request_id(first.request_id)
    assert is_safe_request_id(second.request_id)


def test_runtime_recorder_orders_events_aggregates_metrics_and_writes_artifacts(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    recorder = RuntimeRecorder.from_settings(settings)

    recorder.start_request()
    with recorder.stage("validate_query"):
        pass
    with recorder.stage("retrieve_context") as span:
        span.set_details({"attempt": 1, "retrieved_count": 2})
    with recorder.stage("retrieve_context") as span:
        span.set_details({"attempt": 2, "retrieved_count": 2})
    with recorder.stage("assemble_context") as span:
        recorder.record_context(context='[1] title="Provider Boundaries"\ncontext')
        span.set_details({"context_item_count": 2, "context_char_count": 39})
    with recorder.stage("generate_answer") as span:
        recorder.record_prompt(prompt="Answer using supplied context.")
        span.set_details(
            {
                "generation_backend": "local-grounded",
                "generation_model_id": "local-grounded-v1",
            }
        )
    with recorder.stage("validate_citations") as span:
        span.set_detail("citation_count", 1)
    with recorder.stage("finalize_response"):
        pass

    response = recorder.complete_response(_sample_response())

    assert response.runtime is not None
    runtime_dir = settings.repo_root / settings.observability.runtime_dir
    latest_path = runtime_dir / "latest-request.json"
    request_path = runtime_dir / "requests" / f"{response.runtime.request_id}.json"
    assert latest_path.exists()
    assert request_path.exists()

    latest_payload = _read_payload(latest_path)
    request_payload = _read_payload(request_path)
    assert latest_payload == request_payload

    events = [RuntimeEvent.model_validate(event) for event in latest_payload["events"]]
    metrics = RuntimeMetrics.model_validate(latest_payload["metrics"])
    assert [event.sequence for event in events] == list(range(len(events)))
    assert [event.stage for event in events] == [
        "request",
        "validate_query",
        "retrieve_context",
        "retrieve_context",
        "assemble_context",
        "generate_answer",
        "validate_citations",
        "finalize_response",
        "request",
    ]
    assert [event.status for event in events] == [
        "started",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
    ]
    assert {event.request_id for event in events} == {metrics.request_id}
    assert response.runtime.request_id == metrics.request_id
    assert all(event.duration_ms is None or event.duration_ms >= 0.0 for event in events)

    assert metrics.status == "completed"
    assert metrics.error_code is None
    assert metrics.retrieval_attempts == 2
    assert metrics.retrieved_context_count == 2
    assert metrics.retrieved_source_paths == [
        "datasets/sample_corpus/provider-boundaries.md",
        "datasets/sample_corpus/configuration-and-secrets.md",
    ]
    assert metrics.citation_count == 1
    assert metrics.answer_char_count == len(_sample_response().answer)
    assert metrics.generated_answer_sentence_count == 2
    assert metrics.context_char_count == 39
    assert metrics.prompt_char_count == len("Answer using supplied context.")
    assert metrics.workflow_route == [
        "validate_query",
        "retrieve_context",
        "assemble_context",
        "generate_answer",
        "validate_citations",
        "finalize_response",
    ]
    assert metrics.generation_backend == "local-grounded"
    assert metrics.generation_model_id == "local-grounded-v1"
    assert response.runtime.retrieval_attempts == 2
    assert response.runtime.citation_count == 1

    artifact_text = latest_path.read_text(encoding="utf-8")
    assert "What does Prisma mean" not in artifact_text
    assert "Answer using supplied context." not in artifact_text
    assert "First sentence." not in artifact_text


def test_runtime_recorder_disabled_returns_null_runtime_and_writes_no_artifacts(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path, enabled=False)
    recorder = RuntimeRecorder.from_settings(settings)

    recorder.start_request()
    with recorder.stage("validate_query"):
        pass
    response = recorder.complete_response(_sample_response())

    assert response.runtime is None
    assert not (settings.repo_root / settings.observability.runtime_dir).exists()


def test_runtime_dir_outside_local_is_rejected(tmp_path: Path) -> None:
    settings = _settings(tmp_path, runtime_dir="runtime")
    recorder = RuntimeRecorder.from_settings(settings)

    with pytest.raises(ValueError, match="under .local"):
        recorder.runtime_dir()


def _settings(
    repo_root: Path,
    *,
    runtime_dir: str = ".local/prisma/runtime",
    enabled: bool = True,
) -> PrismaSettings:
    settings = load_settings()
    return replace(
        settings,
        repo_root=repo_root,
        observability=replace(
            settings.observability,
            enabled=enabled,
            runtime_dir=runtime_dir,
        ),
    )


def _sample_response() -> QueryResponse:
    return QueryResponse(
        answer="First sentence. Second sentence [1]",
        citations=[
            Citation(
                citation_id=1,
                source_document="Provider Boundaries",
                source_path="datasets/sample_corpus/provider-boundaries.md",
                chunk_id="provider-boundaries:0",
                chunk_index=0,
                score=0.9,
            )
        ],
        retrieved_context=[
            RetrievedContextItem(
                citation_id=1,
                chunk_id="provider-boundaries:0",
                source_document="Provider Boundaries",
                source_path="datasets/sample_corpus/provider-boundaries.md",
                chunk_index=0,
                score=0.9,
                text="Provider boundaries keep adapters isolated.",
                truncated=False,
            ),
            RetrievedContextItem(
                citation_id=2,
                chunk_id="configuration-and-secrets:0",
                source_document="Configuration and Secrets",
                source_path="datasets/sample_corpus/configuration-and-secrets.md",
                chunk_index=0,
                score=0.8,
                text="Configuration stays declarative.",
                truncated=False,
            ),
        ],
        metadata=ResponseMetadata(
            retrieval_top_k=2,
            context_item_count=2,
            generation_backend="local-grounded",
            generation_model_id="local-grounded-v1",
        ),
        workflow=WorkflowMetadata(
            status="completed",
            retrieval_attempts=2,
            max_retrieval_attempts=2,
            route=[
                "validate_query",
                "retrieve_context",
                "assemble_context",
                "generate_answer",
                "validate_citations",
                "finalize_response",
            ],
            rewritten_query=None,
            context_sufficient=True,
        ),
    )


def _read_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload
