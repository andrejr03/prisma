from __future__ import annotations

from app.retrieval.search import RetrievedChunk
from app.workflow.routing import assess_context, query_tokens, rewrite_query


def test_rewrite_query_is_deterministic_and_transparent():
    rewritten = rewrite_query("What does Prisma mean by provider boundaries?")

    assert rewritten == "prisma provider boundaries"


def test_rewrite_query_returns_none_for_empty_or_unchanged_rewrite():
    assert rewrite_query("and the or") is None
    assert rewrite_query("provider") is None


def test_query_tokens_remove_stopwords_but_preserve_terms():
    assert query_tokens("What does Prisma mean by provider boundaries?") == {
        "prisma",
        "provider",
        "boundaries",
    }


def test_assess_context_requires_score_text_and_token_overlap():
    sufficient = assess_context(
        [_chunk(score=0.4, text="Provider boundaries keep adapters isolated.")],
        query="provider boundaries",
        min_context_score=0.0,
        require_context_token_overlap=True,
    )
    low_score = assess_context(
        [_chunk(score=-0.1, text="Provider boundaries keep adapters isolated.")],
        query="provider boundaries",
        min_context_score=0.0,
        require_context_token_overlap=True,
    )
    empty_text = assess_context(
        [_chunk(score=0.4, text="  ")],
        query="provider boundaries",
        min_context_score=0.0,
        require_context_token_overlap=True,
    )
    no_overlap = assess_context(
        [_chunk(score=0.4, text="Configuration remains declarative.")],
        query="provider boundaries",
        min_context_score=0.0,
        require_context_token_overlap=True,
    )

    assert sufficient.sufficient is True
    assert sufficient.reason == "sufficient"
    assert low_score.sufficient is False
    assert low_score.reason == "score_below_minimum"
    assert empty_text.sufficient is False
    assert empty_text.reason == "empty_text"
    assert no_overlap.sufficient is False
    assert no_overlap.reason == "no_token_overlap"


def _chunk(*, score: float, text: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="chunk-1",
        document_id="doc-1",
        chunk_index=0,
        source_path="datasets/sample_corpus/provider-boundaries.md",
        source_document="Provider Boundaries",
        score=score,
        text=text,
        payload={},
    )
