"""Stable identifiers for corpus, documents, chunks, and vector points."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Iterable


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_document_id(*, corpus_id: str, source_path: str, content_hash: str) -> str:
    return sha256_text(f"document:v1\n{corpus_id}\n{source_path}\n{content_hash}")


def stable_chunk_id(*, document_id: str, chunk_index: int, text_hash: str) -> str:
    return sha256_text(f"chunk:v1\n{document_id}\n{chunk_index}\n{text_hash}")


def stable_point_id(chunk_id: str) -> str:
    digest = hashlib.sha256(f"point:v1\n{chunk_id}".encode()).digest()
    return str(uuid.UUID(bytes=digest[:16]))


def stable_corpus_hash(source_files: Iterable[tuple[str, str]]) -> str:
    lines = [f"{path}\t{content_hash}" for path, content_hash in sorted(source_files)]
    return sha256_text("corpus:v1\n" + "\n".join(lines))


def stable_indexing_fingerprint(
    *,
    corpus_hash: str,
    chunk_size_chars: int,
    chunk_overlap_chars: int,
    embedding_model_id: str,
    collection_name: str,
) -> str:
    payload = {
        "chunk_overlap_chars": chunk_overlap_chars,
        "chunk_size_chars": chunk_size_chars,
        "collection_name": collection_name,
        "corpus_hash": corpus_hash,
        "embedding_model_id": embedding_model_id,
    }
    return sha256_text("index:v1\n" + json.dumps(payload, sort_keys=True, separators=(",", ":")))
