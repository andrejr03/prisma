"""Local vector-index persistence using Qdrant client local mode."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from app.retrieval.chunking import Chunk
from app.retrieval.identifiers import stable_point_id


@dataclass(frozen=True)
class SearchResult:
    chunk_id: str
    source_path: str
    score: float
    payload: dict[str, Any]


class LocalQdrantVectorIndex:
    def __init__(
        self,
        *,
        path: Path,
        collection_name: str,
        dimensions: int,
        distance: str = "cosine",
    ) -> None:
        self.path = path
        self.collection_name = collection_name
        self.dimensions = dimensions
        self.distance = _distance(distance)
        self.client = QdrantClient(path=str(path))

    def collection_exists(self) -> bool:
        return bool(self.client.collection_exists(self.collection_name))

    def recreate_collection(self) -> None:
        if self.collection_exists():
            self.client.delete_collection(self.collection_name)
        self.path.mkdir(parents=True, exist_ok=True)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.dimensions, distance=self.distance),
        )

    def upsert_chunks(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")

        points = [
            PointStruct(
                id=stable_point_id(chunk.chunk_id),
                vector=list(vector),
                payload=chunk.payload(),
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, vector: Sequence[float], *, limit: int = 5) -> list[SearchResult]:
        points = _query_points(
            self.client,
            collection_name=self.collection_name,
            vector=list(vector),
            limit=limit,
        )
        results: list[SearchResult] = []
        for point in points:
            payload = dict(point.payload or {})
            results.append(
                SearchResult(
                    chunk_id=str(payload["chunk_id"]),
                    source_path=str(payload["source_path"]),
                    score=float(point.score),
                    payload=payload,
                )
            )
        return results

    def close(self) -> None:
        close = getattr(self.client, "close", None)
        if callable(close):
            close()


def _query_points(
    client: QdrantClient,
    *,
    collection_name: str,
    vector: list[float],
    limit: int,
) -> Sequence[Any]:
    response: Any = client.query_points(collection_name=collection_name, query=vector, limit=limit)
    return cast(Sequence[Any], response.points)


def _distance(value: str) -> Distance:
    normalized = value.lower()
    if normalized == "cosine":
        return Distance.COSINE
    if normalized == "dot":
        return Distance.DOT
    if normalized == "euclid":
        return Distance.EUCLID
    raise ValueError(f"Unsupported vector distance: {value}")
