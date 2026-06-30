from __future__ import annotations

from app.api.main import app
from app.api.routes import get_rag_service
from app.generation.service import RagService
from fastapi.testclient import TestClient


def test_query_endpoint_returns_structured_index_not_ready_error(phase1_settings):
    app.dependency_overrides[get_rag_service] = lambda: RagService(settings=phase1_settings)
    try:
        client = TestClient(app)
        response = client.post(
            "/query",
            json={"question": "What does Prisma mean by provider boundaries?", "top_k": 4},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "index_not_ready",
            "message": "Local index is missing. Run python -m app.retrieval.index.",
            "details": {},
        }
    }


def test_query_endpoint_rejects_unknown_fields(phase1_settings):
    app.dependency_overrides[get_rag_service] = lambda: RagService(settings=phase1_settings)
    try:
        client = TestClient(app)
        response = client.post(
            "/query",
            json={
                "question": "What does Prisma mean by provider boundaries?",
                "top_k": 4,
                "unexpected": True,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["details"]["errors"]


def test_query_endpoint_rejects_config_limit_violations(phase1_settings):
    app.dependency_overrides[get_rag_service] = lambda: RagService(settings=phase1_settings)
    try:
        client = TestClient(app)
        response = client.post(
            "/query",
            json={"question": "no", "top_k": 4},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "invalid_request"
    assert body["error"]["message"] == "Question is too short."
