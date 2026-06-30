"""Baseline RAG API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.config import PrismaSettings, load_settings
from app.generation.service import RagService
from app.models.rag import QueryRequest, QueryResponse

router = APIRouter()


def get_settings() -> PrismaSettings:
    """Load application settings for request handling."""

    return load_settings()


def get_rag_service(
    settings: Annotated[PrismaSettings, Depends(get_settings)],
) -> RagService:
    """Construct the RAG service."""

    return RagService(settings=settings)


@router.post("/query", response_model=QueryResponse)
def query(
    request: QueryRequest,
    service: Annotated[RagService, Depends(get_rag_service)],
) -> QueryResponse:
    """Answer a question from the local indexed corpus."""

    return service.answer(
        question=request.question,
        top_k=request.top_k,
        max_context_chars=request.max_context_chars,
    )
