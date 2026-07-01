"""Prompt fingerprinting for Phase 5 regression."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from evals.report_models import PromptFingerprint


def fingerprint_prompt(
    *,
    prompt_path: Path,
    repo_root: Path,
    captured_at: str | None = None,
    semantic_version: str | None = None,
) -> PromptFingerprint:
    """Fingerprint a prompt using only its exact UTF-8 bytes."""

    prompt_bytes = prompt_path.read_bytes()
    digest = hashlib.sha256(prompt_bytes).hexdigest()
    decoded = prompt_bytes.decode("utf-8")
    return PromptFingerprint(
        algorithm="sha256",
        digest=f"sha256:{digest}",
        prompt_path=_repo_relative_path(prompt_path, repo_root),
        byte_count=len(prompt_bytes),
        line_count=len(decoded.splitlines()),
        captured_at=captured_at or _utc_timestamp(),
        semantic_version=semantic_version,
    )


def _repo_relative_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
