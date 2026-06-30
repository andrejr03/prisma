from __future__ import annotations

from app.generation.context import assemble_context
from app.retrieval.search import RetrievedChunk


def test_context_assembly_preserves_order_and_metadata():
    chunks = [
        _chunk("chunk-1", 0, "Provider boundaries keep adapters isolated.", 0.9),
        _chunk("chunk-2", 1, "Configuration stays declarative.", 0.7),
    ]

    assembled = assemble_context(chunks, max_context_chars=1000)

    assert assembled.items[0].citation_id == 1
    assert assembled.items[1].citation_id == 2
    assert assembled.items[0].chunk_id == "chunk-1"
    assert assembled.items[1].chunk_id == "chunk-2"
    assert '\n\n---\n\n[2] title="Provider Boundaries"' in assembled.context


def test_context_assembly_truncates_first_chunk_when_needed():
    text = " ".join(f"word{i}" for i in range(100))

    assembled = assemble_context([_chunk("chunk-1", 0, text, 0.9)], max_context_chars=220)

    assert len(assembled.context) <= 220
    assert assembled.items[0].truncated is True
    assert assembled.items[0].text
    assert assembled.items[0].text != text
    assert assembled.items[0].source_path == "datasets/sample_corpus/provider-boundaries.md"


def test_context_assembly_deduplicates_duplicate_chunk_ids():
    chunks = [
        _chunk("chunk-1", 0, "First copy.", 0.9),
        _chunk("chunk-1", 0, "Second copy.", 0.8),
    ]

    assembled = assemble_context(chunks, max_context_chars=1000)

    assert len(assembled.items) == 1
    assert assembled.items[0].text == "First copy."


def _chunk(chunk_id: str, chunk_index: int, text: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id="doc-1",
        chunk_index=chunk_index,
        source_path="datasets/sample_corpus/provider-boundaries.md",
        source_document="Provider Boundaries",
        score=score,
        text=text,
        payload={},
    )
