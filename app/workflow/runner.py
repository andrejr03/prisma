"""Bounded RAG workflow runner."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.config import PrismaSettings
from app.generation.context import assemble_context
from app.generation.service import (
    CitationValidationError,
    InvalidQueryError,
    NoContextError,
    _citations_for,
    _load_prompt,
    _retrieved_context_items,
    _validate_citations,
)
from app.models.rag import QueryResponse, ResponseMetadata
from app.providers.generation import (
    GenerationProvider,
    GenerationRequest,
    create_generation_provider,
)
from app.retrieval.search import IndexNotReadyError, RetrievedChunk, retrieve_chunks
from app.workflow.routing import assess_context, rewrite_query
from app.workflow.state import WorkflowState

ChunkRetriever = Callable[[PrismaSettings, str, int], list[RetrievedChunk]]
PromptLoader = Callable[[Path], str]

_VALIDATE_QUERY = "validate_query"
_DECIDE_RETRIEVAL = "decide_retrieval"
_RETRIEVE_CONTEXT = "retrieve_context"
_ASSESS_CONTEXT = "assess_context"
_REWRITE_QUERY = "rewrite_query"
_ASSEMBLE_CONTEXT = "assemble_context"
_GENERATE_ANSWER = "generate_answer"
_VALIDATE_CITATIONS = "validate_citations"
_FINALIZE_RESPONSE = "finalize_response"


@dataclass(frozen=True)
class RagWorkflowRunner:
    """Run the Phase 3 bounded RAG workflow."""

    settings: PrismaSettings
    generation_provider: GenerationProvider | None = None
    retriever: ChunkRetriever | None = None
    prompt_loader: PromptLoader = _load_prompt

    def answer(
        self,
        *,
        question: str,
        top_k: int | None = None,
        max_context_chars: int | None = None,
    ) -> QueryResponse:
        resolved_top_k = top_k if top_k is not None else self.settings.rag.default_top_k
        resolved_context_chars = (
            max_context_chars
            if max_context_chars is not None
            else self.settings.rag.max_context_chars
        )
        state = WorkflowState.from_request(
            question=question,
            top_k=resolved_top_k,
            max_context_chars=resolved_context_chars,
            max_retrieval_attempts=self.settings.workflow.max_retrieval_attempts,
        )

        self._validate_query(state)
        self._decide_retrieval(state)
        self._retrieve_until_sufficient(state)
        self._assemble_context(state)
        self._generate_answer(state)
        cited_ids = self._validate_citations(state)
        return self._finalize_response(state, cited_ids)

    def _validate_query(self, state: WorkflowState) -> None:
        try:
            _validate_request(
                settings=self.settings,
                question=state.original_question,
                top_k=state.top_k,
                max_context_chars=state.max_context_chars,
            )
        except InvalidQueryError as exc:
            state.final_status = "validation_failed"
            state.record_event(
                node=_VALIDATE_QUERY,
                status="failed",
                message=str(exc),
                details=exc.details,
            )
            state.record_error(
                code="invalid_request",
                message=str(exc),
                details=exc.details,
            )
            raise

        state.record_event(
            node=_VALIDATE_QUERY,
            status="completed",
            message="Query validated.",
        )

    def _decide_retrieval(self, state: WorkflowState) -> None:
        state.record_event(
            node=_DECIDE_RETRIEVAL,
            status="completed",
            message="Grounded retrieval required.",
        )

    def _retrieve_until_sufficient(self, state: WorkflowState) -> None:
        while state.retrieval_attempts < state.max_retrieval_attempts:
            self._retrieve_context(state)
            if self._assess_context(state):
                return

            if not self._can_rewrite(state):
                state.final_status = "no_context"
                raise NoContextError("No sufficient context was retrieved for the question.")

            rewritten = rewrite_query(state.original_question)
            if rewritten is None or rewritten == state.active_query:
                state.final_status = "no_context"
                state.record_event(
                    node=_REWRITE_QUERY,
                    status="skipped",
                    message="Query rewrite did not produce a retry query.",
                )
                raise NoContextError("No sufficient context was retrieved for the question.")

            state.rewritten_query = rewritten
            state.active_query = rewritten
            state.record_event(
                node=_REWRITE_QUERY,
                status="completed",
                message="Query rewritten for one retry.",
                details={"rewritten_query": rewritten},
            )

        state.final_status = "no_context"
        raise NoContextError("No sufficient context was retrieved for the question.")

    def _retrieve_context(self, state: WorkflowState) -> None:
        state.retrieval_attempts += 1
        try:
            retriever = self.retriever or _retrieve_chunks
            state.retrieved_chunks = retriever(
                self.settings,
                state.active_query,
                state.top_k,
            )
        except IndexNotReadyError:
            state.final_status = "index_not_ready"
            state.record_event(
                node=_RETRIEVE_CONTEXT,
                status="failed",
                message="Local index is not ready.",
                details={"retrieval_attempts": state.retrieval_attempts},
            )
            raise

        state.record_event(
            node=_RETRIEVE_CONTEXT,
            status="completed",
            message="Context retrieved.",
            details={
                "retrieval_attempts": state.retrieval_attempts,
                "chunk_count": len(state.retrieved_chunks),
            },
        )

    def _assess_context(self, state: WorkflowState) -> bool:
        assessment = assess_context(
            state.retrieved_chunks,
            query=state.active_query,
            min_context_score=self.settings.workflow.min_context_score,
            require_context_token_overlap=self.settings.workflow.require_context_token_overlap,
        )
        state.context_sufficient = assessment.sufficient
        if assessment.sufficient:
            state.retrieved_chunks = assessment.eligible_chunks
        state.record_event(
            node=_ASSESS_CONTEXT,
            status="completed",
            message="Context sufficiency assessed.",
            details={
                "context_sufficient": assessment.sufficient,
                "reason": assessment.reason,
                "eligible_chunk_count": len(assessment.eligible_chunks),
            },
        )
        return assessment.sufficient

    def _can_rewrite(self, state: WorkflowState) -> bool:
        return (
            self.settings.workflow.enable_query_rewrite
            and state.retrieval_attempts < state.max_retrieval_attempts
        )

    def _assemble_context(self, state: WorkflowState) -> None:
        assembled = assemble_context(
            state.retrieved_chunks,
            max_context_chars=state.max_context_chars,
        )
        if not assembled.items:
            state.final_status = "no_context"
            state.record_event(
                node=_ASSEMBLE_CONTEXT,
                status="failed",
                message="No context was available after assembly.",
            )
            raise NoContextError("No context was available after assembly.")

        state.assembled_context = assembled.context
        state.context_items = assembled.items
        state.record_event(
            node=_ASSEMBLE_CONTEXT,
            status="completed",
            message="Context assembled.",
            details={"context_item_count": len(state.context_items)},
        )

    def _generate_answer(self, state: WorkflowState) -> None:
        provider = self._generation_provider()
        state.generation_result = provider.generate(
            GenerationRequest(
                question=state.original_question,
                prompt=self.prompt_loader(self.settings.prompt_path),
                context=state.assembled_context,
                context_items=state.context_items,
                max_answer_sentences=self.settings.rag.max_answer_sentences,
            )
        )
        state.record_event(
            node=_GENERATE_ANSWER,
            status="completed",
            message="Answer generated.",
            details={"generation_model_id": state.generation_result.model_id},
        )

    def _validate_citations(self, state: WorkflowState) -> list[int]:
        if state.generation_result is None:
            state.final_status = "citation_failed"
            raise CitationValidationError("Generation result is missing.")

        try:
            cited_ids = _validate_citations(
                answer=state.generation_result.answer,
                cited_context_ids=state.generation_result.cited_context_ids,
                context_items=state.context_items,
            )
        except CitationValidationError as exc:
            state.final_status = "citation_failed"
            state.record_event(
                node=_VALIDATE_CITATIONS,
                status="failed",
                message=str(exc),
            )
            state.record_error(code="invalid_citations", message=str(exc))
            raise

        state.citations = _citations_for(state.context_items, cited_ids)
        state.record_event(
            node=_VALIDATE_CITATIONS,
            status="completed",
            message="Citations validated.",
            details={"citation_count": len(state.citations)},
        )
        return cited_ids

    def _finalize_response(self, state: WorkflowState, cited_ids: list[int]) -> QueryResponse:
        if state.generation_result is None:
            state.final_status = "failed"
            raise RuntimeError("Generation result is missing.")

        state.final_status = "completed"
        state.record_event(
            node=_FINALIZE_RESPONSE,
            status="completed",
            message="Response finalized.",
        )
        return QueryResponse(
            answer=state.generation_result.answer,
            citations=_citations_for(state.context_items, cited_ids),
            retrieved_context=_retrieved_context_items(state.context_items),
            metadata=ResponseMetadata(
                retrieval_top_k=state.top_k,
                context_item_count=len(state.context_items),
                generation_backend=self.settings.generation.backend,
                generation_model_id=state.generation_result.model_id,
            ),
            workflow=state.metadata(),
        )

    def _generation_provider(self) -> GenerationProvider:
        if self.generation_provider is not None:
            return self.generation_provider
        return create_generation_provider(
            backend=self.settings.generation.backend,
            model_id=self.settings.generation.model_id,
        )


def _retrieve_chunks(
    settings: PrismaSettings,
    question: str,
    top_k: int,
) -> list[RetrievedChunk]:
    return retrieve_chunks(settings, question=question, top_k=top_k)


def _validate_request(
    *,
    settings: PrismaSettings,
    question: str,
    top_k: int,
    max_context_chars: int,
) -> None:
    if len(question) < settings.rag.min_question_chars:
        raise InvalidQueryError(
            "Question is too short.",
            details={"min_question_chars": settings.rag.min_question_chars},
        )
    if len(question) > settings.rag.max_question_chars:
        raise InvalidQueryError(
            "Question is too long.",
            details={"max_question_chars": settings.rag.max_question_chars},
        )
    if top_k < 1 or top_k > settings.rag.max_top_k:
        raise InvalidQueryError(
            "top_k is outside the configured bounds.",
            details={"min_top_k": 1, "max_top_k": settings.rag.max_top_k},
        )
    if max_context_chars < 500:
        raise InvalidQueryError(
            "max_context_chars is too small.",
            details={"min_context_chars": 500},
        )
    if max_context_chars > settings.rag.max_context_chars_hard_limit:
        raise InvalidQueryError(
            "max_context_chars exceeds the configured hard limit.",
            details={
                "max_context_chars_hard_limit": settings.rag.max_context_chars_hard_limit,
            },
        )
