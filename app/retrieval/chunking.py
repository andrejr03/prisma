"""Deterministic text chunking."""

from __future__ import annotations

from dataclasses import dataclass

from app.retrieval.documents import Document
from app.retrieval.identifiers import sha256_text, stable_chunk_id


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    chunk_index: int
    source_path: str
    title: str
    license: str
    start_char: int
    end_char: int
    text: str
    text_hash: str

    def payload(self) -> dict[str, str | int]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "source_path": self.source_path,
            "title": self.title,
            "license": self.license,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "text_hash": self.text_hash,
            "text": self.text,
        }


def chunk_document(
    document: Document,
    *,
    chunk_size_chars: int,
    chunk_overlap_chars: int,
) -> list[Chunk]:
    if chunk_size_chars <= 0:
        raise ValueError("chunk_size_chars must be positive")
    if chunk_overlap_chars < 0:
        raise ValueError("chunk_overlap_chars must be non-negative")
    if chunk_overlap_chars >= chunk_size_chars:
        raise ValueError("chunk_overlap_chars must be smaller than chunk_size_chars")

    text = document.normalized_text
    chunks: list[Chunk] = []
    start = 0

    while start < len(text):
        end = _choose_end(text, start, chunk_size_chars)
        trimmed_start, trimmed_end = _trim_offsets(text, start, end)
        if trimmed_start >= trimmed_end:
            break

        chunk_text = text[trimmed_start:trimmed_end]
        text_hash = sha256_text(chunk_text)
        chunk_index = len(chunks)
        chunks.append(
            Chunk(
                chunk_id=stable_chunk_id(
                    document_id=document.document_id,
                    chunk_index=chunk_index,
                    text_hash=text_hash,
                ),
                document_id=document.document_id,
                chunk_index=chunk_index,
                source_path=document.source_path,
                title=document.title,
                license=document.license,
                start_char=trimmed_start,
                end_char=trimmed_end,
                text=chunk_text,
                text_hash=text_hash,
            )
        )

        if end >= len(text):
            break
        start = max(end - chunk_overlap_chars, start + 1)

    return chunks


def chunk_documents(
    documents: list[Document],
    *,
    chunk_size_chars: int,
    chunk_overlap_chars: int,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for document in documents:
        chunks.extend(
            chunk_document(
                document,
                chunk_size_chars=chunk_size_chars,
                chunk_overlap_chars=chunk_overlap_chars,
            )
        )
    return chunks


def _choose_end(text: str, start: int, chunk_size_chars: int) -> int:
    limit = min(start + chunk_size_chars, len(text))
    if limit == len(text):
        return limit

    window = text[start:limit]
    min_break = max(1, chunk_size_chars // 2)
    paragraph_break = window.rfind("\n\n")
    if paragraph_break >= min_break:
        return start + paragraph_break

    whitespace = max(window.rfind(" "), window.rfind("\n"))
    if whitespace >= min_break:
        return start + whitespace

    return limit


def _trim_offsets(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end
