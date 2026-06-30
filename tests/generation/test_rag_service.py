from __future__ import annotations

from dataclasses import dataclass

import pytest
from app.generation.service import CitationValidationError, RagService
from app.providers.generation import GenerationRequest, GenerationResult
from app.retrieval.pipeline import run_indexing


def test_rag_service_returns_grounded_answer_with_citations(phase1_settings):
    run_indexing(phase1_settings)
    service = RagService(settings=phase1_settings)

    response = service.answer(
        question="What does Prisma mean by provider boundaries?",
        top_k=4,
    )

    assert response.answer
    assert response.citations
    assert response.citations[0].source_path == "datasets/sample_corpus/provider-boundaries.md"
    assert response.retrieved_context
    assert response.metadata.generation_backend == "local-grounded"
    assert response.workflow.status == "completed"
    assert 1 <= response.workflow.retrieval_attempts <= 2
    assert response.workflow.max_retrieval_attempts == 2
    assert response.workflow.route[0] == "validate_query"
    assert "finalize_response" in response.workflow.route


def test_rag_service_rejects_unknown_generated_citations(phase1_settings):
    run_indexing(phase1_settings)
    service = RagService(settings=phase1_settings, generation_provider=BadCitationProvider())

    with pytest.raises(CitationValidationError):
        service.answer(
            question="What does Prisma mean by provider boundaries?",
            top_k=4,
        )


@dataclass(frozen=True)
class BadCitationProvider:
    model_id: str = "bad-citation-provider"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        return GenerationResult(
            answer=f"{request.question} [999]",
            cited_context_ids=[999],
            model_id=self.model_id,
        )
