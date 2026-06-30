"""Indexing pipeline orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from app.config import PrismaSettings
from app.persistence.vector_index import LocalQdrantVectorIndex, SearchResult
from app.providers.embeddings import create_embedding_provider
from app.retrieval.chunking import Chunk, chunk_documents
from app.retrieval.documents import Document, load_documents
from app.retrieval.identifiers import stable_corpus_hash, stable_indexing_fingerprint


@dataclass(frozen=True)
class IndexingResult:
    document_count: int
    chunk_count: int
    collection_name: str
    manifest_path: Path
    index_path: Path
    up_to_date: bool
    fingerprint: str


def run_indexing(settings: PrismaSettings, *, force: bool = False) -> IndexingResult:
    documents = load_documents(settings.corpus_path, settings.repo_root)
    chunks = chunk_documents(
        documents,
        chunk_size_chars=settings.retrieval.chunk_size_chars,
        chunk_overlap_chars=settings.retrieval.chunk_overlap_chars,
    )
    corpus_hash = stable_corpus_hash(
        (document.source_path, document.content_hash) for document in documents
    )
    fingerprint = stable_indexing_fingerprint(
        corpus_hash=corpus_hash,
        chunk_size_chars=settings.retrieval.chunk_size_chars,
        chunk_overlap_chars=settings.retrieval.chunk_overlap_chars,
        embedding_model_id=settings.embeddings.model_id,
        collection_name=settings.vector_index.collection_name,
    )

    vector_index = LocalQdrantVectorIndex(
        path=settings.index_path,
        collection_name=settings.vector_index.collection_name,
        dimensions=settings.embeddings.dimensions,
        distance=settings.vector_index.distance,
    )
    try:
        if not force and _is_up_to_date(
            manifest_path=settings.manifest_path,
            fingerprint=fingerprint,
            vector_index=vector_index,
        ):
            return IndexingResult(
                document_count=len(documents),
                chunk_count=len(chunks),
                collection_name=settings.vector_index.collection_name,
                manifest_path=settings.manifest_path,
                index_path=settings.index_path,
                up_to_date=True,
                fingerprint=fingerprint,
            )

        provider = create_embedding_provider(
            backend=settings.embeddings.backend,
            dimensions=settings.embeddings.dimensions,
            model_id=settings.embeddings.model_id,
        )
        vectors = provider.embed_texts([chunk.text for chunk in chunks])

        vector_index.recreate_collection()
        vector_index.upsert_chunks(chunks, vectors)

        manifest = build_manifest(
            settings=settings,
            documents=documents,
            chunks=chunks,
            corpus_hash=corpus_hash,
            fingerprint=fingerprint,
        )
        write_manifest(settings.manifest_path, manifest)

        return IndexingResult(
            document_count=len(documents),
            chunk_count=len(chunks),
            collection_name=settings.vector_index.collection_name,
            manifest_path=settings.manifest_path,
            index_path=settings.index_path,
            up_to_date=False,
            fingerprint=fingerprint,
        )
    finally:
        vector_index.close()


def search_index(
    settings: PrismaSettings,
    query: str,
    *,
    limit: int = 5,
) -> list[SearchResult]:
    provider = create_embedding_provider(
        backend=settings.embeddings.backend,
        dimensions=settings.embeddings.dimensions,
        model_id=settings.embeddings.model_id,
    )
    vector = provider.embed_texts([query])[0]
    vector_index = LocalQdrantVectorIndex(
        path=settings.index_path,
        collection_name=settings.vector_index.collection_name,
        dimensions=settings.embeddings.dimensions,
        distance=settings.vector_index.distance,
    )
    try:
        return vector_index.search(vector, limit=limit)
    finally:
        vector_index.close()


def build_manifest(
    *,
    settings: PrismaSettings,
    documents: list[Document],
    chunks: list[Chunk],
    corpus_hash: str,
    fingerprint: str,
) -> dict[str, Any]:
    corpus_id = documents[0].corpus_id if documents else ""
    return {
        "schema_version": 1,
        "corpus_id": corpus_id,
        "corpus_hash": corpus_hash,
        "indexing_fingerprint": fingerprint,
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "chunk_size_chars": settings.retrieval.chunk_size_chars,
        "chunk_overlap_chars": settings.retrieval.chunk_overlap_chars,
        "embedding_backend": settings.embeddings.backend,
        "embedding_model_id": settings.embeddings.model_id,
        "embedding_dimensions": settings.embeddings.dimensions,
        "vector_store": settings.vector_index.backend,
        "collection_name": settings.vector_index.collection_name,
        "index_location": _display_path(settings.index_path, settings.repo_root),
        "manifest_path": _display_path(settings.manifest_path, settings.repo_root),
        "created_timestamp": (
            datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        ),
        "source_files": [
            {
                "path": document.source_path,
                "sha256": document.content_hash,
                "document_id": document.document_id,
            }
            for document in documents
        ],
    }


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp_path.replace(path)


def _is_up_to_date(
    *,
    manifest_path: Path,
    fingerprint: str,
    vector_index: LocalQdrantVectorIndex,
) -> bool:
    manifest = _read_manifest(manifest_path)
    if manifest is None:
        return False
    return manifest.get("indexing_fingerprint") == fingerprint and vector_index.collection_exists()


def _read_manifest(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Index manifest must contain an object: {path}")
    return cast(dict[str, Any], value)


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()
