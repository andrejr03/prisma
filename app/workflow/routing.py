"""Deterministic workflow routing helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.retrieval.search import RetrievedChunk

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "do",
    "does",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "mean",
    "of",
    "or",
    "that",
    "the",
    "to",
    "what",
    "when",
    "where",
    "why",
    "with",
}


@dataclass(frozen=True)
class ContextAssessment:
    """Deterministic context sufficiency result."""

    sufficient: bool
    eligible_chunks: list[RetrievedChunk]
    reason: str


def rewrite_query(question: str) -> str | None:
    """Rewrite a query deterministically for the single retry path."""

    tokens = [
        token
        for token in _TOKEN_RE.findall(question.lower())
        if token not in _STOPWORDS and len(token) > 1
    ]
    deduplicated: list[str] = []
    for token in tokens:
        if token not in deduplicated:
            deduplicated.append(token)

    rewritten = " ".join(deduplicated)
    active = " ".join(_TOKEN_RE.findall(question.lower()))
    if not rewritten or rewritten == active:
        return None
    return rewritten


def assess_context(
    chunks: list[RetrievedChunk],
    *,
    query: str,
    min_context_score: float,
    require_context_token_overlap: bool,
) -> ContextAssessment:
    """Assess retrieved context using deterministic local rules."""

    if not chunks:
        return ContextAssessment(sufficient=False, eligible_chunks=[], reason="no_chunks")

    score_eligible = [chunk for chunk in chunks if chunk.score >= min_context_score]
    if not score_eligible:
        return ContextAssessment(sufficient=False, eligible_chunks=[], reason="score_below_minimum")

    text_eligible = [chunk for chunk in score_eligible if chunk.text.strip()]
    if not text_eligible:
        return ContextAssessment(sufficient=False, eligible_chunks=[], reason="empty_text")

    if not require_context_token_overlap:
        return ContextAssessment(
            sufficient=True,
            eligible_chunks=text_eligible,
            reason="sufficient",
        )

    query_terms = query_tokens(query)
    if not query_terms:
        return ContextAssessment(sufficient=False, eligible_chunks=[], reason="empty_query_terms")

    overlap_eligible = [
        chunk for chunk in text_eligible if not query_terms.isdisjoint(tokenize(chunk.text))
    ]
    if not overlap_eligible:
        return ContextAssessment(sufficient=False, eligible_chunks=[], reason="no_token_overlap")

    return ContextAssessment(sufficient=True, eligible_chunks=overlap_eligible, reason="sufficient")


def query_tokens(text: str) -> set[str]:
    """Tokenize query text and remove routing stopwords."""

    tokens = {token for token in tokenize(text) if token not in _STOPWORDS and len(token) > 1}
    return tokens or tokenize(text)


def tokenize(text: str) -> set[str]:
    """Tokenize text into lowercase alphanumeric terms."""

    return set(_TOKEN_RE.findall(text.lower()))
