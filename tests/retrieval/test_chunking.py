from __future__ import annotations

from app.retrieval.chunking import chunk_document
from app.retrieval.documents import load_documents


def test_chunking_is_deterministic(phase1_settings):
    document = load_documents(phase1_settings.corpus_path, phase1_settings.repo_root)[0]

    first = chunk_document(
        document,
        chunk_size_chars=phase1_settings.retrieval.chunk_size_chars,
        chunk_overlap_chars=phase1_settings.retrieval.chunk_overlap_chars,
    )
    second = chunk_document(
        document,
        chunk_size_chars=phase1_settings.retrieval.chunk_size_chars,
        chunk_overlap_chars=phase1_settings.retrieval.chunk_overlap_chars,
    )

    assert first == second
    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]


def test_chunking_respects_size_and_overlap_bounds(phase1_settings):
    document = load_documents(phase1_settings.corpus_path, phase1_settings.repo_root)[0]
    chunks = chunk_document(document, chunk_size_chars=300, chunk_overlap_chars=50)

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 300 for chunk in chunks)
    assert all(chunk.start_char < chunk.end_char for chunk in chunks)
    assert all(
        chunks[index].start_char <= chunks[index - 1].end_char for index in range(1, len(chunks))
    )
