from __future__ import annotations

from dataclasses import replace
from typing import Any

from app.api.main import app
from app.api.routes import get_rag_service
from app.config import PrismaSettings
from app.generation.service import RagService
from app.retrieval.pipeline import run_indexing
from fastapi.testclient import TestClient


def test_api_runtime_block_is_additive_and_business_fields_are_invariant(
    phase1_settings: PrismaSettings,
) -> None:
    run_indexing(phase1_settings)
    enabled_settings = _with_observability(
        phase1_settings,
        enabled=True,
        runtime_dir=".local/prisma/runtime",
    )
    disabled_settings = _with_observability(
        phase1_settings,
        enabled=False,
        runtime_dir=".local/prisma/runtime",
    )

    enabled_body = _query_body(enabled_settings)
    disabled_body = _query_body(disabled_settings)

    assert enabled_body["runtime"] is not None
    assert disabled_body["runtime"] is None
    assert set(enabled_body["runtime"]) == {
        "request_id",
        "total_latency_ms",
        "retrieval_latency_ms",
        "context_assembly_latency_ms",
        "generation_latency_ms",
        "validation_latency_ms",
        "retrieval_attempts",
        "citation_count",
    }
    assert (
        enabled_body["runtime"]["retrieval_attempts"]
        == enabled_body["workflow"]["retrieval_attempts"]
    )
    assert enabled_body["runtime"]["citation_count"] == len(enabled_body["citations"])

    business_fields = ["answer", "citations", "retrieved_context", "metadata", "workflow"]
    assert {key: enabled_body[key] for key in business_fields} == {
        key: disabled_body[key] for key in business_fields
    }

    runtime_dir = enabled_settings.repo_root / enabled_settings.observability.runtime_dir
    request_id = enabled_body["runtime"]["request_id"]
    assert (runtime_dir / "latest-request.json").exists()
    assert (runtime_dir / "requests" / f"{request_id}.json").exists()


def _with_observability(
    settings: PrismaSettings,
    *,
    enabled: bool,
    runtime_dir: str,
) -> PrismaSettings:
    return replace(
        settings,
        observability=replace(
            settings.observability,
            enabled=enabled,
            runtime_dir=runtime_dir,
        ),
    )


def _query_body(settings: PrismaSettings) -> dict[str, Any]:
    app.dependency_overrides[get_rag_service] = lambda: RagService(settings=settings)
    try:
        client = TestClient(app)
        response = client.post(
            "/query",
            json={"question": "What does Prisma mean by provider boundaries?", "top_k": 4},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    return body
