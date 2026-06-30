from __future__ import annotations

import json

from app.retrieval.pipeline import run_indexing, search_index


def test_indexing_pipeline_writes_manifest_and_is_idempotent(phase1_settings):
    first = run_indexing(phase1_settings)
    second = run_indexing(phase1_settings)

    assert first.up_to_date is False
    assert second.up_to_date is True
    assert first.document_count == 6
    assert first.chunk_count > 6
    assert phase1_settings.manifest_path.exists()

    manifest = json.loads(phase1_settings.manifest_path.read_text(encoding="utf-8"))
    assert manifest["document_count"] == 6
    assert manifest["chunk_count"] == first.chunk_count
    assert manifest["embedding_model_id"] == "hashing-v1-384"
    assert manifest["index_location"].endswith("qdrant")
    assert len(manifest["source_files"]) == 6


def test_retrieval_smoke_returns_expected_source(phase1_settings):
    run_indexing(phase1_settings)

    results = search_index(phase1_settings, "provider boundaries embedding adapters", limit=1)

    assert results
    assert results[0].source_path == "datasets/sample_corpus/provider-boundaries.md"


def test_force_rebuild_is_not_reported_as_up_to_date(phase1_settings):
    run_indexing(phase1_settings)

    result = run_indexing(phase1_settings, force=True)

    assert result.up_to_date is False
