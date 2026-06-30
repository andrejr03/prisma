"""Provider-neutral generation boundary and deterministic local backend."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from app.generation.context import ContextItem

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")
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


class UnsupportedGenerationBackendError(ValueError):
    """Raised when the configured generation backend is not supported."""


@dataclass(frozen=True)
class GenerationRequest:
    """Request sent through the generation boundary."""

    question: str
    prompt: str
    context: str
    context_items: list[ContextItem]
    max_answer_sentences: int


@dataclass(frozen=True)
class GenerationResult:
    """Result returned by a generation provider."""

    answer: str
    cited_context_ids: list[int]
    model_id: str


class GenerationProvider(Protocol):
    """Provider-neutral generation protocol."""

    @property
    def model_id(self) -> str:
        """Stable generation model identifier."""

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate an answer from supplied context only."""


@dataclass(frozen=True)
class LocalGroundedGenerationProvider:
    """Deterministic local backend that answers only from supplied context."""

    model_id: str = "local-grounded-v1"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        terms = _question_terms(request.question)
        selected: list[tuple[str, int]] = []

        for item in request.context_items:
            for sentence in _sentences(item.text):
                if terms and terms.isdisjoint(_tokens(sentence)):
                    continue
                selected.append((_with_citation(sentence, item.citation_id), item.citation_id))
                break
            if len(selected) >= request.max_answer_sentences:
                break

        if not selected:
            item = request.context_items[0]
            sentence = _sentences(item.text)[0] if _sentences(item.text) else item.text
            if not sentence:
                sentence = "The supplied context is insufficient to answer this question."
            selected.append((_with_citation(sentence, item.citation_id), item.citation_id))

        answer = " ".join(sentence for sentence, _citation_id in selected)
        cited_context_ids = _unique_ids(citation_id for _sentence, citation_id in selected)
        return GenerationResult(
            answer=answer,
            cited_context_ids=cited_context_ids,
            model_id=self.model_id,
        )


def create_generation_provider(*, backend: str, model_id: str) -> GenerationProvider:
    """Create the configured generation provider."""

    if backend != "local-grounded":
        raise UnsupportedGenerationBackendError(f"Unsupported generation backend: {backend}")
    return LocalGroundedGenerationProvider(model_id=model_id)


def _question_terms(question: str) -> set[str]:
    tokens = _tokens(question)
    filtered = {token for token in tokens if token not in _STOPWORDS and len(token) > 2}
    return filtered or tokens


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _sentences(text: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in _SENTENCE_BOUNDARY_RE.split(text.strip())
        if sentence.strip()
    ]


def _with_citation(sentence: str, citation_id: int) -> str:
    sentence = sentence.strip()
    if sentence.endswith(f"[{citation_id}]"):
        return sentence
    return f"{sentence} [{citation_id}]"


def _unique_ids(ids: Iterable[int]) -> list[int]:
    unique: list[int] = []
    for citation_id in ids:
        if citation_id not in unique:
            unique.append(citation_id)
    return unique
