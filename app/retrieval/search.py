"""Query-facing retrieval over the Phase 1 local vector index."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import PrismaSettings
from app.persistence.vector_index import LocalQdrantVectorIndex
from app.retrieval.pipeline import search_index


class IndexNotReadyError(RuntimeError):
    """Raised when the local vector index is missing or not queryable."""


@dataclass(frozen=True)
class RetrievedChunk:
    """Retrieved chunk plus normalized metadata needed by RAG generation."""

    chunk_id: str
    document_id: str
    chunk_index: int
    source_path: str
    source_document: str
    score: float
    text: str
    payload: dict[str, Any]


def index_is_ready(settings: PrismaSettings) -> bool:
    """Return whether the local index manifest and Qdrant collection are present."""

    if not settings.manifest_path.exists():
        return False

    vector_index = LocalQdrantVectorIndex(
        path=settings.index_path,
        collection_name=settings.vector_index.collection_name,
        dimensions=settings.embeddings.dimensions,
        distance=settings.vector_index.distance,
    )
    try:
        return vector_index.collection_exists()
    except Exception:
        return False
    finally:
        vector_index.close()


def retrieve_chunks(
    settings: PrismaSettings,
    *,
    question: str,
    top_k: int,
) -> list[RetrievedChunk]:
    """Retrieve normalized chunks from the Phase 1 vector index."""

    if not index_is_ready(settings):
        raise IndexNotReadyError("Local index is missing. Run python -m app.retrieval.index.")

    results = search_index(settings, question, limit=top_k)
    chunks = [
        _to_retrieved_chunk(result.payload, score=result.score)
        for result in results
        if result.score >= settings.rag.min_score
    ]
    return sorted(
        chunks,
        key=lambda chunk: (-chunk.score, chunk.source_path, chunk.chunk_index, chunk.chunk_id),
    )[:top_k]


def _to_retrieved_chunk(payload: dict[str, Any], *, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=str(payload["chunk_id"]),
        document_id=str(payload["document_id"]),
        chunk_index=int(payload["chunk_index"]),
        source_path=str(payload["source_path"]),
        source_document=str(payload["title"]),
        score=score,
        text=str(payload["text"]),
        payload=dict(payload),
    )
