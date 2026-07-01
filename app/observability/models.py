"""Pydantic models for request-local runtime observability."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RuntimeStage = Literal[
    "request",
    "validate_query",
    "retrieve_context",
    "assemble_context",
    "generate_answer",
    "validate_citations",
    "finalize_response",
]
RuntimeEventStatus = Literal["started", "completed", "skipped", "failed"]
RuntimeScalar = str | int | float | bool


class RuntimeEvent(BaseModel):
    """One structured event recorded during a single request."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    sequence: int = Field(ge=0)
    timestamp: str
    stage: RuntimeStage
    status: RuntimeEventStatus
    duration_ms: float | None = None
    details: dict[str, RuntimeScalar] = Field(default_factory=dict)
    error_code: str | None = None


class RuntimeMetrics(BaseModel):
    """Deterministic per-request runtime metrics derived from recorded events."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    total_latency_ms: float
    retrieval_latency_ms: float
    context_assembly_latency_ms: float
    generation_latency_ms: float
    validation_latency_ms: float
    retrieval_attempts: int
    retrieved_context_count: int
    retrieved_source_paths: list[str]
    citation_count: int
    answer_char_count: int
    generated_answer_sentence_count: int
    context_char_count: int
    prompt_char_count: int
    workflow_route: list[str]
    generation_backend: str
    generation_model_id: str
    status: Literal["completed", "failed"]
    error_code: str | None = None


class RuntimeSummary(BaseModel):
    """Compact inline runtime block for successful query responses."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    total_latency_ms: float
    retrieval_latency_ms: float
    context_assembly_latency_ms: float
    generation_latency_ms: float
    validation_latency_ms: float
    retrieval_attempts: int
    citation_count: int
