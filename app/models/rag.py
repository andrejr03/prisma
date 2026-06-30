"""Pydantic models for the baseline RAG API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QueryRequest(BaseModel):
    """Request body for POST /query."""

    model_config = ConfigDict(extra="forbid")

    question: str
    top_k: int | None = Field(default=None, ge=1)
    max_context_chars: int | None = Field(default=None, ge=500)

    @field_validator("question", mode="before")
    @classmethod
    def trim_question(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("question must be a string")
        return value.strip()


class Citation(BaseModel):
    """Citation metadata tied to one retrieved context item."""

    citation_id: int
    source_document: str
    source_path: str
    chunk_id: str
    chunk_index: int
    score: float


class RetrievedContextItem(BaseModel):
    """Context item returned for transparency in API responses."""

    citation_id: int
    chunk_id: str
    source_document: str
    source_path: str
    chunk_index: int
    score: float
    text: str
    truncated: bool


class ResponseMetadata(BaseModel):
    """Execution metadata for a RAG response."""

    retrieval_top_k: int
    context_item_count: int
    generation_backend: str
    generation_model_id: str


class WorkflowMetadata(BaseModel):
    """Request-local workflow execution metadata."""

    status: str
    retrieval_attempts: int
    max_retrieval_attempts: int
    route: list[str]
    rewritten_query: str | None
    context_sufficient: bool


class QueryResponse(BaseModel):
    """Successful POST /query response."""

    answer: str
    citations: list[Citation]
    retrieved_context: list[RetrievedContextItem]
    metadata: ResponseMetadata
    workflow: WorkflowMetadata


class ErrorBody(BaseModel):
    """Structured API error body."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Structured API error response."""

    error: ErrorBody
