from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from app.config import PrismaSettings
from app.generation.service import InvalidQueryError, NoContextError
from app.retrieval.search import RetrievedChunk
from app.workflow.runner import RagWorkflowRunner


def test_runner_performs_no_retrieval_when_validation_fails(phase1_settings):
    retriever = RecordingRetriever([])
    runner = RagWorkflowRunner(
        settings=phase1_settings,
        retriever=retriever,
        prompt_loader=lambda _path: "Answer from context.",
    )

    with pytest.raises(InvalidQueryError):
        runner.answer(question="no", top_k=1)

    assert retriever.calls == []


def test_runner_completes_without_retry_when_context_is_sufficient(phase1_settings):
    retriever = RecordingRetriever(
        [[_chunk("chunk-1", "Provider boundaries keep adapters isolated.", 0.5)]]
    )
    runner = RagWorkflowRunner(
        settings=phase1_settings,
        retriever=retriever,
        prompt_loader=lambda _path: "Answer from context.",
    )

    response = runner.answer(question="What are provider boundaries?", top_k=1)

    assert response.answer
    assert response.citations
    assert response.workflow.status == "completed"
    assert response.workflow.retrieval_attempts == 1
    assert response.workflow.rewritten_query is None
    assert response.workflow.route == [
        "validate_query",
        "decide_retrieval",
        "retrieve_context",
        "assess_context",
        "assemble_context",
        "generate_answer",
        "validate_citations",
        "finalize_response",
    ]
    assert len(retriever.calls) == 1


def test_runner_rewrites_once_and_retries_when_first_context_is_insufficient(phase1_settings):
    retriever = RecordingRetriever(
        [
            [],
            [_chunk("chunk-1", "Provider boundaries keep adapters isolated.", 0.5)],
        ]
    )
    runner = RagWorkflowRunner(
        settings=phase1_settings,
        retriever=retriever,
        prompt_loader=lambda _path: "Answer from context.",
    )

    response = runner.answer(
        question="What does Prisma mean by provider boundaries?",
        top_k=1,
    )

    assert response.workflow.status == "completed"
    assert response.workflow.retrieval_attempts == 2
    assert response.workflow.max_retrieval_attempts == 2
    assert response.workflow.rewritten_query == "prisma provider boundaries"
    assert retriever.calls == [
        "What does Prisma mean by provider boundaries?",
        "prisma provider boundaries",
    ]


def test_runner_returns_no_context_after_one_retry(phase1_settings):
    retriever = RecordingRetriever([[], []])
    runner = RagWorkflowRunner(
        settings=phase1_settings,
        retriever=retriever,
        prompt_loader=lambda _path: "Answer from context.",
    )

    with pytest.raises(NoContextError):
        runner.answer(
            question="What does Prisma mean by provider boundaries?",
            top_k=1,
        )

    assert retriever.calls == [
        "What does Prisma mean by provider boundaries?",
        "prisma provider boundaries",
    ]


@dataclass
class RecordingRetriever:
    results: list[list[RetrievedChunk]]
    calls: list[str] = field(default_factory=list)

    def __call__(
        self,
        _settings: PrismaSettings,
        question: str,
        _top_k: int,
    ) -> list[RetrievedChunk]:
        self.calls.append(question)
        if not self.results:
            return []
        return self.results.pop(0)


def _chunk(chunk_id: str, text: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id="doc-1",
        chunk_index=0,
        source_path="datasets/sample_corpus/provider-boundaries.md",
        source_document="Provider Boundaries",
        score=score,
        text=text,
        payload={},
    )
