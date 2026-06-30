from __future__ import annotations

from app.api.main import app
from app.api.routes import get_rag_service
from app.generation.service import RagService
from app.retrieval.pipeline import run_indexing
from fastapi.testclient import TestClient


def test_query_endpoint_returns_structured_response(phase1_settings):
    run_indexing(phase1_settings)
    app.dependency_overrides[get_rag_service] = lambda: RagService(settings=phase1_settings)
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
    assert body["answer"]
    assert body["citations"]
    assert body["retrieved_context"]
    assert body["metadata"]["retrieval_top_k"] == 4
    assert body["citations"][0]["source_document"] == "Provider Boundaries"
    assert body["citations"][0]["source_path"] == "datasets/sample_corpus/provider-boundaries.md"
    assert body["citations"][0]["chunk_id"]
