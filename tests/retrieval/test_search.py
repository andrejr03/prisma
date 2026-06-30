from __future__ import annotations

import pytest
from app.retrieval.pipeline import run_indexing
from app.retrieval.search import IndexNotReadyError, retrieve_chunks


def test_retrieve_chunks_returns_required_metadata(phase1_settings):
    run_indexing(phase1_settings)

    chunks = retrieve_chunks(
        phase1_settings,
        question="provider boundaries embedding adapters",
        top_k=2,
    )

    assert chunks
    assert len(chunks) <= 2
    assert chunks[0].source_path == "datasets/sample_corpus/provider-boundaries.md"
    assert chunks[0].source_document == "Provider Boundaries"
    assert chunks[0].chunk_id
    assert chunks[0].document_id
    assert chunks[0].text


def test_retrieve_chunks_is_deterministic_for_repeated_query(phase1_settings):
    run_indexing(phase1_settings)

    first = retrieve_chunks(
        phase1_settings,
        question="provider boundaries embedding adapters",
        top_k=4,
    )
    second = retrieve_chunks(
        phase1_settings,
        question="provider boundaries embedding adapters",
        top_k=4,
    )

    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]


def test_retrieve_chunks_raises_when_index_is_missing(phase1_settings):
    with pytest.raises(IndexNotReadyError):
        retrieve_chunks(
            phase1_settings,
            question="provider boundaries",
            top_k=1,
        )
