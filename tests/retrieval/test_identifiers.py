from __future__ import annotations

from app.retrieval.chunking import chunk_document
from app.retrieval.documents import load_documents
from app.retrieval.identifiers import stable_indexing_fingerprint, stable_point_id


def test_document_and_chunk_ids_are_stable(phase1_settings):
    documents = load_documents(phase1_settings.corpus_path, phase1_settings.repo_root)
    chunks = chunk_document(
        documents[0],
        chunk_size_chars=phase1_settings.retrieval.chunk_size_chars,
        chunk_overlap_chars=phase1_settings.retrieval.chunk_overlap_chars,
    )

    documents_again = load_documents(phase1_settings.corpus_path, phase1_settings.repo_root)
    chunks_again = chunk_document(
        documents_again[0],
        chunk_size_chars=phase1_settings.retrieval.chunk_size_chars,
        chunk_overlap_chars=phase1_settings.retrieval.chunk_overlap_chars,
    )

    assert documents[0].document_id == documents_again[0].document_id
    assert [chunk.chunk_id for chunk in chunks] == [chunk.chunk_id for chunk in chunks_again]
    assert stable_point_id(chunks[0].chunk_id) == stable_point_id(chunks_again[0].chunk_id)


def test_indexing_fingerprint_changes_when_chunk_settings_change():
    first = stable_indexing_fingerprint(
        corpus_hash="abc",
        chunk_size_chars=900,
        chunk_overlap_chars=150,
        embedding_model_id="hashing-v1-384",
        collection_name="prisma_sample_corpus",
    )
    second = stable_indexing_fingerprint(
        corpus_hash="abc",
        chunk_size_chars=901,
        chunk_overlap_chars=150,
        embedding_model_id="hashing-v1-384",
        collection_name="prisma_sample_corpus",
    )

    assert first != second
