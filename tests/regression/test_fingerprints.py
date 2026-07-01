from __future__ import annotations

from pathlib import Path

from evals.fingerprints import fingerprint_prompt


def test_fingerprint_stability_excludes_metadata(tmp_path: Path) -> None:
    prompt_path = tmp_path / "prompt.txt"
    prompt_path.write_text("Answer from context only.\n", encoding="utf-8")

    first = fingerprint_prompt(
        prompt_path=prompt_path,
        repo_root=tmp_path,
        captured_at="2026-06-30T00:00:00Z",
    )
    second = fingerprint_prompt(
        prompt_path=prompt_path,
        repo_root=tmp_path,
        captured_at="2026-07-01T00:00:00Z",
        semantic_version="v2",
    )

    assert first.digest == second.digest
    assert first.captured_at != second.captured_at
    assert first.semantic_version != second.semantic_version


def test_fingerprint_changes_when_prompt_bytes_change(tmp_path: Path) -> None:
    prompt_path = tmp_path / "prompt.txt"
    prompt_path.write_text("Answer from context only.\n", encoding="utf-8")
    first = fingerprint_prompt(prompt_path=prompt_path, repo_root=tmp_path)

    prompt_path.write_text("Answer from supplied context only.\n", encoding="utf-8")
    second = fingerprint_prompt(prompt_path=prompt_path, repo_root=tmp_path)

    assert first.digest != second.digest


def test_fingerprint_metadata_uses_repository_relative_path(repo_root: Path) -> None:
    prompt_path = repo_root / "prompts" / "baseline_rag.txt"

    fingerprint = fingerprint_prompt(
        prompt_path=prompt_path,
        repo_root=repo_root,
        captured_at="2026-06-30T00:00:00Z",
    )

    assert fingerprint.prompt_path == "prompts/baseline_rag.txt"
    assert not fingerprint.prompt_path.startswith("/")
    assert fingerprint.digest.startswith("sha256:")
