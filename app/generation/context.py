"""Deterministic context assembly for baseline RAG."""

from __future__ import annotations

from dataclasses import dataclass

from app.retrieval.search import RetrievedChunk

_SEPARATOR = "\n\n---\n\n"


@dataclass(frozen=True)
class ContextItem:
    """A retrieved chunk assigned to one citation id."""

    citation_id: int
    chunk_id: str
    source_document: str
    source_path: str
    chunk_index: int
    score: float
    text: str
    truncated: bool


@dataclass(frozen=True)
class AssembledContext:
    """Bounded context text plus structured citation metadata."""

    context: str
    items: list[ContextItem]


def assemble_context(
    chunks: list[RetrievedChunk],
    *,
    max_context_chars: int,
) -> AssembledContext:
    """Assemble retrieved chunks into a bounded context string."""

    if max_context_chars <= 0:
        raise ValueError("max_context_chars must be positive")

    blocks: list[str] = []
    items: list[ContextItem] = []
    seen_chunk_ids: set[str] = set()
    current_chars = 0

    for chunk in chunks:
        if chunk.chunk_id in seen_chunk_ids:
            continue

        citation_id = len(items) + 1
        item = _context_item(chunk, citation_id=citation_id, truncated=False)
        block = _format_item(item)
        separator = "" if not blocks else _SEPARATOR

        if current_chars + len(separator) + len(block) <= max_context_chars:
            blocks.append(block)
            items.append(item)
            seen_chunk_ids.add(chunk.chunk_id)
            current_chars += len(separator) + len(block)
            continue

        if blocks:
            break

        truncated_item = _truncate_first_item(item, max_context_chars=max_context_chars)
        blocks.append(_format_item(truncated_item))
        items.append(truncated_item)
        seen_chunk_ids.add(chunk.chunk_id)
        break

    return AssembledContext(context=_SEPARATOR.join(blocks), items=items)


def _context_item(
    chunk: RetrievedChunk,
    *,
    citation_id: int,
    truncated: bool,
) -> ContextItem:
    return ContextItem(
        citation_id=citation_id,
        chunk_id=chunk.chunk_id,
        source_document=chunk.source_document,
        source_path=chunk.source_path,
        chunk_index=chunk.chunk_index,
        score=chunk.score,
        text=chunk.text,
        truncated=truncated,
    )


def _format_item(item: ContextItem) -> str:
    title = item.source_document.replace('"', '\\"')
    source_path = item.source_path.replace('"', '\\"')
    chunk_id = item.chunk_id.replace('"', '\\"')
    return (
        f'[{item.citation_id}] title="{title}" source_path="{source_path}" '
        f'chunk_id="{chunk_id}"\n{item.text}'
    )


def _truncate_first_item(item: ContextItem, *, max_context_chars: int) -> ContextItem:
    header = _format_item(
        ContextItem(
            citation_id=item.citation_id,
            chunk_id=item.chunk_id,
            source_document=item.source_document,
            source_path=item.source_path,
            chunk_index=item.chunk_index,
            score=item.score,
            text="",
            truncated=True,
        )
    )
    available = max_context_chars - len(header)
    if available <= 0:
        text = ""
    else:
        text = _truncate_at_whitespace(item.text, available)
    return ContextItem(
        citation_id=item.citation_id,
        chunk_id=item.chunk_id,
        source_document=item.source_document,
        source_path=item.source_path,
        chunk_index=item.chunk_index,
        score=item.score,
        text=text,
        truncated=True,
    )


def _truncate_at_whitespace(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text

    candidate = text[:max_chars].rstrip()
    boundary = max(candidate.rfind(" "), candidate.rfind("\n"))
    if boundary > 0:
        candidate = candidate[:boundary]
    return candidate.rstrip()
