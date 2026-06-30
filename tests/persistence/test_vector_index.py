from __future__ import annotations

from app.persistence.vector_index import LocalQdrantVectorIndex
from app.providers.embeddings import HashEmbeddingProvider
from app.retrieval.chunking import chunk_document
from app.retrieval.documents import load_documents


def test_local_qdrant_index_recreates_upserts_and_searches(tmp_path, phase1_settings):
    documents = load_documents(phase1_settings.corpus_path, phase1_settings.repo_root)
    provider_document = next(
        document
        for document in documents
        if document.source_path.endswith("provider-boundaries.md")
    )
    chunks = chunk_document(
        provider_document,
        chunk_size_chars=500,
        chunk_overlap_chars=50,
    )
    provider = HashEmbeddingProvider(dimensions=64, model_id="hashing-v1-64")
    vectors = provider.embed_texts([chunk.text for chunk in chunks])

    index = LocalQdrantVectorIndex(
        path=tmp_path / "qdrant",
        collection_name="test_collection",
        dimensions=64,
        distance="cosine",
    )
    try:
        index.recreate_collection()
        index.upsert_chunks(chunks, vectors)

        query_vector = provider.embed_texts(["provider boundaries embedding adapters"])[0]
        results = index.search(query_vector, limit=1)
    finally:
        index.close()

    assert results
    assert results[0].source_path == "datasets/sample_corpus/provider-boundaries.md"
