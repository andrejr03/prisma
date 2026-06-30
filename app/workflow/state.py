"""Explicit state records for the bounded RAG workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.generation.context import ContextItem
from app.models.rag import Citation, WorkflowMetadata
from app.providers.generation import GenerationResult
from app.retrieval.search import RetrievedChunk

WorkflowStatus = Literal[
    "completed",
    "validation_failed",
    "index_not_ready",
    "no_context",
    "citation_failed",
    "failed",
]
WorkflowEventStatus = Literal["started", "completed", "skipped", "failed"]


@dataclass(frozen=True)
class WorkflowEvent:
    """One request-local workflow event."""

    node: str
    status: WorkflowEventStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowError:
    """One structured workflow error."""

    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowState:
    """Mutable state for one bounded RAG workflow run."""

    original_question: str
    active_query: str
    top_k: int
    max_context_chars: int
    max_retrieval_attempts: int
    retrieval_attempts: int = 0
    retrieved_chunks: list[RetrievedChunk] = field(default_factory=list)
    assembled_context: str = ""
    context_items: list[ContextItem] = field(default_factory=list)
    generation_result: GenerationResult | None = None
    citations: list[Citation] = field(default_factory=list)
    errors: list[WorkflowError] = field(default_factory=list)
    workflow_events: list[WorkflowEvent] = field(default_factory=list)
    rewritten_query: str | None = None
    context_sufficient: bool = False
    final_status: WorkflowStatus = "failed"

    @classmethod
    def from_request(
        cls,
        *,
        question: str,
        top_k: int,
        max_context_chars: int,
        max_retrieval_attempts: int,
    ) -> WorkflowState:
        trimmed_question = question.strip()
        return cls(
            original_question=trimmed_question,
            active_query=trimmed_question,
            top_k=top_k,
            max_context_chars=max_context_chars,
            max_retrieval_attempts=max_retrieval_attempts,
        )

    def record_event(
        self,
        *,
        node: str,
        status: WorkflowEventStatus,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.workflow_events.append(
            WorkflowEvent(
                node=node,
                status=status,
                message=message,
                details=details or {},
            )
        )

    def record_error(
        self,
        *,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.errors.append(
            WorkflowError(
                code=code,
                message=message,
                details=details or {},
            )
        )

    def route(self) -> list[str]:
        return [event.node for event in self.workflow_events if event.status == "completed"]

    def metadata(self) -> WorkflowMetadata:
        return WorkflowMetadata(
            status=self.final_status,
            retrieval_attempts=self.retrieval_attempts,
            max_retrieval_attempts=self.max_retrieval_attempts,
            route=self.route(),
            rewritten_query=self.rewritten_query,
            context_sufficient=self.context_sufficient,
        )
