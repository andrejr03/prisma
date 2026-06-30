"""Baseline RAG service orchestration."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import PrismaSettings
from app.generation.context import ContextItem, assemble_context
from app.models.rag import Citation, QueryResponse, ResponseMetadata, RetrievedContextItem
from app.providers.generation import (
    GenerationProvider,
    GenerationRequest,
    create_generation_provider,
)
from app.retrieval.search import retrieve_chunks

_CITATION_MARKER_RE = re.compile(r"\[(\d+)]")


class InvalidQueryError(ValueError):
    """Raised when a request passes JSON validation but violates configured limits."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class NoContextError(RuntimeError):
    """Raised when retrieval completes but no usable context is available."""


class CitationValidationError(RuntimeError):
    """Raised when generation returns missing or unsupported citations."""


@dataclass(frozen=True)
class RagService:
    """Retrieve, assemble, generate, validate, and shape a RAG response."""

    settings: PrismaSettings
    generation_provider: GenerationProvider | None = None

    def answer(
        self,
        *,
        question: str,
        top_k: int | None = None,
        max_context_chars: int | None = None,
    ) -> QueryResponse:
        question = question.strip()
        resolved_top_k = top_k if top_k is not None else self.settings.rag.default_top_k
        resolved_context_chars = (
            max_context_chars
            if max_context_chars is not None
            else self.settings.rag.max_context_chars
        )
        self._validate_request(
            question=question,
            top_k=resolved_top_k,
            max_context_chars=resolved_context_chars,
        )

        chunks = retrieve_chunks(self.settings, question=question, top_k=resolved_top_k)
        if not chunks:
            raise NoContextError("No context was retrieved for the question.")

        assembled = assemble_context(chunks, max_context_chars=resolved_context_chars)
        if not assembled.items:
            raise NoContextError("No context was available after assembly.")

        provider = self._generation_provider()
        result = provider.generate(
            GenerationRequest(
                question=question,
                prompt=_load_prompt(self.settings.prompt_path),
                context=assembled.context,
                context_items=assembled.items,
                max_answer_sentences=self.settings.rag.max_answer_sentences,
            )
        )
        cited_ids = _validate_citations(
            answer=result.answer,
            cited_context_ids=result.cited_context_ids,
            context_items=assembled.items,
        )

        return QueryResponse(
            answer=result.answer,
            citations=_citations_for(assembled.items, cited_ids),
            retrieved_context=_retrieved_context_items(assembled.items),
            metadata=ResponseMetadata(
                retrieval_top_k=resolved_top_k,
                context_item_count=len(assembled.items),
                generation_backend=self.settings.generation.backend,
                generation_model_id=result.model_id,
            ),
        )

    def _validate_request(
        self,
        *,
        question: str,
        top_k: int,
        max_context_chars: int,
    ) -> None:
        if len(question) < self.settings.rag.min_question_chars:
            raise InvalidQueryError(
                "Question is too short.",
                details={"min_question_chars": self.settings.rag.min_question_chars},
            )
        if len(question) > self.settings.rag.max_question_chars:
            raise InvalidQueryError(
                "Question is too long.",
                details={"max_question_chars": self.settings.rag.max_question_chars},
            )
        if top_k < 1 or top_k > self.settings.rag.max_top_k:
            raise InvalidQueryError(
                "top_k is outside the configured bounds.",
                details={"min_top_k": 1, "max_top_k": self.settings.rag.max_top_k},
            )
        if max_context_chars < 500:
            raise InvalidQueryError(
                "max_context_chars is too small.",
                details={"min_context_chars": 500},
            )
        if max_context_chars > self.settings.rag.max_context_chars_hard_limit:
            raise InvalidQueryError(
                "max_context_chars exceeds the configured hard limit.",
                details={
                    "max_context_chars_hard_limit": (self.settings.rag.max_context_chars_hard_limit)
                },
            )

    def _generation_provider(self) -> GenerationProvider:
        if self.generation_provider is not None:
            return self.generation_provider
        return create_generation_provider(
            backend=self.settings.generation.backend,
            model_id=self.settings.generation.model_id,
        )


def _load_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _validate_citations(
    *,
    answer: str,
    cited_context_ids: list[int],
    context_items: list[ContextItem],
) -> list[int]:
    valid_ids = {item.citation_id for item in context_items}
    result_ids = set(cited_context_ids)
    marker_ids = {int(value) for value in _CITATION_MARKER_RE.findall(answer)}

    if not result_ids:
        raise CitationValidationError("Generation returned no cited context ids.")
    if not marker_ids:
        raise CitationValidationError("Generation answer contains no citation markers.")
    if result_ids != marker_ids:
        raise CitationValidationError("Generation citations do not match answer markers.")

    invalid_ids = result_ids - valid_ids
    if invalid_ids:
        invalid = ", ".join(str(citation_id) for citation_id in sorted(invalid_ids))
        raise CitationValidationError(f"Generation cited unknown context ids: {invalid}.")

    return _ordered_citation_ids(cited_context_ids)


def _ordered_citation_ids(citation_ids: list[int]) -> list[int]:
    ordered: list[int] = []
    for citation_id in citation_ids:
        if citation_id not in ordered:
            ordered.append(citation_id)
    return ordered


def _citations_for(items: list[ContextItem], citation_ids: list[int]) -> list[Citation]:
    by_id = {item.citation_id: item for item in items}
    return [_citation_for(by_id[citation_id]) for citation_id in citation_ids]


def _citation_for(item: ContextItem) -> Citation:
    return Citation(
        citation_id=item.citation_id,
        source_document=item.source_document,
        source_path=item.source_path,
        chunk_id=item.chunk_id,
        chunk_index=item.chunk_index,
        score=item.score,
    )


def _retrieved_context_items(items: list[ContextItem]) -> list[RetrievedContextItem]:
    return [
        RetrievedContextItem(
            citation_id=item.citation_id,
            chunk_id=item.chunk_id,
            source_document=item.source_document,
            source_path=item.source_path,
            chunk_index=item.chunk_index,
            score=item.score,
            text=item.text,
            truncated=item.truncated,
        )
        for item in items
    ]
