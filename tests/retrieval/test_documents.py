from __future__ import annotations

import pytest
from app.retrieval.documents import load_documents


def test_document_loader_reads_sample_files(phase1_settings):
    documents = load_documents(phase1_settings.corpus_path, phase1_settings.repo_root)

    assert len(documents) == 6
    assert documents[0].source_path == "datasets/sample_corpus/prisma-overview.md"
    assert documents[0].title == "Prisma Overview"
    assert documents[0].license == "CC0-1.0"
    assert documents[0].content_hash
    assert documents[0].document_id


def test_document_loader_rejects_missing_manifest_file(tmp_path, repo_root):
    corpus_path = tmp_path / "corpus"
    corpus_path.mkdir()
    (corpus_path / "manifest.toml").write_text(
        """
[corpus]
id = "missing-corpus"
title = "Missing Corpus"
license = "CC0-1.0"
created_for = "test"
files = ["missing.md"]
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_documents(corpus_path, repo_root)


def test_document_metadata_uses_relative_paths_and_stable_hashes(phase1_settings):
    first = load_documents(phase1_settings.corpus_path, phase1_settings.repo_root)
    second = load_documents(phase1_settings.corpus_path, phase1_settings.repo_root)

    assert [document.source_path for document in first] == [
        document.source_path for document in second
    ]
    assert [document.content_hash for document in first] == [
        document.content_hash for document in second
    ]
    assert [document.document_id for document in first] == [
        document.document_id for document in second
    ]
    assert all(not document.source_path.startswith("/") for document in first)
