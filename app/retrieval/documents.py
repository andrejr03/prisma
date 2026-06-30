"""Document loading and metadata normalization for committed Markdown corpora."""

from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.retrieval.identifiers import stable_document_id

_BLANK_LINES_RE = re.compile(r"\n{3,}")


@dataclass(frozen=True)
class CorpusManifest:
    corpus_id: str
    title: str
    license: str
    created_for: str
    files: tuple[str, ...]


@dataclass(frozen=True)
class Document:
    corpus_id: str
    license: str
    source_path: str
    title: str
    raw_text: str
    normalized_text: str
    content_hash: str
    document_id: str


def load_corpus_manifest(corpus_path: Path) -> CorpusManifest:
    manifest_path = corpus_path / "manifest.toml"
    data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    corpus = _section(data, "corpus")
    files_value = corpus.get("files")
    if not isinstance(files_value, list) or not all(isinstance(item, str) for item in files_value):
        raise ValueError("Corpus manifest must define a string files list")
    return CorpusManifest(
        corpus_id=_get_str(corpus, "id"),
        title=_get_str(corpus, "title"),
        license=_get_str(corpus, "license"),
        created_for=_get_str(corpus, "created_for"),
        files=tuple(files_value),
    )


def load_documents(corpus_path: Path, repo_root: Path) -> list[Document]:
    manifest = load_corpus_manifest(corpus_path)
    documents: list[Document] = []

    for file_name in manifest.files:
        if Path(file_name).name != file_name or not file_name.endswith(".md"):
            raise ValueError(f"Corpus file must be a Markdown filename, got {file_name!r}")
        file_path = corpus_path / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"Corpus file listed in manifest is missing: {file_path}")

        raw_bytes = file_path.read_bytes()
        raw_text = raw_bytes.decode("utf-8")
        normalized_text = normalize_text(raw_text)
        if not normalized_text:
            raise ValueError(f"Corpus document is empty after normalization: {file_path}")

        source_path = file_path.relative_to(repo_root).as_posix()
        content_hash = hashlib.sha256(raw_bytes).hexdigest()
        document_id = stable_document_id(
            corpus_id=manifest.corpus_id,
            source_path=source_path,
            content_hash=content_hash,
        )

        documents.append(
            Document(
                corpus_id=manifest.corpus_id,
                license=manifest.license,
                source_path=source_path,
                title=extract_title(normalized_text, file_path),
                raw_text=raw_text,
                normalized_text=normalized_text,
                content_hash=content_hash,
                document_id=document_id,
            )
        )

    return documents


def normalize_text(value: str) -> str:
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = _BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()


def extract_title(text: str, path: Path) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ").title()


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name)
    if not isinstance(value, dict):
        raise ValueError(f"Missing [{name}] section")
    return value


def _get_str(section: dict[str, Any], key: str) -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Expected non-empty string for {key}")
    return value
