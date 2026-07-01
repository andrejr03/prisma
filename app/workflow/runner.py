"""Bounded RAG workflow runner."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
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
from app.observability.models import RuntimeStage
from app.observability.runtime import RuntimeRecorder
from app.observability.timing import StageSpan
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
    runtime_recorder: RuntimeRecorder | None = None

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

        try:
            self._validate_query(state)
            self._decide_retrieval(state)
            self._retrieve_until_sufficient(state)
            self._assemble_context(state)
            self._generate_answer(state)
            cited_ids = self._validate_citations(state)
            return self._finalize_response(state, cited_ids)
        except Exception:
            self._record_runtime_workflow_state(state)
            raise

    def _validate_query(self, state: WorkflowState) -> None:
        try:
            with self._runtime_stage("validate_query", error_code="invalid_request"):
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
        self._record_runtime_retrieval_attempts(state)
        try:
            retriever = self.retriever or _retrieve_chunks
            with self._runtime_stage("retrieve_context", error_code="index_not_ready") as span:
                state.retrieved_chunks = retriever(
                    self.settings,
                    state.active_query,
                    state.top_k,
                )
                span.set_details(
                    {
                        "attempt": state.retrieval_attempts,
                        "retrieved_count": len(state.retrieved_chunks),
                    }
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
        with self._runtime_stage("assemble_context", error_code="no_context") as span:
            assembled = assemble_context(
                state.retrieved_chunks,
                max_context_chars=state.max_context_chars,
            )
            self._record_runtime_context(assembled.context)
            span.set_details(
                {
                    "context_item_count": len(assembled.items),
                    "context_char_count": len(assembled.context),
                }
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
        with self._runtime_stage("generate_answer") as span:
            prompt = self.prompt_loader(self.settings.prompt_path)
            self._record_runtime_prompt(prompt)
            state.generation_result = provider.generate(
                GenerationRequest(
                    question=state.original_question,
                    prompt=prompt,
                    context=state.assembled_context,
                    context_items=state.context_items,
                    max_answer_sentences=self.settings.rag.max_answer_sentences,
                )
            )
            span.set_details(
                {
                    "generation_backend": self.settings.generation.backend,
                    "generation_model_id": state.generation_result.model_id,
                }
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
            with self._runtime_stage("validate_citations", error_code="invalid_citations") as span:
                cited_ids = _validate_citations(
                    answer=state.generation_result.answer,
                    cited_context_ids=state.generation_result.cited_context_ids,
                    context_items=state.context_items,
                )
                span.set_detail("citation_count", len(cited_ids))
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
        self._record_runtime_workflow_state(state)
        with self._runtime_stage("finalize_response"):
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

    def _runtime_stage(
        self,
        stage: RuntimeStage,
        *,
        error_code: str | None = None,
    ) -> AbstractContextManager[StageSpan]:
        if self.runtime_recorder is None:
            return nullcontext(StageSpan())
        return self.runtime_recorder.stage(stage, error_code=error_code)

    def _record_runtime_context(self, context: str) -> None:
        if self.runtime_recorder is not None:
            self.runtime_recorder.record_context(context=context)

    def _record_runtime_prompt(self, prompt: str) -> None:
        if self.runtime_recorder is not None:
            self.runtime_recorder.record_prompt(prompt=prompt)

    def _record_runtime_retrieval_attempts(self, state: WorkflowState) -> None:
        if self.runtime_recorder is not None:
            self.runtime_recorder.record_retrieval_attempts(state.retrieval_attempts)

    def _record_runtime_workflow_state(self, state: WorkflowState) -> None:
        if self.runtime_recorder is None:
            return
        self.runtime_recorder.record_retrieval_attempts(state.retrieval_attempts)
        self.runtime_recorder.record_workflow_route(state.route())


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
