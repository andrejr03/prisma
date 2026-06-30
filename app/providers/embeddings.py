"""Provider-neutral embedding boundary and deterministic local backend."""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class EmbeddingProvider(Protocol):
    @property
    def model_id(self) -> str:
        """Stable embedding model identifier."""

    @property
    def dimensions(self) -> int:
        """Embedding vector dimensions."""

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed texts as dense vectors."""


@dataclass(frozen=True)
class HashEmbeddingProvider:
    dimensions: int = 384
    model_id: str = "hashing-v1-384"

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _TOKEN_RE.findall(text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0.0:
            return vector
        return [value / norm for value in vector]


def create_embedding_provider(
    *,
    backend: str,
    dimensions: int,
    model_id: str,
) -> EmbeddingProvider:
    if backend != "hashing":
        raise ValueError(f"Unsupported embedding backend: {backend}")
    return HashEmbeddingProvider(dimensions=dimensions, model_id=model_id)
