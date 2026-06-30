"""Configuration loading for Prisma."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "defaults.toml"


@dataclass(frozen=True)
class PathSettings:
    runtime_state: str
    corpus_path: str
    index_path: str
    manifest_path: str


@dataclass(frozen=True)
class RetrievalSettings:
    chunk_size_chars: int
    chunk_overlap_chars: int


@dataclass(frozen=True)
class EmbeddingSettings:
    backend: str
    dimensions: int
    model_id: str


@dataclass(frozen=True)
class VectorIndexSettings:
    backend: str
    collection_name: str
    distance: str


@dataclass(frozen=True)
class PrismaSettings:
    repo_root: Path
    paths: PathSettings
    retrieval: RetrievalSettings
    embeddings: EmbeddingSettings
    vector_index: VectorIndexSettings

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return self.repo_root / path

    @property
    def corpus_path(self) -> Path:
        return self.resolve_path(self.paths.corpus_path)

    @property
    def index_path(self) -> Path:
        return self.resolve_path(self.paths.index_path)

    @property
    def manifest_path(self) -> Path:
        return self.resolve_path(self.paths.manifest_path)

    def with_overrides(
        self,
        *,
        corpus_path: str | None = None,
        index_path: str | None = None,
        manifest_path: str | None = None,
    ) -> PrismaSettings:
        return replace(
            self,
            paths=replace(
                self.paths,
                corpus_path=corpus_path or self.paths.corpus_path,
                index_path=index_path or self.paths.index_path,
                manifest_path=manifest_path or self.paths.manifest_path,
            ),
        )


def load_settings(config_path: Path | str = DEFAULT_CONFIG_PATH) -> PrismaSettings:
    path = Path(config_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    data = tomllib.loads(path.read_text(encoding="utf-8"))

    paths = _section(data, "paths")
    retrieval = _section(data, "retrieval")
    embeddings = _section(data, "embeddings")
    vector_index = _section(data, "vector_index")

    return PrismaSettings(
        repo_root=PROJECT_ROOT,
        paths=PathSettings(
            runtime_state=_get_str(paths, "runtime_state"),
            corpus_path=_get_str(paths, "corpus_path"),
            index_path=_get_str(paths, "index_path"),
            manifest_path=_get_str(paths, "manifest_path"),
        ),
        retrieval=RetrievalSettings(
            chunk_size_chars=_get_int(retrieval, "chunk_size_chars"),
            chunk_overlap_chars=_get_int(retrieval, "chunk_overlap_chars"),
        ),
        embeddings=EmbeddingSettings(
            backend=_get_str(embeddings, "backend"),
            dimensions=_get_int(embeddings, "dimensions"),
            model_id=_get_str(embeddings, "model_id"),
        ),
        vector_index=VectorIndexSettings(
            backend=_get_str(vector_index, "backend"),
            collection_name=_get_str(vector_index, "collection_name"),
            distance=_get_str(vector_index, "distance"),
        ),
    )


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name)
    if not isinstance(value, dict):
        raise ValueError(f"Missing [{name}] configuration section")
    return value


def _get_str(section: dict[str, Any], key: str) -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Expected non-empty string config value for {key}")
    return value


def _get_int(section: dict[str, Any], key: str) -> int:
    value = section.get(key)
    if not isinstance(value, int):
        raise ValueError(f"Expected integer config value for {key}")
    return value
