from __future__ import annotations

from app.providers.embeddings import HashEmbeddingProvider


def test_hash_embeddings_are_deterministic_with_configured_dimension():
    provider = HashEmbeddingProvider(dimensions=384, model_id="hashing-v1-384")

    first = provider.embed_texts(["provider boundaries embedding adapters"])[0]
    second = provider.embed_texts(["provider boundaries embedding adapters"])[0]

    assert first == second
    assert len(first) == 384
    assert sum(value * value for value in first) == 1.0


def test_empty_text_embedding_is_zero_vector():
    provider = HashEmbeddingProvider(dimensions=8, model_id="hashing-v1-8")

    assert provider.embed_texts([""])[0] == [0.0] * 8
